#!/usr/bin/env python3
"""A frame's own colour for its 3D build (frame3d.py), from its cleaned front product shot.

    python3 tools/blender/frame_texture.py F02            # the angle set's A1 shot (work/out/<shot>/)
    python3 tools/blender/frame_texture.py F01 --temples  # and a band for acetate temples in the same material

A tortoise acetate is a pattern, not a colour: the 3D front takes it from the real frame. The cleaned
front shot (tools/photo/clean_lightbox.py: the frame cut out, its lenses in their own layer, the GCD
where the founder placed it) is registered to the 1:1 front drawing (their outlines, an affine fit), and
read as the acetate's colour under the tent's even light: the photograph's linear light over the tent's
white, with the tent's white mirrored in the gloss taken off (a highlight is white light added on top of
the pigment's colour). Beyond the frame's edge and in the lens openings the colour carries on from the
nearest acetate, so the front's walls and inner edges never pick up the tent.

The metal on the front is found in the same shot: the GCD's gold band and its onyx (the band's inside),
and any pin heads (small bright neutral rounds). The build gives them gold, black stone and steel.

Writes work/frames3d/<frame>/: albedo.png (16-bit, linear), masks.png (R gold, G onyx, B pins), map.json
(the affine from the front's millimetres, frame3d's coordinates, to the texture's pixels); with
--temples, temple.png: the same acetate laid anew along a band that frame3d wraps round each temple (the
front shot never sees the temples' faces), its blue and black and their proportions read off the front.
"""
import argparse
import json
import pathlib
import sys

import cv2
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "blender"))


def s2l(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def fill_out(img, known, levels=9):
    """Carry known values out over the unknown (push-pull: the known averaged down a pyramid, pulled back
    up where nothing is known), so every pixel has its nearest region's colour."""
    img = img.astype(np.float32)
    w = known.astype(np.float32)
    pyr = [(img * w[..., None], w)]
    for _ in range(levels):
        a, b = pyr[-1]
        pyr.append((cv2.pyrDown(a), cv2.pyrDown(b)))
    a, b = pyr[-1]
    est = a / np.maximum(b, 1e-6)[..., None]
    for a, b in reversed(pyr[:-1]):
        up = cv2.resize(est, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_LINEAR)
        k = np.clip(b * 4, 0, 1)[..., None]
        est = np.where(b[..., None] > 1e-6, a / np.maximum(b, 1e-6)[..., None], up) * k + up * (1 - k)
    return np.where(known[..., None], img, est)


def tortoise(h, w, ppm, coverage, blue, black, along_mm=5.0, across_mm=2.0, seed=7):
    """A blue-and-black tortoise acetate laid anew (F01's temples), h x w px at `ppm` px per mm, repeating
    both ways: its blue blotches where a smooth random field (a Gaussian's width `along_mm` along the band,
    `across_mm` across it: the sheet's pattern runs drawn out along a temple, as F01's three-quarter and
    detail shots show) stands in its top `coverage`, two finer fields breaking their edges into the torn
    outlines the front's blotches have; inside them the
    blue varies as the real blotches do, 15% either side of the front's own blue (`blue`, linear)."""
    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]

    def field(sa, sc):
        G = np.exp(-2 * np.pi ** 2 * ((sc * ppm * fy) ** 2 + (sa * ppm * fx) ** 2))
        f = np.real(np.fft.ifft2(np.fft.fft2(rng.standard_normal((h, w))) * G))
        return (f - f.mean()) / f.std()
    f = field(along_mm, across_mm) + 0.45 * field(along_mm / 2.5, across_mm / 2.5) + 0.2 * field(along_mm / 6, across_mm / 6)
    t = np.quantile(f, 1 - coverage)
    m = np.clip((f - t) / 0.08 + 0.5, 0, 1)
    m = m * m * (3 - 2 * m)
    shade = 1.0 + 0.15 * np.clip(field(2 * along_mm, 2 * across_mm), -1, 1)
    col = black[None, None, :] * (1 - m[..., None]) + (blue[None, None, :] * shade[..., None]) * m[..., None]
    return col.astype(np.float32)


