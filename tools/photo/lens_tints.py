#!/usr/bin/env python3
"""Measured lens transmission per frame (DRAWER-WALL.md, The frames in 3D, D4): the median transmission of each lens,
per channel, from the A1 stage master, against the stage colour, in linear light; the sample boxes come from
content/photography/lens-samples.json (chosen by eye and committed). Written with its sources to
wall/assets/lens-tints.json. F04 takes #38's values (00-decisions.md): the front view's measured 0.038, 0.038,
0.049, recorded there as the decision says, with this tool's own measurement beside it for the record.

    python3 tools/photo/lens_tints.py [--frames F09 F01]
"""
import argparse
import json
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "content" / "photography" / "lens-samples.json"
OUT = ROOT / "wall" / "assets" / "lens-tints.json"
DAM = ROOT / "dam" / "product"
Image.MAX_IMAGE_PIXELS = None
DECISION_38 = {"F04": {"transmission": [0.038, 0.038, 0.049], "source": "00-decisions.md #38: F04's intended lens colour, the front view's measured tint"}}


def to_linear(s):
    return np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)


def load_linear(path):
    im = Image.open(path)
    a = np.asarray(im)
    if a.dtype == np.uint16:
        f = a.astype(np.float32) / 65535
    else:
        f = a.astype(np.float32) / 255
    return to_linear(f[..., :3])


def box_median(img, box):
    x0, y0, x1, y1 = box
    return np.median(img[y0:y1, x0:x1].reshape(-1, 3), axis=0)


def measure(frame, spec, img):
    stage = box_median(img, spec["stage"])
    lenses = [box_median(img, b) / stage for b in spec["lenses"]]
    t = np.median(np.stack(lenses), axis=0)
    out = {"transmission": [round(float(v), 4) for v in t], "perLens": [[round(float(v), 4) for v in l] for l in lenses],
           "stageLinear": [round(float(v), 4) for v in stage], "boxes": spec["lenses"], "stageBox": spec["stage"]}
    if "gradient" in spec:
        grad = {}
        for name, boxes in spec["gradient"].items():
            vals = [box_median(img, b) / stage for b in boxes]
            grad[name] = {"transmission": [round(float(v), 4) for v in np.median(np.stack(vals), axis=0)], "boxes": boxes}
        out["gradient"] = grad
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--frames", nargs="*", default=None)
    ap.add_argument("--out", default=None, help="where to write (wall/assets/lens-tints.json by default)")
    a = ap.parse_args()
    global OUT
    if a.out:
        OUT = pathlib.Path(a.out)
    samples = json.loads(SAMPLES.read_text())["frames"]
    frames = a.frames or list(samples)
    existing = json.loads(OUT.read_text()) if OUT.exists() else {"frames": {}}
    commit = subprocess.check_output(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--", "tools/photo", "content/photography/lens-samples.json"], cwd=ROOT, text=True).strip():
        commit += "-dirty"
    result = {"$comment": "Each frame's lens transmission (linear, r g b, 0 = opaque, 1 = clear), measured by tools/photo/lens_tints.py on the A1 stage master against the stage colour, in the boxes of content/photography/lens-samples.json. The wall's renders and the live frames take these tints; F04 takes #38's values.",
              "tool": "tools/photo/lens_tints.py", "samples": "content/photography/lens-samples.json", "sourceCommit": commit, "frames": existing.get("frames", {})}
    for frame in frames:
        spec = samples[frame]
        master = f"DS-{frame}-A1-v01-stage.png"
        img = load_linear(DAM / master)
        m = measure(frame, spec, img)
        entry = {"source": f"dam/product/{master}", "measured": m}
        if frame in DECISION_38:
            entry["transmission"] = DECISION_38[frame]["transmission"]
            entry["decision"] = DECISION_38[frame]["source"]
        else:
            entry["transmission"] = m["transmission"]
        if "gradient" in m:
            entry["gradient"] = {k: v["transmission"] for k, v in m["gradient"].items()}
        result["frames"][frame] = entry
        print(f"{frame}: transmission {entry['transmission']}" + (f" (measured {m['transmission']})" if frame in DECISION_38 else "") + (f" gradient top {m['gradient']['top']['transmission']} bottom {m['gradient']['bottom']['transmission']}" if "gradient" in m else ""), file=sys.stderr)
    result["frames"] = dict(sorted(result["frames"].items()))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(f"wrote {OUT}", file=sys.stderr)
    if OUT.resolve() == (ROOT / "wall" / "assets" / "lens-tints.json").resolve():
        write_manifest_entry(result, commit)


def write_manifest_entry(result, commit):
    """The tints' entry in wall/assets/manifest.json (kind `tints`): measured data, so `final` for the frames measured
    from their own photographs and `mockup` while F04 carries #38's values."""
    sys.path.insert(0, str(ROOT / "tools" / "blender"))
    import render_queue
    manifest = ROOT / "wall" / "assets" / "manifest.json"
    m = json.loads(manifest.read_text()) if manifest.exists() else {"$schema": "./manifest.schema.json", "renderSet": "wall-v1", "assets": []}
    decided = sorted(f for f, e in result["frames"].items() if "decision" in e)
    entry = {"id": "lens-tints", "kind": "tints", "files": ["lens-tints.json"], "status": "mockup" if decided else "final",
             "tool": "tools/photo/lens_tints.py", "command": "lens_tints.py (content/photography/lens-samples.json against dam/product/DS-<frame>-A1-v01-stage.png)",
             "sourceCommit": commit, "toolsHash": render_queue.tools_hash(),
             "checks": {"frames": ",".join(sorted(result["frames"])), "gradients": ",".join(f for f, e in sorted(result["frames"].items()) if "gradient" in e) or "none",
                        "takenFromAnotherFrame": ",".join(f"{f} from {result['frames'][f]['decision']}" for f in decided) or "none"}}
    m["assets"] = [e for e in m["assets"] if e["id"] != entry["id"]] + [entry]
    m["assets"].sort(key=lambda e: e["id"])
    manifest.write_text(json.dumps(m, indent=2) + "\n")
    print("manifest: lens-tints entry written", file=sys.stderr)


if __name__ == "__main__":
    main()
