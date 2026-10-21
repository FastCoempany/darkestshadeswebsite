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
        if n >= 1:
            # also when the opening leaves one piece: a speck it wiped out entirely would still be
            # in the mask, and the convex hull below would stretch to it across the rim (F01's
            # inside view and detail had a pale triangle over the rim)
            hits = [lab[int(y - y0), int(x - x0)] for x, y in cfg["lenses"][i]["points"]
                    if 0 <= y - y0 < lab.shape[0] and 0 <= x - x0 < lab.shape[1]]
            hits = [h for h in hits if h > 0]
            keep = hits[0] if hits else 1 + int(np.argmax(ndi.sum(opened, lab, range(1, n + 1))))
            piece = cv2.dilate((lab == keep).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))) > 0
            m = m & piece
        # parts SAM left out that open onto the rim, so no filling can close them (a dark temple
        # seen through the top of F06's gradient shield): polygons added by hand
        for poly in cfg["lenses"][i].get("add", []):
            extra = np.zeros(m.shape, np.uint8)
            cv2.fillPoly(extra, [np.array([[x - x0, y - y0] for x, y in poly], np.int32)], 1)
            m = m | (extra > 0)
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
    core = zone
    zone = cv2.dilate(core.astype(np.uint8), np.ones((1, 2 * side + 1), np.uint8)).astype(np.float32)
    if not soft:
        return zone
    # soft at the sides; a little feathered top and bottom too, so its edges never show as a box
    zone = cv2.GaussianBlur(zone, (0, 1), sigmaX=soft, sigmaY=0.1)
    under = cv2.GaussianBlur(zone, (1, 0), sigmaX=0.1, sigmaY=8)
    # beside the frame the zone starts level with the frame's lowest point in the next columns, a
    # straight line through any shadow there (beside the F08 hero's end-piece): it fades in slowly
    beside = cv2.GaussianBlur(zone, (1, 0), sigmaX=0.1, sigmaY=40)
    w = cv2.GaussianBlur((zone > 0.01).astype(np.float32) * (~core).astype(np.float32), (0, 0), 20)
    return under * (1 - w) + np.minimum(under, beside) * w


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


def grain_of(srgb, mask):
    """The picture's grain over `mask`: the spread of its fine detail in the encoded brightness (the
    median deviation, so edges and reflections there don't count)."""
    Ls = lum(srgb)
    v = (Ls - cv2.GaussianBlur(Ls, (0, 0), 2))[mask]
    return 1.4826 * float(np.median(np.abs(v - np.median(v)))) if v.size else 0.0


def lens_grain(rng, sig, level, stage_l):
    """The camera's grain for a refilled lens, as transmission: in the brightness only (the
    photographs show hardly any colored grain: JPEG keeps color at half resolution), and as even in
    the picture's own encoded terms at every level (`sig`, from `grain_of`) as the camera's is.
    `level` is the lens's brightness on the new stage (linear), `stage_l` the stage's. Drawn per
    channel at one strength in linear light, it came out as colored speckle, black in the dark top
    of a gradient lens (F08)."""
    s = lin_to_srgb(np.clip(level, 0, 1))
    slope = np.where(s <= 0.04045, 1 / 12.92, 2.4 / 1.055 * ((s + 0.055) / 1.055) ** 1.4)
    return (rng.normal(0, 1, level.shape) * (sig * slope / stage_l)).astype(np.float32)


def add_grain(fill, nz):
    """`nz` (brightness) on a filled lens, in proportion to each channel: a neutral lens stays neutral."""
    return fill + nz[..., None] * fill / np.maximum(lum(fill), 1e-4)[..., None]


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
        if mk.get("weak_threshold") is not None and strokes.any():
            # and the fainter parts of those strokes, joined to them: an engraving's shallow ends and
            # thin joins, too faint for the threshold, stood as dark dots in a row where the letters
            # had been (F01's detail); the tortoise's own mottling, joined to no stroke, stays as it is
            from scipy import ndimage as ndi
            weak = (hat > mk["weak_threshold"]) & (area > 0)
            strokes = ndi.binary_propagation(strokes > 0, mask=weak, structure=np.ones((3, 3), bool)).astype(np.uint8)
        if mk.get("fill_whole"):
            strokes = area.copy()
        g = 2 * mk.get("grow_px", 2) + 1       # an engraving's soft shoulder goes with its strokes
        strokes = cv2.dilate(strokes, np.ones((g, g), np.uint8), iterations=1)
        report_mask |= strokes
        if not strokes.any():
            continue
        if mk.get("fill") == "fsr":
            # a patterned face (F01's tortoise): rows rebuilt from their two ends streaked the
            # pattern; frequency-selective reconstruction (opencv-contrib) carries its blobs through
            # the strokes instead
            ys, xs = np.nonzero(strokes)
            pad = 48
            ya, yb = max(0, ys.min() - pad), min(out.shape[0], ys.max() + pad + 1)
            xa, xb = max(0, xs.min() - pad), min(out.shape[1], xs.max() + pad + 1)
            sub = np.ascontiguousarray(cv2.cvtColor(out[ya:yb, xa:xb], cv2.COLOR_RGB2BGR))
            dst = sub.copy()
            cv2.xphoto.inpaint(sub, (1 - strokes[ya:yb, xa:xb]).astype(np.uint8), dst, cv2.xphoto.INPAINT_FSR_BEST)
            out[ya:yb, xa:xb] = cv2.cvtColor(dst, cv2.COLOR_BGR2RGB)
        elif mk.get("fill") == "smooth":
            # a defocused part, every edge of it soft (a print seen through a far lens, running into
            # the rim's blur): the smoothest surface through the patch's border, grain added back
            out = harmonic_fill(out, strokes > 0)
        elif mk.get("temple"):
            out = fill_along_temple(out, strokes, mk["temple"], region_xy, texture_dx=mk.get("texture_dx"),
                                    texture_from=mk.get("texture_from"), side=mk.get("side"))
        elif mk.get("axis") is not None:
            out = inpaint_along(out, strokes, mk["axis"])
        else:
            total |= strokes          # small marks: plain inpainting, all at once below
    if total.any():
        out = cv2.inpaint(out, total, 6, cv2.INPAINT_NS)
        noise = np.random.default_rng(3).normal(0, 1.4, out.shape)   # grain back, as along the temples
        out = np.where(total[..., None] > 0, np.clip(out + noise, 0, 255), out).astype(np.uint8)
    return out.astype(np.float32) / 255.0, report_mask


