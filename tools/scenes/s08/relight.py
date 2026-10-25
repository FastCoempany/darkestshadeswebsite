"""M4 relit for the lounge: his colours divided by the studio's soft light (a key from the camera's right,
read off his skin, over the studio's strong ambient), multiplied by the lounge's lights at his own surface
(lounge_common.LIGHTS: positions, colours, powers, spot cones; the depth model's normals; distances; the
key's shadows marched over the depth map), plus the blue rim along the silhouette edges that face it.

Writes man_relit.npy (linear RGB at the portrait's size, in the background render's units) and a preview."""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import REPO, WORK  # noqa: E402,F401
import json

import cv2
import numpy as np
from scipy import ndimage as ndi

D = WORK
import lounge_common as LC  # noqa: E402

args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
# his colours: the matting's foreground (the studio's white taken out of every edge), with the retouch
# (retouch.py: the stand-in's temple and slivers rebuilt; retouch2.py: the brow's fold healed, the far
# temple refilled, the photograph kept under the nose's tip) where it was made
rt = cv2.cvtColor(cv2.imread(D + "man_rt2.png"), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
Fg = np.load(D + "man_rgb.npy").astype(np.float32)
rm0 = np.load(D + "m_retouched2.npy").astype(np.float32)
rmask = cv2.GaussianBlur(rm0, (0, 0), 1.5)[..., None]
img = np.clip(Fg * (1 - rmask) + rt * rmask, 0, 1)
lin = np.where(img <= 0.04045, img / 12.92, ((img + 0.055) / 1.055) ** 2.4)
alpha = np.load(D + "man_alpha.npy")
H, W = alpha.shape
pose = json.load(open(D + "pose.json"))
K = np.array(pose["K"])
f, cx, cy = K[0, 0], K[0, 2], K[1, 2]

# ---- normals over the whole figure: the head's (its depth calibrated to F05), the body's from the whole
# picture's depth; each from its own depth, smoothed (broad shading only: the photograph keeps the fine
# shading in its colours), blended across a wide band at the head box's edges
box = json.load(open(D + "disp_head.json"))["box"]
Zh = np.load(D + "depth_head_raw.npy").astype(np.float64)
hh, ww = Zh.shape
dall = np.load(D + "disp_all.npy").astype(np.float64)
Zfull = np.full((H, W), np.nan)
Zfull[box[1]:box[1] + hh, box[0]:box[0] + ww] = np.where(np.isfinite(Zh), Zh, np.nan)
both = np.isfinite(Zfull) & (alpha > 0.9)
A = np.stack([dall[both], np.ones(both.sum())], 1)
coef = np.linalg.lstsq(A, 1 / Zfull[both], rcond=None)[0]
Zall = 1 / (coef[0] * dall + coef[1])
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
m = (alpha > 0.5).astype(np.float64)
sig = args.get("nsig", 8.0)


def normals(Zsrc, valid):
    mm = (valid & (m > 0)).astype(np.float32)
    Zf = np.where(mm > 0, Zsrc, 0).astype(np.float32)
    Zs_ = (ndi.gaussian_filter(Zf * mm, sig) / np.maximum(ndi.gaussian_filter(mm, sig), 1e-6)).astype(np.float32)
    P_ = np.stack([((xx - cx) / f * Zs_).astype(np.float32), ((yy - cy) / f * Zs_).astype(np.float32), Zs_], -1)
    gx_, gy_ = np.gradient(P_, axis=1), np.gradient(P_, axis=0)
    N_ = np.cross(gx_, gy_).astype(np.float32)
    del gx_, gy_
    N_ /= np.linalg.norm(N_, axis=-1, keepdims=True) + 1e-9
    N_ = np.where(N_[..., 2:3] > 0, -N_, N_)
    return np.nan_to_num(N_), P_, Zs_


Nh, Ph, Zsh = normals(np.nan_to_num(Zfull, nan=0.0), np.isfinite(Zfull))
Nb, Pb, Zsb = normals(Zall, np.isfinite(Zall))
wbox = np.zeros((H, W), np.float32)
wbox[box[1]:box[1] + hh, box[0]:box[0] + ww] = 1.0
wbox = cv2.GaussianBlur(cv2.erode(wbox, np.ones((241, 241), np.uint8)), (0, 0), 60)
wbox = np.where(np.isfinite(Zfull), wbox, 0.0)[..., None]
N = Nh * wbox + Nb * (1 - wbox)
N /= np.linalg.norm(N, axis=-1, keepdims=True) + 1e-9
P = (Ph * wbox + Pb * (1 - wbox)).astype(np.float32)
Zs = np.where(m > 0, Zsh * wbox[..., 0] + Zsb * (1 - wbox[..., 0]), np.nan).astype(np.float32)
del Nh, Nb, Ph, Pb, Zsh, Zsb


# (before the studio's light is read off him, so both lights see the same surface) near the silhouette the depth model's normals swing to the side and every light from that side drew a
# bright line along the edge: there they lean back towards the camera
N_raw = N.copy()
din = ndi.distance_transform_edt(alpha > 0.5)
wfl = 0.75 * np.exp(-din / args.get("edge_px", 22.0))
# and wherever they turn past ~60 deg from the camera (a jump in the depth: the ear's lobe over the neck,
# the jaw over the collar), the same
tilt = np.degrees(np.arccos(np.clip(np.abs(N[..., 2]), 0, 1)))
wfl = np.maximum(wfl, 0.7 * np.clip((tilt - 58.0) / 22.0, 0, 1))[..., None].astype(np.float32)
N = N * (1 - wfl) + np.array([0.0, 0.0, -1.0]) * wfl
N /= np.linalg.norm(N, axis=-1, keepdims=True) + 1e-9

def lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


# ---- the studio's key: the direction whose Lambert term best explains the skin's brightness
skin = (alpha > 0.95) & (np.abs(img[..., 0] - img[..., 2]) > 0.08) & (lum(img) > 0.45) & (img[..., 0] > img[..., 1])
st = cv2.imread(D + "m_standin.png", 0) > 0
skin &= ~cv2.dilate(st.astype(np.uint8), np.ones((25, 25), np.uint8)).astype(bool)
skin &= np.isfinite(Zs)
Ys = lum(lin)[skin]
Ns = N[skin]
best = (-2, None)
for el in range(-10, 61, 5):
    for az in range(-80, 81, 5):
        a_, e_ = np.radians(az), np.radians(el)
        l0 = np.array([np.sin(a_) * np.cos(e_), -np.sin(e_), -np.cos(a_) * np.cos(e_)])   # cv: up is -y
        c = np.corrcoef(np.clip(Ns @ l0, 0, None), Ys)[0, 1]
        if c > best[0]:
            best = (c, (az, el), l0)
print("studio key az, el", best[1], "corr", round(best[0], 3))
l0 = best[2]
lam0 = np.clip(np.einsum("ijk,k->ij", N, l0), 0, None)
# the studio: its key over a strong ambient; the split from the skin (brightness ~ amb + k * lambert)
A2 = np.stack([np.ones_like(Ys), np.clip(Ns @ l0, 0, None)], 1)
amb, kk = np.linalg.lstsq(A2, Ys, rcond=None)[0]
amb = max(amb, 0.05)
print("studio ambient, key", round(float(amb), 3), round(float(kk), 3))
S0 = (amb + kk * lam0) / (amb + kk)                                      # 1 where the key falls square
alb = lin / np.maximum(S0, 0.25)[..., None] * args.get("albedo", 0.78)   # the brightest skin ~0.5

# ---- the lounge's light at his surface
def to_cv(p):
    return np.array([p[0], -p[2], p[1]]) * 1000.0


E = np.zeros((H, W, 3))
Pv = np.nan_to_num(P)
lights = {k: dict(v) for k, v in LC.LIGHTS.items()}
for k, v in args.get("light_over", {}).items():          # per-light overrides for him alone, e.g. a narrower key
    lights[k].update(v)
for name, Lg in lights.items():
    Lp = to_cv(Lg["pos"])
    Va = Lp[None, None] - Pv
    dist = np.linalg.norm(Va, axis=-1)
    l = Va / dist[..., None]
    # a large soft source on skin: the terminator wraps (light carried under the surface, the source's
    # breadth) instead of the hard cosine of a point, so creases (the nose's wing) shade gently
    wr = args.get("wrap", {}).get(name, 0.0)
    lam = np.clip((np.einsum("ijk,ijk->ij", N, l) + wr) / (1 + wr), 0, None)
    # area light facing its aim: irradiance ~ P cos / (pi d^2) (d in m); a spot's cone
    E_ = Lg["power"] / (np.pi * (dist / 1000.0) ** 2) * lam
    if Lg.get("point"):
        E_ *= 1 / 4.0                                       # a point light: P/4pi per steradian
    if Lg.get("spot"):
        aim = to_cv(Lg["aim"]) - Lp
        aim /= np.linalg.norm(aim)
        cosang = np.einsum("ijk,k->ij", -l, aim)
        half = np.radians(Lg["spot"] / 2)
        blend = 0.6
        E_ *= np.clip((cosang - np.cos(half)) / max(np.cos(half * (1 - blend)) - np.cos(half), 1e-6), 0, 1) ** 2
        E_ *= 1 / (4.0)                                     # a spot's power spreads over the sphere (P/4pi vs P/pi)
    if name in args.get("marched", ["key", "top", "lamp", "fill", "wash"]):
        # its shadows over his own depth: march towards the light
        occ = np.zeros((H, W))
        sub = 2
        Ps = Pv[::sub, ::sub]
        ls = l[::sub, ::sub]
        Zsub = np.nan_to_num(Zs, nan=1e9)
        vis = np.ones(Ps.shape[:2])
        for s in np.linspace(6, 140, 36):
            Q = Ps + ls * s
            u = np.round(cx + f * Q[..., 0] / Q[..., 2]).astype(int)
            v = np.round(cy + f * Q[..., 1] / Q[..., 2]).astype(int)
            inside = (u >= 0) & (u < W) & (v >= 0) & (v < H)
            zm = np.full(u.shape, 1e9)
            zm[inside] = Zsub[v[inside], u[inside]]
            blocked = (zm < Q[..., 2] - 4.0) & (zm > Q[..., 2] - 60.0)
            vis *= np.where(blocked, 0.55, 1.0)
        # softened along his surface but not across a jump in depth: the far cheek's shadow (behind the
        # nose) stays off the nose's tip (a joint bilateral on the depth, at a quarter of his size)
        vb = args.get("vis_blur", 38.0)
        Zg = np.nan_to_num(Zs, nan=1e4).astype(np.float32)
        q4 = (W // 4, H // 4)
        v4 = cv2.resize(vis.astype(np.float32), q4, interpolation=cv2.INTER_AREA)
        z4 = cv2.resize(Zg, q4, interpolation=cv2.INTER_AREA)
        v4 = cv2.ximgproc.jointBilateralFilter(z4, v4, -1, args.get("vis_dz", 14.0), vb / 4)
        vis = cv2.resize(v4, (W, H), interpolation=cv2.INTER_LINEAR)
        vis = cv2.GaussianBlur(vis, (0, 0), 3)
        E_ *= np.clip(vis, 0, 1)
        if name == "key":
            np.save(D + "key_vis.npy", vis)
    E += E_[..., None] * np.array(Lg["color"])[None, None]
# the room's dim ambient (the world colour lights him from all round, the candles' glow from his left)
E += np.array(args.get("ambient", [0.02, 0.016, 0.03]))[None, None] * np.pi
# the change of light, new over old, per pixel; across a jump in the depth (the collar over the neck, the
# lobe over the jaw) and at the silhouette the normals are the model's guesses and the change drew lines
# along them: there it is carried in from either side (a normalized blur that leaves the bands out)
Mx = (E / np.pi) / np.maximum(S0, 0.25)[..., None] * args.get("albedo", 0.78)
tilt_raw = np.degrees(np.arccos(np.clip(np.abs(N_raw[..., 2]), 0, 1)))
band_j = (tilt_raw > args.get("jump_deg", 52.0)) | (din < 3)
band_j = cv2.dilate(band_j.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
keep = (~band_j & (alpha > 0.5)).astype(np.float32)
def nblur(sig_):
    num = np.stack([cv2.GaussianBlur((Mx[..., c] * keep).astype(np.float32), (0, 0), sig_) for c in range(3)], -1)
    den = cv2.GaussianBlur(keep, (0, 0), sig_)
    return num / np.maximum(den, 1e-6)[..., None], den


Ms, den = nblur(7)
for sig_ in (20, 60):                                   # wide bands: reach further for their neighbours
    Mw, dw = nblur(sig_)
    t_ = np.clip((0.25 - den) / 0.2, 0, 1)[..., None]
    Ms = Ms * (1 - t_) + Mw * t_
    den = np.maximum(den, dw)
bj = cv2.GaussianBlur(band_j.astype(np.float32), (0, 0), 2.0)[..., None]
Mx = Mx * (1 - bj) + Ms * bj
relit = lin * Mx
# ---- the rim: silhouette edges whose outward side faces the blue light behind him on the left
edge_in = cv2.GaussianBlur(alpha, (0, 0), 1.0)
gx = cv2.Sobel(edge_in, cv2.CV_32F, 1, 0, ksize=5)
gy = cv2.Sobel(edge_in, cv2.CV_32F, 0, 1, ksize=5)
gn = np.sqrt(gx * gx + gy * gy) + 1e-6
outx, outy = -gx / gn, -gy / gn                                     # outward, image coords
rim_dir = np.array(args.get("rim_dir", [-0.75, -0.65]))
rim_dir = rim_dir / np.linalg.norm(rim_dir)
facing = np.clip(outx * rim_dir[0] + outy * rim_dir[1], 0, 1)
dist_in = ndi.distance_transform_edt(alpha > 0.5)
band = np.exp(-dist_in / args.get("rim_px", 9.0)) * (alpha > 0.02)
facing_s = cv2.GaussianBlur(facing * (gn > 0.02), (0, 0), 8)
facing_s = facing_s / max(facing_s.max(), 1e-6)
rim = band * np.clip(facing_s * 2.5, 0, 1)
rim_col = np.array(LC.LIGHTS["rim"]["color"]) * args.get("rim_gain", 0.35)
relit = relit + rim[..., None] * rim_col[None, None] * (0.35 + lum(alb)[..., None])
np.save(D + "man_relit.npy", relit.astype(np.float32))
x = relit * 2 ** args.get("ev", 0.0)
x = x / (1 + 0.25 * x)
x = np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.clip(x, 0, None) ** (1 / 2.4) - 0.055)
prev = np.clip(x, 0, 1) * alpha[..., None] + 0.03 * (1 - alpha[..., None])
cv2.imwrite(D + "v_relit.jpg", cv2.cvtColor((cv2.resize(prev, (W // 3, H // 3)) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
print("relit: face mean", np.round(relit[skin].mean(0), 3), "max", np.round(np.percentile(relit[alpha > 0.5], 99.5, axis=0), 3))
