"""Application path entitlements from verified Authentik OIDC groups.

Callers must construct ``Principal`` only after validating an OIDC identity.
Cloudflare Access headers alone do not grant an application entitlement.
"""

from dataclasses import dataclass
from typing import Literal

PathClass = Literal["launcher", "chat", "scratch", "unknown"]


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    groups: frozenset[str]


def classify_path(path: str) -> PathClass:
    if not path.startswith("/") or "//" in path or "\\" in path or "\x00" in path:
        return "unknown"
    if any(segment in {".", ".."} for segment in path.split("/")):
        return "unknown"
    if path == "/" or path.startswith("/assets/"):
        return "launcher"
    if path == "/chat" or path.startswith("/chat/"):
        return "chat"
    if path == "/scratch" or path.startswith("/scratch/"):
        return "scratch"
    return "unknown"


def permitted(principal: Principal | None, path: str) -> bool:
    if principal is None or not principal.subject:
        return False
    match classify_path(path):
        case "launcher":
            return True
        case "chat":
            return bool(principal.groups & {"ai-portal-admin", "ai-portal-user"})
        case "scratch" | "unknown":
            return False
