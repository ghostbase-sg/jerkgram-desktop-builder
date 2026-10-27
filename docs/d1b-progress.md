# D1B implementation ledger

Spec: user's attached D1B brief, 2026-10-25. Plan: docs/d1-audit.md sections 11–15.

- SOURCE: four bounded patches authored in temporary workspace; no D0 source modification.
- Materializer tests: five behavioral tests observed failing without implementation, then passing. Covers pristine/output distinction, wrong pin, preimage/postimage/input hash rejection before writes, idempotence, tampering, extra files, traversal and payload symlinks.
- Branding: user explicitly approved JerkgramGlassReveal.icon. Canonical Plane.svg/Oval.svg/icon.json copied read-only from the existing icon package. Flat Linux PNG/symbolic derivatives generated deterministically; Apple glass lighting is not emulated.
- Actions Secrets: names TDESKTOP_API_ID/TDESKTOP_API_HASH present. Values never requested or printed. User authorized one-job self-hosted runner on laptop for trusted D1 workflow.
- D1 source: separate telegram-desktop-d1 checkout; local shared clones reuse pinned Git objects/submodules. D0 out/image/evidence untouched.
- Initial pre-build checkpoint: build had not started. See the current-attempt record below for subsequent progress.
- Ruling: preserve upstream service changelog URL for upstream service attribution; own product footer/version actions open local About, and disabled-update action has no external upgrade URL.
- Scope mistake: an exploratory command accidentally ran the unrelated iOS test suite (556 tests, 24 failures/6 errors). Those results are not Desktop evidence and no iOS changes are planned. Correct Desktop baseline: 8 tests passed. Do not rerun or act on iOS tests.

## Pre-build review and gate

- Independent whole-change code review found three Important issues before build: dependent CMake LTO option gate, ignored source inputs bypassing inventory, and glob-based packaging outside declared payloads.
- Fixed all three; regression tests observed failing before fixes. Full Desktop suite now 18 tests, zero failures.
- Ruling: do not introduce upstream special target just to turn on an option. Keep Docker compiler-provided LTO, enforce actual generated compile flags and final link flags; do not modify global CMAKE_CXX_FLAGS or generated Ninja files.
- D1 overlay configuration refreshed after verifying all previous postimages, restoring only owned D1 overlay paths, then re-materializing. No existing out tree existed in D1; D0 untouched.
- Explicit crash-report disablement is included for alpha so fork diagnostics are not submitted as official client reports. No custom crash infrastructure or updater infrastructure is invented.

- First trusted workflow `40228853969`: source/tests/configure passed, config gate rejected upstream dependent `USE_PACKAGED:INTERNAL=OFF`; **no compilation started**. Root cause: cache type is not effective dependency/link mode. Regression reproduces the INTERNAL cache form. Gate now verifies actual static Qt Core/Gui/Widgets libraries, compiler LTO and final one-worker link flags; requested configuration is recorded separately. Actual generated D1 edge passes the corrected gate. The same existing image/dependencies are retained; no reconfiguration workaround or Ninja edit.


## Resume — 2026-10-27

- Previous attempt 40229101552 ended with container exit 137 after 1070.82 seconds, at operation 207/2378. Host journal shows SIGTERM followed by forced stop after ten seconds; it does not establish OOM. Previous host peak was 20,157,706,240 bytes used, swap peak 200,704 bytes. Do not confuse this external stop with the older D0 LTO OOM.
- Previous evidence preserved at Desktop/d1-evidence-attempt-20261025. No clean/out deletion or credential change.
- Active incremental workflow: https://github.com/ghostbase-sg/jerkgram-desktop-builder/actions/runs/40405894480 at builder d54ec4f597a63d537858128ad9e76fd256a0df56. Source/config checks passed again; Ninja reports 2171 remaining operations after reusing the prior 207.
- Runtime harness is now saved in scripts/runtime_smoke.py rather than /tmp only. Its private test-bus registrar passed independently; actual application checks await the compiled binary.
- Packager now includes 64 tracked pinned-source license/notice files (752330 bytes). Regression proves untracked credential-like files are excluded. Full builder suite: 19 tests passed.
- Current status: SOURCE PASS; CONFIG PASS; RELEASE COMPILE IN PROGRESS; RUNTIME COEXISTENCE PENDING. D1B is not complete.

## 2026-10-27 runtime inspection and bounded follow-up

Initial D1 link target completed (Ninja successful target record, valid 3,340,449,096-byte ELF). The runner lost communication before the campaign summary was written; Actions is failed and is not reported as a successful workflow. Kernel journal in the exact completion interval contains no OOM kill. No second full compile is required.

X11 synthetic coexistence passed: independent Jerkgram/Telegram processes on the same private bus, distinct Gio identities, repeated launch, live activation, default/portable/explicit profiles, unchanged legacy fixtures and startup MIME defaults, safe updater refusal. Actual screenshots exposed two remaining upstream strings describing the client as official. The bounded correction changes only intro_start.cpp and About Text1; retains Telegram API/GPL attribution and upstream version. All objects/out/cache remain in place. A fresh incremental compile/link and new runtime evidence are required before completion.

The screenshot harness now uses the installed Hyprland Lua dispatcher. New runner startup will be detached from the tool session so a UI/tool interruption cannot terminate its parent process group. No assertion is made about the exact cause of the earlier runner disconnect.
