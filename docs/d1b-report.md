# D1B — Jerkgram Desktop identity alpha

Status: **IN PROGRESS — SOURCE PASS / CONFIG PASS / INITIAL RELEASE LINK RECORDED / INITIAL X11 COEXISTENCE PASS / TWO-STRING FOLLOW-UP REQUIRED**.

This is the same Work Local campaign. D0 and builder foundation were not repeated. No Jerkgram product feature work is part of this milestone.

## 1. Builder commits

Development branch: `d1/identity-alpha` in `ghostbase-sg/jerkgram-desktop-builder`.

- `116b742b2f185237436fd85ba1a25bbd6ecc176d`: bounded identity overlay, approved assets, materializer and Release gates.
- `d54ec4f597a63d537858128ad9e76fd256a0df56`: corrected verification of actual static Qt and LTO flags.
- Runtime harness, tracked notice collection and the two-string visual correction are verified locally; final rebuilt/runtime evidence remains pending.

Active compile workflow: https://github.com/ghostbase-sg/jerkgram-desktop-builder/actions/runs/40405894480

## 2. Patches, materializer and payloads

`patches/series` declares exactly four ordered patches:

| Patch | Scope |
| --- | --- |
| 0001-linux-identity.patch | Linux output name, Qt name/display, desktop ID, owned CMake install integration |
| 0002-profile-isolation.patch | Remove Telegram profile fallbacks/adoption, own portable folder and webview socket prefix, no legacy cwd migration |
| 0003-product-surfaces.patch | Own product labels, About presentation version and upstream attribution |
| 0004-integration-policy.patch | No automatic URL-default takeover; local About instead of upgrade links; own desktop resource and absolute shortcut executable |

`scripts/identity.py` validates pin, patch order/hashes, all preimages before writes, staged patch/postimage inventory, payload hashes and exact materialized output. Wrong/partial/dirty/tampered trees fail closed. The overlay state lives in Git metadata. Repeat execution verifies the same output. Existing build output is rejected on initial materialization; a previously verified materialization may retain its own out directory. Ignored source inputs are rejected outside the allowed out tree, including unexpected inputs inside submodules.

`D1_CONFIG.json` is the exact source-file/postimage/patch/payload inventory. Presentation header is generated from `JERKGRAM_VERSION` and pinned upstream identity.

Brand source: user-approved `JerkgramGlassReveal.icon`; canonical Plane.svg/Oval.svg/icon.json and approval provenance in `payloads/linux-identity/master`. The flat Linux rendering keeps canonical vector geometry and derives sRGB gradient colors from the recipe; it does not simulate Apple's glass effects. Payloads include two 256px logos, fourteen icon PNG size/scale variants, three symbolic tray variants, desktop/service/AppStream integration and the generated identity header. Generated PNG dimensions and SVG/XML syntax passed verification.

## 3. Materialized source

Separate checkout: `/home/pixi/Projects/Jerkgram/Desktop/telegram-desktop-d1`.

Pinned upstream: `telegramdesktop/tdesktop`, `v7.3.1`, `6fed91ffab9861771a75f29df65031b3c80b6941`; forty pinned submodules reused through local Git clones. No full materialized source was committed.

Exactly 36 source paths are changed or added; see `D1_CONFIG.json` files map. Owners include Telegram/CMakeLists.txt; core/launcher.cpp, version.h, application.cpp, update_checker.cpp; logs.cpp; Linux specific/main_window; intro_start.cpp; About/main-window/main-menu; telegram.qrc; own xdg templates; logos/icons and the new presentation header. Internal CMake project/target Telegram, upstream version constants, protocol/service identifiers, internal tdata format and tracked upstream AGENTS.md are retained.

Protected D0 checkout remains `/home/pixi/Projects/Jerkgram/Desktop/telegram-desktop`; its out, binary, Docker image and evidence are not materialization targets.

## 4. Final identity configuration

| Surface | Value |
| --- | --- |
| Product / long name | Jerkgram / Jerkgram Desktop |
| Executable | Jerkgram; internal target remains Telegram |
| Qt applicationName / display name | JerkgramDesktop / Jerkgram |
| Desktop/Gio/Wayland ID | com.jerkgram.desktop |
| Desktop file | com.jerkgram.desktop.desktop |
| D-Bus activation service | com.jerkgram.desktop |
| Icon basename / StartupWMClass | com.jerkgram.desktop / JerkgramDesktop |
| Default profile | XDG_DATA_HOME/JerkgramDesktop/tdata |
| Portable profile | adjacent JerkgramForcePortable/tdata |
| Normal downloads | Downloads/Jerkgram |
| MPRIS namespace | org.mpris.MediaPlayer2.JerkgramDesktop |
| Presentation version | 0.1.0-alpha.1 |
| Upstream version | AppVersion=7003001; AppVersionStr=7.3.1 |
| Updater policy | explicitly disabled; manual releases only |

## 5. Profile isolation proof

