"""The lounge's new wall art (the founder: keep the scene, alter the art): hand-painted, no words, no
faces. A loose crimson ring, swept on with a wide brush, cream strokes slashed through it, drips running
down from both, splatter, a few charcoal lines. Painted in wall coordinates: X -1.5..2.0 m, Z -0.9..1.2 m
(Z up), 15 px per cm. Writes art_rgba.png (straight colour, 16-bit; alpha = paint coverage)."""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import REPO, WORK  # noqa: E402,F401
import numpy as np
import cv2

D = WORK
PX = 1500.0                       # px per metre
X0, X1, Z0, Z1 = -1.5, 2.0, -0.9, 1.2
W, H = int((X1 - X0) * PX), int((Z1 - Z0) * PX)
rng = np.random.default_rng(7)


def to_px(x, z):
    return (np.asarray(x) - X0) * PX, (Z1 - np.asarray(z)) * PX


def noise(shape, scale, octaves=4, seed=0):
    r = np.random.default_rng(seed)
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(2, int(scale / (2 ** o)))
        small = r.standard_normal((shape[0] // s + 2, shape[1] // s + 2)).astype(np.float32)
        out += amp * cv2.resize(small, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= 0.5
    return out / tot


col = np.zeros((H, W, 3), np.float32)
cov = np.zeros((H, W), np.float32)


def lay(color, a):
    """Paint `a` (coverage 0..1) of `color` over what is there."""
    global col, cov
    a = np.clip(a, 0, 1)[..., None]
    col = col * (1 - a) + np.asarray(color, np.float32) * a
    cov[:] = 1 - (1 - cov) * (1 - a[..., 0])


def smooth1d(r, n, k):
    v = np.convolve(r.standard_normal(n + 2 * k), np.ones(k) / np.sqrt(k), "same")[k:k + n]
    return v / (v.std() + 1e-9)


def stroke(path, width, color, bristles=70, dry=0.35, seed=0, vary=0.06, skip=0.25):
    """A brush stroke along `path` (metres, wall coords), `width` metres (a scalar or per point): many
    bristles side by side, each a line that starts and stops a little apart from the others and carries
    its own load along the stroke (streaks along the stroke, gaps where a bristle runs dry)."""
    r = np.random.default_rng(seed)
    P = np.asarray(path, np.float64)
    # a smooth curve through the points (Catmull-Rom), evenly resampled
    Pe = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    C = []
    for i in range(1, len(Pe) - 2):
        p0, p1, p2, p3 = Pe[i - 1], Pe[i], Pe[i + 1], Pe[i + 2]
        for u in np.linspace(0, 1, 40, endpoint=False):
            C.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                            + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    C.append(P[-1])
    C = np.array(C)
    seg = np.linalg.norm(np.diff(C, axis=0), axis=1)
    s_ = np.r_[0, np.cumsum(seg)]
    n = max(8, int(s_[-1] * PX / 2))
    q = np.linspace(0, s_[-1], n)
    P = np.stack([np.interp(q, s_, C[:, 0]), np.interp(q, s_, C[:, 1])], 1)
    wv = np.atleast_1d(np.asarray(width, float))
    w = np.interp(q / s_[-1], np.linspace(0, 1, len(wv)), wv)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    N = np.stack([-T[:, 1], T[:, 0]], 1)
    layer = np.zeros((H * 2, W * 2), np.float32) if False else np.zeros((H, W), np.float32)
    load = np.clip(1.1 - dry * np.linspace(0, 1, n) ** 1.3, 0.15, 1)
    for b in range(bristles):
        o = (b + r.uniform(-0.45, 0.45)) / (bristles - 1) * 2 - 1
        t0 = int(abs(r.normal(0, 0.03)) * n * (2.0 if abs(o) > 0.8 else 1))
        t1 = n - int(abs(r.normal(0, 0.06)) * n * (2.5 if abs(o) > 0.7 else 1))
        if t1 - t0 < 4:
            continue
        own = smooth1d(r, n, max(3, n // 25))
        gaps = (own > (1.6 - 2.2 * skip - 1.2 * (1 - load))).astype(np.float32)   # dry: the bristle skips
        gaps = np.convolve(gaps, np.ones(5) / 5, "same")
        inten = r.uniform(0.6, 1.0) * (1 - 0.5 * abs(o) ** 5) * load * (1 - 0.85 * gaps)
        wob = smooth1d(r, n, max(3, n // 12)) * 0.03
        pts = P + N * ((o + wob)[:, None] * w[:, None] / 2)
        xs, ys = to_px(pts[t0:t1, 0], pts[t0:t1, 1])
        th = max(1, int(round(np.mean(w) * PX / bristles * 2.4)))
        for k in range(len(xs) - 1):
            a_ = float(inten[t0 + k])
            if a_ < 0.04:
                continue
            cv2.line(layer, (int(xs[k] * 4), int(ys[k] * 4)), (int(xs[k + 1] * 4), int(ys[k + 1] * 4)), a_, th,
                     cv2.LINE_AA, shift=2)
    layer = np.clip(layer * 1.35, 0, 1)
    jitter = np.asarray(color, np.float32) * (1 + vary * noise((H, W), 250, 2, seed + 5)[..., None])
    global col, cov
    a = layer[..., None]
    col = col * (1 - a) + np.clip(jitter, 0, 1) * a
    cov[:] = 1 - (1 - cov) * (1 - layer)
    return P, w


def drips(P, w, color, count, seed, maxlen=0.28, width=(0.004, 0.009), where=0.5):
    """Paint running down from a stroke's lower edge: a thin tapering line, a drop at its end."""
    r = np.random.default_rng(seed)
    layer = np.zeros((H, W), np.float32)
    for _ in range(count):
        i = r.integers(0, len(P))
        x, z = P[i]
        z = z - w[i] * where * r.uniform(0.6, 1.0)
        L = maxlen * r.uniform(0.1, 1.0) ** 1.6
        dw = r.uniform(*width)
        steps = max(4, int(L * PX))
        zz = z - np.linspace(0, L, steps)
        xx = x + np.cumsum(r.normal(0, 0.00015, steps))
        ww = dw * (1 - 0.55 * np.linspace(0, 1, steps)) * (1 + 0.15 * r.standard_normal(steps).clip(-1, 1))
        px, pz = to_px(xx, zz)
        for k in range(steps - 1):
            cv2.line(layer, (int(px[k] * 4), int(pz[k] * 4)), (int(px[k + 1] * 4), int(pz[k + 1] * 4)), 1.0,
                     max(1, int(ww[k] * PX)), cv2.LINE_AA, shift=2)
        cv2.circle(layer, (int(px[-1] * 4), int(pz[-1] * 4)), max(2, int(dw * PX * 0.9 * 4)), 1.0, -1, cv2.LINE_AA, shift=2)
    lay(color, layer * 0.95)


def splatter(cx, cz, rad, color, count, seed, size=(0.001, 0.006)):
    r = np.random.default_rng(seed)
    layer = np.zeros((H, W), np.float32)
    for _ in range(count):
        d = rad * r.uniform(0, 1) ** 0.7
        a = r.uniform(0, 2 * np.pi)
        x, z = cx + d * np.cos(a), cz + d * np.sin(a) * 0.8
        px, pz = to_px(x, z)
        cv2.circle(layer, (int(px * 4), int(pz * 4)), max(1, int(r.uniform(*size) * PX * 4)), r.uniform(0.6, 1.0), -1,
                   cv2.LINE_AA, shift=2)
    lay(color, layer)


CRIMSON = (0.62, 0.035, 0.05)
DEEP = (0.36, 0.02, 0.04)
CREAM = (0.86, 0.80, 0.66)
BONE = (0.74, 0.70, 0.60)
CHAR = (0.05, 0.05, 0.06)
TEAL = (0.06, 0.20, 0.24)

# the wall's old life: faint grey drips everywhere, the way the room's black paint went on over older paint
fd = np.random.default_rng(77)
for i in range(140):
    x0_, z0_ = fd.uniform(-1.45, 1.95), fd.uniform(-0.6, 1.15)
    drips(np.array([[x0_, z0_], [x0_ + 0.001, z0_]]), np.array([0.0, 0.0]), (0.30, 0.29, 0.28), 1, 1000 + i,
          maxlen=fd.uniform(0.06, 0.7), width=(0.002, 0.005))
cov *= 0.0 + 1.0
faint = cov.copy()
cov = cov * 0.35                    # thin, mostly black over them

# a dark ground wash behind the composition: thinned black-green glaze, uneven
g = noise((H, W), 600, 3, 3)
mask = np.zeros((H, W), np.float32)
px, pz = to_px(np.array([-0.4, 1.3]), np.array([0.7, -0.35]))
cv2.ellipse(mask, (int((px[0] + px[1]) / 2), int((pz[0] + pz[1]) / 2)), (int(abs(px[1] - px[0]) / 2), int(abs(pz[1] - pz[0]) / 2)),
            0, 0, 360, 1.0, -1)
mask = cv2.GaussianBlur(mask, (0, 0), 120)
lay(TEAL, mask * np.clip(0.25 + 0.5 * g, 0, 0.55))

# a bone veil behind where his head is: long, very dry horizontal passes of a wide brush
veil0 = cov.copy()
for k in range(6):
    rr_ = np.random.default_rng(100 + k)
    za = 0.12 + k * 0.11 + rr_.uniform(-0.03, 0.03)
    xa = rr_.uniform(-1.0, -0.7)
    L_ = rr_.uniform(0.9, 1.3)
    pts_ = np.array([[xa, za], [xa + L_ * 0.35, za + rr_.uniform(-0.03, 0.03)], [xa + L_ * 0.7, za + rr_.uniform(-0.04, 0.02)],
                     [xa + L_, za + rr_.uniform(-0.06, 0.0)]])
    stroke(pts_, np.array([0.08, 0.17, 0.16, 0.06]), BONE, bristles=120, dry=0.95, seed=200 + k, skip=0.6)
cov = veil0 + (cov - veil0) * 0.45            # thin: the black shows through it

# a big crimson sweep, arched, from high left down to the right
A = np.array([[-0.05, 0.62], [0.25, 0.52], [0.55, 0.34], [0.80, 0.14], [1.02, 0.02]])
PA, wA = stroke(A, np.array([0.05, 0.13, 0.14, 0.11, 0.05]), CRIMSON, bristles=110, dry=0.45, seed=1, skip=0.2)
drips(PA, wA, CRIMSON, 24, 3, maxlen=0.34, where=0.48)
# a second crimson pass over its lower half, darker
A2 = np.array([[0.42, 0.40], [0.66, 0.24], [0.90, 0.07]])
stroke(A2, np.array([0.04, 0.08, 0.04]), DEEP, bristles=70, dry=0.7, seed=2, skip=0.35)
# a heavy cream stroke falling steeply through it, off the vertical, a little bowed
B = np.array([[0.50, 0.66], [0.56, 0.47], [0.60, 0.30], [0.61, 0.12]])
PB, wB = stroke(B, np.array([0.04, 0.085, 0.09, 0.06]), CREAM, bristles=90, dry=0.65, seed=4, skip=0.3)
drips(PB, wB, CREAM, 10, 5, maxlen=0.30, where=0.0)
# a short bone stroke lower right, laid flat and quick
Cs = np.array([[0.80, 0.33], [0.95, 0.27], [1.14, 0.25]])
stroke(Cs, np.array([0.02, 0.05, 0.02]), BONE, bristles=60, dry=0.6, seed=6, skip=0.35)
# a dark blue-grey bar across the top, almost lost in the black
Dk = np.array([[0.20, 0.47], [0.60, 0.50], [1.15, 0.47]])
stroke(Dk, np.array([0.03, 0.06, 0.03]), (0.10, 0.12, 0.16), bristles=60, dry=0.6, seed=8, skip=0.3)
# behind the head (left of him): crimson laid on its side, cream scumbled under it
E = np.array([[-0.70, 0.36], [-0.40, 0.40], [-0.10, 0.37], [0.08, 0.30]])
PE, wE = stroke(E, np.array([0.03, 0.10, 0.10, 0.04]), CRIMSON, bristles=90, dry=0.5, seed=9, skip=0.25)
drips(PE, wE, CRIMSON, 14, 10, maxlen=0.4)
F = np.array([[-0.62, 0.18], [-0.38, 0.22], [-0.12, 0.21]])
stroke(F, np.array([0.02, 0.05, 0.02]), BONE, bristles=50, dry=0.75, seed=11, skip=0.4)

# splatter and two charcoal lines drawn fast
splatter(0.70, 0.20, 0.30, CRIMSON, 70, 12)
splatter(0.45, 0.50, 0.20, CREAM, 40, 13)
layer = np.zeros((H, W), np.float32)
for k, (xa, za, xb, zb) in enumerate([(0.15, 0.10, 0.70, 0.02), (0.92, 0.55, 1.10, 0.12)]):
    t = np.linspace(0, 1, 60)
    xx = xa + (xb - xa) * t + 0.008 * np.sin(9 * t + k)
    zz = za + (zb - za) * t + 0.01 * np.sin(13 * t + 2 * k)
    px, pz = to_px(xx, zz)
    for i in range(59):
        cv2.line(layer, (int(px[i] * 4), int(pz[i] * 4)), (int(px[i + 1] * 4), int(pz[i + 1] * 4)), 0.85,
                 max(1, int(0.0035 * PX)), cv2.LINE_AA, shift=2)
lay(CHAR, layer * np.clip(0.6 + noise((H, W), 30, 3, 21), 0, 1))

out = np.dstack([col, cov])
cv2.imwrite(D + "art_rgba.png", cv2.cvtColor((np.clip(out, 0, 1) * 65535).astype(np.uint16), cv2.COLOR_RGBA2BGRA))
prev = col * cov[..., None] + 0.03 * (1 - cov[..., None])
cv2.imwrite(D + "v_art.jpg", cv2.resize(cv2.cvtColor((np.clip(prev, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8),
                                                   cv2.COLOR_RGB2BGR), (W // 4, H // 4)))
print("art", W, H)
