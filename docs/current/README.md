# Current state

AI Portal has no runtime, image, database, or deployment yet. The first approved implementation slice is portal/chat. Scratch hub and Scratch AI are separate later initiatives, so `/scratch` remains unavailable until the hub's own acceptance gate.

The launcher will serve `/`; the prefix proxy will serve LibreChat under `/chat` on the same application origin. Authentik is the application identity provider on a separate Access-gated origin. Cloudflare Access admits only enumerated accounts, while Authentik groups determine application roles. Remote model traffic will use OpenRouter. These are approved design boundaries, not deployed behavior.

Deployment ownership is split: this repository builds source images, `deploys` pins workload digests, Orange renders the Argo CD Application and owns the cluster integration, and private inventory holds site identities. Runtime secrets arrive from OpenBao through ESO. The portal DNS record remains withheld until production behavior is verified and the operator approves publication.

The [active initiative](https://github.com/hannosirkel/architecture/blob/main/initiatives/active/ai-portal.md) tracks what remains. The [boundary decision](../decisions/001-portal-boundaries.md) explains the local application design.
