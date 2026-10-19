#!/usr/bin/env python3
"""Measure a temple face in a lightbox shot and place the GCD on it (docs/brief/07-photography.md, step 8).

    python3 tools/photo/temple_gcd.py IMG_3495 --cols 900:1560:50 --band 650:1350 --hinge-x 1603 \\
        --temple-mm 9 --face-mm 8.5 --length-mm 8.8 [--face-dark 40] [--print x,y x,y x,y x,y]

Prints the "gcd" block for the shot's settings file (content/photography/shots/<shot>.json):
`view` (the Blender render's yaw and pitch, e.g. "yaw-50p8") and `anchors_px` (the emblem's center
and the middles of its four sides, in perspective), with what it measured.

How: in each column of `--cols`, the temple's silhouette (darker than the tent) gives its top and
bottom edge; on gloss black acetate seen from above, the outer face starts below the lit top face
(the first pixel darker than `--face-dark`). Straight lines are fitted to the top of the outer face
and to the bottom edge. On the real temple they are parallel, so where they meet in the picture is the
temple's direction in 3D (the camera's focal length comes from the EXIF). The hinge line, `--face-mm`
tall between the two edges, gives the face's down direction and the scale. The GCD's center sits
0.82 x the temple's height from the hinge and 39% down from its top (the logo kit's ratios,
01-brand-system.md), the emblem reading left to right in the picture.

When the two edges are nearly parallel in the picture (the temple seen side-on along its length),
where they meet is too uncertain to give the foreshortening along the temple. Then the old print
gives it: pass the four corners of its first line ("DARKEST": top left, top right, bottom right,
bottom left as seen) with `--print`. On every frame that line is 7.1 times as long as it is tall
(measured on F01, F03 and F09 where the edges converge well), so its proportions in the picture give
the ratio of the two scales. With `--print` on a shot whose edges do converge, the tool reports the
print's size in mm instead, as a check.
"""
import argparse
import json
import pathlib

import cv2
import numpy as np
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS

ROOT = pathlib.Path(__file__).resolve().parents[2]
PRINT_RATIO = 7.1          # length / height of the old print's "DARKEST" line (F01 6.9, F03 7.4, F09 7.1)
GCD_ASPECT = 509.13 / 1551.96   # the emblem's height / length (gcd-geometry.svg's outline)
MIN_CONVERGENCE_DEG = 2.0  # below this angle between the edges, the print gives the foreshortening
PRINT_TOLERANCE = 0.15     # a 3D model that gets the print's proportions further off than this is not used


def load(shot):
    im = ImageOps.exif_transpose(Image.open(ROOT / "work" / "originals" / f"{shot}.jpg"))
    return np.asarray(im.convert("L"), np.float32)


def focal_px(shot):
    """Focal length in pixels: the 35 mm equivalent is for the sensor's full 4:3 frame (the 16:9
    pictures are crops of it, around the same center)."""
    im = Image.open(ROOT / "work" / "originals" / f"{shot}.jpg")
    ex = {TAGS.get(k, k): v for k, v in (im._getexif() or {}).items()}
    return float(ex["FocalLengthIn35mmFilm"]) / 43.267 * float(np.hypot(ex["ExifImageWidth"], ex["ExifImageHeight"]))


def edges(grey, cols, band, sil, face_dark, face_light=None):
    g = cv2.GaussianBlur(grey, (0, 0), 1.5)
    y0, y1 = band
    out = []
    for x in cols:
        col = g[y0:y1, x]
        d = np.nonzero(col < sil)[0]
        if len(d) < 5:
            continue
        runs = np.split(d, np.nonzero(np.diff(d) > 3)[0] + 1)
        run = max(runs, key=len)
        top, bot = run[0], run[-1]
        face = top
        if face_dark is not None:
            f = np.nonzero(col[top:bot] < face_dark)[0]
            face = top + (f[0] if len(f) else 0)
        elif face_light is not None:
            # seen from high above: a dark top face, then the outer face lit by the tent
            seg = col[top:bot]
            for i in range(5, len(seg) - 10):
                if seg[i - 5:i].mean() < face_light - 2 and seg[i:i + 10].min() > face_light:
                    face = top + i
                    break
        out.append((x, y0 + face, y0 + bot, y0 + top))
    return out


