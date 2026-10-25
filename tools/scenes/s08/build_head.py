"""M4's head as a mesh for F05's shadows: Depth Anything's relative inverse depth over the head (disp_head),
the stand-in glasses filled from the face round them, put in millimetres against F05 itself (where the
stand-in's front lies, the fitted F05's front lies: 1/Z = a d + b fitted over those pixels).

Writes head.npz: V (Blender world, metres), F (quads), and depth_head.npy (mm, the head box; inf off him)."""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import REPO, WORK  # noqa: E402,F401
import json

import bpy
import cv2
import numpy as np
from skimage.restoration import inpaint_biharmonic

D = WORK
import frame3d  # noqa: E402
import lounge_common as LC  # noqa: E402

pose = json.load(open(D + "pose.json"))
Rm = cv2.Rodrigues(np.array(pose["rvec"]))[0]
t = np.array(pose["tvec"])
K = np.array(pose["K"])
f, cx, cy = K[0, 0], K[0, 2], K[1, 2]
box = json.load(open(D + "disp_head.json"))["box"]
d = np.load(D + "disp_head.npy").astype(np.float64)
bx0, by0 = box[0], box[1]
h, w = d.shape
st = cv2.imread(D + "m_standin.png", 0)[by0:by0 + h, bx0:bx0 + w] > 0
alpha = np.load(D + "man_alpha.npy")[by0:by0 + h, bx0:bx0 + w]

# F05's front at the pose: its vertices' pixels and depths
bpy.ops.wm.read_factory_settings(use_empty=True)
mats = frame3d.materials_for("F05")
parts, sh, hinges = frame3d.build("F05", mats)
fr = [p for p in parts if p.name == "F05 front"][0]
co = np.zeros(len(fr.data.vertices) * 3)
fr.data.vertices.foreach_get("co", co)
co = co.reshape(-1, 3) / 0.001
cam = co @ Rm.T + t
u = cx + f * cam[:, 0] / cam[:, 2]
v = cy + f * cam[:, 1] / cam[:, 2]
zf = cam[:, 2]
# keep the front's face (the nearer of its two surfaces at each pixel): a z-buffer at 2 px
zb = {}
for ui, vi, zi in zip(np.round(u / 2).astype(int), np.round(v / 2).astype(int), zf):
    k = (ui, vi)
    if k not in zb or zi < zb[k]:
        zb[k] = zi
