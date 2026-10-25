"""Take the stand-in glasses off M4 where F05 will not cover them: the near temple's band (from the ear to the
front), the slivers of the stand-in's front past F05's outline. Each region is rebuilt as a smooth colour
field (filled from its own kind of surround only: skin from skin, hair from hair) plus fine detail (pores,
freckles, hair strands) borrowed from nearby donors of the same kind, tiled with feathered seams.

Writes man_rt.png (the portrait retouched) and v_retouch.jpg."""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import REPO, WORK  # noqa: E402,F401
import cv2
import numpy as np
from scipy import ndimage as ndi
from skimage.restoration import inpaint_biharmonic

D = WORK
img = cv2.imread(D + "man_m.png").astype(np.float32) / 255
H, W = img.shape[:2]
st = cv2.imread(D + "m_standin.png", 0) > 0
left = cv2.imread(D + "m_left.png", 0) > 0
rng = np.random.default_rng(5)

temple = st.copy()
temple[:, 1225:] = False
temple |= np.roll(temple, 6, axis=0) & (np.arange(H)[:, None] < 520)       # the brown lower edge, fully
front_left = left.copy()
front_left[:, :1225] = False
# the front's leftovers grown so F05's edge lands on clean skin, and only where they reach past it
region = temple | (cv2.dilate(front_left.astype(np.uint8), np.ones((11, 11), np.uint8)) > 0)
region = cv2.dilate(region.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
region &= ~(cv2.imread(D + "m_f05.png", 0) > 0) | temple      # under F05's front: leave it (hidden)
region = cv2.dilate(region.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0

# hair or skin, inside the region: the hairline comes down to the temple's top at x ~ 935 and leaves
# its bottom as the sideburn's wisp at x ~ 900; above the ear's root (x < 835, y > 430) it is ear
yy, xx = np.mgrid[0:H, 0:W]
hl_x = 938 + (yy - 385) * (898 - 938) / (495 - 385)
hair_side = (xx < hl_x) & (yy < 520) & (xx < 960)
ear = (xx < 835) & (yy > 432) & (yy < 520)
hair_in = region & hair_side & ~ear
skin_in = region & ~hair_in

# the known surround of each kind
Lum = img.mean(-1)
known = ~cv2.dilate(st.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
hair_known = known & (Lum < 0.22)
skin_known = known & (Lum > 0.35)


def smooth_fill(target, src_known, box):
    """Biharmonic fill of `target` from `src_known` pixels only, at a quarter size, upsampled."""
    x0, y0, x1, y1 = box
    q = 4
    im = img[y0:y1, x0:x1]
    small = cv2.resize(im, ((x1 - x0) // q, (y1 - y0) // q), interpolation=cv2.INTER_AREA)
    kn = cv2.resize(src_known[y0:y1, x0:x1].astype(np.float32), small.shape[1::-1], interpolation=cv2.INTER_AREA) > 0.99
    unknown = ~kn
    out = np.stack([inpaint_biharmonic(small[..., c], unknown) for c in range(3)], -1)
    up = cv2.resize(out, (x1 - x0, y1 - y0), interpolation=cv2.INTER_CUBIC)
    full = img.copy()
    full[y0:y1, x0:x1] = np.where(target[y0:y1, x0:x1, None], up, img[y0:y1, x0:x1])
    return full


def highpass(im, sig):
    return im - cv2.GaussianBlur(im, (0, 0), sig)


def tile_detail(target, donor_mask, box, P=36, step=26, sig=2.2, seed=0, gain=1.0):
    """Fine detail for `target` from random donor patches lying wholly inside `donor_mask`, feathered."""
    r = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    hp = highpass(img, sig)
    acc = np.zeros((H, W, 3), np.float32)
    wsum = np.zeros((H, W), np.float32)
    win = np.outer(np.hanning(P + 2)[1:-1], np.hanning(P + 2)[1:-1]).astype(np.float32)
    dm = cv2.erode(donor_mask.astype(np.uint8), np.ones((P, P), np.uint8)) > 0
    dy, dx = np.nonzero(dm)
    if len(dy) == 0:
        raise SystemExit("no donor")
    for ty in range(y0 - P // 2, y1, step):
        for tx in range(x0 - P // 2, x1, step):
            a0, b0 = max(0, ty), max(0, tx)
            a1, b1 = min(H, ty + P), min(W, tx + P)
            if not target[a0:a1, b0:b1].any():
                continue
            k = r.integers(len(dy))
            sy, sx = dy[k] - P // 2, dx[k] - P // 2
            sy, sx = np.clip(sy, 0, H - P), np.clip(sx, 0, W - P)
            patch = hp[sy:sy + P, sx:sx + P]
            w_ = win[a0 - ty:a1 - ty, b0 - tx:b1 - tx]
            acc[a0:a1, b0:b1] += patch[a0 - ty:a1 - ty, b0 - tx:b1 - tx] * w_[..., None]
            wsum[a0:a1, b0:b1] += w_
    det = acc / np.maximum(wsum, 1e-6)[..., None]
    # the tiles' averaging lowers the detail's contrast: restore it to the donors'
    sd_d = hp[donor_mask].std(0)
    sd_t = det[target].std(0) + 1e-6
    return det * (sd_d / sd_t) * gain


box = (700, 300, 1960, 800)
# (a) the temple band: each column filled from what lies just above and just below it (skin over skin,
# hair over hair, the hairline a soft gradient where hair is above and skin below)
low = img.copy()
band = temple | (region & (xx < 1225) & (yy < 520))
sm = cv2.GaussianBlur(img, (0, 0), 3.0)
cols = np.nonzero(band.any(0))[0]
tops, bots, ctop, cbot = [], [], [], []
for x in cols:
    ys = np.nonzero(band[:, x])[0]
    t, b_ = ys.min(), ys.max()
    tops.append(t); bots.append(b_)
    ctop.append(sm[max(0, t - 9):t - 3, x].mean(0))
    cbot.append(sm[b_ + 3:b_ + 9, x].mean(0))
ctop = ndi.gaussian_filter1d(np.array(ctop), 6, axis=0)
cbot = ndi.gaussian_filter1d(np.array(cbot), 6, axis=0)
for x, t, b_, c0, c1 in zip(cols, tops, bots, ctop, cbot):
    ys = np.arange(t, b_ + 1)
    f = ((ys - t) / max(b_ - t, 1))[:, None]
    f = f * f * (3 - 2 * f)
    low[ys, x] = c0 * (1 - f) + c1 * f
# the hair under the temple: left of the hairline it is the hair just above, cloned down the band's height
# (its strands and sheen come with it); the ear's root below it stays skin
DY = 95
clone = np.zeros_like(img)
clone[DY:] = img[:-DY]
y_h = 443 + (xx - 780) * (461 - 443) / (900 - 780)      # the hair's lower edge, hidden mostly under F05's temple
hz = band & (xx < hl_x) & (yy < y_h)
hzf = cv2.GaussianBlur(hz.astype(np.float32), (0, 0), 3.0)
# the hairline itself (the hair's side, not its foot under the temple) feathered wider: fine hairs
side = cv2.GaussianBlur((band & (xx < hl_x)).astype(np.float32), (0, 0), 6.0)
hzf = np.minimum(hzf, np.where(yy < y_h - 6, side, 1.0))[..., None]
low = np.where(band[..., None], low * (1 - hzf) + clone * hzf, low)
hair_detail_off = hz

# (b) the front's slivers: from the skin round them only (the stand-in and the band marked unknown)
sl = region & ~band
unk = (sl | st | band).astype(np.uint8)
q = 2
small = cv2.resize((img * 255).astype(np.uint8), (W // q, H // q), interpolation=cv2.INTER_AREA)
mk = cv2.resize(unk * 255, (W // q, H // q), interpolation=cv2.INTER_NEAREST)
mk = cv2.dilate(mk, np.ones((3, 3), np.uint8))
fl = cv2.inpaint(small, mk, 12, cv2.INPAINT_TELEA).astype(np.float32) / 255
fl = cv2.GaussianBlur(cv2.resize(fl, (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), 2.0)
# its tone from the skin right beside it (a normalized blur over the known skin only, wider where it has to
# reach): the inpaint alone came out lighter, from the forehead's skin
kn = (skin_known & ~cv2.dilate((st | region).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)).astype(np.float32)
tone = None
for sg in (8, 20, 45):
    num = np.stack([cv2.GaussianBlur(img[..., c] * kn, (0, 0), sg) for c in range(3)], -1)
    den = cv2.GaussianBlur(kn, (0, 0), sg)
    t_ = num / np.maximum(den, 1e-6)[..., None]
    if tone is None:
        tone, dd = t_, den
    else:
        w_ = np.clip((0.2 - dd) / 0.15, 0, 1)[..., None]
        tone = tone * (1 - w_) + t_ * w_
        dd = np.maximum(dd, den)
low[sl] = tone[sl]

# (c) texture: band-passed detail from skin donors, or from the hair where the fill is dark
def bandpass(im, s1, s2):
    return cv2.GaussianBlur(im, (0, 0), s1) - cv2.GaussianBlur(im, (0, 0), s2)


def tile(target, donor_mask, P, step, seed, src):
    r = np.random.default_rng(seed)
    acc = np.zeros((H, W, 3), np.float32)
    wsum = np.zeros((H, W), np.float32)
    win = np.outer(np.hanning(P + 2)[1:-1], np.hanning(P + 2)[1:-1]).astype(np.float32)
    dm = cv2.erode(donor_mask.astype(np.uint8), np.ones((P, P), np.uint8)) > 0
    dy, dx = np.nonzero(dm)
    ys_, xs_ = np.nonzero(target)
    for ty in range(ys_.min() - P // 2, ys_.max() + 1, step):
        for tx in range(xs_.min() - P // 2, xs_.max() + 1, step):
            a0, b0, a1, b1 = max(0, ty), max(0, tx), min(H, ty + P), min(W, tx + P)
            if not target[a0:a1, b0:b1].any():
                continue
            k = r.integers(len(dy))
            sy, sx = int(np.clip(dy[k] - P // 2, 0, H - P)), int(np.clip(dx[k] - P // 2, 0, W - P))
            w_ = win[a0 - ty:a1 - ty, b0 - tx:b1 - tx]
            acc[a0:a1, b0:b1] += src[sy:sy + P, sx:sx + P][a0 - ty:a1 - ty, b0 - tx:b1 - tx] * w_[..., None]
            wsum[a0:a1, b0:b1] += w_
    det = acc / np.maximum(wsum, 1e-6)[..., None]
    # restore the donors' contrast (averaged overlaps are flatter)
    return det * (src[donor_mask].std(0) / (det[target].std(0) + 1e-6))


bp = bandpass(img, 0.6, 7.0)
donor_skin = np.zeros((H, W), bool)
donor_skin[325:392, 975:1215] = True
donor_skin[505:610, 935:1180] = True
donor_skin &= skin_known
donor_hair = np.zeros((H, W), bool)
donor_hair[290:388, 770:925] = True
donor_hair &= hair_known
det_s = tile(region, donor_skin, 40, 28, 1, bp)
det_h = tile(region, donor_hair, 32, 22, 2, bp)
lowL = low.mean(-1)
hw = np.clip((0.30 - lowL) / 0.15, 0, 1)[..., None]           # dark fill: hair detail
hw = np.maximum(hw, cv2.GaussianBlur(hair_detail_off.astype(np.float32), (0, 0), 2.5)[..., None])
clone_w = cv2.GaussianBlur(hair_detail_off.astype(np.float32), (0, 0), 2.5)[..., None]
fill = low + det_s * (1 - hw) + det_h * (hw - clone_w).clip(0, 1)
m = np.clip(cv2.GaussianBlur(region.astype(np.float32), (0, 0), 1.0), 0, 1)[..., None]
out = np.clip(fill * m + img * (1 - m), 0, 1)
cv2.imwrite(D + "man_rt.png", (out * 255 + 0.5).astype(np.uint8))
np.save(D + "m_retouched.npy", region)
x0, y0, x1, y1 = 640, 260, 1980, 820
vis = np.hstack([img[y0:y1, x0:x1], out[y0:y1, x0:x1]])
cv2.imwrite(D + "v_retouch.jpg", (cv2.resize(vis, None, fx=0.6, fy=0.6) * 255).astype(np.uint8))
print("retouched px", int(region.sum()))
