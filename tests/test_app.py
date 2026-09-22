import unittest

import httpx
from starlette.responses import RedirectResponse
from starlette.testclient import TestClient

from portal.access import AccessDenied, AccessIdentity
from portal.app import create_app
from portal.config import PortalConfig, config_from_environ
from portal.proxy import ChatProxy


class StubAccessVerifier:
    def verify(self, assertion):
        if assertion != "signed-access-token":
            raise AccessDenied("invalid")
        return AccessIdentity("access-person-1", "person@example.com")


class StubOIDCClient:
    def __init__(self, groups=None, email="person@example.com"):
        self.groups = ["ai-portal-user"] if groups is None else groups
        self.email = email
        self.redirect_uri = None

    async def authorize_redirect(self, request, redirect_uri):
        self.redirect_uri = redirect_uri
        return RedirectResponse("https://idp.example.com/authorize")

    async def authorize_access_token(self, request):
        return {
            "id_token": "validated-by-authlib",
            "userinfo": {
                "sub": "authentik-person-1",
                "email": self.email,
                "groups": self.groups,
            },
        }


class PortalAppTests(unittest.TestCase):
    def make_client(self, oidc=None, chat_proxy=None):
        oidc = oidc or StubOIDCClient()
        app = create_app(
            PortalConfig(
                public_origin="https://testserver",
                oidc_issuer="https://idp.example.com/application/o/portal/",
                oidc_client_id="portal",
                oidc_client_secret="example-only",
                session_secret="s" * 40,
            ),
            verifier=StubAccessVerifier(),
            oidc_client=oidc,
            chat_proxy=chat_proxy,
        )
        return TestClient(app, base_url="https://testserver"), oidc

    def access_headers(self):
        return {"Cf-Access-Jwt-Assertion": "signed-access-token"}

    def test_access_assertion_is_required_before_login_or_app(self):
        client, _ = self.make_client()
        for path in ("/", "/auth/login", "/auth/callback", "/chat"):
            with self.subTest(path=path):
                response = client.get(path, follow_redirects=False)
                self.assertEqual(response.status_code, 403)

    def test_valid_access_starts_oidc_with_fixed_callback(self):
        client, oidc = self.make_client()
        response = client.get(
            "/", headers=self.access_headers(), follow_redirects=False
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["location"], "/auth/login")
        response = client.get(
            "/auth/login", headers=self.access_headers(), follow_redirects=False
        )
        self.assertEqual(response.status_code, 307)
        self.assertEqual(oidc.redirect_uri, "https://testserver/auth/callback")

    def test_callback_session_authorizes_chat_and_logout_revokes_it(self):
        client, _ = self.make_client()
        callback = client.get(
            "/auth/callback", headers=self.access_headers(), follow_redirects=False
        )
        self.assertEqual(callback.status_code, 302)
        self.assertEqual(callback.headers["location"], "/")
        self.assertEqual(
            client.get("/", headers=self.access_headers()).status_code, 200
        )
        self.assertEqual(
            client.get("/chat", headers=self.access_headers()).status_code, 503
        )
        self.assertEqual(
            client.get("/scratch", headers=self.access_headers()).status_code, 403
        )
        self.assertEqual(
            client.post(
                "/auth/logout", headers=self.access_headers(), follow_redirects=False
            ).status_code,
            302,
        )
        self.assertEqual(
            client.get(
                "/chat", headers=self.access_headers(), follow_redirects=False
            ).status_code,
            302,
        )

    def test_signed_in_chat_request_reaches_upstream_without_identity_headers(self):
        observed = []

        def upstream(request):
            observed.append(request)
            return httpx.Response(200, stream=httpx.ByteStream(b"chat ready"))

        peer = httpx.AsyncClient(transport=httpx.MockTransport(upstream))
        try:
            proxy = ChatProxy("http://librechat:3080", client=peer)
            client, _ = self.make_client(chat_proxy=proxy)
            client.get("/auth/callback", headers=self.access_headers())
            response = client.get(
                "/chat/api/test",
                headers={
                    **self.access_headers(),
                    "X-Authentik-Groups": "ai-portal-admin",
                },
            )
        finally:
            import asyncio

            asyncio.run(peer.aclose())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "chat ready")
        self.assertEqual(observed[0].url.path, "/chat/api/test")
        self.assertNotIn("cf-access-jwt-assertion", observed[0].headers)
        self.assertNotIn("x-authentik-groups", observed[0].headers)
        self.assertNotIn("portal_session", observed[0].headers.get("cookie", ""))

    def test_callback_rejects_mismatched_email(self):
        client, _ = self.make_client(StubOIDCClient(email="other@example.com"))
        response = client.get("/auth/callback", headers=self.access_headers())
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("portal_session", client.cookies)

    def test_direct_chat_requires_group(self):
        client, _ = self.make_client(StubOIDCClient(groups=[]))
        client.get("/auth/callback", headers=self.access_headers())
        self.assertEqual(
            client.get("/chat", headers=self.access_headers()).status_code, 403
        )
        self.assertEqual(
            client.get("/chat/api", headers=self.access_headers()).status_code, 403
        )

    def test_untrusted_host_is_rejected(self):
        client, _ = self.make_client()
        response = client.get(
            "/auth/login", headers={**self.access_headers(), "host": "evil.example"}
        )
        self.assertEqual(response.status_code, 400)

    def test_forged_identity_headers_do_not_grant_chat(self):
        client, _ = self.make_client()
        headers = {
            **self.access_headers(),
            "X-Authentik-Username": "admin",
            "X-Authentik-Groups": "ai-portal-admin",
        }
        response = client.get("/chat", headers=headers, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["location"], "/auth/login")

    def test_tampered_session_cookie_fails_closed(self):
        client, _ = self.make_client()
        client.get("/auth/callback", headers=self.access_headers())
        cookie = client.cookies["portal_session"]
        client.cookies.set("portal_session", cookie + "tampered")
        response = client.get(
            "/chat", headers=self.access_headers(), follow_redirects=False
        )
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_post_does_not_redirect(self):
        client, _ = self.make_client()
        response = client.post(
            "/chat/api/messages", headers=self.access_headers(), follow_redirects=False
        )
        self.assertEqual(response.status_code, 401)

    def test_environment_contract_requires_all_fields(self):
        values = {
            "PORTAL_PUBLIC_ORIGIN": "https://testserver",
            "PORTAL_OIDC_ISSUER": "https://idp.example.com/application/o/portal/",
            "PORTAL_OIDC_CLIENT_ID": "portal",
            "PORTAL_OIDC_CLIENT_SECRET": "example-only",
            "PORTAL_SESSION_SECRET": "s" * 40,
            "PORTAL_ACCESS_ISSUER": "https://team.cloudflareaccess.com",
            "PORTAL_ACCESS_AUDIENCE": "audience",
            "PORTAL_CHAT_UPSTREAM_ORIGIN": "http://librechat:3080",
        }
        self.assertEqual(config_from_environ(values).access_audience, "audience")
        del values["PORTAL_SESSION_SECRET"]
        with self.assertRaisesRegex(ValueError, "PORTAL_SESSION_SECRET"):
            config_from_environ(values)

    def test_config_rejects_insecure_origin_and_weak_session_key(self):
        with self.assertRaises(ValueError):
            PortalConfig(
                "http://testserver", "https://idp.example/", "a", "b", "s" * 40
            )
        with self.assertRaises(ValueError):
            PortalConfig(
                "https://testserver", "https://idp.example/", "a", "b", "short"
            )


if __name__ == "__main__":
    unittest.main()
