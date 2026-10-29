# Linux development, production and recovery

## Scope and current status

Active source: `/home/pixi/Projects/Jerkgram/Desktop/telegram-desktop-d1`.
Builder: `/home/pixi/Projects/Jerkgram/Desktop/jerkgram-desktop-builder`.
Upstream v7.3.1 / `6fed91ffab9861771a75f29df65031b3c80b6941`; D1B builder base `891defe6bc4c187dd61b97386e4b426f856a7b91`.

This milestone changes infrastructure only. The measured report will distinguish restoration/bootstrap from ordinary incremental work; until those runs finish, no performance claim is made. See `fast-dev-progress.md`.

## Daily development

Run commands from the builder directory. Keep one source tree, one persistent `out/dev-fast`, and existing production `out`.

```sh
source_dir=/home/pixi/Projects/Jerkgram/Desktop/telegram-desktop-d1
python3 scripts/builder.py verify-source --source "$source_dir"
# Only once, or after an intentional profile/toolchain change:
python3 scripts/build_profile.py configure --source "$source_dir" --evidence /path/to/new/config-evidence
python3 scripts/build_profile.py build --source "$source_dir" --evidence /path/to/new/build-evidence
```

DEV uses Release optimization, `-g1`, static upstream dependencies, Ninja and native lld linking. It removes image-injected `-flto`/fat objects and checks the generated flags. It neither edits generated Ninja files nor switches the production cache. Configured API credentials are reused through a supported CMake initial-cache loader inside the container; values are never placed in command arguments or reports. Updater remains disabled.

Source verification is strict by default. For an intentional narrow source edit, list each existing owner explicitly, e.g. `--edit-path Telegram/SourceFiles/intro/intro_start.cpp`. This only permits existing `.cpp`/`.h` owners; it does not permit build scripts, payload changes, new files or submodule drift. Builder-owned lasting product changes must still be represented by patches/payload hashes and reviewed. Do not rematerialize over an unrecorded edit.

Run `out/dev-fast/Jerkgram` only with the intended Jerkgram profile. For smoke tests use a fresh synthetic HOME/XDG namespace and private session bus; do not point it at official Telegram data. Existing D1B runtime evidence remains separate from new DEV evidence.

An unchanged build should do no compilation/linking. A changed TU recompiles that TU and links native objects; production LTO is not part of this daily command. Header changes may fan out through dependents. Do not delete build state between tasks.

## Explicit milestone production

1. Verify exact materialization, tests and pinned toolchain.
2. Use the explicit `production.yml` workflow on a trusted proven runner, or:

```sh
python3 scripts/build_profile.py build --profile production --execute-production \
  --source "$source_dir" --evidence /path/to/new/production-evidence
```

3. Perform runtime acceptance on the resulting binary (including identity/profile/update gates).
4. Package using `scripts/package_release.py` with matching evidence; inspect manifest/checksums.

API Secrets must be supplied securely for a new production configuration. Existing configured credentials must not be changed accidentally. Production preserves `-flto=1 --param=lto-max-streaming-parallelism=1`; two compile jobs are the default. The workflow packages a candidate, not an accepted/public release. No automatic publication or source export is implied.

`PRODUCTION_RUNNER_JSON` can select larger/persistent hardware without changing builder architecture. The resource precheck reflects measured D1B needs: at least 30 GiB RAM, 44 GiB RAM+swap and 80 GiB free disk. These are a rejection gate, not a guarantee that every workload will fit. Public PRs never reach this runner. This infrastructure task does not run production.

## Disaster recovery

The primary recovery reference belongs in `toolchains/lock.json`: own versioned GHCR image plus immutable manifest digest, native config digest and daemon image ID. Do not recover from a mutable `latest` tag.

```sh
python3 scripts/toolchain.py restore-registry
python3 scripts/toolchain.py inspect
```

The helper pulls only when absent and checks identity before continuing. A retained image needs no dependency rebuild. The second copy is a checked `docker save` zstd archive outside Docker:

```sh
python3 scripts/toolchain.py restore-archive \
  --archive /path/to/retained-toolchain.tar.zst \
  --metadata /path/to/retained-toolchain.tar.zst.json
```

The archive path and publication/digest acceptance are recorded in the final measurement report. Do not assume retention is complete merely because helper scripts exist. Archive recovery verifies the outer checksum, image identity and every native layer before loading. Docker's daemon ID may identify an OCI index rather than the native config; both are tracked.

If neither image nor archive is available, the pinned upstream recipe can rebuild dependencies:

```sh
python3 scripts/toolchain.py rebuild --source "$source_dir" \
  --renderer-python /path/to/python-with-Jinja2-3.1.6 \
  --evidence /path/to/new/toolchain-evidence --execute
```

This is the slow last resort. It uses the verified upstream template/generator/lock with a recorded HTTPS EPEL transport override. Moving base packages mean a source pin does not promise the historical image digest.

If `out/dev-fast` is lost, a new DEV bootstrap is required. If production `out` is lost, production objects must be rebuilt for the next milestone. Registry retention preserves dependencies; it cannot recover deleted application objects. Losing source edits requires Git/patch recovery, not Docker.

## Storage and concurrency

No automatic clean/prune. `out/dev-fast` isolates incompatible flags without another source clone. Production cache/binary hashes are checked before and after DEV builds; benchmark source bytes and timestamps are restored even on failure.

Toolchain recovery uses BuildKit maximum stage concurrency 2 and dependency jobs 2, with a 24 GiB container cap. DEV defaults to two compile jobs. Do not run dependency recovery, DEV and production builds simultaneously. See `storage.md` for retention costs and consequences of deletion.

For the infrastructure smoke gate (host GNOME introspection Python, Hyprland + grim available):

```sh
dbus-run-session -- /usr/bin/python3 scripts/runtime_dev.py \
  --binary "$source_dir/out/dev-fast/Jerkgram" \
  --root /tmp/jerkgram-dev-runtime-UNIQUE \
  --evidence /path/to/new/runtime-evidence --platform xcb
```

Run a second independent private-bus invocation with `--platform wayland` and new root/evidence. The helper checks UI/process, own default profile/D-Bus and disabled update application; it does not claim authenticated Telegram behavior or redo the completed D1B coexistence campaign.

### Private GHCR without a package PAT

If the retained GHCR package is private and local CLI lacks package scopes, use the trusted Actions token through an existing official one-job runner installation. This needs the existing repository-authorized `gh` login, not a new package PAT. Commit/push the exact reviewed builder branch first.

```sh
python3 scripts/toolchain_actions.py start --operation restore-registry \
  --runner-dir /home/pixi/Projects/Jerkgram/Desktop/d1-ephemeral-runner \
  --evidence /path/to/new/recovery-runner-evidence
```

This dispatches the already registered `linux-preflight.yml` with manual retention selected, calling the dedicated toolchain job on this branch. It pulls/checks the pinned toolchain; it cannot trigger product compilation or access API Secrets. The ephemeral listener survives chat/tool interruptions and accepts one job. Inspect Actions completion and then:

```sh
python3 scripts/toolchain_actions.py cleanup --state /path/to/new/recovery-runner-evidence/runner.json
python3 scripts/toolchain.py inspect
```

The same helper with `--operation publish` creates the versioned registry copy once. It refuses existing runner registrations, an uncommitted/unpushed workflow or arbitrary operations. Runner registration and Actions package tokens are not printed or stored in builder/evidence. Cleanup verifies removal of registration credential files. Do not run untrusted branch code on this runner.
