import time
import unittest

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from portal.access import AccessDenied, AccessVerifier


class AccessAssertionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public_key = cls.private_key.public_key()

    def setUp(self):
        self.verifier = AccessVerifier(
            issuer="https://example.cloudflareaccess.com",
            audience="portal-audience",
            key_for_token=lambda _token: self.public_key,
        )
        now = int(time.time())
        self.claims = {
            "iss": "https://example.cloudflareaccess.com",
            "aud": ["portal-audience"],
            "exp": now + 300,
            "iat": now,
            "nbf": now,
            "sub": "user-subject",
            "type": "app",
            "email": "Person@Example.com",
        }

    def token(self, claims=None, key=None):
        return jwt.encode(
            claims or self.claims, key or self.private_key, algorithm="RS256"
        )

    def test_valid_identity_is_normalized(self):
        identity = self.verifier.verify(self.token())
        self.assertEqual(identity.email, "person@example.com")
        self.assertEqual(identity.subject, "user-subject")

    def test_missing_or_forged_assertion_is_denied(self):
        for token in (
            None,
            "",
            "not-a-jwt",
            self.token(
                key=rsa.generate_private_key(public_exponent=65537, key_size=2048)
            ),
        ):
            with self.subTest(token=bool(token)), self.assertRaises(AccessDenied):
                self.verifier.verify(token)

    def test_wrong_audience_issuer_and_expiry_are_denied(self):
        for replacement in (
            {"aud": ["other-audience"]},
            {"iss": "https://other.cloudflareaccess.com"},
            {"exp": int(time.time()) - 1},
        ):
            with self.subTest(replacement=replacement), self.assertRaises(AccessDenied):
                self.verifier.verify(self.token({**self.claims, **replacement}))

    def test_service_token_and_missing_email_are_denied(self):
        for replacement in (
            {"email": ""},
            {"email": "person@example.com", "sub": ""},
            {"type": "org"},
        ):
            with self.subTest(replacement=replacement), self.assertRaises(AccessDenied):
                self.verifier.verify(self.token({**self.claims, **replacement}))

    def test_team_url_must_be_https_and_host_only(self):
        for issuer in (
            "http://example.cloudflareaccess.com",
            "https://example.cloudflareaccess.com/path",
            "https://example.cloudflareaccess.com@evil.invalid",
        ):
            with self.subTest(issuer=issuer), self.assertRaises(ValueError):
                AccessVerifier(issuer=issuer, audience="portal-audience")


if __name__ == "__main__":
    unittest.main()
