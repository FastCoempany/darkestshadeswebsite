#!/usr/bin/env python3
"""The generated person's head in 3D, from the portrait alone, for wear3d.py: a depth map of the head
(Depth Anything V2 Small, Apache-2.0, ONNX from github.com/fabio-sim/Depth-Anything-ONNX, in
work/models/), put in millimetres by the face's 3D landmarks (InsightFace), and the scene's key light
read off the face's shading.

The depth model gives relative inverse depth (nearer is larger, scale and offset unknown). The face's
68 3D landmarks give real depths for the points they mark (the portrait's lens and the person's
pupillary distance give the scale); inverse depth is fitted to them, over the inner face, where both
agree to a few millimetres. At the face's edge the model's depth is too shallow (the ears and the
jaw's ends read about half as deep as the landmarks put them); nothing there carries the frame's
shadows, which fall on the brows, eyes, nose and cheeks.
"""
import pathlib

import cv2
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODEL = ROOT / "work" / "models" / "depth_anything_v2_vits.onnx"
# The portrait's principal point (pixels): where the lens's axis meets the picture. None: its centre.
# wear3d.py sets it at the eyes' height (the portraits are prompted at eye level, the head placed in
# the picture's upper half: a level camera, the picture cropped below the axis).
PP = None


def cx_(W):
    return PP[0] if PP else W / 2


def cy_(H):
    return PP[1] if PP else H / 2
MODEL_URL = "https://github.com/fabio-sim/Depth-Anything-ONNX/releases/download/v2.0.0/depth_anything_v2_vits.onnx"


