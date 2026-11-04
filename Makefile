# Native PS1 build (PSn00bSDK) — NOT a PC game.
# Prefer building via junction C:\fnaf_ps1 if source path has spaces.

export PATH := C:/PSn00bSDK/bin:C:/PSn00bSDK/mipsel-none-elf/bin:C:/cmake/bin:$(PATH)
export PSN00BSDK_LIBS := C:/PSn00bSDK/lib/libpsn00b

.PHONY: all configure build clean assets bake

all: build

configure:
	cmake --preset default

build: configure
	cmake --build build

clean:
	rm -rf build

assets:
	python giga_compressor.py

bake:
	python tools/bake_binaries.py
