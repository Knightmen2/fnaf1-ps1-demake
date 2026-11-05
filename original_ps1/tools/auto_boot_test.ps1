# FNAF1 PS1 — build, deploy, launch DuckStation, OCR boot step from screenshot.
# Usage: powershell -ExecutionPolicy Bypass -File tools\auto_boot_test.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -ErrorAction SilentlyContinue
if (Test-Path "C:\fnaf_ps1") { $Proj = "C:\fnaf_ps1" } else { $Proj = Join-Path (Split-Path $PSScriptRoot -Parent) "" }
$Dst = "C:\Users\bober\Desktop\FNAF1_PS1"
$Ds = "$env:LOCALAPPDATA\Programs\DuckStation\duckstation-qt-x64-ReleaseLTCG.exe"
$OutDir = Join-Path $Proj "build\auto_boot"
$WaitSec = 6

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $Dst | Out-Null

$env:PATH = "C:\PSn00bSDK\bin;C:\PSn00bSDK\mipsel-none-elf\bin;C:\cmake\bin;" + $env:PATH
$env:PSN00BSDK_LIBS = "C:\PSn00bSDK\lib\libpsn00b"

Write-Host "== BUILD =="
Set-Location $Proj
if (-not (Test-Path "build")) { cmake --preset default }
cmake --build build
if ($LASTEXITCODE -ne 0) { throw "build failed" }

Write-Host "== DEPLOY =="
Get-Process duckstation* -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1
Copy-Item "build\fnaf1.bin" "$Dst\fnaf1.bin" -Force
Copy-Item "build\fnaf1.exe" "$Dst\fnaf1.exe" -Force
@"
FILE `"fnaf1.bin`" BINARY
  TRACK 01 MODE2/2352
    INDEX 01 00:00:00
"@ | Set-Content "$Dst\fnaf1.cue" -Encoding ASCII

Write-Host "== LAUNCH =="
Start-Process -FilePath $Ds -ArgumentList "`"$Dst\fnaf1.cue`"" -WorkingDirectory $Dst
Start-Sleep -Seconds $WaitSec

Write-Host "== CAPTURE =="
$shot = Join-Path $OutDir ("boot_{0:yyyyMMdd_HHmmss}.png" -f (Get-Date))
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
# Grab primary screen region — DuckStation usually foreground
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bmp.Save($shot, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Host "screenshot: $shot"

# Heuristic via OpenCV OCR-ish: detect white boot text by running python if available
$py = @"
import cv2, re, sys
img = cv2.imread(sys.argv[1])
if img is None:
    print('STEP=? FILE_FAIL'); sys.exit(2)
# Crop upper band of likely DS window (rough)
h,w = img.shape[:2]
crop = img[0:h//2, 0:w]
gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
# Threshold bright text
_, th = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
# Save debug
cv2.imwrite(sys.argv[1].replace('.png','_mask.png'), th)
# Very light pattern: count non-black; user/agent reads image.
# Emit known markers if tesseract absent — agent reads PNG.
print('SHOT_OK')
print('HINT=look_for_boot_steps_1_to_8_READY')
"@
$pyPath = Join-Path $OutDir "analyze_boot.py"
Set-Content -Path $pyPath -Value $py -Encoding UTF8
python $pyPath $shot

Write-Host ""
Write-Host "Done. If stuck before '8 READY', open $shot and check last boot line."
Write-Host "Known auto-fixes already in code: ResetCallback, LoadImage2, deferred atlases/SFX."
