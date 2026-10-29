# Fast-dev infrastructure ledger — 2026-10-29

Plan: docs/superpowers/plans/2026-10-29-fast-dev-build.md

Baseline: d1/identity-alpha at 891defe6bc4c187dd61b97386e4b426f856a7b91, clean builder. Source remains exact 36-file D1 materialization on upstream 6fed91ffab9861771a75f29df65031b3c80b6941.

Initial storage: root 476G / used 163G / available 313G; D1 41G; D0 source 1010M; artifacts75M; no Docker images, cache43.11MB. No removals performed.

Ruling: execute the supplied detailed task inline, preserving the authorized scope; avoid redundant permission rounds for restoration/build/commit operations already requested. Report significant storage/design decisions before use. Keep source single and production out untouched; create no milestone clone.

Ruling: upstream CFLAGS/CXXFLAGS inject -flto=auto -ffat-lto-objects even when the dependent CMake LTO option is OFF. Dev must remove ENV LTO at initial supported configuration and verify effective commands/native dependency fallback. Production keeps existing policy.

Ruling: CLI package permission 403 does not rule out GHCR; use supported Actions GITHUB_TOKEN packages:write, investigate layer sizes after recovery. No broader PAT requested.

Initial status (before recovery launch): task1 preparation; no toolchain/Telegram build started. Superseded by the timestamped entries below.

Ruling: DNF stalled on EPEL HTTP mirror.twds.com.tw (Curl28, filelists metadata). Official HTTPS dl.fedoraproject.org/epel returned 200 in 0.66s. Retry uses one bounded, hash-recorded transport-only insertion before the exact upstream PowerTools anchor; no package lists, dependency refs, compiler flags or cache were changed/deleted. Stopped only the build client; preserved failed attempt evidence and BuildKit cache.

Official upstream GHCR digest 4f629171eb8b468ce4d8de9208c3a4523f8a91698fa091ba786849452f90c81c exists, created 2026-10-22. Its environment explicitly omits dependency LTO/debug. It is not silently substituted for the D1B full-LTO dependency image; compatibility/use remains a separate decision.

Ruling: canceled DNF left metadata_lock.pid=1 in its persistent metadata cache. Verified previous DNF is gone and PID1 in the new namespace is the current bash wrapper, not a DNF owner. Released only that stale lock; no metadata/package cache removed. Future recovery inserts the same narrow namespace/comm guard before first DNF to avoid repeating the deadlock. Running retry keeps its already-recorded rendered Dockerfile hash; future recipe renders include the guard.

Status 23:34 Moscow: recovery is active in Qt/heif dependency stages; no duplicate recovery or Telegram build started. 33 builder tests PASS, including complete real Docker29 OCI/gzip save verification and failed-benchmark restoration-report regression. Production preservation inventory recorded: 2178 objects and original binary/cache hashes; dev dir not yet allocated. Benchmark reporting now asserts source restoration only after strict verification.

GitHub checkpoint 0b59e4d pushed; hosted preflight 40950515595 PASS (12 seconds, pinned materialization + 33 tests). New manual workflow files are not registered on the repository default branch yet. Ruling: bootstrap trusted toolchain publication via a manual-only boolean on the existing registered preflight workflow calling the same reusable retention job; pushes/PRs still execute only hosted preflight. No merge/default-branch change or package PAT needed. Policy regression RED→GREEN, suite34 PASS.

Ruling: browser inventory has no signed-in GitHub session; own GHCR packages default private and CLI lacks package scopes. Keep private-registry recovery available through the same trusted Actions workflow GITHUB_TOKEN rather than extracting tokens or requesting a broader PAT. A manual restore-registry operation reuses the pinned image helper and one-job local runner, with no production/API Secrets. Public visibility is optional, not a prerequisite for a real remote backup; local direct anonymous pull must not be claimed for a private package.

Status 2026-10-30 00:01 Moscow: upstream Qt compilation active (921/6919), WebRTC stage past compile; no new restoration error, swap0. Latest hosted preflight 40951930783 PASS at372ee2a, 37 tests. Detached gated continuation is waiting at fast-dev-evidence/continuation.json; it performs compatibility → checked backup → lock → normal DEV configure/bootstrap → five benchmark cases, stops on failure. Registry and runtime acceptance remain explicitly pending. No production build or product changes.

2026-10-30 02:16: Docker dependency build/export/load SUCCEEDED, new native image ID sha256:8a1b4c81f9d09e148df60f7c9819c2a4b10aa34a5c02bef8307c2001d5f1bf07, config ce456fd48f862daee24de5b8cfa78df5f50ece9597fdf2c879f7e88e426744bc, 29,837,815,381 bytes. Initial inspector incorrectly assumed Qt6Core.pc; source of error proven by successful installed qmake/CMake discovery. Corrected only inspector/probe, no image rebuild. Missing-pkgconfig regression RED→GREEN, suite38 PASS. Tiny Qt6Core native executable, partial native old-object link, and one-object one-worker GCC incremental LTO parse/link all exit0; original object SHA preserved. GCC15.2.1 / Qt6.11.2 match D1B, CMake3.26.5, Ninja1.13.2.git.kitware.jobserver-pipe-1, lld21.1.8. Original failed inspection evidence retained; verified recovery report is separate.

02:19: archive `/Desktop/toolchain-backups/tdesktop-v7.3.1-8a1b4c81f9d0.tar.zst` complete, 10,724,587,066 bytes, SHA2564972e808425a22c22d1a8baf9b9b6c9159383c03b192afa2eeaa9f283b606c14. All native layers/config/OCI identity verified before renaming partial file. Exact lock committed separately; registry reference remains pending publication. Real DEV CMake configure PASS: optimized Release, no effective LTO/fat-object flags, static Core/Gui/Widgets, updater disabled; production cache SHA unchanged. First once-only bootstrap started with two compile jobs, 2378 operations planned in new persistent out/dev-fast. No production command executed.
