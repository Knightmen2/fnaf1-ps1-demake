[app]
title = FNAF1 PS1 Demake
package.name = fnaf1ps1
package.domain = org.fnaf.ps1demake
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,mp3,txt,md
version = 1.0.0
requirements = python3,kivy,pillow
orientation = landscape
fullscreen = 1
android.permissions = INTERNET,VIBRATE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a
p4a.branch = master
# No PS1 hardware limits — full assets packaged
android.add_assets = images:images,music:music

[buildozer]
log_level = 2
warn_on_root = 0
