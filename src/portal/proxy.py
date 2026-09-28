"""Bounded, streaming reverse proxy for the LibreChat subdirectory."""

import re
from urllib.parse import urlsplit

import httpx
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import PlainTextResponse, StreamingResponse


class ProxyConfigurationError(ValueError):
    """The upstream is not a fixed HTTP origin."""


_HOP_HEADERS = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
        "host",
    }
)
_IDENTITY_HEADERS = frozenset({"forwarded", "proxy-authorization"})
_COOKIE_PATH = re.compile(r"(?i)(^|;\s*)path=[^;]*")


def rewrite_cookie_path(cookie: str) -> str:
    """Confine each upstream cookie to the chat path."""
    if _COOKIE_PATH.search(cookie):
        return _COOKIE_PATH.sub(r"\g<1>Path=/chat", cookie, count=1)
    return cookie + "; Path=/chat"


def _safe_request_header(name: str, connection_tokens: set[str]) -> bool:
    return (
        name not in _HOP_HEADERS
        and name not in connection_tokens
        and name not in _IDENTITY_HEADERS
        and not name.startswith(("cf-access-", "x-authentik-", "x-forwarded-"))
    )


def _safe_response_header(name: str, connection_tokens: set[str]) -> bool:
    return (
        name not in _HOP_HEADERS
        and name not in connection_tokens
        and name
        not in {
            "content-security-policy",
            "service-worker-allowed",
            "x-content-type-options",
        }
    )


def _upload_route(path: str) -> bool:
    """Deny file ingestion while the first chat release has transient storage."""
    path = path.lower()  # Express matches these upstream routes case-insensitively.
    return (
        path == "/chat/api/files"
        or path.startswith("/chat/api/files/")
        or path == "/chat/api/convos/import"
        or path == "/chat/api/skills"
        or path.startswith("/chat/api/skills/")
    )


class ChatProxy:
    """Forward public /chat requests to LibreChat routes at its root."""

    def __init__(
        self,
        upstream_origin: str,
        *,
        client: httpx.AsyncClient | None = None,
        max_body_bytes: int = 20 * 1024 * 1024,
    ) -> None:
        parsed = urlsplit(upstream_origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
            or max_body_bytes < 1
        ):
            raise ProxyConfigurationError("chat upstream must be a fixed HTTP origin")
        self.origin = upstream_origin.rstrip("/")
        self.max_body_bytes = max_body_bytes
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10, read=300, write=30, pool=5),
            follow_redirects=False,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def _request_body(self, request: Request):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size < 0:
                    return PlainTextResponse("Invalid Content-Length", status_code=400)
                if size > self.max_body_bytes:
                    return PlainTextResponse("Request too large", status_code=413)
            except ValueError:
                return PlainTextResponse("Invalid Content-Length", status_code=400)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > self.max_body_bytes:
                return PlainTextResponse("Request too large", status_code=413)
        return bytes(body)

    def _request_headers(self, request: Request):
        connection_tokens = {
            token.strip().lower()
            for token in request.headers.get("connection", "").split(",")
        }
        headers = []
        for name_bytes, value_bytes in request.headers.raw:
            name = name_bytes.decode("latin-1").lower()
            if not _safe_request_header(name, connection_tokens):
                continue
            if name == "authorization" and not (
                request.scope["path"].startswith("/chat/api/")
                and value_bytes.lower().startswith(b"bearer ")
                and len(value_bytes) > len(b"bearer ")
            ):
                continue
            if name == "cookie":
                cookies = [
                    part.strip() for part in value_bytes.decode("latin-1").split(";")
                ]
                cookies = [
                    part
                    for part in cookies
                    if part and part.split("=", 1)[0] != "portal_session"
                ]
                if cookies:
                    headers.append((name, "; ".join(cookies)))
            elif name not in {"content-length", "accept-encoding"}:
                headers.append((name_bytes, value_bytes))
        # The public origin is HTTPS. LibreChat needs this trusted indicator
        # to issue its Secure OIDC session cookie behind the HTTP cluster hop.
        headers.append((b"x-forwarded-proto", b"https"))
        return headers

    def _target(self, request: Request) -> str:
        path = request.scope["path"]
        raw_path = request.scope.get("raw_path", path.encode("utf-8"))
        query = request.scope.get("query_string", b"")
        # LibreChat v0.8.7 serves assets and APIs at its root. Its generated
        # HTML uses <base href="/chat/"> for the browser-facing path.
        target = self.origin + (raw_path[5:].decode("ascii") or "/")
        if query:
            target += "?" + query.decode("ascii")
        return target

    def _response(self, upstream: httpx.Response) -> StreamingResponse:
        response_tokens = {
            token.strip().lower()
            for token in upstream.headers.get("connection", "").split(",")
        }
        response = StreamingResponse(
            upstream.aiter_raw(),
            status_code=upstream.status_code,
            background=BackgroundTask(upstream.aclose),
        )
        response.raw_headers = [
            (
                name,
                rewrite_cookie_path(value.decode("latin-1")).encode("latin-1")
                if name.lower() == b"set-cookie"
                else value,
            )
            for name, value in upstream.headers.raw
            if _safe_response_header(name.decode("latin-1").lower(), response_tokens)
        ]
        response.headers["Content-Security-Policy"] = (
            # The pinned LibreChat v0.8.7 image emits two stable inline startup
            # scripts. Permit their exact hashes without allowing arbitrary inline JS.
            "default-src 'self'; script-src 'self' "
            "'sha256-ApRfxd0rLedfnw6ZDBJ3VtMvEqlMCVS8OkY8rahs7+Q=' "
            "'sha256-oWye3rCVXoUhqUJ9AiI+/t+rzdB/PSKIhkv0zyf495w='; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob: https:; font-src 'self' data:; "
            "connect-src 'self' wss:; object-src 'none'; base-uri 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Service-Worker-Allowed"] = "/chat/"
        return response

    async def forward(self, request: Request):
        path = request.scope["path"]
        raw_path = request.scope.get("raw_path", path.encode("utf-8"))
        if (path != "/chat" and not path.startswith("/chat/")) or (
            raw_path != b"/chat" and not raw_path.startswith(b"/chat/")
        ):
            return PlainTextResponse("Not found", status_code=404)
        if request.method not in {"GET", "HEAD", "OPTIONS"} and _upload_route(path):
            return PlainTextResponse("Uploads unavailable", status_code=403)
        body = await self._request_body(request)
        if isinstance(body, PlainTextResponse):
            return body
        outbound = self.client.build_request(
            request.method,
            self._target(request),
            headers=self._request_headers(request),
            content=body,
        )
        try:
            upstream = await self.client.send(outbound, stream=True)
        except httpx.HTTPError:
            return PlainTextResponse("Chat unavailable", status_code=502)
        return self._response(upstream)
