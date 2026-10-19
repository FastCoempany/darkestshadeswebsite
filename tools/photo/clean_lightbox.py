#!/usr/bin/env python3
"""Clean one lightbox shot into a catalog image and a cut-out (docs/brief/07-photography.md, track 1).

    python3 tools/photo/clean_lightbox.py content/photography/shots/IMG_3596.json [--debug]

Reads the original from work/originals/ (tools/photo/zipget.py), writes work/out/<shot>/:
    stage.jpg            the frame on the uniform stage color, 4:5 (or the shot's own box), 2000 wide
    stage-full.png       same, at the shot's working resolution (16-bit)
    cutout.png           one-file RGBA: rims and temples opaque, lenses see-through
    layers/frame.png     exact layers for compositing on anything (people, other stages):
    layers/lens.png        multiply the background by shadow.png and lens.png (the lenses'
    layers/shadow.png      measured color transmission), then frame.png on top
    compare.jpg          before / after, for review
    report.json          what was done, with numbers
    debug/               intermediate masks, with --debug

Steps: segment (ISNet via rembg; SAM point prompts per lens) -> model the tent background (smooth
polynomial fit in linear light) -> shadow layer -> see-through lenses (per-channel transmission =
image / background, cleaned of ring-light reflections and dust) -> remove the old marks (per-shot
polygons, rebuilt along the temple) -> place the GCD (Blender render lit like the tent, warped onto
the temple from measured anchors) -> re-stage on #E4E2DD -> frame.
"""
import json
import pathlib
import sys

import cv2
import numpy as np
from PIL import Image, ImageCms, ImageOps

ROOT = pathlib.Path(__file__).resolve().parents[2]
STAGE_HEX = "#E4E2DD"


# ---------- color ----------
def srgb_to_lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def lum(x):
    return 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]


def hex_lin(h):
    h = h.lstrip("#")
    return srgb_to_lin(np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32))


def load_srgb(path):
    """Oriented, converted from the embedded profile (iPhone: Display P3) to sRGB, float32 0..1."""
    im = ImageOps.exif_transpose(Image.open(path))
    icc = im.info.get("icc_profile")
    if icc:
        src = ImageCms.ImageCmsProfile(__import__("io").BytesIO(icc))
        dst = ImageCms.createProfile("sRGB")
        im = ImageCms.profileToProfile(im.convert("RGB"), src, dst, outputMode="RGB")
    return np.asarray(im.convert("RGB"), np.float32) / 255.0


# ---------- segmentation ----------
# Each model runs in its own process and caches its mask as a PNG: ISNet and SAM together need
# more memory than this workspace gives one process.
def _region_rgb(cfg):
    full = load_srgb(ROOT / "work" / "originals" / f"{cfg['shot']}.jpg")
    x0, y0, x1, y1 = cfg["region"]
    return full[y0:y1, x0:x1]


def mask_job(cfg_path, kind, index=None):
    from rembg import new_session, remove
    cfg = json.loads(pathlib.Path(cfg_path).read_text())
    masks = ROOT / "work" / "out" / cfg["shot"] / "masks"
    masks.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray((_region_rgb(cfg) * 255).astype(np.uint8))
    if kind == "isnet":
        m = remove(img, session=new_session("isnet-general-use"), only_mask=True)
        m.save(masks / "alpha.png")
    else:  # SAM, point prompts for one lens
        x0, y0 = cfg["region"][:2]
        pts = [{"type": "point", "data": [x - x0, y - y0], "label": 1} for x, y in cfg["lenses"][index]["points"]]
        m = remove(img, session=new_session("sam"), only_mask=True, sam_prompt=pts)
        m.save(masks / f"lens-{index}.png")


def masks_for(cfg_path, cfg):
    import subprocess
    masks = ROOT / "work" / "out" / cfg["shot"] / "masks"
    jobs = [("isnet", None, masks / "alpha.png")]
    jobs += [("sam", i, masks / f"lens-{i}.png") for i in range(len(cfg.get("lenses", [])))]
    for kind, i, path in jobs:
        if not path.exists():
            args = [sys.executable, __file__, "--mask", kind, str(cfg_path)] + ([str(i)] if i is not None else [])
            subprocess.run(args, check=True)
    alpha = np.asarray(Image.open(masks / "alpha.png"), np.float32) / 255.0
    from scipy import ndimage as ndi
    lens = np.zeros(alpha.shape, bool)
    for i in range(len(cfg.get("lenses", []))):
        # a lens has no holes: what SAM leaves out inside it is something seen through it
        lens |= ndi.binary_fill_holes(np.asarray(Image.open(masks / f"lens-{i}.png")) > 128)
    return alpha, lens