def disparity(crop_bgr):
    """Depth Anything V2 Small on a square crop: relative inverse depth at the crop's size."""
    import onnxruntime as ort
    if not MODEL.exists():
        raise SystemExit(f"missing {MODEL}; download {MODEL_URL}")
    sess = ort.InferenceSession(str(MODEL), providers=["CPUExecutionProvider"])
    n = sess.get_inputs()[0].shape[-1]
    x = cv2.resize(crop_bgr, (n, n), interpolation=cv2.INTER_AREA)[..., ::-1].astype(np.float32) / 255
    x = (x - np.array([0.485, 0.456, 0.406], np.float32)) / np.array([0.229, 0.224, 0.225], np.float32)
    d = sess.run(None, {sess.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0]
    return cv2.resize(d, (crop_bgr.shape[1], crop_bgr.shape[0]), interpolation=cv2.INTER_CUBIC)


def landmark_depths(L, s, D_eyes):
    """The landmarks' depths (mm along the optical axis): the eyes at D_eyes, the rest by InsightFace's
    z (pixels, the image's scale), over the scale s (px/mm)."""
    return D_eyes + (L[:, 2] - L[36:48, 2].mean()) / s


def depth_map(img, face, s, f_px):
    """Depth (mm, along the optical axis) of every pixel in a square round the head, and that square
    (x0, y0, x1, y1). Pixels the fit cannot place (the backdrop) are inf."""
    H, W = img.shape[:2]
    x0, y0, x1, y1 = face.bbox
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 - 0.1 * (y1 - y0)
    side = 2.0 * (x1 - x0)
    box = [int(max(0, cx - side / 2)), int(max(0, cy - side / 2)), int(min(W, cx + side / 2)),
           int(min(H, cy + side / 2))]
    crop = img[box[1]:box[3], box[0]:box[2]]
    d = disparity(crop)
    L = face.landmark_3d_68.astype(np.float64)
    D_eyes = f_px / s
    Dl = landmark_depths(L, s, D_eyes)
    u = np.clip((L[:, 0] - box[0]).round().astype(int), 0, d.shape[1] - 1)
    v = np.clip((L[:, 1] - box[1]).round().astype(int), 0, d.shape[0] - 1)
    dl = d[v, u]
    inner = np.r_[17:68]                                   # brows, nose, eyes, mouth: not the jaw line
    A = np.stack([dl, np.ones_like(dl)], 1)
    coef, *_ = np.linalg.lstsq(A[inner], 1 / Dl[inner], rcond=None)
    inv = coef[0] * d + coef[1]
    D = np.where(inv > 1e-6, 1 / np.maximum(inv, 1e-9), np.inf)
    # the backdrop: the model's far plateau, below a quarter of the way up from it to the face's level
    # (the fit, made on the face, puts the backdrop only a hand's breadth behind the head)
    far, near = np.percentile(d, 2), np.median(dl[inner])
    back = d < far + 0.25 * (near - far)
    back = cv2.dilate(back.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    D[back | (D > D_eyes + 350)] = np.inf
    res = 1 / (A @ coef) - Dl
    fit = {"rms_inner_mm": round(float(np.sqrt(np.mean(res[inner] ** 2))), 2),
           "rms_jaw_mm": round(float(np.sqrt(np.mean(res[:17] ** 2))), 1), "box": box}
    return D, box, fit


def side_corrected(D, box, face, s, f_px):
    """The depth map with the sides of the head pushed back to where the jaw line's landmarks put them
    (the model reads the ears and the jaw's ends about half as deep): a correction growing with the
    distance from the face's midline, k * |x|^p, fitted to the jaw line's 17 points. For hiding the
    temples behind the head, not for the face's own shape (inside the brows, eyes and nose it is a
    few millimetres at most)."""
    L = face.landmark_3d_68.astype(np.float64)
    Dl = landmark_depths(L, s, f_px / s)
    u = np.clip((L[:, 0] - box[0]).round().astype(int), 0, D.shape[1] - 1)
    v = np.clip((L[:, 1] - box[1]).round().astype(int), 0, D.shape[0] - 1)
    res = Dl - D[v, u]
    xc, half = L[27, 0], (L[16, 0] - L[0, 0]) / 2
    xr = np.abs(L[:, 0] - xc) / half
    jaw = np.r_[0:17]
    ok = np.isfinite(res[jaw])
    best = None
    for p in np.arange(1.5, 8.01, 0.25):
        b = xr[jaw][ok] ** p
        k = max(float(np.dot(b, res[jaw][ok]) / np.dot(b, b)), 0.0)
        e = float(np.sqrt(np.mean((res[jaw][ok] - k * b) ** 2)))
        if best is None or e < best[0]:
            best = (e, p, k)
    _, p, k = best
    xx = box[0] + np.arange(D.shape[1])[None, :] + 0.5
    corr = k * np.minimum(np.abs(xx - xc) / half, 1.3) ** p
    return D + corr, {"k_mm": round(k, 1), "p": float(p), "rms_jaw_after_mm": round(best[0], 1)}


def sample_depth(D, box, u, v):
    """Bilinear depth at image points (u, v) (arrays); inf off the map or on the backdrop."""
    x = np.asarray(u, np.float64) - box[0]
    y = np.asarray(v, np.float64) - box[1]
    h, w = D.shape
    ok = (x >= 0) & (x < w - 1) & (y >= 0) & (y < h - 1)
    xi = np.clip(np.floor(x).astype(int), 0, w - 2)
    yi = np.clip(np.floor(y).astype(int), 0, h - 2)
    fx, fy = x - xi, y - yi
    q = D[yi, xi] * (1 - fx) * (1 - fy) + D[yi, xi + 1] * fx * (1 - fy) + D[yi + 1, xi] * (1 - fx) * fy \
        + D[yi + 1, xi + 1] * fx * fy
    return np.where(ok, q, np.inf)


def mesh(D, box, H, W, f_px, step=3, jump_mm=10.0):
    """The depth map as a mesh in camera space (mm; x right, y up, the camera looking down -z), with a
    UV per vertex that is its pixel in the portrait. Quads that straddle a jump in depth (an ear's
    edge, the hair against the backdrop) are left out."""
    Ds = D[::step, ::step]
    h, w = Ds.shape
    yy, xx = np.mgrid[0:h, 0:w]
    u = box[0] + xx * step + 0.5
    v = box[1] + yy * step + 0.5
    ok = np.isfinite(Ds)
    idx = -np.ones((h, w), np.int64)
    idx[ok] = np.arange(ok.sum())
    Dv = Ds[ok]
    X = (u[ok] - cx_(W)) / f_px * Dv
    Y = (cy_(H) - v[ok]) / f_px * Dv
    V = np.stack([X, Y, -Dv], 1)
    UV = np.stack([u[ok] / W, 1 - v[ok] / H], 1)
    a, b, c, d = idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]
    good = (a >= 0) & (b >= 0) & (c >= 0) & (d >= 0)
    q = np.stack([a[good], d[good], c[good], b[good]], 1)
    z = Dv[q]
    q = q[(z.max(1) - z.min(1)) < jump_mm * step / 3]
    return V, q, UV


def normals_from_depth(D, box, H, W, f_px):
    """Per-pixel camera-space positions and normals (towards the camera) of the depth map."""
    h, w = D.shape
    yy, xx = np.mgrid[0:h, 0:w]
    u = box[0] + xx + 0.5
    v = box[1] + yy + 0.5
    Dz = np.where(np.isfinite(D), D, np.nan)
    P = np.stack([(u - cx_(W)) / f_px * Dz, (cy_(H) - v) / f_px * Dz, -Dz], -1)
    dx = np.gradient(P, axis=1)
    dy = np.gradient(P, axis=0)
    N = np.cross(dx, dy)
    N /= np.linalg.norm(N, axis=-1, keepdims=True) + 1e-9
    N = np.where(N[..., 2:3] < 0, -N, N)
    return P, N


def light_scores(lin, face, D, box, f_px, H, W, step=3):
    """How well a key light from each direction explains the face's shading: the correlation of the
    portrait's skin brightness with a Lambertian face lit from (azimuth, elevation), shadows ignored,
    over the inner face (eyes, brows, lips and nostrils left out). Azimuth + to the camera's right."""
    L = face.landmark_3d_68.astype(np.float64)
    Ds = cv2.resize(np.where(np.isfinite(D), D, 1e5).astype(np.float32), (D.shape[1] // step, D.shape[0] // step),
                    interpolation=cv2.INTER_AREA)
    bs = [box[0], box[1]]
    h, w = Ds.shape
    yy, xx = np.mgrid[0:h, 0:w]
    u = bs[0] + (xx + 0.5) * step
    v = bs[1] + (yy + 0.5) * step
    Dz = np.where(Ds > 5e4, np.nan, Ds)
    P = np.stack([(u - cx_(W)) / f_px * Dz, (cy_(H) - v) / f_px * Dz, -Dz], -1)
    N = np.cross(np.gradient(P, axis=1), np.gradient(P, axis=0))
    N /= np.linalg.norm(N, axis=-1, keepdims=True) + 1e-9
    N = np.where(N[..., 2:3] < 0, -N, N)
    Y = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    Yc = cv2.resize(Y[box[1]:box[1] + h * step, box[0]:box[0] + w * step], (w, h), interpolation=cv2.INTER_AREA)
    m = np.zeros((h, w), np.uint8)
    pts = ((L[:, :2] - bs) / step).astype(np.int32)
    cv2.fillConvexPoly(m, cv2.convexHull(pts), 1)
    for grp in (range(36, 42), range(42, 48), range(48, 60), range(17, 22), range(22, 27), range(31, 36)):
        t = np.zeros_like(m)
        cv2.fillConvexPoly(t, cv2.convexHull(pts[list(grp)]), 1)
        m[cv2.dilate(t, np.ones((9, 9), np.uint8)) > 0] = 0
    xc = (L[27, 0] - bs[0]) / step
    hw = (L[16, 0] - L[0, 0]) / 2 / step
    m &= (np.abs(xx - xc) < 0.6 * hw).astype(np.uint8)
    sel = (m > 0) & np.isfinite(N[..., 0])
    out = {}
    for el in range(0, 61, 5):
        for az in range(-80, 81, 5):
            a, e = np.radians(az), np.radians(el)
            l = np.array([np.sin(a) * np.cos(e), np.sin(e), np.cos(a) * np.cos(e)])
            sh = np.clip(N[sel] @ l, 0, None)
            out[(az, el)] = float(np.corrcoef(sh, Yc[sel])[0, 1])
    return out
