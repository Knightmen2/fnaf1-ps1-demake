#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
giga_compressor.py — PS1 asset cook for FNAF demake.
Office split, 8-bit cams, per-animatronic atlases, UI/font atlases, audio downsample.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW_IMG = ROOT / "assets_raw" / "images"
RAW_AUD = ROOT / "assets_raw" / "music"
RAW_FNT = ROOT / "assets_raw" / "fonts"
OUT_GFX = ROOT / "ps1_assets" / "graphics"
OUT_AUD = ROOT / "ps1_assets" / "audio"
OUT_FNT = ROOT / "ps1_assets" / "fonts"
LOG = ROOT / "DEVELOPMENT_LOG.md"
MAP_JSON = ROOT / "ps1_assets" / "atlas_map.json"

# --- Source ID maps from fnaf1.py ---
OFFICE_IDS = ["39.png", "58.png", "127.png", "225.png", "227.png"]  # dark, Llight, Rlight, Bonnie, Chica
CAM_IDS = ["19.png", "48.png", "66.png", "337.png", "0.png", "62.png", "67.png", "49.png", "83.png", "42.png", "41.png"]

BONNIE_SCREAM = [
    "301.png", "300.png", "299.png", "291.png", "303.png", "293.png", "294.png", "295.png",
    "296.png", "297.png", "298.png",
]
BONNIE_CAM = ["68.png", "90.png", "120.png", "205.png", "190.png", "206.png", "188.png"]

CHICA_SCREAM = [
    "281.png", "65.png", "69.png", "216.png", "228.png", "230.png", "231.png", "232.png",
    "233.png", "234.png", "235.png", "236.png",
]
CHICA_CAM = ["224.png", "215.png", "222.png", "217.png", "219.png", "221.png", "226.png", "220.png"]

FREDDY_SCREAM = [
    "307.png", "348.png", "308.png", "309.png", "310.png", "311.png", "312.png", "313.png",
    "314.png", "315.png", "316.png", "317.png",
]
FREDDY_EXTRA = ["304.png", "305.png"]

# Foxy: Python stub — pick pirate-cove-ish frames if present, else dark office crops
FOXY_CANDIDATES = ["66.png", "337.png", "83.png", "301.png"]  # 1C etc + fallback

UI_BUTTONS_L = ["122.png", "124.png", "125.png", "130.png"]
UI_BUTTONS_R = ["134.png", "135.png", "131.png", "47.png"]
UI_BATTERY = ["212.png", "213.png", "214.png", "456.png", "455.png"]
UI_USAGE = ["209.png"]
UI_POWER = ["207.png"]
UI_NIGHT = ["447.png"]
UI_AM = ["251.png"]
UI_RECORD = ["7.png", "7_.png"]
UI_CAM_BTNS = [
    "170.png", "171.png", "177.png", "172.png", "165.png", "168.png",
    "169.png", "173.png", "174.png", "175.png", "176.png",
]
UI_CAM_BTNS_ON = [
    "170_.png", "171_.png", "177_.png", "172_.png", "165_.png", "168_.png",
    "169_.png", "173_.png", "174_.png", "175_.png", "176_.png",
]
UI_CAM_NAMES = ["54.png", "72.png", "70.png", "74.png", "76.png", "50.png", "79.png", "75.png", "71.png", "78.png", "77.png"]
UI_NAV = ["164.png"]
UI_NOISE = ["12.png", "13.png", "14.png", "15.png", "16.png", "17.png", "18.png", "20.png"]
UI_MONITOR = ["142.png", "144.png", "132.png", "133.png", "136.png"]
UI_MISC = ["420.png", "590.png", "102.png", "118.png"]

FONT_CHARS = "0123456789AM%CAM "


def ensure_dirs():
    for d in (OUT_GFX, OUT_AUD, OUT_FNT):
        d.mkdir(parents=True, exist_ok=True)


def to_indexed(im, colors=256):
    from PIL import Image
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    # Composite on black for PS1-ish look
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    bg.paste(im, mask=im.split()[-1] if im.mode == "RGBA" else None)
    rgb = bg.convert("RGB")
    return rgb.quantize(colors=colors, method=Image.MEDIANCUT)


def fit_height(im, height=240):
    from PIL import Image
    w, h = im.size
    if h == height:
        return im
    nw = max(1, int(round(w * (height / float(h)))))
    return im.resize((nw, height), Image.Resampling.LANCZOS)


