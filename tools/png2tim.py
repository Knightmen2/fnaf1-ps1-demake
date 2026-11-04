#!/usr/bin/env python3
"""Convert 8-bit/RGBA PNG to PlayStation TIM (8-bit CLUT)."""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

from PIL import Image


def rgb_to_psx(r: int, g: int, b: int, stp: int = 0) -> int:
    """15-bit BGR + semi-transparency bit."""
    return ((stp & 1) << 15) | ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3)


def image_to_tim_bytes(im: Image.Image) -> bytes:
    if im.mode != "P":
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT)

    w, h = im.size
    # TIM 8-bit pixel width must be even for word packing (2 pixels/word conceptually via bytes)
    if w & 1:
        canvas = Image.new("P", (w + 1, h), 0)
        canvas.putpalette(im.getpalette() or [])
        canvas.paste(im, (0, 0))
        im = canvas
        w, h = im.size

    pal = im.getpalette() or [0] * (256 * 3)
    # Ensure 256 RGB triples
    if len(pal) < 256 * 3:
        pal = pal + [0] * (256 * 3 - len(pal))
    clut = bytearray()
    for i in range(256):
        r, g, b = pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]
        # index 0 often treated as transparent on PS1 if STP set carefully; keep opaque black
        clut += struct.pack("<H", rgb_to_psx(r, g, b, 0))

    pixels = im.tobytes()
    # Pixel data: one byte per pixel
    pix = bytearray(pixels)

    # TIM header
    # ID=0x10, FLAG=8bit(0x02)|CLUT(0x08)=0x0A? Actually:
    # bit0-2: 0=4bit, 1=8bit, 2=16bit, 3=24bit
    # bit3: CLUT present
    # So 8-bit+CLUT = 0x01 | 0x08 = 0x09
    flag = 0x09

    # CLUT block: size includes header fields
    # clut_len = 12 + clut_data_size? Spec:
    #   uint32 bnum = size of the rest of CLUT block including itself? 
    # Common layout:
    #   uint32 clut_bnum  = 12 + clut_bytes  (includes dx,dy,w,h + data)  OR = 4+8+data
    # PSn00b / psx tools typically:
    #   clut_length = 12 + (clut_w * clut_h * 2)  where length field counts from itself
    clut_w, clut_h = 256, 1
    clut_data = bytes(clut)
    clut_bnum = 12 + len(clut_data)  # bnum includes the 4-byte bnum itself + 8 pos/size + data
    # Wait: Sony docs say bnum = size of CLUT block INCLUDING the bnum field.
    # So bnum = 4 (bnum) + 2+2+2+2 (xywh) + data = 12 + data
    clut_block = struct.pack("<IHHHH", clut_bnum, 0, 0, clut_w, clut_h) + clut_data

    # Image block
    # For 8bpp, width in TIM header is in 16-bit units of framebuffer words:
    # fb_w = pixel_width / 2  (because each VRAM word holds 2×8bit pixels)
    img_fb_w = w // 2
    img_fb_h = h
    img_bnum = 12 + len(pix)
    img_block = struct.pack("<IHHHH", img_bnum, 0, 0, img_fb_w, img_fb_h) + bytes(pix)

    return struct.pack("<II", 0x10, flag) + clut_block + img_block


def convert_file(src: Path, dst: Path) -> None:
    im = Image.open(src)
    data = image_to_tim_bytes(im)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--dst", type=Path, required=True)
    ap.add_argument("--batch", action="store_true", help="src/dst are directories")
    args = ap.parse_args()
    if args.batch:
        args.dst.mkdir(parents=True, exist_ok=True)
        n = 0
        for p in sorted(args.src.glob("*.png")):
            convert_file(p, args.dst / (p.stem + ".tim"))
            n += 1
            print("TIM", p.name, "->", p.stem + ".tim", flush=True)
        print("converted", n)
    else:
        convert_file(args.src, args.dst)
        print("wrote", args.dst)


if __name__ == "__main__":
    main()
