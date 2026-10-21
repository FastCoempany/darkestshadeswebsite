#!/usr/bin/env python3
"""Put a real, cleaned frame on a generated person (docs/brief/07-photography.md, track 2).

    python3 tools/photo/wear.py content/photography/people/W1-S07-F02-A1.json
    python3 tools/photo/wear.py --all          # every settings file in content/photography/people/

The person is generated without glasses (reference/casting/prompt-pack.md). The frame comes from the
cleaned lightbox shot of the matching angle (work/out/<shot>/layers, from clean_lightbox.py).
Nothing about the frame is generated: its pixels are the photograph, its size is the 1:1 drawing.

Steps: the portrait at twice its size (EDSR super-resolution; the generator returns about 1.2 MP) ->
face landmarks and head pose (InsightFace) -> scale from the pupils (the person's pupillary
distance) -> fit the photographed lens openings onto the drawing's lens openings at that scale and
pose (a homography from eight points) -> in a dark scene, the frame's photographed highlights kept
where they face the key light and dimmed elsewhere (never added) -> only the front is worn: the
drawing's front outline, fitted to the photographed front, cuts temples and what the product camera
saw past the front -> lens layer: each lens's measured tint, flat, over the eyes, running on under
the rim to its solid part (nothing that sat behind the lens in the product shot) -> the frame's
contact shadow on the skin, cast away from the scene's key light -> the frame lit like the scene (the
scene light's color from a neutral patch, its level from the backdrop against the tent's, or set) ->
the lens's front surface: a faint sheen of the room and one soft reflection of the key -> the SS90
grade (lifted blacks, warm whites, low saturation, halation, grain) over the whole picture -> the
crop (3:4 to the gallery's 4:5).

Coordinates in the settings (boxes, polygons, crop) are in the generated portrait's own pixels.
Writes work/people/<id>/: composite.png (16-bit, the crop), composite.jpg, compare.jpg (before and
after), zoom.jpg (the frame at 1:1), report.json; with --debug also debug.npz (the layers round the
frame); --fast composites at the generated size, into work/people/<id>-fast/, for a quick look.
"""
import json
import pathlib
import re
import sys

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from clean_lightbox import STAGE_HEX, hex_lin, lin_to_srgb, load_srgb, lum, srgb_to_lin  # noqa: E402

PEOPLE = ROOT / "content" / "photography" / "people"
DEBUG = "--debug" in sys.argv
FAST = "--fast" in sys.argv


# ---------- the frame's true geometry, from the 1:1 drawing ----------
def drawing_front(frame_id, px_per_mm=20):
    """From the 1:1 front-view drawing: the extreme points (left, right, top, bottom) of both lens
    openings in mm, origin midway between the two lens-box centres, y down (image left = the wearer's
    right); and the front's silhouette (everything inside its outline, lens openings included) as a
    mask at `px_per_mm`, with that origin in its pixels."""
    import cairosvg
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
    silhouette = ~np.isin(lab, [v for v in border if v != 0])      # all but the outside: lines and what they enclose
    return [extremes(p) - origin for p in lenses], silhouette, origin * px_per_mm


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


def upscaled(path, factor=2, region=None):
    """The generated portrait at `factor` times its size, cached beside it: FSRCNN over the whole picture
    and EDSR, the slower and better model, over `region` (the head, where the frame goes), blended in
    softly; both are OpenCV contrib dnn_superres models from GitHub (Saafke), in work/models/. EDSR runs in
    overlapping tiles so it fits this workspace's memory. Only the generated person is upscaled, never
    the frame, which is drawn from its 12 MP photograph at the upscaled size. On a face, EDSR came
    closest of the free models to the original (a portrait halved and brought back: EDSR +1.3 dB over
    bicubic, FSRCNN +0.5, ESPCN +0.3, LapSRN 0); over a whole portrait it took 10 to 20 minutes here,
    where a backdrop or a coat gains nothing from it."""
    path = pathlib.Path(path)
    out = path.with_name(f"{path.stem}-x{factor}.png")
    if out.exists() and out.stat().st_mtime >= path.stat().st_mtime:
        return load_srgb(out)
    im = cv2.imread(str(path), cv2.IMREAD_COLOR)
    h, w = im.shape[:2]
    fast = cv2.dnn_superres.DnnSuperResImpl_create()
    fast.readModel(str(ROOT / "work" / "models" / f"FSRCNN_x{factor}.pb"))
    fast.setModel("fsrcnn", factor)
    up = fast.upsample(im)
    if region is not None:
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        sr.readModel(str(ROOT / "work" / "models" / f"EDSR_x{factor}.pb"))
        sr.setModel("edsr", factor)
        rx0, ry0, rx1, ry1 = [int(v) for v in region]
        rx0, ry0, rx1, ry1 = max(0, rx0), max(0, ry0), min(w, rx1), min(h, ry1)
        best = np.zeros((h * factor, w * factor, 3), np.uint8)
        tile, pad = 192, 16
        for y in range(ry0, ry1, tile):
            for x in range(rx0, rx1, tile):
                y0, x0 = max(0, y - pad), max(0, x - pad)
                y1, x1 = min(h, y + tile + pad), min(w, x + tile + pad)
                t = sr.upsample(np.ascontiguousarray(im[y0:y1, x0:x1]))
                oy, ox = (y - y0) * factor, (x - x0) * factor
                hh, ww = min(tile, ry1 - y) * factor, min(tile, rx1 - x) * factor
                best[y * factor:y * factor + hh, x * factor:x * factor + ww] = t[oy:oy + hh, ox:ox + ww]
        m = np.zeros((h * factor, w * factor), np.float32)
        e = 24 * factor
        m[ry0 * factor + e:ry1 * factor - e, rx0 * factor + e:rx1 * factor - e] = 1
        m = cv2.GaussianBlur(m, (0, 0), e / 2)[..., None]
        up = np.clip(best * m + up * (1 - m) + 0.5, 0, 255).astype(np.uint8)
    cv2.imwrite(str(out), up)
    return load_srgb(out)


