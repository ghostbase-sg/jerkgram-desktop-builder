# Foundation verification — 2026-10-25

Public builder: https://github.com/ghostbase-sg/jerkgram-desktop-builder

Initial implementation commit: 6aafa71ba23110d9297851fa8e4490009e02f96c.
Verified Actions preflight: https://github.com/ghostbase-sg/jerkgram-desktop-builder/actions/runs/40188365538

All job steps succeeded. The downloaded evidence artifact confirms upstream SHA 6fed91ffab9861771a75f29df65031b3c80b6941, zero product changes and full_build_executed=false. Eight builder tests passed locally and on CI. Packaging tests only strip/archive a small fixture ELF; no D0 packaging or new Telegram compilation was performed.

Measured runner: Ubuntu 24.04.5 LTS, 4 CPUs, 16,766,414,848 bytes RAM, 3,221,221,376 bytes swap, 154,894,188,544 bytes disk with 91,726,893,056 bytes free at preflight. These figures are evidence for this run, not guaranteed runner capacity or a successful production build.

Both TDESKTOP_API_ID and TDESKTOP_API_HASH Actions Secrets were absent. No values were uploaded, printed or changed. They remain production blockers; a secure source must be supplied explicitly before transfer.

The local materialized source remains branch jerkgram/7.3.1 at the exact pinned upstream SHA, with clean tracked files and upstream fetch remote https://github.com/telegramdesktop/tdesktop.git. Push to upstream is deliberately disabled. The separate builder checkout uses main with origin pointing to this builder repository. The public source/release repository was not created.

Preserved: roughly 38 GB out, original 3,340,519,960-byte D0 ELF, D0 evidence, and the 29,959,559,875-byte tdesktop:centos_env image. BuildKit cache remains roughly 43.11 MB after the earlier user cleanup. No prune was run in this task.

Remaining production gates: provision both API Secrets; separately select and test a suitable persistent/larger runner with measured disk/RAM/swap; prepare or provide a pinned toolchain image and record provenance; then run an explicitly authorized clean production campaign with runtime evidence. This preflight does not close those gates.

Next product work: focused read-only D1 identity audit using docs/d1-audit.md. No branding or feature changes were made here.
