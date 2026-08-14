#!/usr/bin/env python3
"""Generate a 1024x1024 source icon (rounded-square gradient + white '>' prompt).

Pure stdlib (zlib + struct). No Pillow/ImageMagick required.
Output: assets/icon-source.png
"""
import math
import os
import struct
import zlib

SIZE = 1024


def smoothstep(edge0, edge1, x):
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def sd_round_rect(px, py, cx, cy, hw, hh, r):
    qx = abs(px - cx) - (hw - r)
    qy = abs(py - cy) - (hh - r)
    ox = max(qx, 0.0)
    oy = max(qy, 0.0)
    outside = math.hypot(ox, oy)
    inside = min(max(qx, qy), 0.0)
    return outside + inside - r


def sd_segment(px, py, ax, ay, bx, by):
    abx, aby = bx - ax, by - ay
    apx, apy = px - ax, py - ay
    denom = abx * abx + aby * aby
    t = 0.0 if denom == 0 else max(0.0, min(1.0, (apx * abx + apy * aby) / denom))
    cx, cy = ax + t * abx, ay + t * aby
    return math.hypot(px - cx, py - cy)


def coverage(sd, aa=1.5):
    """1 inside, 0 outside, anti-aliased over `aa` pixels."""
    return smoothstep(-aa, aa, -sd)


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(lerp(c1[i], c2[i], t) for i in range(3))


def main():
    out = os.path.join(os.path.dirname(__file__), "..", "assets", "icon-source.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    # Palette: indigo -> cyan diagonal-ish (DeepSeek-adjacent blues).
    top = (79, 70, 229)      # #4f46e5 indigo
    bottom = (6, 182, 212)   # #06b6d4 cyan
    white = (255, 255, 255)

    cx = cy = SIZE / 2.0
    hw = hh = SIZE / 2.0 - 16.0
    radius = 220.0

    # Chevron '>' geometry: two thick strokes forming an angle.
    thick = 92.0
    x0, y0 = 356.0, 356.0
    x1, y1 = 600.0, 512.0
    x2, y2 = 356.0, 668.0
    # Cursor bar to the right of the chevron.
    cur_x0, cur_x1 = 688.0, 738.0
    cur_y0, cur_y1 = 344.0, 680.0

    raw = bytearray()
    for y in range(SIZE):
        raw.append(0)  # filter type 0 (None)
        py = y + 0.5
        t = py / SIZE
        for x in range(SIZE):
            px = x + 0.5

            # Background rounded square.
            d_bg = sd_round_rect(px, py, cx, cy, hw, hh, radius)
            a_bg = coverage(d_bg)
            base = mix(top, bottom, t)

            r, g, b, a = 0.0, 0.0, 0.0, 0.0

            # Composite white chevron + cursor over background.
            d_chev = min(sd_segment(px, py, x0, y0, x1, y1),
                         sd_segment(px, py, x1, y1, x2, y2)) - thick / 2.0
            a_chev = coverage(d_chev)
            d_cur = abs(px - (cur_x0 + cur_x1) / 2.0) - (cur_x1 - cur_x0) / 2.0
            d_cur = max(d_cur, abs(py - (cur_y0 + cur_y1) / 2.0) - (cur_y1 - cur_y0) / 2.0)
            a_cur = coverage(d_cur)
            a_fg = max(a_chev, a_cur)

            # Foreground over background.
            r = mix(base, white, a_fg)[0]
            g = mix(base, white, a_fg)[1]
            b = mix(base, white, a_fg)[2]
            a = a_bg

            raw.append(int(round(r)))
            raw.append(int(round(g)))
            raw.append(int(round(b)))
            raw.append(int(round(a * 255.0)))

    def chunk(ctype, data):
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    with open(out, "wb") as f:
        f.write(png)
    print(f"wrote {out} ({len(png)} bytes)")


if __name__ == "__main__":
    main()
