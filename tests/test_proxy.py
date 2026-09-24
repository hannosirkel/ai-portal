import unittest

import httpx
from starlette.requests import Request

from portal.proxy import ChatProxy, ProxyConfigurationError, rewrite_cookie_path


class CountingStream(httpx.AsyncByteStream):
    def __init__(self):
        self.reads = 0

    async def __aiter__(self):
        self.reads += 1
        yield b"data: first\n\n"
        yield b"data: second\n\n"


class ChatProxyTests(unittest.IsolatedAsyncioTestCase):
    def request(
        self, path="/chat/api/messages", query=b"", headers=(), body=b"", method=None
    ):
        sent = False

        async def receive():
            nonlocal sent
            if sent:
                return {"type": "http.disconnect"}
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        scope = {
            "type": "http",
            "method": method or ("POST" if body else "GET"),
            "scheme": "https",
            "server": ("testserver", 443),
            "path": path,
            "raw_path": path.encode(),
            "query_string": query,
            "headers": [
                (key.lower().encode(), value.encode()) for key, value in headers
            ],
        }
        return Request(scope, receive)

    def test_cookie_path_is_confined_to_chat(self):
        for name in (
            "refreshToken",
            "token_provider",
            "openid_access_token",
            "openid_id_token",
            "openid_user_id",
            "connect.sid",
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    rewrite_cookie_path(
                        f"{name}=value; HttpOnly; Path=/; SameSite=Strict"
                    ),
                    f"{name}=value; HttpOnly; Path=/chat; SameSite=Strict",
                )
        self.assertEqual(
            rewrite_cookie_path("other=value; Secure"),
            "other=value; Secure; Path=/chat",
        )

    async def test_proxy_preserves_prefix_query_and_strips_identity_headers(self):
        observed = []

        def upstream(request):
            observed.append(request)
            return httpx.Response(
                200,
                headers=[
                    ("set-cookie", "refreshToken=one; Path=/; HttpOnly"),
                    ("set-cookie", "token_provider=openid; HttpOnly"),
                    ("content-type", "text/plain"),
                    ("service-worker-allowed", "/"),
                ],
                content=b"ok",
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
            proxy = ChatProxy("http://librechat:3080", client=client)
            request = self.request(
                query=b"conversation=one",
                headers=[
                    ("Cf-Access-Jwt-Assertion", "signed-access"),
                    ("X-Authentik-Groups", "ai-portal-admin"),
                    ("X-Forwarded-Host", "evil.example"),
                    ("Cookie", "portal_session=private; refreshToken=one"),
                    ("Connection", "upgrade"),
                ],
            )
            response = await proxy.forward(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(observed[0].url.path, "/chat/api/messages")
            self.assertEqual(observed[0].url.query, b"conversation=one")
            for name in (
                "cf-access-jwt-assertion",
                "x-authentik-groups",
                "x-forwarded-host",
                "upgrade",
            ):
                self.assertNotIn(name, observed[0].headers)
            self.assertEqual(observed[0].headers["cookie"], "refreshToken=one")
            self.assertEqual(
                response.headers.getlist("set-cookie"),
                [
                    "refreshToken=one; Path=/chat; HttpOnly",
                    "token_provider=openid; HttpOnly; Path=/chat",
                ],
            )
            self.assertEqual(response.headers["service-worker-allowed"], "/chat/")
            self.assertEqual(response.headers["x-content-type-options"], "nosniff")
            self.assertIn(
                "script-src 'self'", response.headers["content-security-policy"]
            )
            await response.background()

    async def test_oversized_request_is_rejected_before_upstream(self):
        calls = []

        def upstream(request):
            calls.append(request)
            return httpx.Response(200)

        async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
            proxy = ChatProxy("http://librechat:3080", client=client, max_body_bytes=4)
            response = await proxy.forward(self.request(body=b"12345"))
            self.assertEqual(response.status_code, 413)
            self.assertEqual(calls, [])

    async def test_upload_entry_points_are_denied_before_upstream(self):
        calls = []

        def upstream(request):
            calls.append(request)
            return httpx.Response(200)

        async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
            proxy = ChatProxy("http://librechat:3080", client=client)
            for path in (
                "/chat/api/files",
                "/chat/api/files/images",
                "/chat/api/files/speech/stt",
                "/chat/API/FILES/speech/STT",
                "/chat/api/convos/import",
                "/chat/api/convos/IMPORT",
                "/chat/api/skills/skill-id/files",
            ):
                with self.subTest(path=path):
                    response = await proxy.forward(
                        self.request(path=path, body=b"upload", method="POST")
                    )
                    self.assertEqual(response.status_code, 403)
            self.assertEqual(calls, [])

    async def test_file_route_prefix_does_not_block_chat_messages(self):
        calls = []

        def upstream(request):
            calls.append(request)
            return httpx.Response(200)

        async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
            proxy = ChatProxy("http://librechat:3080", client=client)
            for path in ("/chat/api/messages", "/chat/api/files-extra"):
                response = await proxy.forward(self.request(path=path, body=b"text"))
                self.assertEqual(response.status_code, 200)
                await response.background()
            self.assertEqual(len(calls), 2)

    async def test_proxy_does_not_buffer_streaming_response(self):
        stream = CountingStream()

        def upstream(request):
            return httpx.Response(
                200, headers={"content-type": "text/event-stream"}, stream=stream
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
            proxy = ChatProxy("http://librechat:3080", client=client)
            response = await proxy.forward(self.request())
            self.assertEqual(stream.reads, 0)
            chunks = [chunk async for chunk in response.body_iterator]
            self.assertEqual(chunks, [b"data: first\n\n", b"data: second\n\n"])
            await response.background()

    async def test_proxy_rejects_invalid_upstream_and_non_chat_paths(self):
        with self.assertRaises(ProxyConfigurationError):
            ChatProxy("http://librechat:3080/other")
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda request: httpx.Response(200))
        ) as client:
            proxy = ChatProxy("http://librechat:3080", client=client)
            response = await proxy.forward(self.request(path="/admin"))
            self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
