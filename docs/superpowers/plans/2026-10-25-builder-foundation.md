# Desktop builder foundation implementation plan

Goal: a lightweight Jerkgram-owned builder with an actual green preflight, while retaining the D0 source/build state.
Architecture: separate builder repository; pinned upstream materialized checkout; zero product changes until D1. Public source/release export remains a later explicit gate.
Tech stack: Python 3 standard library, Git, Docker, GitHub Actions, gh.
Spec: user's 2026-10-25 Desktop builder request in the current Work chat.

## Constraints
- Exact upstream v7.3.1 / 6fed91ffab9861771a75f29df65031b3c80b6941.
- Preserve out, D0 binary/evidence, Docker image and existing credentials.
- No full Telegram build or branding; no public release repository yet.
- Never store or print API credentials.
- No subagents or additional chats needed for this implementation.

## Tasks
- [x] Inspect local instructions/Git and GitHub access before mutations.
- [x] Test and implement pinned-source preparation, clean verification and truthful zero-change materialization.
- [x] Add opt-in Release build adapter with link-only LTO limits and sanitized logs; never invoke it in preflight.
- [x] Test packaging on a small fixture ELF: copy, strip, tar.xz, checksum and provenance; retain original binary.
- [x] Add runner-neutral preflight with resource/secret-presence reports and real pinned upstream fetch.
- [x] Document local storage, remote model, production gates and D1 read-only identity audit.
- [ ] Create public builder, push initial commit and verify actual Actions result/artifacts.

## Review focus
Fail closed for wrong upstream SHA, dirty or uninitialized sources, nonempty unapplied overlays, missing credentials, unsafe package destinations, and false production/runtime claims.

## Execution ledger
User explicitly authorized automatic local implementation, repository creation, initial commits/push and preflight. Interactive CLI authorization is the only expected human gate. Stage implementation outside the materialized D0 checkout.

Ruling: the supplied task authorizes direct execution and initial publication; no additional plan-approval pause. CLI device authorization completed by user. Production credentials are not present locally and are not required for a truthful preflight. Full production build and clean source exporter remain explicit future gates.
