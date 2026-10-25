"""F05's pose on M4 (mirrored portrait, man_m.png): PnP from the stand-in glasses' lens centres, front
ends and the temple's line at the ear, then an overlay of F05's outline, lens openings, end piece and
near temple on the portrait. Writes pose.json (frame mm -> OpenCV camera, K of the portrait)."""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import REPO, WORK  # noqa: E402,F401
import json

import bpy
import cv2
import numpy as np
from scipy.optimize import least_squares

import frame3d  # noqa: E402

D = WORK
args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
img = cv2.imread(D + "man_m.png")
H, W = img.shape[:2]
F_PX = args.get("f_px", 85.0 / 36.0 * 2412)
K = np.array([[F_PX, 0, 1056.0], [0, F_PX, 1546.0], [0, 0, 1]])

bpy.ops.wm.read_factory_settings(use_empty=True)
mats = frame3d.materials_for("F05")
parts, sh, hinges = frame3d.build("F05", mats)
cfg = frame3d.FRAMES["F05"]
out = sh["outline"]
xm, zw = frame3d.wrap_profile("F05")
zat = lambda x: float(np.interp(x, xm, zw))
T = cfg["depth"]
th = np.tan(np.radians(cfg["tilt"]))
lens_z = -(cfg["bezel"]["drop"] + cfg["lip_r"] + cfg["lens"]["inset"])
xe = float(out[:, 0].max())
P3 = {
    "lens_near": np.array([-35.95, 0.0, zat(-35.95) + lens_z]),
    "lens_far": np.array([35.95, 0.0, zat(35.95) + lens_z]),
    "end_near": np.array([-xe, 3.0, zat(-xe) - T / 2 + 3.0 * th]),
    "end_far": np.array([xe, 3.0, zat(xe) - T / 2 + 3.0 * th]),
}
h_near = np.asarray(hinges[0], np.float64)
L_EAR = args.get("l_ear", 92.0)
img_pts = args.get("img", {"lens_near": [1380, 615], "lens_far": [1775, 770], "end_near": [1192, 590],
                           "end_far": [1905, 740], "ear": [790, 440]})
wts = args.get("w", {"lens_near": 1.0, "lens_far": 1.0, "end_near": 1.0, "end_far": 0.6, "ear": 1.0})


def ear_pt(psi):
    d = np.array([-np.sin(psi), 0.0, -np.cos(psi)])
    return h_near + d * L_EAR


# the stand-in's top edge (first dark pixel down each column), its near and far ends' x
TOP = np.array(args.get("top", [[1220, 400], [1300, 400], [1400, 419], [1500, 461], [1600, 514], [1700, 561],
                                [1800, 611], [1860, 652]]), np.float64)
X_NEAR, X_FAR = args.get("x_near", 1195.0), args.get("x_far", 1910.0)
EAR = np.array(args.get("ear", [790.0, 435.0]))
tx = np.array([-64, -58, -52, -46, -40, -34, -28, 28, 34, 40, 46, 52, 58], np.float64)


def dense(poly, step=0.1):
    P_ = np.vstack([poly, poly[:1]])
    seg = np.linalg.norm(np.diff(P_, axis=0), axis=1)
    s_ = np.r_[0, np.cumsum(seg)]
    q = np.arange(0, s_[-1], step)
    return np.stack([np.interp(q, s_, P_[:, 0]), np.interp(q, s_, P_[:, 1])], 1)


OUTD = dense(out)


def ytop_out(x, half=0.15):
    m = np.abs(OUTD[:, 0] - x) < half
    return float(OUTD[m, 1].max())


TOP3 = np.array([[x, ytop_out(x), zat(x) - 1.0 + ytop_out(x) * th] for x in tx])
END_N = np.array([-xe, 3.0, zat(-xe) - T / 2 + 3.0 * th])
END_F = np.array([xe, 3.0, zat(xe) - T / 2 + 3.0 * th])


def residual(p):
    rvec, tvec, psi = p[:3], p[3:6], p[6]
    pr, _ = cv2.projectPoints(np.vstack([TOP3, END_N, END_F, ear_pt(psi)]), rvec, tvec, K, None)
    pr = pr[:, 0]
    n = len(TOP3)
    r = list(pr[:n, 1] - np.interp(pr[:n, 0], TOP[:, 0], TOP[:, 1]))
    r += [(pr[n, 0] - X_NEAR) * 1.5, (pr[n + 1, 0] - X_FAR) * 0.7]
    r += list((pr[n + 2] - EAR) * args.get("w_ear", 1.0))
    # the front stands about upright to the camera (a level camera, an upright head): its up axis has
    # little depth in it; tilted `pitch0` deg back at the top if asked
    up = cv2.Rodrigues(rvec)[0][:, 1]
    r += [args.get("w_up", 300.0) * (up[2] - np.sin(np.radians(args.get("pitch0", 0.0))))]
    return np.r_[r, args.get("w_splay", 30.0) * (psi - np.radians(args.get("splay0", 0.0)))]


