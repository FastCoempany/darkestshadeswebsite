#!/usr/bin/env python3
"""Measure a temple face in a lightbox shot and place the GCD on it (docs/brief/07-photography.md, step 8).

    python3 tools/photo/temple_gcd.py IMG_3483 --cols 500:1020:20 --band 600:1050 \\
        --hinge 1040.6,718 1055.3,898 --temple-mm 9.65 --face-mm 9.65 --seam-mm 0.97 --length-mm 9.3 \\
        --print 654,786.4 786,779.7 786,827.1 654,830.7

Prints the "gcd" block for the shot's settings file (content/photography/shots/<shot>.json):
`view` (the Blender render's yaw and pitch, e.g. "yaw-50p8") and `anchors_px` (the emblem's center
and the middles of its four sides, in perspective), with what it measured.

What it needs from the picture, all measured, never judged by eye (column and row profiles, local
contrast; by eye, readings come out tens of pixels off):
- the temple's edges: in each column of `--cols`, the silhouette (darker than the tent) gives its top
  and bottom; on gloss acetate seen from above, the outer face starts below the lit top face (the
  first pixel darker than `--face-dark`). Lines are fitted to them, without the columns where the
  trace caught something else. Where another temple touches this one in the picture, measure the
  two lines by hand and pass them with `--edges`.
- the hinge line (`--hinge`, two points on it): the seam where the temple's face ends and the
  end-piece begins. Not the front's edge: on F03 the end-piece's side runs about 7 mm on from the
  seam, and taking the front's edge for the hinge puts the GCD on the end-piece.
- the seam's slant from the side drawing (`--seam-mm`: how far it runs along the temple from the
  temple's top edge to its bottom edge, where the temple's edge lines start): F01 1.9, F03 0, F06
  0.97, F09 3.19. Square to the temple is then not along the seam; the old print's letters stand
  square to the temple, and their tilt from the seam in the picture matches.
- the old print's first line ("DARKEST": top left, top right, bottom right, bottom left as seen,
  measured from its strokes) with `--print`.

The GCD's center sits 0.82 x the temple's height from the hinge (from the seam at its own height)
and 39% down from the top (the logo kit's ratios, 01-brand-system.md), the emblem along the temple,
square to it, reading left to right in the picture.

Three models of the face:
- 3d: the temple's top and bottom edges are parallel on the frame, so where they meet in the picture is
  its direction in 3D (the camera's focal length comes from the EXIF); the hinge line, `--face-mm` tall,
  gives the face's down direction and its distance. It needs a stretch long enough for the temple's
  height to change clearly across it (`edges.height_change_px`, 30 px or more). With `--print` it
  reports where the print lies in mm (`print_check.ends_mm`) and its length.
- ruler: the print's two ends lie at known distances from the hinge on every shot of a frame
  (`--print-mm d1,d2`, from the 3D model's print_check on the frame's best shot). The hinge and the
  print's ends, three points along the temple at known distances, fix the perspective along it. With
  only the far end (`--print-mm d2`, when the near end is too faint), the edges' convergence gives the
  perspective instead.
- print: the print's proportions (its first line 7.1 times as long as tall). A last resort: the line's
  height is too small to measure well (a 4 px halo on 45 px is 10%), and on F01, F03 and F06 it drew
  the GCD up to a third too short.
Per frame, the 3D model runs on the shot where the temple's edges converge most and the print check
holds; that shot's print positions are the ruler for the frame's other shots, where the 3D model, if
it holds, is a cross-check.

A face that isn't a straight temple (F04's and F05's triangular end-pieces) is placed from the 1:1
drawing instead: four points of the face known both in the side view (content/products/drawings/
F0X-side.svg, in mm) and in the picture give its perspective, and the GCD goes where the drawing says,
along the drawing's x axis. On F04 and F05 the end-piece and the front's side form one flat face, from
the front's corner to the hinge where the wire goes in, so the four points are the hinge's top and
bottom (the wire's edges at its collar) and the front corner's top and bottom (where the end-piece's
top and bottom edges meet it). Check the fit by drawing the drawing's outline over the picture:

    python3 tools/photo/temple_gcd.py IMG_3456 --face-mm 25.0,8.9 25.0,11.85 2.3,3.2 3.5,18.3 \\
        --face-px 1229,2648 1231,2717 1617,2535 1620,2887 --center-mm 17.8,11.1 --length-mm 8.8
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


def robust_line(xs, ys, k=3.0, floor=0.5):
    """Least-squares line y = m x + c, refitted without the columns further off than k robust sigmas
    (where the trace caught a reflection, the print or the other temple)."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    keep = np.ones(len(xs), bool)
    for _ in range(4):
        m, c = np.polyfit(xs[keep], ys[keep], 1)
        r = ys - (m * xs + c)
        sig = max(1.4826 * float(np.median(np.abs(r[keep]))), floor)
        new = np.abs(r) <= k * sig
        if new.sum() < 5 or (new == keep).all():
            break
        keep = new
    m, c = np.polyfit(xs[keep], ys[keep], 1)
    return m, c, float(np.std(ys[keep] - (m * xs[keep] + c))), int((~keep).sum())


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
    away = d if proj(d) @ g["side"] > 0 else -d  # away from the hinge: toward the stretch measured
    k = g["k"]                                   # the seam's run along the temple per mm down (the drawing)
    best = None
    for th in np.linspace(0, 2 * np.pi, 14401):
        v = np.cos(th) * e1 + np.sin(th) * e2
        pv = proj(v + k * away)                  # the seam: down the face, and k along it
        if pv @ hl <= 0:
            continue
        err = abs(pv[0] * hl[1] - pv[1] * hl[0]) / (np.linalg.norm(pv) + 1e-12)
        if best is None or err < best[0]:
            best = (err, v)
    v = best[1]
    rt, rb = ray(ht, c, f), ray(hb, c, f)
    (s, _), *_ = np.linalg.lstsq(np.stack([rt, -rb], 1), -g["Fm"] * (v + k * away), rcond=None)
    Pt = s * rt                                  # the measured top edge at the hinge, in mm
    n = np.cross(d, v); n /= np.linalg.norm(n)
    to_img = lambda P: np.array([c[0] + f * P[0] / P[2], c[1] + f * P[1] / P[2]])
    T, L, Hg = g["T"], g["L"], g["Hg"]
    vc = g["down"] * T - g["allowance"]
    # 0.82 T from the hinge where the GCD sits: from the seam at the GCD's height
    C = Pt + away * (g["along"] * T + k * vc) + v * vc
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
            # along: from the seam at the point's own height
            r = ray(xy, c, f)
            P = (Pt @ n) / (r @ n) * r - Pt
            return np.array([P @ away - k * (P @ v), P @ v])
        uv = [face_uv(x) for x in q]
        Lp = (np.linalg.norm(uv[1] - uv[0]) + np.linalg.norm(uv[2] - uv[3])) / 2
        Hp = (np.linalg.norm(uv[3] - uv[0]) + np.linalg.norm(uv[2] - uv[1])) / 2
        ends = sorted([(uv[0][0] + uv[3][0]) / 2, (uv[1][0] + uv[2][0]) / 2])
        extra["print_check"] = {"length_mm": round(float(Lp), 2), "height_mm": round(float(Hp), 2), "ratio": round(float(Lp / Hp), 2),
                                "from_hinge_mm": round(float(min(u[0] for u in uv)), 1),
                                "ends_mm": [round(float(e), 2) for e in ends]}
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
    # face point (u from the seam at its height, v down from the measured top edge) to the picture
    at = lambda u, v: ht + away * s_r * u + hl * s_d * v
    anchors, yaw, pitch = gcd_on_face(at, g, away)
    extra = {"model": "affine (print)", "px_per_mm": {"along": round(float(s_r), 2), "down": round(float(s_d), 2)},
             "print_px": {"along": round(float(ext_u), 1), "down": round(float(ext_w), 1)}}
    return anchors, yaw, pitch, extra


