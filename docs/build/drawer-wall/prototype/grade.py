"""PROTOTYPE (Nov 4 2026): the cinematic grade the look mockups used (warm interior, cool exterior; grain,
halation, vignette, lens softness). The basis of tools/photo/grade_scene.py (DRAWER-WALL.md, phase D3).

    python3 grade.py src.png out.jpg --crop x0 y0 x1 y1 --size 1080 1620 --look warm
"""
import argparse
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter


def to_linear(s):
    return np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)


def to_srgb(l):
    l = np.clip(l, 0, 1)
    return np.where(l <= 0.0031308, l * 12.92, 1.055 * l ** (1 / 2.4) - 0.055)


def load(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if a.dtype == np.uint16:
        f = a.astype(np.float32) / 65535
    else:
        f = a.astype(np.float32) / 255
    if f.shape[2] == 4:
        al = f[..., 3:4]
        f = f[..., :3] * al  # over black
    f = f[..., ::-1]  # BGR -> RGB
    return to_linear(f)


def filmic(x, shoulder=0.85, toe=0.012):
    # a gentle S: lifted toe, soft shoulder, in the linear domain via a log-ish curve
    x = np.clip(x, 0, None)
    y = x / (x + shoulder * 0.35)  # reinhard-like shoulder
    y = y * (1 + shoulder * 0.35)
    return y * (1 - toe) + toe


def grade(img, look="warm", light=(0.25, 0.15), vignette=0.55, grain=0.028, halation=0.10, exposure=1.0):
    h, w = img.shape[:2]
    x = img * exposure
    lum = x @ np.array([0.2126, 0.7152, 0.0722])
    if look == "warm":
        mult = np.array([1.10, 0.95, 0.76])
        shadow_tint = np.array([0.0, 0.002, 0.006])   # a little blue in the blacks
        high_tint = np.array([1.0, 0.98, 0.94])
    elif look == "cool":
        mult = np.array([0.84, 0.97, 1.04])
        shadow_tint = np.array([0.0, 0.004, 0.004])    # grey-green in the blacks
        high_tint = np.array([0.96, 1.0, 1.0])
    else:
        mult = np.array([1, 1, 1]); shadow_tint = np.zeros(3); high_tint = np.ones(3)
    x = x * mult
    # highlights take the second tint
    hw = np.clip(lum[..., None] * 2.2, 0, 1)
    x = x * (1 - hw) + x * high_tint * hw
    # directional light: brighter toward the light's corner (lx, ly in 0..1 units of the frame)
    lx, ly = light
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = (xx / w - lx); dy = (yy / h - ly)
    fall = 1.18 - 0.75 * np.clip(np.sqrt(dx * dx + dy * dy * 0.7), 0, 1.4)
    x = x * np.clip(fall, 0.45, 1.3)[..., None]
    # vignette
    cx = xx / w - 0.5; cy = yy / h - 0.5
    r = np.sqrt(cx * cx + cy * cy * 1.15) / 0.7
    vig = 1 - vignette * np.clip(r, 0, 1) ** 2.2
    x = x * vig[..., None]
    # halation: bright parts bleed warm
    bright = np.clip(x - 0.35, 0, None)
    glow = gaussian_filter(bright, sigma=(w * 0.012, w * 0.012, 0))
    x = x + glow * halation * np.array([1.0, 0.85, 0.7])
    # tone
    x = filmic(x)
    x = x + shadow_tint * (1 - np.clip(lum[..., None] * 6, 0, 1))
    s = to_srgb(x)
    # lens softness
    s = gaussian_filter(s, sigma=(0.55, 0.55, 0))
    # grain: coarser than a pixel, luminance-weighted, more in the shadows
    rng = np.random.default_rng(7)
    g = rng.normal(0, 1, (h // 2 + 1, w // 2 + 1)).astype(np.float32)
    g = cv2.resize(g, (w, h), interpolation=cv2.INTER_LINEAR)
    l2 = s @ np.array([0.2126, 0.7152, 0.0722])
    amount = grain * (0.55 + 0.45 * (1 - l2))
    s = s + (g * amount)[..., None] * np.array([1.0, 0.95, 0.9])
    return np.clip(s, 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--crop", type=int, nargs=4)
    ap.add_argument("--size", type=int, nargs=2, default=[1080, 1620])
    ap.add_argument("--look", default="warm")
    ap.add_argument("--light", type=float, nargs=2, default=[0.25, 0.15])
    ap.add_argument("--vignette", type=float, default=0.55)
    ap.add_argument("--grain", type=float, default=0.028)
    ap.add_argument("--halation", type=float, default=0.10)
    ap.add_argument("--exposure", type=float, default=1.0)
    a = ap.parse_args()
    img = load(a.src)
    if a.crop:
        x0, y0, x1, y1 = a.crop
        img = img[y0:y1, x0:x1]
    img = cv2.resize(img, tuple(a.size), interpolation=cv2.INTER_AREA if img.shape[1] > a.size[0] else cv2.INTER_CUBIC)
    out = grade(img, a.look, tuple(a.light), a.vignette, a.grain, a.halation, a.exposure)
    cv2.imwrite(a.out, cv2.cvtColor((out * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(a.out, out.shape)


main()
