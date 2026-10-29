Продолжай в ЭТОМ ЖЕ Work Local чате с существующим контекстом Jerkgram Desktop.

Не начинай разработку новых Jerkgram-функций. Сначала нужно исправить сам цикл сборки Linux.

# ЦЕЛЬ

Текущий production build Jerkgram Desktop неприемлем для ежедневной разработки:

- D1B compile/link campaign заняла примерно 7+ часов;
- даже изменение двух `.cpp` привело примерно к 2 часам production LTO link;
- это расходует слишком много времени и Work allowance.

Нужно создать нормальный **fast incremental development pipeline**, при этом сохранить production pipeline без ухудшения качества финальных сборок.

После этой задачи обычное изменение нескольких `.cpp` не должно требовать production LTO и многочасовой линковки.

---

# ТЕКУЩИЙ BASELINE

Builder:

`/home/pixi/Projects/Jerkgram/Desktop/jerkgram-desktop-builder`

GitHub:

`ghostbase-sg/jerkgram-desktop-builder`

D1B builder baseline:

branch:
`d1/identity-alpha`

HEAD:
`891defe6bc4c187dd61b97386e4b426f856a7b91`

Current working source/build tree:

`/home/pixi/Projects/Jerkgram/Desktop/telegram-desktop-d1`

Этот tree содержит уже собранный D1B и его `out`.

НЕ удалять и НЕ очищать его.

D1B artifact/evidence также сохранить.

Production D1B:

- Telegram Desktop upstream `v7.3.1`
- SHA `6fed91ffab9861771a75f29df65031b3c80b6941`
- Jerkgram Desktop `0.1.0-alpha.1`
- binary `Jerkgram`
- updater OFF
- credentials configured
- profile/desktop identity isolation verified
- X11/Wayland coexistence verified

---

# ВАЖНО: DOCKER IMAGE БЫЛ СЛУЧАЙНО УДАЛЁН

Ранее использовался:

`tdesktop:centos_env`

image digest:

`sha256:f8254a3af4ff32abc7cb5b5519f150d84e0df7a5fffe8cf50a2e25a20e2f8d9a`

Он был удалён через:

`docker image prune -a`

Current Docker images: none.

При этом:

**НЕ ПОТЕРЯНЫ:**

- `telegram-desktop-d1`;
- его `out`;
- собранные object files/libraries;
- D1B executable;
- builder;
- Git history;
- artifacts/evidence.

Сначала восстанови build environment стандартным воспроизводимым способом из существующей upstream/builder инфраструктуры.

Не удаляй существующий `out`.

---

# ЗАДАЧА 1 — ВОССТАНОВИТЬ TOOLCHAIN

Восстанови `tdesktop:centos_env` или эквивалентный pinned build image, используя уже доказанный upstream process.

Не экспериментируй с новой toolchain без необходимости.

Зафиксируй:

- source/scripts, из которых image восстановлен;
- resulting image ID/digest;
- размер;
- время восстановления;
- compiler/CMake/Ninja/Qt environment;
- соответствует ли он D1B environment.

Если exact old digest невозможно получить детерминированно, это допустимо, но докажи toolchain compatibility и зафиксируй новый digest.

НЕ запускать production Jerkgram rebuild только ради проверки image.

---

# ЗАДАЧА 2 — БОЛЬШЕ НЕ ТЕРЯТЬ 30 GB TOOLCHAIN

После восстановления сделать build image восстанавливаемым без повторной многочасовой компиляции dependencies.

Предпочтительный порядок:

1. исследовать возможность сохранить versioned image в GHCR:
   `ghcr.io/ghostbase-sg/...`
2. если GitHub permissions / registry limits / practical image size делают GHCR плохим вариантом — использовать другой reproducible cache/archive mechanism;
3. локальный `docker save` может быть fallback, но не единственный strategy без объяснения.

Не публиковать credentials или secrets внутри image.

Если используется GHCR:

- version/tag должен быть immutable или digest-pinned;
- builder должен знать expected digest;
- pull должен восстанавливать среду без rebuild Qt/WebRTC/FFmpeg;
- не включать source tree, credentials, user data или build output в image.

