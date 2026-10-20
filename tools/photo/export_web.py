#!/usr/bin/env python3
"""Export the cleaned lightbox finals for the web (docs/brief/07-photography.md, step 11).

    python3 tools/photo/export_web.py              # every final -> assets/photography/ + MANIFEST.csv
    python3 tools/photo/export_web.py F02 F05      # some frames only (the manifest is rewritten whole)
    python3 tools/photo/export_web.py --masters DIR   # also copy the masters, named for the DAM, to DIR

Reads work/out/<shot>/stage-full.png (16-bit, from tools/photo/clean_lightbox.py) for each shot in
content/photography/shots/: one final per frame and angle, the hero (H) included. Writes
ds-<frame>-<angle>-<width>.avif / .webp / .jpg at the widths below that the master reaches (never
upscaled; a close-up cropped smaller than 2048 also gets its own full width), downsized in linear
light, and assets/photography/MANIFEST.csv, one row per final, with the alt text built from
content/copy/en.json (alt.stage, alt.angles) and the product's descriptor.

The masters (the 16-bit cut-out, cutout.png, and the 16-bit stage version) stay out of this public
repo; they belong in the DAM (07-photography.md, "Where files live").
"""
import csv
import json
import pathlib
import shutil
import sys

import cv2
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from clean_lightbox import lin_to_srgb, srgb_to_lin  # noqa: E402

OUT = ROOT / "assets" / "photography"
WIDTHS = [640, 960, 1440, 2048]
VERSION = "v01"
QUALITY = {"jpg": 84, "webp": 82, "avif": 62}
ANGLES = ["A1", "A2", "A3", "A4", "A5", "A6", "H"]


def finals():
    """One final per frame and angle, from the shot settings."""
    rows = []
    for p in sorted((ROOT / "content" / "photography" / "shots").glob("IMG_*.json")):
        c = json.loads(p.read_text())
        key = c["shot"] + (f"-{c['variant']}" if c.get("variant") else "")
        rows.append({"key": key, "shot": c["shot"], "frame": c["frame"], "angle": c["angle"],
                     "alt": c.get("alt", c["angle"]), "gcd": bool(c.get("gcd")), "marks": bool(c.get("marks"))})
    seen = {}
    for r in rows:
        k = (r["frame"], r["angle"])
        if k in seen:
            sys.exit(f"two finals for {k}: {seen[k]} and {r['key']}")
        seen[k] = r["key"]
    return sorted(rows, key=lambda r: (r["frame"], ANGLES.index(r["angle"])))


def alt_text(copy, product, alt_key):
    angles = copy["alt"]["angles"]
    if alt_key not in angles:
        sys.exit(f"no alt text for {alt_key!r} in content/copy/en.json (alt.angles)")
    return copy["alt"]["stage"].format(descriptor=product["descriptor"], angle=angles[alt_key])


def downsize(lin, width):
    """Area-average in linear light (a thin dark wire keeps its true weight), back to 8-bit sRGB
    with a light dither so the shadow's long gradients don't band."""
    h = int(round(lin.shape[0] * width / lin.shape[1]))
    small = cv2.resize(lin, (width, h), interpolation=cv2.INTER_AREA) if width < lin.shape[1] else lin
    srgb = lin_to_srgb(small) * 255
    rng = np.random.default_rng(width)
    srgb = srgb + rng.uniform(-0.5, 0.5, srgb.shape[:2])[..., None]
    return Image.fromarray(np.clip(srgb + 0.5, 0, 255).astype(np.uint8), "RGB")


def save(im, path, fmt):
    if fmt == "jpg":
        im.save(path, "JPEG", quality=QUALITY["jpg"], optimize=True, progressive=True, subsampling="4:4:4")
    elif fmt == "webp":
        im.save(path, "WEBP", quality=QUALITY["webp"], method=6)
    else:
        im.save(path, "AVIF", quality=QUALITY["avif"], speed=4, subsampling="4:4:4")


def main(argv):
    masters = None
    if "--masters" in argv:
        i = argv.index("--masters")
        masters = pathlib.Path(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    only = {a.upper() for a in argv}
    copy = json.loads((ROOT / "content" / "copy" / "en.json").read_text())
    products = {}
    for p in (ROOT / "content" / "products").glob("f*.json"):
        d = json.loads(p.read_text())
        products[d["id"]] = d
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = OUT / "MANIFEST.csv"
    old = {}
    if manifest.exists():
        with manifest.open() as f:
            old = {r["id"]: r for r in csv.DictReader(f)}
    rows = []
    for r in finals():
        fid = f"ds-{r['frame'].lower()}-{r['angle'].lower()}"
        src = ROOT / "work" / "out" / r["key"]
        if only and r["frame"] not in only:
            if fid in old:
                rows.append(old[fid])
            continue
        rep = json.loads((src / "report.json").read_text())
        st = cv2.imread(str(src / "stage-full.png"), cv2.IMREAD_UNCHANGED)
        if st is None or st.dtype != np.uint16:
            sys.exit(f"{src}/stage-full.png: missing or not 16-bit; run tools/photo/clean_lightbox.py first")
        H, W = st.shape[:2]
        lin = srgb_to_lin(cv2.cvtColor(st, cv2.COLOR_BGR2RGB).astype(np.float32) / 65535).astype(np.float32)
        del st
        widths = [w for w in WIDTHS if w <= W]
        if W < WIDTHS[-1] and W > 1.15 * widths[-1]:
            widths.append(W)                         # a close-up cropped small: its own full width on top
        for old_file in OUT.glob(f"{fid}-*.*"):
            old_file.unlink()
        for w in widths:
            im = downsize(lin, w)
            for fmt in ("avif", "webp", "jpg"):
                save(im, OUT / f"{fid}-{w}.{fmt}", fmt)
        del lin
        master = f"DS-{r['frame']}-{r['angle']}-{VERSION}-master.png"
        if masters:
            masters.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src / "cutout.png", masters / master)
            shutil.copyfile(src / "stage-full.png", masters / master.replace("-master", "-stage"))
        tools = ["tools/photo/clean_lightbox.py"]
        if r["gcd"]:
            tools += ["tools/blender/gcd_render.py", "tools/photo/temple_gcd.py"]
        rows.append({
            "id": fid, "source": r["key"], "frame": r["frame"], "angle": r["angle"], "version": VERSION,
            "width": W, "height": H, "widths": " ".join(map(str, widths)), "formats": "avif webp jpg",
            "tool_chain": "; ".join(tools), "master": master,
            "master_location": "DAM masters/ (to upload; regenerate with tools/photo/clean_lightbox.py)",
            "status": "final", "alt": alt_text(copy, products[r["frame"]], r["alt"]),
            "crop": " ".join(map(str, rep["crop"])),
        })
        print(fid, r["key"], f"{W}x{H}", widths)
    cols = ["id", "source", "frame", "angle", "version", "width", "height", "widths", "formats", "tool_chain",
            "master", "master_location", "status", "alt", "crop"]
    rows.sort(key=lambda r: (r["frame"], ANGLES.index(r["angle"])))
    with manifest.open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        wr.writeheader()
        for row in rows:
            wr.writerow({c: row.get(c, "") for c in cols})
    print(manifest, len(rows), "finals")


if __name__ == "__main__":
    main(sys.argv[1:])
