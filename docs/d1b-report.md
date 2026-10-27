# D1B — Jerkgram Desktop identity alpha: final local candidate

Updated: 2026-10-27 (Europe/Moscow).

**SOURCE PASS + CONFIG PASS + RELEASE TARGET COMPILED + RUNTIME COEXISTENCE PASS + PACKAGE PASS.**

D1B is closed for the local manual-update alpha. GitHub Actions is **not green**: the compile runner lost communication and abandoned the job. Successful local target completion is proven independently and distinguished below. No product feature work or D2 publication was performed.

## 1. Builder commits and provenance

Repository: `ghostbase-sg/jerkgram-desktop-builder`; branch `d1/identity-alpha`.

- `116b742b2f185237436fd85ba1a25bbd6ecc176d` — initial bounded identity/materializer/configuration gates.
- `d54ec4f597a63d537858128ad9e76fd256a0df56` — verify effective static Qt/LTO flags across upstream dependent CMake options.
- `7c95667e6ead318bd6479d07ea9b5a8a26f5bf05` — final product source/configuration used to compile the candidate, correcting inherited official-client welcome/About copy; runtime and packaging tools.
- `c4a225bc3425d3170c49a252933649c67f9fba62` — verified tray/updater runtime probes and regression coverage; clean packager revision.

The final report commit changes documentation only. The artifact manifest distinguishes compile builder SHA from packager SHA and records `builder_dirty=false` at packaging. Full materialized Telegram source was not committed.

Pinned upstream: `telegramdesktop/tdesktop`, `v7.3.1`, `6fed91ffab9861771a75f29df65031b3c80b6941`; forty recursive pinned submodules. Separate source/build: `/home/pixi/Projects/Jerkgram/Desktop/telegram-desktop-d1`. D0 was retained separately.

## 2. Exact patches, materializers and payloads

| Patch | Owned changes |
| --- | --- |
| `patches/0001-linux-identity.patch` | Linux output_name Jerkgram; Qt name/display; desktop/Gio ID; owned install integration |
| `patches/0002-profile-isolation.patch` | Own portable/XDG selectors; remove Telegram legacy adoption/fallback/cwd migration; own webview socket prefix |
| `patches/0003-product-surfaces.patch` | Product/title/menu/About/presentation identity; explicitly independent client wording |
| `patches/0004-integration-policy.patch` | Suppress startup URL default takeover; disabled update actions never open official binaries; own desktop resource; absolute launcher executable |

`D1_CONFIG.json` pins order, input/postimage inventory, patch and payload hashes, configuration and identity. `scripts/identity.py` verifies pristine input versus exact materialized output, stages the complete overlay before writes, rejects partial/dirty/tampered/wrong-pin/symlink/ignored-source inputs and verifies repeated materialization without stacking patches. The state marker lives in Git metadata. It does not bypass cleanliness verification.

`scripts/generate_identity_header.py` supplies presentation identity; `scripts/generate_linux_icons.py` deterministically derives Linux assets. `scripts/release.py` verifies source and actual generated static Qt/LTO/update-disable settings before building. `scripts/runtime_smoke.py` and `scripts/updater_runtime_probe.py` supply synthetic runtime evidence. `scripts/install_linux.py` is an opt-in owned-path installer with dry-run default. `scripts/package_release.py` strips a staging copy and creates an allowlisted archive/provenance.

Brand master: user-approved **JerkgramGlassReveal.icon**. Canonical `Plane.svg`, `Oval.svg`, `icon.json` and `APPROVAL.json` reside under `payloads/linux-identity/master`. Flattening preserves canonical vector geometry/colors and derives sRGB gradient colors; Apple glass lighting is not simulated. Upstream service/intro illustration and unrelated protocol imagery were retained.

Materialized payload inventory (23; exact hashes in `D1_CONFIG.json`):

