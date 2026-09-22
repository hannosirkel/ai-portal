"""Bind an Authentik OIDC identity to the current Cloudflare Access user.

The caller must supply claims from a cryptographically verified ID token.
This module validates their shape and prevents an OIDC session from being
replayed under a different Access identity.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from portal.access import AccessIdentity
from portal.auth import Principal


class OIDCRejected(Exception):
    """A verified token does not describe the current Access user."""


@dataclass(frozen=True, slots=True)
class PortalSession:
    oidc_subject: str
    access_subject: str
    email: str
    groups: frozenset[str]

    def principal(self) -> Principal:
        return Principal(subject=self.oidc_subject, groups=self.groups)

    def principal_for(self, access: AccessIdentity) -> Principal | None:
        if access.subject != self.access_subject or access.email != self.email:
            return None
        return self.principal()


def session_from_claims(
    claims: Mapping[str, object], access: AccessIdentity
) -> PortalSession:
    """Accept well-formed Authentik claims only for the current Access user."""
    subject = claims.get("sub")
    email = claims.get("email")
    groups = claims.get("groups")
    if not isinstance(subject, str) or not subject or len(subject) > 256:
        raise OIDCRejected("OIDC subject is invalid")
    if not isinstance(email, str) or email.casefold() != access.email:
        raise OIDCRejected("OIDC email does not match Access")
    if not isinstance(groups, list) or len(groups) > 64:
        raise OIDCRejected("OIDC groups claim is invalid")
    if any(
        not isinstance(group, str) or not group or len(group) > 128 for group in groups
    ):
        raise OIDCRejected("OIDC group name is invalid")
    return PortalSession(
        oidc_subject=subject,
        access_subject=access.subject,
        email=access.email,
        groups=frozenset(groups),
    )