def model_ruler(g, q, print_mm):
    """The old print as a ruler of known size: its ends lie d1 and d2 mm from the hinge (print_check's
    ends_mm on a shot of the same frame where the 3D model holds). Along the temple the picture is
    t = A u / (1 + B u) (u in mm from the hinge, t in px), with the face's scale down shrinking with the
    same depth, s_d / (1 + B u). With both ends (d1,d2), the hinge and the two ends fix A and B. With
    the far end only (d2, when the near end is too faint to place), the edges give B: lines that are
    parallel on the temple shrink toward their meeting point, so the temple's height at the print's
    far end against its height at the hinge is the depth ratio 1 + B d2."""
    ht, hb, hl = g["ht"], g["hb"], g["hl"]
    ax = np.array([1.0, (g["ms"] + g["mb"]) / 2]); ax /= np.linalg.norm(ax)
    Bm = np.stack([ax, hl], 1)
    k = np.linalg.solve(Bm, (q - ht).T).T                  # along (parallel to the hinge line), down
    away = ax if k[:, 0].mean() > 0 else -ax
    t = np.abs(k[:, 0])
    ends_px = sorted([(t[0] + t[3]) / 2, (t[1] + t[2]) / 2])
    if len(print_mm) == 2:
        d1, d2 = print_mm
        t1, t2 = ends_px
        B = (t1 * d2 / d1 - t2) / (d2 * (t2 - t1))
        A = t1 * (1 + B * d1) / d1
    else:
        d2 = print_mm[0]
        t2 = ends_px[1]
        far = q[[0, 3]] if t[0] + t[3] > t[1] + t[2] else q[[1, 2]]
        x_far, x_h = far[:, 0].mean(), (ht[0] + hb[0]) / 2
        h = lambda x: (g["mb"] * x + g["bb"]) - (g["ms"] * x + g["bs"])
        depth = h(x_h) / h(x_far)                          # 1 + B d2
        B = (depth - 1) / d2
        A = t2 * depth / d2
    s_d = np.linalg.norm(hb - ht) / g["Fm"]
    def at(u, v):
        return ht + away * (A * u / (1 + B * u)) + hl * s_d * v / (1 + B * u)
    uc = g["along"] * g["T"]
    anchors, yaw, pitch = gcd_on_face(at, g, away)
    s_along = A / (1 + B * uc) ** 2
    s_down = s_d / (1 + B * uc)
    extra = {"model": "ruler (print of known size%s)" % (", far end and the edges" if len(print_mm) == 1 else ""),
             "px_per_mm": {"along": round(float(s_along), 2), "down": round(float(s_down), 2)},
             "perspective_per_mm": round(float(B), 5), "print_mm": list(print_mm),
             "print_px_from_hinge": [round(float(v), 1) for v in ends_px]}
    return anchors, yaw, pitch, extra


