# Local storage policy

Measured 2026-10-25: materialized telegram-desktop roughly 39 GB, out roughly 38 GB, out/Telegram roughly 34 GB, unstripped D0 binary roughly 3.2 GB. Docker tdesktop:centos_env is 29,959,559,875 bytes. D0 evidence is preserved separately.

BuildKit cache was already pruned from roughly 54 GB to 43.11 MB. Do not run docker system prune, docker builder prune or docker buildx prune without new evidence and an explicit need. The image and out must be retained.

Reuse a single persistent source/out tree for normal incremental work; let changed objects replace previous objects. Do not allocate another full build tree for each version. A deliberately isolated experiment needs an explicit storage decision.

Do not replace/delete/strip the original D0 binary. Stripping a COPY was observed to reduce about 3.2 GB to 239 MB. Future packages must strip staging copies before compression. The builder's packaging tests use a small fixture ELF, not the D0 binary.

Upload future release artifacts to GitHub only after release approval; retain a bounded local artifact set instead of accumulating every version. Do not export builder/dev history to the clean public source repository.


## Active D1B / fast-dev policy (2026-10-29)

Initial measurement before recovery: root 476G total, 163G used, 313G available. Active D1 tree 41G: production intermediates 34G, Release copies 6.3G; source roughly 1G. Docker image list was empty after the user's earlier prune; build cache43.11MB. These are initial measurements, not final fast-dev totals.

Keep one active source tree. `out/dev-fast` is a separate persistent CMake build directory in the same ignored `out`; it is needed because no-LTO/g1 objects are incompatible with existing production fat-LTO/full-debug objects. Switching flags in place would repeatedly invalidate both configurations. The DEV delta is measured separately during bootstrap; no new 40GB checkout is created.

Critical retained state:

- Pinned toolchain image; own digest-pinned registry copy plus checked `docker save` archive outside Docker. A local tag alone does not survive image prune.
- Production `out` objects/cache and unstripped originals: losing these costs a production bootstrap and LTO campaign.
- DEV `out/dev-fast`: losing it costs the once-only DEV bootstrap again.
- Source edits/patches, API configuration, D1 evidence, released/candidate artifacts: these are not disposable compiler caches.

Rebuildable caches (not automatically removed): BuildKit intermediate layers/source downloads and ccache. Their loss should not change source policy, but costs dependency recompilation/network traffic if image recovery is unavailable. Removing the image is only safe once an independently verified recovery copy exists; removing build state is a separate, expensive decision. Registry retention does not back up application objects or API configuration.

No prune/clean/delete operation is part of this milestone. Only temporary test fixtures and an independently verified stale DNF metadata PID lock were removed. The final report records actual Docker/image/archive/DEV sizes, not an estimate.

Measured after fast-dev bootstrap: root247G used /228G available; active D1 tree52G, checked archive10G, Docker images30.2GB and retained BuildKit volume53.4GB. DEV bootstrap added12,326,957,056 allocated bytes (~11.48GiB). No additional40GB checkout. Remote uploads failed on this network, so the checked local archive is currently the proven image recovery copy; do not delete/move it casually or claim disk-loss coverage.
