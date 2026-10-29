# Production gates and secrets

## Secrets

Required repository Actions Secrets: TDESKTOP_API_ID and TDESKTOP_API_HASH. The infrastructure preflight requires no secrets and only reports presence booleans, never values. Do not set secrets from a public PR context or print the environment.

When a secure local file is supplied, transfer each value with gh secret set through stdin. Never put values in shell history, command arguments, checked-in files, logs or manifests. Do not search another platform's credentials or assume iOS credentials should be reused. Missing credentials do not block infrastructure preflight; they do block production.

The active D1B out has configured client credentials. Preserve them. DEV reuses the existing values through the supported CMake initial-cache loader inside the container. Changing API definitions invalidates objects; do not introduce or replace credentials as an incidental infrastructure operation. Historical D0 test credentials are not the active D1B client configuration.

## Build adapter and LTO

Upstream Docker CXXFLAGS contains -flto=auto. CMAKE_BUILD_PARALLEL_LEVEL controls build scheduling, not GCC's internal LTO worker count. Final Release link flags must override auto with -flto=1 and --param=lto-max-streaming-parallelism=1. The second flag explicitly limits LTO streaming. Do not turn LTO off to hide a resource problem.

D0 failed with global OOM at final link. Its successful one-worker manual relink took 1h31m48s, with host peak RAM about 28.64 GiB and zram swap about 14.51 GiB. Compiler/linker resource requirements and runner disk requirements must be measured before selecting production hardware.

For an existing failed build, do not change global CMAKE_CXX_FLAGS just to limit link workers. Inspect generated commands and preserve compiled objects. D0 was recovered by direct replay of the exact final command with only the two link-time changes. The generic build adapter is for a future explicitly authorized configure/build and is never a D0 repair command.

## Replaceable runner and toolchain

Preflight runs on hosted Ubuntu without secrets/local execution. `production.yml` is an explicit trusted manual candidate workflow with capacity rejection before expensive work; runtime acceptance is still a separate required gate. Select proven larger/persistent hardware through PRODUCTION_RUNNER_JSON, considering CPU, RAM, disk, swap and cache retention. Standard hosted resources are not assumed sufficient. Never run public PR code on a persistent builder.

The historical upstream image tag was mutable. The fast-dev infrastructure records an own immutable registry reference and image/config IDs in toolchains/lock.json after retention is verified; do not treat a mutable tag as a production pin. A production campaign must record image ID, compiler/linker/strip versions, upstream Dockerfile/generator identity and dependency refs. D0 image ID is sha256:f8254a3af4ff32abc7cb5b5519f150d84e0df7a5fffe8cf50a2e25a20e2f8d9a. Toolchain preparation itself downloads some moving distribution packages; pinning source alone is not a claim of byte-identical builds.

## Release gates

Future build: pinned fetch → recursive submodules → materialize/verify → controlled Release/LTO → verify ELF → runtime proof → strip staging copy → tar.xz → SHA256/provenance → clean source export → explicit publication.

Current manifest generation is real, but it does not certify runtime or sign a release. Before public publication add an audited clean source exporter (no .git history, out, local agent overrides or secrets), dependency/license provenance, artifact verification and explicit release gates. Keep ghostbase-sg/jerkgram-desktop-builder as development origin. Only then create jerkgram/Jerkgram-Desktop for clean source/releases.

## Daily development

Use the optimized no-LTO dev-fast profile in [fast-dev.md](fast-dev.md). Disabling LTO there is an intentional separate development policy, not a change to production quality. Production is never the default per-commit build.