def harmonic_fill(img, mask, grain=1.4, seed=13):
    """Fill `mask` (uint8 RGB image) with the solution of Laplace's equation that meets the image
    all round the mask's border: the smoothest fill there is, with no edge of its own."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.linalg import spsolve
    h, w = mask.shape
    ys, xs = np.nonzero(mask)
    n = len(ys)
    idx = -np.ones(mask.shape, np.int64)
    idx[ys, xs] = np.arange(n)
    src = img.astype(np.float64)
    rows, cols, vals = [np.arange(n)], [np.arange(n)], [np.zeros(n)]
    b = np.zeros((n, img.shape[2]))
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        ny, nx = ys + dy, xs + dx
        ok = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
        vals[0][ok] += 1                                   # the pixel's own weight: its neighbors
        inside = np.zeros(n, bool)
        inside[ok] = mask[ny[ok], nx[ok]]
        rows.append(np.nonzero(inside)[0]); cols.append(idx[ny[inside], nx[inside]])
        vals.append(-np.ones(int(inside.sum())))
        edge = ok & ~inside
        b[edge] += src[ny[edge], nx[edge]]
    L = coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()
    sol = np.stack([spsolve(L, b[:, c]) for c in range(img.shape[2])], -1)
    sol += np.random.default_rng(seed).normal(0, grain, sol.shape)
    out = img.copy()
    out[ys, xs] = np.clip(sol, 0, 255).astype(np.uint8)
    return out


def fill_along_temple(img, mask, temple, region_xy, grain=1.4, seed=11, texture_dx=None, texture_from=None,
                      side=None):
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
    them), for a patch longer than the clean face beside it.
    `side` ("left" or "right") carries every row on from that end only, as the mean of its last 16
    clean pixels there, smoothed across rows: a print seen through a far lens runs into the rim at
    its other end, and rows interpolated between the two ends took the rim's darkness in (F01's
    side view)."""
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
        if side:
            src = good[good < bad.min()][-16:] if side == "left" else good[good > bad.max()][:16]
            if not len(src):
                continue
            R[r, bad] = ends[r, src].mean(0)
            continue
        for ch in range(R.shape[2]):
            R[r, bad, ch] = np.interp(bad, good, ends[r, good, ch])
    if side:
        # one row's mean differs a little from the next's: smoothed across the rows, in the patch only
        R = np.where(Rm[..., None], cv2.GaussianBlur(R, (1, 9), sigmaX=0, sigmaY=1.5), R)
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
        span = {"left": idx - left, "right": right - idx}.get(side, np.minimum(idx - left, right - idx))
        ws = np.clip(span / 12.0, 0, 1)[..., None]
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


