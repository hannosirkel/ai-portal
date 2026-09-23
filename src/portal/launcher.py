"""Server-rendered launcher with no script-capable user content."""

from functools import lru_cache
from html import escape
from importlib.resources import files
from string import Template

from starlette.responses import HTMLResponse, Response


@lru_cache(maxsize=1)
def _asset(name: str) -> str:
    return files("portal").joinpath("assets", name).read_text(encoding="utf-8")


def launcher_response(email: str, *, can_chat: bool) -> HTMLResponse:
    chat_action = (
        '<a class="action action--primary" href="/chat/">Open Chat '
        '<span aria-hidden="true">→</span></a>'
        if can_chat
        else '<span class="action action--disabled" aria-disabled="true">'
        "Access unavailable</span>"
    )
    content = Template(_asset("launcher.html")).substitute(
        email=escape(email),
        initial=escape(email[:1].upper()),
        chat_action=chat_action,
        chat_card_class="destination--chat" if can_chat else "destination--locked",
    )
    return HTMLResponse(
        content,
        headers={
            "Content-Security-Policy": (
                "default-src 'none'; style-src 'self'; form-action 'self'; "
                "base-uri 'none'; frame-ancestors 'none'"
            ),
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
        },
    )


def stylesheet_response() -> Response:
    return Response(
        _asset("launcher.css"),
        media_type="text/css",
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=3600",
        },
    )
