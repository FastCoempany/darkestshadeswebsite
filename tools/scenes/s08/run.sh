#!/bin/bash
# M4 in F05 in the lounge (S08), v01, start to finish, with the settings v01 was made with: about an hour on
# two CPU cores, most of it the lounge's render. Needs the founder's portrait of M4 at
# work/people/raw/M4-founder-01.jpg, the models in work/models/ (tools/photo/wear.py's upscalers,
# tools/blender/head3d.py's depth model, InsightFace's buffalo_l, rembg's ISNet) and bpy==5.2.2.
# Writes into work/people/DS-CAST-M4-S08-F05-v01/ (its working files in data/, or in $S08_WORK).
set -e
cd "$(dirname "$0")"
OUT="$(cd ../../.. && pwd)/work/people/DS-CAST-M4-S08-F05-v01"
export S08_WORK="${S08_WORK:-$OUT/data}"
mkdir -p "$S08_WORK" "$OUT"

python3 upscale_man.py                        # his portrait, its white top band off, doubled
python3 man_prep.py                           # mirrored, the screenshot's tab off, cut out
python3 man_geo.py                            # landmarks, the depth model's disparity
cp m4_f05_pose.json "$S08_WORK/pose.json"     # F05's pose as fitted for v01 (fit_f05.py fits one afresh)
python3 standin.py                            # the stand-in glasses' masks, F05's coverage
python3 retouch.py                            # the stand-in taken off where F05 does not cover it
python3 retouch2.py                           # the brow's fold, the far temple, the skin under the nose's tip
python3 build_head.py                         # his head as a mesh, in millimetres against F05
python3 art.py                                # the wall's new art
python3 lounge_bg.py "$S08_WORK/bg_final.exr" --scale 0.5 --samples 64
F05="--samples 128 --bounce 0.25 --hdri-strength 0.8 --hdri-rot 120 --hdri-tint 1.0 0.70 0.78"
python3 f05_lounge.py "$S08_WORK/f05" $F05 --passes glasses --rim 0.03        # the blue rim a sheen on the metal
python3 f05_lounge.py "$S08_WORK/f05" $F05 --passes masks,shadow --rim 0.12
python3 relight.py '{"light_over": {"key": {"color": [1.0, 0.34, 0.58]}, "fill": {"color": [1.0, 0.50, 0.68], "power": 2.6}, "rim": {"power": 0}, "lamp": {"power": 10.0}}, "wrap": {"key": 0.15, "fill": 0.3, "top": 0.1}, "ambient": [0.02, 0.011, 0.02]}'
python3 composite.py "$S08_WORK/bg_final.npy" "$S08_WORK/f05" "$OUT/DS-CAST-M4-S08-F05-v01.png" \
    '{"wrap": 0.12, "ev": -0.2, "shadow_chroma": 0.0, "contrast": 0.3}'
