"""M4's face: InsightFace landmarks (68 3D, 106 2D, 5 kps) and pose on the mirrored portrait, and Depth
Anything V2's relative inverse depth over the whole figure (for the relight's normals). Saves face.json,
disp.npy (full picture size) and an overlay."""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import REPO, WORK  # noqa: E402,F401
import json

import cv2
import numpy as np

from wear import face_of  # noqa: E402
import head3d  # noqa: E402

D = WORK
img = cv2.imread(D + "man_m.png", cv2.IMREAD_COLOR)
H, W = img.shape[:2]
face = face_of(img)
L68 = face.landmark_3d_68.astype(float)
L106 = face.landmark_2d_106.astype(float)
info = {"bbox": face.bbox.tolist(), "kps": face.kps.tolist(), "pose": face.pose.tolist(),
        "l68": L68.tolist(), "l106": L106.tolist(), "W": W, "H": H}
json.dump(info, open(D + "face.json", "w"))
print("bbox", np.round(face.bbox, 1), "pose (pitch, yaw, roll)", np.round(face.pose, 1))
print("kps", np.round(face.kps, 1))

# depth over the figure: the model at its own input size on overlapping squares would be best; one square
# round the head and shoulders is enough for normals (smooth shading)
x0, y0, x1, y1 = face.bbox
side = int(2.6 * (x1 - x0))
cx, cy = int((x0 + x1) / 2), int((y0 + y1) / 2)
box = [max(0, cx - side // 2), max(0, cy - side // 2), min(W, cx + side // 2), min(H, cy + side // 2)]
d_head = head3d.disparity(img[box[1]:box[3], box[0]:box[2]])
d_all = head3d.disparity(img)
np.save(D + "disp_head.npy", d_head)
np.save(D + "disp_all.npy", d_all)
json.dump({"box": box}, open(D + "disp_head.json", "w"))
print("head box", box)

ov = img.copy()
for i, (x, y, z) in enumerate(L68):
    cv2.circle(ov, (int(x), int(y)), 4, (0, 255, 255), -1)
    if i in (0, 8, 16, 27, 30, 33, 36, 39, 42, 45, 48, 54):
        cv2.putText(ov, str(i), (int(x) + 5, int(y) - 5), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
for (x, y) in face.kps:
    cv2.circle(ov, (int(x), int(y)), 8, (0, 0, 255), -1)
cv2.rectangle(ov, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 3)
cv2.imwrite(D + "v_landmarks.jpg", cv2.resize(ov, (W // 2, H // 2)))
dv = (d_head - d_head.min()) / (d_head.max() - d_head.min())
cv2.imwrite(D + "v_disp_head.jpg", (dv * 255).astype(np.uint8))
dv = (d_all - d_all.min()) / (d_all.max() - d_all.min())
cv2.imwrite(D + "v_disp_all.jpg", cv2.resize((dv * 255).astype(np.uint8), (W // 3, H // 3)))
