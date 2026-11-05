#!/usr/bin/env python3
"""
Minimal WAV (PCM16 mono) → Sony VAG (4-bit ADPCM) encoder.
Enough for SPU upload; not bit-identical to Sony tools but plays on real HW / emus.
"""
from __future__ import annotations

import argparse
import struct
import wave
from pathlib import Path

# Filter coefficients used by PS1 SPU (approx)
_FILTERS = [
    (0.0, 0.0),
    (0.9375, 0.0),
    (1.796875, -0.8125),
    (1.53125, -0.859375),
]


def _encode_block(samples28, s1: float, s2: float):
    """Fast ADPCM block: pick filter by residual energy, shift from peak."""
    best = None
    for filt, (f0, f1) in enumerate(_FILTERS):
        residuals = []
        ps1, ps2 = s1, s2
        for x in samples28:
            predicted = ps1 * f0 + ps2 * f1
            delta = x - predicted
            residuals.append(delta)
            # rough hist advance using unquantized (good enough for filter pick)
            ps2 = ps1
            ps1 = predicted + delta
        peak = max(abs(r) for r in residuals) if residuals else 0.0
        shift = 0
        while shift < 12 and (peak / (1 << shift)) > 7.5:
            shift += 1
        enc = []
        ps1, ps2 = s1, s2
        err_acc = 0.0
        for x in samples28:
            predicted = ps1 * f0 + ps2 * f1
            delta = x - predicted
            raw = delta / float(1 << shift) if shift else delta
            q = int(round(raw))
            if q > 7:
                q = 7
            if q < -8:
                q = -8
            recon = predicted + float(q << shift)
            if recon > 32767:
                recon = 32767.0
            if recon < -32768:
                recon = -32768.0
            err_acc += (x - recon) * (x - recon)
            ps2 = ps1
            ps1 = recon
            enc.append(q & 0xF)
        if best is None or err_acc < best[0]:
            best = (err_acc, filt, shift, enc, ps1, ps2)
    _, filt, shift, enc, ns1, ns2 = best
    data = bytearray(14)
    for i in range(14):
        a = enc[i * 2] & 0xF
        b = enc[i * 2 + 1] & 0xF
        data[i] = a | (b << 4)
    header = (shift & 0xF) | ((filt & 0xF) << 4)
    return header, bytes(data), ns1, ns2


def pcm16_to_vag(pcm: bytes, sample_rate: int, name: str = "VAG") -> bytes:
    # Ensure multiple of 28 samples
    samples = list(struct.unpack("<" + "h" * (len(pcm) // 2), pcm))
    while len(samples) % 28 != 0:
        samples.append(0)

    blocks = bytearray()
    s1 = s2 = 0.0
    nblocks = len(samples) // 28
    for bi in range(nblocks):
        chunk = samples[bi * 28 : (bi + 1) * 28]
        # flags: 0=normal, 1=end+loop, 2=?, 3=?, 6=loop start, 7=end
        flags = 0
        if bi == nblocks - 1:
            flags = 1  # end
        hdr, data, s1, s2 = _encode_block([float(x) for x in chunk], s1, s2)
        blocks.append(hdr)
        blocks.append(flags)
        blocks += data

    # VAGp header 48 bytes
    data_size = len(blocks)
    name_bytes = name.encode("ascii", "ignore")[:16]
    name_bytes = name_bytes + b"\x00" * (16 - len(name_bytes))
    header = struct.pack(">4sI", b"VAGp", 0x20)  # magic + version
    header += struct.pack(">I", 0)               # reserved
    header += struct.pack(">I", data_size)
    header += struct.pack(">I", sample_rate)
    header += b"\x00" * 12                       # reserved
    header += name_bytes                         # 16 bytes
    assert len(header) == 48
    return header + bytes(blocks)


def convert_wav(src: Path, dst: Path) -> None:
    with wave.open(str(src), "rb") as w:
        assert w.getnchannels() == 1, src
        assert w.getsampwidth() == 2, src
        rate = w.getframerate()
        pcm = w.readframes(w.getnframes())
    vag = pcm16_to_vag(pcm, rate, src.stem[:16])
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(vag)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--dst", type=Path, required=True)
    ap.add_argument("--batch", action="store_true")
    args = ap.parse_args()
    if args.batch:
        args.dst.mkdir(parents=True, exist_ok=True)
        n = 0
        for p in sorted(args.src.glob("*_ps1.wav")):
            convert_wav(p, args.dst / (p.stem.replace("_ps1", "") + ".vag"))
            n += 1
            print("VAG", p.name, flush=True)
        print("converted", n)
    else:
        convert_wav(args.src, args.dst)
        print("wrote", args.dst)


if __name__ == "__main__":
    main()
