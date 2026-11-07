#!/usr/bin/env python3
"""The wall's web outputs from the renders in work/wall/ (DRAWER-WALL.md, Assets): every image through the one grade
(tools/photo/grade_scene.py), encoded as AVIF and WebP at the budgets, the dark crops cut from the graded dark render
with the plate's own grain, rects.json copied, camera/open.json and inspect.json, the environment map, and every
output's manifest entry (tool, command, source commit, status, checks) written into wall/assets/manifest.json.

    python3 tools/blender/wall_export.py wall --layout portrait --knob black-relief [--status mockup]
    python3 tools/blender/wall_export.py sequence [--frame F09] --width 720 --width 1200
    python3 tools/blender/wall_export.py cameras
    python3 tools/blender/wall_export.py env
    python3 tools/blender/wall_export.py knobs            # the three O15 close-ups into docs/build/drawer-wall/review/R1/
    python3 tools/blender/wall_export.py prune            # drop manifest entries whose files are gone

Nothing here invents anything: the renders are what Blender made, the grade is one function, the budgets are the
doc's; an output over budget is re-encoded at a lower quality until it fits, and reported.
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "photo"))
import grade_scene  # noqa: E402
import render_queue  # noqa: E402

WORK = ROOT / "work" / "wall"
ASSETS = ROOT / "wall" / "assets"
MANIFEST = ASSETS / "manifest.json"
KB = 1024
BUDGET = {"wall-plate": lambda w: 380 * KB if w >= 2000 else 160 * KB, "wall-dark": lambda w: 60 * KB,
          "sequence-frame": lambda w: 80 * KB if w >= 1000 else 45 * KB, "still": lambda w: 200 * KB, "env": lambda w: 600 * KB}
# One grade for every image of the wall (DRAWER-WALL.md, The look: identical on every asset): the cool cast, the
# exposure that puts the leather where the founder-reviewed prototype still has it (about 36/255; measured Nov 7
# 2026), a low toe so the room falls to black. The drawer's warmth comes from the scene's own light, so the drawer
# view continues the wall at its first frame without a shift.
LOOK = {"wall": "cool", "sequence": "cool", "still": "cool", "knob": "cool"}
GRADE = {"exposure": 0.3, "toe": 0.004}
# The edge band, fractions of the width (grade_scene.edge_mask): the plates are black to 2% and at full level from
# 3.2%, inside the 3.27% room round the cabinet, so no drawer is touched; the drawer view's frames and the knob
# close-ups, full-screen pictures of a drawer in the dark, fade over 2% to 6%, the vignette the prototype had
EDGE = {"wall": (0.02, 0.032), "sequence": (0.02, 0.06), "still": (0.02, 0.032), "knob": (0.02, 0.06)}


def grade_for(part):
    return {**GRADE, "edge": EDGE[part]}
TOOLS_HASH = render_queue.tools_hash()     # a stamp of the tool files every entry was made with (see render_queue.TOOLS)


def grade_note(part="wall"):
    return f"grade {LOOK[part]} exposure {GRADE['exposure']} toe {GRADE['toe']}, edge black to {EDGE[part][0]} and full from {EDGE[part][1]} of the width"


def git_commit():
    """The code the file was made with: HEAD's short hash, and -dirty when the tools or the exporter had uncommitted
    changes at export time (the entry's toolsHash stamps the tool files themselves)."""
    try:
        head = subprocess.check_output(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain", "--", "tools/blender", "tools/photo"], cwd=ROOT, text=True).strip()
        return head + ("-dirty" if dirty else "")
    except Exception:
        return "0000000"


def queue_cmd(job_id, fallback):
    """The exact command the render queue ran for a job (work/queue/*.json, the flags included), or `fallback`."""
    qdir = ROOT / "work" / "queue"
    for q in sorted(qdir.glob("*.json")) if qdir.exists() else []:
        try:
            jobs = json.loads(q.read_text())
        except Exception:
            continue
        for j in jobs:
            if isinstance(j, dict) and j.get("id") == job_id and j.get("cmd"):
                return " ".join(j["cmd"]).replace("python3 tools/blender/", "")
    return fallback


def load_manifest():
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"$schema": "./manifest.schema.json", "renderSet": "wall-v1", "assets": []}


def save_manifest(m):
    m["assets"].sort(key=lambda e: e["id"])
    MANIFEST.write_text(json.dumps(m, indent=2) + "\n")


def put(m, entry):
    entry["toolsHash"] = TOOLS_HASH
    m["assets"] = [e for e in m["assets"] if e["id"] != entry["id"]] + [entry]


def edge_max(path, band=0.02):
    """The highest level in the outermost `band` of the width, on every side, of an encoded file (0 is scene black)."""
    import numpy as np
    from PIL import Image
    import pillow_avif  # noqa: F401
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    mm = max(1, int(round(band * a.shape[1])))
    return int(max(a[:mm].max(), a[-mm:].max(), a[:, :mm].max(), a[:, -mm:].max()))


def edge_ok(path, band=0.02, limit=1):
    """Scene black is exact (DRAWER-WALL.md, Assets): the outermost `band` of the width within `limit`/255 of black.
    The lossy encoders can leave a stray level at an edge; the export lowers the quality until none is left."""
    return edge_max(path, band) <= limit


def encode_within(src, out, look, width, budget, seed, crop=None, crop_after=None, quality=82, extra=None, check_edge=True):
    """Grade and encode `src` to `out`, lowering the quality until the file fits its budget and its edges are scene
    black. Returns (quality, bytes)."""
    extra = extra or {}
    q = quality
    graded = None
    while True:
        if crop_after:
            # grade the whole image at the plate's size and seed, then cut the crop: the grain lines up with the plate
            if graded is None:
                graded = grade_scene.grade(grade_scene.load(src) if width is None else resized(src, width), look, seed=seed, **GRADE, **extra)
            x0, y0, x1, y1 = crop_after
            grade_scene.save(graded[y0:y1, x0:x1], out, q)
        else:
            grade_scene.process(src, out, look, crop, width, None, q, seed=seed, **GRADE, **extra)
        size = os.path.getsize(out)
        fits = size <= budget
        clean = (not check_edge) or edge_ok(out)
        if (fits and clean) or q <= 30:
            if not fits or not clean:
                print(f"export: {out} at q{q}: {'over budget' if not fits else ''}{' edge not black' if not clean else ''}", flush=True)
            return q, size
        q -= 6 if not fits else 2


def resized(src, width):
    import cv2
    img = grade_scene.load(src)
    h, w = img.shape[:2]
    if w == width:
        return img
    return cv2.resize(img, (width, int(round(h * width / w))), interpolation=cv2.INTER_AREA if w > width else cv2.INTER_CUBIC)


def cmd_wall(a):
    m = load_manifest()
    commit = git_commit()
    out_dir = ASSETS / "wall" / a.layout / a.knob
    out_dir.mkdir(parents=True, exist_ok=True)
    lit = WORK / f"{a.layout}-{a.knob}-lit.png"
    dark = WORK / f"{a.layout}-{a.knob}-dark.png"
    rects = json.loads(lit.with_suffix(".rects.json").read_text())
    width = rects["plate"]["width"]
    height = rects["plate"]["height"]
    seed = grade_scene.seed_for(f"plate-{a.layout}-{a.knob}")
    report = {}
    files = []
    for ext in ("avif", "webp"):
        out = out_dir / f"plate-lit.{ext}"
        q, size = encode_within(lit, out, LOOK["wall"], width, BUDGET["wall-plate"](width), seed, extra={"edge": EDGE["wall"]})
        report[ext] = {"quality": q, "bytes": size}
        files.append(f"wall/{a.layout}/{a.knob}/plate-lit.{ext}")
    print(f"plate-lit {a.layout} {a.knob}: {report}", flush=True)
    render_cmd = {v: queue_cmd(f"wall-{a.layout}-{v}", f"drawer_wall.py wall --layout {a.layout} --knob {a.knob} --variant {v}") for v in ("lit", "dark")}
    export_cmd = f"wall_export.py wall --layout {a.layout} --knob {a.knob} ({grade_note('wall')})"
    put(m, {"id": f"wall/{a.layout}/{a.knob}/plate-lit", "kind": "wall-plate", "files": files, "status": a.status,
            "tool": "tools/blender/drawer_wall.py", "command": f"{render_cmd['lit']}; {export_cmd}",
            "sourceCommit": commit, "layout": a.layout, "knob": a.knob, "width": width, "height": height,
            "checks": {"avifBytes": report["avif"]["bytes"], "webpBytes": report["webp"]["bytes"], "avifQuality": report["avif"]["quality"],
                       "edgeBlackMaxAvif": edge_max(out_dir / "plate-lit.avif"), "edgeBlackMaxWebp": edge_max(out_dir / "plate-lit.webp"),
                       "grade": f"{LOOK['wall']} e{GRADE['exposure']} toe{GRADE['toe']}"}})
    # both renders graded whole with the plate's seed, kept in work/ for the check (drawer_wall.py check compares the
    # dark crops with the dark one, and the lit with the dark outside the crops); then each drawer's crop of the dark
    grade_scene.save(grade_scene.grade(resized(lit, width), LOOK["wall"], seed=seed, **grade_for("wall")), WORK / f"{a.layout}-{a.knob}-lit.graded.png")
    graded_dark = WORK / f"{a.layout}-{a.knob}-dark.graded.png"
    s = grade_scene.grade(resized(dark, width), LOOK["wall"], seed=seed, **grade_for("wall"))
    grade_scene.save(s, graded_dark)
    for d in rects["drawers"]:
        c = d["crop"]
        x0, y0 = int(round(c["x"] / 100 * width)), int(round(c["y"] / 100 * height))
        x1, y1 = int(round((c["x"] + c["w"]) / 100 * width)), int(round((c["y"] + c["h"]) / 100 * height))
        d["cropPx"] = {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}
        files = []
        rep = {}
        for ext in ("avif", "webp"):
            out = out_dir / f"bay-{d['index']:02d}-dark.{ext}"
            q = 82
            while True:
                grade_scene.save(s[y0:y1, x0:x1], out, q)
                size = os.path.getsize(out)
                if size <= BUDGET["wall-dark"](width) or q <= 30:
                    break
                q -= 6
            rep[ext] = size
            files.append(f"wall/{a.layout}/{a.knob}/bay-{d['index']:02d}-dark.{ext}")
        put(m, {"id": f"wall/{a.layout}/{a.knob}/bay-{d['index']:02d}-dark", "kind": "wall-dark", "files": files, "status": a.status,
                "tool": "tools/blender/drawer_wall.py", "command": f"{render_cmd['dark']}; {export_cmd}",
                "sourceCommit": commit, "layout": a.layout, "knob": a.knob, "width": x1 - x0, "height": y1 - y0,
                "checks": {"avifBytes": rep["avif"], "webpBytes": rep["webp"], "cropPx": f"{x0},{y0},{x1 - x0},{y1 - y0}", "seed": "the plate's (graded whole, then cut)"}})
    (out_dir / "rects.json").write_text(json.dumps(rects, indent=1) + "\n")
    put(m, {"id": f"wall/{a.layout}/{a.knob}/rects", "kind": "rects", "files": [f"wall/{a.layout}/{a.knob}/rects.json"], "status": a.status,
            "tool": "tools/blender/drawer_wall.py", "command": f"{render_cmd['lit']} (writes the rects); {export_cmd}", "sourceCommit": commit,
            "layout": a.layout, "knob": a.knob, "width": width, "height": height,
            "checks": {"drawers": len(rects["drawers"]), "verifiedBy": f"drawer_wall.py check --layout {a.layout} --knob {a.knob}"}})
    save_manifest(m)
    print(f"wall {a.layout} {a.knob}: {len(rects['drawers'])} dark crops, rects.json, manifest updated", flush=True)


def composite_regions(frame):
    """A frame's sequence from its region renders (DRAWER-WALL.md, The drawer view): each region, rendered with the
    frame in the drawer, laid over the base frame with an 8 px feather at its edges; frames before the interior
    shows are the base frames themselves. Writes work/wall/seq/<frame>/NNN.png next to the regions."""
    import cv2
    import numpy as np
    base_dir = WORK / "seq" / "base"
    src_dir = WORK / "seq" / frame
    made = 0
    for base in sorted(base_dir.glob("[0-9][0-9][0-9].png")):
        i = int(base.stem)
        region = src_dir / f"{i:03d}.region.png"
        meta = src_dir / f"{i:03d}.region.json"
        out = src_dir / f"{i:03d}.png"
        if out.exists() and (not region.exists() or out.stat().st_mtime >= region.stat().st_mtime):
            continue
        b = cv2.imread(str(base), cv2.IMREAD_UNCHANGED)
        if not region.exists() or not meta.exists():
            cv2.imwrite(str(out), b)
            made += 1
            continue
        r = cv2.imread(str(region), cv2.IMREAD_UNCHANGED)
        x0, y0, x1, y1 = json.loads(meta.read_text())["border"]
        H, W = b.shape[:2]
        px0, py0 = int(round(x0 * W)), int(round(y0 * H))
        px1, py1 = px0 + r.shape[1], py0 + r.shape[0]
        if px1 > W or py1 > H:
            r = r[: H - py0, : W - px0]
            px1, py1 = px0 + r.shape[1], py0 + r.shape[0]
        # the feather: 8 px of ramp inside the region's edges, except along the frame's own edges
        fh, fw = r.shape[:2]
        f = 8
        yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
        ramp = np.ones((fh, fw), np.float32)
        if px0 > 0: ramp = np.minimum(ramp, np.clip((xx + 1) / f, 0, 1))
        if px1 < W: ramp = np.minimum(ramp, np.clip((fw - xx) / f, 0, 1))
        if py0 > 0: ramp = np.minimum(ramp, np.clip((yy + 1) / f, 0, 1))
        if py1 < H: ramp = np.minimum(ramp, np.clip((fh - yy) / f, 0, 1))
        patch = b[py0:py1, px0:px1].astype(np.float32)
        rr = r[..., :3].astype(np.float32)
        b[py0:py1, px0:px1] = (rr * ramp[..., None] + patch[..., :3] * (1 - ramp[..., None])).astype(b.dtype) if b.shape[-1] == 3 else \
            np.dstack([(rr * ramp[..., None] + patch[..., :3] * (1 - ramp[..., None])), patch[..., 3:4]]).astype(b.dtype)
        cv2.imwrite(str(out), b)
        made += 1
    print(f"composited {made} frames for {frame}", flush=True)


def cmd_sequence(a):
    m = load_manifest()
    commit = git_commit()
    name = a.frame or "base"
    src_dir = WORK / "seq" / name
    if a.frame:
        composite_regions(a.frame)
    frames = sorted(src_dir.glob("[0-9][0-9][0-9].png"))
    if not frames:
        raise SystemExit(f"no frames in {src_dir}")
    for width in a.width:
        out_dir = ASSETS / "seq" / name / str(width)
        out_dir.mkdir(parents=True, exist_ok=True)
        for f in frames:
            i = int(f.stem)
            files, rep = [], {}
            for ext in ("avif", "webp"):
                out = out_dir / f"{i:03d}.{ext}"
                q, size = encode_within(f, out, LOOK["sequence"], width, BUDGET["sequence-frame"](width), grade_scene.seed_for(f"seq-{name}-{i:03d}"), extra={"edge": EDGE["sequence"]})
                rep[ext] = {"quality": q, "bytes": size}
                files.append(f"seq/{name}/{width}/{i:03d}.{ext}")
            render_cmd = queue_cmd(f"seq-{name}-{i:03d}", f"drawer_wall.py sequence --frames {len(frames)} --only {i}{' --frame ' + a.frame + ' --region' if a.frame else ''}")
            if a.frame and i < 3:
                render_cmd = queue_cmd(f"seq-base-{i:03d}", f"drawer_wall.py sequence --frames {len(frames)} --only {i}") + " (the base frame: the interior does not show yet)"
            elif a.frame:
                render_cmd += f" over {queue_cmd(f'seq-base-{i:03d}', 'the base frame')} (an 8 px feather)"
            entry = {"id": f"seq/{name}/{width}/{i:03d}", "kind": "sequence-frame", "files": files, "status": a.status,
                     "tool": "tools/blender/drawer_wall.py", "command": f"{render_cmd}; wall_export.py sequence{' --frame ' + a.frame if a.frame else ''} --width {width} ({grade_note('sequence')})",
                     "sourceCommit": commit, "width": width, "height": int(round(width * 1500 / 1200)),
                     "checks": {"avifBytes": rep["avif"]["bytes"], "webpBytes": rep["webp"]["bytes"], "avifQuality": rep["avif"]["quality"],
                                "edgeBlackMaxAvif": edge_max(out_dir / f"{i:03d}.avif"), "edgeBlackMaxWebp": edge_max(out_dir / f"{i:03d}.webp"), "grade": LOOK["sequence"]}}
            if a.frame:
                entry["frame"] = a.frame
            put(m, entry)
            print(f"seq {name} {width} {i:03d}: avif {rep['avif']['bytes'] // KB} KB q{rep['avif']['quality']}, webp {rep['webp']['bytes'] // KB} KB q{rep['webp']['quality']}", flush=True)
    save_manifest(m)


def cmd_cameras(a):
    m = load_manifest()
    commit = git_commit()
    out_dir = ASSETS / "camera"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("open", "inspect"):
        src = WORK / "camera" / f"{name}.json"
        if not src.exists():
            src = WORK / "seq" / f"{name}.json"
        shutil.copyfile(src, out_dir / f"{name}.json")
        data = json.loads((out_dir / f"{name}.json").read_text())
        put(m, {"id": f"camera/{name}", "kind": "camera", "files": [f"camera/{name}.json"], "status": a.status,
                "tool": "tools/blender/drawer_wall.py", "command": f"{queue_cmd('cameras', 'drawer_wall.py cameras')}; wall_export.py cameras", "sourceCommit": commit,
                "checks": {"frames": ",".join(sorted(data.get("frames", {}))), "lensMm": data["camera"]["lens_mm"], "fovDeg": round(data["camera"]["three"]["fov_deg"], 3)}})
    save_manifest(m)
    print("cameras exported", flush=True)


def cmd_env(a):
    m = load_manifest()
    commit = git_commit()
    out_dir = ASSETS / "env"
    out_dir.mkdir(parents=True, exist_ok=True)
    src = WORK / "env" / "drawer.hdr"
    shutil.copyfile(src, out_dir / "drawer.hdr")
    size = os.path.getsize(out_dir / "drawer.hdr")
    width = 1024
    if size > BUDGET["env"](1024):
        # the RGBE file at 1024 x 512 runs over the 600 KB budget: the map goes down to 768 x 384 (the live frame
        # filters it to a PMREM anyway), and the manifest records the size it shipped at
        import cv2
        env = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
        small = cv2.resize(env, (768, 384), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(out_dir / "drawer.hdr"), small)
        size = os.path.getsize(out_dir / "drawer.hdr")
        width = 768
    put(m, {"id": "env/drawer", "kind": "env", "files": ["env/drawer.hdr"], "status": a.status,
            "tool": "tools/blender/drawer_wall.py", "command": f"{queue_cmd('env', 'drawer_wall.py env')}; wall_export.py env", "sourceCommit": commit, "width": width, "height": width // 2,
            "checks": {"bytes": size, "withinBudget": size <= BUDGET["env"](1024)}})
    save_manifest(m)
    print(f"env exported: {size // KB} KB", flush=True)


def read_still(src, width=None):
    """A lifted still (RGBA PNG, straight alpha, the view transform applied) as linear RGB and alpha, float32, at
    `width` px wide."""
    import cv2
    import numpy as np
    im = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    im = im.astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)
    if width and im.shape[1] != width:
        im = cv2.resize(im, (width, int(round(im.shape[0] * width / im.shape[1]))), interpolation=cv2.INTER_AREA if im.shape[1] > width else cv2.INTER_CUBIC)
    rgb = grade_scene.to_linear(cv2.cvtColor(np.ascontiguousarray(im[..., :3]), cv2.COLOR_BGR2RGB))
    alpha = im[..., 3] if im.shape[-1] == 4 else np.ones(im.shape[:2], np.float32)
    return rgb, alpha


