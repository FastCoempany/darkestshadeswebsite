#!/usr/bin/env python3
"""The one grade every rendered image of the drawer wall goes through (DRAWER-WALL.md, "The look": the prototype's
grade, docs/build/drawer-wall/prototype/grade.py, made a tool). Luminance-weighted film grain about 2.8%, a little
halation on the brightest highlights, a soft vignette, a touch of lens softness, a warm or cool cast; identical on
every asset, the grain seeded per output file so a frame looks the same every time it is built.

    python3 tools/photo/grade_scene.py work/wall/portrait-lit.png wall/assets/wall/portrait/black-relief/plate-lit.avif --look cool --width 1170
    python3 tools/photo/grade_scene.py in.png out.webp --look warm --crop x0 y0 x1 y1 --width 720 --quality 80

Scene black is exact (DRAWER-WALL.md, Assets): the outermost 2% of every output is pure black, whatever the grade does
inside, and no grain is added to pixels the render left black. The input is a render as Blender wrote it (8- or 16-bit
PNG, AgX already applied, sRGB); the output is PNG, JPEG, WebP or AVIF by its extension.
"""
import argparse
import hashlib
import pathlib
import sys

import cv2
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

EDGE_BLACK = 0.02          # the outermost 2% of the frame is exactly scene black
EDGE_FADE = 0.06           # the fade into it starts here


def to_linear(s):
    return np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)


def to_srgb(l):
    l = np.clip(l, 0, 1)
    return np.where(l <= 0.0031308, l * 12.92, 1.055 * l ** (1 / 2.4) - 0.055)


def load(path):
    """An image as linear RGB float32 over black (an alpha channel is composited over black)."""
    im = Image.open(path)
    mode = im.mode
    if mode in ("I;16", "I;16B", "I"):
        a = np.asarray(im).astype(np.float32) / 65535
        a = np.repeat(a[..., None], 3, -1)
    else:
        if mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "A" in mode else "RGB")
        a = np.asarray(im).astype(np.float32)
        a = a / (65535 if a.max() > 255 else 255)
    if a.shape[-1] == 4:
        a = a[..., :3] * a[..., 3:4]
    return to_linear(a[..., :3])


def filmic(x, shoulder=0.85, toe=0.012):
    """A gentle S: a lifted toe, a soft shoulder (the prototype's)."""
    x = np.clip(x, 0, None)
    y = x / (x + shoulder * 0.35)
    y = y * (1 + shoulder * 0.35)
    return y * (1 - toe) + toe