def ray(p, c, f):
    return np.array([(p[0] - c[0]) / f, (p[1] - c[1]) / f, 1.0])


def model_3d(g, q):
    """The temple's direction from where its edges meet, the face's down direction from the hinge
    line, its distance from the hinge line's length; anchors in perspective."""
    c, f, ht, hb, hl = g["c"], g["f"], g["ht"], g["hb"], g["hl"]
    vx = (g["bb"] - g["bs"]) / (g["ms"] - g["mb"])
    vy = g["ms"] * vx + g["bs"]
    d = np.array([vx - c[0], vy - c[1], f]); d /= np.linalg.norm(d)
    if d[2] < 0:
        d = -d
    p = ray((ht + hb) / 2, c, f)
    proj = lambda u: np.array([u[0] - u[2] * p[0], u[1] - u[2] * p[1]])
    e1 = np.cross(d, [0, 0, 1.0]); e1 /= np.linalg.norm(e1)
    e2 = np.cross(d, e1)
    best = None
    for th in np.linspace(0, 2 * np.pi, 14401):
        v = np.cos(th) * e1 + np.sin(th) * e2
        pv = proj(v)
        if pv @ hl <= 0:
            continue
        err = abs(pv[0] * hl[1] - pv[1] * hl[0]) / (np.linalg.norm(pv) + 1e-12)
        if best is None or err < best[0]:
            best = (err, v)
    v = best[1]
    rt, rb = ray(ht, c, f), ray(hb, c, f)
    (s, _), *_ = np.linalg.lstsq(np.stack([rt, -rb], 1), -g["Fm"] * v, rcond=None)
    Pt = s * rt                                  # the measured top edge at the hinge, in mm
    n = np.cross(d, v); n /= np.linalg.norm(n)
    away = d if proj(d) @ g["side"] > 0 else -d  # away from the hinge: toward the stretch measured
    to_img = lambda P: np.array([c[0] + f * P[0] / P[2], c[1] + f * P[1] / P[2]])
    T, L, Hg = g["T"], g["L"], g["Hg"]
    C = Pt + away * (g["along"] * T) + v * (g["down"] * T - g["allowance"])
    e_r = away if proj(away)[0] >= 0 else -away
    pts3 = {"center": C, "left": C - e_r * L / 2, "right": C + e_r * L / 2, "top": C - v * Hg / 2, "bottom": C + v * Hg / 2}
    anchors = {k: to_img(P) for k, P in pts3.items()}
    to_cam = -C / np.linalg.norm(C)
    nn = n if n @ to_cam > 0 else -n
    yaw = np.degrees(np.arctan2(-(to_cam @ e_r), to_cam @ nn))
    pitch = np.degrees(np.arctan2(-(to_cam @ v), np.hypot(to_cam @ nn, to_cam @ e_r)))
    extra = {"model": "3d", "vanishing": [round(float(vx), 1), round(float(vy), 1)]}
    if q is not None:
        def face_uv(xy):
            r = ray(xy, c, f)
            P = (Pt @ n) / (r @ n) * r - Pt
            return np.array([P @ away, P @ v])
        uv = [face_uv(x) for x in q]
        Lp = (np.linalg.norm(uv[1] - uv[0]) + np.linalg.norm(uv[2] - uv[3])) / 2
        Hp = (np.linalg.norm(uv[3] - uv[0]) + np.linalg.norm(uv[2] - uv[1])) / 2
        extra["print_check"] = {"length_mm": round(float(Lp), 2), "height_mm": round(float(Hp), 2), "ratio": round(float(Lp / Hp), 2),
                                "from_hinge_mm": round(float(min(u[0] for u in uv)), 1)}
    return anchors, yaw, pitch, extra