def still_over(src, base, width):
    """The still composited over a base frame (both linear), for R1 and the contact sheet."""
    import cv2
    import numpy as np
    rgb, alpha = read_still(src, width)
    b = grade_scene.load(base)
    b = cv2.resize(b, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_AREA)
    return rgb * alpha[..., None] + b * (1 - alpha[..., None])


def save_rgba(s, alpha, out, quality):
    """An sRGB float image with its alpha as an RGBA AVIF or WebP."""
    import numpy as np
    from PIL import Image
    import pillow_avif  # noqa: F401
    rgba = np.dstack([(s * 255 + 0.5).astype(np.uint8), (alpha * 255 + 0.5).astype(np.uint8)])
    im = Image.fromarray(rgba, "RGBA")
    if out.suffix == ".avif":
        im.save(out, "AVIF", quality=quality, speed=4)
    else:
        im.save(out, "WEBP", quality=quality, method=6)


def cmd_stills(a):
    """The lifted stills (DRAWER-WALL.md, The frames in 3D): work/wall/stills/<frame>-lifted.png, the frame alone
    on transparency at the inspect pose, graded as the wall is (its colour over black, then unpremultiplied, the alpha
    kept) to wall/assets/stills/<frame>-lifted.{avif,webp} at 1200 px within 200 KB; kind `still`."""
    import numpy as np
    m = load_manifest()
    commit = git_commit()
    out_dir = ASSETS / "stills"
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = a.frame or sorted(p.name[:3] for p in (WORK / "stills").glob("F0?-lifted.png"))
    for fid in frames:
        src = WORK / "stills" / f"{fid}-lifted.png"
        if not src.exists():
            print(f"stills: {src.relative_to(ROOT)} is not rendered yet; skipped", flush=True)
            continue
        rgb, alpha = read_still(src, a.width)
        g = grade_scene.grade(rgb * alpha[..., None], LOOK["still"], seed=grade_scene.seed_for(f"stills-{fid}-lifted"), **grade_for("still"))
        # the grade saw the frame over black (premultiplied); the browser composites straight colour, so divide the
        # alpha back out where there is enough of it to divide by
        g = np.where(alpha[..., None] > 0.02, np.clip(g / np.maximum(alpha[..., None], 0.02), 0, 1), 0).astype(np.float32)
        files, rep = [], {}
        for ext in ("avif", "webp"):
            out = out_dir / f"{fid}-lifted.{ext}"
            q = 84
            while True:
                save_rgba(g, alpha, out, q)
                size = os.path.getsize(out)
                if size <= BUDGET["still"](a.width) or q <= 30:
                    break
                q -= 6
            rep[ext] = {"quality": q, "bytes": size}
            files.append(f"stills/{fid}-lifted.{ext}")
        put(m, {"id": f"stills/{fid}-lifted", "kind": "still", "files": files, "status": a.status, "frame": fid,
                "tool": "tools/blender/drawer_wall.py", "command": f"{queue_cmd(f'lifted-{fid}', f'drawer_wall.py lifted --frame {fid}')}; wall_export.py stills --frame {fid} --width {a.width} ({grade_note('still')})",
                "sourceCommit": commit, "width": g.shape[1], "height": g.shape[0],
                "checks": {"avifBytes": rep["avif"]["bytes"], "webpBytes": rep["webp"]["bytes"], "avifQuality": rep["avif"]["quality"], "alpha": True,
                           "alphaCoverage": round(float((alpha > 0.5).mean()), 4), "grade": LOOK["still"]}})
        print(f"still {fid}: avif {rep['avif']['bytes'] // KB} KB q{rep['avif']['quality']}, webp {rep['webp']['bytes'] // KB} KB, {g.shape[1]}x{g.shape[0]}", flush=True)
    save_manifest(m)


