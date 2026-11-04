#!/usr/bin/env python3
"""Bake PNG→TIM and WAV→VAG into ps1_assets/tim and ps1_assets/vag."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(args):
    print("+", " ".join(args), flush=True)
    subprocess.check_call(args)


def main():
    gfx = ROOT / "ps1_assets" / "graphics"
    aud = ROOT / "ps1_assets" / "audio"
    fnt = ROOT / "ps1_assets" / "fonts"
    tim = ROOT / "ps1_assets" / "tim"
    vag = ROOT / "ps1_assets" / "vag"
    tim.mkdir(parents=True, exist_ok=True)
    vag.mkdir(parents=True, exist_ok=True)

    run([PY, str(ROOT / "tools" / "png2tim.py"), "--batch", "--src", str(gfx), "--dst", str(tim)])
    if (fnt / "font_atlas.png").exists():
        run([
            PY, str(ROOT / "tools" / "png2tim.py"),
            "--src", str(fnt / "font_atlas.png"),
            "--dst", str(tim / "font_atlas.tim"),
        ])

    # Convert critical SFX first list, then rest
    run([PY, str(ROOT / "tools" / "wav2vag.py"), "--batch", "--src", str(aud), "--dst", str(vag)])
    print("BAKE OK")


if __name__ == "__main__":
    main()
