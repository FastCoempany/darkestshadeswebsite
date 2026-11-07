import sys, numpy as np
from PIL import Image
a = Image.open(sys.argv[1]).convert("RGBA"); b = Image.open(sys.argv[2]).convert("RGBA")
def over_black(im):
    x = np.asarray(im).astype(np.float32) / 255; return x[..., :3] * x[..., 3:4]
A, B = over_black(a), over_black(b)
if A.shape != B.shape: B = np.asarray(Image.fromarray((B*255).astype(np.uint8)).resize((A.shape[1], A.shape[0]))).astype(np.float32)/255
d = np.abs(A - B)
lum = lambda x: x @ np.array([0.2126, 0.7152, 0.0722])
mask = (lum(A) > 0.02) | (lum(B) > 0.02)
print({"mean_abs_diff_8bit_all": round(float(d.mean()*255), 2), "mean_abs_diff_8bit_on_frame": round(float(d[mask].mean()*255), 2),
       "mean_lum_cycles_on_frame": round(float(lum(A)[mask].mean()*255), 1), "mean_lum_three_on_frame": round(float(lum(B)[mask].mean()*255), 1),
       "frame_px": int(mask.sum())})
side = np.concatenate([A, np.ones((A.shape[0], 8, 3))*0.5, B, np.ones((A.shape[0], 8, 3))*0.5, np.repeat(np.clip(d*4, 0, 1).mean(-1, keepdims=True), 3, -1)], 1)
Image.fromarray((np.clip(side, 0, 1)*255).astype(np.uint8)).save(sys.argv[3], quality=90)