names = ["lens_near", "lens_far", "end_near", "end_far"]
obj = np.stack([P3[k] for k in names])
# a start: the face turned `yaw0` deg to the image's right, rolled `roll0`, `dist0` mm away, the frame's
# origin between the two lens centres seen
th0, r0 = np.radians(args.get("yaw0", 50.0)), np.radians(args.get("roll0", 12.0))
fx_ = np.array([np.cos(th0), 0, np.sin(th0)])
fy_ = np.array([0, -1.0, 0])
fz_ = np.cross(fx_, fy_)
R0 = np.stack([fx_, fy_, fz_], 1)
Rr = cv2.Rodrigues(fz_ * -r0)[0]
R0 = Rr @ R0
rvec = cv2.Rodrigues(R0)[0]
o_img = (np.array(img_pts["lens_near"]) + np.array(img_pts["lens_far"])) / 2
d0 = args.get("dist0", 740.0)
tvec = d0 * np.array([(o_img[0] - K[0, 2]) / K[0, 0], (o_img[1] - K[1, 2]) / K[1, 1], 1.0])
if args.get("no_fit"):
    rvec, tvec, psi = rvec.ravel(), tvec.ravel(), 0.0
else:
    sol = least_squares(residual, np.r_[rvec.ravel(), tvec.ravel(), 0.0], method="trf", x_scale="jac")
    rvec, tvec, psi = sol.x[:3], sol.x[3:6], sol.x[6]
# manual nudges (degrees about the frame's own axes, mm in the camera) on top of the fit
Rm = cv2.Rodrigues(rvec)[0]
nud = args.get("nudge", {})
if nud:
    from scipy.spatial.transform import Rotation as Rot
    Rn = Rot.from_euler("xyz", [nud.get("rx", 0), nud.get("ry", 0), nud.get("rz", 0)], degrees=True).as_matrix()
    # rotate about the frame's origin (between the lenses): R' = R Rn, t unchanged
    Rm = Rm @ Rn
    tvec = tvec + np.array(nud.get("t", [0, 0, 0]), np.float64)
    rvec = cv2.Rodrigues(Rm)[0].ravel()
    psi = psi + np.radians(nud.get("splay", 0.0))
res = residual(np.r_[rvec, tvec, psi])
print("top edge residuals px", np.round(res[:len(TOP3)], 1))
print("near/far end x", np.round(res[len(TOP3):len(TOP3) + 2], 1), "ear", np.round(res[len(TOP3) + 2:len(TOP3) + 4], 1))
fz = Rm @ np.array([0, 0, 1.0])
print("distance mm", np.linalg.norm(tvec).round(1), "yaw deg", np.degrees(np.arctan2(fz[0], -fz[2])).round(1),
      "splay deg", np.degrees(psi).round(2))

# overlay: the front's outline and lens openings (on its face), the near end piece and the temple
ov = img.copy()


def P(xy, zoff=0.0):
    xy = np.asarray(xy, np.float64)
    z = np.array([zat(x) for x in xy[:, 0]]) + zoff + xy[:, 1] * th
    p, _ = cv2.projectPoints(np.c_[xy, z], rvec, tvec, K, None)
    return p[:, 0]


cv2.polylines(ov, [P(out).astype(np.int32)], True, (0, 255, 255), 2)
cv2.polylines(ov, [P(out, -T).astype(np.int32)], True, (0, 160, 255), 1)
for o in sh["openings"]:
    cv2.polylines(ov, [P(o, lens_z).astype(np.int32)], True, (255, 0, 255), 2)
for e in sh["ends"]:
    q = np.array([e["apex"], e["top"], e["bottom"]], np.float64)
    pp, _ = cv2.projectPoints(q, rvec, tvec, K, None)
    cv2.polylines(ov, [pp[:, 0].astype(np.int32)], True, (0, 255, 0) if e["side"] < 0 else (0, 120, 0), 2)
tp = np.stack([h_near + np.array([-np.sin(psi), 0, -np.cos(psi)]) * s for s in np.linspace(0, 120, 30)])
pp, _ = cv2.projectPoints(tp, rvec, tvec, K, None)
cv2.polylines(ov, [pp[:, 0].astype(np.int32)], False, (255, 255, 0), 2)
cv2.polylines(ov, [TOP.astype(np.int32)], False, (0, 0, 255), 2)
cv2.circle(ov, tuple(int(c) for c in EAR), 7, (0, 0, 255), -1)
x0, y0 = 600, 250
crop = ov[y0:y0 + 900, x0:x0 + 1500]
cv2.imwrite(D + "v_fit.jpg", crop)
json.dump({"rvec": list(map(float, rvec)), "tvec": list(map(float, tvec)), "K": K.tolist(), "W": W, "H": H,
           "splay": float(psi), "l_ear": L_EAR, "img": img_pts}, open(D + "pose.json", "w"), indent=1)