def gcd_on_face(at, g, away):
    """The GCD's anchors and the render's view from a map of the face into the picture: at(u, v),
    u in mm along the temple from the seam at that height, v in mm down from the measured top edge.
    The emblem runs along the temple and stands square to it; where the seam slants (k mm along per
    mm down, from the drawing), square to the temple is not along the seam."""
    T, L, Hg, k = g["T"], g["L"], g["Hg"], g["k"]
    uc, vc = g["along"] * T, g["down"] * T - g["allowance"]
    e_sign = 1 if away[0] >= 0 else -1
    lo, hi = at(uc - L / 2, vc), at(uc + L / 2, vc)
    left, right = (lo, hi) if e_sign > 0 else (hi, lo)
    anchors = {"center": at(uc, vc), "left": left, "right": right,
               "top": at(uc + k * Hg / 2, vc - Hg / 2), "bottom": at(uc - k * Hg / 2, vc + Hg / 2)}
    # The face's turn and tilt, for the render: an affine view of a rectangle fixes them (with the
    # temple's far end taken as the farther from the camera), from the images of the unit vectors
    # along and down the face at the GCD.
    av = (at(uc + 0.5, vc) - at(uc - 0.5, vc)) * e_sign
    bv = at(uc - k * 0.5, vc + 0.5) - at(uc + k * 0.5, vc - 0.5)
    yaw, pitch, _ = affine_view(av, bv, -1 if e_sign < 0 else 1)
    return anchors, yaw, pitch


def affine_view(av, bv, far_sign):
    """The turn and tilt of a face from the images of its unit vectors along (av, reading left to
    right) and down (bv), in an affine view: the scale square on, s0, solves
    (s0^2 - |a|^2)(s0^2 - |b|^2) = (a.b)^2; far_sign says which way along recedes (-1: its left end)."""
    A, Bq, Cq = av @ av, bv @ bv, av @ bv
    s0sq = ((A + Bq) + np.sqrt(max((A + Bq) ** 2 - 4 * (A * Bq - Cq ** 2), 0.0))) / 2
    r3 = np.sqrt(max(0.0, 1 - A / s0sq)) * far_sign
    d3 = -Cq / s0sq / r3 if abs(r3) > 1e-6 else np.sqrt(max(0.0, 1 - Bq / s0sq))
    nz = abs(av[0] * bv[1] - av[1] * bv[0]) / s0sq
    return np.degrees(np.arctan2(r3, nz)), np.degrees(np.arctan2(d3, np.hypot(nz, r3))), float(np.sqrt(s0sq))


