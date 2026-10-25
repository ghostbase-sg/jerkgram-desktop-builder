# D1A — Linux identity audit and bounded D1 implementation plan

Date: 2026-10-25. Status: **SOURCE AUDIT COMPLETE; D1 IMPLEMENTATION NOT STARTED**.

## Scope and evidence

D0 and builder foundation remain closed. This audit read the materialized source and builder scripts; it did not launch an application, configure CMake, run Ninja, compile, package, inspect user profiles or change product files. Runtime coexistence remains a future acceptance gate.

- Builder starting revision: `7c0f725363e40414a6e28ae28cf7737493be7c77`, repository `ghostbase-sg/jerkgram-desktop-builder`.
- Source: `telegramdesktop/tdesktop`, tag `v7.3.1`, commit `6fed91ffab9861771a75f29df65031b3c80b6941`, local branch `jerkgram/7.3.1`; tracked working tree clean at inspection.
- Source workspace: `/home/pixi/Projects/Jerkgram/Desktop/telegram-desktop`.
- Gitlinks relevant to conclusions: `Telegram/lib_base` = `de35c7abcbf6464a0845695a55568bdac12a5fba`; `Telegram/lib_ui` = `91ff4463899f23f4227bc4cbbdbe7696d479b9bd`; `cmake` = `699262e441dbc6270f0ba6cc74f2e7a8e4c7e422`.

