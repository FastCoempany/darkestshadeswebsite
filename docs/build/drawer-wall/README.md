# The drawer wall: working material

The run itself is `docs/build/DRAWER-WALL.md`: the drawer wall alone, built in `wall/`, not a website. The decisions are `docs/brief/00-decisions.md` #43–#47 (#47, no price on the wall, came after D7), O15–O18 and O20. This folder holds what the run starts from and what it produces for review.

| Path | What it is |
|---|---|
| `prototype/drawer_scene.py` | The founder-reviewed single drawer (Nov 5 2026): black calfskin with piped edges, the knob tilted 28° up with the GCD on its face (gold in the prototype; black relief is the wall's default, O15), F09 inside on black velvet. Renders the drawer at a list of extensions. The starting point of `tools/blender/drawer_wall.py`. |
| `prototype/lift_scene.py` | The frame alone on black: the "rim", "pool" and "halo" looks the founder saw, and the "dark" and "lit" pair the touch prototypes cross-faded for the lift (three-quarter view, same camera). |
| `prototype/grade.py` | The grade every look mockup used: warm interior or cool exterior, grain, halation, vignette, lens softness. The starting point of `tools/photo/grade_scene.py`. |
| `prototype/interaction/drawer.src.html` | The touch prototype the founder held on his phone: pull the drawer (an 11-frame sequence), tap the frame to lift it, turn it, put it back. `__FRAMES__`, `__DARK__` and `__LIT__` were filled with base64 JPEGs of the renders. |
| `prototype/interaction/pull.src.html` | The first touch prototype: pull the frame toward you out of the dark into the light (the dark and lit pair, cross-faded and scaled). |
| `prototype/stills/` | Reference stills from those renders: the drawer shut, half open and open; the lift pair; the rim-lit front. |
| `research-2026-11-06.md` | The research behind the stack, the mechanics and the budgets, with where the run departs from it. |
| `spikes/` | D0's spikes as run (Nov 7 2026): S1 (`s1_blender.py`, `s1-three.html`, `s1-render.mjs`, `s1-compare.py`, the side-by-side `s1-f09-cycles-vs-three.jpg`), S2 (`s2-index.html`, `s2-probe.js`, the test Artifact's page) and S4 (`s4-touch.mjs`). Their numbers are in `WALL-PROGRESS.md`. Working scripts, not tools, written for the scratchpad they ran in (their paths say so); the tools they led to live in `tools/`. The logs as run: `s3-render.log`, `s1-blender.log`, `s1-sweep.sh`. |
| `usability.md` | Written in D7: the five-person test. |
| `review/R1` … `R4` | The review sets the run publishes for the founder. |
| `launch.md` | Written in D9: how the wall goes into a store later (the metaobject definitions, the adapter, placing `<drawer-wall>`), how to change a drawer, add a frame, swap in a reshoot or a scanned leather. |

Both scripts run from the repo root with `bpy==5.2.2` (they import `tools/blender/frame3d.py`):

```
python3 docs/build/drawer-wall/prototype/drawer_scene.py --ext 0,0.25 --outdir work/drawer-proto --samples 40 --size 760
python3 docs/build/drawer-wall/prototype/lift_scene.py F09 lit tq --out work/lift-proto/tq-lit.png --samples 64
```
