# FNAF 1 PS1 Demake (PSn00bSDK)

Open-source demake of Five Nights at Freddy's 1 for **original PlayStation 1** / DuckStation.

## Repository layout (two folders)

| Folder | What |
|--------|------|
| **`original_ps1/`** | Open-source code + assets to **build** the real PS1 demake (C / PSn00bSDK / CMake, `ps1_assets/`, optional `pc_host` / `android_host` sources) |
| **`emulator_play/`** | Ready-to-run disc image for **DuckStation**: `fnaf1.cue` + `fnaf1.bin` (+ controls) |

### Play now (emulator)

1. Install [DuckStation](https://www.duckstation.org/) and configure a PS1 BIOS.
2. Open `emulator_play/fnaf1.cue` (keep `fnaf1.bin` next to it).
3. Controls: `emulator_play/KEYBOARD.txt`.

### Build from source (hardware / ISO)

```bat
cd original_ps1
cmake --preset default
cmake --build build
```

Requires [PSn00bSDK](https://github.com/Lameguy64/PSn00bSDK). Output: `build/fnaf1.cue` + `build/fnaf1.bin`.

## Docs

- `original_ps1/DEVELOPMENT_LOG.md` (RU)
- `PACKAGING.md` — host EXE/APK local packages (not required to play via DuckStation)

## License

Fan demake for educational / homebrew purposes. FNAF belongs to Scott Cawthon / Steel Wool / etc. Redistribute assets responsibly.
