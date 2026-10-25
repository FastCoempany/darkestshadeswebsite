"""M4-S08-F05: the lounge (lounge_bg.py, half size, up), M4 relit (relight.py) with F05's shadow on his
face, F05 (f05_lounge.py) over him, his nose in front of the frame's far side, the near temple's contact
shadow; then one surface for all: light wrap at his edges, a faint bloom off the brightest highlights,
grain, the grade.

    python3 composite.py BG.npy F05DIR OUT.png [json opts]
"""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import REPO, WORK  # noqa: E402,F401
import json

import cv2
import numpy as np

D = WORK
import lounge_common as LC  # noqa: E402

bg_p, f05_dir, out_p = sys.argv[1], sys.argv[2], sys.argv[3]
o = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
W, H = LC.W_O, LC.H_O
q = 2 if o.get("half") else 1               # a half-size preview: everything at 2000 x 1500
W, H = W // q, H // q

bg = np.load(bg_p)[..., :3].astype(np.float32)
if bg.shape[1] != W:
    bg = cv2.resize(bg, (W, H), interpolation=cv2.INTER_CUBIC)
bg = np.clip(bg, 0, None)

# ---- M4, at the output's scale
relit = np.load(D + "man_relit.npy").astype(np.float32)
alpha = np.load(D + "man_alpha.npy").astype(np.float32)
# where the stand-in reached past his outline (its far lens's outer edge, its top beyond his far temple)
# and F05 does not cover it, the retouch filled it from the studio's white: that is the room's, not his;
# his alpha there is the share of skin the fill holds (the studio's white is bluish, skin is not)
_cr = json.load(open(f05_dir + "/crop.json"))["crop"]
_ga = np.load(f05_dir + "/glasses.npy")[..., 3].astype(np.float32)
_GA = np.zeros((LC.H_O, LC.W_O), np.float32)
_GA[_cr[1]:_cr[1] + _ga.shape[0], _cr[0]:_cr[0] + _ga.shape[1]] = _ga
_GAm = cv2.resize(_GA, (int(round(LC.W_O / LC.S_M)), int(round(LC.H_O / LC.S_M))),
                  interpolation=cv2.INTER_LINEAR)[:alpha.shape[0], :alpha.shape[1]]
