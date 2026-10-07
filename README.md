# AI Portal

AI Portal is the application-source repository for a family AI workspace. The first release is a launcher and LibreChat at `/` and `/chat`. Scratch is unimplemented. The separate [Scratch hub](https://github.com/hannosirkel/architecture/blob/main/initiatives/planned/scratch-hub/README.md) and [Scratch AI](https://github.com/hannosirkel/architecture/blob/main/initiatives/planned/scratch-ai/README.md) plans remain for later releases.

The launcher and LibreChat are deployed behind Cloudflare Access. The portal/chat work item is closed in the [closeout record](https://github.com/hannosirkel/architecture/blob/c47daaf9d09b4cc9cca7431ebb04f0390d63d487/docs/evidence/ai-portal/2026-10-07-closeout.md). [Remaining verification](docs/issues/portal-chat-verification.md) records checks without demonstrated acceptance evidence.

## Ownership

| Concern | Owner |
| --- | --- |
| Launcher, prefix proxy, tests, image builds; future Scratch source | This repository |
| Kubernetes workloads and pinned image digests | `deploys` |
| Argo CD Applications, cluster integration, backup, monitoring | `orange` |
| Live identities and non-secret site choices | `orange-inventory` |
| Secret values | OpenBao through Orange's sanctioned ESO path; never Git |
| Cross-repository contract and gate evidence | `architecture` |

This repository is public. It contains no family names or addresses, group membership, provider keys, OAuth sessions, or private infrastructure values. See [current state](docs/current/README.md), the [portal boundary decision](docs/decisions/001-portal-boundaries.md), and [agent instructions](AGENTS.md).

## Development

Run `ruff check .`, `ruff format --check src tests`, and
`PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py'` for Python
changes. Pull requests also build the pinned container image and start its
readiness endpoint. Main-branch builds publish a digest-addressed image to
GHCR. Promotion of that digest belongs in `deploys`; this repository never
deploys workloads directly.
