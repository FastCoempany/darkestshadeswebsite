#!/bin/bash
# The D4 render queue (DRAWER-WALL.md, D4): the eight frame sequences as region renders (only the frames where the
# drawer's interior shows: the tool skips the rest), and the eight lifted stills. Fill it once, then run chunks:
#   nohup python3 tools/blender/render_queue.py run d4 --minutes 95 > work/queue/d4-run.log 2>&1 &
set -e
cd "$(dirname "$0")/../.."
Q="python3 tools/blender/render_queue.py add d4"
TINTS=${TINTS:-wall/assets/lens-tints.json}
for frame in F09 F01 F02 F03 F04 F05 F06 F08; do   # F09 first: the flows are tried on it
  tint=$(python3 -c "import json;t=json.load(open('$TINTS'))['frames']['$frame']['transmission'];print(' '.join(str(v) for v in t))")
  for i in $(seq 0 23); do
    f=$(printf "%03d" $i)
    # the interior shows from frame 3 on (ext 11.7 mm; frames 0 to 2 are the base frames): earlier frames are the base's, no render needed
    [ $i -lt 3 ] && continue
    $Q seq-$frame-$f --outputs work/wall/seq/$frame/$f.region.png -- \
      python3 tools/blender/drawer_wall.py sequence --frames 24 --only $i --frame $frame --region --tint $tint --samples 48
  done
  $Q lifted-$frame --outputs work/wall/stills/$frame-lifted.png -- python3 tools/blender/drawer_wall.py lifted --frame $frame --tint $tint --samples 64
done
python3 tools/blender/render_queue.py status d4 | head -3
