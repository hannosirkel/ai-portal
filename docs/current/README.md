# Current state

AI Portal has an Access assertion verifier and an ASGI OIDC sign-in entry point.
Its pinned, non-root image build runs a readiness smoke test on pull requests
and publishes an immutable GHCR digest from `main`. The portal image is
promoted to the cluster. The implemented release is portal/chat. Scratch is unimplemented;
`/scratch` remains unavailable until the separate hub release passes acceptance.

The server-rendered launcher serves `/` with a chat destination and a disabled
Scratch card. Its stylesheet is packaged with the Python application and is
served only after the same Access and session checks. The prefix proxy serves
LibreChat under `/chat` on the same application origin. Authentik is the
application identity provider on a separate Access-gated origin. Cloudflare
Access admits only enumerated accounts, while Authentik groups determine
application roles. Remote model traffic uses OpenRouter.

Deployment ownership is split: this repository builds source images,
`deploys` pins workload digests, Orange renders the Argo CD Application and
owns cluster integration, and private inventory holds site identities. Runtime
secrets arrive from OpenBao through ESO. The portal DNS record is published.

The [verification issue](../issues/portal-chat-verification.md) tracks remaining
observations. The [boundary decision](../decisions/001-portal-boundaries.md) explains
the local application design. The [closeout record](https://github.com/hannosirkel/architecture/blob/c47daaf9d09b4cc9cca7431ebb04f0390d63d487/docs/evidence/ai-portal/2026-10-07-closeout.md)
records release evidence and exceptions.

The ASGI entry point binds a validated Authentik ID token to the current
Cloudflare Access subject and email. Its signed, HTTPS-only session expires
after one hour, and direct `/chat` requests require a portal group. The chat
card is unavailable without that group. `/scratch` stays denied. The chat
proxy strips the public `/chat` prefix before forwarding to LibreChat, which
serves its assets and APIs at root. Authorized GET and HEAD requests to
`/chat` or `/chat/` redirect to `/chat/c/new`, preserving query parameters, so
login returns and launcher visits enter an explicit conversation route.
Its chat CSP allows only the two inline
bootstrap script hashes from the pinned LibreChat image; review the hashes when
that image changes. Only LibreChat's API receives browser bearer tokens;
other chat paths and identity headers remain stripped before forwarding.
The proxy replaces client-supplied forwarding headers with its fixed HTTPS
scheme indicator so LibreChat can issue a Secure OIDC session cookie across the
internal HTTP hop. It confines that cookie to `/chat` in the browser.

Only the OpenRouter custom endpoint is enabled. User and restricted profiles
allow the same two configured text models; admin may use the configured
OpenRouter catalog. These deployment choices do not establish live tamper-test
evidence; see the verification issue.

The first chat release has transient LibreChat upload storage. The proxy
rejects writes to LibreChat's file and skill routes and conversation import,
including the speech-to-text upload route, before forwarding a request body.
These routes need persistent storage and a separate release review before they
can be enabled.

Run the app with `uvicorn portal.server:app`. Its required environment is
`PORTAL_PUBLIC_ORIGIN`, `PORTAL_OIDC_ISSUER`, `PORTAL_OIDC_CLIENT_ID`,
`PORTAL_OIDC_CLIENT_SECRET`, `PORTAL_SESSION_SECRET`, `PORTAL_ACCESS_ISSUER`,
and `PORTAL_ACCESS_AUDIENCE`. The session key and OIDC client secret must enter
through OpenBao/ESO; the other values come from the deployment contract.

The container listens on port 8080 as UID/GID 10001. An HTTP readiness probe
to `/healthz` must send the configured public hostname in `Host`; the app's
trusted-host middleware rejects a pod-IP host. The image workflow records the
published digest in its run summary for an approved `deploys` promotion.

## Operations and recovery

Orange's [command catalogue](https://github.com/hannosirkel/orange/blob/main/docs/current/commands.md)
owns reconciliation commands. Its [provisioning guide](https://github.com/hannosirkel/orange/blob/main/docs/current/provisioning.md)
owns credential lifecycle and guarded database restore.

Renew an expired OpenBao operator login with `scripts/openbao-login` from Orange.
Use direct callback mode when the browser is remote. Never put credentials in Git.
Roll back workloads through a known-good image digest or pinned GitOps revision.
Withdraw the portal DNS record for fast exposure rollback.
Run database restore only through the explicit guarded lifecycle, never routine reconciliation.
