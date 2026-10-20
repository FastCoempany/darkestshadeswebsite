#!/usr/bin/env python3
"""Clean one lightbox shot into a catalog image and a cut-out (docs/brief/07-photography.md, track 1).

    python3 tools/photo/clean_lightbox.py content/photography/shots/IMG_3596.json [--debug]

Reads the original from work/originals/ (tools/photo/zipget.py), writes work/out/<shot>/:
    stage.jpg            the frame on the uniform stage color, framed by its angle's rule
                         (content/photography/framing.json) or the shot's own box, 2000 wide
    stage-full.png       same, at the shot's working resolution (16-bit)
    cutout.png           one-file RGBA (16-bit): rims and temples opaque, lenses see-through
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


def out_dir(cfg):
    """work/out/<shot>/, or work/out/<shot>-<variant>/ for a second image made from the same shot
    (F04's hero is its front shot on a wider stage)."""
    return ROOT / "work" / "out" / (cfg["shot"] + (f"-{cfg['variant']}" if cfg.get("variant") else ""))


def mask_job(cfg_path, kind, index=None):
    from rembg import new_session, remove
    cfg = json.loads(pathlib.Path(cfg_path).read_text())
    masks = out_dir(cfg) / "masks"
    masks.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray((_region_rgb(cfg) * 255).astype(np.uint8))
    if kind == "isnet":
        m = remove(img, session=new_session("isnet-general-use"), only_mask=True)
        m.save(masks / "alpha.png")
    else:  # SAM, point prompts for one lens
        x0, y0 = cfg["region"][:2]
        lens = cfg["lenses"][index]
        pts = [{"type": "point", "data": [x - x0, y - y0], "label": 1} for x, y in lens["points"]]
        # points that are not lens (the rims around it, seen from behind as dark as the lens)
        pts += [{"type": "point", "data": [x - x0, y - y0], "label": 0} for x, y in lens.get("exclude", [])]
        m = remove(img, session=new_session("sam"), only_mask=True, sam_prompt=pts)
        m.save(masks / f"lens-{index}.png")


def masks_for(cfg_path, cfg):
    import subprocess
    masks = out_dir(cfg) / "masks"
    jobs = [("isnet", None, masks / "alpha.png")]
    jobs += [("sam", i, masks / f"lens-{i}.png") for i in range(len(cfg.get("lenses", [])))]
    for kind, i, path in jobs:
        if not path.exists():
            args = [sys.executable, __file__, "--mask", kind, str(cfg_path)] + ([str(i)] if i is not None else [])
            subprocess.run(args, check=True)
    alpha = np.asarray(Image.open(masks / "alpha.png"), np.float32) / 255.0
    from scipy import ndimage as ndi
    lens = np.zeros(alpha.shape, bool)
    round_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    x0, y0 = cfg["region"][:2]
    for i in range(len(cfg.get("lenses", []))):
        m = np.asarray(Image.open(masks / f"lens-{i}.png")) > 128
        # a lens is one piece: SAM sometimes adds specks along a temple or across the other lens,
        # which the convex hull below would join into one slab. Cut thin links, keep the piece
        # the prompt points are in (or the largest), back to its own edge.
        opened = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
        lab, n = ndi.label(opened)
        if n > 1:
            hits = [lab[int(y - y0), int(x - x0)] for x, y in cfg["lenses"][i]["points"]
                    if 0 <= y - y0 < lab.shape[0] and 0 <= x - x0 < lab.shape[1]]
            hits = [h for h in hits if h > 0]
            keep = hits[0] if hits else 1 + int(np.argmax(ndi.sum(opened, lab, range(1, n + 1))))
            piece = cv2.dilate((lab == keep).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))) > 0
            m = m & piece
        # a lens has no holes and no notches: what SAM leaves out inside it, or bites out of its
        # edge, is something seen through it (a temple behind, a dark reflection)
        m = ndi.binary_fill_holes(m)
        m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, round_k) > 0
        if cfg["lenses"][i].get("convex"):
            # a lens with no concave edge (round, square, octagon; not F06's shield): bigger bites go too
            pts = cv2.findNonZero(m.astype(np.uint8))
            hull = np.zeros(m.shape, np.uint8)
            cv2.fillConvexPoly(hull, cv2.convexHull(pts), 1)
            m = hull > 0
        lens |= ndi.binary_fill_holes(m)
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