| Builder payload | Source target |
| --- | --- |
| `payloads/linux-identity/com.jerkgram.desktop.desktop` | `lib/xdg/com.jerkgram.desktop.desktop` |
| `payloads/linux-identity/com.jerkgram.desktop.service` | `lib/xdg/com.jerkgram.desktop.service` |
| `payloads/linux-identity/com.jerkgram.desktop.metainfo.xml` | `lib/xdg/com.jerkgram.desktop.metainfo.xml` |
| `payloads/linux-identity/jerkgram_identity.h` | `Telegram/SourceFiles/core/jerkgram_identity.h` |
| `payloads/linux-identity/generated/icon128.png` | `Telegram/Resources/art/icon128.png` |
| `payloads/linux-identity/generated/icon128@2x.png` | `Telegram/Resources/art/icon128@2x.png` |
| `payloads/linux-identity/generated/icon16.png` | `Telegram/Resources/art/icon16.png` |
| `payloads/linux-identity/generated/icon16@2x.png` | `Telegram/Resources/art/icon16@2x.png` |
| `payloads/linux-identity/generated/icon256.png` | `Telegram/Resources/art/icon256.png` |
| `payloads/linux-identity/generated/icon256@2x.png` | `Telegram/Resources/art/icon256@2x.png` |
| `payloads/linux-identity/generated/icon32.png` | `Telegram/Resources/art/icon32.png` |
| `payloads/linux-identity/generated/icon32@2x.png` | `Telegram/Resources/art/icon32@2x.png` |
| `payloads/linux-identity/generated/icon48.png` | `Telegram/Resources/art/icon48.png` |
| `payloads/linux-identity/generated/icon48@2x.png` | `Telegram/Resources/art/icon48@2x.png` |
| `payloads/linux-identity/generated/icon512.png` | `Telegram/Resources/art/icon512.png` |
| `payloads/linux-identity/generated/icon512@2x.png` | `Telegram/Resources/art/icon512@2x.png` |
| `payloads/linux-identity/generated/icon64.png` | `Telegram/Resources/art/icon64.png` |
| `payloads/linux-identity/generated/icon64@2x.png` | `Telegram/Resources/art/icon64@2x.png` |
| `payloads/linux-identity/generated/logo_256.png` | `Telegram/Resources/art/logo_256.png` |
| `payloads/linux-identity/generated/logo_256_no_margin.png` | `Telegram/Resources/art/logo_256_no_margin.png` |
| `payloads/linux-identity/generated/tray_monochrome.svg` | `Telegram/Resources/icons/tray_monochrome.svg` |
| `payloads/linux-identity/generated/tray_monochrome_attention.svg` | `Telegram/Resources/icons/tray_monochrome_attention.svg` |
| `payloads/linux-identity/generated/tray_monochrome_mute.svg` | `Telegram/Resources/icons/tray_monochrome_mute.svg` |

## 3. Source paths changed by materialization

Exactly 36 changed/added paths; all postimages verified:

- `Telegram/CMakeLists.txt`
- `Telegram/Resources/art/icon128.png`
- `Telegram/Resources/art/icon128@2x.png`
- `Telegram/Resources/art/icon16.png`
- `Telegram/Resources/art/icon16@2x.png`
- `Telegram/Resources/art/icon256.png`
- `Telegram/Resources/art/icon256@2x.png`
- `Telegram/Resources/art/icon32.png`
- `Telegram/Resources/art/icon32@2x.png`
- `Telegram/Resources/art/icon48.png`
- `Telegram/Resources/art/icon48@2x.png`
- `Telegram/Resources/art/icon512.png`
- `Telegram/Resources/art/icon512@2x.png`
- `Telegram/Resources/art/icon64.png`
- `Telegram/Resources/art/icon64@2x.png`
- `Telegram/Resources/art/logo_256.png`
- `Telegram/Resources/art/logo_256_no_margin.png`
- `Telegram/Resources/icons/tray_monochrome.svg`
- `Telegram/Resources/icons/tray_monochrome_attention.svg`
- `Telegram/Resources/icons/tray_monochrome_mute.svg`
- `Telegram/Resources/qrc/telegram/telegram.qrc`
- `Telegram/SourceFiles/boxes/about_box.cpp`
- `Telegram/SourceFiles/core/application.cpp`
- `Telegram/SourceFiles/core/jerkgram_identity.h`
- `Telegram/SourceFiles/core/launcher.cpp`
- `Telegram/SourceFiles/core/update_checker.cpp`
- `Telegram/SourceFiles/core/version.h`
- `Telegram/SourceFiles/intro/intro_start.cpp`
- `Telegram/SourceFiles/logs.cpp`
- `Telegram/SourceFiles/platform/linux/main_window_linux.cpp`
- `Telegram/SourceFiles/platform/linux/specific_linux.cpp`
- `Telegram/SourceFiles/window/main_window.cpp`
- `Telegram/SourceFiles/window/window_main_menu.cpp`
- `lib/xdg/com.jerkgram.desktop.desktop`
- `lib/xdg/com.jerkgram.desktop.metainfo.xml`
- `lib/xdg/com.jerkgram.desktop.service`