# ---------- the grade ----------
def ss90(srgb, seed=1, size=1.0, lift=0.043, sat=0.85, halation=0.35, grain=0.022):
    """Lifted blacks, warm paper whites, low saturation, faint halation, fine grain (01-brand-system.md).
    `size` scales the halation and grain with the picture (1 = 1280 px tall). The strengths are set per
    picture (`grade` in the settings); at the full strength the frames' gloss black went grey and pasty
    next to the product photographs (founder, Oct 21 2026)."""
    x = srgb.astype(np.float32)
    y = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
    x = y + (x - y) * sat                                         # low saturation
    hi = np.clip((y - 0.55) / 0.45, 0, 1)
    x = x * (1 + hi * np.array([0.012, 0.0, -0.03], np.float32))  # warm whites
    glow = cv2.GaussianBlur(np.clip(y[..., 0] - 0.82, 0, 1), (0, 0), 7 * size)[..., None]
    x = x + glow * np.array([0.55, 0.22, 0.12], np.float32) * halation   # halation on the brightest whites
    x = lift + (1 - lift) * np.clip(x, 0, 1)                      # blacks lifted (0.043: about #0B0B0C)
    g = np.random.default_rng(seed).normal(0, 1, x.shape[:2]).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 0.7 * size) * grain * size * (1 - 0.5 * y[..., 0])   # same grain at any size
    return np.clip(x + g[..., None], 0, 1)


def box_median(lin, box, k):
    x0, y0, x1, y1 = [int(round(v * k)) for v in box]
    return np.median(lin[y0:y1, x0:x1].reshape(-1, 3), axis=0)


def polygon_mask(shape, polys, k, feather):
    m = np.zeros(shape, np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.round(np.asarray(p, np.float32) * k).astype(np.int32)], 1)
    m = m.astype(np.float32)
    return cv2.GaussianBlur(m, (0, 0), feather) if feather else m