_exp = ((cv2.imread(D + "m_standin.png", 0) > 0) | (np.load(D + "m_retouched.npy") > 0.5)) & (_GAm < 0.5)
_exp &= cv2.dilate((alpha < 0.5).astype(np.uint8), np.ones((31, 31), np.uint8)) > 0
_exp[900:972, 1588:1682] = False                       # the skin under the nose's tip (retouch2.py)
_rtc = cv2.cvtColor(cv2.imread(D + "man_rt2.png"), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
_skin = np.clip((0.05 - (_rtc[..., 2] - _rtc[..., 0])) / 0.15, 0, 1)
alpha = np.where(_exp, alpha * _skin, alpha)
del _ga, _GA, _GAm, _exp, _rtc, _skin
s = LC.S_M / q
mw, mh = int(round(alpha.shape[1] * s)), int(round(alpha.shape[0] * s))
man = cv2.resize(relit, (mw, mh), interpolation=cv2.INTER_AREA)
A = cv2.resize(alpha, (mw, mh), interpolation=cv2.INTER_AREA)
mh, mw = min(mh, H), min(mw, W)
man, A = man[:mh, :mw], A[:mh, :mw]
MAN = np.zeros((H, W, 3), np.float32)
AM = np.zeros((H, W), np.float32)
MAN[:mh, :mw] = man
AM[:mh, :mw] = A

# ---- F05's passes
crop = json.load(open(f05_dir + "/crop.json"))["crop"]
x0, y0, x1, y1 = crop
gl = np.load(f05_dir + "/glasses.npy").astype(np.float32)
mk = np.load(f05_dir + "/masks.npy").astype(np.float32)


HS = (gl.shape[1] // q, gl.shape[0] // q)


def half(a_):
    return cv2.resize(a_, HS, interpolation=cv2.INTER_AREA) if q > 1 else a_


x0, y0 = x0 // q, y0 // q
gl, mk = half(gl), half(mk)
x1, y1 = x0 + gl.shape[1], y0 + gl.shape[0]
GL = np.zeros((H, W, 4), np.float32)
GL[y0:y1, x0:x1] = gl
MK = np.zeros((H, W, 4), np.float32)
MK[y0:y1, x0:x1] = mk

# his ear in front of the temple's end: the temple rests on the ear's root and runs on behind the helix
ear = np.zeros((H, W), np.uint8)
ep_ = np.array([[790, 422], [760, 398], [690, 392], [630, 418], [590, 478], [575, 560], [585, 660], [620, 760],
                [680, 840], [730, 846], [770, 800], [790, 700], [802, 600], [806, 500], [794, 458]], np.float32) * s
cv2.fillPoly(ear, [ep_.round().astype(np.int32)], 1)
ear = cv2.GaussianBlur(ear.astype(np.float32), (0, 0), 1.0)
# the near temple's contact shadow on the skin: its mask, moved away from the key light, softened
tm = MK[..., 2]
sdx, sdy = o.get("temple_shadow_off", [-4, 7])
tsh = np.roll(np.roll(tm, sdy // q, 0), sdx // q, 1)
tsh = cv2.GaussianBlur(tsh, (0, 0), o.get("temple_shadow_blur", 4.0) / q)
tsh = np.clip(tsh * o.get("temple_shadow", 0.55), 0, 0.8) * (1 - ear)
# his nose stands in front of the frame's far side (the far rim, its lens, its pad): his own pixels there;
# under the tip, the nose's underside and his upper lip hide the far rim's lower edge too (down to where the
# rim leaves his profile; outside his outline nothing of him hides it)
nose = np.zeros((H, W), np.uint8)
prof = np.array([[1588, 598], [1595, 640], [1615, 670], [1630, 720], [1642, 780], [1650, 830], [1652, 880],
                 [1664, 905], [1662, 930], [1650, 955], [1636, 985], [1450, 985], [1450, 598]], np.float32) * s
cv2.fillPoly(nose, [prof.round().astype(np.int32)], 1)
nose = cv2.GaussianBlur(nose.astype(np.float32), (0, 0), 1.2)
# (only where his picture, retouched, shows skin: the stand-in's own dark rim beside the nose stays under F05)
_rt = cv2.cvtColor(cv2.imread(D + "man_rt2.png"), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
_rm0 = np.load(D + "m_retouched2.npy").astype(np.float32)
_tab = np.zeros_like(_rm0)                                  # the skin under the nose's tip (retouch2.py):
_tab[900:972, 1588:1682] = np.load(D + "m_retouched.npy")[900:972, 1588:1682]   # skin, though in shadow
_rm = cv2.GaussianBlur(_rm0, (0, 0), 1.5)[..., None]
_img = np.load(D + "man_rgb.npy").astype(np.float32) * (1 - _rm) + _rt * _rm
skin_m = cv2.resize(np.maximum(_img.mean(-1) > 0.35, _tab > 0.5).astype(np.float32), (mw, mh),
                    interpolation=cv2.INTER_AREA)
del _rt, _rm, _rm0, _tab, _img
SKM = np.zeros((H, W), np.float32)
SKM[:mh, :mw] = skin_m[:mh, :mw]
# the far half's share of each frame pixel (its coverage over the frame's: whole along the anti-aliased
# edge too, which the glasses pass drew a little wider), reaching a pixel further into that edge
own = np.clip(MK[..., 1] / np.maximum(MK[..., 3], 1e-3) * (MK[..., 3] > 0.01), 0, 1)
# (and the keyhole's far side from the masks' 12.5 mm line up to the bar's underside: the nose's ridge is the
# line between what of the arch shows and what it hides, so the bar rests on the nose without a notch)
_arch = np.zeros((H, W), np.uint8)
cv2.fillPoly(_arch, [(np.array([[1539, 636], [1556, 636], [1566, 639], [1566, 649], [1539, 649]], np.float32) / q)
                     .round().astype(np.int32)], 1)
own = cv2.dilate(own, np.ones((3, 3), np.uint8))
own = np.maximum(own, cv2.GaussianBlur(_arch.astype(np.float32), (0, 0), 0.8) * (GL[..., 3] > 0.5))
occ = nose * own * cv2.GaussianBlur(SKM, (0, 0), 1.0) * AM
occ = np.maximum(occ, ear * np.clip(MK[..., 2] * 2, 0, 1))

# F05's shadow on him: the shadow pass's ratio (his head lit with the frame over lit without it)
try:
    sh = half(np.load(f05_dir + "/shadow.npy").astype(np.float32))
    SH = np.ones((H, W, 3), np.float32)
    ok = sh[..., 3:4] > 0.5
    rat = np.clip(sh[..., :3], 0, 1)
    rl = (0.2126 * rat[..., 0] + 0.7152 * rat[..., 1] + 0.0722 * rat[..., 2])[..., None]
    rat = rl + (rat - rl) * o.get("shadow_chroma", 0.25)
    SH[y0:y1, x0:x1] = np.where(ok, rat, 1.0)
    # where his nose stands in front of the frame's far side, that side's edges pierce the nose's mesh and
    # the pass drew their contact as a black line across the nose, thickest under the bridge: a grey-level
    # closing there takes out what is thinner than its kernel, and the shadow is kept no deeper than the
    # bridge's broad shadow on the nose (the contact itself is the composite's contact shadow, below)
    kc = max(3, int(o.get("nose_close_px", 25) / q) | 1)
    SHc = cv2.morphologyEx(SH, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kc, kc)))
    SHc = np.maximum(SHc, o.get("nose_shadow_floor", 0.5))
    wn = cv2.dilate((nose * own > 0.02).astype(np.uint8), np.ones((kc, kc), np.uint8))
    wn = cv2.GaussianBlur(wn.astype(np.float32) * nose, (0, 0), 3.0 / q)[..., None]
    SH = SH * (1 - wn) + SHc * wn
    SH = cv2.GaussianBlur(SH, (0, 0), o.get("shadow_soft", 1.2))
except FileNotFoundError:
    SH = np.ones((H, W, 3), np.float32)

# the front and end pieces as seen (not the temple; not what his nose hides)
fa = np.clip(GL[..., 3] * (1 - MK[..., 2]) * (1 - occ), 0, 1)
ao = cv2.GaussianBlur(fa, (0, 0), o.get("contact_px", 9.0) / q) * (1 - fa)
ao = np.clip(ao * o.get("contact", 0.9), 0, 0.6)
MANs = MAN * SH * (1 - tsh[..., None]) * (1 - ao[..., None])

out = bg.copy()
out = MANs * AM[..., None] + out * (1 - AM[..., None])
ga = GL[..., 3:4] * (1 - occ[..., None])
out = GL[..., :3] * (1 - occ[..., None]) + out * (1 - ga)

# ---- one surface
# light wrap: the room's light spilling round his edges (the background, blurred, over the edge's inside)
edge = np.clip(AM - cv2.erode(AM, np.ones((9 // q, 9 // q), np.uint8)), 0, 1)
wrap = cv2.GaussianBlur(bg, (0, 0), 14 / q)
out = out + wrap * cv2.GaussianBlur(edge, (0, 0), 3 / q)[..., None] * o.get("wrap", 0.35)
# bloom off what is very bright (the key's glints, the wall's lit paint)
br = np.clip(out - o.get("bloom_thr", 0.9), 0, None)
bloom = cv2.GaussianBlur(br, (0, 0), 18 / q) + cv2.GaussianBlur(br, (0, 0), 60 / q) * 0.5
out = out + bloom * o.get("bloom", 0.12)
# exposure and a filmic shoulder
out = out * 2 ** o.get("ev", 0.0)
k = o.get("shoulder", 0.35)
out = out / (1 + k * out)
# grade: blacks lifted a touch, the shadows a little cooler
lift = np.array(o.get("lift", [0.006, 0.004, 0.009]), np.float32)
out = out + lift * (1 - np.clip(out / 0.2, 0, 1))
srgb = np.where(out <= 0.0031308, 12.92 * out, 1.055 * np.clip(out, 0, None) ** (1 / 2.4) - 0.055)
# a gentle S round the mid-greys (the print's contrast; the ends stay put)
srgb = np.clip(srgb, 0, 1)
srgb = srgb + o.get("contrast", 0.0) * 4 * srgb * (1 - srgb) * (srgb - o.get("pivot", 0.42))
# grain, the same everywhere (luminance, fine)
rng = np.random.default_rng(11)
g = rng.standard_normal((H, W)).astype(np.float32)
g = cv2.GaussianBlur(g, (0, 0), 0.7)
srgb = srgb + g[..., None] * o.get("grain", 0.012)
srgb = np.clip(srgb, 0, 1)
# the light falls away from his face towards the frame's lower left (his jacket, nearest the floor)
yy0, xx0 = np.mgrid[0:H, 0:W].astype(np.float32)
fall = np.clip((yy0 / H - 0.45) / 0.55, 0, 1) * np.clip(1 - xx0 / (0.6 * W), 0, 1)
srgb = srgb * (1 - o.get("falloff", 0.28) * fall ** 1.3)[..., None]
# vignette
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r2 = ((xx - W * 0.42) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.75)) ** 2
srgb = srgb * (1 - o.get("vignette", 0.18) * np.clip(r2, 0, 1.5))[..., None]
im8 = (np.clip(srgb, 0, 1) * 255 + 0.5).astype(np.uint8)
cv2.imwrite(out_p, cv2.cvtColor(im8, cv2.COLOR_RGB2BGR))
cv2.imwrite(out_p.replace(".png", "-preview.jpg"), cv2.cvtColor(cv2.resize(im8, (1000, 750), interpolation=cv2.INTER_AREA),
                                                               cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
print("saved", out_p)
