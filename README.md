# AI Portal

AI Portal is the application-source repository for a family AI workspace. The first release is a launcher and LibreChat at `/` and `/chat`. Separate planned releases add a Scratch-compatible project hub at `/scratch`, then controlled AI project edits.

The cross-repository [active initiative](https://github.com/hannosirkel/architecture/blob/main/initiatives/active/ai-portal.md) defines the release gates and acceptance behavior. No runtime or image has shipped from this repository yet.

## Ownership

| Concern | Owner |
| --- | --- |
| Launcher, prefix proxy, Scratch source, tests, image builds | This repository |
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