def edge_mask(h, w):
    """1 inside, falling to exactly 0 over the outermost EDGE_FADE .. EDGE_BLACK of the frame on every side."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.minimum(np.minimum(xx / w, 1 - (xx + 1) / w), np.minimum(yy / h, 1 - (yy + 1) / h))   # distance to the nearest edge, 0..0.5
    t = np.clip((d - EDGE_BLACK) / (EDGE_FADE - EDGE_BLACK), 0, 1)
    return t * t * (3 - 2 * t)


def grade(img, look="warm", light=(0.25, 0.15), vignette=0.55, grain=0.028, halation=0.10, exposure=1.0, seed=7, soften=0.55):
    h, w = img.shape[:2]
    x = img * exposure
    black = (x.max(-1) <= 1e-6)                           # what the render left black stays black
    lum = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    if look == "warm":
        mult = np.array([1.10, 0.95, 0.76], np.float32)
        shadow_tint = np.array([0.0, 0.002, 0.006], np.float32)
        high_tint = np.array([1.0, 0.98, 0.94], np.float32)
    elif look == "cool":
        mult = np.array([0.84, 0.97, 1.04], np.float32)
        shadow_tint = np.array([0.0, 0.004, 0.004], np.float32)
        high_tint = np.array([0.96, 1.0, 1.0], np.float32)
    else:
        mult = np.ones(3, np.float32)
        shadow_tint = np.zeros(3, np.float32)
        high_tint = np.ones(3, np.float32)
    x = x * mult
    hw = np.clip(lum[..., None] * 2.2, 0, 1)
    x = x * (1 - hw) + x * high_tint * hw
    lx, ly = light
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = xx / w - lx
    dy = yy / h - ly
    fall = 1.18 - 0.75 * np.clip(np.sqrt(dx * dx + dy * dy * 0.7), 0, 1.4)
    x = x * np.clip(fall, 0.45, 1.3)[..., None]
    cx = xx / w - 0.5
    cy = yy / h - 0.5
    r = np.sqrt(cx * cx + cy * cy * 1.15) / 0.7
    vig = 1 - vignette * np.clip(r, 0, 1) ** 2.2
    x = x * vig[..., None]
    bright = np.clip(x - 0.35, 0, None)
    glow = gaussian_filter(bright, sigma=(w * 0.012, w * 0.012, 0))
    x = x + glow * halation * np.array([1.0, 0.85, 0.7], np.float32)
    x = filmic(x)
    x = x + shadow_tint * (1 - np.clip(lum[..., None] * 6, 0, 1))
    edge = edge_mask(h, w)
    keep = edge * (~black)                                # exact black where the render was black, and at the edges
    x = x * keep[..., None]
    s = to_srgb(x)
    if soften > 0:
        s = gaussian_filter(s, sigma=(soften, soften, 0))
        s = s * keep[..., None]
    rng = np.random.default_rng(seed)
    g = rng.normal(0, 1, (h // 2 + 1, w // 2 + 1)).astype(np.float32)
    g = cv2.resize(g, (w, h), interpolation=cv2.INTER_LINEAR)
    l2 = s @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    amount = grain * (0.55 + 0.45 * (1 - l2)) * keep
    s = s + (g * amount)[..., None] * np.array([1.0, 0.95, 0.9], np.float32)
    return np.clip(s, 0, 1)


def seed_for(path):
    """The grain's seed from the output file's name, so every build of that file grains the same."""
    return int.from_bytes(hashlib.sha256(pathlib.Path(path).name.encode()).digest()[:4], "little")


def save(s, out, quality=82):
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    ext = out.suffix.lower()
    if ext == ".png":
        arr = (s * 65535 + 0.5).astype(np.uint16)
        cv2.imwrite(str(out), cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
        return
    im = Image.fromarray((s * 255 + 0.5).astype(np.uint8))
    if ext in (".jpg", ".jpeg"):
        im.save(out, quality=quality, subsampling=0, optimize=True)
    elif ext == ".webp":
        im.save(out, "WEBP", quality=quality, method=6)
    elif ext == ".avif":
        import pillow_avif  # noqa: F401  (the AVIF plugin registers itself)
        im.save(out, "AVIF", quality=quality, speed=4)
    else:
        raise SystemExit(f"grade_scene: unknown output type {ext}")


def process(src, out, look="warm", crop=None, width=None, height=None, quality=82, light=(0.25, 0.15), vignette=0.55,
            grain=0.028, halation=0.10, exposure=1.0, soften=0.55, seed=None):
    img = load(src)
    if crop:
        x0, y0, x1, y1 = crop
        img = img[y0:y1, x0:x1]
    if width or height:
        h, w = img.shape[:2]
        if width and not height:
            height = int(round(h * width / w))
        if height and not width:
            width = int(round(w * height / h))
        interp = cv2.INTER_AREA if img.shape[1] > width else cv2.INTER_CUBIC
        img = cv2.resize(img, (width, height), interpolation=interp)
    s = grade(img, look, light, vignette, grain, halation, exposure, seed_for(out) if seed is None else seed, soften)
    save(s, out, quality)
    return s.shape


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--look", default="warm", choices=["warm", "cool", "neutral"])
    ap.add_argument("--crop", type=int, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--width", type=int)
    ap.add_argument("--height", type=int)
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--light", type=float, nargs=2, default=[0.25, 0.15])
    ap.add_argument("--vignette", type=float, default=0.55)
    ap.add_argument("--grain", type=float, default=0.028)
    ap.add_argument("--halation", type=float, default=0.10)
    ap.add_argument("--exposure", type=float, default=1.0)
    ap.add_argument("--soften", type=float, default=0.55)
    ap.add_argument("--seed", type=int, default=None, help="the grain's seed; by default from the output file's name")
    a = ap.parse_args(argv)
    shape = process(a.src, a.out, a.look, a.crop, a.width, a.height, a.quality, tuple(a.light), a.vignette, a.grain,
                    a.halation, a.exposure, a.soften, a.seed)
    print(a.out, shape[1], "x", shape[0], file=sys.stderr)


if __name__ == "__main__":
    main()
