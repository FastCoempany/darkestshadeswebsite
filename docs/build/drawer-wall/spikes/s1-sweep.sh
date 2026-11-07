#!/bin/bash
# S1's environment-orientation sweep and GLB inspection, as run on Nov 7 2026 from the scratchpad this spike lived in
# (three.js 0.187.0 installed there with `npm i three@0.187.0`; `playwright` 1.63.0 linked from /opt/node-tools).
# Layout it expects: $S/s1/{s1_blender.py,render.mjs,compare.py,web/index.html,out/,out-ms4/} and $S/node_modules.
set -e
S=${S:?the scratchpad root}
cd "$S/s1"
# the four rotations, with the map as saved and mirrored: the unrotated map as saved won (31.58)
python3 - <<PY
import cv2, numpy as np
env = cv2.imread('$S/s1/out/env.hdr', cv2.IMREAD_UNCHANGED)
cv2.imwrite('$S/s1/out/env-mirror.hdr', np.ascontiguousarray(env[:, ::-1]))
PY
for hdr in env.hdr env-mirror.hdr; do for rot in 0 90 180 270; do
  printf "%-15s rot %-4s " $hdr $rot
  node render.mjs /s1/out match "$S/s1/out/three-$hdr-$rot.png" $rot $hdr 2>/dev/null | tail -0
  python3 compare.py "$S/s1/out/cycles.png" "$S/s1/out/three-$hdr-$rot.png" "$S/s1/out/side-$hdr-$rot.jpg"
done; done
# Results on Nov 7 2026 (mean_abs_diff_8bit_on_frame): env.hdr 0: 31.58, 90: 54.47, 180: 50.75, 270: 44.94;
# env-mirror.hdr 0: 34.05, 90: 53.67, 180: 50.75, 270: 45.62.
# the GLB's materials and extensions (KHR_materials_ior was not written: 1.49 rounds to glTF's default)
python3 - <<PY
import json, struct
b = open('$S/s1/out/F09.glb', 'rb').read()
ln = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + ln])
print('extensionsUsed', j.get('extensionsUsed'))
for m in j['materials']: print(json.dumps(m)[:300])
PY
# Output on Nov 7 2026: extensionsUsed None; acetate.001 roughness 0.06 metallic 0; gcd_gold roughness 0.22 (metallic
# default 1); gcd_onyx roughness 0.04; lens.001 alphaMode BLEND, baseColor alpha 0.9383, roughness 0.
