# Jerkgram Desktop Builder

Canonical development/build infrastructure: `ghostbase-sg/jerkgram-desktop-builder`.

The pinned implementation is Official Telegram Desktop v7.3.1 at `6fed91ffab9861771a75f29df65031b3c80b6941`. This repository contains builder-owned scripts, tests, metadata and future overlays, not the Telegram source history or local build output.

D1B identity alpha `0.1.0-alpha.1` is compiled and runtime-tested. The current infrastructure milestone separates daily optimized no-LTO development from explicit production LTO. See [daily/recovery instructions](docs/fast-dev.md) and [measurement ledger](docs/fast-dev-progress.md) for actual completion status.

## Architecture

One pinned, materialized source tree → two persistent build configurations → independent verification and packaging. Builder owns patches/assets/configuration; it does not carry Telegram source history. Existing production `out/` and artifacts are preserved. Daily work uses only `out/dev-fast` in the same source tree.

`jerkgram/Jerkgram-Desktop` remains reserved for future clean source snapshots and approved public Releases.

## Fast preflight

Run `python3 scripts/preflight.py --output reports`, `python3 scripts/build_profile.py validate` and `python3 -m unittest discover -s tests -v`.

Every push/PR runs hosted source/profile/fixture tests and pinned materialization. It needs no API Secrets and never compiles Telegram or executes public PR code on a local runner. Production and toolchain publication are separate explicit workflows.

## Source preparation

Use a persistent materialized source directory outside this builder repository:

```sh
python3 scripts/builder.py prepare --source /path/to/telegram-desktop
python3 scripts/builder.py materialize --source /path/to/telegram-desktop
```

Preparation fetches the pinned tag and rejects an unexpected SHA. Existing checkouts are verified before any operation; no reset, clean or overwrite is performed. Default preparation initializes pinned recursive submodules. `--skip-submodules` is a fetch-only preflight mode, never proof of a build-ready dependency tree.

Materialization applies and verifies the ordered D1 patches and hashed payloads. It accepts pristine pinned input or the exact already materialized state, and fails closed on drift. Reuse the existing active source tree rather than creating another checkout per milestone.

## Development and production

[Build profiles and recovery](docs/fast-dev.md) describe the supported commands. `dev-fast` is the default; production requires explicit opt-in and proven runner capacity. Production retains Release LTO with one streaming worker. DEV is optimized Release with LTO disabled in both the image-derived initial compiler environment and normal CMake options; effective generated commands are checked.

Packaging requires matching compile/config evidence and strips a staging copy. It does not certify runtime or authorize publication. Milestone runtime acceptance remains a separate gate.

## Boundaries

- Never commit API credentials, full source checkout, out, binaries, Docker/cache or private logs.
- Keep upstream tracked `AGENTS.md` intact; local source instructions belong in ignored `AGENTS.override.md`.
- Preserve the expensive D0 source/build state and Docker image: [storage policy](docs/storage.md).
- Product feature development remains outside the fast-dev infrastructure milestone.

## D1B identity alpha

The D1 overlay is defined by `D1_CONFIG.json`, ordered `patches/series`, hashed payloads and `JERKGRAM_VERSION`. Read `docs/d1-audit.md` and `docs/d1b-progress.md` for ownership, scope and actual evidence. D1 completion requires Release compile and runtime coexistence; unit tests are not that proof.

For first materialization use pristine pinned input. For daily work reuse the active D1 source; never reapply patches to unrelated or partial trees. `python3 scripts/builder.py materialize --source PATH` accepts pristine pinned input or verifies the exact previously materialized output; mismatched/partial overlays fail closed. `verify-source` reports the verified state. Generated build output is allowed only under `out`; unexpected ignored source inputs are rejected.

Approved Linux branding is `JerkgramGlassReveal.icon`; canonical source vectors/recipe and approval provenance live in `payloads/linux-identity/master`. Derivatives are committed and hash checked. Regenerate with `python3 scripts/generate_linux_icons.py` (librsvg `rsvg-convert` required), and generate presentation header with `python3 scripts/generate_identity_header.py`. Review/update manifest hashes after intentional changes; never accept unverified payload drift.

The explicit production workflow uses trusted manual dispatch and a separately selected production runner. Standard hosted preflight resources are not evidence of production LTO capacity. Production Secrets are forwarded only through environment variables, and subprocess output is redacted.

`python3 scripts/package_release.py --source PATH --evidence PATH --output NEW_PATH` requires matching compile/config evidence. It strips a copy, packages only explicit own assets/notices and produces SHA256/provenance. No Updater/Packer/profile/credential/build-log packaging. Optional user-local integration is explicit via the packaged `install_linux.py`; it does not set default URL handlers.
