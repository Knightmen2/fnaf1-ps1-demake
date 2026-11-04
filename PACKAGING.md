# Упаковка релизов FNAF1 PS1 demake

## 1. GitHub (open-source)

https://github.com/Knightmen2/fnaf1-ps1-demake

Локальный clean tree: `%USERPROFILE%\Downloads\fnaf1-ps1-github-clean\`
(`src/`, `include/`, `ps1_assets/`, CMake, docs, `pc_host/`, `android_host/`).

## 2. OriginalFnaf1Ps1 (DuckStation) — не менять хостами

`%USERPROFILE%\Downloads\OriginalFnaf1Ps1\`
- `fnaf1.cue` + `fnaf1.bin` + `KEYBOARD.txt`
- Реальный PS1 demake с аппаратными лимитами.

## 3. Fnaf1PS1Exe (Windows)

`%USERPROFILE%\Downloads\Fnaf1PS1Exe\`
- `Fnaf1PS1.exe` + **`ps1_assets/`** (жмыхнутые graphics/audio/fonts)
- Мышь как оригинал FNAF; двери/кнопки из `door_*.png` + `ui_atlas.png`
- Меню: New Game / Continue / **Ps1Version**
- **VHS overlay** (только EXE/APK)
- Scale 320×240 → окно ×4; логика/тайминги как demake

## 4. FNAFPS1APK (Android)

`%USERPROFILE%\Downloads\FNAFPS1APK\`
- `Fnaf1PS1-debug.apk` + `ps1_assets/` + `android/`
- Touch HUD (LOOK/DOOR/LIGHT/CAMS) + **Ps1Version** + **VHS**
- Те же crushed assets, без full-res подмены

## Политика ассетов хостов

EXE/APK = визуал/звук/шрифты demake (`ps1_assets`), не raw Python media.
Единственные отличия от ISO: масштаб экрана, схема ввода (мышь/тач), VHS-оверлей, пункт меню Ps1Version.
