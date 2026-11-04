# DEVELOPMENT LOG — FNAF 1 PS1 Demake

Журнал ведётся на русском. Каждое значимое действие фиксируется здесь.

---

## 2026-11-04 — Разные фото камер (запись 19.10.19)

Почему все cams были одинаковые: анти-0FPS фикс форсил только embed `cam0`.
Теперь при смене камеры (pad, не draw) грузится `\TIM\CAM00..10.TIM` с ISO
через `cd_load_file` + timeout; fallback cam0 если CD fail. Краткая статика при смене.

---

## 2026-11-04 — Стабильные камеры + дубли клавиш ПК

### Камеры → 0 FPS
- Причина: `assets_load_camera` / `LoadImage` в `draw_cameras` при каждом открытии.
- Фикс: `assets_preload_cameras()` в `enter_gameplay`; в draw **нет** upload.
- Пока все cams = embed `cam0` (без CD) — стабильно.

### Клавиатура ПК
- PS1 не читает KB напрямую — только pad через DuckStation.
- Каждое действие на 2–5 кнопках пада (L2/R2 двери, L1/R1/Select/L3/R3 камеры…).
- Документ: `KEYBOARD.txt` (+ копия в Desktop\FNAF1_PS1_NEW).

---

## 2026-11-04 — Анти-0FPS: полный аудит блокировок (запись 19.00.07)

Зависание на буте **`5e SKIP DOOR`** (текст на экране) → **Игра 0 FPS**.

### Все найденные клинья и фикс
| Источник | Почему 0 FPS | Фикс |
|----------|--------------|------|
| `assets_boot_load_step(4)` двери TIM | `LoadImage`+DrawSync wedge | двери снова **SKIP** |
| `DrawSync(0/1)` busy-wait | GPU IRQ не приходит | убран из upload и `render_end` |
| `CdReadSync(0)` | вечный wait на CD | poll `CdReadSync(1)` + лимит |
| `try_cd_tim` офис/камеры | CD во время игры | **отключён** (только embed) |
| `assets_load_anim_atlases` | 4×256 TIM подряд | **no-op** |
| BGM 160KB `SpuWrite` одним куском | SPU DMA stall | chunk **4KB/кадр** deferred |
| Full SFX на буте | длинная цепочка DMA | minimal на буте, full на кадре 30 |

Меню BGM урезан до ~48 КБ ADPCM (`menu_embed`).

---

## 2026-11-04 — Точные звуки + ночь + спрайты (запись 18.55.25)

### Музыка (было неправильно)
- Меню играло **`pirate_song2`** → «стремный» пиратский трек. Заменено на **`darkness_music_short.vag`** (= `darkness music.wav` из оригинала).
- Офис: только **`buzz_fan_florescent2`** (как в `musicbg2()` Python).
- Один слот SPU `0x50000`: menu/fan/mbox меняются местами (512 КБ лимит).

### Ночь «растянута»
- Было: час 43с + power 8с/% → слишком долго для demake.
- Стало: час **30с**, power как в py (**4/3/1.7/1.4/1** с), Bonnie/Chica раньше.

### Спрайты «инвертированы» / зелёные
- Неон UI: atlas battery green + неверный tpage/CLUT. Кнопки дверей → простые TILE; HUD серый; CLUT UI на `0,490`; двери грузятся на буте.
- Transition: убран Fnt поверх loading-картинки (двойной «12 AM»).

---

## 2026-11-04 — Где звуки / почему тишина

### Карта аудио сейчас
| Что | Где лежит | В игре |
|-----|-----------|--------|
| blip, door, error, windowscare, put_down, scream, static, steps, run | EXE (`incbin` VAG) | да, `audio_play(SFX_*)` |
| Меню BGM (`pirate_song2` → `menu_embed.vag`) | EXE @SPU `0x5F000` | да, на MODE_MENU |
| Fan buzz (`fan_embed.vag`) | EXE @SPU `0x50000` | да, при входе в ночь |
| MENU/FAN/MBOX/PWR/CHIME | ISO `\SND\*.VAG` | fallback / music box / chimes / power |
| ~40 остальных VAG (voiceover, laughs, garble, circus…) | только `ps1_assets/vag/` | **ещё не подключены** |

Лимит SPU RAM = **512 КБ** — нельзя вшить все оригинальные wav разом; длинные → CD, короткие → EXE.

### Фикс тишины
- После `SpuInit` не выставлялся `SpuSetCommonMasterVolume` → каналы key-on, но мастер = 0.
- ADSR2=0 глушил сэмплы → `0x80ff` / `0x1fc2`.

---

