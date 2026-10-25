"""M4's portrait as the founder sent it (work/people/raw/M4-founder-01.jpg, a 1206 x 1623 screenshot): its
white band along the top (77 px) cut off, then doubled (tools/photo/wear.py: EDSR on the head and collar,
FSRCNN elsewhere). Writes man_clean.png and man_clean-x2.png."""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import RAW, WORK  # noqa: E402
import cv2  # noqa: E402
import wear  # noqa: E402

im = cv2.imread(str(RAW / "M4-founder-01.jpg"))
assert im is not None and im.shape[:2] == (1623, 1206), "the founder's portrait of M4 goes in work/people/raw/"
cv2.imwrite(WORK + "man_clean.png", im[77:])
# the head and collar (EDSR), the rest FSRCNN; region in the cleaned picture's pixels
wear.upscaled(WORK + "man_clean.png", 2, region=(120, 0, 960, 900))
print("done")