No global Telegram replacement. Internal project/target `Telegram`, internal C++ types, protocol/service identifiers, tdata layout, upstream tracked AGENTS.md and numeric/string upstream build version are retained. The two-string correction was staged against pristine pinned preimages and applied only after verifying the old materialization; out/objects/libraries were preserved.

## 4. Final identity values

| Surface | Value |
| --- | --- |
| Display / long name | Jerkgram / Jerkgram Desktop |
| Binary | Jerkgram; internal CMake project/target Telegram |
| Qt applicationName / displayName | JerkgramDesktop / Jerkgram |
| Runtime desktop/Gio/Wayland ID | com.jerkgram.desktop |
| Desktop file / icon basename | com.jerkgram.desktop.desktop / com.jerkgram.desktop |
| D-Bus activation service | com.jerkgram.desktop |
| X11 StartupWMClass / actual class | JerkgramDesktop |
| Normal profile | $XDG_DATA_HOME/JerkgramDesktop/tdata |
| Portable profile | adjacent JerkgramForcePortable/tdata |
| Explicit advanced override | -workdir retained |
| Downloads default | Downloads/Jerkgram |
| MPRIS namespace (source) | org.mpris.MediaPlayer2.JerkgramDesktop |
| Own presentation version | 0.1.0-alpha.1 |
| Upstream protocol/build values | AppVersion=7003001; AppVersionStr=7.3.1 |
| Updater | explicitly disabled; manual releases only |

## 5. Profile isolation proof

SOURCE: `core/launcher.cpp::CheckPortableVersionFolder`, `logs.cpp::Logs::start`, Linux `psAppDataPath` and download path owners use the owned selectors. No .TelegramDesktop fallback, Telegram alpha/beta/portable adoption or Linux legacy cwd migration remains. Explicit -workdir is preserved.

RUNTIME: X11, native Wayland and extracted-package tests use new synthetic HOME/XDG roots on a private bus. Seeded .TelegramDesktop, XDG TelegramDesktop, legacy cwd data/config/tdata and adjacent TelegramForcePortable/TelegramAlpha_data/TelegramBeta_data sentinels retain hashes and mtimes. Jerkgram creates its own default tdata; separate tests prove JerkgramForcePortable and -workdir selection. Synthetic adjacent fixtures were removed after passing. Real user Telegram profiles were never inspected, migrated or used.

## 6. URL handler and integration policy proof

SOURCE: the startup call to autoRegisterUrlScheme is removed; explicit registration capability and tg/ton/tonsite protocols are retained. The optional installer writes own desktop/service/hicolor files, uses the actual absolute executable path, does not delete official Telegram entries and does not set MIME defaults.

RUNTIME: pre-seeded mimeapps defaults for all three protocols and an official desktop-file sentinel remain unchanged after fresh Jerkgram startup. Installer fixture tests independently check owned-path dry-run/apply behavior. No installation into the user's real desktop directories was performed.

## 7. Updater-disable proof

CONFIG: explicit `DESKTOP_APP_DISABLE_AUTOUPDATE=ON`; generated identity header refuses compilation without `TDESKTOP_DISABLE_AUTOUPDATE`. `core/update_checker.cpp` initializes `UpdaterIsDisabled=true`. `core/sandbox.cpp::Sandbox::start` creates UpdateChecker only when not disabled; application MTProto updater binding and startup ready-update handling have the same guard. No endpoint or signing-key substitution was made.

UI: `Core::UpdateApplication` returns safely when disabled. Version/footer actions open local About/manual-release information; no official Telegram download is presented as a Jerkgram upgrade. Telegram API/GPL/source attribution remains.

RUNTIME: `/home/pixi/Projects/Jerkgram/Desktop/d1-evidence/updater-probe.json` records **zero HTTP discovery start, zero MTP discovery start and zero UpdateChecker construction** during 35 seconds at a synthetic unauthenticated welcome. GDB breakpoints observe the actual Release executable using minimal symbols without DWARF loading. Observed process name: Jerkgram; no Updater/Packer observed. `-installupdate` exits nonzero with “Automatic updates are disabled” on X11, Wayland and extracted-package tests. No update package was installed. This observation is explicitly bounded to welcome; authenticated traffic is not claimed.

## 8. Actual build scope, duration and completion evidence

Official existing image: `sha256:f8254a3af4ff32abc7cb5b5519f150d84e0df7a5fffe8cf50a2e25a20e2f8d9a` (`tdesktop:centos_env`). Release; static Qt Core/Gui/Widgets verified in generated edge; existing image-provided GCC compile LTO; final `-flto=1 --param=lto-max-streaming-parallelism=1`. No global CMAKE_CXX_FLAGS edits, generated Ninja edits, clean/cache deletion or D0 rebuild.