def shadow_zone(obj, reach=600, side=150, soft=40, around=None):
    """Where the frame's own shadow can fall in this tent: below the frame in the picture (light from
    above, camera looking down) and a little to either side. Anything darker elsewhere (the sweep's
    horizon behind the frame) is tent, not shadow. Weight 0..1, soft at the sides only: it starts
    inside the frame, so it never bleeds above it. Seen from straight above (`around`, px), the
    shadow lies all round the frame instead, and there is no horizon to confuse it with."""
    if around:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * around + 1,) * 2)
        zone = cv2.dilate(obj.astype(np.uint8), k).astype(np.float32)
        return cv2.GaussianBlur(zone, (0, 0), soft) if soft else zone
    h, w = obj.shape
    last = np.full(w, -10 ** 6, np.int64)
    zone = np.zeros((h, w), bool)
    for y in range(h):
        last = np.where(obj[y], y, last)
        d = y - last
        zone[y] = (d > 0) & (d <= reach)
    zone = cv2.dilate(zone.astype(np.uint8), np.ones((1, 2 * side + 1), np.uint8)).astype(np.float32)
    if not soft:
        return zone
    # soft at the sides; a little feathered top and bottom too, so its edges never show as a box
    zone = cv2.GaussianBlur(zone, (0, 1), sigmaX=soft, sigmaY=0.1)
    return cv2.GaussianBlur(zone, (1, 0), sigmaX=0.1, sigmaY=8)


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


