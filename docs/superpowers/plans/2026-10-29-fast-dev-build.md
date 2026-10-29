# Fast incremental Linux development implementation plan

> **For agentic workers:** Use superpowers:executing-plans in this chat. No per-task implementer agents; one final independent review.

**Goal:** Restore and retain the official toolchain; measure a persistent optimized no-LTO daily loop without degrading production.

**Architecture:** Reuse telegram-desktop-d1. Preserve existing production out and D1B artifacts. A normal CMake-configured persistent out/dev-fast isolates incompatible compile flags; production continues using out with one-worker LTO. A pinned registry image plus a checked archive provide recovery independent of Docker caches.

**Tech Stack:** Existing upstream Docker/Jinja/GCC15/static Qt6, Python stdlib builder, CMake/Ninja, GitHub Actions/GHCR.

**Spec:** ../specs/2026-10-29-fast-dev-request.md (user's authoritative request).

## Global constraints

- No product features, Debug baseline, source fork, clean/prune, production LTO campaign or credentials changes.
- Preserve D1 source/out, production binaries/evidence/artifacts and remotes.
- Branch from 891defe6bc4c187dd61b97386e4b426f856a7b91; all permanent infrastructure changes belong in the builder.
- Verify actual effective compile/link flags; DESKTOP_APP_ENABLE_LTO alone does not remove image ENV flags.
- Reuse existing configured API credentials within CMake without printing them or placing them in reports/image.

## Approaches and storage decision

Measured: 313 GiB free; D1 41 GiB (34 GiB Telegram build intermediates, 6.3 GiB Release binaries), source otherwise about 1 GiB. Docker images absent.

In-place switching would invalidate production/dev objects on every switch. A duplicate source tree is unnecessary. Selected minimal proposal: one source plus out/dev-fast, leaving production out intact. New tree starts as CMake metadata only; measure representative object sizes and bootstrap delta, do not clone a 40 GiB checkout. Reduced line-level debug metadata and no fat-LTO should reduce dev output. Exact delta remains measured, not promised.

GHCR: CLI lacks read/write:packages; trusted Actions GITHUB_TOKEN with packages:write can publish. Evaluate restored layer sizes against GHCR's 10 GB/layer and 10 minute upload limits. Keep a digest-checked archive outside Docker as secondary protection; if registry fails, document a tested remote archive fallback.

## Review focus

1. Accidental production invalidation: profile routing must reject wrong build dir and preserve production cache/binary hashes.
2. Hidden LTO from static dependencies: verify generated flags and native fallback in fat archives; actually observe no LTO processes in dev links.
3. Credential/image leakage: minimal generated context; never include source/out/HOME/API settings; test rejected local COPY inputs.
4. Source verification vs benchmarks: controlled temporary edits restore exact bytes/mtime in finally; ordinary dirty sources fail closed.
5. Recovery false confidence: verify stored archive/digest and restore path without deleting the valuable installed image or compiling dependencies again.

## Tasks

### 1. Toolchain recovery and retention

- [ ] Add failing safety tests for pinned recipe and context.
- [ ] Implement recipe/render/build/inspect helpers and bounded BuildKit parallelism; verify tests.
- [ ] Restore from unchanged upstream template/generator/lock; record versions, image ID, size, time, compatibility and storage.
- [ ] Snapshot/archive and publish through trusted workflow or verified fallback; pin registry manifest and test recovery.

### 2. Profile routing and preflight

- [ ] Add tests for no-LTO env derivation, CMake seed/routing, generated flag gates, source/credential safety.
- [ ] Implement dev-fast optimized Release + no LTO, one persistent build state, supported CMake configuration. Production remains Release + one-worker LTO.
- [ ] Update lightweight per-commit checks and explicit production workflow; no production execution in this task.

### 3. Bootstrap and benchmarks

- [ ] Verify source/config and production preservation; run the once-only dev bootstrap.
- [ ] Measure no-op, one TU, two TUs, narrow header fanout and realistic owner-local temporary edit; restore exact source.
- [ ] Record compile/link/total, operations, host memory/swap, disk deltas and runtime smoke.

### 4. Documentation, review and delivery

- [ ] Write daily/milestone/recovery/cache guidance and measured comparison table; update stale README baseline claims.
- [ ] Independent final review, resolve material findings, verify all gates, commit/push builder branch and run lightweight GitHub checks.
- [ ] Stop before product features or public product release.