Paths below are relative to the source root unless marked **builder**. Symbols and exact literals identify evidence without drifting line numbers. Root files can be inspected at the [immutable upstream snapshot](https://github.com/telegramdesktop/tdesktop/tree/6fed91ffab9861771a75f29df65031b3c80b6941). Submodule evidence belongs to its pinned gitlink, not to a presumed copy in the root repository.

### Main conclusions

1. A desktop-ID change alone is insufficient: profile fallback, Qt application name, single-instance sockets, MPRIS and URL-handler registration have separate owners.
2. Use the supported `DESKTOP_APP_DISABLE_AUTOUPDATE=ON`. Endpoint substitution or `-noupdate` is insufficient. HTTP and MTP discovery both exist.
3. Disabled updater also disables automatic portable launcher installation. Supply explicit, Jerkgram-owned integration rather than re-enabling upstream `InstallLauncher()` wholesale.
4. Remove all automatic adoption/migration of Telegram profiles, including legacy files in the initial current directory. Keeping the internal `tdata` layout under a separate root is safe; renaming every `tdata` token is unnecessary.
5. Keep Telegram build/protocol version integers separate from Jerkgram presentation/release version.

## 1. Product/display identity owners

| Owner / symbol | Stock value and consumers | D1 decision |
| --- | --- | --- |
| `Telegram/SourceFiles/core/version.h`: `AppName` | `Telegram Desktop`; tray tooltip (`tray.cpp`), hidden notification title (`window/notifications_manager.cpp`), notification settings title (`settings/sections/settings_notifications.cpp`), GLib/PulseAudio identity (`Platform::start()`), notification sender, media controls, normal download folder | Product display `Jerkgram`; About title can be `Jerkgram Desktop` separately |
| Same header: `AppFile` | `Telegram`; spellchecker initialization in `chat_helpers/spellchecker_common.cpp`; Windows executable/autostart consumer | Align executable-related constant deliberately; do not mistake it for Linux output-name owner |
| `core/launcher.cpp`: `Launcher::init()` | `QApplication::setApplicationName("TelegramDesktop")` before application construction | `JerkgramDesktop`, separate from display name; affects paths, X11 class, sockets, MPRIS |
| `window/main_window.cpp`: `MainWindow::updateTitle()` | Default title `Telegram`; otherwise account/chat/media title plus unread counter/native suffix | Change only default product title; preserve account/chat logic |
| `intro/intro_start.cpp`: `StartWidget` constructor | Welcome title `Telegram Desktop` | `Jerkgram Desktop` |
| `boxes/about_box.cpp`: `AboutBox()`, `Text1/2/3()`, `CurrentVersionText()` | Hardcoded About title; upstream version; API/GPL/source/FAQ links; version click opens upstream changelog or private alpha link | Add own presentation version and upstream attribution; replace release/source destination where appropriate, retain upstream credit/legal/service links |
| `window/window_main_menu.cpp`: footer setup | `Telegram Desktop` link to `https://desktop.telegram.org`, version via `currentVersionShortText()`, changelog/About links | Own product/version/footer destination; retain `_telegram` member/style names |
| `platform/linux/main_window_linux.cpp`: `MainWindow::createGlobalMenu()` | Quit/About action labels pass `Telegram` through `lt_telegram` | Replace those product placeholders only |
| Root `CMakeLists.txt`: `project(Telegram ...)` | Description `Official Telegram Desktop messenger`, homepage `https://desktop.telegram.org`; build project identifier is internal | Adjust descriptive metadata if exported; keep project/target identifier |
| `lib/xdg/org.telegram.desktop.desktop`, `.metainfo.xml` | Launcher name/comment/quit action; AppStream name, developer, URLs, screenshot/release metadata | Own launcher and optional AppStream payload; do not claim Telegram FZ-LLC is Jerkgram publisher |

There is no single product-name switch. Translation resources (`Telegram/Resources/langs/lang.strings`, cloud packs and generated language keys) also contain service-facing Telegram references. Do not mass-rebrand service/legal/API text or mutate generated translation keys. For D1, route the explicit product surfaces above through a small Jerkgram identity definition. Review translated About body text as attribution, not an instruction to rename Telegram the service.

## 2. Executable naming path

- `Telegram/CMakeLists.txt`: `add_executable(Telegram WIN32 MACOSX_BUNDLE)` is the internal target. The non-Mac-store branch sets `output_name` to `Telegram`; `set_target_properties(Telegram ... OUTPUT_NAME ${output_name})` owns the filesystem name.
- The same file computes `output_folder`: Apple, multi-config generators, executable suffixes, or an output name other than `Telegram` select `${CMAKE_BINARY_DIR}`; otherwise single-config Linux uses `${CMAKE_BINARY_DIR}/bin`. Config-specific placement then follows the generator. Do not assume every configuration produces the D0 path.
- Minimal Linux change: set the Linux output name to `Jerkgram`, retaining target `Telegram`, `$<TARGET_FILE:Telegram>` references and the CMake project name. Verify the resulting path for the chosen Release generator.
- `SourceFiles/settings.h`: `cExeName()/cExeDir()` delegate to `base::Integration`. `Telegram/lib_base/base/integration.cpp`: `Integration::Integration()` resolves `Platform::CurrentExecutablePath()`, canonicalizes it and records actual basename/directory. Linux ordinary restart in `platform/linux/launcher_linux.cpp`, `Launcher::launchUpdater(JustRelaunch)`, uses that discovered path. Renaming output does not require renaming C++ types.
- Explicit assumptions remain in static `.desktop` `TryExec`, main/quit `Exec`, static `.service` `Exec`, upstream Linux packaging and update-package layout. Generated launcher functions rewrite executable paths, subject to the caveats in section 3.
- `Telegram/build/build.sh` Linux branch sets `BinaryName=Telegram`, packages `Telegram/Telegram` plus `Updater`, and invokes `PackUpdate`. `Telegram/build/docker/build.sh` also expects `Telegram`, `Updater`, `Packer` and moves outputs into `root`. Do not reuse those production packaging stages for the first Jerkgram alpha.
- `SourceFiles/_other/updater_linux.cpp` defaults `exeName` to `Telegram`, supports `-exename`, and maps the archive's `Telegram` member to an alternate executable name. `platform/linux/update_install_linux.cpp` requires exact top-level `Telegram` and `Updater` package members. A renamed executable still accepts official update identity if the updater is left enabled.
- **Builder** `scripts/builder.py`: `build_release()` currently returns `out/Release/Telegram`; `package()` stages/archive-names `Telegram` and labels it stock. These consumers must be updated deliberately in D1, not bypassed by relabeling a D0 archive.

## 3. Desktop/app ID, launcher, notification and window identity

Verified stock file: `lib/xdg/org.telegram.desktop.desktop`:

```ini
Name=Telegram
TryExec=Telegram
Exec=Telegram -- %U
Icon=org.telegram.desktop
StartupWMClass=TelegramDesktop
MimeType=x-scheme-handler/tg;x-scheme-handler/tonsite;x-scheme-handler/ton;
DBusActivatable=true
SingleMainWindow=true
X-GNOME-UsesNotifications=true
```

The quit action is `Exec=Telegram -quit`, `Name=Quit Telegram`. Categories/keywords describe a messenger; they are not unique namespaces.

### Dataflow

- `platform/linux/specific_linux.cpp`, `Platform::start()` sets `QGuiApplication::desktopFileName()`:
  - Flatpak: `FLATPAK_ID`;
  - Snap: `SNAP_INSTANCE_NAME + '_' + cExeName()`;
  - normal updater-enabled binary: `org.telegram.desktop._<Launcher::instanceHash()>`;
  - updater-disabled binary: fixed `org.telegram.desktop`.
- `Launcher::instanceHash()` in `core/launcher.cpp` is MD5 of absolute custom working directory, otherwise executable directory + name. This is **not** the single-instance hash in `Sandbox::start()`.
- `Platform::ApplicationIconName()` removes the `._<instanceHash>` suffix from the desktop ID (Snap has a separate name), yielding the stable icon theme basename.
- `specific_linux.cpp`, `GenerateDesktopFile()` reads embedded `:/misc/org.telegram.desktop.desktop`, writes `<desktopFileName>.desktop`, rewrites executable paths, preserves `%U` and adds `-workdir` for a custom profile. `GenerateServiceFile()` writes `<desktopFileName>.service`, `Name=<desktopFileName>`, `Exec=<executable>` with custom workdir if applicable.
- Static `lib/xdg/org.telegram.desktop.service` has `Name=org.telegram.desktop`, `Exec=@CMAKE_INSTALL_FULL_BINDIR@/Telegram`. `Telegram/CMakeLists.txt` configures/installs this service, `.desktop`, AppStream and hicolor icons **only for `LINUX AND DESKTOP_APP_USE_PACKAGED`**. Static dependency linking is a separate choice; do not enable packaged mode merely to obtain an install rule.
- `platform/linux/integration_linux.cpp`, local `Application::Application()` passes desktopFileName to `Gio::Application::set_application_id()`, enables `HANDLES_OPEN`, installs `quit`, and `MakeApplication()` registers it. Activation calls `Core::App().activate()`; open events feed URLs to Qt. Own application bus name must match own activation service.
- `notifications_manager_linux.cpp` sends `desktop-entry=desktopFileName`, uses `AppName` and `ApplicationIconName`; GNotification also uses the registered Gio application. Unity badge integration in `main_window_linux.cpp` uses `application://<desktopFileName>.desktop` (older Qt path; current Qt uses badge API).
- Qt separates desktop basename from display name ([QGuiApplication documentation](https://doc.qt.io/qt-6/qguiapplication.html#desktopFileName-prop)). In Qt 6.11.2, [QXcbWindow creation](https://github.com/qt/qtbase/blob/v6.11.2/src/plugins/platforms/xcb/qxcbwindow.cpp) publishes desktopFileName as `_GTK_APPLICATION_ID` and `_KDE_NET_WM_DESKTOP_FILE`; [QXcbIntegration::wmClass()](https://github.com/qt/qtbase/blob/v6.11.2/src/plugins/platforms/xcb/qxcbintegration.cpp) derives the WM_CLASS class from Qt applicationName, instance from command/environment/argv. [QWaylandWindow::initWindow()](https://github.com/qt/qtbase/blob/v6.11.2/src/plugins/platforms/wayland/qwaylandwindow.cpp) sends desktopFileName as shell app ID. These are toolkit source expectations; verify the actual patched static Qt binary at runtime.

### Integration policy

Use fixed `com.jerkgram.desktop` for the first updater-disabled alpha; `.desktop` filename `com.jerkgram.desktop.desktop`, service `com.jerkgram.desktop.service`, icon basename `com.jerkgram.desktop`. Set Qt applicationName to `JerkgramDesktop` and desktop `StartupWMClass=JerkgramDesktop`. Retain Flatpak/Snap-specific behavior outside this initial distribution scope.

**Important side effects:** `InstallLauncher()` returns early for disabled updater, alpha, sandbox, or nonempty `DESKTOPINTEGRATION`. It therefore will not install portable-alpha launcher/service/icons automatically. `ExecutablePathForShortcuts()` also switches to argv basename / cExeName rather than an absolute path when updater is disabled. A portable directory is not normally on PATH: a future explicit installer must write quoted absolute paths to its stable install location. Do not copy a bare `Exec=Jerkgram` desktop file into the user's menu and assume it works.

Do not lift the updater guard on `InstallLauncher()` as a shortcut. Its legacy cleanup deletes `telegram.desktop`, `telegramdesktop.desktop`, old `org.telegram.desktop.*` launchers/services, and `telegram.png`. These must never target official Telegram from Jerkgram. With integration handled explicitly, leave this cleanup unreachable; any later reuse must remove or re-scope it.

### URL handlers — separate default ownership risk

`core/application.cpp`, constructor: when `Local::oldSettingsVersion() < AppVersion`, calls `autoRegisterUrlScheme()`; that method invokes `RegisterUrlScheme()` unless experimental `OptionSkipUrlSchemeRegister` is set. Registration supplies `tg`, `tonsite`, `ton`, product names and executable. `Telegram/lib_base/base/platform/linux/base_url_scheme_linux.cpp`, `RegisterUrlScheme()` uses desktop ID when possible, otherwise creates a userapp entry, and calls `set_as_default_for_type()` in both paths. `UnregisterUrlScheme()` deletes matching generated userapp entries.

Thus a fresh profile can seize the same protocol defaults despite unique app IDs and updater OFF. D1 must suppress automatic registration in the Jerkgram application owner; keep explicit user-requested registration available. Merely changing `shortAppName=tdesktop` does not fix Linux behavior. Packaging may advertise handlers but must not set defaults or remove Telegram entries. Do not rename the Telegram protocol schemes themselves.

## 4. Icon pipeline and required payloads

| Source asset / owner | Generated/runtime consumer | Required Jerkgram material |
| --- | --- | --- |
| `Telegram/Resources/art/logo_256.png` | `Resources/qrc/telegram/telegram.qrc` alias `:/gui/art/logo_256.png`; `window/main_window.cpp` logo accessor/CreateIcon path; app/window and tray fallback; `InstallLauncher()` copies this to hicolor 256 | Own 256px logo with appropriate margin |
| `Resources/art/logo_256_no_margin.png` | Same qrc; main-window logo accessor / icon rendering | Own 256px no-margin variant |
| `Resources/icons/tray_monochrome.svg`, `_attention.svg`, `_mute.svg` | Same qrc aliases `:/gui/icons/tray/monochrome*.svg`; `platform/linux/tray_linux.cpp`, `PanelIconName()` and `IconGraphic::systemIcon()` prefer theme names with fallback rendering/counters | Three own symbolic variants with readable monochrome silhouettes |
| `Resources/art/icon{16,32,48,64,128,256,512}.png` and each `@2x` | CMake hicolor install under each corresponding size/scale, renamed to stock desktop ID | Fourteen PNGs; @2x pixels twice nominal size (up to 1024px) |
| Same three tray SVGs | CMake symbolic hicolor installation, runtime InstallLauncher copies | `<id>-symbolic.svg`, `<id>-attention-symbolic.svg`, `<id>-mute-symbolic.svg` |
| `lib/xdg/...desktop` | qrc `/misc` embeds launcher template; OS package also installs a file | Own template, qrc mapping and consumer path agree |

`Telegram/CMakeLists.txt` includes qrc files and calls `target_prepare_qrc(Telegram)`; pinned `cmake/target_prepare_qrc.cmake` enables `AUTORCC` on Linux. Qt rcc produces C++ resource data compiled into Telegram; changing embedded assets requires resource regeneration, object compile and relink. Hicolor-only payloads need packaging/install changes, not C++ compilation. This Linux path does not automatically derive all PNG sizes from a master image: builder must record deterministic conversion and hashes or supply the exact variants. No replacement assets were created here.

Do not replace emoji, premium/service badges, topic icons, chat content, generic `plane_white.svg`, themes or protocol imagery just because a name resembles Telegram. Windows `.ico`/`.rc`, macOS `.icns`/asset catalog and bundle metadata are outside this Linux milestone.

## 5. Profile/data path — critical isolation boundary

Exact stock selection order:

1. `Logs::start()` in `SourceFiles/logs.cpp` first calls `Launcher::checkPortableVersionFolder()` -> `CheckPortableVersionFolder()` in `core/launcher.cpp`.
2. Portable detection first runs `MoveLegacyAlphaFolder()` for adjacent `TelegramAlpha_data` / `TelegramBeta_data`, renaming to `TelegramForcePortable` and potentially copying alpha markers. If `cExeDir()/TelegramForcePortable` exists it forces the working dir there; alpha builds also force/create it.
3. Otherwise Linux Release uses `psAppDataPath()` (not the executable directory).
4. `platform/linux/specific_linux.cpp`, `psAppDataPath()` first checks `~/.TelegramDesktop/tdata/settings0`, `settings1`, `settingss`; **if any exists, it returns that old Telegram root**. Otherwise returns `QStandardPaths::AppLocalDataLocation + '/'`.
5. Qt applicationName is `TelegramDesktop`; under normal Linux XDG defaults this gives `~/.local/share/TelegramDesktop/`, or `$XDG_DATA_HOME/TelegramDesktop/`. This follows the [Qt standard-path contract](https://doc.qt.io/qt-6/qstandardpaths.html); user environment may override the base directory. Desktop ID does not select it.
6. `Launcher::processArguments()` parses `-workdir`; `validateCustomWorkingDir()` forces that absolute path after initial selection. `-key` selects a data-file key within the same root; it is not root isolation. `settings.h`, `cForceWorkingDir()` creates the root, normalizes it and sets owner-only permissions.
7. `Logs::start()` creates `<working>/tdata`, changes process cwd, initializes local options/logs/crash handling. Linux non-Debug also calls `MoveOldDataFiles(initialWorkingDir())`; that function can copy and remove legacy `data`, `data_config`, `tdata/config`. This migration must not run for Jerkgram.

Storage consumers:

- `storage/localstorage.cpp`, `Local::start()`: `_basePath=cWorkingDir()+"tdata/"`; legacy settings/config, modern keyed settings are under that root. `autoupdatePrefixFile()` and `updateManifestFile()` use `tdata/prefix` and `tdata/update-manifest` when updater enabled.
- `storage/storage_account.cpp`: `BaseGlobalPath()` = `<working>/tdata/`; account `_basePath` is keyed under that, `ComputeDatabasePath()` = `tdata/user_<dataName>/`; `cachePath()` = `cache`, big-file database = `media_cache`; constructor `_tempPath` = `tdata/temp_<dataName>/`; legacy temp = `tdata/tdld/`; webview storage = `wvbots` / `wvother` under the account database.
- `core/launcher.cpp`: experimental options `tdata/experimental_options.json`, debug markers, installation usertag; `logs.cpp`: log files/DebugLogs; `core/crash_reports.cpp`, `StartCatching()`: `tdata/dumps`.
- `core/file_utilities.cpp`, `File::DefaultDownloadPath()` = `QStandardPaths::DownloadLocation / DefaultDownloadPathFolder()`; normal folder is `AppName` (currently `Telegram Desktop`), support mode uses `Tsupport Desktop`. User-selected download/dialog paths are preferences, not private profile roots. AppName=Jerkgram gives normal `Downloads/Jerkgram`; preserve explicit user choices.

**Proposed minimal safe policy:** Qt app name `JerkgramDesktop` -> XDG root `$XDG_DATA_HOME/JerkgramDesktop/` (normally `~/.local/share/JerkgramDesktop/`) with unchanged internal `tdata` layout. Remove the `.TelegramDesktop` fallback for the Jerkgram materialization; bypass Telegram legacy alpha/beta migration and Linux cwd legacy migration; detect only `JerkgramForcePortable` for explicit portable mode. A portable archive need not force adjacent data by default: ordinary launch uses XDG, adjacent JerkgramForcePortable opts into movable data. Never silently consume adjacent TelegramForcePortable. Keep advanced `-workdir` supported; an explicit override can still point anywhere, so it is not a safety sandbox. Runtime tests must use isolated synthetic roots and never pass the user's official profile.

No profile or migration was exercised in this audit.

## 6. Single instance / IPC / D-Bus proof

| Owner | Stock identity / formula | Consequence |
| --- | --- | --- |
| `core/sandbox.cpp`, `Sandbox::start()` -> `Platform::SingleInstanceLocalServerName()` | MD5 of encoded absolute **working directory**, then Linux Qt >=6.2 `hash + '-' + QCoreApplication::applicationName()`; abstract namespace sockets. Snap instead `snap.<instance>.<hash>` | Desktop ID alone changes neither input. Own working root plus own Qt name separates official Telegram; Qt name also separates a mistakenly equal root, but does not prevent data sharing |
| `Sandbox::start()` QLockFile | temporary directory / MD5(cExeDir+cExeName) + `-` + `cGUIDStr()`; stale time 0 | Different actual executable paths suffice for Telegram/Jerkgram. Shared GUID alone is not a collision. Do not rename GUID blindly; a new one is optional, unnecessary for minimal Linux D1 |
| `core/launcher.cpp`, `Launcher::instanceHash()` | executable-path MD5 normally; custom-workdir MD5 for overrides | Feeds generated desktop ID and webview socket hash, distinct from sandbox hash |
| `specific_linux.cpp`, `HashForSocketPath()` / `Platform::start()` | first 24 bytes of URL-base64 SHA256(instanceHash); `<tmp>/<hash>-TD-webview-{}` | Own executable path separates normal runs; same explicit custom dir can collide. Recommend a narrow Jerkgram webview prefix for defense in depth; do not rename helper protocol/types |
| `platform/linux/integration_linux.cpp`, `Application` / `MakeApplication()` | Gio bus identity from desktopFileName | Fixed own app ID required for updater-disabled alpha; service name/file must match |
| `Telegram/lib_base/base/platform/linux/base_system_media_controls_linux.cpp`, `SystemMediaControls::Private` bus setup | normal bus name `org.mpris.MediaPlayer2.<QCoreApplication::applicationName()>`; Flatpak/Snap use their identities. MPRIS desktop entry and identity use desktopFileName | **Desktop ID alone leaves org.mpris.MediaPlayer2.TelegramDesktop collision.** Qt applicationName change fixes cross-product bus name without a submodule patch |
| `integration_linux.cpp` inhibit monitor | unique connection bus name + random `tdesktop` token | Per-request uniqueness; no need to rename random token prefixes |
| Notifications/portals/logind/tray | `org.freedesktop.Notifications`, `org.freedesktop.portal.*`, `org.freedesktop.login1`, `org.kde.StatusNotifierWatcher` are shared system services | Do not rebrand these interfaces. `org.telegram.DBus.Service/ObjectPath` annotations in XML describe generated system proxies, not an owned Telegram activation bus |

Same-product multiple custom profiles may still compete for the fixed alpha Gio and MPRIS names. D1 acceptance is one official Telegram plus one Jerkgram simultaneously; arbitrary multiple Jerkgram profiles require a later deliberate instance-ID policy. Do not imply desktop ID provides that policy.

## 7. About, versions, protocol and diagnostics

- `core/version.h`: `AppVersion=7003001`, `AppVersionStr="7.3.1"`, Beta=false, alpha macros. `Telegram/build/version` repeats production version fields and is parsed by `cmake/version.cmake` via root `desktop_app_parse_version()` into CMake project metadata. Do not repurpose these as Jerkgram semver.
- `boxes/about_box.cpp`: `AboutBox()` hardcoded title; `CurrentVersionText(bool)` and exported current-version helpers append canary, alpha, beta, architecture/debug markers. Version link dispatches to `Core::App().changelogLink()` for normal builds (`core/application.cpp`, `Application::changelogLink()` returns `https://telegramdesktop.github.io/tdesktop/changelog/`). `settings/sections/settings_advanced.cpp` also displays `currentVersionText()` in its update UI; keep every visible product version coherent while retaining the upstream-only helper where required. Jerkgram UI needs a separate display model, while retaining upstream 7.3.1 attribution and applicable build details.
- `mtproto/session_private.cpp`, `ComputeAppVersion()` builds `AppVersionStr + architecture/store flags` for protocol client metadata. Preserve this in initial D1; do not let UI semver alter the upstream protocol assumptions.
- `core/update_channel.h`, `RunningUpdateVersion()` uses `Updates::MakeUpdateVersion(AppVersion, CanaryBuildCounter)`. Update selection/rollback and `Local::oldSettingsVersion()` comparisons also depend on upstream numeric version. Jerkgram version must not be substituted here.
- `logs.cpp`, `Logs::start()` records numeric AppVersion and executable; `core/crash_reports.cpp`, `StartCatching()` records Binary, ApiId, Version, Platform, usertag. Add separate Jerkgram provenance metadata when diagnostics are enabled, keeping upstream version meaningful; never print credentials. Crash submission identity/endpoints are a distinct concern from updater identity; no new Jerkgram crash service is proposed. For alpha, explicitly consider supported `DESKTOP_APP_DISABLE_CRASH_REPORTS=ON` rather than silently submitting fork diagnostics as stock.

Proposed model: builder `JERKGRAM_VERSION` is authoritative for the Jerkgram release (next value proposed `0.1.0-alpha.1`, not assigned here). Materialize a small generated Jerkgram identity header containing product display strings, version and upstream base SHA/version. About displays `Jerkgram Desktop 0.1.0-alpha.1` and `Based on Telegram Desktop 7.3.1`; product/release links lead only to owned destinations once those destinations exist. Preserve API/GPL/Telegram service attribution. Avoid a global `-D` version/product flag on every translation unit.

## 8. Complete Linux updater path and first-alpha policy

### Discovery and download

1. `cmake/variables.cmake`: supported `DESKTOP_APP_DISABLE_AUTOUPDATE` option. Default depends on special target (plain builds default disabled; production special targets can enable it; Flatpak adjusts default). Therefore explicitly pin ON, never rely on a default.
2. `Telegram/cmake/telegram_options.cmake` turns ON into Telegram target definition `TDESKTOP_DISABLE_AUTOUPDATE`.
3. `core/update_checker.cpp`: macro initializes `UpdaterIsDisabled=true`; `UpdaterDisabled()` gates sandbox/application/UI construction and startup ready-update checks. `SetUpdaterDisabledAtStartup()` supports external-updater detection (`core/launcher.cpp`, `ComputeExternalUpdater()`, matching executable entries in `externalupdater.d`). CLI `-noupdate` only sets `gNoStartUpdate`, not permanent updater disablement.
4. `storage/localstorage.cpp`, `readAutoupdatePrefixRaw()` reads profile `tdata/prefix`, otherwise `https://td.telegram.org`; normalized by `readAutoupdatePrefix()`.
5. `HttpChecker::start()` requests `<prefix>/current<AutoUpdateVersion()>`; `Telegram/lib_base/base/platform/linux/base_info_linux.cpp` returns version 6 normally, 2 for glibc <2.28, platform key `linux`. Thus normal current endpoint is `https://td.telegram.org/current6`, compatibility endpoint `/current2`. JSON/old-map parsing chooses version/channel and payload link. `HttpLoaderActor` downloads using HTTP Range.
6. `Updater::start()` also starts `MtpChecker`. Stable/beta `MtpChecker::start()` resolves `tdhbcfeed6` (or `tdhbcfeed2`) and reads feed messages; MTP loader obtains update documents. Canary channels have separate discovery/metadata configuration and manifest adoption. Replacing the HTTP domain leaves this path intact.

### Trust and verification

- `Telegram/cmake/generate_update_keys.cmake` creates `gen/update_keys_data.h` from `Resources/update/root-public.pem`, `manifest.min.json`, `manifest.sig`; `core/update_keys.cpp` exposes embedded root and manifest bytes.
- `core/update_checker.cpp`, `HeldManifest()` verifies embedded and persisted manifests; `AdoptManifest()` stores newer authenticated metadata in `tdata/update-manifest`.
- `core/update_verify.cpp`, `ParseVerifiedManifest()` verifies an **Ed25519 root signature before JSON parsing**. Manifest defines channel signing key groups, revocations and key expiration. This pinned manifest requires stable/beta signatures satisfying both the Ed25519 release-key group and ES256 release-key group. It is not simply the old RSA updater trust model.
- `VerifyUpdate()` parses the envelope; validates platform target, root-authenticated carried/held manifest, channel policy, signatures and newer running version. `SigningInput()` binds signed envelope region plus SHA256(payload). `VerifyChannelAuthorization()` requires every configured group; `VerifySignature()` supports Ed25519 and ES256/P-256. Existing RSA/SHA1 private-alpha URL signing in `countAlphaVersionSignature()` is a separate legacy path, not the v2 root trust.
- `core/update_checker.cpp`, `UnpackUpdateV2()` verifies before decompression and staging under working-directory `tupdates/temp`, with a ready marker. `core/update_unpack.cpp` owns payload extraction. Protected mode also stages a signed `tupdates/ready-package`, validated again by `platform/linux/update_install_linux.cpp` using root/channel/target/version rules.

### Apply/restart

- `Sandbox::socketError()` gates `checkReadyUpdate()` with `!UpdaterDisabled()` and `!cNoStartUpdate()` before starting UI. `core/launcher.cpp` restart-update path is also gated.
- `platform/linux/launcher_linux.cpp`, `Launcher::launchUpdater()` checks readiness, runs adjacent `Updater` with `-justupdate -workpath -exename -exepath` for writable installs, then relaunches the discovered executable. Ordinary restart directly launches the executable.
- Protected install validates running executable/installation and signed package, invokes `run0` or `pkexec` on the trusted executable with `-installupdate`, then `InstallUpdateIfRequested()` validates command/root mode and installs. `update_install_linux.cpp` maps package member `Telegram` onto the running executable name, installs helper, runs helper, and handles cleanup/restart. Thus filesystem renaming does not reject Telegram-signed packages.
- `_other/updater_linux.cpp` applies staged files and relaunches, with legacy ready/temp layouts and `.TelegramDesktop` fallback. Do not include this helper in the alpha archive.

### Supported safe first-alpha configuration

Set **`DESKTOP_APP_DISABLE_AUTOUPDATE=ON`** explicitly in builder-generated D1 configuration. CMake excludes the Updater target (and Packer branch); macro disables normal discovery/startup application; Linux protected-update functions refuse disabled builds, including explicit `-installupdate`. Keep no helper/update artifacts in release packaging. Do not invent fake signatures, swap official keys, or set a pretend Jerkgram endpoint before signed infrastructure exists. Official public key files may remain inert upstream source; the safety boundary is disabled execution plus verification, not deleting unrelated cryptography.

Residual UI: `Core::UpdateApplication()` when disabled opens official `desktop.telegram.org` (or platform store links). Settings `HasUpdate()` returns false and hides its ordinary updater section, but other entry points remain. D1 must replace or remove Jerkgram release/update actions and changelog destinations so they never present official binaries as Jerkgram upgrades. A future manual release link may use `https://github.com/jerkgram/Jerkgram-Desktop/releases` **only after the repository exists**; this audit does not assert ownership/creation or publish anything.

No updater runtime/network behavior was tested here. Runtime gates must prove no HTTP or MTP update discovery and refusal of update installation; absence of an Updater file or endpoint strings alone is not sufficient.

## 9. Coexistence collision register

| Collision point | What prevents it in D1 |
| --- | --- |
| Binary basename/PATH/upstream packaging assumptions | Output Jerkgram; own archive and explicit integration paths; retain internal target |
| XDG data root and ~/.TelegramDesktop fallback | Own Qt app name/root; remove legacy Telegram fallback |
| Adjacent portable folders and legacy initial-cwd migration | JerkgramForcePortable only; no Telegram migration/fallback |
| Local socket and per-executable lock | Own Qt name and working root; distinct actual executable path |
| Gio activation bus/service, desktop filename, Wayland ID | Consistent com.jerkgram.desktop across runtime/static integration |
| X11 WM_CLASS | Qt JerkgramDesktop matches StartupWMClass; verify actual metadata |
| MPRIS bus | Qt JerkgramDesktop -> org.mpris.MediaPlayer2.JerkgramDesktop |
| Webview socket prefix/custom workdir | Own prefix plus isolated root/path; verify helpers |
| Notifications, icon theme, tray, badge entry | Own desktop/icon IDs and embedded assets |
| Auto-start launcher | Own desktop filename and absolute Jerkgram executable; no Telegram cleanup |
| MIME scheme defaults | Advertise supported schemes, no automatic default takeover; explicit opt-in only |
| AppStream identity | Own component/launchable/dbus IDs, publisher/source/release metadata |
| Downloads | Normal Downloads/Jerkgram via product name; retain user-selected destinations |
| Autoupdate overwrite/discovery/manual links | Supported OFF policy, no helper, own/manual UI destinations |

Separate profiles are established by source policy, not by testing against real user data. This audit never accessed the user's installed Telegram profile.

## 10. Proposed final identity values

| Surface | Proposed value / policy |
| --- | --- |
| Display / product short name | Jerkgram |
| Welcome/About long name | Jerkgram Desktop |
| Executable output | Jerkgram |
| Internal CMake target/project | Telegram (retain) |
| Qt applicationName / X11 class | JerkgramDesktop |
| Qt applicationDisplayName | Jerkgram |
| Runtime desktop/Gio/Wayland ID | com.jerkgram.desktop |
| Desktop filename | com.jerkgram.desktop.desktop |
| Activation service name/file | com.jerkgram.desktop / com.jerkgram.desktop.service |
| Icon name | com.jerkgram.desktop; symbolic suffix variants |
| StartupWMClass | JerkgramDesktop |
| AppStream component | com.jerkgram.desktop, if shipped |
| Normal profile | XDG_DATA_HOME/JerkgramDesktop/tdata (default ~/.local/share/JerkgramDesktop/tdata) |
| Explicit portable profile | Adjacent JerkgramForcePortable/tdata |
| Default downloads | Downloads/Jerkgram |
| Webview prefix | Jerkgram-owned prefix replacing only the TD literal in the socket template |
| MPRIS | org.mpris.MediaPlayer2.JerkgramDesktop |
| Jerkgram release version | Proposed 0.1.0-alpha.1 via JERKGRAM_VERSION; not set by D1A |
| Upstream numeric/string version | 7003001 / 7.3.1 (retain) |
| Update policy | DESKTOP_APP_DISABLE_AUTOUPDATE=ON; manual owned releases |

These are a coherent recommended set, not implemented assignments. Desktop filename has two `desktop` components intentionally: reverse-DNS ID ends with `.desktop`, then the format extension adds `.desktop`.

## 11. Bounded builder materialization plan (A/B/C/D/E)

A = textual/source patch; B = generated build configuration; C = resource payload; D = runtime verification; E = packaging. No full Telegram source fork.

| Proposed unit | Class | Exact scope |
| --- | --- | --- |
| `patches/0001-linux-identity.patch` | A | Linux CMake output-name branch; launcher Qt name/display; Linux desktop ID; no internal target/type renames |
| `patches/0002-profile-isolation.patch` | A | psAppDataPath legacy fallback; Jerkgram portable-only selection/no alpha migration; Linux initial-cwd migration bypass; own webview socket prefix |
| `patches/0003-product-surfaces.patch` | A | AppName/AppFile deliberately; welcome/main default title/About/main-menu footer/Linux menu labels; separate Jerkgram version display and provenance; no translation-wide replacement |
| `patches/0004-integration-policy.patch` | A | Suppress automatic URL-default registration in application owner; coherent embedded desktop template path if changed; manual release/changelog actions; retain disabled portable auto-install guard |
| Generated identity header | B | Small output derived from JERKGRAM_VERSION + pinned base and reviewed identity manifest; included only by actual consumers, not all-target compile defines |
| D1 config manifest / invocation | B | Explicit updater OFF; Release/LTO configuration retained; preserve credentials; bounded compile/link concurrency; fail if identity/updater configuration disagrees |
| `payloads/linux-identity/` | C | Own launcher/service and optional AppStream template; icon PNG/SVG/logo assets mapped by hash into exact sources; deterministic generation recipe where applicable |
| Materializer and tests | A/B | Expand current zero-change builder only after design approval: validate pin, preimages, expected file inventory, patch series order/hashes and payload hashes; reject mismatches/partial overlays; repeat run verifies exact state rather than stacking patches |
| Integration installer/uninstaller | E | Explicit opt-in, absolute quoted installed executable; only own desktop/service/hicolor/autostart files; never change protocol defaults automatically or remove Telegram files |
| Portable tar.xz | E | Own directory/binary/icon/integration templates; strip staging copy only; no Updater/Packer, credentials, tdata, D0 objects, symbols or logs; include licenses/notice and reproducibility/provenance manifest |
| D1 acceptance evidence | D | Tests in section 13; record actual behavior, cannot infer runtime from textual checks |

Current **builder** `materialize()` and `overlay()` explicitly accept zero changes only; `verify_source()` rejects a dirty checkout. D1 must design distinct states: pristine pinned input, verified materialized output with allowlisted hashes, and build/package eligibility for that output. Do not simply disable cleanliness checks. Validate all preimages before writes, record overlay manifest, and use a disposable materialization destination that contains no D0 out tree. Pinned submodules should remain unchanged; MPRIS and scheme behavior can be corrected from application owners.

New builder configuration must discover the CMake target output instead of assuming `out/Release/Telegram`. Update package metadata to identify Jerkgram version, upstream SHA, builder SHA, overlay/payload digests, updater policy and actual compile/runtime evidence separately. Public source distribution should include the exact reproducible overlay and required notices; no source-export implementation in D1A.

## 12. Files/names that must not be blindly renamed

- CMake target/project `Telegram`, `tdesktop::` aliases, C++ namespaces/types/classes, `.cpp` inventories and submodule names.
- `AppVersion`, `AppVersionStr`, Telegram/build/version protocol/build counters and storage migration comparisons.
- `tg`, `ton`, `tonsite`, Telegram API/MTProto schema, service URLs, server public keys and API credentials.
- `AppId` Windows GUID and `cGUIDStr()` cross-platform constant: not the Linux desktop ID; no global UUID replacement.
- Internal `tdata` storage layout, account/key/database formats; isolate the root instead.
- Freedesktop/KDE/logind/portal D-Bus APIs, MPRIS standard interfaces and object paths, generated proxy annotations.
- Generated CMake/Ninja files, generated qrc C++, generated language/style headers; change their true input owners only.
- Upstream licenses/attribution, cloud translations, Telegram service references and unrelated icons.
- Windows/macOS signing/bundles/installers and official update key material as a speculative Linux rename task.
- Upstream AGENTS.md and local agent instructions are not product payloads.

## 13. Verification plan for D1 implementation

### Before a build

1. In a disposable source materialization, verify pinned SHA/gitlinks, preimages, overlay inventory, payload hashes, expected postimages, repeatability/idempotence, and fail-closed wrong-pin/partial-overlay behavior. Never use the protected D0 tree as a test fixture.
2. Source contract checks must independently enumerate profile selectors, migration entry points, startup registration and updater guards. Include synthetic legacy `.TelegramDesktop`, TelegramForcePortable, alpha/beta and cwd files; assert they remain untouched. Test XDG defaults/override and JerkgramForcePortable separately.
3. Validate desktop/service/AppStream syntax and equality of IDs, executable paths, StartupWMClass/icon name, quit action, URI placeholders and safe quoting (including spaces). Installer dry-run must show only owned destinations. Validate actual PNG sizes and symbolic payload inventory.
4. Future configure-only checks in the authorized D1 build tree must confirm updater ON-disable flag, compile macro, no Updater/Packer production dependency, target output Jerkgram, Release/LTO and bounded LTO streaming settings. No credentials in logs/artifacts. Do not claim no official updates from string absence alone.

### Build and package gates (require a later authorized implementation/build task)

5. Compile materialized Release using official container environment; preserve D0 and existing credentials. Capture actual scheduled compile scope and peak LTO resources; no promise of a relink-only D1.
6. Validate binary ELF metadata/dependencies and target name; strip only package staging copy, compare original hashes; inspect tar members and provenance. No helper, profiles or secret/build artifacts.

### Runtime gates

7. First launch in a fresh synthetic HOME/XDG tree with deliberately seeded fake legacy Telegram profiles and adjacent portable/cwd fixtures. Observe file opens/writes (e.g. syscall trace), not only log claims; all fake Telegram files remain unchanged. No real user's Telegram profile is a fixture.
8. Start stock D0 with its own synthetic profile and Jerkgram with its own defaults **on the same test session bus**. Independent UI/processes; repeated launch/quit/URL activation routes to the intended product. An isolated bus per product would hide collisions and is insufficient proof.
9. Record Qt applicationName, desktopFileName, X11 WM_CLASS and desktop properties; test Wayland app_id where available. Verify Gio activation names/service Exec, MPRIS bus names and controls, notification attribution, tray themed/fallback icons, unread badges and autostart isolation. Missing platform coverage is recorded as pending.
10. Snapshot MIME defaults/launcher/icon/service files before/after launch in test XDG roots; assert no automatic takeover or removal. Separately test explicit opt-in URL registration and uninstall removing only own integration.
11. Prove disabled updater: source/config contract plus runtime no HTTP/MTP discovery (instrument relevant dispatcher or outbound observations), no scheduled checker, no helper spawn; benign `-installupdate` attempt refuses before file installation. Inspect every reachable release/update/changelog action. Ordinary restart still works and preserves own profile. Do not exercise a real official update package against installed data/binaries.
12. Capture About screenshot with Jerkgram version and upstream base; default welcome/window labels, downloads root, diagnostics provenance. Login is not required for launch/About/profile gates; MTP/notification checks may need later controlled account evidence and must not be claimed from welcome UI.

Acceptance requires **SOURCE + CONFIG + RELEASE COMPILE + RUNTIME COEXISTENCE** evidence. Passing verifiers or compilation alone does not close D1.

## 14. Estimated rebuild scope

| Change | Expected work |
| --- | --- |
| External archive name, installer, hicolor-only files, nonembedded service/AppStream | Package/install only; no C++ work |
| Linux OUTPUT_NAME | Configure/generate in future D1 tree, target relink/output placement and package consumers; by itself should not recompile existing source objects, subject to actual generated build |
| Embedded desktop template/logo/tray SVGs/qrc | AUTORCC regeneration, resource object compilation, final LTO relink |
| Localized resource key additions/style assets | Language/style codegen; generated-header consumers may recompile widely. Avoid expanding schemas for simple product strings |
| Local .cpp identity/profile/About/registration patches | Changed translation units plus final LTO relink; shared identity-header consumers recompile |
| Changes to core/version.h | Potentially many consumers: protocol/UI/storage/crash/update. Avoid injecting Jerkgram semver there |
| DESKTOP_APP_DISABLE_AUTOUPDATE definition | **Broad Telegram target recompilation likely**: target-wide compile command changes and precompiled header rebuild (`target_precompile_headers(Telegram ... stdafx.h)`). Libraries without that definition may be reused; no guarantee all dependencies remain untouched after configuration |
| Global CMAKE_CXX_FLAGS, toolchain/Qt/dependency changes | Broad invalidation; not required for D1 |

A safe D1 alpha cannot honestly be promised as packaging-only or final-link-only: supported updater disablement changes the compilation contract. Keep existing D0 output/cache intact. Plan a separate authorized Release build and reuse compatible compiler/dependency cache; retain the proven one-worker LTO policy and do not estimate elapsed time from source inspection alone. No configuration/build commands were run for these estimates.

## 15. Exact next milestone and stop boundary

**D1B — Jerkgram Identity / Branding materialization, Linux manual-update alpha.**

Implement only the bounded source/config/resource/packaging units above after user authorization and availability of reviewed branding payloads. First secure profile/update/URL-default isolation, then presentation/integration, then run the explicit compile/runtime acceptance gates. Do not start feature development or create a release repository as a side effect.

D1A changes documentation only. Product identity proposals remain unmaterialized; current D0 binary, out tree, Docker image/cache, D0 evidence and API credentials are outside this task. No production build, branding patch, icon replacement, packaging or runtime launch belongs to this audit.