def rows_inpaint(img, mask, scale=4):
    """Fill `mask` row by row from both ends of each masked run, at low resolution: the tent's
    structure behind a front view (the horizon where floor meets wall) runs across the picture,
    so it carries straight on behind the frame and through a light lens."""
    h, w = mask.shape
    small = cv2.resize(img, (w // scale, h // scale), interpolation=cv2.INTER_AREA)
    m = cv2.resize(mask.astype(np.uint8), (w // scale, h // scale), interpolation=cv2.INTER_NEAREST) > 0
    out = small.copy()
    xs = np.arange(small.shape[1])
    for y in range(small.shape[0]):
        good = ~m[y]
        if m[y].any() and good.sum() >= 2:
            out[y, m[y]] = np.interp(xs[m[y]], xs[good], small[y, good])
    out = np.where(m, cv2.GaussianBlur(out, (0, 0), sigmaX=1.0, sigmaY=2.0), out)
    up = cv2.resize(out, (w, h), interpolation=cv2.INTER_CUBIC)
    return np.where(mask, up, img)


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
        g = 2 * mk.get("grow_px", 2) + 1       # an engraving's soft shoulder goes with its strokes
        strokes = cv2.dilate(strokes, np.ones((g, g), np.uint8), iterations=1)
        report_mask |= strokes
        if not strokes.any():
            continue
        if mk.get("temple"):
            out = fill_along_temple(out, strokes, mk["temple"], region_xy, texture_dx=mk.get("texture_dx"),
                                    texture_from=mk.get("texture_from"))
        elif mk.get("axis") is not None:
            out = inpaint_along(out, strokes, mk["axis"])
        else:
            total |= strokes          # small marks: plain inpainting, all at once below
    if total.any():
        out = cv2.inpaint(out, total, 6, cv2.INPAINT_NS)
        noise = np.random.default_rng(3).normal(0, 1.4, out.shape)   # grain back, as along the temples
        out = np.where(total[..., None] > 0, np.clip(out + noise, 0, 255), out).astype(np.uint8)
    return out.astype(np.float32) / 255.0, report_mask


def fill_along_temple(img, mask, temple, region_xy, grain=1.4, seed=11, texture_dx=None, texture_from=None):
    """Rebuild a patch of temple face line by line. The face is rectified between guide lines along
    it, so every row follows the acetate, core wire and bevel stripes exactly; masked runs are
    interpolated from both ends of the row. The guides are the temple's measured top and bottom
    edges, y = a*x + b in original-image coordinates (`top`, `bottom`), or, where the stripes are
    not parallel to each other (a core wire running at a slant inside clear acetate), every stripe's
    edge from top to bottom (`guides`); a third coefficient, y = a*x + b + c*x*x, follows a line
    that bends in the picture.
    On a textured face (gloss acetate that mirrors the tent's dimpled wall, a grained metal core
    seen through clear acetate), rows interpolated from their two ends come out as streaks: then the
    rebuilt rows give only the face's smooth shading, and its fine texture comes from the same rows
    where the face is clean, `texture_dx` px along the picture, or by `texture_from`: segments
    [x0, x1, s0, s1] in the picture's x, columns x0..x1 taking columns s0..s1 (s1 < s0 mirrors
    them), for a patch longer than the clean face beside it."""
    ox, oy = region_xy
    curves = temple.get("guides") or [temple["top"], temple["bottom"]]

    def guide(coef, x):
        return coef[0] * x + coef[1] + (coef[2] * x * x if len(coef) > 2 else 0)

    ys, xs = np.nonzero(mask)
    pad = 60
    xa, xb = xs.min() - pad, xs.max() + pad
    segs = []                                                      # (u0, u1, s0, s1), region x
    if texture_dx:
        segs.append((xs.min(), xs.max(), xs.min() + texture_dx, xs.max() + texture_dx))
    for x0_, x1_, s0, s1 in texture_from or []:
        segs.append((x0_ - ox, x1_ - ox, s0 - ox, s1 - ox))
    for _, _, s0, s1 in segs:
        xa, xb = min(xa, int(min(s0, s1)) - pad), max(xb, int(max(s0, s1)) + pad)
    xa, xb = max(0, xa), min(img.shape[1] - 1, xb)
    U = np.arange(xa, xb + 1, dtype=np.float32)
    G = [guide(c, U + ox) - oy for c in curves]
    nb = len(G) - 1                                                # bands between the guides
    n = [int(np.ceil((G[k + 1] - G[k]).max())) + 1 for k in range(nb)]
    start = np.cumsum([0] + n[:-1])                                # each band's first row
    scale = np.array([n[k] if k < nb - 1 else n[k] - 1 for k in range(nb)], np.float32)
    bands = []
    for k in range(nb):                                            # the last band ends on its guide
        V = np.linspace(0, 1, n[k], endpoint=k == nb - 1, dtype=np.float32)
        bands.append(G[k][None, :] + V[:, None] * (G[k + 1] - G[k])[None, :])
    map_y = np.concatenate(bands, 0).astype(np.float32)
    nv = map_y.shape[0]
    map_x = np.repeat(U[None, :], nv, 0).astype(np.float32)
    R = cv2.remap(img.astype(np.float32), map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Rm = cv2.remap(mask.astype(np.float32), map_x, map_y, cv2.INTER_LINEAR) > 0.3
    R0 = R.copy()
    ends = R0
    if segs:
        # A textured face: each row runs between the face's local average at either end, not single
        # pixels, whose grain would streak it; the texture is laid on top below.
        ok = (~Rm).astype(np.float32)
        num = cv2.GaussianBlur(R0 * ok[..., None], (49, 1), 8)
        den = cv2.GaussianBlur(ok, (49, 1), 8)[..., None]
        ends = np.where(den > 1e-3, num / np.maximum(den, 1e-3), R0)
    for r in range(nv):
        row = Rm[r]
        if not row.any() or (~row).sum() < 2:
            continue
        good = np.nonzero(~row)[0]
        bad = np.nonzero(row)[0]
        for ch in range(R.shape[2]):
            R[r, bad, ch] = np.interp(bad, good, ends[r, good, ch])
    if segs:
        base = cv2.GaussianBlur(R, (0, 0), 5)                      # the face's smooth shading
        hp = R0 - cv2.GaussianBlur(R0, (0, 0), 5)                  # its fine texture
        # Segments that overlap cross-fade (keeping the texture's strength); a lone one is used as is.
        acc = np.zeros_like(hp)
        wsum = np.zeros(U.shape, np.float32)
        sy = np.repeat(np.arange(nv, dtype=np.float32)[:, None], len(U), 1)
        for u0, u1, s0, s1 in segs:
            sel = (U >= u0) & (U <= u1)
            if not sel.any():
                continue
            src = s0 + (U - u0) * (s1 - s0) / max(u1 - u0, 1)   # column u takes column src[u]
            w = np.where(sel, np.clip(np.minimum(U - u0, u1 - U) / 20.0, 1e-3, 1), 0).astype(np.float32)
            sx = np.repeat((src - xa)[None, :], nv, 0).astype(np.float32)
            acc += cv2.remap(hp, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) * w[None, :, None]
            wsum += w * w
        tex = acc / np.sqrt(np.maximum(wsum, 1e-12))[None, :, None]
        # and the patch fades in from the clean face at both ends of every row, over 12 px
        idx = np.arange(len(U))[None, :].repeat(nv, 0)
        left = np.maximum.accumulate(np.where(~Rm, idx, -10 ** 6), axis=1)
        right = np.minimum.accumulate(np.where(~Rm, idx, 10 ** 6)[:, ::-1], axis=1)[:, ::-1]
        ws = np.clip(np.minimum(idx - left, right - idx) / 12.0, 0, 1)[..., None]
        R = np.where(Rm[..., None], R0 * (1 - ws) + (base + tex) * ws, R)
    else:
        R += np.random.default_rng(seed).normal(0, grain, R.shape).astype(np.float32)
    # back to image space, only inside the mask (feathered)
    yy, xx = np.mgrid[0:img.shape[0], xa:xb + 1].astype(np.float32)
    Gs = np.stack(G, 0)                                            # guides per column, region y
    k = np.zeros(yy.shape, np.int32)                               # each pixel's band
    for j in range(1, nb):
        k += yy >= Gs[j][None, :]
    col = np.broadcast_to(np.arange(yy.shape[1])[None, :], yy.shape)
    gk, gk1 = Gs[k, col], Gs[k + 1, col]
    v = (start[k] + (yy - gk) / np.maximum(gk1 - gk, 1) * scale[k]).astype(np.float32)
    u = (xx - xa).astype(np.float32)
    back = cv2.remap(R, u, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    mm = cv2.GaussianBlur(mask[:, xa:xb + 1].astype(np.float32), (0, 0), 3.0 if segs else 1.2)[..., None]
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
FRAMING = ROOT / "content" / "photography" / "framing.json"


def framing_rule(cfg):
    """The shot's framing: its angle's rule (content/photography/framing.json), then the shot's
    own keys over it ("fill" is the older name for "width")."""
    rule = dict(json.loads(FRAMING.read_text())["angles"].get(cfg["angle"], {}))
    own = dict(cfg.get("framing", {}))
    if "fill" in own:
        own["width"] = own.pop("fill")
    if "bottom" in own or "center_y" in own:
        rule.pop("bottom", None)
        rule.pop("center_y", None)
    rule.update(own)
    return rule


def picture_bounds(rule, photo_hw):
    """The picture's edges in photograph pixels (x0, y0, x1, y1): the photograph's own, or where
    the shot's framing 'cut' ends it sooner (a side beyond which the frame can't be held)."""
    ph, pw = photo_hw
    b = {"left": 0, "top": 0, "right": pw, "bottom": ph}
    b.update(rule.get("cut", {}))
    return b["left"], b["top"], b["right"], b["bottom"]


def photo_edges(alpha, region, bounds, min_run=5):
    """The sides where the frame meets the picture's edge (a temple running out of the picture,
    or a tip touching it): there the canvas ends at that edge too, so the frame runs off the
    picture instead of stopping in mid-air."""
    x0, y0 = region[:2]
    bx0, by0, bx1, by1 = bounds
    a = alpha > 0.15
    hh, ww = a.shape
    cl, ct, cr, cb = bx0 - x0, by0 - y0, bx1 - x0, by1 - y0      # the edges in region pixels
    touch = {"left": 0 <= cl < ww - 3 and a[:, cl:cl + 3].any(1).sum() >= min_run,
             "right": 3 < cr <= ww and a[:, cr - 3:cr].any(1).sum() >= min_run,
             "top": 0 <= ct < hh - 3 and a[ct:ct + 3, :].any(0).sum() >= min_run,
             "bottom": 3 < cb <= hh and a[cb - 3:cb, :].any(0).sum() >= min_run}
    return [s for s in ("left", "right", "top", "bottom") if touch[s]]


def frame_extent(alpha, min_area=100):
    """The frame's extent in the region (x0, y0, x1, y1, ends exclusive): everything the alpha holds
    above 0.15, lenses included, less specks."""
    n, _, st, _ = cv2.connectedComponentsWithStats((alpha > 0.15).astype(np.uint8), connectivity=8)
    keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= min_area]
    x0 = min(st[i, 0] for i in keep)
    y0 = min(st[i, 1] for i in keep)
    x1 = max(st[i, 0] + st[i, 2] for i in keep)
    y1 = max(st[i, 1] + st[i, 3] for i in keep)
    return int(x0), int(y0), int(x1), int(y1)


def canvas_for(rule, ext, runs, region, bounds):
    """The canvas (left, top, W, H in region pixels) that frames the frame by its angle's rule, so
    an angle sits at the same size and height in every frame's set.

    width: the frame's share of the canvas width. Where a temple runs off a side of the picture,
    the visible width is not the frame's, so the frame's height sets the scale instead (height:
    its share of the canvas height), as long as the frame then fills at least min_width of the
    canvas (otherwise the width rule), and at most what leaves the open side the margin a centred
    frame has. The side it runs off stays the picture's edge (bounds, photograph pixels). bottom:
    where the frame's lowest point sits (share of the canvas height from the top), or center_y:
    where its middle sits."""
    rx0, ry0 = region[:2]
    bx0, by0, bx1, by1 = bounds
    x0, y0, x1, y1 = ext
    bw, bh = x1 - x0, y1 - y0
    ax, ay = rule["aspect"]
    width = rule["width"]
    off = [s for s in ("left", "right") if s in runs]
    how = "width"
    if len(off) == 2:
        Wc = bx1 - bx0
        how = "picture's width"
    else:
        Wc = bw / width
        if off and rule.get("height"):
            Wh = bh / rule["height"] * ax / ay
            if bw / Wh >= rule.get("min_width", 0.75):
                Wc = max(Wh, bw / (1 - (1 - width) / 2))
                how = "height"
    # whole multiples of the aspect, so every picture is exactly 4:5 (or 3:2); a canvas held by
    # the picture's edges on both sides stays inside them
    k = max(1, int(Wc // ax) if len(off) == 2 else int(round(Wc / ax)))
    W, H = ax * k, ay * k
    if "left" in runs:
        left = bx0 - rx0
    elif "right" in runs:
        left = bx1 - rx0 - W
    else:
        left = int(round((x0 + x1) / 2 - W / 2))
    if "bottom" in rule:
        top = int(round(y1 - rule["bottom"] * H))
    else:
        top = int(round((y0 + y1) / 2 - rule.get("center_y", 0.5) * H))
    if "top" in runs:
        top = by0 - ry0
    elif "bottom" in runs:
        top = by1 - ry0 - H
    return int(left), int(top), int(W), int(H), how


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
    out = out_dir(cfg)
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
        fill = rows_inpaint if cfg.get("tent_fill") == "rows" else lowres_inpaint
        C = fill(np.where(tent, np.clip(ratio, 0.3, 3), 1).astype(np.float32), ~tent)
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
    fade = np.clip((450 - d) / 300, 0, 1) * zone
    hh, ww = S.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    # Whatever is seen through a lens or a gap stays in its transmission (below), so the shadow
    # layer is 1 there; the frame itself hides the rest of the inpainted shadow.
    see = cv2.dilate((lens | (filled & ~solid)).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    S_measured = S

    def finish_shadow(open_side):
        # and to 1 at the region's border where the picture is padded beyond it: no seam with the
        # padding. A border that is also the picture's edge (a close-up kept in the photographer's
        # crop, the frame running off it) keeps its shadow right up to the edge.
        sides = {"left": xx, "top": yy, "right": ww - 1 - xx, "bottom": hh - 1 - yy}
        edge = np.full((hh, ww), 1e9, np.float32)
        for side, dist in sides.items():
            if open_side[side]:
                edge = np.minimum(edge, dist.astype(np.float32))
        wt = fade * np.clip(edge / 120.0, 0, 1)
        # darkening within the tent model's error (about 2%) is not shadow: it would show as
        # faint patches on the even stage
        Sf = 1 - np.clip((1 - S_measured) - 0.02, 0, 1) / 0.98 * wt
        Sf = np.where(see, 1.0, Sf).astype(np.float32)
        return np.where(see | solid, cv2.GaussianBlur(Sf, (0, 0), 2), Sf).astype(np.float32)

    rule = framing_rule(cfg)
    box = rule.get("box")
    bounds = picture_bounds(rule, full.shape[:2])

    def open_sides(runs):
        if box is None:
            return {s: s not in runs for s in ("left", "top", "right", "bottom")}
        return {"left": box[0] < x0, "top": box[1] < y0, "right": box[2] > x1, "bottom": box[3] > y1}

    # where the frame meets the picture's edge: first from the model's alpha, measured again on the
    # finished alpha below (a blurred tip the model misses)
    runs0 = photo_edges(alpha_m, cfg["region"], bounds)
    S = finish_shadow(open_sides(runs0))
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
    # A light lens (F01's blue, F03's yellow) shows the tent's textured wall through it; with
    # `keep_behind`, things clearly darker than the lens's own tint (a temple or nose pad behind
    # it) stay, and only the tent behind is evened out.
    # Each lens keeps the tint its own photograph measured: a lens seen at an angle, with the tent's
    # light on it, looks as it did in that shot (founder, Oct 19 2026).
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
            if lc.get("keep_behind"):
                ratio = lum(Tc) / np.maximum(lum(fitimg), 1e-4)
                lo, hi = lc.get("behind_ratio", [0.5, 0.75])
                m = cv2.GaussianBlur(np.clip((hi - ratio) / (hi - lo), 0, 1).astype(np.float32), (0, 0), 1.5)
                new = new * (1 - m[..., None]) + Tc * m[..., None]
            Tc[li] = np.clip(new[li], 0, 1)
    report["lens"] = {"hole_px": int(holes.sum()), "cleaned_px": int(spots.sum()),
                      "dust_px": int((dust & holes).sum()),
                      "transmission_median_rgb": [round(float(np.median(Tc[..., c][holes])), 3) for c in range(3)] if holes.any() else None}

    # remove the old marks, then unmix the opaque parts from the tent behind their soft edges
    srgb_clean, mark_mask = remove_marks(srgb, cfg.get("marks", []), rx)
    report["marks_px"] = int(mark_mask.sum())
    lin_clean = srgb_to_lin(srgb_clean)
    # Soft edges unmix against the tent right beside them, not against the tent model under the
    # frame: that is filled in from all round (both sides of a thin temple, tent further off), so
    # where the tent darkens towards the frame (the sweep's falloff, a halo round a defocused
    # temple) it is brighter than what is really behind the edge, and the edge got a grey halo, or
    # began with a step, ragged where the gates below cut it (IMG_3487's far temple). The tent is
    # read on a ring 10 to 16 px outside the frame, only where it is tent: out of the frame's own
    # shadow (unmixed against it, an edge would no longer match the shadow layer it is put back
    # over), and away from anything more than 10 px outside the model's frame that is clearly dark
    # or colored (a defocused far temple the model missed, F01's blue tortoise, F02's red; nearer
    # in, it is the edge's own blur): its blur would pass for tent and make the part beside it
    # see-through. Each pixel takes the local average of that ring, weighted by how much of it is
    # near, so the handover back to the model is smooth. It sets the soft edges' opacity and
    # color; the gates that decide what is frame (`dark` below) keep the tent model.
    d_out = cv2.distanceTransform((1 - obj).astype(np.uint8), cv2.DIST_L2, 5)
    mx, mn = srgb_clean.max(-1), srgb_clean.min(-1)
    stray = ((lum(lin_clean) < 0.6 * lum(back)) | ((mx - mn) / (mx + 1e-4) > 0.22)) & (d_out > 10)
    stray = cv2.dilate(stray.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))
    ring = ((d_out > 10) & (d_out <= 16) & (lum(lin) > 0.85 * lum(back))).astype(np.float32)
    ring *= np.clip((S - 0.85) / 0.1, 0, 1) * (1 - cv2.GaussianBlur(stray.astype(np.float32), (0, 0), 8))
    if ring.max() > 0:
        den = cv2.GaussianBlur(ring, (0, 0), 15)
        back_e = cv2.GaussianBlur(lin * ring[..., None], (0, 0), 15) / np.maximum(den, 1e-6)[..., None]
        w = np.clip(den / 0.05, 0, 1)[..., None]
        back_s = (back * (1 - w) + back_e * w).astype(np.float32)
    else:
        w = np.zeros(S.shape + (1,), np.float32)
        back_s = back
    # Opacity from physics as well as from the model: a pixel much darker than the tent behind it
    # is mostly frame, whatever the model thinks (defocused rims get soft model alphas). Highlights
    # on the acetate keep the model's alpha.
    T_all = np.clip(lum(lin_clean) / (lum(back) + 1e-5), 0, 1)
    model_zone = cv2.dilate((alpha_m > 0.05).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
    near = model_zone.copy()
    dark = (1 - T_all) > 0.4                          # clearly darker than the tent: frame or lens
    lab, n = ndi.label(dark)
    if n:
        hit = np.unique(lab[(alpha_m > 0.5) & dark])
        near |= np.isin(lab, hit[hit > 0])
    # Two layers: the opaque frame (F, A) and the see-through filter (Tf, multiplies what's behind)
    t0 = 0.05                                         # darkening within the tent model's noise
    A_phys = np.clip((1 - T_all - t0) / (1 - t0), 0, 1)
    A_phys = cv2.GaussianBlur(A_phys.astype(np.float32), (0, 0), 1.0)   # per-pixel noise would speckle the edges
    # the model's soft edges, against the tent beside them (above)
    T_s = np.clip(lum(lin_clean) / (lum(back_s) + 1e-5), 0, 1)
    A_s = cv2.GaussianBlur(np.clip((1 - T_s - t0) / (1 - t0), 0, 1).astype(np.float32), (0, 0), 1.0)
    A = np.where(near, np.maximum(alpha_m, A_s), alpha_m).astype(np.float32)
    # Parts the model missed altogether (a defocused far temple): the tent is neutral grey, so a
    # clearly colored pixel is frame too, however light (F01's blue tortoise patches), and black
    # acetate still reflects a little, so past 0.8 it is solid. Measured per pixel this is noisy;
    # those edges are soft anyway, so it is smoothed, and given a margin to fade out in.
    A_sat = np.clip(((mx - mn) / (mx + 1e-4) - 0.12) / 0.2, 0, 1).astype(np.float32)
    lab, n = ndi.label(dark | (A_sat > 0.5))
    missed = np.zeros(A.shape, bool)
    if n:
        hit = np.unique(lab[(alpha_m > 0.5) & (dark | (A_sat > 0.5))])
        missed = cv2.dilate(np.isin(lab, hit[hit > 0]).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
        missed &= ~model_zone
        # against the tent beside the frame where that was read (the outer blur of a defocused edge
        # lies here, past the model's zone); the gate fades in over a few px, as a square-cut edge
        # would show in a soft shadow or a blur
        A_pix = np.clip(cv2.GaussianBlur(np.maximum(A_s, A_sat).astype(np.float32), (0, 0), 1.5) / 0.8, 0, 1)
        g = cv2.GaussianBlur(missed.astype(np.float32), (0, 0), 4) * (missed | ~model_zone)
        A = (A * (1 - g) + A_pix * g).astype(np.float32)
    A[holes] = 0.0
    rim = solid & ~holes
    A[rim] = np.maximum(A[rim], 0.995)
    F = np.where(A[..., None] > 0.02, (lin_clean - (1 - A[..., None]) * back_s) / np.maximum(A[..., None], 0.02), 0)
    if missed.any():
        # with a measured alpha, unmixing per channel blows small tints up into strong color (a
        # grey wire that picked up a little red from the rim beside it); unmix the brightness
        # only and keep the pixel's own color there
        Fl = np.clip((lum(lin_clean) - (1 - A) * lum(back)) / np.maximum(A, 0.02), 0, 1)
        Fc = lin_clean * (Fl / np.maximum(lum(lin_clean), 1e-4))[..., None]
        F = np.where(missed[..., None], Fc, F)
    F = np.clip(F, 0, 1).astype(np.float32)
    Tf = np.ones_like(lin, dtype=np.float32)
    Tf[holes] = Tc[holes]

    if cfg.get("gcd"):
        place_gcd(F, A, cfg, rx, report)

    # Where the frame, lenses included, meets the picture's edge, the canvas ends there too
    # (framing, below) and the shadow is kept right up to it. The finished alpha also holds what
    # the model missed: a blurred tip just touching the edge (F01's side view), a front the
    # model lost at the edge (F05's).
    held = A + (1 - A) * (1 - Tf.min(-1))
    runs = photo_edges(held, cfg["region"], bounds)
    if open_sides(runs) != open_sides(runs0):
        S = finish_shadow(open_sides(runs))

    # re-stage on the uniform stage color, keeping the frame's own contact shadow
    stage = hex_lin(STAGE_HEX)
    comp = F * A[..., None] + stage * S[..., None] * Tf * (1 - A[..., None])
    if "--debug" in sys.argv:
        dbg = out / "debug"
        dbg.mkdir(exist_ok=True)
        for name, m in {"holes": holes, "near": near, "spots": spots, "alpha_opaque": A, "transmission": T,
                        "shadow": S, "model_alpha": alpha_m, "marks": mark_mask, "alpha_physical": A_phys,
                        "darkening": T_all, "shadow_zone": zone, "tent_behind": lum(back_s), "missed": missed,
                        "model_zone": model_zone, "edge_ring": ring, "edge_weight": w[..., 0],
                        "stray": stray}.items():
            Image.fromarray((np.clip(m.astype(np.float32), 0, 1) * 255).astype(np.uint8)).save(dbg / f"{name}.png")

    # framing (content/photography/framing.json): close-ups and the photographed heroes keep the
    # photographer's crop (a box); every other angle is cut around the frame by its angle's rule
    report["runs_off"] = runs
    ax, ay = rule["aspect"]
    if box:
        bx0, by0, bx1, by1 = box
        left, top, W, H = bx0 - x0, by0 - y0, bx1 - bx0, by1 - by0
        report["framing"] = {"box": box}
    else:
        bx0, by0, bx1, by1 = bounds
        inb = np.zeros(held.shape, bool)
        inb[max(0, by0 - y0):max(0, by1 - y0), max(0, bx0 - x0):max(0, bx1 - x0)] = True
        ext = frame_extent(np.where(inb, held, 0))
        left, top, W, H, how = canvas_for(rule, ext, runs, cfg["region"], bounds)
        ex0, ey0, ex1, ey1 = ext
        report["framing"] = {"scale": how, "fill_width": round((ex1 - ex0) / W, 3),
                             "fill_height": round((ey1 - ey0) / H, 3)}
        inside = {"left": ex0 >= left, "right": ex1 <= left + W, "top": ey0 >= top, "bottom": ey1 <= top + H}
        if not all(inside[s] or s in runs for s in inside):
            report["framing_note"] = "the canvas cuts the frame: " + ", ".join(s for s in inside if not inside[s] and s not in runs)
    if abs(W * ay / (H * ax) - 1) > 0.002:
        report["framing_note"] = f"the canvas is {W}x{H}, not {ax}:{ay}"
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
    # 16-bit: the master that goes to the DAM (07-photography.md, step 11)
    cv2.imwrite(str(out / "cutout.png"), cv2.cvtColor((np.clip(cut, 0, 1) * 65535 + 0.5).astype(np.uint16), cv2.COLOR_RGBA2BGRA))

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