Отчёт должен сказать, как восстановить environment после полного `docker image prune`.

---

# ЗАДАЧА 3 — СОЗДАТЬ ДВА BUILD PROFILE

Нужно чётко разделить:

## A. DEV-FAST

Для ежедневной разработки.

Требования:

- Release-oriented / optimized;
- НЕ Debug как основной dev baseline;
- same product code;
- same Jerkgram identity;
- same credentials;
- same updater OFF;
- same Telegram/Jerkgram behavior;
- **LTO OFF**;
- incremental Ninja;
- reuse existing dependencies;
- reuse one persistent build tree;
- no automatic clean;
- no new full checkout/build tree per milestone;
- symbols/debug metadata можно оставить настолько, насколько это не делает rebuild существенно тяжелее.

Главная цель — минимальное время:

`edit → compile changed TU → link → run`

## B. PRODUCTION

Сохранить существующий production policy:

- Release;
- LTO ON;
- constrained:
  `-flto=1`
  `--param=lto-max-streaming-parallelism=1`
- production packaging;
- production verification.

Production build используется только для:

- milestone;
- Beta candidate;
- RC;
- public release.

Не использовать production LTO для каждого feature commit.

---

# ВАЖНО ПРО CMAKE/NINJA

НЕ:

- патчить generated Ninja files;
- редактировать `impl-Release.ninja`;
- менять CMake cache вручную хаками;
- глобально подменять flags через случайный `CMAKE_CXX_FLAGS`;
- делать `rm -rf out`;
- делать clean rebuild без доказанной необходимости.

Dev-fast должен быть выражен через нормальную builder/CMake configuration.

---

# BUILD TREE STRATEGY

Нам нельзя снова получать:

- `telegram-desktop`
- `telegram-desktop-d1`
- `telegram-desktop-d2`
- `telegram-desktop-d3`
- ...

по 40 GB каждый.

D1 tree теперь считается активной рабочей базой.

Нужно выбрать безопасную стратегию дальнейшего reuse.

Предпочтительно:

- один active source tree;
- один active dev build state;
- production artifacts отдельно;
- production configuration не должна уничтожать полезный dev cache.

Если CMake технически требует отдельный build directory для dev-fast и production — сначала измерить реальный disk impact и предложить минимальную схему.

Не создавать ещё один 40GB tree автоматически.

---

# ЗАДАЧА 4 — FIRST DEV-FAST BOOTSTRAP

После настройки dev-fast можно сделать первый bootstrap build.

Важно:

изменение compile flags с LTO → no-LTO может потребовать широкую recompilation.

Это допустимо **один раз**.

Не классифицировать эту первую bootstrap стоимость как обычную incremental стоимость.

Зафиксировать отдельно:

- сколько operations rebuilt;
- compile duration;
- link duration;
- peak RAM;
- peak swap;
- final binary size;
- disk delta.

НЕ запускать после этого production LTO rebuild.

---

# ЗАДАЧА 5 — BENCHMARK FAST LOOP

После успешного bootstrap обязательно измерить:

### Test 1 — no-op

Без изменений:

`build`

Ничего не должно массово пересобираться.

Зафиксировать duration.

### Test 2 — один маленький `.cpp`

Сделать безопасное временное no-behavior source touch/edit, которое действительно заставляет пересобрать ровно один TU.

Измерить:

- compile;
- link;
- total.

После теста вернуть source точно.

### Test 3 — два `.cpp`

То же самое для двух TU.

Измерить total.

### Test 4 — небольшой header impact

Если безопасно, проверить ограниченный header change, чтобы понять realistic rebuild fanout.

Не делать broad central-header invalidation.

### Test 5 — normal Jerkgram patch simulation

Выбрать небольшой типичный source-native Jerkgram owner и измерить realistic incremental rebuild.

Не менять поведение продукта.

---

# TARGET

Не обещать заранее конкретное время.

Но определить, можем ли мы получить practical loop порядка:

- small change: минуты;
- medium feature: десятки минут;
- тяжёлый incremental change: желательно <= 1–1.5 часа.

Главное:

**обычная разработка больше не должна включать 2-часовой LTO link.**

