"""M4 prep: the doubled portrait mirrored (so the GCD side, the wearer's right, faces the camera), the
screenshot's UI tab cropped off, cut out (ISNet for the shape, closed-form matting against the studio's
fitted backdrop for the edges: hair, the shearling collar), colours freed of the backdrop's spill.

Writes man_rgb.npy (float32 linear-ish sRGB 0..1, the foreground colour), man_alpha.npy, man_bg.npy (the
fitted backdrop), previews."""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import REPO, WORK  # noqa: E402,F401
import time

import cv2
import numpy as np
from PIL import Image

D = WORK
CROP_LEFT = 150            # the UI tab (the original's right edge, x >= 1135 at 1x) after the mirror

im = np.asarray(Image.open(D + "man_clean-x2.png").convert("RGB"))
im = im[:, ::-1][:, CROP_LEFT:].copy()
H, W = im.shape[:2]
print("size", W, H)
Image.fromarray(im).save(D + "man_m.png")

# 1. the shape: ISNet on a 1024 version
from rembg import new_session, remove
t = time.time()
sess = new_session("isnet-general-use")
small = Image.fromarray(im).resize((W // 2, H // 2), Image.LANCZOS)
m = remove(small, session=sess, only_mask=True, post_process_mask=False)
coarse = cv2.resize(np.asarray(m).astype(np.float32) / 255, (W, H), interpolation=cv2.INTER_LINEAR)
print("isnet", round(time.time() - t, 1), "s")
np.save(D + "man_coarse.npy", coarse)

# 2. the backdrop: a smooth surface (2nd order in x, y per channel) fitted to the sure background
f = im.astype(np.float32) / 255
sure_bg = cv2.erode((coarse < 0.02).astype(np.uint8), np.ones((41, 41), np.uint8)) > 0
ys, xs = np.nonzero(sure_bg)
sel = np.random.default_rng(0).choice(len(ys), min(200000, len(ys)), replace=False)
ys, xs = ys[sel], xs[sel]


def basis(x, y):
    x, y = x / W - 0.5, y / H - 0.5
    return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y, x * x * y, x * y * y, x ** 3, y ** 3], -1)


A = basis(xs.astype(np.float64), ys.astype(np.float64))
coef = np.linalg.lstsq(A, f[ys, xs].astype(np.float64), rcond=None)[0]
yy, xx = np.mgrid[0:H, 0:W]
bg = (basis(xx.astype(np.float64), yy.astype(np.float64)) @ coef).astype(np.float32)
res = np.abs(f[ys, xs] - bg[ys, xs]).mean()
print("backdrop fit residual", round(float(res) * 255, 2), "/255; backdrop mean", (bg.mean((0, 1)) * 255).round(1))
np.save(D + "man_bg.npy", bg)

# 3. trimap: sure foreground well inside ISNet's shape; sure background well outside it and close to the
# backdrop's colour; a wide unknown band round the hair and the collar
dist = np.linalg.norm(f - bg, axis=-1)
from scipy import ndimage as ndi
# the body is cut by the picture's left and bottom edges: closed along them, anything ISNet left unsure
# inside the jacket is a hole and filled
closed = (coarse > 0.5).copy()
closed[:, 0] = True
closed[-1, :] = True
body = ndi.binary_fill_holes(closed)
body[:, 0] = coarse[:, 0] > 0.5
body[-1, :] = coarse[-1, :] > 0.5
fg = cv2.erode(body.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))) > 0
bgk = (cv2.erode((coarse < 0.03).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))) > 0) & (dist < 0.05)
# the cut edges (left, bottom) are the picture's edges: foreground right up to them
edge = np.zeros_like(fg)
edge[-4:, :] = True
edge[:, :4] = True
fg |= edge & (coarse > 0.5)
tri = np.full((H, W), 0.5, np.float64)
tri[fg] = 1.0
tri[bgk] = 0.0
print("unknown px", int((tri == 0.5).sum()))
Image.fromarray((tri * 255).astype(np.uint8)).resize((W // 4, H // 4)).save(D + "v_trimap.png")

# 4. closed-form matting, in tiles round the unknown band (the whole picture at once is too big)
from pymatting import estimate_alpha_cf, estimate_foreground_ml
t = time.time()
alpha = tri.copy()
unk = (tri == 0.5).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(unk)
T = 640
P = 48
for y0 in range(0, H, T):
    for x0 in range(0, W, T):
        y1, x1 = min(H, y0 + T), min(W, x0 + T)
        if not unk[y0:y1, x0:x1].any():
            continue
        Y0, X0, Y1, X1 = max(0, y0 - P), max(0, x0 - P), min(H, y1 + P), min(W, x1 + P)
        tt = tri[Y0:Y1, X0:X1]
        if not (tt == 1).any() or not (tt == 0).any():
            a = np.where(tt == 0.5, 1.0 if (tt == 1).any() else 0.0, tt)
        else:
            a = estimate_alpha_cf(f[Y0:Y1, X0:X1].astype(np.float64), tt,
                                  laplacian_kwargs={"epsilon": 1e-6}, cg_kwargs={"maxiter": 2000})
        alpha[y0:y1, x0:x1] = np.where(tri[y0:y1, x0:x1] == 0.5, a[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0],
                                       tri[y0:y1, x0:x1])
print("matting", round(time.time() - t, 1), "s")
alpha = np.clip(alpha, 0, 1).astype(np.float32)
np.save(D + "man_alpha.npy", alpha)

# 5. the foreground's own colour (the backdrop's light taken out of the edges)
t = time.time()
F = estimate_foreground_ml(f.astype(np.float64), alpha.astype(np.float64)).astype(np.float32)
print("foreground", round(time.time() - t, 1), "s")
np.save(D + "man_rgb.npy", F)

# previews: over black and over magenta, at a quarter
for name, col in (("black", (0.02, 0.02, 0.02)), ("mag", (0.45, 0.05, 0.3))):
    comp = F * alpha[..., None] + np.array(col, np.float32) * (1 - alpha[..., None])
    Image.fromarray((np.clip(comp, 0, 1) * 255).astype(np.uint8)).resize((W // 3, H // 3), Image.LANCZOS).save(
        D + f"v_cut_{name}.jpg", quality=90)