# ---------- background ----------
def fit_background(lin, alpha, dist_px=160, degree=3):
    """Smooth model of the tent (unshadowed) in linear light: robust 2D polynomial per channel,
    fitted on pixels well away from the frame and its shadow."""
    h, w = alpha.shape
    obj = (alpha > 0.02).astype(np.uint8)
    far = cv2.distanceTransform(1 - obj, cv2.DIST_L2, 5) > dist_px
    ys, xs = np.nonzero(far[::4, ::4])
    ys, xs = ys * 4, xs * 4
    u, v = xs / w * 2 - 1, ys / h * 2 - 1
    terms = [u ** i * v ** j for i in range(degree + 1) for j in range(degree + 1 - i)]
    A = np.stack(terms, 1)
    U, V = np.meshgrid(np.linspace(-1, 1, w, dtype=np.float32), np.linspace(-1, 1, h, dtype=np.float32))
    full_terms = [U ** i * V ** j for i in range(degree + 1) for j in range(degree + 1 - i)]
    B = np.zeros_like(lin)
    for c in range(3):
        y = lin[ys, xs, c]
        keep = np.ones_like(y, bool)
        for _ in range(3):  # drop shadows and dust: keep pixels at or above the fit
            coef, *_ = np.linalg.lstsq(A[keep], y[keep], rcond=None)
            r = y - A @ coef
            keep = r > -1.5 * r[keep].std()
        B[..., c] = sum(cf * t for cf, t in zip(coef, full_terms))
    return np.clip(B, 1e-4, None)


def shadow_zone(obj, reach=600, side=150, soft=40):
    """Where the frame's own shadow can fall in this tent: below the frame in the picture (light from
    above, camera looking down) and a little to either side. Anything darker elsewhere (the sweep's
    horizon behind the frame) is tent, not shadow. Weight 0..1, soft at the sides only: it starts
    inside the frame, so it never bleeds above it."""
    h, w = obj.shape
    last = np.full(w, -10 ** 6, np.int64)
    zone = np.zeros((h, w), bool)
    for y in range(h):
        last = np.where(obj[y], y, last)
        d = y - last
        zone[y] = (d > 0) & (d <= reach)
    zone = cv2.dilate(zone.astype(np.uint8), np.ones((1, 2 * side + 1), np.uint8)).astype(np.float32)
    return cv2.GaussianBlur(zone, (0, 1), sigmaX=soft, sigmaY=0.1) if soft else zone


