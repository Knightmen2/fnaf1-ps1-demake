# Build Fnaf1PS1Exe with PyInstaller (no PS1 HW limits, mouse controls)
$ErrorActionPreference = "Stop"
$ws = Split-Path $PSScriptRoot -Parent
$out = Join-Path $env:USERPROFILE "Downloads\Fnaf1PS1Exe"
$img = Join-Path $ws "fnaf_files_for_py\images"
$music = Join-Path $ws "fnaf_files_for_py\music"

New-Item -ItemType Directory -Force -Path $out | Out-Null
Copy-Item (Join-Path $PSScriptRoot "main.py") (Join-Path $out "main.py") -Force

python -m pip install -q pygame-ce pyinstaller

Push-Location $out
python -m PyInstaller --noconfirm --onefile --windowed `
  --name "Fnaf1PS1" `
  --distpath "$out\dist" `
  --workpath "$out\build" `
  --specpath "$out" `
  --add-data "$img;images" `
  --add-data "$music;music" `
  main.py

# Flatten: put exe + asset folders for portable run without unpacking
Copy-Item "$out\dist\Fnaf1PS1.exe" "$out\Fnaf1PS1.exe" -Force
if (-not (Test-Path "$out\images")) {
  robocopy $img "$out\images" /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
}
if (-not (Test-Path "$out\music")) {
  robocopy $music "$out\music" /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
}

@"
# Fnaf1PS1Exe — PC build (no PS1 hardware limits)

## Run
Double-click ``Fnaf1PS1.exe`` (assets ``images/`` + ``music/`` must sit next to it).

Or: ``python main.py`` with pygame-ce installed.

## Controls (original FNAF mouse scheme)
- Move mouse to left/right edges of the screen to pan the office
- Click door buttons (grey rectangles on left/right walls) to toggle doors
- Hold mouse on yellow light zones to shine hallway lights
- Click bottom CAMERAS bar to flip tablet; click CAM 1–11 buttons
- Esc — return to menu / quit from menu

## Notes
- Full-resolution textures (no 256x256 TPage / 2 MB RAM / VRAM caps)
- Night logic simplified from PS1 demake (Bonnie + Chica)
"@ | Set-Content "$out\README.md" -Encoding UTF8

Pop-Location
Write-Host "OK: $out\Fnaf1PS1.exe"