def relight(F, A, surround, key_from_deg=None, rim_px=40.0, sharp=2.0, gloss=1.0, key_front=0.0, key_spec=None):
    """The frame lit like the scene, from its photograph in the tent.

    Its own photographed highlights are kept where the surface faces the scene's key light and dimmed to
    `surround` (how bright the scene round the frame is against the tent) where it faces anything else.
    In the tent every face of the gloss acetate mirrored bright fabric; in a dark scene only the faces
    turned to the light would. The highlights are the frame's neutral part (a gloss reflection has the
    light's color), so the acetate's own colors (the tortoise, the gold) stay as photographed.

    Which way a face turns is read from the frame's outline: a rim is flat in front and rounds over at
    each edge, a bevel about `rim_px` wide, its normal turning towards the nearest edge. `key_spec`
    adds the scene key's own reflection on those bevels (Blinn-Phong: where the bevel's normal halves the
    angle between the camera and the light, a thin line along the rim, as hard as the light is small):
    a key the tent didn't have leaves its line on gloss acetate, and without it a black frame in a dark
    scene was a flat black shape."""
    mn = F.min(-1)
    solid = A > 0.5
    base = float(np.percentile(mn[solid], 5))
    spec = np.clip(mn - base, 0, None)
    diffuse = F - spec[..., None]
    w = np.zeros_like(spec)
    info = {"spec_base": round(base, 4), "surround": surround, "key_from_deg": key_from_deg, "gloss": gloss,
            "key_front": key_front}
    if key_from_deg is not None or key_front or key_spec:
        d = cv2.distanceTransform(solid.astype(np.uint8), cv2.DIST_L2, 5)
        gy, gx = np.gradient(cv2.GaussianBlur(d, (0, 0), 3))
        mag = np.hypot(gx, gy) + 1e-6
        nx, ny = -gx / mag, -gy / mag                  # the way the surface turns: towards the nearest edge
        tilt = np.clip(1 - d / rim_px, 0, 1)            # 0 where the front is flat, 1 at its edge
        if key_from_deg is not None:
            a = np.radians(key_from_deg)                # image coordinates, y down: 270 = from above
            w = np.clip(nx * np.cos(a) + ny * np.sin(a), 0, 1) ** sharp * tilt
        # a light from the camera's side (a flash, a doorway behind the camera) is mirrored by the faces
        # turned to the camera: there the photographed highlights (the ring light's, on the camera's axis
        # too) stay. Dimmed with the rest, black frames came out flat black shapes.
        w = np.maximum(w, key_front * (1 - tilt) ** 2)
    keep = surround + (1 - surround) * w
    out = diffuse + spec[..., None] * keep[..., None]
    if gloss != 1:
        # a brighter scene than the tent's soft box: the photographed sheen stands out more; only what
        # stands above the acetate's own dark (its 60th percentile) is raised, so black stays black
        t = float(np.percentile(spec[solid], 60))
        out = out + (gloss - 1) * (np.clip(spec - t, 0, None) * keep)[..., None]
    if key_spec:
        al = np.arcsin(tilt)                            # a round bevel: the normal's angle from the camera axis
        n = np.stack([np.sin(al) * nx, np.sin(al) * ny, np.cos(al)], -1)
        th, ph = np.radians(key_spec.get("off_axis_deg", 20)), np.radians(key_spec.get("from_deg", 270))
        L = np.array([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])
        Hv = L + np.array([0, 0, 1.0])
        Hv /= np.linalg.norm(Hv)
        hl = np.clip(n @ Hv, 0, 1) ** key_spec.get("power", 60) * key_spec.get("strength", 0.5)
        hl *= (tilt > 0) * cv2.GaussianBlur(solid.astype(np.float32), (0, 0), 2)
        if key_spec.get("follow_photo", True):
            # where the photograph shows gloss on that bevel, and as much: the line breaks and varies as the
            # acetate's own reflections do (drawn even all round, it read as an embossed outline)
            g = cv2.GaussianBlur(spec, (0, 0), 0.5 * rim_px)
            hl *= np.clip(g / max(float(np.percentile(g[solid], 97)), 1e-4), 0, 1)
        out = out + hl[..., None]
        info["key_spec"] = key_spec
    info["spec_kept"] = round(float((spec * keep)[solid].sum() / max(spec[solid].sum(), 1e-6)), 3)
    return out, info


