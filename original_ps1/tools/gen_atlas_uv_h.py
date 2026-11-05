#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
m = json.loads((root / "ps1_assets" / "atlas_map.json").read_text(encoding="utf-8"))
m["doors"] = {
    "L": {"file": "door_L.png", "x": 0, "y": 0, "w": 62, "h": 240},
    "R": {"file": "door_R.png", "x": 0, "y": 0, "w": 62, "h": 240},
}
(root / "ps1_assets" / "atlas_map.json").write_text(
    json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8"
)

lines = [
    "#ifndef FNAF_ATLAS_UV_H",
    "#define FNAF_ATLAS_UV_H",
    "",
    "/* Auto-generated from atlas_map.json — do not hand-edit */",
    "",
]


def emit_rect(name, s):
    lines.append(f"#define {name}_U  {s['x']}")
    lines.append(f"#define {name}_V  {s['y']}")
    lines.append(f"#define {name}_W  {s['w']}")
    lines.append(f"#define {name}_H  {s['h']}")


for atlas in ("bonnie_atlas", "chica_atlas", "freddy_atlas", "foxy_atlas"):
    block = m.get(atlas, {})
    lines.append(f"/* {atlas} -> {block.get('file', '')} */")
    for k, s in block.get("slots", {}).items():
        emit_rect(f"{atlas.upper()}_{k.upper()}", s)
    lines.append("")

ui = m.get("ui_atlas", {})
lines.append(f"/* ui_atlas -> {ui.get('file', '')} */")
for k, s in ui.get("slots", {}).items():
    key = "".join(ch if ch.isalnum() else "_" for ch in k).upper()
    emit_rect(f"UI_{key}", s)
lines.append("")

font = m.get("font_atlas", {})
lines.append(f"/* font_atlas -> {font.get('file', '')} */")
for k, s in font.get("slots", {}).items():
    if k == "%":
        key = "PCT"
    elif k.isalnum():
        key = k
    else:
        key = "SPC"
    emit_rect(f"FONT_{key}", s)

lines += ["", "#endif", ""]
(root / "include" / "atlas_uv.h").write_text("\n".join(lines), encoding="utf-8")
print("wrote include/atlas_uv.h")
