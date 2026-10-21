#!/usr/bin/env python3
"""Export the cleaned lightbox finals for the web (docs/brief/07-photography.md, step 11).

    python3 tools/photo/export_web.py              # every final -> assets/photography/ + MANIFEST.csv,
                                                   # and its masters -> dam/product/
    python3 tools/photo/export_web.py F02 F05      # some frames only (the manifest is rewritten whole)
    python3 tools/photo/export_web.py --no-masters    # web files and manifest only
    python3 tools/photo/export_web.py --manifest      # rewrite MANIFEST.csv only (after a copy change)

Reads work/out/<shot>/stage-full.png (16-bit, from tools/photo/clean_lightbox.py) for each shot in
content/photography/shots/: one final per frame and angle, the hero (H) included. Writes
ds-<frame>-<angle>-<width>.avif / .webp / .jpg at the widths below that the master reaches (never
upscaled; a close-up cropped smaller than 2048 also gets its own full width), downsized in linear
light, and assets/photography/MANIFEST.csv, one row per final, with the alt text built from
content/copy/en.json (alt.stage, alt.subjects, alt.angles).

The masters, the 16-bit cut-out (cutout.png) and the 16-bit stage version (stage-full.png, the source
of every web file), go to the DAM in this repo, dam/product/ (dam/README.md; founder, Oct 21 2026),
named DS-<frame>-<angle>-<version>-master.png and -stage.png, losslessly recompressed; a master newer
than its source is left as it is.

On-model finals (content/photography/people/<id>.json with "status": "final", composited by
tools/photo/wear.py into work/people/<id>/composite.png) go the same way: ds-cast-<cast>-<scene>-<frame>
web files, a manifest row (alt.onModel), and the master to dam/people/.
"""
import csv
import json
import pathlib
import sys

import cv2
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from clean_lightbox import lin_to_srgb, srgb_to_lin  # noqa: E402

OUT = ROOT / "assets" / "photography"
DAM = ROOT / "dam" / "product"
DAM_PEOPLE = ROOT / "dam" / "people"
PEOPLE = ROOT / "content" / "photography" / "people"
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


def alt_text(copy, frame, alt_key):
    angles, subjects = copy["alt"]["angles"], copy["alt"]["subjects"]
    if alt_key not in angles or frame not in subjects:
        sys.exit(f"no alt text for {frame} {alt_key!r} in content/copy/en.json (alt.subjects, alt.angles)")
    text = copy["alt"]["stage"].format(subject=subjects[frame], angle=angles[alt_key])
    return text[0].upper() + text[1:]


def people_finals():
    """The on-model finals: settings files marked final."""
    out = []
    for p in sorted(PEOPLE.glob("*.json")):
        c = json.loads(p.read_text())
        if c.get("status") == "final":
            out.append(c)
    return out


def on_model_alt(copy, c):
    a = copy["alt"]
    for group, key in (("people", c["cast"]), ("wardrobe", c["wardrobe"]), ("scenes", c["scene"]), ("subjects", c["frame"])):
        if key not in a[group]:
            sys.exit(f"no alt text for {c['id']}: alt.{group}.{key} in content/copy/en.json")
    return a["onModel"].format(person=a["people"][c["cast"]], wardrobe=a["wardrobe"][c["wardrobe"]],
                               subject=a["subjects"][c["frame"]], scene=a["scenes"][c["scene"]])


