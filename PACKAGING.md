# Упаковка релизов FNAF1 PS1 demake

Документ описывает четыре артефакта для распространения.

## 1. GitHub (open-source исходники)

Чистый репозиторий: только `fnaf_ps1_ready/` без `build/`, без видеокадров, без `__pycache__`.

Содержимое:
- `src/`, `include/`, `tools/`, `CMakeLists.txt`, `iso.xml`, `system.cnf`
- `ps1_assets/` (TIM/VAG/atlas map)
- `DEVELOPMENT_LOG.md`, `.cursorrules`, `KEYBOARD.txt`, `PACKAGING.md`

Сборка PS1: PSn00bSDK + CMake (см. Makefile).

## 2. OriginalFnaf1Ps1 (DuckStation)

Путь: `%USERPROFILE%\Downloads\OriginalFnaf1Ps1\`
- `fnaf1.cue` + `fnaf1.bin` + `KEYBOARD.txt` + `README.txt`
- Запуск: DuckStation → Open → `fnaf1.cue` (нужен BIOS).

## 3. Fnaf1PS1Exe (Windows EXE)

Путь: `%USERPROFILE%\Downloads\Fnaf1PS1Exe\`
- ПК-сборка **без** лимитов PS1 (VRAM/SPU/CD).
- Управление как в оригинале FNAF: мышь (look / двери / свет / камеры).
- Сборка: PyInstaller из `pc_host/` (pygame).

## 4. FNAFPS1APK (Android)

Путь: `%USERPROFILE%\Downloads\FNAFPS1APK\`
- APK **без** аппаратных лимитов PS1.
- Дублированное сенсорное управление (зоны на экране).
- Сборка: Buildozer / python-for-android или Gradle wrapper (см. `android_host/`).

## Статус шагов

| Шаг | Статус |
|-----|--------|
| OriginalFnaf1Ps1 | сделано |
| GitHub push | в процессе |
| EXE | в процессе |
| APK | в процессе |

При команде «продолжай» — брать следующий незакрытый шаг из этой таблицы и `DEVELOPMENT_LOG.md`.