def smart_cell(im, cell_w, cell_h):
    """Scale image to fit inside cell keeping aspect, paste centered on black."""
    from PIL import Image
    im = im.convert("RGBA")
    # Focus: slight center crop if ultra-wide screamer (1600x720)
    w, h = im.size
    if w > h * 1.6:
        # Keep central 70% width — animatronic usually centered
        cw = int(w * 0.70)
        left = (w - cw) // 2
        im = im.crop((left, 0, left + cw, h))
        w, h = im.size
    scale = min(cell_w / float(w), cell_h / float(h))
    nw = max(1, int(w * scale))
    nh = max(1, int(h * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 255))
    canvas.paste(im, ((cell_w - nw) // 2, (cell_h - nh) // 2), im)
    return canvas


def build_office_splits(atlas_map: dict):
    from PIL import Image
    atlas_map["office"] = {}
    for name in OFFICE_IDS:
        src = RAW_IMG / name
        if not src.exists():
            print("MISSING office", name)
            continue
        im = Image.open(src)
        im = fit_height(im, 240)
        # Target total width 512 → two 256 halves
        im = im.resize((512, 240), Image.Resampling.LANCZOS)
        left = im.crop((0, 0, 256, 240))
        right = im.crop((256, 0, 512, 240))
        stem = Path(name).stem
        lp = OUT_GFX / f"office_{stem}_L.png"
        rp = OUT_GFX / f"office_{stem}_R.png"
        to_indexed(left).save(lp)
        to_indexed(right).save(rp)
        atlas_map["office"][stem] = {
            "L": {"file": lp.name, "x": 0, "y": 0, "w": 256, "h": 240},
            "R": {"file": rp.name, "x": 0, "y": 0, "w": 256, "h": 240},
        }
        print("office", stem, "-> 2x 256x240")


def build_cameras(atlas_map: dict):
    from PIL import Image
    atlas_map["cameras"] = {}
    for i, name in enumerate(CAM_IDS):
        src = RAW_IMG / name
        if not src.exists():
            print("MISSING cam", name)
            continue
        im = Image.open(src)
        im = fit_height(im, 240)
        # Fit width into 256
        w, h = im.size
        if w != 256:
            im = im.resize((256, 240), Image.Resampling.LANCZOS)
        out = OUT_GFX / f"cam_{i:02d}_{Path(name).stem}.png"
        to_indexed(im).save(out)
        atlas_map["cameras"][f"cam{i}"] = {
            "src": name, "file": out.name, "x": 0, "y": 0, "w": 256, "h": 240
        }
        print("cam", i, name)


def pack_atlas(label: str, frames: list[str], cell: tuple[int, int], out_name: str, atlas_map: dict):
    from PIL import Image
    cell_w, cell_h = cell
    cols = 256 // cell_w
    rows = 256 // cell_h
    max_slots = cols * rows
    existing = [f for f in frames if (RAW_IMG / f).exists()]
    if not existing:
        print("NO FRAMES for", label)
        return
    if len(existing) > max_slots:
        # Evenly sample to keep scream start/mid/end recognizable
        step = len(existing) / float(max_slots)
        use = [existing[min(len(existing) - 1, int(i * step))] for i in range(max_slots)]
    else:
        use = existing

    atlas = Image.new("RGBA", (256, 256), (0, 0, 0, 255))
    slots = {}
    for idx, fname in enumerate(use):
        cx = idx % cols
        cy = idx // cols
        if cy >= rows:
            break
        im = Image.open(RAW_IMG / fname)
        cell_im = smart_cell(im, cell_w, cell_h)
        x, y = cx * cell_w, cy * cell_h
        atlas.paste(cell_im, (x, y), cell_im)
        key = f"frame_{idx}"
        slots[key] = {"src": fname, "x": x, "y": y, "w": cell_w, "h": cell_h}
    out = OUT_GFX / out_name
    to_indexed(atlas).save(out)
    atlas_map[label] = {"file": out.name, "cell": [cell_w, cell_h], "slots": slots}
    print(f"atlas {label}: {len(slots)} cells -> {out.name}")


def build_animatronic_atlases(atlas_map: dict):
    # 64x64 cells = 4x4 = 16 readable poses (NOT 8x8 mush)
    bonnie_frames = BONNIE_SCREAM + BONNIE_CAM
    pack_atlas("bonnie_atlas", bonnie_frames, (64, 64), "bonnie_atlas.png", atlas_map)

    chica_frames = CHICA_SCREAM + CHICA_CAM
    pack_atlas("chica_atlas", chica_frames, (64, 64), "chica_atlas.png", atlas_map)

    freddy_frames = FREDDY_SCREAM + FREDDY_EXTRA
    pack_atlas("freddy_atlas", freddy_frames, (64, 64), "freddy_atlas.png", atlas_map)

    foxy_frames = []
    for f in FOXY_CANDIDATES + ["102.png", "118.png", "227.png", "66.png", "337.png"]:
        if (RAW_IMG / f).exists() and f not in foxy_frames:
            foxy_frames.append(f)
    # Foxy: 3–4 larger stage frames (128x128) for Pirate Cove readability
    pack_atlas("foxy_atlas", foxy_frames[:4], (128, 128), "foxy_atlas.png", atlas_map)


def build_ui_atlas(atlas_map: dict):
    from PIL import Image
    atlas = Image.new("RGBA", (256, 256), (0, 0, 0, 255))
    slots = {}
    # Fixed grid packing to avoid overflow: dense PS1 UI strip
    # Row0 y0: batteries+labels; Row1: doors buttons; Row2: cam buttons; Row3: noise+monitor

    def blit(name: str, x: int, y: int, max_w: int, max_h: int, key: str):
        src = RAW_IMG / name
        if not src.exists():
            return
        im = Image.open(src).convert("RGBA")
        im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        w, h = im.size
        if x + w > 256 or y + h > 256:
            print("UI skip OOB", key)
            return
        atlas.paste(im, (x, y), im)
        slots[key] = {"src": name, "x": x, "y": y, "w": w, "h": h}

    x = 0
    for i, n in enumerate(UI_BATTERY):
        blit(n, x, 0, 32, 16, f"battery_{i}")
        x += 32
    blit(UI_USAGE[0], x, 0, 40, 16, "usage"); x += 40
    blit(UI_POWER[0], x, 0, 48, 16, "power_label"); x += 48
    blit(UI_NIGHT[0], 0, 16, 40, 14, "night_label")
    blit(UI_AM[0], 40, 16, 28, 14, "am")
    blit(UI_RECORD[0], 70, 16, 16, 16, "record_0")
    if len(UI_RECORD) > 1:
        blit(UI_RECORD[1], 88, 16, 16, 16, "record_1")
    blit("420.png", 110, 16, 48, 14, "mon_open")
    blit("590.png", 160, 16, 12, 12, "nose")

    x = 0
    for i, n in enumerate(UI_BUTTONS_L):
        blit(n, x, 36, 36, 48, f"btnL_{i}")
        x += 36
    for i, n in enumerate(UI_BUTTONS_R):
        blit(n, x, 36, 36, 48, f"btnR_{i}")
        x += 36

    x = 0
    for i, n in enumerate(UI_CAM_BTNS):
        blit(n, x, 90, 22, 14, f"cambtn_{i}")
        x += 22
        if x > 240:
            x = 0
    x = 0
    for i, n in enumerate(UI_CAM_BTNS_ON):
        blit(n, x, 106, 22, 14, f"cambtn_on_{i}")
        x += 22
        if x > 240:
            x = 0

    blit(UI_NAV[0], 0, 124, 56, 56, "cam_nav")
    x = 60
    for i, n in enumerate(UI_NOISE[:8]):
        blit(n, x, 124, 24, 18, f"noise_{i}")
        x += 24
    x = 60
    for i, n in enumerate(UI_MONITOR[:5]):
        blit(n, x, 148, 32, 20, f"monitor_{i}")
        x += 32

    # Door sprites scaled tiny reference (full doors stay separate cooked files)
    blit("102.png", 0, 188, 28, 64, "door_l_ref")
    blit("118.png", 30, 188, 28, 64, "door_r_ref")

    out = OUT_GFX / "ui_atlas.png"
    to_indexed(atlas).save(out)
    atlas_map["ui_atlas"] = {"file": out.name, "slots": slots}
    print("ui_atlas slots", len(slots))


def build_font_atlas(atlas_map: dict):
    from PIL import Image, ImageDraw, ImageFont
    font_path = RAW_FNT / "fnaf_font.ttf"
    if not font_path.exists():
        print("NO FONT")
        return
    # Glyph cell 16x24 → 16 cols x ~10 rows fits 256
    cell_w, cell_h = 16, 24
    atlas = Image.new("L", (256, 256), 0)
    draw = ImageDraw.Draw(atlas)
    try:
        font = ImageFont.truetype(str(font_path), 18)
    except Exception:
        font = ImageFont.load_default()
    slots = {}
    chars = list(dict.fromkeys(FONT_CHARS))  # unique preserve order
    for i, ch in enumerate(chars):
        if ch == " ":
            continue
        cx = i % 16
        cy = i // 16
        x, y = cx * cell_w, cy * cell_h
        # Center-ish
        draw.text((x + 1, y + 1), ch, fill=255, font=font)
        slots[ch] = {"x": x, "y": y, "w": cell_w, "h": cell_h}
    out = OUT_FNT / "font_atlas.png"
    # Save as 8-bit indexed-looking PNG (mode L is fine; also dump RGB palette version)
    atlas_rgb = Image.merge("RGB", (atlas, atlas, atlas))
    to_indexed(atlas_rgb.convert("RGBA"), 16).save(out)
    atlas_map["font_atlas"] = {"file": out.name, "cell": [cell_w, cell_h], "slots": slots}
    print("font_atlas glyphs", len(slots))


def compress_audio(audio_report: list):
    try:
        from pydub import AudioSegment
    except Exception as e:
        print("pydub import failed:", e)
        print("Trying wave-only fallback for .wav")
        return compress_audio_wave_fallback(audio_report)

    for src in sorted(RAW_AUD.iterdir()):
        if src.suffix.lower() not in {".wav", ".mp3", ".ogg"}:
            continue
        try:
            seg = AudioSegment.from_file(str(src))
            seg = seg.set_channels(1)
            # Prefer 22050; very long ambience → 11025
            rate = 11025 if len(seg) > 8000 else 22050
            seg = seg.set_frame_rate(rate)
            seg = seg.set_sample_width(2)  # 16-bit PCM for quality before VAG
            out_name = src.stem.lower().replace(" ", "_") + "_ps1.wav"
            out = OUT_AUD / out_name
            seg.export(str(out), format="wav")
            audio_report.append({
                "src": src.name,
                "out": out.name,
                "channels": 1,
                "sample_width_bytes": 2,
                "frame_rate": rate,
                "duration_ms": len(seg),
            })
            print("audio", src.name, "->", out.name, rate, "Hz")
        except Exception as ex:
            print("audio FAIL", src.name, ex)


def _get_audioop():
    try:
        import audioop as ao
        return ao
    except ImportError:
        try:
            import pyaudioop as ao
            return ao
        except ImportError:
            return None


def _resample_pcm16_mono(samples: bytes, rate_from: int, rate_to: int) -> bytes:
    """Naive linear resampler when audioop missing (int16 mono)."""
    import array
    if rate_from == rate_to:
        return samples
    src = array.array("h")
    src.frombytes(samples)
    if not src:
        return samples
    n_out = max(1, int(len(src) * rate_to / float(rate_from)))
    dst = array.array("h", [0] * n_out)
    for i in range(n_out):
        pos = i * (len(src) - 1) / float(max(1, n_out - 1))
        i0 = int(pos)
        i1 = min(i0 + 1, len(src) - 1)
        t = pos - i0
        dst[i] = int(src[i0] * (1.0 - t) + src[i1] * t)
    return dst.tobytes()


def compress_audio_wave_fallback(audio_report: list):
    import wave
    ao = _get_audioop()
    for src in sorted(RAW_AUD.glob("*.wav")):
        try:
            with wave.open(str(src), "rb") as w:
                nch = w.getnchannels()
                sw = w.getsampwidth()
                rate = w.getframerate()
                nframes = w.getnframes()
                frames = w.readframes(nframes)
            dur = nframes / float(rate) if rate else 0
            if ao:
                if nch == 2:
                    frames = ao.tomono(frames, sw, 0.5, 0.5)
                    nch = 1
                if sw != 2:
                    frames = ao.lin2lin(frames, sw, 2)
                    sw = 2
                target = 11025 if dur > 8 else 22050
                if rate != target:
                    frames, _ = ao.ratecv(frames, sw, 1, rate, target, None)
                    rate = target
            else:
                # Manual path: force mono int16 + resample
                import array
                if sw == 1:
                    # unsigned 8-bit → signed 16
                    src_u = array.array("B")
                    src_u.frombytes(frames)
                    tmp = array.array("h", [(v - 128) << 8 for v in src_u])
                elif sw == 2:
                    tmp = array.array("h")
                    tmp.frombytes(frames)
                else:
                    print("skip unsupported width", src.name, sw)
                    continue
                if nch == 2:
                    mono = array.array("h", [
                        (tmp[i] + tmp[i + 1]) // 2 for i in range(0, len(tmp) - 1, 2)
                    ])
                else:
                    mono = tmp
                frames = mono.tobytes()
                sw = 2
                nch = 1
                target = 11025 if dur > 8 else 22050
                frames = _resample_pcm16_mono(frames, rate, target)
                rate = target
            out_name = src.stem.lower().replace(" ", "_") + "_ps1.wav"
            out = OUT_AUD / out_name
            with wave.open(str(out), "wb") as o:
                o.setnchannels(1)
                o.setsampwidth(2)
                o.setframerate(rate)
                o.writeframes(frames)
            audio_report.append({
                "src": src.name, "out": out.name, "channels": 1,
                "sample_width_bytes": 2, "frame_rate": rate,
                "duration_ms": int(dur * 1000),
            })
            print("audio(fallback)", out.name, rate, "Hz")
        except Exception as ex:
            print("wav fail", src, ex)

    # Also convert mp3/ogg if ffmpeg available via simple skip note
    for src in list(RAW_AUD.glob("*.mp3")) + list(RAW_AUD.glob("*.ogg")):
        print("NOTE: non-wav skipped without pydub/ffmpeg:", src.name)


def append_log(atlas_map: dict, audio_report: list):
    lines = []
    lines.append("\n---\n## 2026-11-04 — Шаг 3: giga_compressor выполнен\n")
    lines.append("### Архитектурные компромиссы по ассетам\n")
    lines.append("- Офис 1600×720 → высота 240, ширина 512, **вертикальный разрез** на `*_L.png` / `*_R.png` (256×240), 8-bit.\n")
    lines.append("- Камеры → 256×240 Indexed 8-bit.\n")
    lines.append("- Аниматроники: атласы 256×256, ячейки **128×128** (не 8×8), ключевые кадры скримера + cam-позы.\n")
    lines.append("- Foxy: упрощённый атлас из доступных кадров (в Python ИИ почти отсутствует).\n")
    lines.append("- Скримеры урезаны по числу кадров, чтобы влезть в TPage и остаться узнаваемыми.\n")
    lines.append("\n### Карта VRAM / UV (см. также `ps1_assets/atlas_map.json`)\n")
    for key in ("bonnie_atlas", "chica_atlas", "freddy_atlas", "foxy_atlas", "ui_atlas", "font_atlas"):
        block = atlas_map.get(key)
        if not block:
            continue
        lines.append(f"\n#### {key} → `{block.get('file')}`\n")
        slots = block.get("slots", {})
        lines.append("| Имя | X | Y | W | H |\n|-----|---|---|---|---|\n")
        for name, s in list(slots.items())[:64]:
            lines.append(f"| {name} | {s['x']} | {s['y']} | {s['w']} | {s['h']} |\n")
        if len(slots) > 64:
            lines.append(f"| … | | | | (+{len(slots)-64} слотов в JSON) |\n")
    lines.append("\n### Офис / камеры\n")
    lines.append("- Каждый office_*_L/R: x=0,y=0,w=256,h=240 (отдельный файл = отдельная загрузка в TPage).\n")
    lines.append("- cam_XX_*: x=0,y=0,w=256,h=240.\n")
    lines.append("\n### Аудио (готово к VAG)\n")
    lines.append("| Исходник | Выход | Hz | Bits | Ch |\n|----------|-------|----|------|----|\n")
    for a in audio_report:
        bits = a["sample_width_bytes"] * 8
        lines.append(f"| {a['src']} | {a['out']} | {a['frame_rate']} | {bits} | {a['channels']} |\n")
    with LOG.open("a", encoding="utf-8") as f:
        f.writelines(lines)
    print("LOG updated")


def main():
    ensure_dirs()
    atlas_map: dict = {}
    audio_report: list = []
    print("=== GRAPHICS ===")
    build_office_splits(atlas_map)
    build_cameras(atlas_map)
    build_animatronic_atlases(atlas_map)
    build_ui_atlas(atlas_map)
    print("=== FONT ===")
    build_font_atlas(atlas_map)
    print("=== AUDIO ===")
    compress_audio(audio_report)
    MAP_JSON.write_text(json.dumps(atlas_map, indent=2, ensure_ascii=False), encoding="utf-8")
    append_log(atlas_map, audio_report)
    print("DONE. atlas_map →", MAP_JSON)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
