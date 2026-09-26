#!/usr/bin/env python3
"""
Build MakerWorld covers (4:3 + 3:4) and a screen-mockup render for Display-Puck GC9A01.

Input : docs/img/render-hero.png, render-exploded.png (from fusion/render_puck.py)
Output: docs/img/hero-screen.png   (hero render with a sample HUD on the black glass)
        docs/img/cover-4x3.png     (1600x1200)
        docs/img/cover-3x4.png     (1200x1600)

The covers use the real print photo (docs/img/photos/) when present, else the render.
The HUD on the glass of hero-screen.png is a drawn sample screen.
Usage:  python3 tools/make_covers.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "img"

# --- palette (matches the original Display-Case covers) ------------------------
BG = (11, 16, 15)
GRID = (22, 32, 29)
GREEN = (61, 255, 143)
GREEN_DIM = (30, 120, 70)
WHITE = (245, 247, 246)
GREY = (150, 160, 156)
SCREEN_BG = (4, 8, 10)
CARD_BG = (225, 228, 226)

# --- fonts ---------------------------------------------------------------------
FONT_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"

# --- texts ---------------------------------------------------------------------
TAG = "ESP32-C3 · GC9A01 1.28\" ROUND"
TITLE = ("ROUND", "DISPLAY", "PUCK")
SUBTITLE = ("Screwless 15° desk puck —", "snap-fit lid, no supports,", "same 5 browser-flash firmwares.")
PILLS = ("No screws", "No supports", "USB-C rear", "~60 min print")
BADGE = "NEW VARIANT"
FOOTER = "Display-Puck GC9A01 · github.com/medpex"

# --- geometry --------------------------------------------------------------------
GRID_STEP = 40
DARK_LUMA = 45               # render pixels darker than this = display glass
SCREEN_SUPERSAMPLE = 4
SCREEN_SIZE = 480
BODY_BRIGHTEN = 1.12
COVER_PHOTO = IMG / "photos" / "photo-angle.jpg"          # 4:3 cover (portrait card)
COVER_PHOTO_WIDE = IMG / "photos" / "photo-front-matrix.jpg"  # 3:4 cover (landscape card)
PHOTO_FOCUS_Y = 0.5         # vertical crop focus (0 = top, 1 = bottom)
PHOTO_FOCUS_Y_WIDE = 0.47
CARD_RADIUS = 28


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def draw_hud(size: int) -> Image.Image:
    """Sample HUD screen: clock, date, weather and a sun arc (round, 240x240-style)."""
    s = size * SCREEN_SUPERSAMPLE
    im = Image.new("RGB", (s, s), SCREEN_BG)
    d = ImageDraw.Draw(im)
    c = s / 2
    ring = s * 0.46
    w = int(s * 0.022)
    d.arc([c - ring, c - ring, c + ring, c + ring], 135, 405, fill=GREEN_DIM, width=w)
    d.arc([c - ring, c - ring, c + ring, c + ring], 135, 135 + 270 * 0.62, fill=GREEN, width=w)
    for i in range(12):
        a = math.radians(i * 30)
        r0, r1 = s * 0.40, s * 0.425
        d.line([c + r0 * math.cos(a), c + r0 * math.sin(a), c + r1 * math.cos(a), c + r1 * math.sin(a)],
               fill=GREY, width=max(2, w // 3))
    big = font(FONT_BOLD, int(s * 0.25))
    mid = font(FONT_BOLD, int(s * 0.075))
    small = font(FONT_REG, int(s * 0.06))
    d.text((c, c - s * 0.05), "13:37", font=big, fill=WHITE, anchor="mm")
    d.text((c, c + s * 0.14), "SA · 26 SEP", font=mid, fill=GREEN, anchor="mm")
    d.text((c, c + s * 0.25), "18°C · BERLIN", font=small, fill=GREY, anchor="mm")
    d.text((c, c - s * 0.27), "HUD", font=small, fill=GREEN_DIM, anchor="mm")
    im = im.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def put_screen(render: Image.Image) -> Image.Image:
    """Replace the dark glass area of a render by the HUD (masked by the glass pixels)."""
    rgba = render.convert("RGBA")
    arr = np.asarray(rgba).astype(np.int32)
    luma = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    dark = (luma < DARK_LUMA) & (arr[..., 3] > 200)
    labels, count = ndimage.label(dark)
    if count == 0:
        raise ValueError("no dark glass area found in render")
    sizes = ndimage.sum(dark, labels, range(1, count + 1))
    glass = labels == (int(np.argmax(sizes)) + 1)          # largest blob = glass, not edges
    glass = ndimage.binary_fill_holes(glass)
    ys, xs = np.nonzero(glass)
    if len(xs) == 0:
        raise ValueError("no dark glass area found in render")
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    hud = draw_hud(SCREEN_SIZE).resize((x1 - x0 + 1, y1 - y0 + 1), Image.LANCZOS)
    mask = Image.fromarray((glass[y0:y1 + 1, x0:x1 + 1] * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(1.2))
    body = ImageEnhance.Brightness(rgba).enhance(BODY_BRIGHTEN)
    body.paste(hud.convert("RGB"), (int(x0), int(y0)), mask)
    body.putalpha(rgba.getchannel("A"))
    return body


def background(w: int, h: int) -> Image.Image:
    im = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(im)
    for x in range(0, w, GRID_STEP):
        d.line([x, 0, x, h], fill=GRID, width=1)
    for y in range(0, h, GRID_STEP):
        d.line([0, y, w, y], fill=GRID, width=1)
    return im


def pill(d: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, f, pad=(22, 12)) -> int:
    x, y = xy
    tw = int(d.textlength(text, font=f))
    th = f.size
    d.rounded_rectangle([x, y, x + tw + 2 * pad[0], y + th + 2 * pad[1]], radius=(th + 2 * pad[1]) // 2,
                        fill=(16, 34, 26), outline=GREEN_DIM, width=2)
    d.text((x + pad[0], y + pad[1] - 2), text, font=f, fill=GREEN)
    return tw + 2 * pad[0]


def card(product: Image.Image, w: int, h: int) -> Image.Image:
    """Light rounded card with the product render, green glow border."""
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=28, fill=CARD_BG + (255,), outline=GREEN, width=4)
    p = product.copy()
    p.thumbnail((int(w * 0.95), int(h * 0.95)), Image.LANCZOS)
    c.alpha_composite(p, ((w - p.width) // 2, (h - p.height) // 2))
    return c


def card_photo(photo: Image.Image, w: int, h: int, focus_y: float = PHOTO_FOCUS_Y) -> Image.Image:
    """Card filled edge to edge with a real photo (cover crop), green border."""
    src = photo.convert("RGB")
    scale = max(w / src.width, h / src.height)
    src = src.resize((int(src.width * scale + 0.5), int(src.height * scale + 0.5)), Image.LANCZOS)
    x0 = (src.width - w) // 2
    y0 = int((src.height - h) * focus_y)
    src = src.crop((x0, y0, x0 + w, y0 + h))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=CARD_RADIUS, fill=255)
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    c.paste(src, (0, 0), mask)
    ImageDraw.Draw(c).rounded_rectangle([0, 0, w - 1, h - 1], radius=CARD_RADIUS, outline=GREEN, width=4)
    return c


def text_block(d, x, y, scale: float, max_title_w: int) -> int:
    ftag = font(FONT_BOLD, int(26 * scale))
    tag_w = int(d.textlength(TAG, font=ftag))
    d.rounded_rectangle([x, y, x + tag_w + 60, y + int(56 * scale)], radius=int(28 * scale),
                        fill=(16, 34, 26), outline=GREEN_DIM, width=2)
    d.text((x + 30, y + int(14 * scale)), TAG, font=ftag, fill=GREEN)
    y += int(100 * scale)
    size = int(118 * scale)
    ft = font(FONT_BLACK, size)
    while max(d.textlength(t, font=ft) for t in TITLE) > max_title_w and size > 40:
        size -= 4
        ft = font(FONT_BLACK, size)
    for i, t in enumerate(TITLE):
        d.text((x, y), t, font=ft, fill=GREEN if i == len(TITLE) - 1 else WHITE)
        y += int(size * 1.02)
    y += int(46 * scale)
    d.line([x, y, x + int(110 * scale), y], fill=GREEN, width=4)
    y += int(34 * scale)
    fs = font(FONT_REG, int(34 * scale))
    for line in SUBTITLE:
        d.text((x, y), line, font=fs, fill=GREY)
        y += int(46 * scale)
    y += int(28 * scale)
    fp = font(FONT_BOLD, int(26 * scale))
    px = x
    row_h = int(80 * scale)
    for i, t in enumerate(PILLS):
        if i == 2:
            px, y = x, y + row_h
        px += pill(d, (px, y), t, fp) + int(18 * scale)
    return y + row_h


def badge(im: Image.Image, x: int, y: int, scale: float) -> None:
    fb = font(FONT_BLACK, int(30 * scale))
    tmp = ImageDraw.Draw(im)
    tw = int(tmp.textlength(BADGE, font=fb))
    b = Image.new("RGBA", (tw + 56, int(70 * scale)), (0, 0, 0, 0))
    ImageDraw.Draw(b).rounded_rectangle([0, 0, b.width - 1, b.height - 1], radius=14, fill=GREEN + (255,))
    ImageDraw.Draw(b).text((28, int(16 * scale)), BADGE, font=fb, fill=BG)
    b = b.rotate(-3, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(b, (x - b.width // 2, y))


def make_card(product: Image.Image, photo, w: int, h: int, focus_y: float = PHOTO_FOCUS_Y) -> Image.Image:
    return card_photo(photo, w, h, focus_y) if photo is not None else card(product, w, h)


def cover_4x3(product: Image.Image, photo=None) -> Image.Image:
    w, h = 1600, 1200
    im = background(w, h).convert("RGBA")
    d = ImageDraw.Draw(im)
    text_block(d, 96, 170, 1.0, 640)
    cw, ch = 640, 940
    im.alpha_composite(make_card(product, photo, cw, ch), (w - cw - 70, 130))
    badge(im, w - 70 - 120, 95, 1.0)
    d.text((96, h - 90), "• " + FOOTER, font=font(FONT_BOLD, 24), fill=GREY)
    return im.convert("RGB")


def cover_3x4(product: Image.Image, photo=None) -> Image.Image:
    w, h = 1200, 1600
    im = background(w, h).convert("RGBA")
    d = ImageDraw.Draw(im)
    y_end = text_block(d, 80, 90, 0.92, 1000)
    cw, ch = w - 160, h - y_end - 170
    im.alpha_composite(make_card(product, photo, cw, ch, PHOTO_FOCUS_Y_WIDE), (80, y_end + 40))
    badge(im, w - 200, y_end + 5, 0.9)
    d.text((80, h - 80), "• " + FOOTER, font=font(FONT_BOLD, 22), fill=GREY)
    return im.convert("RGB")


def main() -> int:
    try:
        hero = Image.open(IMG / "render-hero.png")
    except OSError as exc:
        print(f"ERROR: {exc} - run fusion/render_puck.py first", file=sys.stderr)
        return 1
    shot = put_screen(hero)
    bbox = shot.getchannel("A").getbbox()
    shot = shot.crop(bbox) if bbox else shot
    shot.save(IMG / "hero-screen.png")
    photos = {}
    for key, path in (("tall", COVER_PHOTO), ("wide", COVER_PHOTO_WIDE)):
        try:
            photos[key] = Image.open(path)
        except OSError:
            print(f"no photo at {path.name} - using render")
            photos[key] = None
    cover_4x3(shot, photos["tall"]).save(IMG / "cover-4x3.png")
    cover_3x4(shot, photos["wide"]).save(IMG / "cover-3x4.png")
    print("written: hero-screen.png, cover-4x3.png, cover-3x4.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
