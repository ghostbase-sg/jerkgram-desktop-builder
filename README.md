# Jerkgram Desktop Builder

Canonical development/build infrastructure: `ghostbase-sg/jerkgram-desktop-builder`.

The pinned implementation is Official Telegram Desktop v7.3.1 at `6fed91ffab9861771a75f29df65031b3c80b6941`. This repository contains builder-owned scripts, tests, metadata and future overlays, not the Telegram source history or local build output.

Current milestone: builder foundation after D0. **Zero Jerkgram product changes.** `JERKGRAM_VERSION=0.0.0-d0` is builder metadata; it is not a branded app release. D1 identity is not implemented.

## Architecture

Pinned clean upstream → verify SHA/submodules → materialize Jerkgram-owned changes → verify → Release build with controlled LTO → strip a copy → package/checksum/provenance → later clean source export and public release.

`jerkgram/Jerkgram-Desktop` is reserved for future clean source snapshots, tags, provenance and Releases. Do not use it as the development origin or transfer builder history into it. Do not create it before D1 build/runtime/artifact/source-export gates pass.

## Preflight

Run `python3 scripts/preflight.py --output reports` and `python3 -m unittest discover -s tests -v`.

Actions runs resource reporting, small builder tests and a real fetch/verification of the pinned upstream tag/SHA. It deliberately skips recursive submodule downloads and all Telegram compilation/runtime. Missing production secrets are reported as presence booleans and do not make this infrastructure preflight pretend production readiness.

Runner selection is replaceable: `PREFLIGHT_RUNNER_JSON` repository variable, or `runner_json` on workflow_dispatch, accepts a JSON runner label or label array. Default: `"ubuntu-24.04"`. There is no automatic pull-request execution on self-hosted machines.

## Source preparation

Use a persistent materialized source directory outside this builder repository:

```sh
python3 scripts/builder.py prepare --source /path/to/telegram-desktop
python3 scripts/builder.py materialize --source /path/to/telegram-desktop
```

Preparation fetches the pinned tag and rejects an unexpected SHA. Existing checkouts are verified before any operation; no reset, clean or overwrite is performed. Default preparation initializes pinned recursive submodules. `--skip-submodules` is a fetch-only preflight mode, never proof of a build-ready dependency tree.

Materialization currently verifies a clean pinned checkout and returns `product_changes: []`. Nonempty patch/payload manifests fail explicitly until D1 materialization is implemented and audited; they are never silently ignored.

## Future production build (explicit opt-in)

See [production build requirements](docs/production.md) before running any expensive operation.

```sh
python3 scripts/builder.py build-release --source /path/to/managed-source --execute
```

The adapter uses the official `tdesktop:centos_env` image and existing `out/`, Release configuration, current environment API credentials, two compile jobs by default, and Release link overrides `-flto=1 --param=lto-max-streaming-parallelism=1`. It does not prepare/rebuild the Docker image. It sanitizes API credential values from subprocess output.

This adapter is an implementation for a future authorized build, **not a claim that a production build has passed**. Preflight never calls it. Do not point it at the valuable D0 tree with production credentials: changing its test credentials changes compile definitions and causes recompilation. D0's successful manual relink is documented separately.

## Packaging

```sh
python3 scripts/builder.py package --source /path/to/managed-source \
  --binary /path/to/managed-source/out/Release/Telegram \
  --output /path/to/artifacts/version
```

Packaging copies and strips an x86-64 ELF, writes a portable `.tar.xz`, `SHA256SUMS` and `manifest.json`. The input binary is preserved. Output must be a new directory outside the source/build tree. Current artifact names explicitly say `stock-telegram-desktop`; D1 will introduce branded packaging after the identity audit.

Packaging does not assert compile/runtime evidence. The manifest records upstream/builder commits, dirty state, zero overlays, input/stripped/artifact hashes and sizes. Future release publication must join these records to actual successful build/runtime evidence and pinned toolchain provenance; no export/publish workflow exists yet.

## Boundaries

- Never commit API credentials, full source checkout, out, binaries, Docker/cache or private logs.
- Keep upstream tracked `AGENTS.md` intact; local source instructions belong in ignored `AGENTS.override.md`.
- Preserve the expensive D0 source/build state and Docker image: [storage policy](docs/storage.md).
- Next milestone starts with the [D1 focused read-only identity audit](docs/d1-audit.md), not automatic product edits.
