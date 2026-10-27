#!/usr/bin/env python3
"""A cast picture cut out: the person wearing the frame, on transparency, to set in any scene.

    python3 tools/photo/cutout.py content/photography/people/M1-S06-F04-A1.json
    python3 tools/photo/cutout.py --all        # every cast picture rendered in 3D (work/people/<id>-3d/)

The cast portraits are made on plain studio backdrops so the person, wearing the frame, can be lifted off
them and used in any setting (founder, Oct 27 2026; docs/brief/07-photography.md, "Cut-outs"). The cut-out
is the finished picture (tools/blender/wear3d.py: composite.png, its crop and its grade) with an alpha
channel:

- the person's outline from depth: Depth Anything V2 Small (head3d.disparity) on the portrait as generated,
  without the frame. In a studio portrait the backdrop is a far plateau and the person stands well in front
  of it, so the outline holds where the colours do not part: a black sweater on black, a white shirt on the
  warm white (a colour model, ISNet, made both half see-through; BiRefNet, the better portrait model, needs
  more memory than this workspace has);
- its edge read from the picture: a band either side of the outline solved by closed-form matting
  (PyMatting, MIT), wider round the head for the hair; where person and backdrop are too alike in colour to
  tell apart there (dark hair on black), the depth's own edge, softened by a pixel;
- the frame from its renders, exactly: the front and the temples where they reach past the person, and a
  lens with the backdrop behind it (a three-quarter view's far lens, past the cheek; layers/lens_mask.exr)
  as a filter, opaque by what its transmission holds back. One alpha cannot carry a lens's colour: there it
  darkens a new background without tinting it;
- the colours along the edge freed of the backdrop (PyMatting's foreground estimate), so no fringe of the
  old black or white comes along onto a new background. Unmixed in sRGB, as design tools blend: laid on the
  old backdrop in Photoshop or Figma, the cut-out gives the picture back.

The cut-out carries the picture's SS90 grade (lifted blacks, grain), as approved; the scene it is set in
takes the same grade (tools/photo/wear.py, ss90).

Writes work/people/<id>-3d/: cutout.png (16-bit RGBA, straight alpha, sRGB, the picture's crop),
cutout-check.jpg (the cut-out on white, mid grey, black and a colour; its edges at 1:1) and cutout.json.
"""
import json
import pathlib
import sys

import cv2
import numpy as np
from scipy import ndimage as ndi

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "blender"))
sys.path.insert(0, str(ROOT / "tools" / "photo"))
PEOPLE = ROOT / "content" / "photography" / "people"

# the matting band either side of the depth outline (px, at the picture's 2x size): round the head, where
# hair runs past the outline the depth model draws (about 4 px to its pixel here); below the chin, where
# the outline is a collar or a shoulder
BAND_HEAD, BAND_BODY = 22, 8
# colour difference (sRGB, 0-1) between the person and the backdrop beside an edge below which the picture
# cannot place it, and above which it can be trusted fully
TELL_LO, TELL_HI = 0.08, 0.20


def read_exr(path):
    """A render, linear RGBA, top row first (through Blender's image loader: this OpenCV reads no EXR)."""
    import bpy
    im = bpy.data.images.load(str(path), check_existing=False)
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(h, w, 4)[::-1]


def spread(img, known, levels=10):
    """Known values carried out over the unknown (push-pull), so each pixel takes its nearest region's."""
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


def outline(img_bgr8):
    """The person's outline (bool) from depth: the backdrop's far plateau against the person in front of it
    (two groups of depths with almost nothing between: Otsu's split), the largest piece, holes filled."""
    import head3d
    d = head3d.disparity(img_bgr8).astype(np.float32)
    # the model's 518 px grid, brought up to the picture's size, drew its steps into the outline as a row
    # of small teeth along a shoulder: smoothed over a few pixels first
    d = cv2.GaussianBlur(d, (0, 0), 0.6 * max(img_bgr8.shape[:2]) / 518)
    lo, hi = np.percentile(d, [1, 99])
    u = np.clip((d - lo) / max(hi - lo, 1e-6) * 255, 0, 255).astype(np.uint8)
    t, _ = cv2.threshold(u, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    sil = u > t
    n, lab, st, _ = cv2.connectedComponentsWithStats(sil.astype(np.uint8))
    sil = ndi.binary_fill_holes(lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])))
    gap = float(np.mean(u[sil]) - np.mean(u[~sil])) / 255
    return sil, gap