- Earlier attempt 40229101552 stopped at 207/2378 after 1,070.82 seconds. Journal evidence was SIGTERM then forced container stop; it is not classified as OOM.
- Initial resumed D1 target 40405894480 reused those objects, completed 2171 remaining operations in 17,727.622 seconds; link 5,182.129 seconds. A valid initial ELF and X11 coexistence passed. Visual inspection found two inherited “official” strings, so this was not the final candidate. Its binary and all evidence were preserved under out/Release/Jerkgram.initial-unstripped and d1-evidence-initial-20261027.
- Final follow-up 40445628539 rebuilt **only intro_start.cpp and about_box.cpp**, plus normal tiny generated checks, then linked. No library or mass .cpp recompilation. Ninja target campaign: **7241.872 seconds (2h00m41.872s)**; link: **7231.145 seconds (2h00m31.145s)**.

The final successful `Release/Jerkgram` record in out/.ninja_log is preserved in build.json, with `link_exit_code=0`. ELF metadata, hash, current source/config verification and actual runtime independently confirm the target. The runner later reported SSL/communication failure and **Abandoned**; GitHub concluded **cancelled**. The aggregate campaign exit was not captured (`campaign_exit_code=null`). This is **not a green Actions result**. It was not hidden or repaired by launching another long rebuild.

## 9. Measured LTO resources

Final follow-up, host samples every three seconds:

- Peak host used (MemTotal minus MemAvailable): **31,259,123,712 bytes / 29.11 GiB**.
- Peak logical zram swap used: **12,304,707,584 bytes / 11.46 GiB**. Peaks need not coincide; swap is not zram's physical RAM allocation.
- Peak simultaneous lto1 variants: **1**. No lto1-wpa-stream subprocess was observed; serial WPA/ltrans work was observed, consistent with the one-worker configuration.
- Exact kernel completion window contained no OOM-kill record. No OOM cause is asserted for runner communication failures.

## 10. Unstripped binary

`/home/pixi/Projects/Jerkgram/Desktop/telegram-desktop-d1/out/Release/Jerkgram`

**3,340,342,992 bytes**; SHA256 `00fccd4abd483d29eb3838ddc2485f6d36b2b751fdd5c1380d65f973ec4ea35b`.

ELF64 x86-64 PIE, debug_info retained, GNU/Linux interpreter /lib64/ld-linux-x86-64.so.2; BuildID `9239f9c5042593767e0dda5d2521b93d8ba94aa5`. Static Qt does not mean fully static glibc/Pango/Cairo/system dependencies; host ldd resolved all needed system libraries.

## 11. Stripped binary

**250,364,512 bytes**; SHA256 `ff2e2eaf3b86cce73c6bb60d86ac813f24ae5d47bdfe98d0d30f603911aecb74`. Only staging copy was stripped; original ELF hash remained unchanged. The extracted stripped executable passed the same synthetic X11 coexistence/identity/profile/updater checks.

## 12. Archive size and checksum

`jerkgram-desktop-0.1.0-alpha.1-linux-x86_64.tar.xz` — **78,191,584 bytes**.

SHA256: `ee25953e73e2c86ad85b8eff1902c8e2b53399e6eb0c12ea1f702ce5df587924`.

Archive validated: 89 regular file members; no links or path escapes. Contains executable, explicit Linux integration assets/installer, README, LICENSE/LEGAL/NOTICE and 64 tracked pinned-source notice/license files. No profiles/tdata, Updater/Packer, credential files, logs, build intermediates or Git metadata. Untracked credential-like notice files are excluded by tracked-file collection and regression tests. Required client API configuration stays compiled into the executable; credential environment/cache/source files are not release members.

## 13. Artifact and evidence paths

Artifact directory: `/home/pixi/Projects/Jerkgram/Desktop/d1-artifacts/0.1.0-alpha.1-candidate-20261027`.

