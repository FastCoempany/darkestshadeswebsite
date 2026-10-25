"""Second retouch pass over man_rt.png (retouch.py's output), for what the composite at 1:1 showed:

  (a) the brow: the fold the stand-in's heavy top pressed into the skin above it, left standing a few mm above
      F05's lower top; healed: each column's tone carried straight across it from above to below, the skin's
      texture borrowed from just above.
  (b) the far temple, just above F05's far rim: the fill there came out paler than the skin above it, with a
      dark notch at its top; refilled from the skin just above it (its tone, its texture).
  (c) under the nose's tip: the dark band there is his own skin in shadow (the columella, the far nostril's
      wing), not the stand-in: the photograph's own pixels back.

Writes man_rt2.png and m_retouched2.npy (retouch.py's region, less (c), plus (a) and (b)).
"""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import REPO, WORK  # noqa: E402,F401
import cv2
import numpy as np

D = WORK
rt = cv2.cvtColor(cv2.imread(D + "man_rt.png"), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
Fg = np.load(D + "man_rgb.npy").astype(np.float32)
region = np.load(D + "m_retouched.npy").astype(np.float32)
H, W = region.shape
# the picture as relight.py saw it: the photograph, the retouch where it was made
r0 = cv2.GaussianBlur(region, (0, 0), 1.5)[..., None]
img = Fg * (1 - r0) + rt * r0
out = img.copy()
new = np.zeros((H, W), np.float32)


def heal_columns(x0, x1, y0, y1, shift, below=True, feather=4):
    """Rows y0..y1 of columns x0..x1: tone interpolated from the row above (and below), texture from `shift`
    rows above."""
    global out, new
    pad = 12
    sub = img[y0 - shift - pad:y1 + pad + 1, x0 - pad:x1 + pad + 1]
    low = cv2.GaussianBlur(img, (0, 0), 3.0)
    hi = img - low
    ys = np.arange(y0, y1 + 1)
    t = (ys - y0) / max(y1 - y0, 1)
    top = low[y0 - 3, x0:x1 + 1]                                # the tone just above
    bot = low[y1 + 3, x0:x1 + 1] if below else top              # and just below (or carried down)
    base = top[None] * (1 - t[:, None, None]) + bot[None] * t[:, None, None]
    tex = hi[y0 - shift:y1 - shift + 1, x0:x1 + 1]
    patch = base + tex
    m = np.zeros((H, W), np.float32)
    m[y0:y1 + 1, x0:x1 + 1] = 1
    m = cv2.GaussianBlur(cv2.erode(m, np.ones((3, 3), np.uint8)), (0, 0), feather / 2)
    full = out.copy()
    full[y0:y1 + 1, x0:x1 + 1] = patch
    out = out * (1 - m[..., None]) + full * m[..., None]
    new = np.maximum(new, m)
    del sub


# (a) the brow's fold
heal_columns(1186, 1366, 361, 393, shift=34, below=True, feather=6)
# (b) the far temple above F05's far rim (the skin only: right of x ~ 1748, his outline, is the studio's white, cut away
# by the composite)
heal_columns(1706, 1747, 551, 590, shift=42, below=False, feather=3)
# (c) the photograph back under the nose's tip
box = (slice(900, 972), slice(1588, 1682))
region2 = np.maximum(region, (new > 0.02).astype(np.float32))
region2[box] = 0
out[box] = Fg[box]
cv2.imwrite(D + "man_rt2.png", cv2.cvtColor((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR))
np.save(D + "m_retouched2.npy", region2.astype(np.float32))
for nm, (x0, x1, y0, y1) in {"brow": (1150, 1400, 320, 430), "far": (1680, 1790, 510, 620)}.items():
    a = (img[y0:y1, x0:x1] * 255).astype(np.uint8)
    b = (np.clip(out[y0:y1, x0:x1], 0, 1) * 255).astype(np.uint8)
    v = np.concatenate([a, b], 1)
    cv2.imwrite(D + f"v_rt2_{nm}.png", cv2.cvtColor(cv2.resize(v, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
                                                   cv2.COLOR_RGB2BGR))
print("saved man_rt2.png, m_retouched2.npy")