## 2026-11-04 — 0 FPS на меню (запись 17.11.27)

**Диагноз по mp4:** DuckStation Video 60 FPS, **Игра 0 FPS**, кадр меню с VHS, без текста. Эмулятор жив — вечный wait в игре.

**Причина:** в `game_update` каждые ~8–18 кадров вызывался `assets_load_menu_frame` → `LoadImage` + `DrawSync(0)` на TIM 256×240 **пока GPU ещё рисует** предыдущий OT. `DrawSync(0)` без таймаута клинит DuckStation. Плюс `draw_loading()` грузил TIM каждый кадр transition; `FntOpen` каждый кадр.

**Фикс:**
- Меню: один раз `assets_load_menu()` → `menu.tim` в OFFICE_L, `menu2.tim` в OFFICE_R.
- Twitch = `menu_pose ^= 1` (переключение tpage), **без** LoadImage в цикле.
- `DrawSync(0)` → poll `DrawSync(1)` с лимитом 200000.
- Loading TIM один раз при входе в transition.
- `FntOpen` только при смене mode.

---

## 2026-11-04 — Фикс меню: зелёный VHS / 0 FPS / Фредди / версия

По записи DuckStation `17.00.54.02`:
- **Зелёный VHS** — UI_NOISE + semi-trans (abr) давали зелёный артефакт. Заменено на серые TILE scanline + точки, без текстур/ABR.
- **0 FPS hang** — `assets_load_menu_frame` читал CD (`CdRead`) на смене позы + `VSync()` внутри `LoadImage` во время `video_draw`. CD убран для меню (только embed), VSync убран из upload, загрузка позы в `game_update` до кадра.
- **Фредди не зациклен** — был random pose + CD stall. Теперь цикл **0→1→2→3→0**, hold 10..18 кадров.
- **`v 0.2.2`** убран из меню (в оригинале только `v 1.13` у Скотта — нам не нужен).

---

## 2026-11-04 — Меню оригинала + VHS + звук + скримеры

Сверка с референсом меню (файл пользователя **не** добавлялся в ISO).

### Меню (как в оригинале)
- Пункты: **New Game** / **Continue** (D-pad Up/Down, Start/Enter = OK).
- Под Continue: `Night N` (`continue_night`, RAM-сейв без Memory Card; после победы ночь +1, max 5).
- New Game всегда ставит `night = 1`; Continue берёт `continue_night`.
- Fnt слева: заголовок Five/Nights/at/Freddy's, `>>` у выбранного пункта, `v 0.2.2`.