- Archive: `/home/pixi/Projects/Jerkgram/Desktop/d1-artifacts/0.1.0-alpha.1-candidate-20261027/jerkgram-desktop-0.1.0-alpha.1-linux-x86_64.tar.xz`.
- Checksums: `/home/pixi/Projects/Jerkgram/Desktop/d1-artifacts/0.1.0-alpha.1-candidate-20261027/SHA256SUMS`.
- Provenance/build manifest: `/home/pixi/Projects/Jerkgram/Desktop/d1-artifacts/0.1.0-alpha.1-candidate-20261027/manifest.json` (compile builder SHA, packager SHA, upstream, config, overlay/payload digests, updater policy, image/configuration, binary/archive hashes and sizes).
- Evidence: `/home/pixi/Projects/Jerkgram/Desktop/d1-evidence` — config-verified.json, build.json, compile.log, memory.jsonl, updater-probe.*, package-validation.json and runtime-xcb/runtime-wayland/runtime-package reports/screenshots.

No artifact was published to a public Release, and no release repository was created.

## 14. Runtime coexistence result

| Gate | X11 / Xwayland | Native Wayland | Extracted stripped package |
| --- | --- | --- | --- |
| Fresh welcome launch / no immediate crash | PASS | PASS | PASS (X11) |
| Same private bus with stock D0, independent processes | PASS | PASS | PASS |
| Independent repeated launch and live Gio Activate | PASS | PASS | PASS |
| Own default/portable/-workdir profiles | PASS | PASS | PASS |
| Legacy Telegram and startup URL-default sentinels | PASS | PASS | PASS |
| Class / app_id | JerkgramDesktop | com.jerkgram.desktop | JerkgramDesktop |
| Own Gio identity | com.jerkgram.desktop | com.jerkgram.desktop | com.jerkgram.desktop |
| Stock identity | org.telegram.desktop | org.telegram.desktop | org.telegram.desktop |
| Tray Id/Title / tooltip | JerkgramDesktop / Jerkgram | same | same |
| Disabled installupdate refusal | PASS | PASS | PASS |

Identity logs retain upstream Launched version 7003001 and record own executable, data root and App ID. Each successful harness cleaned up only the exact synthetic adjacent folders it created. Test applications were terminated. D0 Git status remains clean, D0 binary remains 3,340,519,960 bytes with its original 2026-10-25 modification time. Original Docker image/out/evidence remain.

## 15. About and welcome evidence

Visually inspected actual screenshots:

- `/home/pixi/Projects/Jerkgram/Desktop/d1-evidence/runtime-xcb/about.png` — Jerkgram Desktop, version 0.1.0-alpha.1, “Based on Telegram Desktop 7.3.1”, independent client/API/GPL attribution.
- `/home/pixi/Projects/Jerkgram/Desktop/d1-evidence/runtime-wayland/welcome.png` — Jerkgram Desktop and independent-client text; actual native app_id captured separately.
- `/home/pixi/Projects/Jerkgram/Desktop/d1-evidence/runtime-package/about.png` — same identity from extracted stripped candidate.

Native Wayland did not export the global-menu About action on this host; About was verified on X11, including the packaged executable. No claim of Wayland-specific About activation is made. Upstream intro illustration was deliberately retained; owned app/hicolor/tray assets come from the approved Reveal master.

## 16. Remaining coverage and limitations

- MPRIS playback and authenticated media/notification behavior require a controlled authenticated account and remain pending; no login was requested or simulated. Source MPRIS namespace is owned. Welcome HTTP/MTP discovery probe does not assert later authenticated traffic observation.
- Actions runner communication/SSL reliability requires a separate investigation before relying on automated release CI. Both target completions and failed/cancelled workflow conclusions remain recorded honestly. Latest ephemeral registration/credential files were removed; GitHub runner count is zero.
- Other Linux distributions and clean-room reproduction were not runtime-tested here; actual runtime host is this Arch/Hyprland laptop, compilation used the pinned official container.
- Public source export/release publication is D2, not performed here.

Verification: **20 builder tests pass**, hash/materialization/configuration verification passes, package checksum/inventory passes, X11/Wayland/extracted-package runtime passes. Account-dependent pending coverage does not replace any claimed baseline gate.

## 17. Exact D2 recommendation

Next milestone: **D2 — public release/source export**, only after explicit authorization. Export the exact verified materialized source including owned new files and pinned dependency/toolchain provenance; do not use bare upstream git archive. Exclude .git/out, local agent overrides, API credential configuration, profiles and evidence logs. Include required notices and corresponding source/build instructions. Validate clean-room reproduction and the distribution's actual system dependencies, resolve CI runner reliability, then create/publish to jerkgram/Jerkgram-Desktop with versioned tar.xz, checksums, provenance and source assets.

Keep manual updates until separate signed Jerkgram infrastructure is implemented and reviewed. No product features start automatically. D0, user data, credentials and remotes were preserved; this milestone did not implement deleted messages, ghost mode or other product features.
