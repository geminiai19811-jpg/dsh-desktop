#!/usr/bin/env python3
"""Compose the dsh-desktop app icon.

DeepSeek whale (white) on a DeepSeek-blue gradient rounded square, with a
macOS-style window motif (traffic-light dots) to signal "desktop app".

Inputs:  assets/whale.png (black whale on transparent, rendered from whale.svg)
Output: assets/icon-source.png (1024x1024)

Requires Pillow:  python3 -m pip install --target ./pylibs Pillow
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pylibs"))

from PIL import Image, ImageDraw

SIZE = 1024
CORNER = 220                 # app-icon rounded-square corner radius
WHALE_SCALE = 0.62           # whale width as a fraction of the canvas

# DeepSeek-ish blue, top-left -> bottom-right.
C_TOP = (77, 107, 254)       # #4D6BFE
C_BOTTOM = (30, 58, 138)     # #1E3A8A

# macOS traffic-light colors.
TRAFFIC = [(255, 95, 87), (254, 188, 46), (40, 200, 64)]


def rounded_rect_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def diagonal_gradient(size, c1, c2):
    mid = tuple((a + b) // 2 for a, b in zip(c1, c2))
    g = Image.new("RGB", (2, 2))
    g.putpixel((0, 0), c1)
    g.putpixel((1, 1), c2)
    g.putpixel((1, 0), mid)
    g.putpixel((0, 1), mid)
    return g.resize((size, size), Image.BILINEAR)


def main():
    out = os.path.join(ROOT, "assets", "icon-source.png")
    whale_path = os.path.join(ROOT, "assets", "whale.png")

    canvas = diagonal_gradient(SIZE, C_TOP, C_BOTTOM).convert("RGBA")
    canvas.putalpha(rounded_rect_mask(SIZE, CORNER))

    # Recolor the black whale to white using its alpha channel.
    whale_black = Image.open(whale_path).convert("RGBA")
    alpha = whale_black.getchannel("A")
    whale_white = Image.new("RGBA", whale_black.size, (255, 255, 255, 255))
    whale_white.putalpha(alpha)

    w = int(SIZE * WHALE_SCALE)
    h = int(w * whale_white.height / whale_white.width)
    whale = whale_white.resize((w, h), Image.LANCZOS)
    wx = (SIZE - whale.width) // 2
    wy = (SIZE - whale.height) // 2
    canvas.alpha_composite(whale, (wx, wy))

    # Window chrome: three traffic-light dots in the top-left.
    d = ImageDraw.Draw(canvas)
    dot_r = 26
    y = 150
    x0 = 165
    gap = 68
    for i, color in enumerate(TRAFFIC):
        x = x0 + i * gap
        d.ellipse([x - dot_r, y - dot_r, x + dot_r, y + dot_r], fill=color)

    canvas.save(out)
    print(f"wrote {out}  (whale {whale.width}x{whale.height} @ ({wx},{wy}))")


if __name__ == "__main__":
    main()