def widths_for(W):
    widths = [w for w in WIDTHS if w <= W]
    if W < WIDTHS[-1] and W > 1.15 * widths[-1]:
        widths.append(W)                             # cropped small: its own full width on top
    return widths


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
    masters = None if "--no-masters" in argv or "--manifest" in argv else DAM
    images = "--manifest" not in argv
    only = {a.upper() for a in argv if not a.startswith("--")}
    copy = json.loads((ROOT / "content" / "copy" / "en.json").read_text())
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
        with Image.open(src / "stage-full.png") as probe:
            W, H = probe.size
        widths = widths_for(W)
        if images:
            st = cv2.imread(str(src / "stage-full.png"), cv2.IMREAD_UNCHANGED)
            if st is None or st.dtype != np.uint16:
                sys.exit(f"{src}/stage-full.png: missing or not 16-bit; run tools/photo/clean_lightbox.py first")
            lin = srgb_to_lin(cv2.cvtColor(st, cv2.COLOR_BGR2RGB).astype(np.float32) / 65535).astype(np.float32)
            del st
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
            for name, dst in (("cutout.png", masters / master), ("stage-full.png", masters / master.replace("-master", "-stage"))):
                if dst.exists() and dst.stat().st_mtime >= (src / name).stat().st_mtime:
                    continue
                a = cv2.imread(str(src / name), cv2.IMREAD_UNCHANGED)
                cv2.imwrite(str(dst), a, [cv2.IMWRITE_PNG_COMPRESSION, 9])
                del a
        tools = ["tools/photo/clean_lightbox.py"]
        if r["gcd"]:
            tools += ["tools/blender/gcd_render.py", "tools/photo/temple_gcd.py"]
        rows.append({
            "id": fid, "source": r["key"], "frame": r["frame"], "angle": r["angle"], "version": VERSION,
            "width": W, "height": H, "widths": " ".join(map(str, widths)), "formats": "avif webp jpg",
            "tool_chain": "; ".join(tools), "master": master,
            "master_location": "dam/product/",
            "status": "final", "alt": alt_text(copy, r["frame"], r["alt"]),
            "crop": " ".join(map(str, rep["crop"])),
        })
        print(fid, r["key"], f"{W}x{H}", widths)
    for c in people_finals():
        fid = c["id"].rsplit("-v", 1)[0].lower()
        src = ROOT / "work" / "people" / c["id"] / "composite.png"
        if only and c["frame"] not in only:
            if fid in old:
                rows.append(old[fid])
            continue
        rep = json.loads((src.parent / "report.json").read_text())
        with Image.open(src) as probe:
            W, H = probe.size
        widths = widths_for(W)
        if images:
            st = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
            if st is None or st.dtype != np.uint16:
                sys.exit(f"{src}: missing or not 16-bit; run tools/photo/wear.py first")
            lin = srgb_to_lin(cv2.cvtColor(st, cv2.COLOR_BGR2RGB).astype(np.float32) / 65535).astype(np.float32)
            del st
            for old_file in OUT.glob(f"{fid}-*.*"):
                old_file.unlink()
            for w in widths:
                im = downsize(lin, w)
                for fmt in ("avif", "webp", "jpg"):
                    save(im, OUT / f"{fid}-{w}.{fmt}", fmt)
            del lin
        master = f"{c['id']}-master.png"
        if masters:
            DAM_PEOPLE.mkdir(parents=True, exist_ok=True)
            dst = DAM_PEOPLE / master
            if not (dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime):
                cv2.imwrite(str(dst), cv2.imread(str(src), cv2.IMREAD_UNCHANGED), [cv2.IMWRITE_PNG_COMPRESSION, 9])
        ps = c["portrait_source"]
        rows.append({
            "id": fid, "source": f"figma {ps['figma_file']} node {ps['node']} + {c['product_shot']}",
            "frame": c["frame"], "angle": c.get("angle", "A1"), "version": c["id"].rsplit("-", 1)[1],
            "width": W, "height": H, "widths": " ".join(map(str, widths)), "formats": "avif webp jpg",
            "tool_chain": f"Figma generate_image ({ps['model']}); {rep.get('upscale', 'none')} (upscaled); tools/photo/wear.py",
            "master": master, "master_location": "dam/people/", "status": "final",
            "alt": on_model_alt(copy, c), "crop": " ".join(map(str, rep.get("crop", []))),
        })
        print(fid, c["portrait"], f"{W}x{H}", widths)
    cols = ["id", "source", "frame", "angle", "version", "width", "height", "widths", "formats", "tool_chain",
            "master", "master_location", "status", "alt", "crop"]
    rows.sort(key=lambda r: (r["id"].startswith("ds-cast"), r["id"] if r["id"].startswith("ds-cast")
                             else (r["frame"], ANGLES.index(r["angle"]))))
    with manifest.open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        wr.writeheader()
        for row in rows:
            wr.writerow({c: row.get(c, "") for c in cols})
    print(manifest, len(rows), "finals")


if __name__ == "__main__":
    main(sys.argv[1:])
