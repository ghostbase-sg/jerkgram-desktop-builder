# Local storage policy

Measured 2026-10-25: materialized telegram-desktop roughly 39 GB, out roughly 38 GB, out/Telegram roughly 34 GB, unstripped D0 binary roughly 3.2 GB. Docker tdesktop:centos_env is 29,959,559,875 bytes. D0 evidence is preserved separately.

BuildKit cache was already pruned from roughly 54 GB to 43.11 MB. Do not run docker system prune, docker builder prune or docker buildx prune without new evidence and an explicit need. The image and out must be retained.

Reuse a single persistent source/out tree for normal incremental work; let changed objects replace previous objects. Do not allocate another full build tree for each version. A deliberately isolated experiment needs an explicit storage decision.

Do not replace/delete/strip the original D0 binary. Stripping a COPY was observed to reduce about 3.2 GB to 239 MB. Future packages must strip staging copies before compression. The builder's packaging tests use a small fixture ELF, not the D0 binary.

Upload future release artifacts to GitHub only after release approval; retain a bounded local artifact set instead of accumulating every version. Do not export builder/dev history to the clean public source repository.
