# Упаковка релизов FNAF1 PS1 demake

Документ описывает четыре артефакта для распространения.

## 1. GitHub (open-source исходники)

Чистый tree: `%USERPROFILE%\Downloads\fnaf1-ps1-github-clean\`
(только `fnaf_ps1_ready` без `build/`, без мусора).

Содержимое:
- `src/`, `include/`, `tools/`, `CMakeLists.txt`, `iso.xml`, `system.cnf`
- `ps1_assets/` (TIM/VAG/atlas map)
- `DEVELOPMENT_LOG.md`, `.cursorrules`, `KEYBOARD.txt`, `PACKAGING.md`

Сборка PS1: PSn00bSDK + CMake.

**Статус push:** локальный git commit готов; нужен `gh auth login` (device code), затем:

```bat
cd %USERPROFILE%\Downloads\fnaf1-ps1-github-clean
gh repo create fnaf1-ps1-demake --public --source=. --remote=origin --push
```

## 2. OriginalFnaf1Ps1 (DuckStation)

Путь: `%USERPROFILE%\Downloads\OriginalFnaf1Ps1\`
- `fnaf1.cue` + `fnaf1.bin` + `KEYBOARD.txt` + `README.txt`
- Запуск: DuckStation → Open → `fnaf1.cue` (нужен BIOS).
- Это **оригинальный PS1 demake** с аппаратными лимитами.

## 3. Fnaf1PS1Exe (Windows EXE)

Путь: `%USERPROFILE%\Downloads\Fnaf1PS1Exe\`
- `Fnaf1PS1.exe` + папки `images/` и `music/` (+ `main.py` исходник)
- **Без** лимитов PS1 (VRAM/SPU/CD/TPage).
- Управление как в оригинале FNAF: **мышь** (look / двери / свет / камеры).
- Исходник сборки: `pc_host/main.py`, скрипт `pc_host/build_exe.ps1`.

## 4. FNAFPS1APK (Android)

Путь: `%USERPROFILE%\Downloads\FNAFPS1APK\`
- Готовый APK: `Fnaf1PS1-debug.apk`
- Исходники Gradle: `android/`
- Браузерный smoke-test: `www/index.html` + `images/`
- **Без** аппаратных лимитов PS1.
- Дублированное сенсорное управление (LOOK/DOOR/LIGHT/CAMS на экране).
- Пересборка: `cd android && set JAVA_HOME=C:\Program Files\Java\jdk-17 && gradlew.bat assembleDebug`

## Статус шагов

| Шаг | Статус |
|-----|--------|
| OriginalFnaf1Ps1 | **готово** |
| Fnaf1PS1Exe | **готово** (`Fnaf1PS1.exe`) |
| FNAFPS1APK | **готово** (`Fnaf1PS1-debug.apk`) |
| GitHub push | **ждёт `gh auth login`** (локальный repo готов) |
| DEVELOPMENT_LOG | обновлён |

При команде «продолжай» — в первую очередь завершить GitHub push после авторизации.
