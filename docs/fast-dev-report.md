# Fast Linux build infrastructure — measured report

Date:2026-10-30. Builder base891defe6bc4c187dd61b97386e4b426f856a7b91; branch`d2/fast-dev-build`.

## Result and outstanding condition

The daily optimized Release/no-LTO loop is compiled, measured and runtime-tested. Two changed TUs take36.62s end to end, including verification; their native link takes20.538s. The previous D1B change of the **same intro/about owners** took7241.872s end to end and7231.145s in production LTO. The old full production campaign was approximately7+hours. Bootstrap is a separate once-only cost.

The exact restored toolchain is locally recoverable after Docker prune from a complete checked archive outside Docker. **Remote retention is not complete:** two GHCR blob PUT attempts reset, GitHub Releases body upload returned408, and a45s probe through the existing explicit local proxy timed out. The incomplete infrastructure draft is unpublished; no remote digest is claimed. No network settings were changed. This is the remaining operational risk: loss of the laptop/disk loses the local backup too. Product features were not started.

## Measurements

Durations include source/config/hash verification. Compile span is the wall envelope of compilation; link time comes from actual Ninja records. RAM and logical zram swap are whole-host samples every3s, including desktop and cache effects; they are not process RSS or guaranteed sub-second maxima. DEV began with existing swap use (~2.14GiB); do not attribute every swap byte to a compiler.

| Operation | Duration | Recompiled TU | Link | Peak host RAM | Peak logical swap | Allocated disk delta |
|---|---:|---:|---:|---:|---:|---:|
| Toolchain restore (build/export/load) | 3h 6m 3.4s | upstream dependencies | included | 18.92GiB | 0.30GiB | +68.41GiB |
| First DEV bootstrap | 1h 23m 54.9s | 2178 | 24.07s | 17.98GiB | 3.32GiB | +11.48GiB |
| No-op | 7.89s | 0 | 0.00s | 7.50GiB | 3.24GiB | +0.00MiB |
| 1 TU | 33.64s | 1 | 19.98s | 17.12GiB | 3.69GiB | +0.36MiB |
| 2 TUs | 36.62s | 2 | 20.54s | 17.13GiB | 3.66GiB | +0.37MiB |
| Narrow header | 46.26s | 2 | 20.42s | 16.84GiB | 3.73GiB | +0.36MiB |
| Typical small patch | 49.37s | 1 | 23.29s | 15.72GiB | 5.66GiB | +0.36MiB |

Toolchain row is the successful dependency build/export/load duration; a prior EPEL mirror failure cost886.7s and was retained separately. Inspection initially used nonexistent Qt pkg-config metadata; it was corrected to installed qmake/CMake without rebuilding the image. Tiny Qt/native/old-object GCC LTO probes passed. A checked backup cost169.345s separately. Toolchain disk delta includes BuildKit/image growth; archive storage is additional.

Bootstrap compiled2178 objects,2377 executed operations (2378 initially planned; Ninja restat changes its progress denominator). It used jobs2 then4 after measured memory headroom: a graceful interruption preserved1377 completed operations and resumed only1001 planned remaining operations. Compile spans4957.186s; total5034.853s includes both segments, verification and the pause. No compile flags/reconfigure/clean occurred during that switch. All segments and the intentional interrupted status are preserved, not relabelled as a successful first command.

One-TU compile3.826s; two-TU compile span6.517s; narrow-header15.33s; typical owner16.20s. Narrow header affected exactly2TUs. Every DEV segment/case observed zero GCC LTO processes. Source bytes/mtimes were restored. The separate original-source cleanup really compiled1TU and linked19.401s; Ninja log compaction exposed the original byte-offset measurement bug. Original evidence is retained, corrected metrics were recovered from the complete log/output timestamps, and the collector now handles compaction with a regression. Final post-restoration no-op8.813s compiled0 and linked0.

## Profiles and storage model

One active source:`/home/pixi/Projects/Jerkgram/Desktop/telegram-desktop-d1` at upstream6fed91ffab9861771a75f29df65031b3c80b6941 with exact D1 materialization. No milestone source clone was created.

- DEV:`out/dev-fast`, Ninja single-config Release, O3/DNDEBUG, g1, no fat-LTO objects, no LTO/plugin, lld native link, static Qt, same configured API/identity/updater OFF. Initial compiler ENV is derived from the image through supported CMake initialization; generated Ninja/cache files are not patched.
- Production:existing`out`, Release+LTO, `-flto=1 --param=lto-max-streaming-parallelism=1`. Explicit execution only. No production campaign was run.
- Existing API values are loaded inside container CMake from the existing production cache; no values are printed/retrieved from Actions Secrets or copied into images/reports.

DEV adds approximately11.48GiB after bootstrap, rather than another40GiB checkout. Final totals follow below. Main production cache, both original binaries and all2178 original object sizes/mtimes match the initial inventory. The production binary remains SHA256`00fccd4abd483d29eb3838ddc2485f6d36b2b751fdd5c1380d65f973ec4ea35b`.

DEV binary:`/home/pixi/Projects/Jerkgram/Desktop/telegram-desktop-d1/out/dev-fast/Jerkgram`,1,835,801,848bytes. ELF64 x86-64 PIE, static Qt/Core/Gui/Widgets and C++ runtime; ordinary upstream system GLib/Pango/glibc dependencies remain dynamic. This is not a claim of fully static glibc. Generated graph and actual ELF NEEDED entries agree.

## Toolchain identity and recovery evidence

