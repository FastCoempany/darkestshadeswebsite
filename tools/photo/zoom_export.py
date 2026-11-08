#!/usr/bin/env python3
"""The photographs for the wall's zoom (DRAWER-WALL.md, The photographs, D4): each frame's A1, A2, A3 and A6 stage
masters from the DAM, the long side 4096 px at most, WebP quality 85, into wall/public/zoom/, with each one's alt
text from assets/photography/MANIFEST.csv in wall/public/zoom/index.json. Run by `npm run assets`; never committed
(wall/public/zoom/ is git-ignored). The photographs are never altered beyond the resize.

    python3 tools/photo/zoom_export.py [--frames F09 F01] [--max 4096] [--quality 85]
"""
import argparse
import csv
import json
import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
DAM = ROOT / "dam" / "product"
OUT = ROOT / "wall" / "public" / "zoom"
MANIFEST = ROOT / "assets" / "photography" / "MANIFEST.csv"
FRAMES = ["F01", "F02", "F03", "F04", "F05", "F06", "F08", "F09"]
ANGLES = ["A1", "A2", "A3", "A6"]
Image.MAX_IMAGE_PIXELS = None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--frames", nargs="*", default=FRAMES)
    ap.add_argument("--max", type=int, default=4096)
    ap.add_argument("--quality", type=int, default=85)
    a = ap.parse_args()
    alts = {}
    with open(MANIFEST, newline="") as f:
        for row in csv.DictReader(f):
            alts[(row["frame"], row["angle"])] = row
    OUT.mkdir(parents=True, exist_ok=True)
    index = {"note": "The real lightbox photographs on their stage colour, resized and nothing else (00-decisions.md #8, #29); alt text from assets/photography/MANIFEST.csv.", "frames": {}}
    for frame in a.frames:
        entries = []
        for angle in ANGLES:
            row = alts.get((frame, angle))
            src = DAM / f"DS-{frame}-{angle}-v01-stage.png"
            if not row or not src.exists():
                print(f"zoom: {frame} {angle}: no final ({'no manifest row' if not row else 'no master'}); left out", file=sys.stderr)
                continue
            im = Image.open(src)
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGB")
            if im.mode == "RGBA":
                im = im.convert("RGB")
            w, h = im.size
            k = min(1.0, a.max / max(w, h))
            if k < 1.0:
                im = im.resize((int(round(w * k)), int(round(h * k))), Image.LANCZOS)
            name = f"{frame.lower()}-{angle.lower()}.webp"
            im.save(OUT / name, "WEBP", quality=a.quality, method=6)
            size = (OUT / name).stat().st_size
            entries.append({"angle": angle, "file": name, "width": im.size[0], "height": im.size[1], "bytes": size, "alt": row["alt"], "source": row["source"], "master": row["master"]})
            print(f"zoom: {name} {im.size[0]}x{im.size[1]} {size // 1024} KB", file=sys.stderr)
        index["frames"][frame] = entries
    (OUT / "index.json").write_text(json.dumps(index, indent=1))
    print(f"zoom: {sum(len(v) for v in index['frames'].values())} photographs in {OUT.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
