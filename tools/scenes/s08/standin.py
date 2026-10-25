"""The stand-in glasses on M4 (the portrait came with someone else's frame): their mask (front, lenses, the
near temple to the ear), F05's coverage at the fitted pose (the front's outline, face and back, the near
end piece, the temple), and what of the stand-in stays visible past F05. Saves masks as PNGs."""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import REPO, WORK  # noqa: E402,F401
import json

import bpy
import cv2
import numpy as np
from scipy import ndimage as ndi

import frame3d  # noqa: E402

D = WORK
img = cv2.imread(D + "man_m.png").astype(np.float32)
H, W = img.shape[:2]
B, G, R_ = img[..., 0], img[..., 1], img[..., 2]
L = img.mean(-1)

# ---- the stand-in's front and lenses
roi = np.zeros((H, W), bool)
roi[375:1000, 1165:1975] = True
dark = (L < 80) & roi
green = (G - np.maximum(R_, B) > 12) & (L < 190) & roi
m = dark | green
m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0
lab, n = ndi.label(m)
sizes = ndi.sum(m, lab, range(1, n + 1))
front = lab == (1 + int(np.argmax(sizes)))
# the glints on it (hinge pins, rim highlights) and the anti-aliased edge
holes = ndi.binary_fill_holes(front) & ~front
hl, hn = ndi.label(holes)
hs = ndi.sum(holes, hl, range(1, hn + 1))
for i, s in enumerate(hs):
    if s < 1500:
        front |= hl == i + 1
front = cv2.dilate(front.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) > 0

# ---- the temple: the dark band from the ear's front to the front's end, top to its brown lower edge
temple = np.zeros((H, W), np.uint8)
poly = np.array([[775, 392], [960, 391], [1215, 396], [1215, 500], [1100, 494], [960, 482], [860, 492], [800, 478],
                 [775, 450]], np.int32)
cv2.fillPoly(temple, [poly], 1)
band = (temple > 0) & ((L < 95) | ((R_ - B > 25) & (L < 140)))     # black, or the brown translucent edge
band = cv2.morphologyEx(band.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0
band = ndi.binary_fill_holes(band)
temple = cv2.dilate((band & (temple > 0)).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) > 0
# where the temple crosses the hair, the hair's own black hides its edge: take the band's rows there
standin = front | temple
cv2.imwrite(D + "m_standin.png", standin.astype(np.uint8) * 255)

# ---- F05's coverage at the pose
p = json.load(open(D + "pose.json"))
Rm = cv2.Rodrigues(np.array(p["rvec"]))[0]
t = np.array(p["tvec"])
K = np.array(p["K"])
bpy.ops.wm.read_factory_settings(use_empty=True)
mats = frame3d.materials_for("F05")
parts, sh, hinges = frame3d.build("F05", mats)
cov = np.zeros((H, W), np.uint8)
# every part's vertices projected, each part's convex hull per mesh island is too coarse: splat faces
for pt in parts:
    me = pt.data
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3) / 0.001
    Mw = np.asarray(pt.matrix_world)
    co = co @ Mw[:3, :3].T + Mw[:3, 3] / 0.001
    pr, _ = cv2.projectPoints(co, np.array(p["rvec"]), t, K, None)
    pr = pr[:, 0]
    for f in me.polygons:
        q = pr[list(f.vertices)].round().astype(np.int32)
        cv2.fillConvexPoly(cov, q, 1)
# the near temple to the ear, the end of its run past the ear left out
h = np.asarray(hinges[0])
psi = p["splay"]
tp = np.stack([h + np.array([-np.sin(psi), 0, -np.cos(psi)]) * s for s in np.linspace(0, p["l_ear"] + 4, 40)])
pr, _ = cv2.projectPoints(tp, np.array(p["rvec"]), t, K, None)
cv2.polylines(cov, [pr[:, 0].round().astype(np.int32)], False, 1, 19)
cov = cov > 0
cv2.imwrite(D + "m_f05.png", cov.astype(np.uint8) * 255)
left = standin & ~cv2.erode(cov.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
cv2.imwrite(D + "m_left.png", left.astype(np.uint8) * 255)
ov = img.copy()
ov[standin] = ov[standin] * 0.5 + np.array([0, 0, 255]) * 0.5
ov[cov] = ov[cov] * 0.6 + np.array([255, 255, 0]) * 0.4
ov[left] = np.array([0, 255, 0])
cv2.imwrite(D + "v_standin.jpg", ov[250:1050, 650:2050])
print("stand-in px", int(standin.sum()), "F05 px", int(cov.sum()), "left visible px", int(left.sum()))
