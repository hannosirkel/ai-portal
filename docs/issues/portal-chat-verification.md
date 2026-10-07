# Portal/chat verification evidence gaps

Portal/chat is deployed and its implementation work item is closed. The checks
below lack complete demonstrated acceptance evidence at closeout on 2026-10-07.
This issue preserves unresolved observations; it is not an implementation plan
or a claim that the deployed controls fail.

The [closeout record](https://github.com/hannosirkel/architecture/blob/c47daaf9d09b4cc9cca7431ebb04f0390d63d487/docs/evidence/ai-portal/2026-10-07-closeout.md)
owns dated release observations, source and deployment references, and exceptions.
Record identity-bearing observations in private inventory and link a sanitized
summary here when a check is demonstrated. Automated tests alone do not prove
live browser, network, or operator behavior.

## Remaining observations

| Boundary | Observation still needing complete evidence |
| --- | --- |
| Session renewal | Expire Authentik's session while Google's session remains valid; confirm re-establishment without another credential prompt. |
| Access | Confirm an unlisted account is denied before origin, including the published external route. Remove an Access-listed account and confirm revocation. |
| Entitlement | Check direct `/chat` access and launcher visibility against group membership. Remove an Authentik group and confirm capability revocation. |
| Profiles | Exercise restricted, user, and separately assigned admin profiles. Reject tampered hidden model/tool selections server-side; confirm group changes on next sign-in. |
| Browser routing | Retest `/chat` and `/chat/` after the redirect fix in a real browser. Check OIDC redirects, assets, and MCP OAuth callback without doubled or missing prefixes. |
| Proxy and cookies | Confirm forged headers fail on a non-tunnel path and origin ports are unreachable outside approved paths. Verify all five auth cookie paths and absence of portal name collisions. |
| Stream and body | Observe incremental model output and complete errors for body/upload limits on the deployed release. |
| Provider | Demonstrate OpenRouter-only requests, clear expired-key errors and operator alerts, and the operator-set spend limit. |
| Availability | Fire and clear portal and MongoDB availability alerts; preserve evidence that portal, chat, and database rules render. |
| Headroom | Confirm MongoDB PVC and host disk capacity on the dashboard and the host disk alert protecting local-path storage. |
| GitOps and publication | Demonstrate rollback to a known-good application and compare the serving digest with the recorded release. Preserve external Access and Cloudflare gate observations. |

The synthetic-identity probe of the deployed redirect code does not replace a
real browser retest. A text reply and visible model selector do not establish
profile tamper resistance or account revocation. Existing restore and failure
alert observations remain evidence in the closeout record; repeat them only
when the release or acceptance claim needs new evidence.

## Independent HTTPS monitor exception

The local release handoff records an operator waiver dated 2026-09-29 for the
independent public HTTPS monitor because the portal is non-critical. The
closeout record preserves that local-note provenance. This issue does not
reopen that monitor as a blocker. Internal availability and failure alerts
remain required.

## Scratch boundary

Scratch is unimplemented, and `/scratch` remains unavailable. The separate
[Scratch hub](https://github.com/hannosirkel/architecture/blob/main/initiatives/planned/scratch-hub/README.md)
and [Scratch AI](https://github.com/hannosirkel/architecture/blob/main/initiatives/planned/scratch-ai/README.md)
plans remain. Project archive and user-derived response checks belong to those
releases before uploaded project content can be exposed.