Image`sha256:8a1b4c81f9d09e148df60f7c9819c2a4b10aa34a5c02bef8307c2001d5f1bf07`;
native config`sha256:ce456fd48f862daee24de5b8cfa78df5f50ece9597fdf2c879f7e88e426744bc`;
29,837,815,381bytes.

GCC15.2.1 (Red Hat15.2.1-7), CMake3.26.5, Ninja1.13.2.git.kitware.jobserver-pipe-1, Qt6.11.2, lld21.1.8. GCC/Qt match D1B; old-object native and one-object incremental GCC LTO compatibility both pass without modifying the old object. This is compatibility evidence, not a new full production compile.

Recipe:unchanged pinned upstream Dockerfile/generator/Poetry lock inputs in`toolchains/recipe.json`, Jinja3.1.6; DEBUG1/LTO1 dependency policy retained. Bounded HTTPS EPEL transport override and stale-lock guard are documented. The actually used rendered Dockerfile SHA is committed in the lock; future guard rendering differs, so an exact image is recovered by its retained bytes, not by claiming moving distro packages reproduce the old historical digest. Source/out/API were never in the image context; final product mount is empty.

Archive:`/home/pixi/Projects/Jerkgram/Desktop/toolchain-backups/tdesktop-v7.3.1-8a1b4c81f9d0.tar.zst`,10,724,587,066bytes;
SHA256`4972e808425a22c22d1a8baf9b9b6c9159383c03b192afa2eeaa9f283b606c14`.
All50native layers and native config/manifest identity verified; actual `docker load` from the archive returned the same image. Existing installed image was preserved. See[recovery commands](fast-dev.md#disaster-recovery). If application`out` is deleted, objects require bootstrap again; recovering the toolchain cannot recreate lost app objects or API configuration.

GHCR attempts:[40982243247](https://github.com/ghostbase-sg/jerkgram-desktop-builder/actions/runs/40982243247),[40982591550](https://github.com/ghostbase-sg/jerkgram-desktop-builder/actions/runs/40982591550), both failed network transfer. Both one-job runners self-removed credentials/registration and cleanup was verified. GitHub Releases fallback uses128MiB checksummed parts and a pinned manifest, but no completed remote image/archive exists yet. No broader PAT requested; no global Docker/proxy changes.

## Runtime

Host X11/Xwayland and native Wayland both passed: mapped Jerkgram UI, no immediate crash, own default synthetic profile, own Gio/D-Bus owner, disabled installupdate refusal, unchanged synthetic official-Telegram sentinel. X11 classJerkgramDesktop; native Wayland classcom.jerkgram.desktop. Welcome and X11About were visually reviewed: Jerkgram Desktop0.1.0-alpha.1, based on Telegram Desktop7.3.1. Test children terminated normally. No user account/profile was opened; authenticated MTP/media behavior is not claimed. Existing D1B coexistence evidence remains preserved.

## GitHub and daily use

Every push/PR runs only hosted pin/materialization/source/profile/unit/fixture verification, with no API Secrets/self-hosted product build. Actual preflight runs finish in seconds. `production.yml` remains manual, with measured capacity rejection before restore/build, replaceable production runner selection, candidate package/manifest/checksums, and separate runtime acceptance. Standard hosted memory is not assumed sufficient. No production workflow dispatch occurred.

Use the commands in[fast-dev.md](fast-dev.md). Daily default is dev-fast; production requires both`--profile production --execute-production`. Explicit declared cpp/header owner edits are supported without a blanket dirty-tree bypass. Permanent feature changes still belong in reproducible patches/payloads.

## Evidence locations and limitations

All raw local evidence is under`/home/pixi/Projects/Jerkgram/Desktop/fast-dev-evidence`: restore/compatibility/backup metadata, bootstrap segments/campaign, five benchmarks and cleanup corrections, preservation inventory, screenshots/runtime JSON, masked failed upload records. No full source, credentials or build output were committed to the builder.

Remote retention remains unresolved due network upload failure. Local archive survives Docker prune but shares the host disk. A true remote cold recovery is not claimed. Runtime coverage is synthetic startup/identity/update refusal, not authenticated application regression coverage. Production quality policy is preserved in configuration and existing artifacts; it was not recompiled for a green badge.

## Final measured storage (before review,04:12 Moscow)

| Measurement | Initial | Final |
|---|---:|---:|
| Root used / available |163G /313G |247G /228G |
| Active D1 source + production + DEV |41G |52G |
| Stock source |1010M |1010M |
| D1 artifacts |75M |75M |
| D1 ephemeral runner |900M |913M |
| Builder |1.6M |2.6M |
| Fast-dev evidence |absent |18M |
| Checked archive outside Docker |absent |10G |
| Docker images |0 |2 /30.2GB (BuildKit + pinned toolchain) |
| Docker named volume |0 |1 /53.4GB (retained BuildKit state) |
| Docker build cache |43.11MB |43.11MB |

D0 evidence240M and all D1 evidence directories remain. No prune/clean/out removal occurred. Disposable upload spools are distinct from protected backups/artifacts; no duplicate source clone or milestone build tree was created. Docker image size and host filesystem allocated/physical sizes are different measurements and need not add exactly.

## Final review / delivery record

Whole-branch independent review and final hosted preflight are recorded in the delivery ledger. Integration remains the requested separate pushed builder branch; no automatic merge or product release. The only published effects are builder commits/preflight; the incomplete infrastructure Release remains a draft. The open network issue is explicitly separate from the proven daily build/runtime/local recovery results.