def model_print(g, q):
    """Nearly parallel edges: affine on the face, the scale down from the hinge line, the scale along
    from the old print's proportions."""
    ht, hb, hl = g["ht"], g["hb"], g["hl"]
    ax = np.array([1.0, (g["ms"] + g["mb"]) / 2]); ax /= np.linalg.norm(ax)
    B = np.stack([ax, hl], 1)                     # skewed basis: along the temple, down the hinge line
    k = np.linalg.solve(B, (q - q[0]).T).T
    ext_u = (abs(k[1, 0] - k[0, 0]) + abs(k[2, 0] - k[3, 0])) / 2
    ext_w = (abs(k[3, 1] - k[0, 1]) + abs(k[2, 1] - k[1, 1])) / 2
    s_d = np.linalg.norm(hb - ht) / g["Fm"]
    s_r = s_d * (ext_u / ext_w) / PRINT_RATIO
    away = ax if ((q.mean(0) - ht) @ ax) > 0 else -ax      # away from the hinge: toward the print
    T, L, Hg = g["T"], g["L"], g["Hg"]
    C = ht + away * s_r * (g["along"] * T) + hl * s_d * (g["down"] * T - g["allowance"])
    e_r = away if away[0] >= 0 else -away
    anchors = {"center": C, "left": C - e_r * s_r * L / 2, "right": C + e_r * s_r * L / 2,
               "top": C - hl * s_d * Hg / 2, "bottom": C + hl * s_d * Hg / 2}
    # The face's turn and tilt, for the render: an affine view of a rectangle fixes them (with the
    # temple's far end taken as the farther from the camera). Images of the unit vectors along and
    # down the face: a, b; the scale for a face seen square on, s0, solves
    # (s0^2 - |a|^2)(s0^2 - |b|^2) = (a.b)^2.
    av, bv = e_r * s_r, hl * s_d
    A, Bq, Cq = av @ av, bv @ bv, av @ bv
    s0sq = ((A + Bq) + np.sqrt(max((A + Bq) ** 2 - 4 * (A * Bq - Cq ** 2), 0.0))) / 2
    r3 = np.sqrt(max(0.0, 1 - A / s0sq)) * (-1 if e_r @ away < 0 else 1)   # the far end recedes
    d3 = -Cq / s0sq / r3 if abs(r3) > 1e-6 else np.sqrt(max(0.0, 1 - Bq / s0sq))
    nz = abs(av[0] * bv[1] - av[1] * bv[0]) / s0sq
    yaw = np.degrees(np.arctan2(r3, nz))
    pitch = np.degrees(np.arctan2(d3, np.hypot(nz, r3)))
    extra = {"model": "affine (print)", "px_per_mm": {"along": round(float(s_r), 2), "down": round(float(s_d), 2)},
             "print_px": {"along": round(float(ext_u), 1), "down": round(float(ext_w), 1)}}
    return anchors, yaw, pitch, extra


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("shot")
    ap.add_argument("--cols", required=True, help="x0:x1:step, columns across a straight stretch of the temple")
    ap.add_argument("--band", required=True, help="y0:y1 to search in")
    ap.add_argument("--sil", type=float, default=150, help="silhouette threshold (grey, 0-255)")
    ap.add_argument("--face-dark", type=float, default=None,
                    help="the outer face starts at the first pixel darker than this below the silhouette's top "
                         "(gloss black seen from above: 40, 70 on brighter gloss); omit when no top face shows")
    ap.add_argument("--face-light", type=float, default=None,
                    help="seen from high above, the top face is dark and the outer face lit: it starts where the grey "
                         "first rises above this and stays (about 22 on black acetate)")
    ap.add_argument("--hinge-x", type=float, help="the hinge line, upright at this x")
    ap.add_argument("--hinge", nargs=2, help="or the hinge line as two points x,y x,y (top, bottom)")
    ap.add_argument("--temple-mm", type=float, required=True, help="the temple's height at the hinge (06-products.md)")
    ap.add_argument("--face-mm", type=float, required=True, help="the real height between the two measured edges at the hinge")
    ap.add_argument("--length-mm", type=float, required=True, help="the GCD's length (06-products.md)")
    ap.add_argument("--along", type=float, default=0.82)
    ap.add_argument("--down", type=float, default=0.39)
    ap.add_argument("--print", dest="print_", nargs=4, help="the old print's first line: corners x,y (TL TR BR BL)")
    ap.add_argument("--model", choices=["auto", "3d", "print"], default="auto", help="force one model (to compare them)")
    a = ap.parse_args()

    grey = load(a.shot)
    H, W = grey.shape
    c = np.array([W / 2, H / 2])
    f = focal_px(a.shot)
    cols = range(*[int(v) for v in a.cols.split(":")])
    pts = edges(grey, cols, [int(v) for v in a.band.split(":")], a.sil, a.face_dark, a.face_light)
    xs = np.array([p[0] for p in pts], float)
    mt, bt = np.polyfit(xs, [p[1] for p in pts], 1)          # the outer face's top edge
    mb, bb = np.polyfit(xs, [p[2] for p in pts], 1)          # the bottom edge
    ms, bs = np.polyfit(xs, [p[3] for p in pts], 1)          # the silhouette's top
    res_t = np.std(np.array([p[1] for p in pts]) - (mt * xs + bt))
    res_b = np.std(np.array([p[2] for p in pts]) - (mb * xs + bb))
    # The temple's direction comes from the silhouette's top and the bottom edge: crisp edges against
    # the tent, parallel on the real temple. The outer face's top edge on gloss acetate is a highlight's
    # boundary and can bend with the surface; it only gives the hinge line's top.
    if a.hinge:
        (tx, ty), (bx, by) = [[float(v) for v in s.split(",")] for s in a.hinge]
        # the hinge line's ends on the two fitted edges
        def meet(m, b):
            dx, dy = bx - tx, by - ty
            t = (m * tx + b - ty) / (dy - m * dx)
            return np.array([tx + t * dx, ty + t * dy])
        ht, hb = meet(mt, bt), meet(mb, bb)
    else:
        X = a.hinge_x
        ht, hb = np.array([X, mt * X + bt]), np.array([X, mb * X + bb])
    hl = (hb - ht) / np.linalg.norm(hb - ht)
    conv = abs(np.degrees(np.arctan(ms) - np.arctan(mb)))
    T, Fm, L = a.temple_mm, a.face_mm, a.length_mm
    Hg = L * GCD_ASPECT
    allowance = T - Fm                       # the temple's top above the measured top edge
    report = {"shot": a.shot, "focal_px": round(f, 1), "edges": {"silhouette_top": [round(ms, 4), round(bs, 1)], "face_top": [round(mt, 4), round(bt, 1)],
              "bottom": [round(mb, 4), round(bb, 1)],
              "fit_px": [round(float(res_t), 1), round(float(res_b), 1)], "convergence_deg": round(conv, 2)},
              "hinge": {"top": ht.round(1).tolist(), "bottom": hb.round(1).tolist()}}

    q = np.array([[float(v_) for v_ in s_.split(",")] for s_ in a.print_]) if a.print_ else None
    geo = dict(c=c, f=f, ht=ht, hb=hb, hl=hl, ms=ms, bs=bs, mb=mb, bb=bb, T=T, Fm=Fm, L=L, Hg=Hg,
               allowance=allowance, along=a.along, down=a.down, side=np.array([xs.mean(), np.mean([p_[1] for p_ in pts])]) - ht)
    result = None
    if a.model == "3d":
        result = model_3d(geo, q)
    elif a.model == "print":
        result = model_print(geo, q)
    elif conv >= MIN_CONVERGENCE_DEG:
        result = model_3d(geo, q)
        chk = result[3].get("print_check")
        if chk and abs(chk["ratio"] / PRINT_RATIO - 1) > PRINT_TOLERANCE:
            report["note"] = ("the 3D model gets the print's proportions %.2f (expected %.1f): the edges' meeting point is "
                              "too uncertain; the print gives the foreshortening instead" % (chk["ratio"], PRINT_RATIO))
            report["rejected_3d"] = result[3]
            result = None
    if result is None:
        if q is None:
            raise SystemExit("the temple's edges hardly converge (%.2f deg): pass the old print's corners with --print" % conv)
        result = model_print(geo, q)
    anchors, yaw, pitch, extra = result
    report.update(extra)
    report["gcd"] = {"view": f"yaw{int(round(yaw))}p{int(round(pitch))}", "anchors_px": {k: [round(float(p_[0]), 1), round(float(p_[1]), 1)] for k, p_ in anchors.items()},
                     "length_mm": L}
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
