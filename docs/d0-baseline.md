# D0 stock baseline evidence summary

Official Telegram Desktop v7.3.1 at 6fed91ffab9861771a75f29df65031b3c80b6941 was compiled in Release and launched locally on 2026-10-25. A fresh-profile welcome UI was visible and the process survived startup. Login/auth was outside D0 scope. No Jerkgram product changes were present.

Default -flto=auto caused kernel-confirmed global OOM. Direct replay of the existing final link command with only -flto=1 and --param=lto-max-streaming-parallelism=1 succeeded, reusing existing objects and libraries. Relink took about 1h31m48s. Sampled host peak RAM was 28.64 GiB, zram swap 14.51 GiB; maximum concurrent LTO processes was one.

The generated Ninja file remained identical to its backup; Git stayed clean. Full local evidence is retained beside the materialized checkout and is not uploaded here. This summary does not certify a production GitHub build or a branded artifact.
