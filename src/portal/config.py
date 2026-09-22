"""Validated deployment configuration for the portal runtime."""

from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class PortalConfig:
    public_origin: str
    oidc_issuer: str
    oidc_client_id: str
    oidc_client_secret: str
    session_secret: str
    access_issuer: str = ""
    access_audience: str = ""

    def __post_init__(self) -> None:
        public = urlsplit(self.public_origin)
        issuer = urlsplit(self.oidc_issuer)
        if (
            public.scheme != "https"
            or not public.hostname
            or public.username
            or public.password
            or public.path not in {"", "/"}
            or public.query
            or public.fragment
        ):
            raise ValueError("public origin must be an HTTPS origin")
        if (
            issuer.scheme != "https"
            or not issuer.hostname
            or issuer.username
            or issuer.password
            or issuer.query
            or issuer.fragment
        ):
            raise ValueError("OIDC issuer must be HTTPS")
        if not self.oidc_client_id or not self.oidc_client_secret:
            raise ValueError("OIDC client credentials are required")
        if len(self.session_secret) < 32:
            raise ValueError("session signing key is too short")


def config_from_environ(env: Mapping[str, str]) -> PortalConfig:
    """Read only the explicit runtime contract; never echo secret values."""
    names = (
        "PORTAL_PUBLIC_ORIGIN",
        "PORTAL_OIDC_ISSUER",
        "PORTAL_OIDC_CLIENT_ID",
        "PORTAL_OIDC_CLIENT_SECRET",
        "PORTAL_SESSION_SECRET",
        "PORTAL_ACCESS_ISSUER",
        "PORTAL_ACCESS_AUDIENCE",
    )
    missing = [name for name in names if not env.get(name)]
    if missing:
        raise ValueError("missing portal configuration: " + ", ".join(missing))
    return PortalConfig(*(env[name] for name in names))