def face_from_drawing(a):
    """A flat face located by points known both in the side drawing (mm) and in the picture: four or
    more give its perspective (a homography, least squares past four), three an affine map. The GCD
    lies along the drawing's x axis, centered at --center-mm."""
    mm = np.array([[float(v) for v in s_.split(",")] for s_ in a.face_mm], np.float64)
    px = np.array([[float(v) for v in s_.split(",")] for s_ in a.face_px], np.float64)
    if len(mm) < 3 or len(mm) != len(px):
        raise SystemExit("--face-mm and --face-px take the same three or more points")
    if len(mm) >= 4:
        Hm, _ = cv2.findHomography(mm, px, 0)
    else:
        Hm = np.vstack([cv2.getAffineTransform(mm.astype(np.float32), px.astype(np.float32)), [0, 0, 1]])
    def to_px(x, y):
        v = Hm @ np.array([x, y, 1.0])
        return v[:2] / v[2]
    resid = [float(np.linalg.norm(to_px(*m_) - q)) for m_, q in zip(mm, px)]
    cx, cy = [float(v) for v in a.center_mm.split(",")]
    L = a.length_mm
    Hg = L * GCD_ASPECT
    C = to_px(cx, cy)
    ends = sorted([to_px(cx - L / 2, cy), to_px(cx + L / 2, cy)], key=lambda q: q[0])   # reads left to right
    tb = sorted([to_px(cx, cy - Hg / 2), to_px(cx, cy + Hg / 2)], key=lambda q: q[1])
    anchors = {"center": C, "left": ends[0], "right": ends[1], "top": tb[0], "bottom": tb[1]}
    # the face's turn and tilt at the GCD, for the render's shading, from the local scales; the
    # drawing's x grows from the front toward the temple's end, which recedes
    ax_img = to_px(cx + 1, cy) - C
    dn_img = to_px(cx, cy + 1) - C
    e_r = ax_img if ax_img[0] >= 0 else -ax_img
    e_d = dn_img if dn_img[1] >= 0 else -dn_img
    yaw, pitch, s0 = affine_view(e_r, e_d, 1 if ax_img[0] >= 0 else -1)
    return {"shot": a.shot, "model": "face from the drawing (%s)" % ("perspective" if len(mm) >= 4 else "affine"),
            "fit_px": [round(r_, 1) for r_ in resid],
            "px_per_mm": {"along": round(float(np.linalg.norm(ax_img)), 2), "down": round(float(np.linalg.norm(dn_img)), 2),
                          "square_on": round(s0, 2)},
            "gcd": {"view": f"yaw{int(round(yaw))}p{int(round(pitch))}",
                    "anchors_px": {k: [round(float(v[0]), 1), round(float(v[1]), 1)] for k, v in anchors.items()},
                    "length_mm": L}}

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("shot")
    ap.add_argument("--cols", help="x0:x1:step, columns across a straight stretch of the temple")
    ap.add_argument("--band", help="y0:y1 to search in")
    ap.add_argument("--sil", type=float, default=150, help="silhouette threshold (grey, 0-255)")
    ap.add_argument("--face-dark", type=float, default=None,
                    help="the outer face starts at the first pixel darker than this below the silhouette's top "
                         "(gloss black seen from above: 40, 70 on brighter gloss); omit when no top face shows")
    ap.add_argument("--face-light", type=float, default=None,
                    help="seen from high above, the top face is dark and the outer face lit: it starts where the grey "
                         "first rises above this and stays (about 22 on black acetate)")
    ap.add_argument("--edges", nargs=2, help="m,c m,c: the outer face's top and bottom edge lines y = m x + c, measured by hand "
                    "(when another temple touches this one in the picture and the automatic trace can't separate them)")
    ap.add_argument("--hinge-x", type=float, help="the hinge line, upright at this x")
    ap.add_argument("--hinge", nargs=2, help="or the hinge line as two points x,y x,y (top, bottom)")
    ap.add_argument("--temple-mm", type=float, help="the temple's height at the hinge (06-products.md)")
    ap.add_argument("--face-mm", nargs="+", help="the real height between the two measured edges at the hinge; "
                    "or, with --face-px, three or more points x,y of a face in the side drawing's millimetres")
    ap.add_argument("--face-px", nargs="+", help="the same points x,y in the picture (three or more)")
    ap.add_argument("--center-mm", help="x,y: the GCD's center in the side drawing's millimetres")
    ap.add_argument("--length-mm", type=float, required=True, help="the GCD's length (06-products.md)")
    ap.add_argument("--seam-mm", type=float, default=0.0,
                    help="how far the hinge line runs along the temple from the temple's top edge to its bottom edge, in mm "
                         "(positive toward the tip), from the side drawing: where the temple's edge lines start")
    ap.add_argument("--along", type=float, default=0.82)
    ap.add_argument("--down", type=float, default=0.39)
    ap.add_argument("--print", dest="print_", nargs=4, help="the old print's first line: corners x,y (TL TR BR BL)")
    ap.add_argument("--print-mm", help="d1,d2: the print's near and far ends in mm from the hinge (print_check's ends_mm on a "
                    "shot of the same frame where the 3D model holds), or d2 alone when the near end is too faint to place: "
                    "makes the print a ruler")
    ap.add_argument("--model", choices=["auto", "3d", "print", "ruler"], default="auto", help="force one model (to compare them)")
    a = ap.parse_args()
    if a.face_px:
        print(json.dumps(face_from_drawing(a), indent=1))
        return
    a.face_mm = float(a.face_mm[0])

    grey = load(a.shot)
    H, W = grey.shape
    c = np.array([W / 2, H / 2])
    f = focal_px(a.shot)
    if a.edges:
        (mt, bt), (mb, bb) = [[float(v) for v in e.split(",")] for e in a.edges]
        ms, bs = mt, bt
        res_t = res_b = 0.0
        dropped = [0, 0, 0]
        x_lo, x_hi = (a.hinge_x - 400, a.hinge_x) if a.hinge_x else (0, 1)
        xs = np.linspace(x_lo, x_hi, 9)
        pts = [(x, mt * x + bt, mb * x + bb, mt * x + bt) for x in xs]
    else:
        cols = range(*[int(v) for v in a.cols.split(":")])
        pts = edges(grey, cols, [int(v) for v in a.band.split(":")], a.sil, a.face_dark, a.face_light)
        xs = np.array([p[0] for p in pts], float)
        mt, bt, res_t, drop_t = robust_line(xs, [p[1] for p in pts])    # the outer face's top edge
        mb, bb, res_b, drop_b = robust_line(xs, [p[2] for p in pts])    # the bottom edge
        ms, bs, _, drop_s = robust_line(xs, [p[3] for p in pts])        # the silhouette's top
        dropped = [drop_t, drop_b, drop_s]
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
              "fit_px": [round(float(res_t), 1), round(float(res_b), 1)], "columns_dropped": dropped,
              "convergence_deg": round(conv, 2),
              # how much the temple's height changes across the stretch measured: the meeting point is
              # only as good as this is large against the fit (a long stretch beats a steep angle)
              "height_change_px": round(float(abs((ms - mb) * (xs.max() - xs.min()))), 1)},
              "hinge": {"top": ht.round(1).tolist(), "bottom": hb.round(1).tolist()}}

    q = np.array([[float(v_) for v_ in s_.split(",")] for s_ in a.print_]) if a.print_ else None
    geo = dict(c=c, f=f, ht=ht, hb=hb, hl=hl, ms=ms, bs=bs, mb=mb, bb=bb, T=T, Fm=Fm, L=L, Hg=Hg,
               allowance=allowance, along=a.along, down=a.down, k=a.seam_mm / T, side=np.array([xs.mean(), np.mean([p_[1] for p_ in pts])]) - ht)
    result = None
    if a.model == "3d":
        result = model_3d(geo, q)
    elif a.model == "print":
        result = model_print(geo, q)
    elif a.model == "ruler":
        result = model_ruler(geo, q, [float(v) for v in a.print_mm.split(",")])
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
        result = model_ruler(geo, q, [float(v) for v in a.print_mm.split(",")]) if a.print_mm else model_print(geo, q)
    anchors, yaw, pitch, extra = result
    report.update(extra)
    report["gcd"] = {"view": f"yaw{int(round(yaw))}p{int(round(pitch))}", "anchors_px": {k: [round(float(p_[0]), 1), round(float(p_[1]), 1)] for k, p_ in anchors.items()},
                     "length_mm": L}
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
