# Fast-dev infrastructure ledger — 2026-10-29

Plan: docs/superpowers/plans/2026-10-29-fast-dev-build.md

Baseline: d1/identity-alpha at 891defe6bc4c187dd61b97386e4b426f856a7b91, clean builder. Source remains exact 36-file D1 materialization on upstream 6fed91ffab9861771a75f29df65031b3c80b6941.

Initial storage: root 476G / used 163G / available 313G; D1 41G; D0 source 1010M; artifacts75M; no Docker images, cache43.11MB. No removals performed.

Ruling: execute the supplied detailed task inline, preserving the authorized scope; avoid redundant permission rounds for restoration/build/commit operations already requested. Report significant storage/design decisions before use. Keep source single and production out untouched; create no milestone clone.

Ruling: upstream CFLAGS/CXXFLAGS inject -flto=auto -ffat-lto-objects even when the dependent CMake LTO option is OFF. Dev must remove ENV LTO at initial supported configuration and verify effective commands/native dependency fallback. Production keeps existing policy.

Ruling: CLI package permission 403 does not rule out GHCR; use supported Actions GITHUB_TOKEN packages:write, investigate layer sizes after recovery. No broader PAT requested.

Status: task1 preparation; no toolchain/Telegram build started yet.

Ruling: DNF stalled on EPEL HTTP mirror.twds.com.tw (Curl28, filelists metadata). Official HTTPS dl.fedoraproject.org/epel returned 200 in 0.66s. Retry uses one bounded, hash-recorded transport-only insertion before the exact upstream PowerTools anchor; no package lists, dependency refs, compiler flags or cache were changed/deleted. Stopped only the build client; preserved failed attempt evidence and BuildKit cache.

Official upstream GHCR digest 4f629171eb8b468ce4d8de9208c3a4523f8a91698fa091ba786849452f90c81c exists, created 2026-10-22. Its environment explicitly omits dependency LTO/debug. It is not silently substituted for the D1B full-LTO dependency image; compatibility/use remains a separate decision.

Ruling: canceled DNF left metadata_lock.pid=1 in its persistent metadata cache. Verified previous DNF is gone and PID1 in the new namespace is the current bash wrapper, not a DNF owner. Released only that stale lock; no metadata/package cache removed. Future recovery inserts the same narrow namespace/comm guard before first DNF to avoid repeating the deadlock. Running retry keeps its already-recorded rendered Dockerfile hash; future recipe renders include the guard.

Status 23:34 Moscow: recovery is active in Qt/heif dependency stages; no duplicate recovery or Telegram build started. 33 builder tests PASS, including complete real Docker29 OCI/gzip save verification and failed-benchmark restoration-report regression. Production preservation inventory recorded: 2178 objects and original binary/cache hashes; dev dir not yet allocated. Benchmark reporting now asserts source restoration only after strict verification.
