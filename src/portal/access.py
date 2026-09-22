"""Verify Cloudflare Access application assertions before trusting identity."""

from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlsplit

import jwt


class AccessDenied(Exception):
    """An Access application assertion did not establish a user."""


@dataclass(frozen=True, slots=True)
class AccessIdentity:
    subject: str
    email: str


class AccessVerifier:
    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        key_for_token: Callable[[str], object] | None = None,
    ) -> None:
        parsed = urlsplit(issuer)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or not parsed.hostname.endswith(".cloudflareaccess.com")
            or parsed.username
            or parsed.password
            or parsed.port
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Access issuer must be an HTTPS Cloudflare team domain")
        if not audience:
            raise ValueError("Access audience is required")
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        if key_for_token is None:
            client = jwt.PyJWKClient(
                f"{self.issuer}/cdn-cgi/access/certs", lifespan=300
            )
            self.key_for_token = lambda token: (
                client.get_signing_key_from_jwt(token).key
            )
        else:
            self.key_for_token = key_for_token

    def verify(self, assertion: str | None) -> AccessIdentity:
        if not assertion or len(assertion) > 16_384:
            raise AccessDenied("Access assertion is missing or oversized")
        try:
            claims = jwt.decode(
                assertion,
                self.key_for_token(assertion),
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.audience,
                options={"require": ["iss", "aud", "exp", "iat", "nbf", "sub"]},
            )
        except Exception as exc:
            raise AccessDenied("Access assertion is invalid") from exc
        subject = claims.get("sub")
        email = claims.get("email")
        if (
            claims.get("type") != "app"
            or not isinstance(subject, str)
            or not subject
            or not isinstance(email, str)
            or "@" not in email
            or any(char.isspace() for char in email)
        ):
            raise AccessDenied("Access assertion does not identify a person")
        return AccessIdentity(subject=subject, email=email.casefold())
