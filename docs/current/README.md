# Current state

AI Portal has an Access assertion verifier and an ASGI OIDC sign-in entry point, but no deployable image, chat proxy, database, or deployment yet. The first approved implementation slice is portal/chat. Scratch hub and Scratch AI are separate later initiatives, so `/scratch` remains unavailable until the hub's own acceptance gate.

The server-rendered launcher serves `/` with a chat destination and a disabled
Scratch card. Its stylesheet is packaged with the Python application and is
served only after the same Access and session checks. The prefix proxy serves
LibreChat under `/chat` on the same application origin. Authentik is the
application identity provider on a separate Access-gated origin. Cloudflare
Access admits only enumerated accounts, while Authentik groups determine
application roles. Remote model traffic will use OpenRouter. These are approved
design boundaries, not deployed behavior.

Deployment ownership is split: this repository builds source images, `deploys` pins workload digests, Orange renders the Argo CD Application and owns the cluster integration, and private inventory holds site identities. Runtime secrets arrive from OpenBao through ESO. The portal DNS record remains withheld until production behavior is verified and the operator approves publication.

The [active initiative](https://github.com/hannosirkel/architecture/blob/main/initiatives/active/ai-portal.md) tracks what remains. The [boundary decision](../decisions/001-portal-boundaries.md) explains the local application design.

The ASGI entry point binds a validated Authentik ID token to the current
Cloudflare Access subject and email. Its signed, HTTPS-only session expires
after one hour, and direct `/chat` requests require a portal group. The chat
card is unavailable without that group. `/scratch` stays denied. The chat
proxy returns 503 until its LibreChat upstream is configured; it is not a
deployed chat service.

Run the app with `uvicorn portal.server:app`. Its required environment is
`PORTAL_PUBLIC_ORIGIN`, `PORTAL_OIDC_ISSUER`, `PORTAL_OIDC_CLIENT_ID`,
`PORTAL_OIDC_CLIENT_SECRET`, `PORTAL_SESSION_SECRET`, `PORTAL_ACCESS_ISSUER`,
and `PORTAL_ACCESS_AUDIENCE`. The session key and OIDC client secret must enter
through OpenBao/ESO; the other values come from the deployment contract.