def register(sil_photo, sil_draw, init):
    """The affine taking the drawing's pixels to the photo's, refined from `init` by matching the two
    filled outlines (blurred), at a quarter of the photo's size."""
    q = 4
    a = cv2.GaussianBlur(cv2.resize(sil_photo.astype(np.float32), None, fx=1 / q, fy=1 / q, interpolation=cv2.INTER_AREA), (0, 0), 2)
    S = np.diag([1 / q, 1 / q, 1.0])
    M = (S @ np.vstack([init, [0, 0, 1]]))[:2].astype(np.float32)
    # warp the drawing into the photo's (quartered) frame and refine there
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)
    tmpl = a
    Hd, Wd = sil_draw.shape
    src = cv2.GaussianBlur(sil_draw.astype(np.float32), (0, 0), 2 * q * 20 / 20.8)   # the same blur in mm
    # ECC finds W with tmpl(x) ~ src(W x): W maps the photo's pixels to the drawing's; start from init's inverse
    Minv = cv2.invertAffineTransform(M)
    _, Wm = cv2.findTransformECC(tmpl, src, Minv.astype(np.float32), cv2.MOTION_AFFINE, crit, None, 5)
    Mq = cv2.invertAffineTransform(Wm)                       # drawing px -> quartered photo px
    return (np.diag([q, q, 1.0]) @ np.vstack([Mq, [0, 0, 1]]))[:2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frame")
    ap.add_argument("--shot", default=None)
    ap.add_argument("--ppm", type=float, default=12.0, help="the texture's pixels per mm")
    ap.add_argument("--temples", action="store_true", help="also lay the acetate along a band for the temples")
    ap.add_argument("--temple-mm", type=float, nargs=2, default=(170.0, 32.0),
                    help="the band's length along the temple and its height round the temple's section, mm")
    a = ap.parse_args()
    import frame3d
    shot = a.shot
    if not shot:
        sets = json.loads((ROOT / "content" / "photography" / "lightbox-angle-set.json").read_text())
        shot = sets["frames"][a.frame]["picks"]["A1"]
    po = ROOT / "work" / "out" / shot
    cut = np.asarray(Image.open(po / "cutout.png")).astype(np.float32)
    rgb, alpha = cut[..., :3], cut[..., 3] / 255
    T = np.asarray(Image.open(po / "layers" / "lens.png")).astype(np.float32) / 255
    lens = T.mean(-1) < 0.9
    stage = np.asarray(Image.open(po / "stage-full.png")).astype(np.float32)
    bg = float(s2l(np.median(stage[(alpha < 0.01)][:, :3], axis=0) / 255).mean())   # the tent's white, linear
    from scipy import ndimage as ndi
    sil_photo = ndi.binary_fill_holes(alpha > 0.5)

    # the drawing at 20 px/mm, its outline filled
    sh = frame3d.front_shapes(a.frame, ppm=20)
    ppm_d = sh["ppm"]
    openings = np.zeros_like(sh["solid"])
    for m in sh["opening_masks"]:
        openings |= m
    sil_draw = ndi.binary_fill_holes(sh["solid"] | openings)
    # a first guess from the two outlines' boxes
    ys, xs = np.nonzero(sil_photo)
    yd, xd = np.nonzero(sil_draw)
    sx = (xs.max() - xs.min()) / (xd.max() - xd.min())
    sy = (ys.max() - ys.min()) / (yd.max() - yd.min())
    init = np.array([[sx, 0, xs.min() - sx * xd.min()], [0, sy, ys.min() - sy * yd.min()]])
    A = register(sil_photo, sil_draw, init)                  # drawing px -> photo px
    ox, oy = sh["origin_px"]
    # millimetres (x right as drawn, y up; frame3d's) -> drawing px -> photo px
    D = np.array([[ppm_d, 0, ox], [0, -ppm_d, oy], [0, 0, 1.0]])
    Mp = (np.vstack([A, [0, 0, 1]]) @ D)[:2]
    # check: the drawing's outline in the photo
    warped = cv2.warpAffine(sil_draw.astype(np.uint8), A.astype(np.float32), (sil_photo.shape[1], sil_photo.shape[0]),
                            flags=cv2.INTER_NEAREST)
    iou = float((warped.astype(bool) & sil_photo).sum() / (warped.astype(bool) | sil_photo).sum())

    # the texture: the frame's box in the photo, at `ppm` px per mm
    scale = a.ppm / float(np.sqrt(abs(np.linalg.det(Mp[:, :2]))))
    pad = 30
    x0, y0, x1, y1 = xs.min() - pad, ys.min() - pad, xs.max() + pad, ys.max() + pad
    tw, th = int(round((x1 - x0) * scale)), int(round((y1 - y0) * scale))
    C = np.array([[scale, 0, -x0 * scale], [0, scale, -y0 * scale], [0, 0, 1.0]])
    Mt = (C @ np.vstack([Mp, [0, 0, 1]]))[:2]               # mm -> texture px

    lin = s2l(rgb / 255)
    acetate = (alpha > 0.98) & ~cv2.dilate(lens.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    # the metal first (its colour is not the acetate's)
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    gold = acetate & (R > 110) & (G > 70) & (B < 0.75 * G) & (R - B > 60) & (G > 0.55 * R)
    gold = cv2.morphologyEx(gold.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(gold.astype(np.uint8))
    gold = np.isin(lab, [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 200])
    onyx = ndi.binary_fill_holes(cv2.dilate(gold.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & ~gold
    Lm = rgb.mean(-1)
    sat = (rgb.max(-1) - rgb.min(-1)) / np.maximum(rgb.max(-1), 1)
    bright = acetate & (Lm > 120) & (sat < 0.3)
    n, lab, st, cen = cv2.connectedComponentsWithStats(bright.astype(np.uint8))
    pins = np.zeros_like(bright)
    ppm_p = float(np.sqrt(abs(np.linalg.det(Mp[:, :2]))))
    for i in range(1, n):
        w_, h_, ar = st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT], st[i, cv2.CC_STAT_AREA]
        # a pin head: round, 0.6-2.5 mm across, filled
        if 0.6 * ppm_p < max(w_, h_) < 2.5 * ppm_p and 0.6 < w_ / max(h_, 1) < 1.6 and ar > 0.5 * w_ * h_:
            pins |= lab == i
    pins = cv2.dilate(pins.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0
    metal = gold | onyx | pins

    # the acetate's colour: the tent's white mirrored in the gloss taken off (white added on top of the
    # pigment shows as the darkest channel lifted off the pigment's floor), over the tent's white
    white = np.clip(lin.min(-1) - 0.006, 0, None)
    alb = np.clip((lin - white[..., None]) / bg, 0, 1)
    glare = white > 0.04                                      # too much mirrored to read the colour under
    known = acetate & ~metal & ~cv2.dilate(glare.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    alb = fill_out(alb, known)

    def to_tex(img, interp=cv2.INTER_AREA):
        crop = img[max(0, y0):y1, max(0, x0):x1]
        return cv2.resize(crop, (tw, th), interpolation=interp)

    out = ROOT / "work" / "frames3d" / a.frame
    out.mkdir(parents=True, exist_ok=True)
    A_t = to_tex(alb)
    cv2.imwrite(str(out / "albedo.png"), cv2.cvtColor((np.clip(A_t, 0, 1) * 65535 + 0.5).astype(np.uint16), cv2.COLOR_RGB2BGR))
    Mk = np.dstack([gold, onyx, pins]).astype(np.float32)
    M_t = np.clip(to_tex(Mk), 0, 1)
    Image.fromarray((M_t * 255 + 0.5).astype(np.uint8)).save(out / "masks.png")
    # a preview: the colour as sRGB, the metal tinted
    prev = np.where(A_t <= 0.0031308, 12.92 * A_t, 1.055 * np.clip(A_t, 0, 1) ** (1 / 2.4) - 0.055)
    prev = prev * (1 - M_t.max(-1, keepdims=True)) + M_t @ np.array([[0.85, 0.7, 0.3], [0.2, 0.2, 0.2], [0.8, 0.8, 0.85]])
    Image.fromarray((np.clip(prev, 0, 1) * 255).astype(np.uint8)).save(out / "preview.jpg", quality=92)
    info = {"frame": a.frame, "shot": shot, "size": [tw, th], "ppm": a.ppm,
            "mm_to_px": [[round(float(v), 6) for v in r] for r in Mt],
            "outline_iou": round(iou, 4), "tent_white_linear": round(bg, 4),
            "metal_px": {"gold": int(gold.sum()), "onyx": int(onyx.sum()), "pins": int(pins.sum())}}
    if a.temples:
        # acetate temples in the same material (F01): the front shot never sees their faces, so their
        # colour is the front's acetate laid anew along a band (`--temple-mm` long, round the temple's
        # section, repeating), with the front's own blue and black in the front's proportions
        px = alb[known]
        blueness = px[:, 2] - np.maximum(px[:, 0], px[:, 1])
        is_blue = blueness > 0.05
        coverage = float(is_blue.mean())
        blue = np.median(px[blueness > np.percentile(blueness[is_blue], 50)], axis=0) if is_blue.any() else px.mean(0)
        black = np.median(px[blueness < 0.01], axis=0)
        L_mm, V_mm = a.temple_mm
        band = tortoise(int(round(V_mm * a.ppm)), int(round(L_mm * a.ppm)), a.ppm, coverage, blue, black)
        cv2.imwrite(str(out / "temple.png"), cv2.cvtColor((np.clip(band, 0, 1) * 65535 + 0.5).astype(np.uint16), cv2.COLOR_RGB2BGR))
        bp = np.where(band <= 0.0031308, 12.92 * band, 1.055 * np.clip(band, 0, 1) ** (1 / 2.4) - 0.055)
        Image.fromarray((np.clip(bp, 0, 1) * 255).astype(np.uint8)).save(out / "temple-preview.jpg", quality=92)
        info["temple"] = {"file": "temple.png", "mm": [L_mm, V_mm], "ppm": a.ppm, "blue_coverage": round(coverage, 3),
                          "blue": [round(float(v), 4) for v in blue], "black": [round(float(v), 4) for v in black]}
    (out / "map.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info))


if __name__ == "__main__":
    main()
