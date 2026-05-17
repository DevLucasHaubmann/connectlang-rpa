#!/usr/bin/env python3
"""Generates assets/icon.ico for the ConnectLang RPA desktop app.

Run from the project root:
    uv run python scripts/generate_icon.py

Design:
- Background: #111318 (matches theme.BG_PRIMARY)
- Symbol: #e94560 (matches theme.ACCENT — the primary action red)
- Shape: play triangle (▶), representing run/automate
- Sizes: 256x256, 48x48, 32x32, 16x16
"""
from __future__ import annotations

import struct
from pathlib import Path

_OUTPUT = Path(__file__).parent.parent / "assets" / "icon.ico"

# BGRA tuples — Windows BMP stores channels in B, G, R, A order
_BG = (24, 19, 17, 255)       # #111318
_ACCENT = (96, 69, 233, 255)  # #e94560  (R=233, G=69, B=96 → BGRA = 96,69,233,255)


def _sign(x1: int, y1: int, x2: int, y2: int, x3: int, y3: int) -> int:
    return (x1 - x3) * (y2 - y3) - (x2 - x3) * (y1 - y3)


def _in_triangle(
    px: int, py: int,
    ax: int, ay: int,
    bx: int, by: int,
    cx: int, cy: int,
) -> bool:
    d1 = _sign(px, py, ax, ay, bx, by)
    d2 = _sign(px, py, bx, by, cx, cy)
    d3 = _sign(px, py, cx, cy, ax, ay)
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (has_neg and has_pos)


def _make_pixels(size: int) -> bytes:
    """Returns a flat BGRA pixel array in bottom-to-top row order (BMP convention)."""
    # Play triangle vertices, with proportional margins
    margin = max(2, int(size * 0.22))
    inner_margin = max(1, int(size * 0.05))

    ax = margin               # left edge (top-left and bottom-left vertices)
    bx = ax
    cx = size - margin        # right vertex (tip of arrow)

    ay = margin + inner_margin      # top-left vertex
    by = size - margin - inner_margin  # bottom-left vertex
    cy = size // 2             # right vertex (vertical center)

    rows: list[int] = []
    for row in range(size - 1, -1, -1):  # BMP rows are bottom-to-top
        for col in range(size):
            color = _ACCENT if _in_triangle(col, row, ax, ay, bx, by, cx, cy) else _BG
            rows.extend(color)
    return bytes(rows)


def _make_and_mask(size: int) -> bytes:
    """AND mask: all zeros = fully opaque (alpha channel is used for 32bpp)."""
    row_stride = ((size + 31) // 32) * 4  # padded to 4-byte boundary
    return bytes(row_stride * size)


def _make_dib(size: int) -> bytes:
    """Returns a Device Independent Bitmap (BMP without file header) for one icon size."""
    pixels = _make_pixels(size)
    and_mask = _make_and_mask(size)

    header = struct.pack(
        "<IiiHHIIiiII",
        40,        # biSize: header size
        size,      # biWidth
        size * 2,  # biHeight: doubled in ICO format (XOR + AND stacked)
        1,         # biPlanes
        32,        # biBitCount: 32bpp BGRA
        0,         # biCompression: BI_RGB (uncompressed)
        0,         # biSizeImage: can be 0 for BI_RGB
        0, 0,      # biXPelsPerMeter, biYPelsPerMeter
        0, 0,      # biClrUsed, biClrImportant
    )
    return header + pixels + and_mask


def generate() -> None:
    sizes = [256, 48, 32, 16]
    dibs = [_make_dib(s) for s in sizes]

    # ICO directory header: reserved=0, type=1 (icon), count=N
    ico = struct.pack("<HHH", 0, 1, len(sizes))

    # ICONDIRENTRY array — offsets start after header (6 bytes) + entries (16 * N bytes)
    offset = 6 + 16 * len(sizes)
    for size, dib in zip(sizes, dibs, strict=True):
        ico += struct.pack(
            "<BBBBHHII",
            0 if size == 256 else size,  # bWidth: 0 means 256 in ICO format
            0 if size == 256 else size,  # bHeight: same
            0,          # bColorCount: 0 for 32bpp (no palette)
            0,          # bReserved
            1,          # wPlanes
            32,         # wBitCount
            len(dib),   # dwBytesInRes
            offset,     # dwImageOffset: byte offset from start of file
        )
        offset += len(dib)

    for dib in dibs:
        ico += dib

    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_bytes(ico)
    print(f"Generated: {_OUTPUT}  ({len(ico):,} bytes)")
    for s in sizes:
        print(f"  {s:>3}x{s}")


if __name__ == "__main__":
    generate()
