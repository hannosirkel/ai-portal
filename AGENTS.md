# ai-portal

<!-- BEGIN MANAGED ARCHITECTURE BASELINE -->
<!-- Generated from hannosirkel/architecture. Do not edit inside these markers.
     Regenerate with: tooling/universe sync-baseline ai-portal -->

Governed by [`architecture`](https://github.com/hannosirkel/architecture).

| | |
| --- | --- |
| Profile | `application-public` |
| Visibility | declared public, currently public |
| Languages | none |

**Standards that apply here.** Read a standard before you change something it
governs.

- [Agent operation](https://github.com/hannosirkel/architecture/blob/main/standards/agent-operation.md) — worktrees, branches, multi-agent safety, delegation
- [Security](https://github.com/hannosirkel/architecture/blob/main/standards/security.md) — secrets, public and private boundaries, workflow hardening
- [Code quality](https://github.com/hannosirkel/architecture/blob/main/standards/code-quality.md) — gates, coaching, testing, review cutoff
- [Repository contract](https://github.com/hannosirkel/architecture/blob/main/standards/repository-contract.md) — required files, profiles, skills
- [Work routing](https://github.com/hannosirkel/architecture/blob/main/standards/work-routing.md) — where a change starts, and where a working plan belongs
- [Planning](https://github.com/hannosirkel/architecture/blob/main/standards/planning.md) — how a plan row is sized, the pull-request size gate

**Never commit to a default branch.** Work in `~/app/.worktrees/ai-portal/<task>`.
Branch from `origin/main`. Open a pull request.

**A working plan for this repository goes in `docs/working/`.** A change
spanning several repositories with no clear owner starts in `architecture`
instead.

**This repository must be safe to publish.** Never commit a password, token, key, kubeconfig,
rendered Secret, or live export. No repository in this universe holds a secret
value, and a private one is no exception.

**Run `habit-hooks` before declaring an edit done.** If it is not on `PATH`:

```bash
uv tool install "habit-hooks[python,typescript]"
```

That command names every language plugin **this universe** uses, not this
repository's. Install it whole: a later install naming fewer extras silently
removes the rest.

<!-- END MANAGED ARCHITECTURE BASELINE -->

## What this repository is

Registered, not implemented. It holds these governance files and nothing else.
`main` had no commits until the one that added them.

The intended product is `ai.future.ee`: LibreChat integration, and the agentic
and manual Scratch playground.

## Rules specific to this repository

- **Do not start the build from here.** Implementation starts as a separate
  approved initiative. Read the
  [planned record](https://github.com/hannosirkel/architecture/blob/main/initiatives/planned/ai-portal/README.md)
  first.
- **Do not scaffold.** No application directory, no package manifest, no
  placeholder code, no container definition. An empty frame invites a build no
  one approved.
- **It is public.** It must never hold a family identity, group membership, a
  provider key, an OAuth session, or a private infrastructure variable.
- **It owns nothing yet.** `deploys` will own its deployable desired state, and
  `orange` its Argo CD `Application` object.
- **Branch from now on.** The initial commit went to `main` directly under the
  empty-repository exception, because a branch cannot exist before the first
  commit. Every later change works by branch and pull request.