### Freddy twitch (не статичный PNG)
- Кадры лобби: `431/440/441/442` → `menu.tim`…`menu4.tim` (256×240, 8-bit).
- Вшиты в EXE + дубли MENU2..4 на CD `\TIM\`.
- `assets_load_menu_frame(pose)` грузит только при смене позы.
- Смена позы каждые 8..24 кадра (LCG), микро-сдвиг X/Y по `freddy.flicker`.

### VHS-эффект
- Scanline-полосы (тёмные TILE каждые 3 px, случайно).
- 18 полупрозрачных спрайтов `UI_NOISE_0..7` (abr=1) поверх лобби.

### Аудио (обход лимита SPU / тишины)
- **Причина тишины:** BGM только с CD + `SpuIsTransferCompleted(WAIT)` мог клинить; полный банк SFX не грузился на буте.
- **Решение:** вшить `fan_embed.vag` (buzz fan) и `menu_embed.vag` (pirate_song2 ≈60 КБ) в EXE.
- Раскладка SPU: SFX с `0x1010`, FAN `@0x50000`, MENU `@0x5F000`.
- `audio_update()` мягко перезапускает FAN/MENU каждые 560 кадров (~9.3 с).
- CD-стрим: WAIT → PEEK+таймаут; длинные MBOX/PWR/CHIME по-прежнему с `\SND\`.
- Бут: `audio_load_sfx()` (полный банк) + сразу `BGM_MENU`.

### Скримеры (спрайтовая анимация)
| Перс | Атлас | Кадры анимации | Примечание |
|------|-------|----------------|------------|
| Bonnie | `bonnie_atlas` 64×64 | 0..7 | scream в начале атласа |
| Chica | `chica_atlas` 64×64 | 0..7 | то же |
| Freddy | `freddy_atlas` 64×64 | 0..9 | power-out |
| Foxy | `foxy_atlas` 128×128 | 0..3 | только 4 ячейки — clamp с 6→4 |
- Ленивая загрузка атласов; shake ±2 px по кадру.

### UV / ассеты меню
| TIM | Источник raw | VRAM |
|-----|--------------|------|
| menu.tim | 431.png | OFFICE_L 640,0 CLUT 640,248 |
| menu2.tim | 440.png | то же (pose 1) |
| menu3.tim | 441.png | pose 2 |
| menu4.tim | 442.png | pose 3 |

---

## 2026-11-04 — Фикс шага 5 TIM + auto_boot_test

После `4 SPU INIT OK` зависание на `assets_boot_load` (0 FPS).
- `ResetCallback()` до GPU (DMA IRQ)
- TIM через `LoadImage2` + таймаут вместо вечного `DrawSync`
- CLUT унесён на y=480; debug `FntLoad(0,480)`
- Атласы аниматроников отложены (`assets_load_anim_atlases`)
- Скрипт: `tools/auto_boot_test.ps1` (build→deploy→DuckStation→screenshot)

## 2026-11-04 — Фикс зависшего бута в DuckStation

По записи: SCE-лого → SONY → **0 FPS**. Причина: `SYSTEM.CNF` указывал на `fnaf1.exe`, на диске файл `FNAF1.EXE`.
- Исправлен BOOT → `cdrom:\FNAF1.EXE;1`
- Ранний кадр «FNAF1 BOOT OK» до CD/audio
- DuckStation: NTSC-U + PatchFastBoot + TTY
- Обновлён `Desktop\FNAF1_PS1\`

---

## 2026-11-04 — Закрытие «Ещё нет / сыро»

### SPU / VAG
- Короткие SFX (blip, door, error, scare, put_down, scream, static, steps, run) вшиты в EXE и заливаются в SPU через `SpuWrite` DMA.
- Длинные: `MENU/FAN/MBOX/PWR/CHIME` лежат в `\SND\` на ISO; `cd_stream_vag_to_spu()` читает сектора и пишет прямо в SPU по адресу `0x50000`.
- Обрезки под лимит SPU 512 КБ: `*_short.vag` (music_box ~180 КБ, darkness ~160 КБ и т.д.).

### CD-ассеты
- Камеры `CAM00..10.TIM` и варианты офиса `OFF58/127/225/227` только с диска.
- В EXE: dark office 39 L/R, UI/font, двери, 4 атласа аниматроников, cam0 fallback.
- `fnaf1.exe` ≈ **948224** байт (без предупреждения «larger than RAM»).
- Образ: `build/fnaf1.bin` + `build/fnaf1.cue` (~5.6 МБ).

### Геймплей / видео
- Двери: `door_*_y` анимация open/shut.
- Монитор: wipe + кадры `UI_MONITOR_0..4`.
- Кам-кнопки: уникальные UV `UI_CAMBTN_*` / `ON_*`.
- Оверлеи Bonnie/Chica/Foxy на соответствующих камерах.
- Foxy: stage 0→3, hold на cam 1C (index 2), run, дверь L → откат / иначе screamer.

### VRAM (актуальная)
| Слот | X,Y | CLUT |
|------|-----|------|
| Bonnie/Chica atlas | 320/448,0 | 320/448,248 |
| Freddy/Foxy atlas | 320/576,256 | 320/576,496 |
| Cam stream | 448,256 | 448,496 |
| Office L/R | 640/768,0 | 640/768,240 |
| UI / Font | 896,256 / 640,400 | 960,240 / 960,248 |
| Door L/R | 960/992,0 | 960/992,232 |

---

## 2026-11-04 — Ревизия входа и Шаг 1

### Сканирование рабочей папки
| Тип | Кол-во | Расположение |
|-----|--------|--------------|
| Python `.py` | 1 | `FNAF-Python-main/FNAF-Python-main/fnaf1.py` |
| PNG/JPG | ~634 | `fnaf_files_for_py/images/` |
| Аудио wav/mp3/ogg | 54 | `fnaf_files_for_py/music/` |
| Шрифты `.ttf` | 1 | `fnaf_files_for_py/fonts/fnaf_font.ttf` |

### Логика Python (кратко)
- Режимы: `menu`, `transition`, `game`, `cameras`, `outpower`, `win`, `lose`.
- Офис 1600×720 со скроллом; двери L/R, свет L/R, монитор камер.
- Энергия 100%, usage 1..5 ускоряет расход.
- **Bonnie**: path steps → дверь слева; закрытая дверь = откат.
- **Chica**: path steps → дверь справа.
- **Freddy**: только после power-out (music box → screamer).
- **Foxy**: переменная есть, полноценного ИИ в Python нет.
- Час тикает каждые 43 секунды (ускоренный demake-таймер).

### Создано
- Корневые `.cursorrules`, `PS1_HARDWARE_CHEATSHEET.md`.
- Проект `fnaf_ps1_ready/` со структурой src/include/assets_raw/ps1_assets.
- Сырьё скопировано в `assets_raw/`.

### Архитектурные компромиссы (зафиксированы заранее)
1. Дисплей цели: **320×240 NTSC**, не 1280×720.
2. Офис: высота 240, ширина разрезана на **2× ≤256×240** (лево/право) для D-pad scroll.
3. Таймеры Python (float seconds) → **кадровые int-счётчики** (см. `constants.h`).
4. `random.triangular` → целый диапазон `rng_range(min,max)`.
5. Foxy: **3 статических кадра** Pirate Cove в личном атласе (экономия VRAM).
6. Скримеры: не все 20+ кадров Python — выборка ключевых поз в атлас 256×256, чтобы персонажи оставались узнаваемыми (не 8×8).
7. Нет `malloc` в цикле; всё состояние в статическом `GameState g_game`.

---

## Статус пайплайна
- [x] Шаг 1: шпора железа
- [x] Шаг 2: C-порт ядра (skeleton под PSn00bSDK)
- [x] Шаг 3: giga_compressor
- [x] Карта VRAM / UV-атласы (`atlas_map.json`, `include/atlas_uv.h`)
- [x] Список сжатого аудио (ниже + в логе компрессора)
- [x] PNG→TIM / WAV→VAG bake + GPU draw list в `video.c`
- [x] **Нативный PS1 runtime** (psxgpu / psxpad / psxspu)
- [x] Сборка `fnaf1.exe` + CD image `fnaf1.bin/.cue` через PSn00bSDK
- [x] SPU: DMA upload VAG + playback (`audio.c`, short SFX в EXE)
- [x] CD-стриминг TIM/VAG (`cd_assets.c`, `\TIM\` + `\SND\`)
- [x] Меню / анимация дверей / flip монитора / позы на камерах
- [x] Foxy AI Pirate Cove (stage → run → door check / jumpscare)
- [x] EXE ужат под 2 МБ RAM (~926 КБ)

---

## 2026-11-04 — ЦЕЛЬ: только оригинальная PS1

**Важно:** игра собирается под настоящее железо PS1 / эмуляторы (DuckStation и т.п.), не под Windows.
`host_preview.py` — опциональный черновик для проверки ассетов; **не** целевой билд.

### Установлено
- PSn00bSDK 0.24 → `C:\PSn00bSDK`
- mipsel-none-elf-gcc 12.3.0 (в комплекте SDK)
- CMake 3.28.3 → `C:\cmake`

### Нативный runtime
| Модуль | PS1 API |
|--------|---------|
| `main.c` | `ResetGraph`, `FntLoad`, цикл + `render_end` |
| `ps1_render.c` | double-buffer OT, `DrawOTagEnv`, `VSync` |
| `video.c` | `SPRT` + `DR_TPAGE`, TIM UV из `atlas_uv.h` |
| `assets.c` | `GetTimInfo` / `LoadImage` / `getTPage` / `getClut` |
| `input.c` | `InitPAD` / `StartPAD`, active-low → `ACT_*` |
| `audio.c` | `SpuInit` (+ очередь SFX; DMA VAG — следующий шаг) |

### VRAM (исправлено под FB 320x240×2)
Текстуры только при **X ≥ 640**, чтобы не затереть framebuffer.

### Сборка (путь без пробелов!)
Папка `Downloads\fnaf py files` ломает `elf2x`/`nm`. Используй junction:
```
C:\fnaf_ps1  →  ...\fnaf_ps1_ready
set PATH=C:\PSn00bSDK\bin;C:\PSn00bSDK\mipsel-none-elf\bin;C:\cmake\bin;%PATH%
set PSN00BSDK_LIBS=C:\PSn00bSDK\lib\libpsn00b
cd /d C:\fnaf_ps1
cmake --preset default
cmake --build build
```
Артефакты: `build/fnaf1.exe`, `build/fnaf1.bin`, `build/fnaf1.cue`

### Запуск
Открыть `build/fnaf1.cue` в DuckStation / PCSX-Redux / записать на CD для реального PS1.

---

## 2026-11-04 — Продолжение: runtime layer + bake

### PSn00bSDK
- На ПК **не найден** (`PSN00BSDK_LIBS` / типичные пути пусты). Сборка `.exe/.cue` отложена.
- Добавлены `CMakeLists.txt` и цели `make bake` / `make preview`.

### Новые модули C
| Файл | Роль |
|------|------|
| `src/assets.c` + `include/assets.h` | карта VRAM-слотов, stream office/cam/atlases |
| `src/audio.c` + `include/audio.h` | статическая voice-таблица SPU, SFX hooks |
| `src/video.c` (переписан) | draw list офис/камеры/HUD/скример + `video_set_backend()` |
| `include/pad.h` | общие маски кнопок |

### Звуковые события в `game.c`
- Двери → `SFX_DOOR` / `SFX_ERROR`
- Свет у окна с аниматроником → `SFX_WINDOW_SCARE`
- Монитор / камеры → `SFX_PUT_DOWN` / `SFX_BLIP`
- Screamer → `SFX_SCREAM` → lose `SFX_STATIC`
- Power-out → `SFX_POWERDOWN` + `SFX_MUSIC_BOX`

### Карта VRAM (загрузка)
```
OFFICE_L  (0,256)   256x240  CLUT (0,496)
OFFICE_R  (256,256) 256x240  CLUT (256,496)
CAM/ATL   (512,256) 256x240  CLUT (512,496)  — камера ИЛИ screamer atlas
UI        (768,256) 256x256  CLUT (768,496)
DOOR_L/R  (640/704,0) 64x240
```

### Bake-пайплайн
- `tools/png2tim.py` — 8-bit CLUT TIM (без внешних img2tim)
- `tools/wav2vag.py` — VAGp ADPCM (быстрый filter/shift pick)
- `tools/bake_binaries.py` → `ps1_assets/tim/`, `ps1_assets/vag/`
- Host: `python host_preview.py` (tkinter+Pillow, ускоренные таймеры ночи, F1 = AI awake)

### Компромиссы
- Screamer на экране = 4 тайла 64×64 (PS1 SPRT), host апскейлит cell→256×240.
- FONT atlas логически в отдельном слоте; на реальном FB 320×240 нужно аккуратно не затереть framebuffer (загрузка в свободную полосу / CD stream).
- Длинные voiceover.vag тяжёлые для SPU RAM — на диске ок, в рантайме грузить выборочно.

---

## 2026-11-04 — Шаг 2: C-порт логики

### Модули
| Файл | Роль |
|------|------|
| `src/main.c` | boot + цикл 60Hz |
| `src/game.c` | режимы, энергия, двери/свет, часы, usage |
| `src/ai.c` | Bonnie/Chica path AI, упрощённый Foxy, Freddy power-out |
| `src/input.c` | маппинг pad → abstract masks |
| `src/video.c` | заготовки отрисовки + UV-плейсхолдеры |
| `include/constants.h` | кадры вместо секунд, лимиты VRAM |
| `include/atlas_uv.h` | автоген UV из JSON |

### Компромиссы кода
- OOP Python → `GameState` / `Animatronic` / `OfficeState` / `CameraState` (статика, без malloc).
- Мышь → D-Pad scroll офиса (`scroll_x` int).
- `powerspeed` float → таблица `FR_POWER_U1..U5` в кадрах.
- Screamer: 8/8/6/10 кадров атласа вместо 20+ raw PNG.
- Foxy: stage 0..3, замедляется на cam 1C; dash = lose.
- `video.c` пока stub: реальные `SPRT`/TIM подключатся после img2tim.

---
## 2026-11-04 — Шаг 3: giga_compressor выполнен
### Архитектурные компромиссы по ассетам
- Офис 1600×720 → высота 240, ширина 512, **вертикальный разрез** на `*_L.png` / `*_R.png` (256×240), 8-bit.
- Камеры → 256×240 Indexed 8-bit.
- Bonnie/Chica/Freddy: атласы 256×256, ячейки **64×64** (16 поз, НЕ 8×8), скример + cam.
- Foxy: атлас 256×256, ячейки **128×128**, 4 кадра (читаемые стадии Cove).
- Двери отдельно: `door_L/R.png` ~62×240 8-bit.
- UI: `ui_atlas.png` 256×256; шрифт: `font_atlas.png` (цифры/AM/%/CAM).
- Аудио: mono 16-bit WAV @ 22050 (SFX) / 11025 (длинные ambience/voiceover), готово к VAG.
- Python 3.15: для pydub потребовался пакет `audioop-lts`; mp3/ogg `put_down` пропущены (есть wav).

### Карта VRAM / UV (см. также `ps1_assets/atlas_map.json`)

#### bonnie_atlas → `bonnie_atlas.png`
| Имя | X | Y | W | H |
|-----|---|---|---|---|
| frame_0 | 0 | 0 | 64 | 64 |
| frame_1 | 64 | 0 | 64 | 64 |
| frame_2 | 128 | 0 | 64 | 64 |
| frame_3 | 192 | 0 | 64 | 64 |
| frame_4 | 0 | 64 | 64 | 64 |
| frame_5 | 64 | 64 | 64 | 64 |
| frame_6 | 128 | 64 | 64 | 64 |
| frame_7 | 192 | 64 | 64 | 64 |
| frame_8 | 0 | 128 | 64 | 64 |
| frame_9 | 64 | 128 | 64 | 64 |
| frame_10 | 128 | 128 | 64 | 64 |
| frame_11 | 192 | 128 | 64 | 64 |
| frame_12 | 0 | 192 | 64 | 64 |
| frame_13 | 64 | 192 | 64 | 64 |
| frame_14 | 128 | 192 | 64 | 64 |
| frame_15 | 192 | 192 | 64 | 64 |

#### chica_atlas → `chica_atlas.png`
| Имя | X | Y | W | H |
|-----|---|---|---|---|
| frame_0 | 0 | 0 | 64 | 64 |
| frame_1 | 64 | 0 | 64 | 64 |
| frame_2 | 128 | 0 | 64 | 64 |
| frame_3 | 192 | 0 | 64 | 64 |
| frame_4 | 0 | 64 | 64 | 64 |
| frame_5 | 64 | 64 | 64 | 64 |
| frame_6 | 128 | 64 | 64 | 64 |
| frame_7 | 192 | 64 | 64 | 64 |
| frame_8 | 0 | 128 | 64 | 64 |
| frame_9 | 64 | 128 | 64 | 64 |
| frame_10 | 128 | 128 | 64 | 64 |
| frame_11 | 192 | 128 | 64 | 64 |
| frame_12 | 0 | 192 | 64 | 64 |
| frame_13 | 64 | 192 | 64 | 64 |
| frame_14 | 128 | 192 | 64 | 64 |
| frame_15 | 192 | 192 | 64 | 64 |

#### freddy_atlas → `freddy_atlas.png`
| Имя | X | Y | W | H |
|-----|---|---|---|---|
| frame_0 | 0 | 0 | 64 | 64 |
| frame_1 | 64 | 0 | 64 | 64 |
| frame_2 | 128 | 0 | 64 | 64 |
| frame_3 | 192 | 0 | 64 | 64 |
| frame_4 | 0 | 64 | 64 | 64 |
| frame_5 | 64 | 64 | 64 | 64 |
| frame_6 | 128 | 64 | 64 | 64 |
| frame_7 | 192 | 64 | 64 | 64 |
| frame_8 | 0 | 128 | 64 | 64 |
| frame_9 | 64 | 128 | 64 | 64 |
| frame_10 | 128 | 128 | 64 | 64 |
| frame_11 | 192 | 128 | 64 | 64 |
| frame_12 | 0 | 192 | 64 | 64 |
| frame_13 | 64 | 192 | 64 | 64 |

#### foxy_atlas → `foxy_atlas.png`
| Имя | X | Y | W | H |
|-----|---|---|---|---|
| frame_0 | 0 | 0 | 128 | 128 |
| frame_1 | 128 | 0 | 128 | 128 |
| frame_2 | 0 | 128 | 128 | 128 |
| frame_3 | 128 | 128 | 128 | 128 |

#### ui_atlas → `ui_atlas.png`
| Имя | X | Y | W | H |
|-----|---|---|---|---|
| battery_0 | 0 | 0 | 32 | 10 |
| battery_1 | 32 | 0 | 32 | 10 |
| battery_2 | 64 | 0 | 32 | 10 |
| battery_3 | 96 | 0 | 32 | 10 |
| battery_4 | 128 | 0 | 32 | 10 |
| usage | 160 | 0 | 40 | 8 |
| power_label | 200 | 0 | 48 | 5 |
| night_label | 0 | 16 | 40 | 9 |
| am | 40 | 16 | 23 | 14 |
| record_0 | 70 | 16 | 16 | 16 |
| record_1 | 88 | 16 | 16 | 16 |
| mon_open | 110 | 16 | 48 | 5 |
| nose | 160 | 16 | 12 | 12 |
| btnL_0 | 0 | 36 | 18 | 48 |
| btnL_1 | 36 | 36 | 18 | 48 |
| btnL_2 | 72 | 36 | 18 | 48 |
| btnL_3 | 108 | 36 | 18 | 48 |
| btnR_0 | 144 | 36 | 18 | 48 |
| btnR_1 | 180 | 36 | 18 | 48 |
| btnR_2 | 216 | 36 | 18 | 48 |
| cambtn_0 | 0 | 90 | 21 | 14 |
| cambtn_1 | 22 | 90 | 21 | 14 |
| cambtn_2 | 44 | 90 | 21 | 14 |
| cambtn_3 | 66 | 90 | 21 | 14 |
| cambtn_4 | 88 | 90 | 21 | 14 |
| cambtn_5 | 110 | 90 | 21 | 14 |
| cambtn_6 | 132 | 90 | 21 | 14 |
| cambtn_7 | 154 | 90 | 21 | 14 |
| cambtn_8 | 176 | 90 | 21 | 14 |
| cambtn_9 | 198 | 90 | 21 | 14 |
| cambtn_10 | 220 | 90 | 21 | 14 |
| cambtn_on_0 | 0 | 106 | 21 | 14 |
| cambtn_on_1 | 22 | 106 | 21 | 14 |
| cambtn_on_2 | 44 | 106 | 21 | 14 |
| cambtn_on_3 | 66 | 106 | 21 | 14 |
| cambtn_on_4 | 88 | 106 | 21 | 14 |
| cambtn_on_5 | 110 | 106 | 21 | 14 |
| cambtn_on_6 | 132 | 106 | 21 | 14 |
| cambtn_on_7 | 154 | 106 | 21 | 14 |
| cambtn_on_8 | 176 | 106 | 21 | 14 |
| cambtn_on_9 | 198 | 106 | 21 | 14 |
| cambtn_on_10 | 220 | 106 | 21 | 14 |
| cam_nav | 0 | 124 | 56 | 56 |
| noise_0 | 60 | 124 | 24 | 14 |
| noise_1 | 84 | 124 | 24 | 14 |
| noise_2 | 108 | 124 | 24 | 14 |
| noise_3 | 132 | 124 | 24 | 14 |
| noise_4 | 156 | 124 | 24 | 14 |
| noise_5 | 180 | 124 | 24 | 14 |
| noise_6 | 204 | 124 | 24 | 14 |
| noise_7 | 228 | 124 | 24 | 14 |
| monitor_0 | 60 | 148 | 32 | 18 |
| monitor_1 | 92 | 148 | 32 | 18 |
| monitor_2 | 124 | 148 | 32 | 18 |
| monitor_3 | 156 | 148 | 32 | 18 |
| monitor_4 | 188 | 148 | 32 | 18 |
| door_l_ref | 0 | 188 | 17 | 64 |
| door_r_ref | 30 | 188 | 17 | 64 |

#### font_atlas → `font_atlas.png`
| Имя | X | Y | W | H |
|-----|---|---|---|---|
| 0 | 0 | 0 | 16 | 24 |
| 1 | 16 | 0 | 16 | 24 |
| 2 | 32 | 0 | 16 | 24 |
| 3 | 48 | 0 | 16 | 24 |
| 4 | 64 | 0 | 16 | 24 |
| 5 | 80 | 0 | 16 | 24 |
| 6 | 96 | 0 | 16 | 24 |
| 7 | 112 | 0 | 16 | 24 |
| 8 | 128 | 0 | 16 | 24 |
| 9 | 144 | 0 | 16 | 24 |
| A | 160 | 0 | 16 | 24 |
| M | 176 | 0 | 16 | 24 |
| % | 192 | 0 | 16 | 24 |
| C | 208 | 0 | 16 | 24 |

### Офис / камеры
- Каждый office_*_L/R: x=0,y=0,w=256,h=240 (отдельный файл = отдельная загрузка в TPage).
- cam_XX_*: x=0,y=0,w=256,h=240.

### Аудио (готово к VAG)
| Исходник | Выход | Hz | Bits | Ch |
|----------|-------|----|------|----|
| ambience2.wav | ambience2_ps1.wav | 11025 | 16 | 1 |
| BallastHumMedium2.wav | ballasthummedium2_ps1.wav | 11025 | 16 | 1 |
| blip3.wav | blip3_ps1.wav | 22050 | 16 | 1 |
| buzz_fan_florescent2.wav | buzz_fan_florescent2_ps1.wav | 11025 | 16 | 1 |
| CAMERA_VIDEO_LOA_60105303.wav | camera_video_loa_60105303_ps1.wav | 22050 | 16 | 1 |
| chimes 2.wav | chimes_2_ps1.wav | 11025 | 16 | 1 |
| circus.wav | circus_ps1.wav | 11025 | 16 | 1 |
| ColdPresc B.wav | coldpresc_b_ps1.wav | 11025 | 16 | 1 |
| COMPUTER_DIGITAL_L2076505.wav | computer_digital_l2076505_ps1.wav | 11025 | 16 | 1 |
| CROWD_SMALL_CHIL_EC049202.wav | crowd_small_chil_ec049202_ps1.wav | 22050 | 16 | 1 |
| darkness music.wav | darkness_music_ps1.wav | 11025 | 16 | 1 |
| deep_steps.wav | deep_steps_ps1.wav | 22050 | 16 | 1 |
| DOOR_POUNDING_ME_D0291401.wav | door_pounding_me_d0291401_ps1.wav | 22050 | 16 | 1 |
| DoorClose.wav | doorclose_ps1.wav | 22050 | 16 | 1 |
| EerieAmbienceLargeSca_MV005.wav | eerieambiencelargesca_mv005_ps1.wav | 11025 | 16 | 1 |
| error.wav | error_ps1.wav | 22050 | 16 | 1 |
| garble1.wav | garble1_ps1.wav | 22050 | 16 | 1 |
| garble2.wav | garble2_ps1.wav | 22050 | 16 | 1 |
| garble3.wav | garble3_ps1.wav | 22050 | 16 | 1 |
| knock2.wav | knock2_ps1.wav | 22050 | 16 | 1 |
| Laugh_Giggle_Girl_1.wav | laugh_giggle_girl_1_ps1.wav | 22050 | 16 | 1 |
| Laugh_Giggle_Girl_1d.wav | laugh_giggle_girl_1d_ps1.wav | 22050 | 16 | 1 |
| Laugh_Giggle_Girl_2d.wav | laugh_giggle_girl_2d_ps1.wav | 22050 | 16 | 1 |
| Laugh_Giggle_Girl_8d.wav | laugh_giggle_girl_8d_ps1.wav | 22050 | 16 | 1 |
| MiniDV_Tape_Eject_1.wav | minidv_tape_eject_1_ps1.wav | 11025 | 16 | 1 |
| music box.wav | music_box_ps1.wav | 11025 | 16 | 1 |
| OVEN-DRA_1_GEN-HDF18119.wav | oven-dra_1_gen-hdf18119_ps1.wav | 22050 | 16 | 1 |
| OVEN-DRA_2_GEN-HDF18120.wav | oven-dra_2_gen-hdf18120_ps1.wav | 22050 | 16 | 1 |
| OVEN-DRA_7_GEN-HDF18121.wav | oven-dra_7_gen-hdf18121_ps1.wav | 11025 | 16 | 1 |
| OVEN-DRAWE_GEN-HDF18122.wav | oven-drawe_gen-hdf18122_ps1.wav | 22050 | 16 | 1 |
| PartyFavorraspyPart_AC01__3.wav | partyfavorraspypart_ac01__3_ps1.wav | 22050 | 16 | 1 |
| pirate song2.wav | pirate_song2_ps1.wav | 11025 | 16 | 1 |
| powerdown.wav | powerdown_ps1.wav | 11025 | 16 | 1 |
| put_down.wav | put_down_ps1.wav | 22050 | 16 | 1 |
| robotvoice.wav | robotvoice_ps1.wav | 11025 | 16 | 1 |
| run.wav | run_ps1.wav | 22050 | 16 | 1 |
| running fast3.wav | running_fast3_ps1.wav | 22050 | 16 | 1 |
| static.wav | static_ps1.wav | 11025 | 16 | 1 |
| static2.wav | static2_ps1.wav | 11025 | 16 | 1 |
| Vocals_Breaths_S_35972006.wav | vocals_breaths_s_35972006_ps1.wav | 22050 | 16 | 1 |
| Vocals_Breaths_S_35972008.wav | vocals_breaths_s_35972008_ps1.wav | 22050 | 16 | 1 |
| Vocals_Breaths_S_35972012.wav | vocals_breaths_s_35972012_ps1.wav | 22050 | 16 | 1 |
| Vocals_Breaths_S_35972014.wav | vocals_breaths_s_35972014_ps1.wav | 22050 | 16 | 1 |
| voiceover1c.wav | voiceover1c_ps1.wav | 11025 | 16 | 1 |
| voiceover2a.wav | voiceover2a_ps1.wav | 11025 | 16 | 1 |
| voiceover3.wav | voiceover3_ps1.wav | 11025 | 16 | 1 |
| voiceover4.wav | voiceover4_ps1.wav | 11025 | 16 | 1 |
| voiceover5.wav | voiceover5_ps1.wav | 11025 | 16 | 1 |
| whispering2.wav | whispering2_ps1.wav | 11025 | 16 | 1 |
| windowscare.wav | windowscare_ps1.wav | 22050 | 16 | 1 |
| XSCREAM.wav | xscream_ps1.wav | 22050 | 16 | 1 |
| XSCREAM2.wav | xscream2_ps1.wav | 11025 | 16 | 1 |