SOURCE: psAppDataPath no longer consults .TelegramDesktop; Telegram alpha/beta folder migration is removed; only JerkgramForcePortable is recognized; Linux cwd legacy migration is bypassed. Explicit -workdir remains supported. RUNTIME: pending compiled binary, synthetic HOME/XDG and seeded legacy fixtures. Real user profiles are not test fixtures.

## 6. URL-handler policy proof

SOURCE: startup/fresh-profile call to autoRegisterUrlScheme is removed; explicit registration capability remains. Protocols tg/ton/tonsite are unchanged. The explicit integration installer writes only owned paths and never sets MIME defaults or deletes Telegram entries. Behavioral installer tests prove dry-run isolation and unchanged official launcher/default fixtures. Application startup runtime comparison remains pending.

## 7. Updater proof

SOURCE/CONFIG: DESKTOP_APP_DISABLE_AUTOUPDATE=ON is explicit; generated header refuses compilation without its macro. Official endpoints/signing keys are not substituted. No Updater/Packer production target is enabled. Disabled update UI does not send the user to official binaries as Jerkgram upgrades; product/version footer opens local About. Supported crash-report disablement is also explicit for alpha.

Generated Release edge verifies static Qt Core/Gui/Widgets, actual compiler LTO and final -flto=1 plus --param=lto-max-streaming-parallelism=1. The dependent CMake option/cache type is not used as a false proxy for actual linkage.

RUNTIME: safe -installupdate refusal and helper/discovery checks pending. Authenticated MTP/notification behavior will not be inferred from welcome-only testing.

## 8–9. Build scope, duration and resources

First compile attempt (40229101552) stopped at 207/2378 with Docker exit 137 after 1070.82 seconds. Host journal shows SIGTERM followed by forced stop after ten seconds; this is not evidence of OOM. Previous peak host used memory: 20,157,706,240 bytes; swap: 200,704 bytes. Its evidence was preserved separately.

Current attempt is incremental with the same credentials/configuration and original image ID `sha256:f8254a3af4ff32abc7cb5b5519f150d84e0df7a5fffe8cf50a2e25a20e2f8d9a`. It reused the prior 207 operations and scheduled 2171 remaining. No clean, cache removal, generated Ninja edits or D0 output copying. Two compile jobs; one LTO worker per link. Live host metrics include lto1 variants, g++, ld, MemAvailable and zram swap; final peak/duration pending.

## 10–13. Candidate artifacts

Unstripped binary: planned `telegram-desktop-d1/out/Release/Jerkgram`; size and ELF verification pending.

Stripped binary size, tar.xz size, SHA256 and artifact path: pending successful compile and packaging.

Packager strips a staging copy only and uses an explicit inventory. It rejects undeclared/symlink assets; untracked credential-like files cannot enter the notice bundle. It includes 64 tracked pinned-source license/notice files, required upstream notices and own integration resources. No profiles, Updater/Packer, credentials, logs, source build intermediates or .git are release members. Provenance separates the build workflow commit from the packager commit, and records upstream/config/overlay/payload identities and actual binary/archive hashes/sizes. Packaging unit tests use a tiny ELF fixture and are not a claim about the unfinished Telegram binary.

## 14–15. Runtime coexistence and About/welcome

Pending. `scripts/runtime_smoke.py` is a synthetic-only harness for one shared private bus, independent stock/Jerkgram processes/profiles, repeated launch, live Gio activation, X11/Wayland metadata, legacy/default-handler sentinels, portable/workdir selection and updater refusal. The test menu registrar passed independently. Actual application screenshots and visual verification await the compiled binary.

## 16. Remaining gates

- Complete Release compile/link; record exit status, binary metadata and resources.
- Run actual synthetic runtime coexistence and inspect About/welcome captures.
- Package and validate the actual stripped candidate.
- Mark account/notifier-dependent coverage precisely; do not claim those checks from an unauthenticated welcome screen.
- Commit/push final verified owned changes and evidence report.
- Confirm ephemeral runner registration/credentials cleanup.

D1B must not be marked complete until SOURCE + CONFIG + RELEASE COMPILE + RUNTIME COEXISTENCE pass.

## 17. D2 recommendation

After D1B passes: authorize a separate public release/source-export milestone. Export the verified materialized working tree including owned new files, not bare upstream git archive; exclude .git/out, local agent overrides, API credentials, profiles and evidence logs. Record dependency/toolchain/source provenance and complete distribution notices/source obligations, validate clean-room reproduction and artifact contents, then create/publish to jerkgram/Jerkgram-Desktop only with explicit authorization. Keep manual updates until separately signed Jerkgram update infrastructure exists. No product feature milestone starts automatically.

## Visual follow-up

The initial X11 candidate passed synthetic coexistence. Screenshot inspection found inherited intro/About copy claiming official status. The follow-up changes only these two text owners, with no generated language table changes. API/GPL attribution remains. Current source hashes therefore require a new incremental compile/link before candidate closure. Initial workflow failure records runner communication loss; it is not a successful Actions run.