def along_outline(v, d_s, half=6, sig=3.0):
    """`v` smoothed along the lens's outline: over about +-`sig` px along the iso-lines of the signed
    distance `d_s` from it, so each pixel is averaged with others at its own distance from the edge."""
    ds = cv2.GaussianBlur(d_s.astype(np.float32), (0, 0), 1.5)
    gx = cv2.Sobel(ds, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(ds, cv2.CV_32F, 0, 1, ksize=3)
    g = np.maximum(np.hypot(gx, gy), 1e-6)
    tx, ty = -gy / g, gx / g
    del gx, gy, g, ds
    h, w = v.shape
    xx = np.broadcast_to(np.arange(w, dtype=np.float32)[None, :], (h, w))
    yy = np.broadcast_to(np.arange(h, dtype=np.float32)[:, None], (h, w))
    v = v.astype(np.float32)
    acc = np.zeros((h, w), np.float32)
    total = 0.0
    for o in range(-half, half + 1):
        wo = float(np.exp(-0.5 * (o / sig) ** 2))
        acc += wo * cv2.remap(v, (xx + o * tx).astype(np.float32), (yy + o * ty).astype(np.float32),
                              cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        total += wo
    return acc / total


def edge_tube(ly, A_box, conf, zone, d_in, d_out, U=18.0, du=0.5, half=40):
    """The lens's edge along its whole outline. Point by point along SAM's outline, how far the edge
    as read (`A_box`) lies from it, along the outline's normal; smoothed with a running median over
    about 80 px of outline, from the points where the reading could tell lens from frame (`conf`),
    and carried across the stretches where it could not. Read pixel by pixel, the edge went wherever
    each pixel's reading took it: crumbs where the texture seen through a lens met the rim (F02's
    and F04's details), a step where the reading lapsed and the masks' edge came back, a few pixels
    off (F04's front), a blob where a dark reflection or a filled one touched the rim (F08's front).
    Returns (lo, hi, g, up) for the lens's box: bounds for each pixel's opacity, a tube about 2 px
    either side of that smoothed edge where it is sharp, wider where it is soft (and up to 3 px more
    outwards where the reading is sure: a sharp corner that SAM rounded), how much they apply (none
    where the edge is not read: clear tent beside the lens, the box's border), each pixel's signed
    distance from the outline (+ inside), and the outline's numbers for --debug. None when too
    little of the outline could be read."""
    import warnings
    from scipy import ndimage as ndi
    from scipy.special import ndtr
    h, w = ly.shape
    cs, _ = cv2.findContours(ly.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return None
    c = max(cs, key=len)[:, 0, :].astype(np.float64)
    n = len(c)
    if n < 200:
        return None
    P = np.stack([ndi.gaussian_filter1d(c[:, 0], 2, mode="wrap"),
                  ndi.gaussian_filter1d(c[:, 1], 2, mode="wrap")], 1)
    tg = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    tg /= np.maximum(np.hypot(tg[:, 0], tg[:, 1]), 1e-9)[:, None]
    nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)

    def prof(img, uu):
        X = (P[:, :1] + uu[None] * nrm[:, :1]).astype(np.float32)
        Y = (P[:, 1:] + uu[None] * nrm[:, 1:]).astype(np.float32)
        return cv2.remap(img.astype(np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE), X, Y

    if prof(ly.astype(np.float32), np.array([2.0], np.float32))[0].mean() < 0.5:
        nrm = -nrm                                    # the normal points into the lens
    u = np.arange(-U, U + du / 2, du, dtype=np.float32)
    Ap, X, Y = prof(A_box, u)
    neg = u < 0
    # each side taken up to its first clear reading: past it on the frame's side may lie the tent
    # (a thin rim), past it on the lens's side the texture seen through the lens
    fr = np.maximum.accumulate(Ap[:, neg][:, ::-1], axis=1)[:, ::-1]
    le = np.minimum.accumulate(Ap[:, ~neg], axis=1)
    Am = np.concatenate([fr, le], 1)
    e = ((Am[:, neg] - 1).sum(1) + Am[:, ~neg].sum(1)) * du          # + : the frame reaches into the mask
    s = (Am * (1 - Am)).sum(1) * du * np.sqrt(np.pi)                  # the edge's blur (an erf's sigma)
    near = np.abs(u[None] - e[:, None]) <= 2
    cnt = np.maximum(near.sum(1), 1)
    wc = (prof(conf, u)[0] * near).sum(1) / cnt
    zc = (prof(zone.astype(np.float32), u)[0] * near).sum(1) / cnt
    inb = (X.min(1) >= 1) & (X.max(1) <= w - 2) & (Y.min(1) >= 1) & (Y.max(1) <= h - 2)
    applies = (zc > 0.5) & inb & (Ap[:, neg].max(1) >= 0.8)
    wv = wc * applies
    ok = wv >= 0.5
    if ok.mean() < 0.1:
        return None
    idx = (np.arange(n)[:, None] + np.arange(-half, half + 1)[None]) % n
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)              # windows with no reading
        med = np.nanmedian(np.where(ok[idx], e[idx], np.nan), axis=1)
        smed = np.nanmedian(np.where(ok[idx], s[idx], np.nan), axis=1)
    del idx

    def carried(m):                                   # across the stretches with no reading
        good = ~np.isnan(m)
        i = np.arange(n)
        xi = np.concatenate([i[good] - n, i[good], i[good] + n])
        return np.interp(i, xi, np.tile(m[good], 3))

    e_s = ndi.gaussian_filter1d(carried(med), 5, mode="wrap")
    s_s = np.clip(ndi.gaussian_filter1d(carried(smed), 5, mode="wrap"), 0.7, 8.0)
    w_s = np.clip(ndi.gaussian_filter1d(wv, 3, mode="wrap"), 0, 1)
    g = ndi.gaussian_filter1d(applies.astype(np.float64), 3, mode="wrap")
    # each pixel takes the outline point nearest it
    cm = np.zeros((h, w), bool)
    ci = np.zeros((h, w), np.int32)
    cx, cy = c[:, 0].astype(int), c[:, 1].astype(int)
    cm[cy, cx] = True
    ci[cy, cx] = np.arange(n)
    _, (iy, ix) = ndi.distance_transform_edt(~cm, return_indices=True)
    j = ci[iy, ix]
    del cm, ci, iy, ix
    up = np.where(ly, d_in - 1, -d_out).astype(np.float32)
    sj = s_s[j].astype(np.float32)
    st = 1.25 * sj + 0.25
    tol = 1.25 + 0.5 * sj                             # a soft edge's place is soft too
    es = e_s[j].astype(np.float32)
    lo = ndtr((es - tol - 2.75 * w_s[j] - up) / st).astype(np.float32)
    hi = ndtr((es + tol - up) / st).astype(np.float32)
    gp = (g[j] * (np.abs(up) <= U - 1)).astype(np.float32)
    return lo, hi, gp, up, {"edge_c": c, "edge_e": e, "edge_es": e_s, "edge_w": wv}


def read_lens_edge(lm, holes, A, F, Tf, lin_clean, srgb_clean, back_s, debug=None, kept=None):
    """The lens meets the frame along a line the masks draw in whole pixels: the lens's hole is cut
    by its SAM mask (shrunk a little), the rim by the model's alpha, which calls a dark lens solid.
    Switched there from lens (A 0) to frame (A 1), a light lens's edge ran as a staircase (F03's
    yellow, IMG_3327), and a dark lens kept a band of its old self along the rim, darker than the
    lens on the new stage (F04's front). Within a few pixels of that line each pixel's opacity is
    read from the picture instead: how far it lies from the lens's own color, just inside, towards
    the frame's, a little further out. So each pixel keeps its own look plus its share of the
    lens's change (the clean tint on the new stage). A pixel past the lens's color on the side away
    from the frame's (a highlight along a black rim) is frame; where lens and frame are too alike to
    tell (a dark lens in a black rim), the line is only softened. One lens (`lm`, its whole SAM
    mask: a dark lens's last few pixels are "solid") at a time, in its own box; A, F and Tf change
    in place. `lin_clean` is the picture with the lenses' reflections and dust already out (a lens's
    bright corner, taken for glare, left the edge beside it unread, its rim's soft edge over bare
    stage: the F03 hero), the lens's own edge kept as photographed. Nothing is read where the band
    the lens's color comes from is not the lens (SAM's mask run into a dark rim), or where clear tent
    lies nearer than the lens. `kept`: what a light lens keeps behind it (`keep_behind`), never taken
    for the lens's own color. Returns how many pixels were read."""
    from scipy import ndimage as ndi
    ys_, xs_ = np.nonzero(lm)
    pad = 24
    by0, by1 = max(0, ys_.min() - pad), min(A.shape[0], ys_.max() + pad + 1)
    bx0, bx1 = max(0, xs_.min() - pad), min(A.shape[1], xs_.max() + pad + 1)
    sl = (slice(by0, by1), slice(bx0, bx1))
    ly, hz, Az = lm[sl], holes[sl], A[sl].copy()
    d_in = ndi.distance_transform_edt(ly).astype(np.float32)
    d_out = ndi.distance_transform_edt(~ly).astype(np.float32)
    # the lens's own color is read 5 to 12 px inside its mask: SAM's mask can reach a few pixels
    # past the lens's real edge, and the soft edge there was taken for lens (a staircase along the
    # bottom of the F03 hero's lenses)
    inner = ly & hz & (d_in > 4.5) & (d_in <= 12)
    # and from the lens itself, not a temple seen through a light lens just inside its rim: read
    # against the temple, the strip of lens between it and the rim was taken for a highlight on the
    # rim, a grey dash under F01's front rim
    kb = kept[sl] if kept is not None else np.zeros(ly.shape, bool)
    if (inner & ~kb).sum() >= 200:
        inner &= ~kb
    outer = ~hz & (d_out > 6) & (d_out <= 14) & (Az > 0.9)
    # frame-side: what is frame at least in part (a lens's edge against the tent stays), 6 px out,
    # and 12 px where the frame is still soft: SAM can stop 6 px short of a light lens's edge, and
    # past the old reach the rim's soft edge lay over bare stage, a grey line (the F03 hero)
    soft = np.clip(2 * cv2.GaussianBlur((Az < 0.95).astype(np.float32), (0, 0), 1.5), 0, 1)
    reach = (6 + 6 * soft).astype(np.float32)
    # and what the model took for tent but is not: a light lens's bevel, yellow beside the yellow
    # lens, past SAM's mask (the F03 hero's corner), stayed see-through with bare stage behind it
    Lb, Lp = lum(back_s[sl]), lum(lin_clean[sl])
    mx_, mn_ = lin_clean[sl].max(-1), lin_clean[sl].min(-1)
    tentlike = (np.abs(Lp / np.maximum(Lb, 1e-5) - 1) < 0.12) & ((mx_ - mn_) / np.maximum(mx_, 1e-4) < 0.15)
    del Lb, Lp, mx_, mn_
    # but not where clear tent lies nearer than the lens: the frame's soft edge there lies over the
    # tent, not the lens, and read against the lens it would keep the tent's old grey in the new
    # stage. Faded out over 3 px.
    clear = ~ly & ~hz & (Az < 0.05) & tentlike
    by_lens = (np.clip((ndi.distance_transform_edt(~clear) - d_out + 2) / 3, 0, 1).astype(np.float32)
               if clear.any() else np.ones(ly.shape, np.float32))
    del clear
    zone = (ly & (d_in <= 4.5)) | (~hz & (d_out <= reach) & ((Az > 0.05) | ~tentlike) & (by_lens > 0))
    if not (inner.any() and outer.any() and zone.any()):
        return 0
    d_i, idx_i = ndi.distance_transform_edt(~inner, return_indices=True)
    zone &= d_i <= 12
    del d_i
    d_o, idx_o = ndi.distance_transform_edt(~outer, return_indices=True)
    zone &= d_o <= 12

    def spread(v, m, idx):
        # each pixel takes the value at the nearest pixel of `m`, smoothed along `m` first and after
        # (taken as is, the nearest pixel's value came in blocks, which the edge then showed)
        mf = m.astype(np.float32)
        den = cv2.GaussianBlur(mf, (0, 0), 2)
        vs = cv2.GaussianBlur(v * mf[..., None], (0, 0), 2) / np.maximum(den, 1e-6)[..., None]
        return cv2.GaussianBlur(vs[idx[0], idx[1]].astype(np.float32), (0, 0), 2.5)

    Lc = lin_clean[sl].astype(np.float32)
    Lv, Tz = spread(Lc, inner, idx_i), np.clip(spread(Tf[sl], inner, idx_i), 0, 1)
    del idx_i
    # SAM's mask can reach several pixels past the lens into a dark rim (F05's detail, F08's
    # three-quarter, the F03 front's yellow lens bottom): the band the lens's color is read from is
    # then partly rim, and read against it, the rim came out as lens, lit in blocks by the lens's
    # change. Where that band differs from the lens 12 to 30 px in by more than about half, the lens
    # is read from there instead. And the reading reaches 12 px in, to take the rim back out of the
    # mask: there only what reads as rim, joined to the edge, changes; the lens stays as cleaned.
    deep = ly & hz & (d_in > 12) & (d_in <= 30)
    if (deep & ~kb).sum() >= 200:
        deep &= ~kb
    trust = np.ones(ly.shape, np.float32)
    if deep.any():
        _, idx_d = ndi.distance_transform_edt(~deep, return_indices=True)
        Ld, Td = spread(Lc, deep, idx_d), np.clip(spread(Tf[sl], deep, idx_d), 0, 1)
        del idx_d
        r = lum(Lv) / np.maximum(lum(Ld), 1e-6)
        trust = (np.clip((r - 0.45) / 0.15, 0, 1) * np.clip((2.2 - r) / 0.4, 0, 1)).astype(np.float32)
        tw = trust[..., None]
        Lv, Tz = (tw * Lv + (1 - tw) * Ld).astype(np.float32), (tw * Tz + (1 - tw) * Td).astype(np.float32)
        del Ld, Td, tw, r
    deeper = ly & hz & ~zone & (d_in <= 12) & (d_o <= 26)
    base = zone & ly
    del deep, d_o
    lp, ll = lum(Lc), lum(Lv)
    # The reading uses the picture evened out along the edge, with the pixels beside each one at
    # its own distance from the outline: read pixel by pixel, the texture seen through a lens (the
    # tent's dimpled wall, F04's and F02's details) came out as crumbs along the edge, and a dark line
    # along it came and went with the noise, in dashes. Lines along the edge keep their profile.
    d_s = np.where(ly, d_in, -d_out)
    Lc_s = np.stack([along_outline(Lc[..., c], d_s) for c in range(3)], -1)
    lp_s = lum(Lc_s)
    # the frame's own color: the larger of the band's two halves, darker and lighter than its local
    # average, not the average itself: a thin highlight along a black rim's inner edge, averaged
    # in, made the rim look like the lens, and the edge went unread (F06's shield)
    lo_ = cv2.GaussianBlur(lp, (0, 0), 1.0)

    def local_mean(m):
        mf = m.astype(np.float32)
        c = cv2.GaussianBlur(mf, (0, 0), 4)
        return cv2.GaussianBlur(lo_ * mf, (0, 0), 4) / np.maximum(c, 1e-6), c

    m_all, _ = local_mean(outer)
    m_lo, c_lo = local_mean(outer & (lo_ <= m_all))
    m_hi, c_hi = local_mean(outer & (lo_ > m_all))
    # weighted towards the larger half, not switched to it: switched where the two halves were about
    # as large, the frame's color jumped, and the edge's reading with it, in blocks (F05's and F04's
    # details)
    w_lo = np.clip(0.5 + 2.5 * (c_lo - c_hi) / np.maximum(c_lo + c_hi, 1e-6), 0, 1)
    lr = cv2.GaussianBlur((w_lo * m_lo + (1 - w_lo) * m_hi)[idx_o[0], idx_o[1]].astype(np.float32), (0, 0), 2.5)
    # and in color, for pixels the smoothed edge (edge_tube, below) gives back to the frame, with the
    # frame's own opacity there (a dark grey rim the model calls 0.96 opaque shows the stage a little:
    # given back at 1, a strip of it went black, F09's hero)
    Fr = spread(F[sl], outer, idx_o)
    Ar = spread(np.repeat(Az[..., None], 3, -1), outer, idx_o)[..., 0]
    del idx_o, m_all, m_lo, c_lo, m_hi, c_hi, lo_, w_lo
    # the picture's noise on the lens: a difference within it counts for nothing. It is about even
    # in the picture's encoded terms, so in linear light it is much smaller on a dark lens than on a
    # light one: measured once, scaled to each pixel's level (one figure for all levels gave the
    # dark top of F06's shield the bright part's noise, and no edge at all)
    se = lin_to_srgb(np.clip(ll, 0, 1))
    n = (2.0 * grain_of(srgb_clean[sl], inner) *
         np.where(se <= 0.04045, 1 / 12.92, 2.4 / 1.055 * ((se + 0.055) / 1.055) ** 1.4)).astype(np.float32)
    gap = np.abs(lr - ll)
    t = (lp_s - ll) * np.sign(lr - ll)              # towards the frame's color (+) or away (-)
    A_to = np.clip((t - n) / np.maximum(gap - n, 1e-6), 0, 1)
    A_away = np.clip((-t - n) / (0.3 * ll + 2 * n + 1e-6), 0, 1)
    # one pixel's reading against its neighbors': a lone outlier (noise on a dark lens by a dark
    # rim) showed as a dark fleck along the edge (F02's detail)
    A_e = cv2.GaussianBlur(cv2.medianBlur(np.maximum(A_to, A_away).astype(np.float32), 3), (0, 0), 0.7)
    k = (np.clip((gap - 3 * n) / (3 * n + 1e-6), 0, 1) *
         np.clip((gap / np.maximum(np.maximum(ll, lr), 1e-6) - 0.2) / 0.2, 0, 1)).astype(np.float32)
    # Where the reading can't tell lens from frame pixel by pixel (a dark lens's darkest stretch
    # beside a black rim, the difference within the picture's noise), it reads the picture smoothed
    # over a few pixels, where the noise is a third as large; only where that can't tell either does
    # the edge stay as the masks drew it. Falling back to the masks straight away, the rim inside the
    # lens's mask took the lens's clean tint in blocks wherever the reading lapsed (F05's
    # three-quarter and detail, F04's). The two readings' trust is smoothed too, so they hand over
    # gradually.
    n2 = n / 3
    t2 = (cv2.GaussianBlur(lp, (0, 0), 2.0) - ll) * np.sign(lr - ll)
    A_e2 = np.maximum(np.clip((t2 - n2) / np.maximum(gap - n2, 1e-6), 0, 1),
                      np.clip((-t2 - n2) / (0.3 * ll + 2 * n2 + 1e-6), 0, 1)).astype(np.float32)
    k2 = (np.clip((gap - 3 * n2) / (3 * n2 + 1e-6), 0, 1) *
          np.clip((gap / np.maximum(np.maximum(ll, lr), 1e-6) - 0.2) / 0.2, 0, 1)).astype(np.float32)
    k, k2 = cv2.GaussianBlur(k, (0, 0), 2.0), cv2.GaussianBlur(k2, (0, 0), 2.0)
    conf = (k + (1 - k) * k2).astype(np.float32)      # either reading could tell
    A_fb = A_e2 * k2 + cv2.GaussianBlur(Az, (0, 0), 0.7) * (1 - k2)
    A_z = (A_e * k + A_fb * (1 - k)).astype(np.float32)
    del t2, A_e2, k2, A_fb
    # the rim taken back out of the lens's mask, 4.5 to 12 px in: what reads as rim there and is
    # joined to the edge through more of it (a dark speck further in stays lens)
    # and only what reads as the frame's color or past it (the rim): something darker than the
    # lens beside a lighter frame (a shadow inside F02's lens by the rim) is lens, not rim, and
    # carved out it stood as a dark ring
    toward = cv2.GaussianBlur((A_to >= A_away).astype(np.float32), (0, 0), 1.5) > 0.5
    # A dark band seen through the lens (a temple behind it: F04's and F02's fronts, the F06 hero's
    # shield top) can run into the edge too. It reaches much further in than a rim inside the mask
    # ever does (at most about 16 px, a defocused rim's blur where the mask overshoots it), so it is
    # lens: not carved, and the edge beside it stays as the masks drew it, not read as rim (a dark
    # shelf or a step along the edge where it met the rim). Only near where it runs deep: a rim's
    # blur joined to it along the edge stays rim (taken whole, F04's and F05's details lost their
    # soft edges to a hard line along the mask).
    lab_b, n_b = ndi.label(ly & hz & (d_in > 4.5) & (d_in <= 40) & (A_z > 0.3) & toward)
    through = np.zeros(ly.shape, bool)
    if n_b:
        deepest = np.asarray(ndi.maximum(d_in, lab_b, np.arange(1, n_b + 1)))
        through = np.isin(lab_b, 1 + np.nonzero(deepest > 22)[0])
        core = cv2.dilate((through & (d_in > 22)).astype(np.uint8),
                          cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51))) > 0
        through &= core
        del core
    del lab_b
    beside = cv2.dilate(through.astype(np.uint8), np.ones((13, 13), np.uint8)) > 0
    carve = ndi.binary_propagation(base, mask=base | (deeper & (A_z > 0.15) & toward & ~through)) & deeper
    # a band along the edge, not a thin line running into it (a reflection inside F02's lens, left
    # as a spike where it met the rim)
    carve &= cv2.morphologyEx((carve | base).astype(np.uint8), cv2.MORPH_OPEN,
                              cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0
    zone |= carve
    del base, deeper
    # The frame's part of each pixel is the picture's own; the lens's part is the cleaned lens (its
    # tint and grain, where the lens's hole is), not the picture's texture seen through it: kept, the
    # old texture showed as a band along the edge. So what each pixel keeps of the picture goes from
    # its own look where it is frame to the look evened out along the edge where it is lens.
    Lc_mix = A_z[..., None] * Lc + (1 - A_z[..., None]) * Lc_s
    F_z = np.clip((Lc_mix - (1 - A_z[..., None]) * Lv) / np.maximum(A_z[..., None], 0.02), 0, 1)
    # (the cleaned lens's own pixels where the hole is, unless much darker than the lens beside them:
    # a light lens keeps what is darker behind it, and the rim's blur inside the mask was kept so,
    # and showed as a dark line along the edge, the F03 hero's yellow gone olive-black)
    Tl = np.where(((ly & hz) & (lum(Tf[sl]) >= 0.85 * lum(Tz)))[..., None], Tf[sl], Tz)
    del Lc_mix, Lc_s
    # on the frame's side the reading fades out over its last 3 px, back to the frame as it was:
    # cut off square, it left a step across a soft bevel (F06's shield). Blended as the picture is
    # made (frame over, lens times stage), so the layers stay one picture.
    wz = np.where(ly, 1.0, np.clip((reach - d_out) / 3, 0, 1) * by_lens).astype(np.float32)
    wz = np.where(carve, np.clip((A_z - 0.15) / 0.3, 0, 1), wz).astype(np.float32)
    wz = np.where(ly & beside & ~carve, 0, wz).astype(np.float32)
    Ab = wz * A_z + (1 - wz) * Az
    P = wz[..., None] * F_z * A_z[..., None] + (1 - wz[..., None]) * F[sl] * Az[..., None]
    Q = wz[..., None] * (1 - A_z[..., None]) * Tl + (1 - wz[..., None]) * (1 - Az[..., None]) * Tf[sl]
    Fb = np.clip(P / np.maximum(Ab[..., None], 1e-4), 0, 1)
    Tb = np.clip(Q / np.maximum(1 - Ab[..., None], 1e-4), 0, 1)
    Tb = np.where((1 - Ab[..., None]) > 1e-4, Tb, 1)
    A[sl] = np.where(zone, Ab, Az)
    F[sl] = np.where(zone[..., None], Fb, F[sl])
    Tf[sl] = np.where(zone[..., None], Tb, Tf[sl])
    # Then the edge as one line along the outline (edge_tube): each pixel's opacity is kept within a
    # pixel or two of the edge smoothed along it. What that gives back to the frame takes the
    # frame's color beside it; what it gives to the lens, the cleaned lens. More frame only on the
    # lens's side of SAM's outline, or where the model has solid frame: past a thin rim lies the tent.
    tube = edge_tube(ly, A[sl], conf * wz * zone, zone, d_in, d_out)
    tube_dbg = {}
    if tube is not None:
        lo, hi, gp, up, tube_dbg = tube
        # and, on a light lens that keeps what is behind it, not beside a band seen through it
        # (above): where a temple seen through the lens starts at the rim, it starts there (held to
        # the smoothed line, its first few pixels went and the rest floated free: F01's
        # three-quarter). A dark lens drops what is behind it, and the edge there is smoothed like
        # any other (held, the masks' line showed as a nick where F08's far temple met the rim).
        if kb.any():
            gp = gp * (1 - cv2.GaussianBlur(beside.astype(np.float32), (0, 0), 2))
        lo = np.where((up >= -2) | (Az >= 0.9), lo * np.clip(Ar, 0, 1), 0)
        A0 = A[sl].copy()
        A1 = (A0 + (np.clip(A0, lo, hi) - A0) * gp).astype(np.float32)
        more = np.clip(A1 - A0, 0, None)[..., None]
        less = np.clip(A0 - A1, 0, None)[..., None]
        F[sl] = np.where(more > 0, (A0[..., None] * F[sl] + more * Fr) / np.maximum(A1[..., None], 1e-4), F[sl])
        Tf[sl] = np.where(less > 0, ((1 - A0[..., None]) * Tf[sl] + less * Tl) /
                          np.maximum(1 - A1[..., None], 1e-4), Tf[sl])
        A[sl] = A1
        tube_dbg["tube"] = A1 - A0
        del lo, hi, gp, up, A0, A1, more, less
    if debug is not None:
        np.savez_compressed(debug / f"lens_edge_{by0}_{bx0}.npz", zone=zone, A_read=A_e, k=k, noise=n,
                            lens=ll, frame=lr, pixel=lp, A_edge=A_z, weight=wz, before=Az, trust=trust,
                            by_lens=by_lens, carve=carve, through=through, smoothed=lp_s, conf=conf,
                            **tube_dbg)
    return int(zone.sum())


def grow_soft_edge(seed, light, A_s, steps=45, tol=0.05, fade=12):
    """From `seed` out through `light`, only ever darker (the physical opacity A_s not falling by
    more than `tol` below the grown pixel beside it), at most `steps` px: the soft edge between an
    open gap and the frame round it, not a light part of the frame beyond it. Returns each grown
    pixel's weight: 1, fading to 0 over the last `fade` steps where the growth runs to its limit
    (stopped square there, mid-way through a soft edge, it left a hard stepped line: F03's side
    view, the gap's lower corner)."""
    grown = seed.copy()
    when = np.zeros(seed.shape, np.int16)
    A = A_s.astype(np.float32)
    k = np.ones((3, 3), np.uint8)
    for i in range(1, steps + 1):
        nb_min = cv2.erode(np.where(grown, A, np.float32(9)), k)
        cand = (cv2.dilate(grown.astype(np.uint8), k) > 0) & ~grown & light & (A >= nb_min - tol)
        if not cand.any():
            break
        grown |= cand
        when[cand] = i
    w = np.clip((steps + 1 - when.astype(np.float32)) / fade, 0, 1)
    return np.where(grown & ~seed, w, 0).astype(np.float32)


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
    # the frame's shadow joins the frame: darkening that doesn't (a speck on the tent's fabric, in
    # the zone where shadow can fall) is not shadow and would sit on the stage as a smudge (F06's
    # detail). Kept: what can be reached from the frame without crossing lighter tent.
    from skimage.morphology import reconstruction
    D = np.clip(1 - S, 0, 1).astype(np.float32)
    hs, ws = D.shape[0] // 4, D.shape[1] // 4
    Dq = cv2.resize(D, (ws, hs), interpolation=cv2.INTER_AREA)
    seed = cv2.resize(cv2.dilate(obj.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))),
                      (ws, hs), interpolation=cv2.INTER_NEAREST) > 0
    Dr = reconstruction(np.where(seed, Dq, 0), Dq, method="dilation").astype(np.float32)
    Dr = cv2.resize(Dr, (D.shape[1], D.shape[0]), interpolation=cv2.INTER_LINEAR)
    S = (1 - np.minimum(D, Dr + 0.004)).astype(np.float32)
    # keep only the frame's own shadow: fade S to 1 between 150 and 450 px from the frame, so the
    # stage is one even color everywhere else (no tent gradient, no seams at the crop edge)
    d = cv2.distanceTransform((1 - obj).astype(np.uint8), cv2.DIST_L2, 5)
    fade = np.clip((450 - d) / 300, 0, 1) * zone
    hh, ww = S.shape
    yy = np.arange(hh, dtype=np.float32)[:, None]
    xx = np.arange(ww, dtype=np.float32)[None, :]
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
    # An open gap is see-through only past its soft edge: the edge itself is the frame's, with the
    # rest of the frame's edges (below). Taken as transmission right up to the solid rim, it was
    # scaled to the new stage while the rim beside it was not, and the switch between the two ran
    # ragged along the rim (F08's bridge).
    holes = lens_in | (filled & ~solid & (alpha_m <= 0.05))
    # and a lens runs right up to the solid rim: the band its mask was shrunk by would otherwise go
    # to the model, which calls a light lens tent, so it showed as a pale line of bare stage
    # between lens and rim (F01's blue)
    lens_band = lens & ~solid & ~lens_in
    holes |= lens_band
    back = B * S[..., None]                          # the tent behind, in the frame's shadow
    # the old marks come off first, so a print seen through a lens (the inner face of the far
    # temple, F01) goes from the lens's transmission too
    srgb_clean, mark_mask = remove_marks(srgb, cfg.get("marks", []), rx)
    report["marks_px"] = int(mark_mask.sum())
    lin_clean = srgb_to_lin(srgb_clean)
    Tc = np.clip(lin_clean / (back + 1e-5), 0, 1).astype(np.float32)
    Tc0 = Tc.copy()                                 # as measured, before the clean-up below
    T = np.clip(lum(lin_clean) / (lum(back) + 1e-5), 0, 1).astype(np.float32)
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
    # the lens's own structure that would pass for dust (the dark line where the F03 hero's lens
    # turns into its bevel by the bridge, cleaned away inside SAM's mask and kept past it, ragged)
    keep = np.zeros(T.shape, np.uint8)
    for poly in lc.get("keep", []):
        cv2.fillPoly(keep, [np.array([[x - x0, y - y0] for x, y in poly], np.int32)], 1)
    spots &= keep == 0
    # The lens's own edge is not dust: the rim's dark inner edge, a few pixels inside the hole,
    # passes for a dark speck; and on a lens seen at a steep angle (`as_shot`, below) the bright
    # facet along its edge passes for a reflection. Filled from the lens beside them, such edges
    # came back flat, cut square along the mask's steps, with a dark block or a notch where a
    # filled stretch ended (F08's and F05's three-quarter views, F06's three-quarter and detail).
    # What reaches to within 4 px of the lens's outline stays as photographed in the picture the
    # lens's edge is read from (`seen`, below); specks and lint on the lens's face still go, and a
    # clean lens's fit still leaves all of them out.
    near_rim = ~(cv2.erode(lens.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0)

    def reaching_rim(m):
        lab_r, _ = ndi.label(m, structure=np.ones((3, 3), bool))
        hit = np.unique(lab_r[m & near_rim])
        return np.isin(lab_r, hit[hit > 0])

    rim_sp = reaching_rim(dust & holes)
    if lc.get("as_shot"):
        rim_sp |= reaching_rim((glare | dust) & holes)
    rim_sp = (cv2.dilate(rim_sp.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & spots
    report["rim_spots_kept_px"] = int(rim_sp.sum())
    del near_rim
    glare_sp = spots & (cv2.dilate((glare & holes).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
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
        fill = np.stack([smooth_fill(Tc[..., c], paint, support) for c in range(3)], -1)
        stage_l = float(lum(hex_lin(STAGE_HEX)))
        fill = add_grain(fill, lens_grain(np.random.default_rng(5), grain_of(srgb_clean, ring),
                                          stage_l * lum(fill), stage_l))
        Tc = np.where(paint[..., None], fill, Tc).astype(np.float32)
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
    kept_behind = np.zeros(T.shape, bool)
    if mode:
        deg = 0 if mode == "flat" else 2
        lab, nl = ndi.label(lens_in)
        rng2 = np.random.default_rng(9)
        grains = []
        for i in range(1, nl + 1):
            core = lab == i
            if core.sum() < 2000:
                continue
            li = core | (cv2.dilate(core.astype(np.uint8), np.ones((13, 13), np.uint8)) > 0) & lens_band
            fitimg = Tc.copy()
            for c in range(3):
                fitimg[..., c] = smooth_fill(Tc[..., c], li, core & ~spots, degree=deg)
            if lc.get("tint"):
                # the founder's exception to the rule above (00-decisions.md #38): F04's close-up,
                # where the lens, seen at a steep angle with the tent's light on it, measures about
                # three times lighter than F04's lens is; it takes the front view's measured tint
                fitimg = np.broadcast_to(np.asarray(lc["tint"], np.float32), Tc.shape).copy()
            stage_l = float(lum(hex_lin(STAGE_HEX)))
            grain = grain_of(srgb_clean, core & ~spots)
            new = add_grain(fitimg, lens_grain(rng2, grain, stage_l * lum(fitimg), stage_l))
            grains.append(round(grain * 255, 2))
            if lc.get("keep_behind"):
                ratio = lum(Tc) / np.maximum(lum(fitimg), 1e-4)
                lo, hi = lc.get("behind_ratio", [0.5, 0.75])
                m = np.clip((hi - ratio) / (hi - lo), 0, 1).astype(np.float32)
                # A reflection or speck takes what is kept round it, well inside the lens: on a temple
                # seen through the lens it goes into the temple (F01's three-quarter: specks there
                # came out as pale dots of lens tint); on the lens itself, or by its rim, it is never
                # kept (a bright corner taken for glare stayed half-kept, F03's hero).
                core_in = cv2.erode(core.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
                deep_in = core_in & ~glare_sp
                di = deep_in.astype(np.float32)
                m_nb = cv2.GaussianBlur(m * di, (0, 0), 4) / np.maximum(cv2.GaussianBlur(di, (0, 0), 4), 1e-3)
                m = np.where(glare_sp, np.where(cv2.GaussianBlur(di, (0, 0), 4) > 0.2, np.clip(m_nb, 0, 1), 0), m).astype(np.float32)
                del core_in, deep_in, di, m_nb
                # softened within the lens only: past its edge nothing is kept (the fit is the
                # picture there), and blurred in, that left a pale line of lens tint along the rim
                # where a temple is seen through the lens right up to it (F01's far lens, IMG_3556)
                lf = li.astype(np.float32)
                m = cv2.GaussianBlur(m * lf, (0, 0), 1.5) / np.maximum(cv2.GaussianBlur(lf, (0, 0), 1.5), 1e-6)
                new = new * (1 - m[..., None]) + Tc * m[..., None]
                kept_behind |= li & (m > 0.5)
            Tc[li] = np.clip(new[li], 0, 1)
    # the picture with the lenses' reflections and dust taken out, as the tent lit it (the lens's
    # own edge kept, above)
    seen = np.where((spots & ~(rim_sp & ~paint))[..., None], Tc * back, lin_clean).astype(np.float32)
    del rim_sp
    if lc.get("as_shot"):
        # A lens seen at a steep angle shows mostly its own edge and reflections, not the tent behind
        # it: it keeps its look as photographed, its transmission taken against the stage color (on
        # the stage, exactly the photograph; on anything else, the same filter). Against the tent it
        # came out lighter than the frame round it, and where SAM's mask stopped inside the lens the
        # step ran ragged (F06's three-quarter and detail). After the clean-up: spots are filled from
        # round them, and the tent-measured transmission just past the lens is lighter.
        Tc = np.where(lens[..., None], np.clip(seen / hex_lin(STAGE_HEX), 0, 1), Tc).astype(np.float32)
    report["lens_grain"] = grains if mode else None              # per refilled lens, in 8-bit levels
    report["lens"] = {"hole_px": int(holes.sum()), "cleaned_px": int(spots.sum()),
                      "dust_px": int((dust & holes).sum()),
                      "transmission_median_rgb": [round(float(np.median(Tc[..., c][holes])), 3) for c in range(3)] if holes.any() else None}

    # unmix the opaque parts from the tent behind their soft edges (the old marks are off, above)
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
    # Inside an open gap (a bridge, the space between a side view's temples) the tent is read on the
    # gap's own clear part: the model is filled in there from all round and comes out brighter
    # than the tent really seen through it, which left the gap grey and its edge dark.
    gaps = holes & ~lens
    gap_tent = np.zeros(S.shape, bool)
    if gaps.any():
        lab_g, n_g = ndi.label(gaps)
        Lg = lum(lin)
        for i in range(1, n_g + 1):
            gi = lab_g == i
            if gi.sum() < 400:
                continue
            p90 = float(np.percentile(Lg[gi], 90))
            if p90 < 0.5 * float(np.median(lum(back)[gi])):
                continue                              # a gap that sees only dark things
            gap_tent |= gi & (Lg > 0.55 * p90)          # all of the tent seen there, not a temple behind
        ring = np.maximum(ring, gap_tent.astype(np.float32))
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
    # the gate fades in over a few px: cut square, its edge showed as a scalloped line along a soft
    # blurred part (F05's detail, under the far temple)
    nearw = cv2.GaussianBlur(near.astype(np.float32), (0, 0), 3)
    A = (alpha_m + (np.maximum(alpha_m, A_s) - alpha_m) * nearw).astype(np.float32)
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
    # The model sometimes takes the tent seen through an open gap for frame, partly (the nose
    # bridge of a front view, the space between the temples of a side view): grey patches whose
    # edge followed the model's guess, not the picture. Over a broad, uncolored area of partial
    # model opacity well clear of the solid frame, the opacity is the physical one throughout, so
    # it follows the picture's own shading. Thin lines there (a highlight along a wire) and colored
    # parts (tortoise) stay with the model.
    over = (alpha_m > 0.02) & (alpha_m < 0.9) & (A_sat < 0.3)
    d_solid = cv2.distanceTransform((~solid).astype(np.uint8), cv2.DIST_L2, 5)
    over = cv2.morphologyEx((over & (d_solid > 8)).astype(np.uint8), cv2.MORPH_OPEN,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))) > 0
    report["model_overreach_px"] = int(over.sum())
    # And round such a gap the model's own soft edge, which it calls solid (0.9 and more) though it
    # is the tent seen there with the frame's blur over it: a band of the old tent's grey stood round
    # the gap between F03's temples in the side view. Grown from the gap through what the model calls
    # frame but is lighter than solid frame and uncolored, only ever darker, at most 45 px: the soft
    # edge, not a light part of the frame past it (a lit face, F08's clear temples; let run to 150 px,
    # it took the light parts of F03's side-view hinge with it). Where it runs that far, it fades out.
    rim_gap = np.zeros(over.shape, bool)
    rim_w = np.zeros(over.shape, np.float32)
    clear_gap = np.zeros(over.shape, bool)
    if over.any():
        near_lens = cv2.dilate((lens_in | lens_band).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
        # (not the frame's outer soft edge, against the tent round it, which the model reads well)
        d_bg = cv2.distanceTransform((alpha_m >= 0.05).astype(np.uint8), cv2.DIST_L2, 5)
        light = (alpha_m > 0.5) & (A_s < 0.9) & (A_sat < 0.3) & ~near_lens & ~holes & (d_bg > 15)
        # only from a gap that is clearly tent (as light as the tent model, mostly): a patch of grey
        # the model took for tent beside a lit face of the frame (the rim's inner wall by F03's nose
        # bridge in the front view) would take the face with it
        # and a gap the frame closes round, not the zone of soft edge between a defocused part and
        # the tent outside it (most of its rim is open tent there: grown into the soft edge of
        # F04's and F09's far temples and F03's end-piece, it cut it into light blocks and streaks)
        lab_o, n_o = ndi.label(over)
        if n_o:
            idx_o = np.arange(1, n_o + 1)
            med_o = np.asarray(ndi.median(A_s, lab_o, idx_o))
            ring_o = cv2.dilate(lab_o.astype(np.float32), np.ones((7, 7), np.uint8)).astype(np.int32) * ~over
            open_o = np.asarray(ndi.mean((alpha_m < 0.05).astype(np.float32), ring_o, idx_o))
            # and a broad one (the space between a side view's temples), not a narrow light gap the
            # frame's own parts close round (beside F04's end-piece, by F09's hinge), whose rims are
            # the frame's soft edges, not the tent's
            size_o = np.asarray(ndi.sum(over, lab_o, idx_o))
            clear_gap = np.isin(lab_o, idx_o[(med_o < 0.1) & (open_o < 0.25) & (size_o >= 30000)])
            del ring_o
        rim_w = grow_soft_edge(clear_gap, light, A_s) * ~over
        rim_gap = rim_w > 0
        del d_bg, near_lens, light, lab_o
    report["gap_rim_px"] = int(rim_gap.sum())
    if over.any():
        # faded in from its edge; a clear gap all of it, fading out past its edge (faded in, the
        # model's opacity stood as a faint ridge between the gap and its rim, below, a line round
        # F03's side-view gap)
        gw = np.maximum(cv2.GaussianBlur(over.astype(np.float32), (0, 0), 3) * (alpha_m < 0.9), clear_gap)
        A = (A * (1 - gw) + np.minimum(A, A_s) * gw).astype(np.float32)
    if rim_gap.any():
        # its opacity the physical one, up to solid where it is nearly as dark as the frame
        A_rg = A_s + (1 - A_s) * np.clip((A_s - 0.75) / 0.2, 0, 1)
        gr = np.maximum(cv2.GaussianBlur(rim_w, (0, 0), 1.5), rim_w)
        A = (A * (1 - gr) + np.minimum(A, A_rg) * gr).astype(np.float32)
        del A_rg
    else:
        gr = np.zeros(A.shape, np.float32)
    del clear_gap
    # The model is unsure of a defocused part well inside the frame (F06's far hinge, round and
    # out of focus: 0.85 to 0.9) and only 0.9 counts as solid, so it showed as a lighter patch with a
    # hard edge. Well clear of anything open (the tent, a gap, a lens), what the model calls nearly
    # solid is solid; faded in with the distance, so soft edges keep their opacity.
    # Not where the tent seen through a gap was taken for frame (`over` and its rim, above).
    d_open = cv2.distanceTransform((~((alpha_m < 0.5) | holes)).astype(np.uint8), cv2.DIST_L2, 5)
    lift = (np.clip((alpha_m - 0.75) / 0.15, 0, 1) * np.clip((d_open - 4) / 4, 0, 1) *
            (1 - np.clip(2 * cv2.GaussianBlur((over | rim_gap).astype(np.float32), (0, 0), 3), 0, 1))).astype(np.float32)
    A = (A + (np.maximum(A, 0.995) - A) * lift).astype(np.float32)
    report["lifted_px"] = int(((lift > 0.5) & ~solid & ~holes).sum())
    del d_open, lift
    # And a clearly colored pixel inside the frame is the frame's own color, not the tent seen
    # through it (the tent is neutral grey): F01's blue tortoise patches, dark and translucent, read
    # 0.95 opaque against the tent, and the 5% of new stage seen through them washed them lavender.
    # (Not by the lenses, whose colored glass the rim's soft edge lies over; and not near black, where
    # the camera's own color noise passes for color, block by block: those blocks went solid and the
    # rest stayed at the rim's 0.995, a checkerboard on F01's black rims once brightened.)
    inside = filled & ~holes & ~(cv2.dilate((lens_in | lens_band).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0)
    colored = np.clip((A_sat - 0.3) / 0.4, 0, 1) * np.clip((mx - 0.06) / 0.06, 0, 1)
    colored = cv2.GaussianBlur(colored.astype(np.float32), (0, 0), 1.5)
    A = np.where(inside, np.maximum(A, colored), A).astype(np.float32)
    del inside, colored
    A[holes] = 0.0
    rim = solid & ~holes & ~rim_gap
    A[rim] = np.maximum(A[rim], 0.995)
    # The rim's inner soft edge lies over the lens, not the stage: its partly covered pixels are
    # unmixed against the tent as the lens shows it, and put back over the lens as cleaned. Over
    # bare stage they made a pale line round a light lens (the F03 hero's yellow, F01's blue).
    lens_h = (lens_in | lens_band).astype(np.float32)
    den = cv2.GaussianBlur(lens_h, (0, 0), 4)
    lens_ring = (den > 0.002) & ~holes & (A < 0.995)
    Tb = np.ones_like(Tc)
    Tfr = np.ones_like(Tc)
    if lens_ring.any():
        wr = np.clip(den / 0.25, 0, 1)[..., None]
        ext0 = cv2.GaussianBlur(Tc0 * lens_h[..., None], (0, 0), 4) / np.maximum(den, 1e-6)[..., None]
        ext1 = cv2.GaussianBlur(Tc * lens_h[..., None], (0, 0), 4) / np.maximum(den, 1e-6)[..., None]
        Tb = np.where(lens_ring[..., None], 1 + (np.clip(ext0, 0, 1) - 1) * wr, 1).astype(np.float32)
        Tfr = np.where(lens_ring[..., None], 1 + (np.clip(ext1, 0, 1) - 1) * wr, 1).astype(np.float32)
    report["lens_ring_px"] = int(lens_ring.sum())
    # No part of the frame is lighter in any channel than its share of the tent behind it allows:
    # where it is darker than that, it is more opaque. Unmixed at the lower opacity, a deep color's
    # weak channels went below zero and were cut there, and the stage's share came back on top, a
    # grey film over F02's red tortoise (most in the out-of-focus end pieces); where the clearly
    # colored parts were made solid (above) and the rest kept the film, each patch had a grey
    # outline and each dark spot in it a grey ring. From 0.9 opaque, the opacity is at least what
    # keeps each channel at zero or above, so the frame comes out as photographed; less of that
    # further out on a soft edge, down to none at 0.5 (switched on at 0.85, the bevel's soft edge on
    # F01's detail kept a lavender film past a hard line).
    behind = back_s * Tb
    A_min = np.clip(1 - (lin_clean / np.maximum(behind, 1e-4)).min(-1), 0, 1)
    w_min = np.clip((A - 0.5) / 0.4, 0, 1) * ~holes
    report["darker_than_tent_px"] = int(((A_min > A + 0.001) & (w_min > 0)).sum())
    A = (A + (np.maximum(A, A_min) - A) * w_min).astype(np.float32)
    del behind, A_min, w_min
    F = np.where(A[..., None] > 0.02, (lin_clean - (1 - A[..., None]) * back_s * Tb) / np.maximum(A[..., None], 0.02), 0)
    if missed.any():
        # with a measured alpha, unmixing per channel blows small tints up into strong color (a
        # grey wire that picked up a little red from the rim beside it); unmix the brightness
        # only and keep the pixel's own color there
        Fl = np.clip((lum(lin_clean) - (1 - A) * lum(back)) / np.maximum(A, 0.02), 0, 1)
        Fc = lin_clean * (Fl / np.maximum(lum(lin_clean), 1e-4))[..., None]
        F = np.where(missed[..., None], Fc, F)
    F = np.clip(F, 0, 1).astype(np.float32)
    Tf = Tfr.copy()
    Tf[holes] = Tc[holes]
    if gap_tent.any():
        # a gap shows the stage: the tent seen through it, against the tent read there (above)
        Tf[gaps] = np.clip(lin / (back_s + 1e-5), 0, 1)[gaps]
    report["gap_tent_px"] = int(gap_tent.sum())
    if lc.get("tint"):
        # A lens with a set tint is not read from the picture (below): its edge is the convex mask's
        # line, feathered outward as soft as the photograph's, with the set tint behind the rim's
        # soft inner edge (cut square, F04's close-up's dark lenses ended in a 1-2 px step where
        # the photograph's edges are soft, out-of-focus gradients)
        lens_h = (lens_in | lens_band).astype(np.float32)
        f = np.clip(2 * cv2.GaussianBlur(lens_h, (0, 0), 3), 0, 1)
        feather = (f > 0.002) & ~holes
        A = np.where(feather, A * (1 - f), A).astype(np.float32)
        Tf = np.where(feather[..., None], np.asarray(lc["tint"], np.float32), Tf).astype(np.float32)
        report["lens_feather_px"] = int(feather.sum())
        del lens_h, f, feather

    # the lens's edge, read from the picture (read_lens_edge), one lens at a time
    del Tb, Tfr
    report["lens_edge_px"] = 0
    lab_l, n_l = ndi.label(lens)
    dbg_dir = out / "debug" if "--debug" in sys.argv else None
    if dbg_dir is not None:
        dbg_dir.mkdir(exist_ok=True)
    # (not on a lens kept as shot: it is the photograph up to its edge already, and past it the
    # reading took the frame's soft edge over the tent for frame over lens, a notch of the tent's
    # old grey where F06's shield meets its far temple)
    # (nor where the lens takes a set tint, lc["tint"]: the picture's lens is not the lens shown,
    # and read against it the tent's dimples by the rim stayed as bright crumbs on the dark lens and
    # its blurred bottom went ragged, F04's close-up; there the convex mask's line is the edge)
    for i in range(1, n_l + 1 if not (lc.get("as_shot") or lc.get("tint")) else 1):
        lm = lab_l == i
        if lm.sum() >= 2000:
            report["lens_edge_px"] += read_lens_edge(lm, holes, A, F, Tf, seen, srgb_clean, back_s, dbg_dir,
                                                     kept=kept_behind)
    del lab_l

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
    # the tent seen round a gap's edge (rim_gap, above) is no more in shadow than the gap itself
    S = (S + (1 - S) * gr).astype(np.float32)
    del gr

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
                        "stray": stray, "overreach": over, "gap_rim": rim_gap, "gap_tent": gap_tent, "lens": lens,
                        "lens_band": lens_band, "lens_ring": lens_ring, "solid": solid,
                        "lens_filter": lum(Tf), "lens_measured": lum(Tc0)}.items():
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
