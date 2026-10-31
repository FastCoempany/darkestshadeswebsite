#!/usr/bin/env python3
"""The entry's stills (docs/brief/03-references.md, "The entry sequence", "Assets", "Safety").

Makes black-and-white stills from the finished photography (assets/photography/, registered in
MANIFEST.csv) into assets/entry/, and writes assets/entry/sequence.json, the one file the player
(app/components/house/Entry.tsx) and tools/flashcheck.py both read.

- Every still is black and white, graded in this tool, never in CSS.
- Burst 1 (12 a second, small 3:4 prints): every pixel's relative luminance stays at or under 0.09
  (sRGB grey 84), so no change between frames can reach the 10% that counts as a flash.
- Burst 2 (3 a second, full bleed): at most one bright frame a second; the frames between are graded
  dark like burst 1. Cast stills join from the manifest's finals.
- AVIF and WebP at two sizes; the phone set stays under 1.5 MB in all.

Usage: python3 tools/photo/entry_stills.py [--out assets/entry] [--check]
"""
import argparse
import csv
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parents[2]
PHOTO = ROOT / "assets" / "photography"
COPY = ROOT / "content" / "copy" / "en.json"

DARK_MAX = 0.060          # target for the brightest pixel in a dark frame: headroom under the 0.09 rule for the encoders’ ringing
DARK_SRGB_MAX = 84        # sRGB grey at relative luminance 0.09
SIZES = {"framed": [(480, 640), (720, 960)], "bleed": [(720, 900), (1440, 1800)]}
RATIO = {"framed": (3, 4), "bleed": (4, 5)}
QUALITY = {"avif": 48, "webp": 68}
DARK_QUALITY = {"avif": 90, "webp": 92}   # dark stills: near-lossless first; WebP falls back to lossless

# Burst 1: the eight frames at three-quarter (the GCD side) plus F09's hero; the home image recurs
# (A-B-A-C), two pairs swap back and forth (03, reference 1). 28 cuts from nine stills.
BURST1_STILLS = ["ds-f09-a2", "ds-f01-a2", "ds-f02-a2", "ds-f03-a2", "ds-f04-a2", "ds-f05-a2", "ds-f06-a2", "ds-f08-a2", "ds-f09-h"]
BURST1_ORDER = ["ds-f09-a2", "ds-f01-a2", "ds-f09-a2", "ds-f02-a2", "ds-f09-a2", "ds-f03-a2", "ds-f09-a2", "ds-f04-a2",
                "ds-f05-a2", "ds-f06-a2", "ds-f05-a2", "ds-f06-a2", "ds-f05-a2", "ds-f06-a2",
                "ds-f09-a2", "ds-f08-a2", "ds-f09-a2", "ds-f09-h", "ds-f09-a2", "ds-f01-a2",
                "ds-f02-a2", "ds-f03-a2", "ds-f02-a2", "ds-f03-a2",
                "ds-f09-a2", "ds-f04-a2", "ds-f09-a2", "ds-f09-a2"]
# Burst 2: cast and product, full bleed, 3 a second: one bright frame (a person) then two dark frames.
BURST2_ORDER = [("ds-cast-w1-s07-f02", True), ("ds-f02-a1", False), ("ds-f02-a6", False),
                ("ds-cast-m1-s06-f04", True), ("ds-f04-a1", False), ("ds-f04-a6", False),
                ("ds-cast-w2-s06-f09-a2", True), ("ds-f09-a6", False)]


def srgb_to_linear(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(y):
    return np.where(y <= 0.0031308, y * 12.92, 1.055 * np.power(np.clip(y, 0, 1), 1 / 2.4) - 0.055)


def luminance(img):
    a = np.asarray(img.convert("RGB"), dtype=np.float64) / 255.0
    lin = srgb_to_linear(a)
    return 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]


def manifest():
    rows = {}
    with open(PHOTO / "MANIFEST.csv", newline="") as f:
        for r in csv.DictReader(f):
            rows[r["id"]] = r
    return rows


def source_file(row):
    widths = sorted(int(w) for w in row["widths"].split())
    pick = next((w for w in widths if w >= 1440), widths[-1])
    return PHOTO / f"{row['id']}-{pick}.jpg"


def cast_code(mid):
    """ds-cast-w1-s07-f02 -> W1-S07-F02-A1; ds-cast-w2-s06-f09-a2 -> W2-S06-F09-A2."""
    parts = mid.replace("ds-cast-", "").upper().split("-")
    if len(parts) == 3:
        parts.append("A1")
    return "-".join(parts)


def cover(img, size):
    w, h = size
    sw, sh = img.size
    scale = max(w / sw, h / sh)
    out = img.resize((max(1, round(sw * scale)), max(1, round(sh * scale))), Image.LANCZOS)
    left, top = (out.width - w) // 2, (out.height - h) // 2
    return out.crop((left, top, left + w, top + h))