def person_matte(rgb, img_bgr8, chin_y):
    """The person's matte (0-1) on the portrait as generated (sRGB, 0-1)."""
    from pymatting import estimate_alpha_cf
    H, W = rgb.shape[:2]
    sil, gap = outline(img_bgr8)
    din = ndi.distance_transform_edt(sil)
    dout = ndi.distance_transform_edt(~sil)

    def trimap(band):
        t = np.full((H, W), 0.5)
        t[sil & (din > band)] = 1.0
        t[~sil & (dout > band)] = 0.0
        return t

    def telling(t):
        """How far the picture can tell person from backdrop beside the edge: their colours there (each
        carried out from its own side), apart by TELL_LO or less: not at all; by TELL_HI or more: fully."""
        d = np.linalg.norm(spread(rgb, t == 1.0) - spread(rgb, t == 0.0), axis=-1)
        return np.clip((d - TELL_LO) / (TELL_HI - TELL_LO), 0, 1)
    # the band widens round the head for the hair, but only where the hair parts from the backdrop: where
    # it does not (dark hair on black), a wide band only let the picture's grain in, as grey smudges
    yy = np.arange(H, dtype=np.float32)[:, None]
    head = np.clip((chin_y + 80 - yy) / 160, 0, 1) * np.ones((1, W), np.float32)
    tell0 = cv2.GaussianBlur(telling(trimap(BAND_BODY)).astype(np.float32), (0, 0), 15)
    tri = trimap(BAND_BODY + (BAND_HEAD - BAND_BODY) * head * tell0)
    alpha = np.clip(estimate_alpha_cf(rgb.astype(np.float64), tri), 0, 1).astype(np.float32)
    # the solve takes the picture's grain into the edge as a speckle in its opacity (a lens draws an edge
    # smooth): evened out along the picture's own structure (a guided filter), so a hair keeps its line
    alpha = np.clip(cv2.ximgproc.guidedFilter(rgb.astype(np.float32), alpha, 2, 2e-4), 0, 1)
    # where the person and the backdrop beside the edge are too alike to tell apart, the picture cannot
    # place the edge: the depth's outline, softened as a lens would
    tell = telling(tri)
    soft = cv2.GaussianBlur(sil.astype(np.float32), (0, 0), 1.2)
    unknown = tri == 0.5
    a = np.where(unknown, tell * alpha + (1 - tell) * soft, tri).astype(np.float32)
    stats = {"depth_gap": round(gap, 3), "band_px": [BAND_HEAD, BAND_BODY],
             "edge_read_from_picture": round(float(tell[unknown].mean()), 3)}
    return a, sil, stats


