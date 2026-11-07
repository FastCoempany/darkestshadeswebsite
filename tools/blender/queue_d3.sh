#!/bin/bash
# The D3 render queue (DRAWER-WALL.md, D3): the two walls lit and dark, the three knob close-ups for O15, the base
# sequence (24 frames, one job each), the cameras and the environment map. Run it once to fill the queue, then
#   nohup python3 tools/blender/render_queue.py run d3 --minutes 95 > work/queue/d3-run.log 2>&1 &
# and again after each chunk until it exits 0. Jobs whose outputs exist are skipped, so it resumes.
set -e
cd "$(dirname "$0")/../.."
Q="python3 tools/blender/render_queue.py add d3"
for layout in portrait landscape; do
  for variant in lit dark; do
    $Q wall-$layout-$variant --outputs work/wall/$layout-black-relief-$variant.png -- \
      python3 tools/blender/drawer_wall.py wall --layout $layout --knob black-relief --variant $variant --samples 64
  done
done
for knob in black-relief gold plain; do
  $Q knob-$knob --outputs work/wall/knob-$knob.png -- python3 tools/blender/drawer_wall.py knob --knob $knob --samples 96
done
for i in $(seq 0 23); do
  f=$(printf "%03d" $i)
  $Q seq-base-$f --outputs work/wall/seq/base/$f.png -- python3 tools/blender/drawer_wall.py sequence --frames 24 --only $i --samples 48
done
$Q cameras --outputs work/wall/camera/open.json work/wall/camera/inspect.json -- python3 tools/blender/drawer_wall.py cameras
$Q env --outputs work/wall/env/drawer.hdr -- python3 tools/blender/drawer_wall.py env --samples 48 --cameras work/wall/camera
# F09's lifted still for R1, with its measured lens tint (tools/photo/lens_tints.py; D4 renders all eight from wall/assets/lens-tints.json)
$Q lifted-F09 --outputs work/wall/stills/F09-lifted.png -- python3 tools/blender/drawer_wall.py lifted --frame F09 --tint 0.0443 0.0444 0.0567 --samples 64
python3 tools/blender/render_queue.py status d3
