# The drawer wall: working material

The run itself is `docs/build/DRAWER-WALL.md`; the decisions are `docs/brief/00-decisions.md` #43–#45 and O15–O18. This folder holds what the run starts from and what it produces for review.

| Path | What it is |
|---|---|
| `prototype/drawer_scene.py` | The founder-reviewed single drawer (Nov 5 2026): black calfskin with piped edges, the knob tilted 28° up with the GCD on its face (gold in the prototype; black relief is the wall's default, O15), F09 inside on black velvet. Renders the drawer at a list of extensions. The starting point of `tools/blender/drawer_wall.py`. |
| `prototype/lift_scene.py` | The frame alone on black: the "rim", "pool" and "halo" looks the founder saw, and the "dark" and "lit" pair the touch prototypes cross-faded for the lift (three-quarter view, same camera). |
| `prototype/grade.py` | The grade every look mockup used: warm interior or cool exterior, grain, halation, vignette, lens softness. The starting point of `tools/photo/grade_scene.py`. |
| `prototype/interaction/drawer.src.html` | The touch prototype the founder held on his phone: pull the drawer (an 11-frame sequence), tap the frame to lift it, turn it, put it back. `__FRAMES__`, `__DARK__` and `__LIT__` were filled with base64 JPEGs of the renders. |
| `prototype/interaction/pull.src.html` | The first touch prototype: pull the frame toward you out of the dark into the light (the dark and lit pair, cross-faded and scaled). |
| `prototype/stills/` | Reference stills from those renders: the drawer shut, half open and open; the lift pair; the rim-lit front. |
| `research-2026-11-06.md` | The research behind the stack, the mechanics and the budgets, with where the run departs from it. |
| `usability.md` | Written in D7: the five-person test. |
| `review/R1` … `R4` | The review sets the run publishes for the founder. |
| `launch.md` | Written in D9: what the store connection needs, how to change a drawer, add a frame, swap in a reshoot or a scanned leather. |

Both scripts run from the repo root with `bpy==5.2.2` (they import `tools/blender/frame3d.py`):

```
python3 docs/build/drawer-wall/prototype/drawer_scene.py --ext 0,0.25 --outdir work/drawer-proto --samples 40 --size 760
python3 docs/build/drawer-wall/prototype/lift_scene.py F09 lit tq --out work/lift-proto/tq-lit.png --samples 64
```