Если no-LTO link всё ещё занимает ненормально долго — выяснить почему и оптимизировать build graph дальше.

---

# GITHUB

GitHub builder остаётся canonical infrastructure.

Разделить обязанности:

## На каждый commit

GitHub должен быстро выполнять:

- pin verification;
- materialization;
- patch/hash verification;
- source/config checks;
- tests;
- dev-profile configuration validation.

Не обязательно выполнять полный Telegram Desktop production compile на каждый commit.

## Production

Отдельный explicit workflow:

- manual dispatch / milestone;
- production LTO;
- package;
- manifest;
- checksums;
- artifact.

Не запускать production build автоматически при каждом push.

---

# GITHUB RUNNER

Предыдущий standard runner был измерен примерно как:

- 4 CPU;
- ~16.8 GB RAM;
- ~3.2 GB swap;
- ~155 GB disk;
- ~92 GB free в том конкретном run.

D1B локально production LTO достигал примерно:

- ~29.1 GiB host used;
- ~11.46 GiB logical zram;
- один LTO worker.

Поэтому не предполагай, что standard GitHub runner гарантированно подходит для production LTO.

Но:

- source/tests/preflight/dev verification должны оставаться GitHub-friendly;
- production runner strategy исследовать отдельно;
- если нужен larger runner — архитектура builder не должна меняться.

Не запускать новый многчасовой GitHub production campaign в рамках этой задачи.

---

# STORAGE

В начале и в конце измерить:

`df -h /`

`du -sh` для Desktop trees

`docker system df`

Нельзя автоматически делать:

- `docker system prune`
- `docker image prune -a`
- `docker buildx prune`
- удаление `out`
- удаление D1 evidence/artifacts.

Builder должен прямо документировать, какие caches безопасно удалять, а какие критичны.

---

# BUILDER CHANGES

Все постоянные изменения должны жить в:

`ghostbase-sg/jerkgram-desktop-builder`

а не быть ручными undocumented командами на ноутбуке.

Создай отдельный builder milestone/branch от текущего D1B baseline, например:

`d2/fast-dev-build`

или эквивалентное понятное имя.

Не коммить полный materialized Telegram tree.

---

# ДОКУМЕНТАЦИЯ

Добавить краткую инструкцию:

## Daily development

1. materialize/update;
2. build dev-fast;
3. run;
4. test.

## Milestone production

1. verify;
2. production build;
3. runtime;
4. package.

## Disaster recovery

Если Docker image удалён:

1. pull/restore pinned toolchain;
2. verify digest;
3. continue existing build tree.

Если `out` потерян:

честно указать, что требуется bootstrap rebuild.

---

# ПОСЛЕ ИНФРАСТРУКТУРЫ

НЕ начинать автоматически:

- Deleted Messages;
- Edit History;
- Ghost Mode;
- другие product features.

Сначала закончить fast build infrastructure и показать мне результаты.

---

# DEFINITION OF DONE

Задача завершена только если:

1. build environment восстановлен;
2. он сохранён/recoverable без повторной тяжёлой dependency build;
3. dev-fast profile существует;
4. production profile сохранён;
5. dev-fast bootstrap успешно собран;
6. no-op incremental build измерен;
7. 1-TU incremental build измерен;
8. 2-TU incremental build измерен;
9. link без LTO измерен;
10. production LTO не запускался без необходимости;
11. builder changes committed/pushed;
12. working D1 source/output/artifacts не потеряны.

В финальном отчёте дай таблицу:

| Operation | Duration | Recompiled | Link | Peak RAM | Disk delta |
|---|---:|---:|---:|---:|---:|
| Toolchain restore | | | | | |
| First dev-fast bootstrap | | | | | |
| No-op build | | | | | |
| 1 TU | | | | | |
| 2 TU | | | | | |
| Typical small patch | | | | | |

И отдельно:

- old production D1B cost;
- new practical dev cost;
- exact commands/workflows для daily development;
- exact recovery procedure после `docker image prune`;
- Git commit SHA;
- GitHub checks/workflows;
- что осталось нерешённым.

Главный критерий:

**после этого обычная разработка Jerkgram Desktop не должна требовать production LTO и многочасовой сборки на каждое изменение.**