ste = cv2.erode(st.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
U, Vv, Z = [], [], []
for (ui, vi), zi in zb.items():
    x, y = ui * 2 - bx0, vi * 2 - by0
    if 0 <= x < w and 0 <= y < h and ste[y, x]:
        U.append(x); Vv.append(y); Z.append(zi)
U, Vv, Z = np.array(U), np.array(Vv), np.array(Z)
ds = d[Vv, U]
A = np.stack([ds, np.ones_like(ds)], 1)
coef = np.linalg.lstsq(A, 1 / Z, rcond=None)[0]
for _ in range(3):                                  # trim the worst (the stand-in is not F05)
    res = np.abs(1 / (A @ coef) - Z)
    ok = res < np.percentile(res, 80)
    coef = np.linalg.lstsq(A[ok], 1 / Z[ok], rcond=None)[0]
res = 1 / (A @ coef) - Z
print("calibration points", len(Z), "a, b", coef, "residual mm median", round(float(np.median(np.abs(res))), 2))

# the stand-in filled from the face round it, at a quarter size
q = 4
small = cv2.resize(d, (w // q, h // q), interpolation=cv2.INTER_AREA)
hole = cv2.resize(cv2.dilate(st.astype(np.uint8), np.ones((15, 15), np.uint8)), (w // q, h // q),
                  interpolation=cv2.INTER_NEAREST) > 0
filled = inpaint_biharmonic(small, hole)
fill_up = cv2.resize(filled, (w, h), interpolation=cv2.INTER_CUBIC)
holef = cv2.dilate(st.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
wgt = cv2.GaussianBlur(holef.astype(np.float32), (0, 0), 4)
d2 = d * (1 - wgt) + fill_up * wgt
Zm = 1 / (coef[0] * d2 + coef[1])
Zraw = Zm.copy()
Zraw[alpha < 0.5] = np.inf
np.save(D + "depth_head_raw.npy", Zraw.astype(np.float32))
# the skin stays behind the frame: under F05's footprint (front and lenses) it is pushed back to at least
# 6 mm behind the frame's back, the push spread smoothly (a frame rests on the nose and floats over the
# cheeks; the depth model, which sees glasses and skin at nearly one depth, put them together)
zmax = np.full((h, w), -np.inf)
zmin = np.full((h, w), np.inf)
for p in parts:
    if not (p.name.startswith("F05 front") or p.name.startswith("F05 lens")):
        continue
    c2 = np.zeros(len(p.data.vertices) * 3)
    p.data.vertices.foreach_get("co", c2)
    c2 = c2.reshape(-1, 3) / 0.001
    cm = c2 @ Rm.T + t
    uu_ = np.round(cx + f * cm[:, 0] / cm[:, 2] - bx0).astype(int)
    vv_ = np.round(cy + f * cm[:, 1] / cm[:, 2] - by0).astype(int)
    okk = (uu_ >= 0) & (uu_ < w) & (vv_ >= 0) & (vv_ < h)
    np.maximum.at(zmax, (vv_[okk], uu_[okk]), cm[okk, 2])
    np.minimum.at(zmin, (vv_[okk], uu_[okk]), cm[okk, 2])
from scipy import ndimage as ndi
zmax = ndi.grey_dilation(np.where(np.isfinite(zmax), zmax, -1e9), size=(7, 7))
zmin = ndi.grey_erosion(np.where(np.isfinite(zmin), zmin, 1e9), size=(7, 7))
# only where the skin is not well in front of the frame (the nose stands in front of the far lens)
need = np.where((zmax > 0) & (Zm > zmin - 15.0), zmax + 6.0 - Zm, 0.0)
push = ndi.grey_dilation(np.maximum(need, 0), size=(25, 25))
push = cv2.GaussianBlur(push.astype(np.float32), (0, 0), 14)
Zm = Zm + np.maximum(push, np.maximum(need, 0))
print("pushed back: max", round(float(push.max()), 1), "mm")
Zm[alpha < 0.5] = np.inf
Zm[(Zm < 300) | (Zm > 2000)] = np.inf
np.save(D + "depth_head.npy", Zm.astype(np.float32))
for name, (px, py) in {"near lens centre": (1396, 620), "ear contact": (795, 440), "nose tip": (1590, 890),
                       "chin": (1320, 1385), "cheek": (1450, 850), "forehead": (1500, 300)}.items():
    print(f"  {name:16s} Z {Zm[py - by0, px - bx0]:.0f} mm")

# the mesh, every 3 px, in Blender's world
step = 3
Zs = Zm[::step, ::step]
hh, ww = Zs.shape
yy, xx = np.mgrid[0:hh, 0:ww]
uu = bx0 + xx * step + 0.5
vv = by0 + yy * step + 0.5
ok = np.isfinite(Zs)
idx = -np.ones((hh, ww), np.int64)
idx[ok] = np.arange(ok.sum())
Zv = Zs[ok]
X = (uu[ok] - cx) / f * Zv
Yd = (vv[ok] - cy) / f * Zv
Vw = np.stack([X, Zv, -Yd], 1) * 0.001
a_, b_, c_, d_ = idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]
good = (a_ >= 0) & (b_ >= 0) & (c_ >= 0) & (d_ >= 0)
Fq = np.stack([a_[good], d_[good], c_[good], b_[good]], 1)
zq = Zv[Fq]
Fq = Fq[(zq.max(1) - zq.min(1)) < 12.0]
np.savez(D + "head.npz", V=Vw.astype(np.float32), F=Fq.astype(np.int64))
print("head mesh", len(Vw), "verts", len(Fq), "quads")