def fit_outline(sil, Aw, s):
    """The drawing's front outline (on the face, placed by the lens openings) moved onto the
    photographed front: an affine ECC fit of the two filled shapes, blurred by a millimetre, in a box
    round the frame at half size, leaving out what the photograph shows more than 3 mm past the outline
    (temples). Kept only if it is a small correction (under 4 mm at the frame's middle, under 12% of
    scale or shear); otherwise the outline stays where the lens openings put it."""
    ys, xs = np.nonzero(Aw > 0.5)
    m = int(12 * s)
    y0, y1, x0, x1 = max(0, ys.min() - m), min(Aw.shape[0], ys.max() + m), max(0, xs.min() - m), min(Aw.shape[1], xs.max() + m)
    f = 0.5
    filled = ndi.binary_fill_holes(Aw[y0:y1, x0:x1] > 0.5)          # the outline holds the lens openings too
    near = cv2.dilate((sil[y0:y1, x0:x1] > 0.5).astype(np.uint8),       # not what lies far past it (temples)
                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(6 * s) | 1,) * 2)) > 0
    a = cv2.resize((filled & near).astype(np.float32), None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
    b = cv2.resize(sil[y0:y1, x0:x1], None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
    a, b = cv2.GaussianBlur(a, (0, 0), s * f), cv2.GaussianBlur(b, (0, 0), s * f)
    M = np.eye(2, 3, dtype=np.float32)
    try:
        cc, M = cv2.findTransformECC(a, b, M, cv2.MOTION_AFFINE,
                                     (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), None, 5)
    except cv2.error:
        return sil, np.eye(3), {"kept": False, "why": "no fit"}
    cy, cx = [float(v.mean()) for v in np.nonzero(a > 0.5)]
    shift_mm = float(np.hypot(*((M[:, :2] - np.eye(2)) @ [cx, cy] + M[:, 2]))) / f / s   # at the frame's middle
    lin_dev = float(np.abs(M[:, :2] - np.eye(2)).max())
    info = {"shift_mm": round(shift_mm, 2), "linear_dev": round(lin_dev, 4), "cc": round(float(cc), 4)}
    if shift_mm > 4 or lin_dev > 0.12:
        return sil, np.eye(3), dict(info, kept=False)
    # M maps the photograph's box (half size) into the outline's: undo it on the outline, at full size
    T = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]], np.float64)
    S = np.diag([f, f, 1.0])
    Mf = np.linalg.inv(S) @ np.vstack([M, [0, 0, 1]]) @ S
    full = np.linalg.inv(T) @ Mf @ T
    out = cv2.warpAffine(sil, full[:2].astype(np.float32), (sil.shape[1], sil.shape[0]),
                         flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
    return out, full, dict(info, kept=True)


def main(cfg_path):
    cfg = json.loads(pathlib.Path(cfg_path).read_text())
    if FAST:                                        # a quick look at the generated size, beside the real one
        cfg["upscale"], cfg["id"] = 1, cfg["id"] + "-fast"
    out = ROOT / "work" / "people" / cfg["id"]
    out.mkdir(parents=True, exist_ok=True)
    report = {"id": cfg["id"], "cast": cfg["cast"], "scene": cfg["scene"], "frame": cfg["frame"],
              "product_shot": cfg["product_shot"]}

    # the person, at twice the generated size
    k = int(cfg.get("upscale", 1))
    if k > 1:
        raw = cv2.imread(str(ROOT / cfg["portrait"]), cv2.IMREAD_COLOR)
        fb = face_of(raw).bbox                     # the head, and room round it for the frame and the hair
        cx, cy, fw_, fh_ = (fb[0] + fb[2]) / 2, (fb[1] + fb[3]) / 2, fb[2] - fb[0], fb[3] - fb[1]
        region = [cx - 1.1 * fw_, cy - 1.0 * fh_, cx + 1.1 * fw_, cy + 0.9 * fh_]
        person = upscaled(ROOT / cfg["portrait"], k, region)
    else:
        person = load_srgb(ROOT / cfg["portrait"])
    lin = srgb_to_lin(person)
    H, W = lin.shape[:2]
    report["size"] = [W, H]
    report["upscale"] = f"FSRCNN x{k}, EDSR x{k} on the head" if k > 1 else "none"
    face = face_of(cv2.cvtColor((person * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    eyes = np.array(sorted(face.kps[:2].tolist()), np.float32)      # image left eye first
    mid = eyes.mean(0)
    ipd = float(np.linalg.norm(eyes[1] - eyes[0]))
    s = ipd / cfg.get("pd_mm", 62.0)                                  # px per mm on the face
    roll = float(np.arctan2(eyes[1][1] - eyes[0][1], eyes[1][0] - eyes[0][0]))
    dx = float(face.kps[2][0] - mid[0])                               # nose tip right of the eye midpoint: turned to image right
    yaw = np.radians(abs(float(face.pose[1]))) * (1 if dx >= 0 else -1)
    report["face"] = {"ipd_px": round(ipd, 1), "pd_mm": cfg.get("pd_mm", 62.0), "px_per_mm": round(s, 3),
                      "roll_deg": round(np.degrees(roll), 2), "yaw_deg": round(np.degrees(yaw), 2),
                      "pitch_deg": round(float(face.pose[0]), 2)}

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
    lens_src = []
    for mp in sorted(po.glob("masks/lens-*.png")):
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
    ppm = 20
    lens_mm, silhouette, origin_px = drawing_front(cfg["frame"], ppm)
    dst_mm = np.concatenate(lens_mm)
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
    light = cfg.get("light", {})
    surround = float(light.get("surround", 1.0))
    key_from = light.get("key_from_deg")
    gloss = float(light.get("gloss", 1.0))
    if surround < 1 or key_from is not None or gloss != 1 or light.get("key_spec"):
        F, report["relight"] = relight(F, A, surround, key_from, rim_px=light.get("rim_mm", 2.0) * s / scale, gloss=gloss,
                                       key_front=float(light.get("key_front", 0.0)), key_spec=light.get("key_spec"))
    PA = warp(np.dstack([F * A[..., None], A]).astype(np.float32))
    soften = cfg.get("soften_px", 0.6) * (k if k > 1 else 1)
    if soften:
        PA = cv2.GaussianBlur(PA, (0, 0), soften)
    Aw = np.clip(PA[..., 3], 0, 1)
    Fw = np.where(Aw[..., None] > 1e-4, PA[..., :3] / np.maximum(Aw[..., None], 1e-4), 0)
    src_px_per_mm = s / scale

    # only the front is worn: the drawing's front outline cuts what the product shot shows past it
    # (F03's temples, opened and seen from above, stood up over the brows like horns; the tent seen soft
    # beside an end piece, or under the bridge, lay over the skin as a grey film). The outline is placed
    # as the lens openings are, then fitted to the photographed front (an affine fit of the two shapes:
    # the product shot sees a rim's top face from a little above, so its outline sits up to 2 mm higher
    # than the drawing's round the same lens openings, and cut there, the rim lost its top edge), and
    # given a millimetre of slack, so the photograph's own edge stays (its dark edge: see below).
    D = np.diag([np.cos(yaw) * s / ppm, s / ppm]).astype(np.float32)
    Ma = np.hstack([Rm @ D, (Rm @ (-D @ origin_px + np.array([0, drop * s], np.float32)) + anchor)[:, None]])
    sil = cv2.warpAffine(silhouette.astype(np.float32), Ma.astype(np.float32), (W, H), flags=cv2.INTER_LINEAR)
    sil, fit, report["outline_fit"] = fit_outline(sil, Aw, s)
    # the cut itself is drawn at four times the size in a box round the frame and brought down by area,
    # so its edge is as smooth as the photograph's (drawn at the face's size and thresholded, it left a
    # stepped edge where the frame is small, a runway shot's 1.3 px to the mm)
    ys, xs = np.nonzero(Aw > 0.02)
    mg = int(4 * s) + 2
    y0r, y1r, x0r, x1r = max(0, ys.min() - mg), min(H, ys.max() + mg), max(0, xs.min() - mg), min(W, xs.max() + mg)
    SS = 4
    to_face = np.diag([1 / SS, 1 / SS, 1.0]); to_face[:2, 2] = [x0r, y0r]   # box pixel at 4x -> face pixel
    M3 = np.vstack([Ma, [0, 0, 1]])
    to_draw = np.linalg.inv(M3) @ fit @ to_face                               # box pixel at 4x -> drawing pixel
    hi = cv2.warpAffine(silhouette.astype(np.float32), to_draw[:2].astype(np.float32), ((x1r - x0r) * SS, (y1r - y0r) * SS),
                        flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP) > 0.5
    slack = cfg.get("outline_slack_mm", 1.0) * s * SS
    inner_hi = hi
    hi = cv2.dilate(hi.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(slack) + 1,) * 2)) > 0
    # where the product camera saw an end piece's side face (the shot's settings say so: wear.side_face,
    # in mm from the front's outer edge), what is pale and uncolored along that edge is the side face,
    # not the front (the outline's fit takes it in, and it stayed as a pale line along F03's end piece);
    # elsewhere the edge keeps everything, gloss highlights included
    side = scfg.get("wear", {}).get("side_face")
    if side:
        up = lambda a: cv2.resize(a[y0r:y1r, x0r:x1r], ((x1r - x0r) * SS, (y1r - y0r) * SS), interpolation=cv2.INTER_LINEAR)
        Fh, Ah = up(Fw), up(Aw)
        front_lum = float(np.median(lum(Fh[(Ah > 0.9) & inner_hi])))
        grey = (Fh.max(-1) - Fh.min(-1)) < 0.35 * Fh.max(-1)
        filled = ndi.binary_fill_holes(Ah > 0.5)
        edge = cv2.distanceTransform(filled.astype(np.uint8), cv2.DIST_L2, 5) < float(side) * s * SS
        pale = edge & (lum(Fh) >= max(0.06, 3 * front_lum)) & grey & (Ah > 0.02)
        hi &= ~cv2.dilate(pale.astype(np.uint8), np.ones((3 * SS, 3 * SS), np.uint8)).astype(bool)
        report["side_face_px"] = int(pale.sum() / SS ** 2)
        del Fh, Ah
    sil = np.zeros((H, W), np.float32)
    sil[y0r:y1r, x0r:x1r] = cv2.resize(hi.astype(np.float32), (x1r - x0r, y1r - y0r), interpolation=cv2.INTER_AREA)
    sil = np.clip(cv2.GaussianBlur(sil, (0, 0), 0.15 * s), 0, 1)
    report["outside_outline"] = round(float((Aw * (1 - sil)).sum() / max(Aw.sum(), 1)), 4)
    Aw = Aw * sil
    report["frame_width_px"] = round(float(np.ptp(np.nonzero(Aw > 0.5)[1])), 1)

    # what stays in front of the frame (a strand of hair across an end piece), from the settings
    front = polygon_mask((H, W), cfg["in_front"], k, 1.0 * k) if cfg.get("in_front") else np.zeros((H, W), np.float32)
    Aw = Aw * (1 - front)

    # lens layer on the face: each lens's own tint, flat, nothing that was behind it in the product shot.
    # The lens runs on under the rim, its edge set in the rim's groove. SAM's mask stops a few pixels
    # short of the rim's solid part, and the face showed there untinted, a light ring inside the rim;
    # so a lens covers what the cleaned shot's lens layer covers (clean_lightbox runs the lens up to the
    # solid rim: under a partly see-through rim edge it is lens, not tent), grows on through the rim's
    # soft inner edge (some frame, not yet solid) up to the solid rim, never out past the frame, then on
    # under the solid rim, as far as the frame's softening on the face reaches (3 px under it, the
    # softened rim still let 5% of the bare face through: a hairline inside the rim) and no further than
    # the solid rim goes.
    tints, lens_on_face, grown = [], [], []
    reach = max(2, int(round(cfg.get("lens_under_rim_mm", 1.5) * src_px_per_mm)))
    soft_edge = (A > 0.02) & (A < 0.9)
    solid = A >= 0.9
    # share of the light on the eyes that comes round the frame rather than through the lens: little,
    # with a big front close to the face and the light in front (at 0.35 the eyes showed through a 4%
    # lens like a grey film; through real dark lenses they are all but gone)
    fill = cfg.get("eye_fill", 0.1)
    under = int(np.ceil(max(3.0, (3 * soften + 2) / scale)))
    report["lens_under_solid_px"] = under
    lab_t, _ = ndi.label((lum(T) < 0.995) | np.any(lens_src, axis=0))
    # the lens's tint pixel by pixel, as the cleaned shot has it: F06's and F08's lenses are gradients,
    # dark at the top (one flat tint drew them as plain lenses), and every lens keeps the photograph's
    # grain, which a flat fill lost (it read as painted). A light lens that keeps what was behind it in
    # the shot (F01's and F03's: a temple seen through) is its own tint, flat: the temple isn't behind it
    # on a face.
    keep_behind = scfg.get("lens_cleanup", {}).get("keep_behind")
    Tsrc = np.ones_like(T)
    for m in lens_src:
        er = cv2.erode(m.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
        vals = T[er]
        keep = lum(vals) > 0.5 * np.median(lum(vals))
        tint = np.median(vals[keep], axis=0)
        tints.append([round(float(v), 4) for v in tint])
        ids = np.unique(lab_t[m])
        g = np.isin(lab_t, ids[ids > 0]) | m
        g = ndi.binary_dilation(g, iterations=reach, mask=g | soft_edge)
        g = ndi.binary_dilation(g, iterations=under, mask=g | solid)
        grown.append(int(g.sum() - m.sum()))
        gy_, gx_ = np.nonzero(g)
        by0, by1, bx0, bx1 = gy_.min(), gy_.max() + 1, gx_.min(), gx_.max() + 1
        if keep_behind:
            tmap = np.broadcast_to(tint, (by1 - by0, bx1 - bx0, 3))
        else:
            own = ((lum(T) < 0.995) & m)[by0:by1, bx0:bx1]        # the lens's own pixels, carried out under the rim
            iy, ix = ndi.distance_transform_edt(~own, return_distances=False, return_indices=True)
            tmap = T[by0:by1, bx0:bx1][iy, ix]
        Tsrc[by0:by1, bx0:bx1] = np.where(g[by0:by1, bx0:bx1, None], tmap, Tsrc[by0:by1, bx0:bx1])
        mw = np.clip(warp(cv2.GaussianBlur(g.astype(np.float32), (0, 0), 1.0)), 0, 1) * (1 - front)
        lens_on_face.append(mw)
    report["lens_tint_rgb"] = tints
    report["lens_grown_px"] = grown
    lens_cov = np.clip(np.sum(lens_on_face, 0), 0, 1)
    Tw = np.clip(cv2.warpPerspective(small(Tsrc), Hs, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                                     borderValue=(1.0, 1.0, 1.0)), 0, 1)
    Tface_single = 1 - lens_cov[..., None] * (1 - Tw)               # one pass: what the lens's shadow lets by
    Tface = Tface_single * (fill + (1 - fill) * Tface_single)        # there and back: what the camera sees of the eye

    # the frame lit like the scene. Color: the scene light's, from a patch that is neutral in the
    # scene (the backdrop, a white shirt, grey concrete), against the tent's. Level: the backdrop's
    # against the tent's where the backdrop is lit like the face, else set in the settings.
    full = load_srgb(ROOT / "work" / "originals" / f"{shot}.jpg")
    alpha = np.asarray(Image.open(po / "masks" / "alpha.png"), np.float32) / 255
    rg = srgb_to_lin(full[scfg["region"][1]:scfg["region"][3], scfg["region"][0]:scfg["region"][2]])
    far = cv2.distanceTransform((alpha < 0.02).astype(np.uint8), cv2.DIST_L2, 5) > 200
    tent = np.median(rg[far], axis=0)
    del full, rg
    neutral_box = light.get("neutral_box", cfg.get("backdrop_box"))
    neutral = box_median(lin, neutral_box, k) if neutral_box else tent
    light_lum = float(lum(neutral[None])[0])                       # a neutral surface in the scene's light
    color = (neutral / light_lum) / (tent / float(lum(tent[None])[0]))
    level_box = light.get("level_box", cfg.get("backdrop_box"))
    if "level" in light:
        level = float(light["level"])
    elif level_box:
        back = box_median(lin, level_box, k)
        level = float(np.clip(lum(back[None])[0] / lum(tent[None])[0], 0.85, 1.25))
    else:
        level = 1.0
    gain = color * level * cfg.get("light_gain", 1.0)
    Fw = Fw * gain
    report["light"] = {"tent_lin": [round(float(v), 3) for v in tent], "neutral_lin": [round(float(v), 3) for v in neutral],
                       "level": round(level, 3), "gain": [round(float(v), 3) for v in gain]}

    # the frame's shadow on the skin. What casts it: the frame, and each lens as far as it stops light.
    # Cast: away from the key light (90 degrees: straight down), as sharp as the light is small (a
    # flash's shadow is a thin hard line just under the rim; blurred wide, it read as a drop shadow).
    # Contact: a little darkening of the skin hugging the frame where it sits close (bridge, end
    # pieces). Not behind the lens itself, whose shading is in the lens layer.
    stop = 1 - lum(Tface_single)
    caster = Aw + (1 - Aw) * lens_cov * stop
    sh = cfg.get("shadow", {})
    ang = np.radians(sh.get("dir_deg", 90.0 if key_from is None else key_from + 180.0))
    off = sh.get("offset_mm", 1.0) * s
    Ms = np.float32([[1, 0, off * np.cos(ang)], [0, 1, off * np.sin(ang)]])
    cast = cv2.GaussianBlur(cv2.warpAffine(caster, Ms, (W, H)), (0, 0), max(sh.get("blur_mm", 0.4) * s, 0.5))
    contact = cv2.GaussianBlur(caster, (0, 0), sh.get("contact_mm", 0.8) * s)
    shade = 1 - (1 - sh.get("strength", 0.5) * cast) * (1 - sh.get("contact", 0.2) * contact)
    face_lin = lin * (1 - shade * (1 - lens_cov))[..., None]

    # the lens's front surface mirrors what is in front of the face, as glass does (about 4.5% at
    # normal incidence): the room, lighter at the top than at the bottom. Through a dark lens this
    # reflection, not the eye, is what the camera sees. A reflection of the key itself can be set
    # (`reflection.key`: where on the lens, how big, how bright), but none is drawn by default: a
    # drawn catchlight, a soft glow or a soft band all read as painted on.
    rf = cfg.get("reflection", {})
    F0 = rf.get("reflectance", 0.045)
    front_env = rf.get("front_env", 0.3) * light_lum                # the room in front of the face
    refl = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    key = rf.get("key")                     # none by default: drawn catchlights and glows read as painted on
    for i, (m, mw) in enumerate(zip(lens_src, lens_on_face)):
        ys, xs = np.nonzero(m)
        top = cv2.perspectiveTransform(np.float32([[[xs.mean(), ys.min()]], [[xs.mean(), ys.max()]]]), Hm)[:, 0, 1]
        v = np.clip((yy - top[0]) / max(top[1] - top[0], 1), 0, 1)
        refl += F0 * front_env * mw * (1 - rf.get("gradient", 0.65) * v)
        if key:
            at = key.get("at", [0.5, 0.3])
            fx = at[0] if (i == 0 or not key.get("mirror", True)) else 1 - at[0]
            cx, cy = xs.min() + fx * np.ptp(xs), ys.min() + at[1] * np.ptp(ys)
            p = cv2.perspectiveTransform(np.float32([[[cx, cy]]]), Hm)[0, 0]
            rad = max(key.get("size", 0.05) * np.ptp(xs) * scale, 1.0)
            spot = np.exp(-(((xx - p[0]) / (key.get("aspect", 1.3) * rad)) ** 2 + ((yy - p[1]) / rad) ** 2) ** key.get("hardness", 1.0))
            refl += key.get("peak", 1.0) * light_lum * mw * spot
    sheen = refl[..., None] * (neutral / light_lum)
    report["lens_reflection"] = {"F0": F0, "front_env": round(front_env, 3), "key": key}

    # what the camera sees through the lens: the face behind it, darkened twice by the tint, its finest
    # detail lost in that little light (rendered sharp, lashes and irises read as a grey film laid over
    # the eyes), plus the reflection above; mixed with the lens as photographed in the product shot,
    # the bright stage seen through it (`lens.photo`, 0 to 1), whose look is a real lens's
    ln = cfg.get("lens", {})
    soft = cv2.GaussianBlur(face_lin, (0, 0), ln.get("face_blur_mm", 1.0) * s)
    seen = face_lin * (1 - lens_cov[..., None]) + soft * lens_cov[..., None]
    photo = float(ln.get("photo", 0.0))
    stage_rgb = hex_lin(STAGE_HEX) * gain * surround
    inside = (1 - photo) * seen * Tface + photo * (Tw * stage_rgb)
    under = face_lin * (1 - lens_cov[..., None]) + inside * lens_cov[..., None] + sheen
    comp = Fw * Aw[..., None] + (1 - Aw[..., None]) * under
    report["lens"] = {"photo": photo, "face_blur_mm": ln.get("face_blur_mm", 1.0), "fill": fill}
    if DEBUG:
        ys, xs = np.nonzero(Aw > 0.02)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        np.savez_compressed(out / "debug.npz", origin=np.array([x0, y0]), Aw=Aw[y0:y1, x0:x1], Fw=Fw[y0:y1, x0:x1],
                            Tface=Tface[y0:y1, x0:x1], lens=np.sum(lens_on_face, 0)[y0:y1, x0:x1],
                            face=face_lin[y0:y1, x0:x1], comp=comp[y0:y1, x0:x1], sil=sil[y0:y1, x0:x1],
                            Aw_full=np.clip(PA[..., 3], 0, 1)[y0:y1, x0:x1])
    grade = cfg.get("grade", True)
    size = H / 1280
    gk = grade if isinstance(grade, dict) else {}
    final = ss90(lin_to_srgb(comp), size=size, **gk) if grade else lin_to_srgb(comp)
    before = ss90(person, size=size, **gk) if grade else person

    # the crop, in the generated portrait's pixels: a 3:4 portrait is cut to the gallery's 4:5, a quarter of
    # what goes from the top and the rest from the bottom (the head sits in the upper half)
    crop = cfg.get("crop")
    if not crop and cfg.get("format") == "4:5":
        w0, h0 = W // k, H // k
        if h0 > round(w0 * 5 / 4):
            th = round(w0 * 5 / 4)
            top = round(0.25 * (h0 - th))
            crop = [0, top, w0, top + th]
    if crop:
        x0, y0, x1, y1 = [int(round(v * k)) for v in crop]
        final, before = final[y0:y1, x0:x1], before[y0:y1, x0:x1]
        report["crop"] = [x0, y0, x1, y1]
    fy, fx = np.nonzero(Aw > 0.5)
    ox, oy = report.get("crop", [0, 0])[:2]
    report["frame_box"] = [int(fx.min() - ox), int(fy.min() - oy), int(fx.max() - ox), int(fy.max() - oy)]
    cv2.imwrite(str(out / "composite.png"), cv2.cvtColor((final * 65535 + 0.5).astype(np.uint16), cv2.COLOR_RGB2BGR))
    Image.fromarray((final * 255 + 0.5).astype(np.uint8)).save(out / "composite.jpg", quality=94)
    hh = 1280
    ww = int(round(final.shape[1] * hh / final.shape[0]))
    sheet = np.hstack([cv2.resize(before, (ww, hh), interpolation=cv2.INTER_AREA), np.ones((hh, 16, 3), np.float32),
                       cv2.resize(final, (ww, hh), interpolation=cv2.INTER_AREA)])
    Image.fromarray((sheet * 255 + 0.5).astype(np.uint8)).save(out / "compare.jpg", quality=90)
    # the frame at 1:1, with a margin
    ys, xs = np.nonzero(Aw > 0.05)
    oy, ox = report.get("crop", [0, 0])[1], report.get("crop", [0, 0])[0]
    pad = int(0.25 * np.ptp(xs))
    z = final[max(0, ys.min() - pad - oy):ys.max() + pad - oy, max(0, xs.min() - pad - ox):xs.max() + pad - ox]
    Image.fromarray((z * 255 + 0.5).astype(np.uint8)).save(out / "zoom.jpg", quality=94)
    (out / "report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a not in ("--debug", "--fast")]
    for p in (sorted(PEOPLE.glob("*.json")) if args == ["--all"] else args):
        main(p)