def smooth_fill(ch, mask, support, degree=2):
    """Values for `mask` from a robust low-order surface fitted on `support` (a lens is smooth)."""
    ys, xs = np.nonzero(support)
    step = max(1, len(xs) // 40000)
    ys, xs = ys[::step], xs[::step]
    h, w = ch.shape
    u, v = xs / w * 2 - 1, ys / h * 2 - 1
    terms = lambda U, V: [U ** i * V ** j for i in range(degree + 1) for j in range(degree + 1 - i)]
    A = np.stack(terms(u, v), 1)
    y = ch[ys, xs]
    keep = np.ones_like(y, bool)
    for _ in range(3):
        coef, *_ = np.linalg.lstsq(A[keep], y[keep], rcond=None)
        r = y - A @ coef
        keep = np.abs(r) < 2.5 * r[keep].std() + 1e-6
    my, mx = np.nonzero(mask)
    out = ch.copy()
    out[my, mx] = np.stack(terms(mx / w * 2 - 1, my / h * 2 - 1), 1) @ coef
    return out


def lowres_inpaint(img, mask, scale=4, radius=12):
    """Fill `mask` from its surroundings at low resolution (smooth fields: shadow, transmission)."""
    h, w = mask.shape
    small = cv2.resize(img, (w // scale, h // scale), interpolation=cv2.INTER_AREA)
    m = cv2.resize(mask.astype(np.uint8), (w // scale, h // scale), interpolation=cv2.INTER_NEAREST)
    s16 = np.clip(small * 65535 / 2, 0, 65535).astype(np.uint16)
    filled = cv2.inpaint(s16, m, radius, cv2.INPAINT_TELEA).astype(np.float32) * 2 / 65535
    up = cv2.resize(filled, (w, h), interpolation=cv2.INTER_CUBIC)
    return np.where(mask, up, img)


# ---------- old marks ----------
def remove_marks(srgb, marks, region_xy):
    out = (srgb * 255).astype(np.uint8)
    L = cv2.cvtColor(out, cv2.COLOR_RGB2GRAY)
    total = np.zeros(L.shape, np.uint8)
    report_mask = np.zeros(L.shape, np.uint8)
    for mk in marks:
        poly = np.array([[x - region_xy[0], y - region_xy[1]] for x, y in mk["poly"]], np.int32)
        area = np.zeros_like(L)
        cv2.fillPoly(area, [poly], 1)
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (mk.get("stroke_px", 15),) * 2)
        if mk.get("kind", "dark") == "dark":
            hat = cv2.morphologyEx(L, cv2.MORPH_BLACKHAT, k)
        else:
            hat = cv2.morphologyEx(L, cv2.MORPH_TOPHAT, k)
        strokes = ((hat > mk.get("threshold", 10)) & (area > 0)).astype(np.uint8)
        if mk.get("fill_whole"):
            strokes = area.copy()
        strokes = cv2.dilate(strokes, np.ones((5, 5), np.uint8), iterations=1)
        report_mask |= strokes
        if not strokes.any():
            continue
        if mk.get("temple"):
            out = fill_along_temple(out, strokes, mk["temple"], region_xy)
        elif mk.get("axis") is not None:
            out = inpaint_along(out, strokes, mk["axis"])
        else:
            total |= strokes          # small marks: plain inpainting, all at once below
    if total.any():
        out = cv2.inpaint(out, total, 6, cv2.INPAINT_NS)
        noise = np.random.default_rng(3).normal(0, 1.4, out.shape)   # grain back, as along the temples
        out = np.where(total[..., None] > 0, np.clip(out + noise, 0, 255), out).astype(np.uint8)
    return out.astype(np.float32) / 255.0, report_mask


def fill_along_temple(img, mask, temple, region_xy, grain=1.4, seed=11):
    """Rebuild a patch of temple face line by line. The face is rectified between its measured top
    and bottom edges (y = a*x + b, original-image coordinates), so every row follows the acetate,
    core wire and bevel stripes exactly; masked runs are interpolated from both ends of the row."""
    ox, oy = region_xy
    (at, bt), (ab, bb) = temple["top"], temple["bottom"]
    ys, xs = np.nonzero(mask)
    pad = 60
    xa, xb = max(0, xs.min() - pad), min(img.shape[1] - 1, xs.max() + pad)
    U = np.arange(xa, xb + 1, dtype=np.float32)
    top = at * (U + ox) + bt - oy
    bot = ab * (U + ox) + bb - oy
    nv = int(np.ceil((bot - top).max())) + 1
    V = np.linspace(0, 1, nv, dtype=np.float32)
    map_x = np.repeat(U[None, :], nv, 0).astype(np.float32)
    map_y = (top[None, :] + V[:, None] * (bot - top)[None, :]).astype(np.float32)
    R = cv2.remap(img.astype(np.float32), map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Rm = cv2.remap(mask.astype(np.float32), map_x, map_y, cv2.INTER_LINEAR) > 0.3
    for r in range(nv):
        row = Rm[r]
        if not row.any() or (~row).sum() < 2:
            continue
        good = np.nonzero(~row)[0]
        bad = np.nonzero(row)[0]
        for ch in range(R.shape[2]):
            R[r, bad, ch] = np.interp(bad, good, R[r, good, ch])
    R += np.random.default_rng(seed).normal(0, grain, R.shape).astype(np.float32)
    # back to image space, only inside the mask (feathered)
    yy, xx = np.mgrid[0:img.shape[0], xa:xb + 1].astype(np.float32)
    t = at * (xx + ox) + bt - oy
    b_ = ab * (xx + ox) + bb - oy
    v = ((yy - t) / np.maximum(b_ - t, 1) * (nv - 1)).astype(np.float32)
    u = (xx - xa).astype(np.float32)
    back = cv2.remap(R, u, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    mm = cv2.GaussianBlur(mask[:, xa:xb + 1].astype(np.float32), (0, 0), 1.2)[..., None]
    seg = img[:, xa:xb + 1].astype(np.float32)
    img[:, xa:xb + 1] = np.clip(seg * (1 - mm) + back * mm, 0, 255).astype(np.uint8)
    return img


def inpaint_along(img, mask, axis, grain=1.6, seed=7):
    """Fill `mask` by interpolating along a direction (a temple's length): the stripes of acetate,
    core wire and bevel run along the temple, so each line parallel to it is rebuilt from its own
    two ends. Film grain is added back so the fill doesn't look painted."""
    ys, xs = np.nonzero(mask)
    pad = 40
    x0, x1 = max(0, xs.min() - pad), min(img.shape[1], xs.max() + pad)
    y0, y1 = max(0, ys.min() - pad), min(img.shape[0], ys.max() + pad)
    patch = img[y0:y1, x0:x1].astype(np.float32)
    m = mask[y0:y1, x0:x1].astype(np.uint8)
    ang = np.degrees(np.arctan2(axis[1], axis[0]))
    h, w = m.shape
    c = (w / 2, h / 2)
    R = cv2.getRotationMatrix2D(c, ang, 1.0)          # rotate so the temple runs horizontally
    cos, sin = abs(R[0, 0]), abs(R[0, 1])
    W2, H2 = int(h * sin + w * cos) + 2, int(h * cos + w * sin) + 2
    R[0, 2] += W2 / 2 - c[0]
    R[1, 2] += H2 / 2 - c[1]
    pr = cv2.warpAffine(patch, R, (W2, H2), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    mr = cv2.warpAffine(m, R, (W2, H2), flags=cv2.INTER_NEAREST) > 0
    valid = cv2.warpAffine(np.ones_like(m), R, (W2, H2), flags=cv2.INTER_NEAREST) > 0
    filled = pr.copy()
    for yy in range(H2):
        row_m = mr[yy]
        if not row_m.any():
            continue
        good = valid[yy] & ~row_m
        if good.sum() < 2:
            continue
        xi = np.nonzero(good)[0]
        for ch in range(pr.shape[2]):
            filled[yy, row_m, ch] = np.interp(np.nonzero(row_m)[0], xi, pr[yy, good, ch])
    Rinv = cv2.invertAffineTransform(R)
    back = cv2.warpAffine(filled, Rinv, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    rng = np.random.default_rng(seed)
    back += rng.normal(0, grain, back.shape).astype(np.float32)
    mm = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0)[..., None]
    patch = patch * (1 - mm) + back * mm
    img[y0:y1, x0:x1] = np.clip(patch, 0, 255).astype(np.uint8)
    return img


# ---------- GCD ----------
def gcd_render(g):
    """The Blender render of the GCD for this placement (lightbox lighting, the temple's yaw), made
    on first use with tools/blender/gcd_render.py (needs bpy), with its 2D anchors beside it."""
    size = g.get("render_px", 1200)
    path = ROOT / "work" / "gcd" / f"gcd-3d-{g['view']}-lightbox-{size}.png"
    if not path.exists():
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "tools" / "blender" / "gcd_render.py"), "--light", "lightbox",
                        "--views", g["view"], "--size", str(size), "--samples", str(g.get("samples", 128)),
                        "--relief", str(g.get("relief_mm", 0.15)), "--anchors", "--out", str(path.parent)], check=True)
    return path


def place_gcd(F, A, cfg, region_xy, report):
    g = cfg["gcd"]
    path = gcd_render(g)
    render = np.asarray(Image.open(path).convert("RGBA"), np.float32) / 255.0
    anc = json.loads(path.with_suffix(".json").read_text())
    bx0, by0, bx1, by1 = anc["bbox_svg"]
    L = g["length_mm"]
    H = L * (by1 - by0) / (bx1 - bx0)
    keys = ["center", "left", "right", "top", "bottom"]
    src_pts = np.array([anc[k] for k in keys], np.float32)
    if "anchors_px" in g:
        # a placement in perspective, anchor by anchor (a wing seen at an angle and close up: its near
        # half looks bigger than its far half); the anchors come from an approved placement mapped
        # onto this shot through the face's own landmarks
        dst_pts = np.array([np.array(g["anchors_px"][k], np.float32) - region_xy for k in keys], np.float32)
        M, _ = cv2.findHomography(src_pts, dst_pts, 0)
        c = dst_pts[0]
        scale = float(np.linalg.norm(dst_pts[2] - dst_pts[1]) / np.linalg.norm(src_pts[2] - src_pts[1]))
        eu_len = float(np.linalg.norm(dst_pts[2] - dst_pts[1]) / L)
        ev_len = float(np.linalg.norm(dst_pts[4] - dst_pts[3]) / H)
    else:
        eu = np.array(g["axis"], np.float32)
        eu = eu / np.linalg.norm(eu) * g["px_per_mm_along"]  # px per mm along the face (away from the hinge on a temple)
        if "center" in g:
            # a placement measured directly (F02's wing on the frame front): center, axis, down, scale
            c = np.array(g["center"], np.float32) - region_xy
            ev = np.array(g["down"], np.float32)
            ev = ev / np.linalg.norm(ev) * g["px_per_mm_down"]
        else:
            # on a temple, from the hinge line with the logo-kit placement ratios
            T = g["temple_mm"]
            ht = np.array(g["hinge_top"], np.float32) - region_xy
            hb = np.array(g["hinge_bottom"], np.float32) - region_xy
            ev = (hb - ht) / T                       # px per mm down the temple face
            c = ht + ev * (0.39 * T) + eu * (0.82 * T)
        er = eu if eu[0] >= 0 else -eu               # the emblem reads left to right in the picture
        dst = {"center": c, "left": c - er * L / 2, "right": c + er * L / 2, "top": c - ev * H / 2, "bottom": c + ev * H / 2}
        dst_pts = np.array([dst[k] for k in keys], np.float32)
        M, _ = cv2.estimateAffine2D(src_pts, dst_pts, method=cv2.LMEDS)
        M = np.vstack([M, [0, 0, 1]]).astype(np.float32)
        scale = float(np.sqrt(abs(np.linalg.det(M[:2, :2]))))
        eu_len, ev_len = float(np.linalg.norm(eu)), float(np.linalg.norm(ev))
    # premultiply, pre-shrink to about twice the target size to avoid aliasing, then warp
    pre = min(1.0, 2.0 * scale)
    if pre < 1.0:
        render = cv2.resize(render, None, fx=pre, fy=pre, interpolation=cv2.INTER_AREA)
        M = M @ np.array([[1 / pre, 0, 0], [0, 1 / pre, 0], [0, 0, 1]], np.float32)
    rgb_lin = srgb_to_lin(render[..., :3]) * render[..., 3:4]
    h, w = A.shape
    warped = cv2.warpPerspective(np.dstack([rgb_lin, render[..., 3]]), M, (w, h), flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    ea = cv2.GaussianBlur(warped[..., 3], (0, 0), g.get("soften_px", 0.6))
    ec = cv2.GaussianBlur(warped[..., :3], (0, 0), g.get("soften_px", 0.6))   # premultiplied
    # contact shadow: a soft occlusion just outside the emblem's edge
    occl = cv2.GaussianBlur(ea, (0, 0), 2.5)
    shade = 1 - 0.35 * np.clip(occl - ea, 0, 1)
    # emblem over the temple, premultiplied, back to straight color
    P = ec + (F * A[..., None] * shade[..., None]) * (1 - ea[..., None])
    A[:] = ea + A * (1 - ea)
    F[:] = np.where(A[..., None] > 1e-4, P / np.maximum(A[..., None], 1e-4), 0)
    report["gcd"] = {"center_px": (c + region_xy).round(1).tolist(), "length_mm": L, "height_mm": round(H, 2),
                     "px_per_mm": {"along": round(eu_len, 2), "down": round(ev_len, 2)}}


# ---------- framing ----------
def frame_crop(alpha, aspect, fill, center_y):
    ys, xs = np.nonzero(alpha > 0.15)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    bw = x1 - x0
    W = int(bw / fill)
    Hh = int(W * aspect[1] / aspect[0])
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    left = int(round(cx - W / 2))
    top = int(round(cy - center_y * Hh))
    return left, top, W, Hh


def paste_canvas(img, left, top, W, H, fill_value):
    canvas = np.empty((H, W) + img.shape[2:], img.dtype)
    canvas[...] = fill_value
    sx0, sy0 = max(0, left), max(0, top)
    sx1, sy1 = min(img.shape[1], left + W), min(img.shape[0], top + H)
    canvas[sy0 - top:sy1 - top, sx0 - left:sx1 - left] = img[sy0:sy1, sx0:sx1]
    return canvas


def main(cfg_path):
    cfg_path = pathlib.Path(cfg_path).resolve()
    cfg = json.loads(pathlib.Path(cfg_path).read_text())
    shot = cfg["shot"]
    out = ROOT / "work" / "out" / shot
    out.mkdir(parents=True, exist_ok=True)
    report = {"shot": shot, "frame": cfg["frame"], "angle": cfg["angle"]}

    full = load_srgb(ROOT / "work" / "originals" / f"{shot}.jpg")
    x0, y0, x1, y1 = cfg["region"]
    rx = np.array([x0, y0], np.float32)
    srgb = full[y0:y1, x0:x1].copy()
    before = srgb.copy()

    alpha_m, lens = masks_for(cfg_path, cfg)
    lin = srgb_to_lin(srgb)
    B = fit_background(lin, np.maximum(alpha_m, lens.astype(np.float32)))

    # Lenses count as object even where the segmentation model calls them background (a
    # defocused far lens), or their darkness would be taken for shadow.
    solid = alpha_m > 0.9
    filled = cv2.morphologyEx(solid.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    from scipy import ndimage as ndi
    filled = ndi.binary_fill_holes(filled).astype(bool)
    obj = filled | (alpha_m > 0.02) | lens
    zone = shadow_zone(obj, **cfg.get("shadow_zone", {}))
    # The tent's own structure that the smooth fit misses (the sweep's horizon, light falloff):
    # measured right up to the frame wherever its shadow can't fall, carried under the frame and
    # its shadow zone, and made part of the background. Unmixing the frame's soft edges then
    # sees the true tent behind them.
    ratio = lum(lin) / lum(B)
    tent = ~(cv2.dilate(obj.astype(np.uint8), np.ones((17, 17), np.uint8)) > 0) & (zone < 0.5)
    if tent.any():
        C = lowres_inpaint(np.where(tent, np.clip(ratio, 0.3, 3), 1).astype(np.float32), ~tent)
        B = B * cv2.GaussianBlur(C, (0, 0), 6)[..., None]
    # shadow layer: how much darker than the tent each background pixel is
    ratio = lum(lin) / lum(B)
    far = cv2.distanceTransform((1 - obj).astype(np.uint8), cv2.DIST_L2, 5) > 300
    norm = float(np.median(ratio[far])) if far.any() else 1.0
    S = np.clip(ratio / norm, 0, 1.0)
    S = lowres_inpaint(S, cv2.dilate(obj.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0)
    S = cv2.GaussianBlur(S, (0, 0), 3)
    # keep only the frame's own shadow: fade S to 1 between 150 and 450 px from the frame, so the
    # stage is one even color everywhere else (no tent gradient, no seams at the crop edge)
    d = cv2.distanceTransform((1 - obj).astype(np.uint8), cv2.DIST_L2, 5)
    w = np.clip((450 - d) / 300, 0, 1) * zone
    hh, ww = S.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    edge = np.minimum.reduce([xx, yy, ww - 1 - xx, hh - 1 - yy]).astype(np.float32)
    w = w * np.clip(edge / 120.0, 0, 1)      # and to 1 at the region's border: no seam with the padding
    S = 1 - (1 - S) * w
    # Whatever is seen through a lens or a gap stays in its transmission (below), so the shadow
    # layer is 1 there; the frame itself hides the rest of the inpainted shadow.
    see = cv2.dilate((lens | (filled & ~solid)).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    S = np.where(see, 1.0, S).astype(np.float32)
    S = np.where(see | solid, cv2.GaussianBlur(S, (0, 0), 2), S).astype(np.float32)
    B = B * norm
    report["background_norm"] = round(norm, 3)

    # see-through: the lenses (SAM masks, kept just inside the rims) and any open gaps (bridge
    # keyhole, the space between brow and far temple). Each is a color filter: transmission per
    # channel = image / tent, so a yellow or blue lens keeps its color on the new stage.
    lens_in = cv2.erode(lens.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    holes = lens_in | (filled & ~solid)
    back = B * S[..., None]                          # the tent behind, in the frame's shadow
    Tc = np.clip(lin / (back + 1e-5), 0, 1).astype(np.float32)
    T = np.clip(lum(lin) / (lum(back) + 1e-5), 0, 1).astype(np.float32)
    # clean the lenses: ring-light reflections (bright spots) and dust (small dark specks)
    lc = cfg.get("lens_cleanup", {})
    T16 = (T * 65535).astype(np.uint16)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (lc.get("tophat_px", 31),) * 2)
    glare = cv2.morphologyEx(T16, cv2.MORPH_TOPHAT, k).astype(np.float32) / 65535 > lc.get("threshold", 0.05)
    # dust: a small dip, clearly deeper than the noise both in absolute and in relative terms
    # (near-black areas are all noise in relative terms)
    kd = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (lc.get("dust_px", 11),) * 2)
    Td16 = (cv2.GaussianBlur(T, (0, 0), 1.2) * 65535).astype(np.uint16)
    dip = cv2.morphologyEx(Td16, cv2.MORPH_BLACKHAT, kd).astype(np.float32) / 65535
    dust = (dip > lc.get("dust_min", 0.006)) & \
        (dip / (cv2.GaussianBlur(T, (0, 0), 8) + 1e-3) > lc.get("dust_threshold", 0.12))
    spots = cv2.dilate(((glare | dust) & holes).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    if spots.any():
        for c in range(3):
            ch = (Tc[..., c] * 65535).astype(np.uint16)
            Tc[..., c] = cv2.inpaint(ch, spots.astype(np.uint8), 5, cv2.INPAINT_TELEA).astype(np.float32) / 65535
    # reflections too big to detect (a striped light panel mirrored in the lens): per-shot polygons,
    # refilled as the smooth field a clean lens is, with the lens's own grain put back
    paint = np.zeros(T.shape, np.uint8)
    for poly in lc.get("paint", []):
        cv2.fillPoly(paint, [np.array([[x - x0, y - y0] for x, y in poly], np.int32)], 1)
    paint = (cv2.dilate(paint, np.ones((9, 9), np.uint8)) > 0) & holes
    if paint.any():
        # fitted only on clean lens around the patch, so the rim's color never bleeds in
        support = (cv2.dilate(paint.astype(np.uint8), np.ones((301, 301), np.uint8)) > 0) & lens_in & ~paint & ~spots
        ring = (cv2.dilate(paint.astype(np.uint8), np.ones((41, 41), np.uint8)) > 0) & ~paint & lens_in
        rng = np.random.default_rng(5)
        for c in range(3):
            ch = Tc[..., c]
            grain = float(np.std((ch - cv2.GaussianBlur(ch, (0, 0), 2))[ring])) if ring.any() else 0.0
            fill = smooth_fill(ch, paint, support)
            Tc[..., c] = np.where(paint, fill + rng.normal(0, grain, ch.shape).astype(np.float32), ch)
        spots |= paint
    # A lens on an even stage shows its own tint, not the tent's horizon seen through it (front
    # views look straight through to where the floor meets the back wall): "flat" gives each lens
    # one tint, "gradient" a smooth fit for gradient lenses, each with the lens's own grain. What
    # sat behind the lens goes too (in a front view, the temples): kept, it came out in fragments.
    mode = lc.get("smooth")
    if mode:
        deg = 0 if mode == "flat" else 2
        lab, nl = ndi.label(lens_in)
        rng2 = np.random.default_rng(9)
        for i in range(1, nl + 1):
            li = lab == i
            if li.sum() < 2000:
                continue
            fitimg = Tc.copy()
            for c in range(3):
                fitimg[..., c] = smooth_fill(Tc[..., c], li, li & ~spots, degree=deg)
            grain = float(np.std((Tc - cv2.GaussianBlur(Tc, (0, 0), 2))[li & ~spots]))
            new = fitimg + rng2.normal(0, grain, Tc.shape).astype(np.float32)
            Tc[li] = new[li]
    report["lens"] = {"hole_px": int(holes.sum()), "cleaned_px": int(spots.sum()),
                      "dust_px": int((dust & holes).sum()),
                      "transmission_median_rgb": [round(float(np.median(Tc[..., c][holes])), 3) for c in range(3)] if holes.any() else None}

    # remove the old marks, then unmix the opaque parts from the tent behind their soft edges
    srgb_clean, mark_mask = remove_marks(srgb, cfg.get("marks", []), rx)
    report["marks_px"] = int(mark_mask.sum())
    lin_clean = srgb_to_lin(srgb_clean)
    # Opacity from physics as well as from the model: a pixel much darker than the tent behind it
    # is mostly frame, whatever the model thinks (defocused rims get soft model alphas). Highlights
    # on the acetate keep the model's alpha.
    T_all = np.clip(lum(lin_clean) / (lum(back) + 1e-5), 0, 1)
    near = cv2.dilate((alpha_m > 0.05).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
    dark = (1 - T_all) > 0.4                          # clearly darker than the tent: frame or lens
    lab, n = ndi.label(dark)
    if n:
        hit = np.unique(lab[(alpha_m > 0.5) & dark])
        near |= np.isin(lab, hit[hit > 0])
    # Two layers: the opaque frame (F, A) and the see-through filter (Tf, multiplies what's behind)
    t0 = 0.05                                         # darkening within the tent model's noise
    A_phys = np.clip((1 - T_all - t0) / (1 - t0), 0, 1)
    A = np.where(near, np.maximum(alpha_m, A_phys), alpha_m).astype(np.float32)
    A[holes] = 0.0
    rim = solid & ~holes
    A[rim] = np.maximum(A[rim], 0.995)
    F = np.where(A[..., None] > 0.02, (lin_clean - (1 - A[..., None]) * back) / np.maximum(A[..., None], 0.02), 0)
    F = np.clip(F, 0, 1).astype(np.float32)
    Tf = np.ones_like(lin, dtype=np.float32)
    Tf[holes] = Tc[holes]

    if cfg.get("gcd"):
        place_gcd(F, A, cfg, rx, report)

    # re-stage on the uniform stage color, keeping the frame's own contact shadow
    stage = hex_lin(STAGE_HEX)
    comp = F * A[..., None] + stage * S[..., None] * Tf * (1 - A[..., None])
    if "--debug" in sys.argv:
        dbg = out / "debug"
        dbg.mkdir(exist_ok=True)
        for name, m in {"holes": holes, "near": near, "spots": spots, "alpha_opaque": A, "transmission": T,
                        "shadow": S, "model_alpha": alpha_m}.items():
            Image.fromarray((np.clip(m.astype(np.float32), 0, 1) * 255).astype(np.uint8)).save(dbg / f"{name}.png")

    fr = cfg.get("framing", {})
    if fr.get("box"):                                # close-ups keep the photographer's crop
        bx0, by0, bx1, by1 = fr["box"]
        left, top, W, H = bx0 - x0, by0 - y0, bx1 - bx0, by1 - by0
    else:
        left, top, W, H = frame_crop(A, fr.get("aspect", [4, 5]), fr.get("fill", 0.86), fr.get("center_y", 0.56))
    comp_c = paste_canvas(comp, left, top, W, H, stage)
    stage_srgb = lin_to_srgb(comp_c)
    ow = 2000
    oh = int(round(ow * H / W))
    Image.fromarray((stage_srgb * 255 + 0.5).astype(np.uint8)).resize((ow, oh), Image.LANCZOS).save(out / "stage.jpg", quality=92)
    cv2.imwrite(str(out / "stage-full.png"), cv2.cvtColor((stage_srgb * 65535).astype(np.uint16), cv2.COLOR_RGB2BGR))

    # Exact layers, same crop. Over any background: multiply by shadow.png and lens.png, then
    # put frame.png on top (normal blend). Multiply layers are sRGB-encoded, so the multiply
    # works in an ordinary sRGB document.
    lay = out / "layers"
    lay.mkdir(exist_ok=True)
    rgba = paste_canvas(np.dstack([lin_to_srgb(F), A]), left, top, W, H, 0)
    Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA").save(lay / "frame.png", optimize=True)
    Tf_c = paste_canvas(Tf, left, top, W, H, 1.0)
    Image.fromarray((lin_to_srgb(Tf_c) * 255 + 0.5).astype(np.uint8), "RGB").save(lay / "lens.png", optimize=True)
    S_c = paste_canvas(S, left, top, W, H, 1.0)
    Image.fromarray((lin_to_srgb(S_c) * 255 + 0.5).astype(np.uint8), "L").save(lay / "shadow.png", optimize=True)
    # One-file cut-out: the lens filter folded into the alpha (a neutral dark glass plus its tint,
    # exact over the stage color, close over anything light)
    Tmin = Tf.min(-1)
    A_cut = A + (1 - A) * (1 - Tmin)
    P_cut = F * A[..., None] + (1 - A[..., None]) * stage * (Tf - Tmin[..., None])
    F_cut = np.where(A_cut[..., None] > 1e-4, P_cut / np.maximum(A_cut[..., None], 1e-4), 0)
    cut = paste_canvas(np.dstack([lin_to_srgb(F_cut), A_cut]), left, top, W, H, 0)
    Image.fromarray((cut * 255 + 0.5).astype(np.uint8), "RGBA").save(out / "cutout.png", optimize=True)

    # review sheet: original crop vs result, same framing
    orig_c = paste_canvas(before, left, top, W, H, before[0, 0])
    pw = 800
    ph = int(round(pw * H / W))
    a = Image.fromarray((orig_c * 255).astype(np.uint8)).resize((pw, ph), Image.LANCZOS)
    b = Image.fromarray((stage_srgb * 255).astype(np.uint8)).resize((pw, ph), Image.LANCZOS)
    sheet = Image.new("RGB", (2 * pw + 20, ph), "white")
    sheet.paste(a, (0, 0)); sheet.paste(b, (pw + 20, 0))
    sheet.save(out / "compare.jpg", quality=90)

    report["crop"] = [left + x0, top + y0, W, H]
    (out / "report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report))


if __name__ == "__main__":
    if sys.argv[1] == "--mask":
        mask_job(sys.argv[3], sys.argv[2], int(sys.argv[4]) if len(sys.argv) > 4 else None)
    else:
        main(sys.argv[1])
