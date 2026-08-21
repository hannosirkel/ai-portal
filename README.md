# ai-portal

Registered, not implemented. This repository holds its governance files and no
product code. Its `main` had no commits before the one that added them.

The intended product is `ai.future.ee` and its subprojects: LibreChat
integration, and the agentic and manual Scratch playground.

## What it owns

Nothing yet. When the product exists, this repository will own its source, its
tests, and its image build.

## What it does not own

| Concern | Owner |
| --- | --- |
| Deployable desired state | `deploys` |
| Argo CD `Application` objects and cluster bootstrap | `orange` |
| Live private values | `orange-inventory` |
| Reusable agent skills | `myskills` |
| Standards, profiles, and the catalogue | [`architecture`](https://github.com/hannosirkel/architecture) |

## Visibility

Public, and it must stay safe to publish. It must never hold a family identity,
group membership, a provider key, an OAuth session, or a private infrastructure
variable.

## Developing and testing

There is nothing to build, run, or test. The repository declares no language, so
no language gate applies to it.

## Starting the implementation

Implementation starts as a separate approved initiative, not from this
repository. The planned record is
[`initiatives/planned/ai-portal/`](https://github.com/hannosirkel/architecture/blob/main/initiatives/planned/ai-portal/README.md).
It states the product boundary, the ownership split, and the steps that open the
real initiative.

## Where things live

| Question | Answer |
| --- | --- |
| How do I work here? | [`AGENTS.md`](AGENTS.md) |
| What is planned? | the [planned record](https://github.com/hannosirkel/architecture/blob/main/initiatives/planned/ai-portal/README.md) |
| What rules apply everywhere? | [`architecture`](https://github.com/hannosirkel/architecture) |