def frame_layers(cfg, out, crop):
    """The frame's coverage from its renders, as the composite lays them (wear3d.composite): the front's
    solid parts, the temples (the ear laid over them where it is), the lenses."""
    look = cfg.get("look3d", {})
    sigma = look.get("soften_px", 0.6)
    x0, y0, x1, y1 = crop

    def alpha(name):
        p = out / "layers" / name
        if not p.exists():
            return None
        a = read_exr(p)[..., 3].astype(np.float32)
        return cv2.GaussianBlur(a, (0, 0), sigma) if sigma > 0 else a
    f_a = alpha("front.exr")
    H, W = f_a.shape
    t_a = alpha("temples.exr")
    if t_a is None or not look.get("temples", True):
        t_a = np.zeros_like(f_a)
    ear = np.zeros((H, W), np.float32)
    for poly in look.get("ear_occluders_px", []):
        q = 4
        big = np.zeros((H * q, W * q), np.uint8)
        cv2.fillPoly(big, [np.round((np.asarray(poly, np.float64) + 0.5) * q - 0.5).astype(np.int32)], 255, cv2.LINE_AA)
        ear = np.maximum(ear, cv2.resize(big, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255)
    if ear.max() > 0:
        ear = cv2.GaussianBlur(ear, (0, 0), look.get("ear_feather_px", 0.7))
        t_a = t_a * (1 - ear)
    lens = alpha("lens_mask.exr")
    has_lens = lens is not None
    if lens is None:
        lens = np.zeros_like(f_a)
    lens = np.clip(lens, 0, 1)
    solid = np.clip(f_a - lens, 0, 1)
    c = lambda a: a[y0:y1, x0:x1]
    return c(solid), c(np.clip(t_a, 0, 1)), c(lens), has_lens


def checks(rgba, frame_any, path):
    """The cut-out on white, mid grey, black and a colour, and its edges at 1:1: the top of the head, the
    frame's side, a shoulder."""
    F, a = rgba[..., :3], rgba[..., 3:4]
    H, W = a.shape[:2]
    bgs = [(1.0, 1.0, 1.0), (0.5, 0.5, 0.5), (0.0, 0.0, 0.0), (0.16, 0.33, 0.52)]
    th = 640
    tw = int(round(W * th / H))
    row1 = np.hstack([cv2.resize(F * a + np.asarray(b, np.float32) * (1 - a), (tw, th), interpolation=cv2.INTER_AREA)
                      for b in bgs])
    ys, xs = np.nonzero(a[..., 0] > 0.5)
    top = (int(xs[np.argmin(ys)]), int(ys.min()))
    fy, fx = np.nonzero(frame_any > 0.5)
    side = (int(fx.min()), int(fy[np.argmin(fx)])) if len(fx) else (int(xs.min()), int(np.median(ys)))
    # a shoulder: the outline's left edge where it runs down from the neck, clear of the picture's side
    left = [(int(np.nonzero(a[y, :, 0] > 0.5)[0].min()), y) for y in range(int(0.45 * H), H, 8)
            if (a[y, :, 0] > 0.5).any() and np.nonzero(a[y, :, 0] > 0.5)[0].min() > 40]
    shoulder = left[len(left) // 2] if left else (0, int(0.8 * H))
    s = 420
    tiles = []
    for (cx, cy), b in zip((top, side, shoulder), ((0.5, 0.5, 0.5), (1.0, 1.0, 1.0), (1.0, 1.0, 1.0))):
        xa, ya = int(np.clip(cx - s // 2, 0, W - s)), int(np.clip(cy - s // 2, 0, H - s))
        cc = F[ya:ya + s, xa:xa + s] * a[ya:ya + s, xa:xa + s] + np.asarray(b, np.float32) * (1 - a[ya:ya + s, xa:xa + s])
        tiles.append(cc)
    row2 = np.hstack(tiles)
    row2 = np.pad(row2, ((0, 0), (0, max(0, row1.shape[1] - row2.shape[1])), (0, 0)), constant_values=1.0)[:, :row1.shape[1]]
    sheet = np.vstack([row1, np.ones((12, row1.shape[1], 3), np.float32), row2])
    cv2.imwrite(str(path), cv2.cvtColor((np.clip(sheet, 0, 1) * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 90])


def cut(cfg_path):
    from pymatting import estimate_foreground_ml
    from wear import face_of
    cfg = json.loads(pathlib.Path(cfg_path).read_text())
    out = ROOT / "work" / "people" / (cfg["id"] + "-3d")
    report = json.loads((out / "report.json").read_text())
    x0, y0, x1, y1 = report["crop"]
    final = cv2.imread(str(out / "composite.png"), cv2.IMREAD_UNCHANGED)
    C = cv2.cvtColor(final, cv2.COLOR_BGR2RGB).astype(np.float64) / 65535
    # the portrait as generated, at the size the frame was rendered at, cut as the picture is
    k = int(cfg.get("upscale", 2))
    raw = ROOT / cfg["portrait"]
    up = raw.with_name(f"{raw.stem}-x{k}.png")
    por = cv2.imread(str(up if up.exists() else raw), cv2.IMREAD_COLOR)[y0:y1, x0:x1]
    if por.shape[:2] != C.shape[:2]:
        raise SystemExit(f"{cfg['id']}: the portrait's crop {por.shape[:2]} is not the picture's {C.shape[:2]}")
    rgb = cv2.cvtColor(por, cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    face = face_of(por)
    chin_y = float(face.landmark_3d_68[8, 1])
    a_p, sil, stats = person_matte(rgb, por, chin_y)
    solid, temples, lens, has_lens = frame_layers(cfg, out, (x0, y0, x1, y1))
    # a lens with the backdrop behind it: a filter, letting through its transmission (luminance-weighted;
    # in sRGB terms, as the cut-out is unmixed: a 4% grey lens over white reads 23% in sRGB)
    T = np.asarray(report.get("lens_tint", [0.05, 0.05, 0.05]), np.float64)
    t_srgb = float(np.dot([0.2126, 0.7152, 0.0722], T)) ** (1 / 2.2)
    alpha = 1 - (1 - a_p) * (1 - solid) * (1 - temples) * (1 - lens * (1 - t_srgb))
    alpha = np.clip(alpha, 0, 1)
    F = estimate_foreground_ml(C, alpha.astype(np.float64))
    F = np.clip(F, 0, 1)
    rgba = np.dstack([F, alpha]).astype(np.float32)
    bgra = cv2.cvtColor((rgba * 65535 + 0.5).astype(np.uint16), cv2.COLOR_RGBA2BGRA)
    cv2.imwrite(str(out / "cutout.png"), bgra)
    checks(rgba, np.maximum(solid, temples), out / "cutout-check.jpg")
    # the frame past the person: how much of the cut-out only the renders give
    past = (np.maximum(solid, temples) > 0.5) & (a_p < 0.5)
    info = {"id": cfg["id"], "size": [int(C.shape[1]), int(C.shape[0])], "crop": [x0, y0, x1, y1],
            "person": stats, "frame_past_person_px": int(past.sum()),
            "lens_mask": has_lens, "lens_backdrop_px": int(((lens > 0.5) & (a_p < 0.5)).sum()),
            "lens_transmission_srgb": round(t_srgb, 3), "opaque_share": round(float((alpha > 0.99).mean()), 3)}
    if not has_lens:
        info["note"] = "no lens mask: every lens counted solid (right in a front view, where the face is behind them)"
    (out / "cutout.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--all" in sys.argv:
        args = [str(p) for p in sorted(PEOPLE.glob("*.json"))
                if (ROOT / "work" / "people" / (json.loads(p.read_text())["id"] + "-3d") / "composite.png").exists()]
    for a in args:
        cut(a)
