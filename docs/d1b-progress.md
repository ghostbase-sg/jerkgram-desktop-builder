# D1B implementation ledger

Spec: user's attached D1B brief, 2026-10-25. Plan: docs/d1-audit.md sections 11–15.

- SOURCE: four bounded patches authored in temporary workspace; no D0 source modification.
- Materializer tests: five behavioral tests observed failing without implementation, then passing. Covers pristine/output distinction, wrong pin, preimage/postimage/input hash rejection before writes, idempotence, tampering, extra files, traversal and payload symlinks.
- Branding: user explicitly approved JerkgramGlassReveal.icon. Canonical Plane.svg/Oval.svg/icon.json copied read-only from the existing icon package. Flat Linux PNG/symbolic derivatives generated deterministically; Apple glass lighting is not emulated.
- Actions Secrets: names TDESKTOP_API_ID/TDESKTOP_API_HASH present. Values never requested or printed. User authorized one-job self-hosted runner on laptop for trusted D1 workflow.
- D1 source: separate telegram-desktop-d1 checkout; local shared clones reuse pinned Git objects/submodules. D0 out/image/evidence untouched.
- Build not started. CONFIG, RELEASE COMPILE and RUNTIME COEXISTENCE pending.
- Ruling: preserve upstream service changelog URL for upstream service attribution; own product footer/version actions open local About, and disabled-update action has no external upgrade URL.
- Scope mistake: an exploratory command accidentally ran the unrelated iOS test suite (556 tests, 24 failures/6 errors). Those results are not Desktop evidence and no iOS changes are planned. Correct Desktop baseline: 8 tests passed. Do not rerun or act on iOS tests.

## Pre-build review and gate

- Independent whole-change code review found three Important issues before build: dependent CMake LTO option gate, ignored source inputs bypassing inventory, and glob-based packaging outside declared payloads.
- Fixed all three; regression tests observed failing before fixes. Full Desktop suite now 18 tests, zero failures.
- Ruling: do not introduce upstream special target just to turn on an option. Keep Docker compiler-provided LTO, enforce actual generated compile flags and final link flags; do not modify global CMAKE_CXX_FLAGS or generated Ninja files.
- D1 overlay configuration refreshed after verifying all previous postimages, restoring only owned D1 overlay paths, then re-materializing. No existing out tree existed in D1; D0 untouched.
- Explicit crash-report disablement is included for alpha so fork diagnostics are not submitted as official client reports. No custom crash infrastructure or updater infrastructure is invented.
