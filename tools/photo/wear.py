#!/usr/bin/env python3
"""Put a real, cleaned frame on a generated person (docs/brief/07-photography.md, track 2).

    python3 tools/photo/wear.py content/photography/people/W1-S07-F02-A1.json

The person is generated without glasses (reference/casting/model-bibles.md). The frame comes from
the cleaned lightbox shot of the matching angle (work/out/<shot>/layers, from clean_lightbox.py).
Nothing about the frame is generated: its pixels are the photograph, its size is the 1:1 drawing.

Steps: face landmarks and head pose (InsightFace, models from GitHub releases) -> scale from the
pupils (an assumed pupillary distance) -> fit the photographed lens openings onto the drawing's
lens openings at that scale and pose (a homography from eight points) -> lens layer: each lens's
measured tint, flat, over the eyes (nothing that sat behind the lens in the product shot) ->
the frame's contact shadow on the skin -> the frame lit like the scene (white balance and level
of the scene's backdrop against the tent's) -> one soft reflection per lens -> the SS90 grade
(lifted blacks, warm whites, low saturation, halation, grain) over the whole picture.

Writes work/people/<id>/: composite.png (16-bit), composite.jpg, compare.jpg, report.json.
"""
import io
import json
import pathlib
import re
import sys

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from clean_lightbox import hex_lin, lin_to_srgb, load_srgb, lum, srgb_to_lin  # noqa: E402


# ---------- the frame's true geometry, from the 1:1 drawing ----------
def drawing_lens_points(frame_id, px_per_mm=20):
    """Extreme points (left, right, top, bottom) of both lens openings in the front view, in mm,
    origin midway between the two lens-box centres, y down. Image left = the wearer's right."""
    import cairosvg
    from scipy import ndimage as ndi
    svg = (ROOT / "content" / "products" / "drawings" / f"{frame_id}-front.svg").read_text()
    svg = svg.replace("currentColor", "#000").replace('stroke-width="0.25"', 'stroke-width="0.06"')
    svg = svg.replace('vector-effect="non-scaling-stroke"', "")
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    w, h = int(vb[2] * px_per_mm), int(vb[3] * px_per_mm)
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=w, output_height=h, background_color="white")
    im = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_GRAYSCALE)
    free = 1 - cv2.dilate((im < 200).astype(np.uint8), np.ones((3, 3), np.uint8))
    lab, n = ndi.label(free)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    sizes = ndi.sum(np.ones_like(lab), lab, range(1, n + 1))
    best = sorted([(sizes[i - 1], i) for i in range(1, n + 1) if i not in border], reverse=True)[:2]
    lenses = sorted([np.argwhere(lab == i)[:, ::-1] / px_per_mm for _, i in best], key=lambda p: p[:, 0].mean())
    centres = [((p[:, 0].min() + p[:, 0].max()) / 2, (p[:, 1].min() + p[:, 1].max()) / 2) for p in lenses]
    origin = np.mean(centres, axis=0)
    return [extremes(p) - origin for p in lenses]


def extremes(pts):
    """Leftmost, rightmost, topmost, bottommost points of a point set (x, y), each the mean of its
    extreme band, so a flat edge gives its middle."""
    out = []
    for axis, sign in ((0, -1), (0, 1), (1, -1), (1, 1)):
        v = pts[:, axis] * sign
        band = pts[v >= v.max() - 0.4 * (np.ptp(pts[:, axis]) / 100 + 0.02)]
        out.append(band.mean(axis=0))
    return np.array(out)


# ---------- the person ----------
def face_of(img_bgr):
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name="buffalo_s", providers=["CPUExecutionProvider"],
                       allowed_modules=["detection", "landmark_2d_106", "landmark_3d_68"])
    app.prepare(ctx_id=-1, det_size=(640, 640))
    faces = sorted(app.get(img_bgr), key=lambda f: -(f.bbox[2] - f.bbox[0]))
    if not faces:
        raise SystemExit("no face found")
    return faces[0]


# ---------- the grade ----------
def ss90(srgb, seed=1):
    """Lifted blacks, warm paper whites, low saturation, faint halation, fine grain (01-brand-system.md)."""
    x = srgb.astype(np.float32)
    y = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
    x = y + (x - y) * 0.85                                        # low saturation
    hi = np.clip((y - 0.55) / 0.45, 0, 1)
    x = x * (1 + hi * np.array([0.012, 0.0, -0.03], np.float32))  # warm whites
    glow = cv2.GaussianBlur(np.clip(y[..., 0] - 0.82, 0, 1), (0, 0), 7)[..., None]
    x = x + glow * np.array([0.55, 0.22, 0.12], np.float32) * 0.35  # halation on the brightest whites
    x = 0.043 + (1 - 0.043) * np.clip(x, 0, 1)                    # blacks lifted to about #0B0B0C
    g = np.random.default_rng(seed).normal(0, 1, x.shape[:2]).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 0.7) * 0.022 * (1 - 0.5 * y[..., 0])
    return np.clip(x + g[..., None], 0, 1)


