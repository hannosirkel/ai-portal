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

## Purpose and boundaries

This public repository owns AI Portal application source, tests, and immutable image builds. The approved cross-repository initiative is [`architecture/initiatives/active/ai-portal.md`](https://github.com/hannosirkel/architecture/blob/main/initiatives/active/ai-portal.md). Its first release is portal/chat; Scratch hub and Scratch AI are separate later initiatives.

`deploys` owns Kubernetes workload manifests and promoted image digests. Orange owns Argo CD Applications, Access/tunnel integration, backup, and monitoring. Private inventory owns live identities and non-secret site values. Secret values enter workloads only through OpenBao and ESO. Never commit a family identity, group membership, provider key, session, or private infrastructure value here.

## Development

This foundation branch contains documentation only; code and its exact local test commands arrive with the first implementation PR. For a documentation edit, run `git diff --check` and the repository's Documentation CI. Run `habit-hooks --file <changed-file>` before declaring an edit done. Read `docs/current/README.md` and `docs/decisions/` before changing a boundary.

The launcher must enforce authorization on direct `/chat` and future `/scratch` requests. Never treat hidden cards, `Cf-Access-*` headers from an arbitrary client, or cookie `Path` as sufficient authorization. Serve future user-uploaded project bytes only as whole attachments with `nosniff` and sandbox CSP; no individual asset URLs on the shared origin.

## Branches and releases

Branch from a freshly fetched `origin/main` in `~/app/.worktrees/ai-portal/<task>`. Do not change `main` directly. Open a PR with relevant behavior tests. Build an immutable image here, then promote its digest through `deploys`; never deploy by a durable manual cluster edit. Public DNS publication has a separate operator gate.