def grade(img, bright):
    """Black and white, film-like: lifted blacks, soft shoulder. Dark frames are scaled under the ceiling."""
    y = luminance(img)
    if bright:
        # Lift the blacks a little and roll off the highlights: a print, not screen white.
        y = 0.012 + y * 0.9
        y = np.where(y > 0.6, 0.6 + (y - 0.6) * 0.55, y)
        y = np.clip(y, 0, 0.85)
    else:
        # Keep the picture's own tonal order, scaled so the brightest pixel sits under the ceiling.
        top = max(float(np.percentile(y, 99.9)), 1e-6)
        y = np.clip(y / top, 0, 1) * DARK_MAX
    s = np.clip(linear_to_srgb(y) * 255.0, 0, 255).astype(np.uint8)
    out = Image.fromarray(s, mode="L").convert("RGB")
    if bright:
        out = out.filter(ImageFilter.GaussianBlur(0.3))
    return out


def verify_dark(img):
    arr = np.asarray(img.convert("L"))
    return int(arr.max()), float(luminance(img).max())


def encode(img, path, fmt, dark=False):
    """Write the file; for a dark still, re-read it and prove every pixel stays under the ceiling."""
    quality = DARK_QUALITY[fmt] if dark else QUALITY[fmt]
    attempts = [quality, 95, 100] if dark else [quality]
    for i, q in enumerate(attempts):
        kwargs = {"quality": q}
        if fmt == "avif":
            kwargs["speed"] = 4
        if fmt == "webp" and dark and i == len(attempts) - 1:
            kwargs = {"lossless": True}
        img.save(path, format=fmt.upper(), **kwargs)
        if not dark:
            break
        mx, ml = verify_dark(Image.open(path))
        if mx <= DARK_SRGB_MAX and ml <= 0.09:
            break
    return path.stat().st_size


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "assets" / "entry")
    ap.add_argument("--check", action="store_true", help="(kept for the docs) the ceiling and the budget are always verified; a failure exits 1 and writes no sequence")
    args = ap.parse_args(argv)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    rows = manifest()
    copy = json.loads(COPY.read_text())
    stills = {}
    phone_bytes = 0
    failures = []

    def make(mid, layout, bright):
        key = f"{'b1' if layout == 'framed' else 'b2'}-{mid.replace('ds-', '')}"
        if key in stills:
            return key
        row = rows.get(mid)
        if not row or row.get("status") != "final":
            raise SystemExit(f"{mid}: not a final in MANIFEST.csv")
        src = Image.open(source_file(row)).convert("RGB")
        entry = {"ratio": "3:4" if layout == "framed" else "4:5", "bright": bright, "shot": f"{row['frame']}-{row['angle']}" if not mid.startswith("ds-cast") else cast_code(mid), "sources": {"avif": [], "webp": []}, "sizes": []}
        for i, size in enumerate(SIZES[layout]):
            frame = grade(cover(src, size), bright)
            for fmt in ("avif", "webp"):
                path = out / f"{key}-{size[0]}.{fmt}"
                n = encode(frame, path, fmt, dark=not bright)
                if not bright:
                    # The rule holds for the file the browser decodes, not the frame in memory.
                    mx, ml = verify_dark(Image.open(path))
                    if mx > DARK_SRGB_MAX or ml > 0.09:
                        failures.append(f"{path.name}: max sRGB {mx}, luminance {ml:.3f} after encoding")
                entry["sources"][fmt].append(str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path))
                if i == 0 and fmt == "avif":
                    nonlocal_bytes[0] += n
            entry["sizes"].append({"width": size[0], "height": size[1]})
        stills[key] = entry
        return key

    nonlocal_bytes = [0]
    burst1 = [make(m, "framed", False) for m in BURST1_ORDER]
    burst2 = [make(m, "bleed", b) for m, b in BURST2_ORDER]
    phone_bytes = nonlocal_bytes[0]

    sequence = {
        "version": 1,
        "$comment": "Made by tools/photo/entry_stills.py from the finals in assets/photography. The player and tools/flashcheck.py read this file.",
        "stills": stills,
        "steps": [
            {"type": "card", "card": 0, "text": copy["entry"]["cards"][0], "seconds": 1.2, "ground": "surface-overlay"},
            {"type": "burst", "layout": "framed", "fps": 12, "ground": "surface-canvas", "frames": burst1},
            {"type": "card", "card": 1, "text": copy["entry"]["cards"][1], "seconds": 2.0, "ground": "surface-overlay"},
            {"type": "logo", "seconds": 2.4, "ground": "surface-overlay"},
            {"type": "burst", "layout": "bleed", "fps": 3, "ground": "black", "frames": burst2},
            {"type": "end", "seconds": 1.6, "ground": "black"},
        ],
    }
    seconds = 1.2 + len(burst1) / 12 + 2.0 + 2.4 + len(burst2) / 3 + 1.6
    if phone_bytes > 1.5 * 1024 * 1024:
        failures.append(f"phone set {phone_bytes} bytes over 1.5 MB")
    if failures:
        print("[entry_stills] FAIL: no sequence written\n  " + "\n  ".join(failures))
        return 1
    (out / "sequence.json").write_text(json.dumps(sequence, indent=1))
    print(f"[entry_stills] {len(stills)} stills, {len(burst1)} + {len(burst2)} cuts, {seconds:.1f}s; phone set (smallest AVIF of each) {phone_bytes / 1024:.0f} KB; wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}/sequence.json")
    print("[entry_stills] every dark file decodes under the ceiling (sRGB 84, relative luminance 0.09); the phone set within budget")
    return 0


if __name__ == "__main__":
    sys.exit(main())