def main(cfg_path):
    cfg = json.loads(pathlib.Path(cfg_path).read_text())
    out = ROOT / "work" / "people" / cfg["id"]
    out.mkdir(parents=True, exist_ok=True)
    report = {"id": cfg["id"], "cast": cfg["cast"], "scene": cfg["scene"], "frame": cfg["frame"], "product_shot": cfg["product_shot"]}

    # the person
    person = load_srgb(ROOT / cfg["portrait"])
    lin = srgb_to_lin(person)
    H, W = lin.shape[:2]
    face = face_of(cv2.cvtColor((person * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    eyes = np.array(sorted(face.kps[:2].tolist()), np.float32)      # image left eye first
    mid = eyes.mean(0)
    ipd = float(np.linalg.norm(eyes[1] - eyes[0]))
    s = ipd / cfg.get("pd_mm", 62.0)                                  # px per mm on the face
    roll = float(np.arctan2(eyes[1][1] - eyes[0][1], eyes[1][0] - eyes[0][0]))
    dx = float(face.kps[2][0] - mid[0])                               # nose tip right of the eye midpoint: turned to image right
    yaw = np.radians(abs(float(face.pose[1]))) * (1 if dx >= 0 else -1)
    report["face"] = {"ipd_px": round(ipd, 1), "px_per_mm": round(s, 3), "roll_deg": round(np.degrees(roll), 2),
                      "yaw_deg": round(np.degrees(yaw), 2), "pitch_deg": round(float(face.pose[0]), 2)}

    # the frame: cleaned layers and the lens masks of its product shot
    shot = cfg["product_shot"]
    po = ROOT / "work" / "out" / shot
    rep = json.loads((po / "report.json").read_text())
    scfg = json.loads((ROOT / "content" / "photography" / "shots" / f"{shot}.json").read_text())
    cl, ct = rep["crop"][:2]
    rx, ry = scfg["region"][:2]
    fr = np.asarray(Image.open(po / "layers" / "frame.png"), np.float32) / 255
    F, A = srgb_to_lin(fr[..., :3]), fr[..., 3]
    T = srgb_to_lin(np.asarray(Image.open(po / "layers" / "lens.png"), np.float32) / 255)
    masks = sorted(po.glob("masks/lens-*.png"))
    lens_src = []
    from scipy import ndimage as ndi
    for mp in masks:
        m = ndi.binary_fill_holes(np.asarray(Image.open(mp)) > 128)   # a lens has no holes
        full = np.zeros(A.shape, bool)                                # region coords -> layer coords
        ys, xs = np.nonzero(m)
        xs, ys = xs + rx - cl, ys + ry - ct
        ok = (xs >= 0) & (ys >= 0) & (xs < A.shape[1]) & (ys < A.shape[0])
        full[ys[ok], xs[ok]] = True
        lens_src.append(full)
    lens_src.sort(key=lambda m: np.nonzero(m)[1].mean())
    src = np.concatenate([extremes(np.argwhere(m)[:, ::-1].astype(np.float32)) for m in lens_src])

    # where those points go on the face: the drawing's lens openings, at the face's scale and pose
    dst_mm = np.concatenate(drawing_lens_points(cfg["frame"]))
    drop = cfg.get("lens_drop_mm", 3.0)
    vertex = cfg.get("vertex_mm", 12.0)
    c, sn = np.cos(roll), np.sin(roll)
    Rm = np.array([[c, -sn], [sn, c]], np.float32)
    # the bridge sits on the nose: horizontally the frame centres on the nose bridge at eye level
    # (InsightFace 106-point landmark 72), which already carries the head's turn
    bridge_x = float(face.landmark_2d_106[72][0]) if cfg.get("centre_on_nose", True) else mid[0] + vertex * np.sin(yaw) * s
    anchor = np.array([bridge_x, mid[1]], np.float32)
    pts = np.stack([dst_mm[:, 0] * np.cos(yaw), dst_mm[:, 1] + drop], 1) * s
    dst = (Rm @ pts.T).T + anchor
    Hm, _ = cv2.findHomography(src.astype(np.float32), dst.astype(np.float32), 0)
    # pre-shrink the photographed frame to about twice its size on the face, so warping doesn't alias
    scale = np.sqrt(abs(np.linalg.det(Hm[:2, :2])))
    pre = min(1.0, 2.0 * scale)
    Dn = np.diag([pre, pre, 1.0])
    small = lambda a: cv2.resize(a, None, fx=pre, fy=pre, interpolation=cv2.INTER_AREA) if pre < 1 else a
    Hs = Hm @ np.linalg.inv(Dn)
    warp = lambda a, border=0: cv2.warpPerspective(small(a), Hs, (W, H), flags=cv2.INTER_LINEAR,
                                                   borderMode=cv2.BORDER_CONSTANT, borderValue=border)
    PA = warp(np.dstack([F * A[..., None], A]).astype(np.float32))
    if cfg.get("soften_px", 0.6):
        PA = cv2.GaussianBlur(PA, (0, 0), cfg.get("soften_px", 0.6))
    Aw = np.clip(PA[..., 3], 0, 1)
    Fw = np.where(Aw[..., None] > 1e-4, PA[..., :3] / np.maximum(Aw[..., None], 1e-4), 0)
    report["frame_width_px"] = round(float(np.ptp(np.nonzero(Aw > 0.5)[1])), 1)

    # lens layer on the face: each lens's own tint, flat, nothing that was behind it in the product shot
    Tface = np.ones_like(lin)
    tints, lens_on_face = [], []
    for m in lens_src:
        er = cv2.erode(m.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
        vals = T[er]
        keep = lum(vals) > 0.5 * np.median(lum(vals))
        tint = np.median(vals[keep], axis=0)
        tints.append([round(float(v), 4) for v in tint])
        mw = np.clip(warp(cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0)), 0, 1)
        lens_on_face.append(mw)
        fill = cfg.get("eye_fill", 0.35)              # share of the light that reaches the eyes around the frame
        eff = tint * (fill + (1 - fill) * tint)
        Tface = Tface * (1 - mw[..., None] * (1 - eff))
    report["lens_tint_rgb"] = tints

    # the frame lit like the scene: backdrop against the tent it was shot in
    full = load_srgb(ROOT / "work" / "originals" / f"{shot}.jpg")
    alpha = np.asarray(Image.open(po / "masks" / "alpha.png"), np.float32) / 255
    rg = srgb_to_lin(full[scfg["region"][1]:scfg["region"][3], scfg["region"][0]:scfg["region"][2]])
    far = cv2.distanceTransform((alpha < 0.02).astype(np.uint8), cv2.DIST_L2, 5) > 200
    tent = np.median(rg[far], axis=0)
    bd = cfg.get("backdrop_box")                                      # [x0, y0, x1, y1] of clean backdrop in the portrait
    back = np.median(lin[bd[1]:bd[3], bd[0]:bd[2]].reshape(-1, 3), axis=0)
    gain = back / tent
    g_l = float(lum(gain[None])[0])
    gain = gain / g_l * float(np.clip(g_l, 0.85, 1.25)) * cfg.get("light_gain", 1.0)
    Fw = Fw * gain
    report["light"] = {"tent_lin": [round(float(v), 3) for v in tent], "backdrop_lin": [round(float(v), 3) for v in back],
                       "gain": [round(float(v), 3) for v in gain]}

    # the frame's contact shadow on the skin (flash a little above the lens: the shadow drops a little)
    sh = cfg.get("shadow", {})
    dy = sh.get("offset_mm", 1.2) * s
    Ms = np.float32([[1, 0, 0], [0, 1, dy]])
    shadow = cv2.GaussianBlur(cv2.warpAffine(Aw, Ms, (W, H)), (0, 0), sh.get("blur_mm", 1.0) * s)
    face_lin = lin * (1 - sh.get("strength", 0.45) * shadow[..., None])

    # one soft reflection per lens: the flash, high on the lens, towards the outer side
    refl = np.zeros((H, W), np.float32)
    k = cfg.get("reflection", {}).get("strength", 0.02)
    if k:
        yy, xx = np.mgrid[0:H, 0:W]
        for m, mw in zip(lens_src, lens_on_face):
            ys, xs = np.nonzero(m)
            cx, cy = xs.mean(), ys.min() + 0.3 * np.ptp(ys)
            cx += (0.18 if cx > A.shape[1] / 2 else -0.18) * np.ptp(xs)
            p = cv2.perspectiveTransform(np.float32([[[cx, cy]]]), Hm)[0, 0]
            rad = 0.10 * np.ptp(xs) * scale
            refl += mw * np.exp(-(((xx - p[0]) / (1.6 * rad)) ** 2 + ((yy - p[1]) / rad) ** 2))
        refl = refl * k

    comp = Fw * Aw[..., None] + (1 - Aw[..., None]) * (face_lin * Tface + refl[..., None] * back)
    final = ss90(lin_to_srgb(comp)) if cfg.get("grade", True) else lin_to_srgb(comp)
    cv2.imwrite(str(out / "composite.png"), cv2.cvtColor((final * 65535).astype(np.uint16), cv2.COLOR_RGB2BGR))
    Image.fromarray((final * 255 + 0.5).astype(np.uint8)).save(out / "composite.jpg", quality=94)
    before = ss90(person) if cfg.get("grade", True) else person
    sheet = np.hstack([before, np.ones((H, 16, 3), np.float32), final])
    Image.fromarray((sheet * 255 + 0.5).astype(np.uint8)).save(out / "compare.jpg", quality=90)
    (out / "report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report))


if __name__ == "__main__":
    main(sys.argv[1])
