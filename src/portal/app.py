"""Access-gated ASGI entry point and Authentik OIDC sign-in."""

from collections.abc import Mapping
from contextlib import asynccontextmanager
from typing import Protocol
from urllib.parse import urlsplit

from authlib.integrations.base_client import OAuthError
from authlib.integrations.starlette_client import OAuth
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from starlette.routing import Route

from portal.access import AccessDenied, AccessIdentity, AccessVerifier
from portal.auth import permitted
from portal.config import PortalConfig
from portal.oidc import OIDCRejected, PortalSession, session_from_claims
from portal.proxy import ChatProxy


class OIDCClient(Protocol):
    async def authorize_redirect(self, request: Request, redirect_uri: str): ...

    async def authorize_access_token(self, request: Request): ...


def _load_session(request: Request) -> PortalSession | None:
    value = request.session.get("portal")
    if not isinstance(value, dict):
        return None
    subject = value.get("oidc_subject")
    access_subject = value.get("access_subject")
    email = value.get("email")
    groups = value.get("groups")
    if (
        not isinstance(subject, str)
        or not subject
        or not isinstance(access_subject, str)
        or not access_subject
        or not isinstance(email, str)
        or not isinstance(groups, list)
        or len(groups) > 64
        or any(not isinstance(group, str) or not group for group in groups)
    ):
        return None
    return PortalSession(subject, access_subject, email, frozenset(groups))


class PortalRuntime:
    """Request handlers for the Access and Authentik security boundary."""

    def __init__(
        self,
        config: PortalConfig,
        verifier: AccessVerifier,
        oidc_client: OIDCClient,
        chat_proxy: ChatProxy | None,
    ) -> None:
        self.config = config
        self.verifier = verifier
        self.oidc_client = oidc_client
        self.chat_proxy = chat_proxy

    def access_identity(self, request: Request) -> AccessIdentity | None:
        try:
            return self.verifier.verify(request.headers.get("Cf-Access-Jwt-Assertion"))
        except AccessDenied:
            return None

    async def health(self, _request: Request):
        return PlainTextResponse("ok")

    async def login(self, request: Request):
        if self.access_identity(request) is None:
            return PlainTextResponse("Forbidden", status_code=403)
        callback = self.config.public_origin.rstrip("/") + "/auth/callback"
        return await self.oidc_client.authorize_redirect(request, callback)

    async def callback(self, request: Request):
        access = self.access_identity(request)
        if access is None:
            return PlainTextResponse("Forbidden", status_code=403)
        try:
            token = await self.oidc_client.authorize_access_token(request)
            if not isinstance(token, Mapping) or not isinstance(
                token.get("id_token"), str
            ):
                raise OIDCRejected("OIDC ID token is missing")
            claims = token.get("userinfo")
            if not isinstance(claims, Mapping):
                raise OIDCRejected("OIDC claims are missing")
            session = session_from_claims(claims, access)
        except (OAuthError, OIDCRejected):
            request.session.pop("portal", None)
            return PlainTextResponse("Forbidden", status_code=403)
        request.session["portal"] = {
            "oidc_subject": session.oidc_subject,
            "access_subject": session.access_subject,
            "email": session.email,
            "groups": sorted(session.groups),
        }
        return RedirectResponse("/", status_code=302)

    async def logout(self, request: Request):
        request.session.clear()
        return RedirectResponse("/", status_code=302)

    async def application(self, request: Request):
        access = self.access_identity(request)
        if access is None:
            return PlainTextResponse("Forbidden", status_code=403)
        session = _load_session(request)
        principal = session.principal_for(access) if session else None
        if principal is None:
            if request.method in {"GET", "HEAD"}:
                return RedirectResponse("/auth/login", status_code=302)
            return PlainTextResponse("Unauthorized", status_code=401)
        path = request.url.path
        if not permitted(principal, path):
            return PlainTextResponse("Forbidden", status_code=403)
        if path == "/":
            return HTMLResponse("<main><h1>AI Portal</h1></main>")
        if path == "/chat" or path.startswith("/chat/"):
            if self.chat_proxy is None:
                return PlainTextResponse("Chat is not deployed", status_code=503)
            return await self.chat_proxy.forward(request)
        return PlainTextResponse("Not found", status_code=404)


def create_app(
    config: PortalConfig,
    *,
    verifier: AccessVerifier | None = None,
    oidc_client: OIDCClient | None = None,
    chat_proxy: ChatProxy | None = None,
) -> Starlette:
    """Build the portal with injectible protocol peers for behavior tests."""
    if verifier is None:
        verifier = AccessVerifier(
            issuer=config.access_issuer, audience=config.access_audience
        )
    if oidc_client is None:
        oauth = OAuth()
        oidc_client = oauth.register(
            "authentik",
            client_id=config.oidc_client_id,
            client_secret=config.oidc_client_secret,
            server_metadata_url=(
                config.oidc_issuer.rstrip("/") + "/.well-known/openid-configuration"
            ),
            client_kwargs={"scope": "openid profile email groups"},
        )
    if chat_proxy is None and config.chat_upstream_origin:
        chat_proxy = ChatProxy(config.chat_upstream_origin)
    runtime = PortalRuntime(config, verifier, oidc_client, chat_proxy)

    @asynccontextmanager
    async def lifespan(_app):
        try:
            yield
        finally:
            if chat_proxy is not None:
                await chat_proxy.aclose()

    app = Starlette(
        lifespan=lifespan,
        routes=[
            Route("/healthz", runtime.health, methods=["GET"]),
            Route("/auth/login", runtime.login, methods=["GET"]),
            Route("/auth/callback", runtime.callback, methods=["GET"]),
            Route("/auth/logout", runtime.logout, methods=["POST"]),
            Route(
                "/{path:path}",
                runtime.application,
                methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            ),
        ],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=config.session_secret,
        session_cookie="portal_session",
        max_age=3600,
        same_site="lax",
        https_only=True,
    )
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=[urlsplit(config.public_origin).hostname]
    )
    return app