def cmd_knobs(a):
    out_dir = ROOT / "docs" / "build" / "drawer-wall" / "review" / "R1"
    out_dir.mkdir(parents=True, exist_ok=True)
    for knob in ("black-relief", "gold", "plain"):
        src = WORK / f"knob-{knob}.png"
        if src.exists():
            grade_scene.process(src, out_dir / f"knob-{knob}.jpg", LOOK["knob"], None, 1024, None, 86, **grade_for("knob"))
            print("knob", knob, flush=True)


def cmd_r1(a):
    """R1, the founder's first look (DRAWER-WALL.md, D3): docs/build/drawer-wall/review/R1/ with a contact sheet of
    both walls lit and dark, the view's frames 0, 8, 16 and 23, the three knob close-ups and one lifted still, each
    graded as the wall is, plus the pieces as single JPEGs and an index.md."""
    from PIL import Image, ImageDraw
    out_dir = ROOT / "docs" / "build" / "drawer-wall" / "review" / "R1"
    out_dir.mkdir(parents=True, exist_ok=True)
    pieces = []
    for layout in ("portrait", "landscape"):
        for variant in ("lit", "dark"):
            src = WORK / f"{layout}-black-relief-{variant}.png"
            if src.exists():
                out = out_dir / f"wall-{layout}-{variant}.jpg"
                grade_scene.process(src, out, LOOK["wall"], None, 1170 if layout == "portrait" else 1600, None, 84, seed=grade_scene.seed_for(f"plate-{layout}-black-relief"), **grade_for("wall"))
                pieces.append((f"The {layout} wall, every drawer {variant}", out))
    for i in (0, 8, 16, 23):
        src = WORK / "seq" / "base" / f"{i:03d}.png"
        if src.exists():
            out = out_dir / f"view-{i:02d}.jpg"
            grade_scene.process(src, out, LOOK["sequence"], None, 900, None, 84, seed=grade_scene.seed_for(f"seq-base-{i:03d}"), **grade_for("sequence"))
            pieces.append((f"The drawer view, frame {i} of 24", out))
    for knob in ("black-relief", "gold", "plain"):
        src = WORK / f"knob-{knob}.png"
        if src.exists():
            out = out_dir / f"knob-{knob}.jpg"
            grade_scene.process(src, out, LOOK["knob"], None, 900, None, 86, **grade_for("knob"))
            pieces.append((f"The knob, {knob} (O15)", out))
    src = WORK / "stills" / "F09-lifted.png"
    base = WORK / "seq" / "base" / "023.png"
    if src.exists() and base.exists():
        out = out_dir / "lifted-F09.jpg"
        grade_scene.save(grade_scene.grade(still_over(src, base, 900), LOOK["still"], seed=grade_scene.seed_for("stills-F09-lifted"), **grade_for("sequence")), out, 84)
        pieces.append(("F09 lifted into the light, over the open drawer (the still; the live frame takes this pose)", out))
    # the contact sheet: every piece scaled into a 3-wide grid on black, labelled
    cell_w, pad = 600, 24
    thumbs = []
    for label, path in pieces:
        im = Image.open(path).convert("RGB")
        k = cell_w / im.size[0]
        thumbs.append((label, im.resize((cell_w, int(im.size[1] * k)), Image.LANCZOS)))
    cols = 3
    rows = [thumbs[i:i + cols] for i in range(0, len(thumbs), cols)]
    row_h = [max(t.size[1] for _, t in r) + 40 for r in rows]
    sheet = Image.new("RGB", (cols * (cell_w + pad) + pad, sum(row_h) + pad * (len(rows) + 1)), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    y = pad
    for r, rh in zip(rows, row_h):
        x = pad
        for label, t in r:
            sheet.paste(t, (x, y))
            d.text((x, y + t.size[1] + 10), label, fill=(166, 165, 161))
            x += cell_w + pad
        y += rh + pad
    sheet.save(out_dir / "contact-sheet.jpg", quality=82)
    lines = ["# R1 · the founder's first look", "", "Made by `tools/blender/wall_export.py r1` on the renders in `work/wall/` (DRAWER-WALL.md, D3). Every image is graded as the wall is. Black relief is the knob's default (O15); the gold and plain close-ups are the alternatives. Answer on the D3 pull request.", "", "![contact sheet](contact-sheet.jpg)", ""]
    for label, path in pieces:
        lines.append(f"- {label}: `{path.name}`")
    (out_dir / "index.md").write_text("\n".join(lines) + "\n")
    print(f"R1: {len(pieces)} pieces and the contact sheet in {out_dir.relative_to(ROOT)}", flush=True)


def cmd_prune(a):
    m = load_manifest()
    before = len(m["assets"])
    m["assets"] = [e for e in m["assets"] if all((ASSETS / f).exists() for f in e["files"])]
    save_manifest(m)
    print(f"pruned {before - len(m['assets'])} entries", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("wall")
    p.add_argument("--layout", required=True)
    p.add_argument("--knob", default="black-relief")
    p.add_argument("--status", default="mockup", choices=["prototype", "mockup", "final"])
    p = sub.add_parser("sequence")
    p.add_argument("--frame", default=None)
    p.add_argument("--width", type=int, action="append", default=None)
    p.add_argument("--status", default="mockup", choices=["prototype", "mockup", "final"])
    for name in ("cameras", "env"):
        p = sub.add_parser(name)
        p.add_argument("--status", default="mockup", choices=["prototype", "mockup", "final"])
    p = sub.add_parser("stills")
    p.add_argument("--frame", action="append", default=None)
    p.add_argument("--width", type=int, default=1200)
    p.add_argument("--status", default="mockup", choices=["prototype", "mockup", "final"])
    sub.add_parser("knobs")
    sub.add_parser("r1")
    sub.add_parser("prune")
    a = ap.parse_args()
    if a.cmd == "sequence" and not a.width:
        a.width = [720, 1200]
    {"wall": cmd_wall, "sequence": cmd_sequence, "cameras": cmd_cameras, "env": cmd_env, "stills": cmd_stills, "knobs": cmd_knobs, "r1": cmd_r1, "prune": cmd_prune}[a.cmd](a)


if __name__ == "__main__":
    main()
