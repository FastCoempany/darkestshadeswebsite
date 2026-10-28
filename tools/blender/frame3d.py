#!/usr/bin/env python3
"""Build a frame in 3D from its 1:1 technical drawings, with Blender's Python module (bpy).

    python3 tools/blender/frame3d.py F04 --check --out /tmp/F04.png     # the front, upright in a light tent

The founder found every flat composite "pasted on" (Oct 21 2026): a product photo is a flat front
view of the glasses standing on a table, lit by a lightbox; a pair on a head is a 3D object, its front
curved round the face, its temples running back to the ears, lit and shadowed by the scene. So each
frame is rebuilt from the drawings (content/products/drawings/<frame>-front|top|side.svg, 1:1 mm):

- the front: the front view's outline with the lens openings cut through it, a solid whose face and
  back are height fields over the front view: the face rounded at the outer edge, domed across the
  rim, stepping down to the ring round each lens where the front view draws it, rounding into the
  lens; bent to the wrap the top view measures (how far the front's face falls back from the bridge
  towards each end), tilted at the bottom towards the face (pantoscopic tilt);
- the lenses: the openings, a little larger (set in the rim's groove), thin shells at a base curve;
- nose pads, end pieces and temples: from the top and side views, per frame in FRAMES below.

`--check` renders the frame upright in a light tent, as the product shot was taken: compare it with
work/out/<shot>/stage.jpg for shape and gloss.

Units: Blender metres, built from millimetres. Origin: midway between the two lens-box centres on
the front's face, x to the wearer's left (image right in a front view), y up, z towards the camera.
"""
import argparse
import pathlib
import re
import sys

import bpy
import cv2
import numpy as np
from mathutils import Matrix

ROOT = pathlib.Path(__file__).resolve().parents[2]
DRAW = ROOT / "content" / "products" / "drawings"
MM = 0.001

# Per-frame build settings measured from the drawings (mm, degrees). depth: the front's thickness
# front to back (side view); edge_r: the radius its outer edge is rounded to; back_r: its back edges;
# bezel: the ring round each lens (front view: the double line `width` mm out from the opening, a
# step of `step` mm up to the front's face from a ring `drop` mm below it); lip_r: the ring's rounded
# edge into the lens; lens: its front's radius of curvature (base curve) and thickness, set `inset`
# mm behind the ring; tilt: the front's lean from the temples' line, bottom back (pantoscopic; built
# as a shear, so the top stays level and the front view keeps the drawing's outline); pads: the nose pads behind the bridge (top
# and side views: centre x, y, how far behind the front's back, radii); hinge: where the temple
# starts, behind the front's face and below its top (side view); endpiece: the wedge from the front's
# back to the hinge, from `top` to `bottom` mm below the front's top; `metal`: it is polished black
# metal, a plate over the tab's outer side standing `plate` mm proud of it, run on back to the hinge as
# the wedge, one flat outer face (the founder's desk shots, Oct 22 2026: it mirrors the room); temple:
# "wire" (round, `radius`) or "strip" (a flat bar `height` tall and `thick` across, side and top
# views), running `straight` mm back from the hinge, then curving `drop` mm down behind the ear; from
# `tip_from` mm along it the acetate tip, `tip` = (height, width) mm; or "acetate" (F03: a solid
# temple whose `heights` and `thicks` taper along it, on a "block" end piece; `gcd`: the emblem set into
# one temple's outer face). Meshing: mesh_step (the front's grid, in drawing pixels of 0.05 mm),
# edge_floor (mm: right at an edge the height runs level along it), exact_distance (edges measured to
# the outline smoothed into curves, not to its pixel steps); all three keep a three-quarter view's gloss
# free of streaks.
#
# F04 against the founder's side shot of the real frame (Oct 22 2026), where it differs from drawing 05:
# the frame's top is a flat plateau, its front edge rounded tightly (edge_r 1.8); the arm runs square to
# the front (tilt 0; the drawing leans the front 12 deg); and the end piece, the metal triangle behind
# the acetate tab (endpiece["outline"]: u mm back from the tab's back, v mm down from the front's top at
# the end; edges traced on the shot, scaled by the tab's 15.25 mm from the drawing; its length agrees
# with the side view's): its base is the tab's back edge, top to bottom, the top corner flush with the
# plateau; its top edge falls 26 deg to the apex, which sits 14.5 mm back and 56% down (the drawing:
# 46%); its bottom edge rises 20 deg to it. Top view: the outer face is flush with the tab's side and
# the temple's, the triangle 2.25 mm across, the strip 1.25; the hinge's pin is vertical, its barrel
# inside, the screw head on top. The ring round each lens (drawing 05's front view and the cleaned
# front shot, Oct 27 2026): flat, 3.3-3.4 mm from the opening to a crisp step up to the face, whose
# two edges the drawing draws 0.26-0.35 mm apart; in the light tent the ring reads one even black, only
# the lip's rounding into the lens catching a faint line. Built with a pillow and a groove along the
# step, it drew four or five parallel highlights round each lens that the frame does not have.
# F01 (drawing 01, its cleaned shots, Oct 27 2026): a navigator in blue-and-black tortoise acetate, its
# straight brow bar across the top over the nose's opening; a narrow bevel (0.8 mm) round each light blue
# lens; the front 10 deg off upright; 12 mm acetate temples at the front's mid-height (17.9 mm below its
# top), 3.95 mm thick at the joint tapering to 2.1, straight for 73.5 mm and then narrowing to 6 mm before
# the tip's paddle (its eyelet is not built: it is always behind the ear on a head); the joint 6.5 mm
# behind the end tab's face; the GCD on the right temple. The front's colour is the cleaned front shot's;
# the temples', which that shot never sees, the same blue and black laid anew along them
# (frame_texture.py --temples).
# F02 (drawing 03 and its cleaned front shot): a thick crimson-tortoise front (6.5 mm, its outer edge
# well rounded), a 3.2 mm bevel round each lens (the black layer under the tortoise: the "lens bay's bevel
# inlay"), the front leaning ~10 deg at its rims (side view: 13.5 deg below the brow, the brow itself
# upright), wings at its top corners run back 17 mm to the hinges (side view: the block from 1 to 15 mm
# below the top, the temple's centre 9.7 mm down), and black metal temples 2.6 x 1.2 mm (built round:
# from the front they are lines). `texture`: the acetate's colour and the metal on the front, from the
# cleaned front shot (tools/blender/frame_texture.py).
# F05 (drawing 04, the cleaned front and right three-quarter shots, the founder's desk shots of Oct 25 2026):
# a puffy gloss black front (7.5 mm, its outer edge rounded 2.2 mm, the broad face domed 0.9 mm), each lens
# deep in a well: the face sweeps down into it in one smooth convex curve 3.4 mm wide, no ring, no wall, no
# crease, to the lens 3.2 mm under the face's top (a 0.15 mm seam where they meet); the front leans
# ~11 deg (side view); the temples' tips, which hang below the front
# at its outer ends in the front view, trimmed off its outline (`trim_tips`, |x| mm). The end piece is
# F04's kind of metal triangle on the tab's side, from the side view: level along the front's top for
# 4.9 mm (`top_flat`), falling 21 deg to the apex 18 mm back, its bottom edge rising 31 deg to it; its
# base set 3.4 mm into the tab (the band the side view draws along it covers the tab's side); then a
# flat metal temple 2.7 to 2.4 mm tall to the acetate tip's joint 74 mm back, the tip curving down as drawn.
# The metal is satin black paint (`coated`, `metal_rough`: the product shots show soft gradients on it, no
# mirror, and black at every angle).
# F03 (drawing 02, its cleaned shots, the founder's desk shots of Oct 26 2026): F02's front (the two drawings'
# fronts lie on each other: the same outline, openings, bevel line, bridge, lean and wrap), all gloss black,
# with a yellow lens; its face flatter (the photographs: one even tone across it, dome 0.3). Round each lens
# a straight bevel (the photographs: the broad face, then a defined edge where a sloped band runs down to
# the lens, its amber edge glowing through it): a chamfer from the drawing's line 3.2 mm out, rounded over
# 0.3 mm at its top, to the lens 2.1 mm under the face. Acetate temples (side view: 9 mm tall from the
# joint, 8.2 mm behind the end's face, to 80 mm back, then narrowing to 5 mm and turning down behind the
# ear; top view: 4.3 mm across at the joint, 2 mm at the tip; edges rounded 0.9 mm), the joint on a short
# acetate block that carries the temple's section into the end tab; the GCD on the right temple's outer
# face (f03.json: 8.8 mm long, centred 0.82 x the 9 mm face from the joint, 39% down it).
# F06 (drawing 06, its cleaned shots, Oct 27 2026): a flat-top shield in gloss black acetate. Drawing 06's
# front view draws the outline and, 3 mm inside it, one line round the whole shield (139 x 48 mm, the lens
# size the product data carries). The front shot shows that line as a step: the face a band round the
# outside, a lower level inside it, 1.9 mm wide over the brow and 2.6 mm below each opening, and at that
# level a bridge from the brow down to the nose between two openings, which the drawing does not draw. So
# the openings are the photograph's (frame_texture.py --openings), the step is the drawing's line, and one
# flat lens lies behind both openings out to the step (`shield`). The front 5.5 mm deep and 7 deg off upright
# (side view); acetate temples flush with the brow's top, 9.65 mm tall and 2.85 mm thick from the joint,
# narrowing from 91 mm back to the tip's hook; tall smoky pads (side and top views: 19 mm tall, 7 mm behind
# the front); the GCD on the right temple. The front view draws the temples' tips hanging below the front's
# ends: left out (`front_drop`).
# F08 (drawing 08, its cleaned shots, Oct 27 2026): a squared aviator in gloss black acetate, 4.3 mm deep (top
# view), its edges rounded 1 mm; the double bridge: a straight brow across the top, and below it, between
# the lenses, a keyhole cut through the front (`holes`: the region inside the drawing's lines there; its
# edge rounds into it as the outer edge does). Round each lens the face rounds down into it over 1.5 mm (the
# drawing's double line), the lip catching a line of light along the lens's bottom edge in the front shot;
# the lens a grey gradient as measured. The front 8 deg off the temples' line (side view). Translucent smoke
# grey acetate temples on a short black block (the joint 5 mm behind the end's face), 10.75 mm tall at the
# joint, the top edge straight back to the bend while the bottom edge dips 2.8 mm 55-80 mm back and rises to
# a 5.5 mm neck over the ear (`offsets`), 3.9 mm thick tapering to 2.1, edges rounded 1.4 mm; inside each a
# textured metal core, seen through the acetate (`core`); the GCD on the right temple.
FRAMES = {
    "F01": {"depth": 5.5, "edge_r": 2.4, "back_r": 1.0, "dome": 0.3,
            # a narrow bevel round each lens (drawing 01's double line, 0.6-0.85 mm out from the opening)
            "bezel": {"kind": "well", "width": 0.8, "p": 1.0, "round": 0.2, "seam": 0.12, "blend": 0.3,
                      "step": 0.0, "drop": 0.6},
            "lip_r": 0.0, "mesh_step": 1, "edge_floor": 0.18, "exact_distance": True,
            "lens": {"radius": 150.0, "thick": 1.6, "inset": 0.5},
            "tilt": 10.0,
            # small clear pads inside the rims at the lens centres' height (the inside shot), 11.8 mm apart
            # (the top view), just behind the bridge
            "pads": {"x": 7.1, "y": 2.0, "back": 2.5, "r": (1.2, 3.0, 2.0), "clear": True},
            "endpiece": {"kind": "block", "back": 6.5, "inset": 0.03, "flare": 0.6, "into": 2.0},
            "temple": {"kind": "acetate", "top_below": 17.9, "height": 12.0, "edge_r": 0.8,
                       "heights": [(0, 12.0), (73.5, 12.0), (78.5, 10.4), (82.5, 8.9), (85.5, 8.1), (90.5, 7.2),
                                   (95.5, 6.6), (100.5, 6.2), (110, 6.0), (122, 6.6), (129, 7.3), (136, 9.0),
                                   (142, 9.5), (150, 7.0)],
                       "thicks": [(0, 3.95), (15.5, 3.77), (35.5, 3.5), (55.5, 3.23), (75.5, 2.96), (105.5, 2.57),
                                  (125.5, 2.31), (139.5, 2.12), (150, 2.0)],
                       "straight": 73.5, "drop": 30.0,
                       # the mid-line beyond the straight run (mm back, mm down), side view
                       "tip_path": [(0, 0), (5, -0.6), (9, -1.26), (12, -1.58), (17, -1.85), (22, -1.88), (27, -1.68),
                                    (32, -1.19), (37, -0.17), (42, 1.52), (47, 4.15), (52, 8.3), (55, 12.7), (59, 16.2),
                                    (62, 18.1), (65, 20.1)]},
            "gcd": {"side": -1, "on": "temple"},
            "texture": "work/frames3d/F01"},
    "F02": {"depth": 6.5, "edge_r": 2.6, "back_r": 1.2, "dome": 0.7,
            "bezel": {"width": 3.2, "step": 0.8, "drop": 1.2, "bump": 0.3, "groove": 0.0, "groove_w": 0.5},
            "lip_r": 0.8, "mesh_step": 1, "edge_floor": 0.18, "exact_distance": True,
            "lens": {"radius": 150.0, "thick": 1.6, "inset": 0.9},
            "tilt": 10.0,
            "pads": {"x": 10.0, "y": -3.0, "back": 1.5, "r": (1.4, 4.5, 2.5)},     # tucked behind the rims (the front shot shows none)
            "endpiece": {"top": 1.0, "bottom": 13.0, "inset": 4.0},
            "hinge": {"down": 9.7, "back": 17.0},
            "temple": {"kind": "wire", "radius": 1.0, "straight": 95.0, "drop": 30.0},
            "texture": "work/frames3d/F02"},
    "F03": {"depth": 6.5, "edge_r": 2.6, "back_r": 1.2, "dome": 0.3,
            "bezel": {"kind": "well", "width": 3.2, "p": 1.0, "round": 0.3, "seam": 0.15, "blend": 0.6,
                      "step": 0.0, "drop": 1.2},
            "lip_r": 0.0, "mesh_step": 1, "edge_floor": 0.18, "exact_distance": True,
            "lens": {"radius": 150.0, "thick": 1.6, "inset": 0.9},
            "tilt": 10.0,
            "pads": {"x": 10.0, "y": -3.0, "back": 1.5, "r": (1.4, 4.5, 2.5)},
            "endpiece": {"kind": "block", "back": 8.2, "inset": 0.03, "flare": 1.2, "into": 2.0},
            "temple": {"kind": "acetate", "top_below": 3.7, "height": 9.0, "edge_r": 0.9,
                       "heights": [(0, 9.0), (80, 9.0), (90, 7.8), (95, 6.4), (100, 5.2), (110, 4.8), (150, 4.0)],
                       "thicks": [(0, 4.3), (20, 4.0), (40, 3.6), (60, 3.3), (90, 2.75), (120, 2.25), (150, 2.0)],
                       "straight": 80.0, "drop": 30.0,
                       # the mid-line beyond the straight run (mm back, mm down), side view
                       "tip_path": [(0, 0), (10, -0.5), (15, -1.0), (20, -1.3), (30, 0.1), (40, 4.4),
                                    (50, 11.4), (58, 14.3)]},
            "gcd": {"side": -1, "on": "temple"}},
    "F04": {"depth": 7.0, "edge_r": 1.8, "back_r": 1.0, "dome": 0.9,
            "bezel": {"width": 3.5, "step": 0.5, "drop": 1.3, "bump": 0.0, "groove": 0.0},
            "lip_r": 0.9, "mesh_step": 1, "edge_floor": 0.18, "exact_distance": True,
            "lens": {"radius": 260.0, "thick": 1.6, "inset": 1.4},
            "tilt": 0.0,
            "pads": {"x": 10.8, "y": -4.0, "back": 4.5, "r": (1.6, 5.0, 3.0)},
            "endpiece": {"metal": True, "proud": 0.03, "thick": 2.25, "overlap": 0.3, "bevel": 0.12,
                         "r_top": 0.3, "r_flat": 0.8, "r_bottom": 0.3,
                         "outline": {"base_top": (0.0, 0.0), "apex_top": (14.5, 7.06), "apex_bottom": (14.5, 9.93),
                                     "bottom_flat": (1.0, 15.25), "base_bottom": (0.0, 15.25)},
                         "hinge_barrel": {"r": 0.8, "in": 1.7, "behind": 0.7, "above": 0.35, "head_r": 0.6}},
            "temple": {"kind": "strip", "height": 2.9, "thick": 1.25, "straight": 75.0, "drop": 36.0,
                       "tip_from": 72.0, "tip": (3.0, 2.4), "tip_straight": 12.0,
                       # the acetate tip's mid-line from the joint (mm back, mm down), side view
                       "tip_path": [(0, 0), (3, 0.05), (13, 0.6), (21, 2.25), (27, 4.65), (33, 9.45),
                                    (43, 19.15), (53, 29.15), (59.5, 35.15)]},
            # where the cleaned shots set it (IMG_3456, tools/photo/temple_gcd.py): the side view's mm, the
            # emblem's centre and the hinge's (the wire's collar), on the face the end piece and the front's
            # side make
            "gcd": {"side": -1, "on": "endpiece", "hinge_mm": (25.0, 10.375), "centre_mm": (11.47, 10.59)}},
    "F05": {"depth": 7.5, "edge_r": 2.2, "back_r": 1.2, "dome": 0.9,
            "bezel": {"kind": "well", "width": 3.4, "p": 2.5, "seam": 0.15, "blend": 0.6, "step": 0.0, "drop": 1.8},
            "lip_r": 0.0, "mesh_step": 1, "edge_floor": 0.18, "exact_distance": True,
            "trim_tips": (58.0, 53.0),
            "lens": {"radius": 220.0, "thick": 1.6, "inset": 1.4},
            "tilt": 10.0,
            "pads": {"x": 10.0, "y": -5.0, "back": 3.5, "r": (1.6, 5.0, 3.0)},
            "endpiece": {"metal": True, "coated": True, "metal_rough": 0.34, "proud": 0.03, "thick": 2.0, "overlap": 3.7, "bevel": 0.12,
                         "r_top": 0.5, "r_topflat": 1.5, "r_flat": 0.6, "r_bottom": 0.5,
                         "outline": {"base_top": (0.0, 0.0), "top_flat": (4.9, 0.1), "apex_top": (18.0, 5.6),
                                     "apex_bottom": (17.5, 8.1), "bottom_flat": (4.6, 15.1), "base_bottom": (0.0, 15.1)},
                         "hinge_barrel": {"r": 0.8, "in": 1.7, "behind": 0.7, "above": 0.35, "head_r": 0.6}},
            "temple": {"kind": "strip", "height": 2.6, "thick": 1.3, "straight": 75.0, "drop": 30.0,
                       "tip_from": 74.0, "tip": (3.0, 2.2), "tip_straight": 12.0,
                       "tip_path": [(0, 0), (1, 0.03), (8, 0.46), (13, 0.94), (18, 1.63), (23, 2.58), (28, 3.85),
                                    (33, 5.65), (38, 8.35), (43, 12.63), (48, 17.9), (53, 22.78), (55, 24.0)]},
            # as the cleaned shots set it (IMG_3545, IMG_3547)
            "gcd": {"side": -1, "on": "endpiece", "hinge_mm": (27.4, 22.15), "centre_mm": (13.93, 22.45)}},
    "F06": {"depth": 5.5, "edge_r": 1.2, "back_r": 0.8, "dome": 0.15,
            "shield": True, "openings": "photo", "front_drop": {"x_within": 3.1, "y_below": 11.45},
            # the openings beside the nose, where the front shot sees the pads through the lens: the lower
            # level 2.3 mm wide inside the step, as round the rest (frame_texture.py --openings)
            "openings_pads": {"ring": 2.3, "below": 15.0, "half": 22.0},
            "bezel": {"kind": "terrace", "width": 0.0, "step": 0.8, "drop": 0.35},
            "lip_r": 0.5, "mesh_step": 1, "edge_floor": 0.18, "exact_distance": True,
            # the grey gradient, dark at the top: the cleaned front shot's transmission (linear) row by row
            # across the openings, at mm above the openings' centre (frame_texture.py's registration)
            "lens": {"radius": 1.0e5, "thick": 1.6, "inset": 0.5,
                     "gradient": [(22, (0.0161, 0.0141, 0.0218)), (18, (0.0178, 0.0138, 0.0264)),
                                  (14, (0.0240, 0.0181, 0.0369)), (10, (0.0349, 0.0280, 0.0512)),
                                  (6, (0.0508, 0.0433, 0.0691)), (2, (0.0716, 0.0643, 0.0915)),
                                  (-2, (0.0973, 0.0910, 0.1176)), (-6, (0.1282, 0.1230, 0.1477)),
                                  (-10, (0.1649, 0.1608, 0.1820)), (-14, (0.2079, 0.2051, 0.2205)),
                                  (-18, (0.2577, 0.2564, 0.2653)), (-22, (0.2917, 0.2918, 0.2974))]},
            "tilt": 7.0,
            # smoky acetate pads: dark seen along their length from above (the top shot), a grey that light
            # passes through from the front (the hero shot, through the lens)
            "pads": {"x": 12.3, "y": -6.0, "back": 5.6, "r": (2.0, 9.5, 3.5), "clear": True, "smoke": 0.35},
            "endpiece": {"kind": "block", "back": 6.0, "inset": 0.03, "flare": 0.0, "into": 2.0},
            "temple": {"kind": "acetate", "top_below": 1.2, "height": 9.65, "edge_r": 0.9,
                       "heights": [(0, 9.7), (90.7, 9.65), (92.7, 9.5), (94.7, 9.15), (96.7, 8.7), (98.7, 8.2),
                                   (100.7, 7.65), (102.7, 7.0), (104.7, 6.5), (106.7, 5.95), (108.7, 5.5),
                                   (110.7, 5.2), (112.7, 4.95), (116.8, 4.95), (120.5, 5.4), (123.2, 5.7),
                                   (128.8, 6.6), (134.9, 7.9), (141.2, 9.7), (144.2, 10.5), (147.0, 10.5),
                                   (149.6, 9.0), (152.1, 5.7)],
                       "thicks": [(0, 2.85), (76, 2.85), (86, 2.8), (96, 2.7), (106, 2.45), (116, 2.25),
                                  (126, 1.95), (136, 1.7), (152, 1.4)],
                       "straight": 90.7, "drop": 30.0,
                       # the mid-line beyond the straight run (mm back, mm down), side view
                       "tip_path": [(0, 0), (2, -0.07), (4, -0.22), (6, -0.45), (8, -0.7), (10, -0.92), (12, -1.15),
                                    (14, -1.32), (17, -1.45), (20, -1.37), (22, -1.17), (27, -0.07), (32, 1.75),
                                    (37, 4.33), (42, 7.48), (47, 11.4), (52, 14.58), (55, 15.4), (57, 15.6)]},
            "gcd": {"side": -1, "on": "temple"}},
    "F08": {"depth": 4.3, "edge_r": 1.0, "back_r": 0.6, "dome": 0.2,
            # the keyhole between the brow and the lower bridge (the double bridge), cut through the front
            "holes": [(0.0, 18.0)],
            # the ring round each lens (drawing 08's double line, 1.4-1.6 mm out from the opening): the face
            # rounding down into the lens, its lip catching a line of light along the lens's edge
            "bezel": {"kind": "well", "width": 1.5, "p": 2.0, "seam": 0.12, "blend": 0.3, "step": 0.0, "drop": 1.0},
            "lip_r": 0.0, "mesh_step": 1, "edge_floor": 0.18, "exact_distance": True,
            # the grey gradient, dark and a little blue at the top: the cleaned front shot's transmission
            # (linear) row by row across the openings, at mm above the openings' centre
            "lens": {"radius": 180.0, "thick": 1.6, "inset": 0.4,
                     "gradient": [(20.5, (0.0165, 0.0134, 0.0250)), (18, (0.0292, 0.0260, 0.0418)),
                                  (15, (0.0443, 0.0407, 0.0603)), (12, (0.0600, 0.0561, 0.0787)),
                                  (9, (0.0794, 0.0767, 0.0986)), (6, (0.1002, 0.0976, 0.1222)),
                                  (3, (0.1228, 0.1204, 0.1471)), (0, (0.1494, 0.1472, 0.1733)),
                                  (-3, (0.1790, 0.1779, 0.2026)), (-6, (0.2120, 0.2118, 0.2340)),
                                  (-9, (0.2476, 0.2481, 0.2667)), (-12, (0.2862, 0.2878, 0.3022)),
                                  (-15, (0.3269, 0.3303, 0.3391)), (-18, (0.3708, 0.3763, 0.3777)),
                                  (-20, (0.4006, 0.4071, 0.4041))]},
            "tilt": 8.0,
            # black acetate fins standing back from the rims beside the nose opening, just under the lower
            # bridge (the top shot: two sculpted fins behind the bridge, one either side of it; the back view:
            # their ends at the opening's top corners)
            "pads": {"x": 9.5, "y": -2.0, "back": 4.0, "r": (1.5, 6.5, 4.5)},
            "endpiece": {"kind": "block", "back": 5.0, "inset": 0.03, "flare": 0.0, "into": 2.0},
            "temple": {"kind": "acetate", "top_below": 16.55, "height": 10.75, "edge_r": 1.4,
                       "heights": [(0, 10.75), (2.8, 10.75), (7.8, 10.65), (12.8, 10.55), (22.8, 10.25), (32.8, 10.1),
                                   (42.8, 10.0), (52.8, 10.25), (57.8, 10.6), (62.8, 11.1), (67.8, 11.9), (70.8, 12.6),
                                   (72.8, 13.15), (74.8, 13.2), (77.8, 12.6), (82.8, 10.75), (87.8, 8.7), (92.8, 7.1),
                                   (97.8, 6.0), (102.8, 5.5), (106.8, 5.43), (108.8, 5.54), (110.8, 5.71), (112.8, 5.95),
                                   (117.0, 6.62), (121.3, 7.19), (125.8, 7.54), (130.4, 7.94), (135.2, 8.31),
                                   (140.0, 8.64), (144.9, 8.96), (149.8, 9.27), (152.2, 9.43), (155.2, 9.4)],
                       # the section's centre below the straight run (mm): the bottom edge's wave, the top edge
                       # straight (side view)
                       "offsets": [(0, 0.0), (12.8, 0.1), (22.8, 0.2), (32.8, 0.32), (42.8, 0.52), (52.8, 0.85),
                                   (57.8, 1.12), (62.8, 1.52), (67.8, 2.02), (70.8, 2.42), (72.8, 2.75), (74.8, 2.82),
                                   (77.8, 2.57), (82.8, 1.75), (87.8, 0.87), (92.8, 0.17), (97.8, -0.28), (100.8, -0.4),
                                   (104.8, -0.425), (108.8, -0.225), (110.8, 0.0)],
                       "thicks": [(0, 3.9), (3, 3.89), (8, 3.84), (13, 3.8), (23, 3.64), (33, 3.54), (43, 3.39),
                                  (53, 3.3), (63, 3.14), (73, 3.04), (83, 2.91), (93, 2.8), (103, 2.7), (113, 2.57),
                                  (124, 2.43), (135, 2.36), (147, 2.23), (153, 2.17), (157, 2.13)],
                       "straight": 110.8, "drop": 25.0, "round_end": 4.5,
                       # the mid-line beyond the straight run (mm back, mm down), side view
                       "tip_path": [(0, 0), (2, 0.33), (4, 0.85), (6, 1.5), (8, 2.28), (10, 3.16), (12, 4.13),
                                    (14, 5.18), (16, 6.31), (18, 7.5), (20, 8.75), (22, 10.06), (24, 11.35),
                                    (26, 12.7), (28, 14.08), (30, 15.48), (32, 16.88), (34, 18.31), (36, 19.7),
                                    (38, 21.0)],
                       # translucent smoke grey acetate (what passing through it lets by: the backdrop behind a
                       # temple shows at 0.20-0.25 of its light in the three-quarter shots), round a textured
                       # metal core (the shots: 45% of the temple's height, the hinge's leaf at the joint taller;
                       # it ends 88 mm back, its bottom edge rising to its top)
                       "smoke": (0.19, 0.18, 0.187),
                       "core": {"heights": [(0, 6.4), (6.0, 6.4), (8.0, 4.6), (82.0, 4.6), (88.0, 0.3)],
                                "ups": [(0, 0.0), (82.0, 0.0), (88.0, 2.15)],
                                "thick": 0.6, "from": 0.3, "to": 88.0}},
            "gcd": {"side": -1, "on": "temple"}},
}


# ---------- reading the drawings ----------
def render_view(frame, view, ppm=20):
    import cairosvg
    svg = (DRAW / f"{frame}-{view}.svg").read_text()
    svg = svg.replace("currentColor", "#000").replace('stroke-width="0.25"', 'stroke-width="0.06"')
    svg = svg.replace('vector-effect="non-scaling-stroke"', "")
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    drop = FRAMES.get(frame, {}).get("front_drop") if view == "front" else None
    if drop:
        # the temples' tips, which the front view draws hanging below the front's ends (F06): every line
        # wholly below `y_below` mm and within `x_within` mm of either side of the drawing left out
        def keep(m):
            pts = np.array([(float(a), float(b)) for a, b in re.findall(r"([-\d.]+)[ ,]([-\d.]+)", m.group(1))])
            if not len(pts):
                return True
            low = pts[:, 1].min() >= drop["y_below"]
            side = pts[:, 0].max() <= vb[0] + drop["x_within"] or pts[:, 0].min() >= vb[0] + vb[2] - drop["x_within"]
            return not (low and side)
        svg = re.sub(r'<path[^>]* d="([^"]+)"[^>]*/>', lambda m: m.group(0) if keep(m) else "", svg)
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=int(vb[2] * ppm), output_height=int(vb[3] * ppm),
                           background_color="white")
    return cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_GRAYSCALE), ppm


def front_shapes(frame, ppm=20):
    """The front view's outline and lens openings as polygons in mm (origin midway between the two
    lens-box centres, x right as drawn, y up)."""
    from scipy import ndimage as ndi
    cfg = FRAMES.get(frame, {})
    im, ppm = render_view(frame, "front", ppm)
    free = 1 - cv2.dilate((im < 200).astype(np.uint8), np.ones((3, 3), np.uint8))
    lab, n = ndi.label(free)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    sizes = ndi.sum(np.ones_like(lab), lab, range(1, n + 1))
    inner = [(sizes[i - 1], i) for i in range(1, n + 1) if i not in border]
    step = None
    if cfg.get("shield"):
        # one region inside the drawing's lines (F06): the step round the whole shield, one line from end
        # to end over the brow; the openings are the photograph's (below)
        # (the drawing's centre line, down from the top to the nose, halves it: the two halves rejoined)
        halves = [lab == i for _, i in sorted(inner, reverse=True)[:2]]
        step = cv2.morphologyEx((halves[0] | halves[1]).astype(np.uint8), cv2.MORPH_CLOSE,
                                cv2.getStructuringElement(cv2.MORPH_RECT, (int(0.3 * ppm) | 1, 1))) > 0
        lens_masks = [step]
    else:
        lenses = [i for _, i in sorted(inner, reverse=True)[:2]]
        lens_masks = sorted([lab == i for i in lenses], key=lambda m: np.nonzero(m)[1].mean())
    if cfg.get("openings") == "photo":
        # the lens openings as the cleaned front shot shows them, registered to the drawing
        # (frame_texture.py --openings): F06's front has a bridge down from the brow between two openings,
        # where the drawing's front view draws only the step round one shield
        f = ROOT / "work" / "frames3d" / frame / "openings.png"
        if f.exists():
            op = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
            if op.shape != im.shape:
                op = cv2.resize(op, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_AREA)
            k_, lab2, st2, _ = cv2.connectedComponentsWithStats((op > 127).astype(np.uint8))
            big = 1 + np.argsort(-st2[1:, cv2.CC_STAT_AREA])[:2]
            lens_masks = sorted([lab2 == i for i in big], key=lambda m: np.nonzero(m)[1].mean())
        else:
            print(f"{frame}: no {f}; the drawing's region stands in for the openings")
    # everything inside the outermost line: closed over the drawing's narrow double lines first (a bevel
    # line close beside the edge left a slit open to the outside, and the front got a groove along it)
    ink = cv2.morphologyEx((im < 200).astype(np.uint8), cv2.MORPH_CLOSE,
                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(0.8 * ppm) | 1,) * 2))
    silhouette = ndi.binary_fill_holes(ink > 0)
    centres = []
    for m in lens_masks:
        ys, xs = np.nonzero(m)
        centres.append(((xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2))
    ox, oy = np.mean(centres, axis=0)
    # holes through the front where the drawing draws them (F08's keyhole between the brow and the lower
    # bridge): the region inside the drawing's lines at each point given (mm, the frame's coordinates)
    holes = []
    for hx, hy in cfg.get("holes", []):
        px, py = int(round(ox + hx * ppm)), int(round(oy - hy * ppm))
        i = lab[py, px]
        if i == 0 or i in border:
            raise ValueError(f"{frame}: no region inside the drawing's lines at ({hx}, {hy}) mm")
        holes.append(cv2.dilate((lab == i).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
    trim = FRAMES.get(frame, {}).get("trim_tips")
    if trim:
        # the temples' acetate tips, hanging behind the ears, show below the front at its outer ends in
        # the front view: not the front. Between |x| = trim[0] and trim[1] mm its bottom edge runs straight
        # from the edge's height at one to the other
        for side in (-1, 1):
            xa, xb = (int(round(ox + side * v * ppm)) for v in trim)
            lo, hi = min(xa, xb), max(xa, xb)
            ya, yb = (int(np.nonzero(silhouette[:, x])[0].max()) for x in (xa, xb))
            for x in range(lo, hi + 1):
                yl = ya + (yb - ya) * (x - xa) / (xb - xa)
                silhouette[int(np.ceil(yl)) + 1:, x] = False

    def poly(mask, grow_px=0):
        m = mask.astype(np.uint8)
        if grow_px:
            m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow_px + 1,) * 2))
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cs, key=cv2.contourArea)[:, 0, :].astype(np.float64)
        c = cv2.approxPolyDP(c.astype(np.float32), 0.6, True)[:, 0, :].astype(np.float64)
        return np.stack([(c[:, 0] - ox) / ppm, (oy - c[:, 1]) / ppm], 1)

    openings = np.zeros_like(silhouette)
    for m in lens_masks:
        openings |= cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    for m in holes:
        silhouette = silhouette & ~m
    if step is not None:
        # one lens behind both openings: the shield, out to the step line less 0.3 mm (its edge inside the
        # front, under the lower level and the bridge)
        shells = [cv2.erode(step.astype(np.uint8), cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (int(0.3 * ppm) * 2 + 1,) * 2)) > 0]
    else:
        shells = [cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (int(1.2 * ppm) * 2 + 1,) * 2)) > 0 for m in lens_masks]
    return {"outline": poly(silhouette), "openings": [poly(m, 1) for m in lens_masks],
            "opening_masks": [cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0 for m in lens_masks],
            "lenses": [poly(m, int(1.0 * ppm)) for m in (shells if step is not None else lens_masks)],
            "width": float(np.ptp(np.nonzero(silhouette)[1]) / ppm),
            "solid": silhouette & ~openings, "lens_masks": shells, "step_mask": step, "holes": holes,
            "origin_px": (ox, oy), "ppm": ppm}


def wrap_profile(frame, ppm=20):
    """How far the front's face falls back from its most forward point, as a function of x (mm), from
    the top view: the lowest drawn line in the front's band is its face."""
    im, ppm = render_view(frame, "top", ppm)
    ink = im < 200
    H, W = ink.shape
    band = ink[H - 25 * ppm:]
    cols = np.nonzero(band.any(0))[0]
    x0, x1 = cols.min(), cols.max()
    xs = np.arange(x0, x1 + 1, ppm // 2)
    z = np.array([np.nonzero(band[:, x])[0].max() for x in xs], np.float64) / ppm
    xm = (xs - (x0 + x1) / 2) / ppm
    from scipy.ndimage import gaussian_filter1d, median_filter
    # the drawn line is a staircase of pixels: median, then a 3 mm Gaussian, so the front's face bends
    # smoothly (its steps had shown as streaks in the gloss)
    z = gaussian_filter1d(median_filter(z, 5, mode="nearest"), 3.0 / (xs[1] - xs[0]) * ppm, mode="nearest")
    z = z - z.max()                                   # 0 at the most forward point, negative behind
    return xm, z


# ---------- building in Blender ----------
def to_mesh(ob):
    """A curve object as a mesh object (same name, same place)."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    new = bpy.data.objects.new(ob.name, me)
    bpy.context.scene.collection.objects.link(new)
    new.matrix_world = ob.matrix_world
    bpy.data.objects.remove(ob)
    return new


def field_mesh(name, mask, zf, zb, origin_px, ppm, step=1):
    """A solid over the mask's outline whose front face is the height field `zf` and whose back face is
    `zb` (mm, z towards the viewer), joined round its edges by a wall: dense and even, so it shades
    smoothly and takes the wrap without creasing; the edge's pixel steps smoothed away."""
    m = mask[::step, ::step].astype(np.uint8)
    zf, zb = zf[::step, ::step], zb[::step, ::step]
    ys, xs = np.nonzero(m)
    idx = -np.ones(m.shape, np.int64)
    idx[ys, xs] = np.arange(len(xs))
    X = (xs * step - origin_px[0]) / ppm
    Y = (origin_px[1] - ys * step) / ppm
    n = len(xs)
    a_ = idx[:-1, :-1]; b_ = idx[:-1, 1:]; c_ = idx[1:, 1:]; d_ = idx[1:, :-1]
    ok = (a_ >= 0) & (b_ >= 0) & (c_ >= 0) & (d_ >= 0)
    q = np.stack([a_[ok], d_[ok], c_[ok], b_[ok]], 1)                 # counter-clockwise seen from the front (y up)
    front = q
    back = q[:, ::-1] + n
    e = np.concatenate([q[:, [0, 1]], q[:, [1, 2]], q[:, [2, 3]], q[:, [3, 0]]])
    key = np.sort(e, 1)
    uniq, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    edge = e[cnt[inv.ravel()] == 1]
    side = np.stack([edge[:, 1], edge[:, 0], edge[:, 0] + n, edge[:, 1] + n], 1)
    bv = np.unique(edge)
    P = np.stack([X, Y], 1)
    nb = {}
    for a1, b1 in edge:
        nb.setdefault(a1, []).append(b1)
        nb.setdefault(b1, []).append(a1)
    # the outline's pixel steps smoothed (Taubin: a shrinking step, then a growing one, so curves keep
    # their size); the walls' facets then turn evenly round it
    nbl = {v: np.asarray(nb[v]) for v in bv}
    bvl = np.asarray(list(bv))
    for _ in range(40):
        for lam in (0.5, -0.53):
            avg = np.stack([P[nbl[v]].mean(0) for v in bvl])
            P[bvl] = P[bvl] + lam * (avg - P[bvl])
    # Taubin passes long waves untouched, and along a nearly level or upright stretch of outline the
    # pixel steps come a millimetre or more apart: the edge stayed stepped. Each closed loop also
    # smoothed along itself, as its walls' normals are (and as the heights' distances measure it); no
    # vertex moved more than `cap` px, so a corner never folds over the row inside
    from scipy.ndimage import gaussian_filter1d
    cap = 0.6 * step / ppm
    for L in outline_loops(nbl):
        if len(L) < 12 or int(L[0]) not in set(nbl[int(L[-1])].tolist()):
            continue
        pts = P[L]
        spacing = float(np.median(np.linalg.norm(np.diff(pts, axis=0), axis=1)))
        sm = np.stack([gaussian_filter1d(pts[:, i], max(0.6 / max(spacing, 1e-6), 1.0), mode="wrap")
                       for i in range(2)], 1)
        mv = sm - pts
        ln = np.linalg.norm(mv, axis=1, keepdims=True)
        P[L] = pts + mv * np.minimum(1.0, cap / np.maximum(ln, 1e-9))
    V = np.concatenate([np.stack([P[:, 0], P[:, 1], zf[ys, xs]], 1), np.stack([P[:, 0], P[:, 1], zb[ys, xs]], 1)]) * MM
    F = np.concatenate([front, back, side])
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.ravel())
    me.loops.add(F.size)
    me.loops.foreach_set("vertex_index", F.ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set("loop_start", np.arange(0, F.size, 4))
    me.polygons.foreach_set("loop_total", np.full(len(F), 4))
    me.update(calc_edges=True)
    me.validate()
    # smooth shading, with the walls' rims sharp: a wall shades smooth along the outline but is never
    # swept to the face's or the back's normal across its height (that mirrored the room as bands on
    # the walls in a three-quarter view)
    me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
    ev = np.zeros(len(me.edges) * 2, np.int64)
    me.edges.foreach_get("vertices", ev)
    ev = np.sort(ev.reshape(-1, 2), 1)
    rim = np.sort(np.concatenate([edge, edge + n]), 1)
    sharp = (np.isin(ev[:, 0] * (2 * n + 1) + ev[:, 1], rim[:, 0] * (2 * n + 1) + rim[:, 1]))
    attr = me.attributes.get("sharp_edge") or me.attributes.new("sharp_edge", "BOOLEAN", "EDGE")
    attr.data.foreach_set("value", sharp)
    # the walls' normals square to the outline smoothed along itself: even smoothed, the outline keeps
    # traces of its pixel steps, and the face's and back's heights wander along it, so the wall's facets
    # twisted and banded the gloss across the frame's outer sides and top (a polished part has none)
    def inside(Q):
        c = np.clip(np.round((Q[:, 0] * ppm + origin_px[0]) / step).astype(int), 0, m.shape[1] - 1)
        r = np.clip(np.round((origin_px[1] - Q[:, 1] * ppm) / step).astype(int), 0, m.shape[0] - 1)
        return m[r, c] > 0
    WN = wall_normals(P, nbl, inside)
    me.update()
    cn = np.zeros(len(me.loops) * 3)
    me.corner_normals.foreach_get("vector", cn)
    cn = cn.reshape(-1, 3)
    lv = np.zeros(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", lv)
    ls = np.zeros(len(me.polygons), np.int64)
    lt = np.zeros(len(me.polygons), np.int64)
    me.polygons.foreach_get("loop_start", ls)
    me.polygons.foreach_get("loop_total", lt)
    pv = lv[ls[:, None] + np.arange(4)[None, :]] if (lt == 4).all() else None
    if pv is not None:
        wall = (pv.min(1) < n) & (pv.max(1) >= n)
        for pi in np.nonzero(wall)[0]:
            for j in range(4):
                v = int(lv[ls[pi] + j]) % n
                w = WN.get(v)
                if w is not None:
                    cn[ls[pi] + j] = (w[0], w[1], 0.0)
        me.normals_split_custom_set(cn.tolist())
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def outline_loops(nbl):
    """An outline's vertices (`nbl`: each one's neighbours along it) as loops, each walked in order."""
    left = set(int(v) for v in nbl)
    loops = []
    while left:
        v0 = left.pop()
        loop, prev, cur = [v0], None, v0
        while True:
            cands = [int(w) for w in nbl[cur] if int(w) != prev and int(w) in left]
            if not cands:
                break
            prev, cur = cur, cands[0]
            left.discard(cur)
            loop.append(cur)
        loops.append(np.asarray(loop))
    return loops


def wall_normals(P, nbl, inside, sigma_mm=0.6):
    """Outward normals (2D, unit) at an outline's vertices: each closed loop walked in order, smoothed
    along itself (Gaussian, sigma_mm), its tangents turned outward (tested with `inside`)."""
    from scipy.ndimage import gaussian_filter1d
    N = {}
    for L in outline_loops(nbl):
        if len(L) < 12:
            continue
        pts = P[L]
        spacing = float(np.median(np.linalg.norm(np.diff(pts, axis=0), axis=1)))
        sig = max(sigma_mm / max(spacing, 1e-6), 1.0)
        sm = np.stack([gaussian_filter1d(pts[:, i], sig, mode="wrap") for i in range(2)], 1)
        t = np.roll(sm, -1, 0) - np.roll(sm, 1, 0)
        t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-12
        nn = np.stack([t[:, 1], -t[:, 0]], 1)
        if inside(sm + nn * 0.25).mean() > 0.5:
            nn = -nn
        for v, w in zip(L, nn):
            N[int(v)] = w
    return N


def rounded(d, r):
    """A quarter circle of radius r: 0 at d = 0 rising to r at d >= r (the height a rounded edge has
    gained d mm in from the edge)."""
    t = np.clip(d, 0, r)
    return np.sqrt(np.maximum(r * r - (r - t) ** 2, 0))


def curve_distance(region, shape, d_edt, ppm, near_mm=6.0, sigma_px=4.0):
    """Distance (mm) from the pixels of `region` to the outline of `shape` smoothed into curves, for
    pixels within `near_mm` of it (the rest keep the pixel distance `d_edt`, smooth enough that far in):
    the outline traced at pixel level, each contour smoothed along itself, densified, then the nearest
    point."""
    from scipy.ndimage import gaussian_filter1d
    from scipy.spatial import cKDTree
    cs, _ = cv2.findContours(shape.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    pts = []
    for c in cs:
        c = c[:, 0, :].astype(np.float64)
        if len(c) < 30:
            continue
        c = np.stack([gaussian_filter1d(c[:, 0], sigma_px, mode="wrap"), gaussian_filter1d(c[:, 1], sigma_px, mode="wrap")], 1)
        seg = np.diff(np.vstack([c, c[:1]]), axis=0)
        n = np.maximum(1, np.ceil(np.linalg.norm(seg, axis=1) / 0.25)).astype(int)
        pts.append(np.concatenate([c[i] + seg[i] * np.linspace(0, 1, n[i], endpoint=False)[:, None]
                                   for i in range(len(c))]))
    tree = cKDTree(np.concatenate(pts))
    ys, xs = np.nonzero(region & (d_edt < near_mm))
    dist, _ = tree.query(np.stack([xs, ys], 1).astype(np.float64), workers=-1)
    out = d_edt.copy()
    # a boundary pixel's centre is half a pixel inside the edge (as the pixel distance has it)
    out[ys, xs] = (dist + 0.5) / ppm
    # blend into the pixel distance over the last mm, so there is no seam where the two meet
    w = np.clip((near_mm - out[ys, xs]) / 1.0, 0, 1)
    out[ys, xs] = w * out[ys, xs] + (1 - w) * d_edt[ys, xs]
    return out


def rim_fields(sh, cfg):
    """The front's face and back as height fields over the front view (mm; z = 0 mid-thickness): the
    face rounded at the outer edge, stepping down to the ring round each lens and rounding into the
    lens (bezel kind "well": no ring, the face sweeping down into each lens in one smooth curve); the
    back flat, its edges rounded."""
    from scipy import ndimage as ndi
    ppm = sh["ppm"]
    solid = sh["solid"]
    openings = np.zeros_like(solid)
    for m in sh["opening_masks"]:
        openings |= m
    sil = ndi.binary_fill_holes(solid | openings)
    for m in sh.get("holes", []):
        sil &= ~m                                         # a hole's edge is an outer edge (F08's keyhole)
    d_out = ndi.distance_transform_edt(sil) / ppm
    d_in = ndi.distance_transform_edt(~openings) / ppm
    if cfg.get("exact_distance"):
        # the distance to a pixel outline is scalloped along a near-vertical or near-level edge (the
        # nearest outline pixel jumps at each step of the staircase): a rounded edge read off it came
        # out terraced. Near the outlines, measure to the outlines smoothed into curves instead
        d_out = curve_distance(sil, sil, d_out, ppm)
        # the openings' outlines smoothed as their walls are (0.6 mm): at 0.2 mm, the steps along their
        # nearly level stretches, a millimetre apart, still waved every height read off the distance, and
        # the slope into each lens mirrored the lens's rim as a row of scallops (F05)
        d_in = curve_distance(sil & ~openings, openings, d_in, ppm, sigma_px=0.6 * ppm)
    T = cfg["depth"]
    r = cfg["edge_r"]
    # the roundings meet the walls vertically, so right at an edge the height changes fastest: read
    # there, the outline's pixel steps became a sawtooth along the edge (0.05 mm, every few vertices)
    # that streaked the gloss; from `edge_floor` mm in, the height runs level along every edge
    f = cfg.get("edge_floor", 0.0)
    d_out_e, d_in_e = np.maximum(d_out, f), np.maximum(d_in, f)
    z_out = T / 2 - r + rounded(d_out_e, r)
    bz = cfg["bezel"]
    w, st, dr, lr = bz["width"], bz["step"], bz["drop"], cfg["lip_r"]
    rb = cfg["back_r"]

    # a polished part has no creases: the distance fields kink along the middle of every band (the
    # bridge's centre, each rim's midline), which showed as lines in the gloss; smoothed out within
    # the front (a blur that takes nothing from outside it)
    def smooth(z, sig_mm):
        m = solid.astype(np.float64)
        return ndi.gaussian_filter(z * m, sig_mm * ppm) / np.maximum(ndi.gaussian_filter(m, sig_mm * ppm), 1e-6)

    if bz.get("kind") == "terrace":
        # F06 (drawing 06 and its cleaned shots): the face is a band round the outside, `drop` mm proud of
        # a lower level inside the drawing's step line, one line round the whole shield and straight across
        # the brow; the lower level runs round both openings and is the bridge between them. The step is a
        # smooth rise `step` mm wide (its rounded top catches the faint line the front shot shows); the
        # lower level rounds into each opening (lip_r)
        stp = sh["step_mask"]
        d_si = ndi.distance_transform_edt(stp) / ppm
        d_so = ndi.distance_transform_edt(~stp) / ppm
        if cfg.get("exact_distance"):
            d_si = curve_distance(stp & sil, stp, d_si, ppm, sigma_px=0.6 * ppm)
            d_so = curve_distance(sil & ~stp, ~stp & sil, d_so, ppm, sigma_px=0.6 * ppm)
        sd = np.where(stp, -d_si, d_so)                    # mm from the step line, + towards the outer edge
        u = np.clip(sd / st + 0.5, 0, 1)
        u = u * u * (3 - 2 * u)
        # the face domed a little across its band, highest midway between the outer edge and the step
        tb = np.clip(d_out / np.maximum(d_out + np.maximum(sd, 0), 1e-3), 0, 1)
        face = T / 2 - cfg.get("dome", 0.0) * (1 - np.sin(np.pi * tb))
        zo = face - r + rounded(d_out_e, r)
        z_low = T / 2 - dr
        z = z_low + (zo - z_low) * u
        z_lip = np.where(d_in_e < lr, z_low - lr + rounded(d_in_e, lr), np.inf)
        zf = np.minimum(np.minimum(z, zo), z_lip)
        zb = -(T / 2 - rb) - rounded(np.minimum(d_out_e, d_in_e), rb)
        near = np.minimum(d_out, d_in)
        wgt = np.clip((near - 0.4) / 0.8, 0, 1)
        return wgt * smooth(zf, 0.3) + (1 - wgt) * zf, wgt * smooth(zb, 0.3) + (1 - wgt) * zb

    if bz.get("kind") == "well":
        # the face and the lens wells as one smooth surface (F05, the founder's desk shots of Oct 25 2026:
        # no ring, no wall, no crease anywhere between the face and the lens). The face is a low dome
        # across the rim; at the outer edge it rounds over (edge_r); towards each opening it sweeps down,
        # one convex curve `width` mm wide, to a hair (`seam`) above the lens's own edge, which meets it
        # with only that seam's dark line. The parts meet through a smooth minimum: a plain minimum
        # creased wherever two of them crossed, and every crease drew its own line in the gloss.
        W_ = bz["width"]
        seam = bz.get("seam", 0.15)
        # the lens's front under every point of the rim (its sphere carried on past its edge), the
        # nearer lens's
        lf = [lens_fields(sh, cfg, i)[0] for i in range(len(sh["opening_masks"]))]
        dd = [ndi.distance_transform_edt(~m) for m in sh["opening_masks"]]
        zl = np.where(dd[0] <= dd[1], lf[0], lf[1]) if len(lf) > 1 else lf[0]
        tb = np.clip(d_out / np.maximum(d_out + d_in, 1e-3), 0, 1)
        face = T / 2 - cfg.get("dome", 0.0) * (1 - np.sin(np.pi * tb))
        zo = face - r + rounded(d_out_e, r)
        # the sweep starts `edge_floor` mm out from the opening, level up to there (as the outer edge
        # does): right at the opening it is at its steepest, and the edge row's heights, read at the
        # pixel steps, would run in a sawtooth along the lens's edge
        ti = np.clip((d_in - f) / max(W_ - f, 1e-3), 0, None)
        if bz.get("p", 2.0) == 1.0:
            # a straight bevel (F03): a chamfer from the lens up to the face, meeting it at a defined
            # edge, rounded over `round` mm either side (a parabola: the slope runs down to the face's in
            # that width, no kink)
            rho = bz.get("round", 0.3) / max(W_ - f, 1e-3)
            g = np.where(ti < 1 - rho, ti, np.where(ti < 1 + rho, ti - (ti - (1 - rho)) ** 2 / (4 * rho), 1.0))
        else:
            g = 1 - (1 - np.clip(ti, 0, 1)) ** bz.get("p", 2.0)
        zi = zl + seam + (face - zl - seam) * g
        k = bz.get("blend", 0.6)
        h = np.clip(k - np.abs(zo - zi), 0, None) / k
        zf = np.minimum(zo, zi) - h * h * k / 4
        zb = -(T / 2 - rb) - rounded(np.minimum(d_out_e, d_in_e), rb)
        # the blur only away from the edges: along the outer edge the heights stay as the distances give
        # them, and down in each well's foot as the sweep gives them (the blur, taking nothing from the
        # opening, lifted the foot off the lens and turned its last mm concave)
        wo = np.clip((d_out - 0.4) / 0.8, 0, 1) * np.clip((d_in - 0.5) / 1.0, 0, 1)
        wb = np.clip((np.minimum(d_out, d_in) - 0.4) / 0.8, 0, 1)
        return wo * smooth(zf, bz.get("smooth_mm", 0.35)) + (1 - wo) * zf, wb * smooth(zb, 0.3) + (1 - wb) * zb

    # the ring: up from the lens groove round the lip, a low rounded band, then the step's shoulder up
    # to the front's face
    u = np.clip((d_in - (w - st / 2)) / st, 0, 1)
    z_in = T / 2 - dr * (1 - u * u * (3 - 2 * u))
    band = np.clip((d_in - lr) / max(w - st / 2 - lr, 1e-3), 0, 1)
    z_in = z_in + bz.get("bump", 0.0) * np.sin(np.pi * band) * (d_in < w)
    z_in = z_in - bz.get("groove", 0.0) * np.exp(-((d_in - w) / bz.get("groove_w", 0.45)) ** 2)
    # the lip only within its radius of the opening: run on past it at the ring's height, it capped
    # the whole face at the ring (every front came out flat, the step, the dome and the rounded outer
    # edge all under that cap: F05's puffy front read as a cut-out with no gloss along its edges)
    z_lip = np.where(d_in_e < lr, T / 2 - dr - lr + rounded(d_in_e, lr), np.inf)
    d_step = np.maximum(d_in - (w + st / 2), 0)
    # the face itself domed across the rim (a pillow, not a plate): highest midway between the outer
    # edge and the ring's step
    t = d_out / np.maximum(d_out + d_step, 1e-3)
    z_dome = T / 2 - cfg.get("dome", 0.0) * (1 - np.sin(np.pi * np.clip(t, 0, 1)) ** 0.5)
    zf = np.minimum(np.minimum(np.minimum(z_out, z_in), z_lip), z_dome)
    zb = -(T / 2 - rb) - rounded(np.minimum(d_out_e, d_in_e), rb)
    if not f:
        return smooth(zf, 0.5), smooth(zb, 0.3)
    # near an edge the blur's window is cut by the outline's steps and its average with them: there
    # the heights stay as the (even) distances give them; the blur takes over from 0.4 mm in
    near = np.minimum(d_out, d_in)
    wgt = np.clip((near - 0.4) / 0.8, 0, 1)
    return wgt * smooth(zf, 0.5) + (1 - wgt) * zf, wgt * smooth(zb, 0.3) + (1 - wgt) * zb


def lens_fields(sh, cfg, i):
    """Lens i as a thin spherical shell set in the front: its front face curved to the base curve
    about the lens box's centre, its edge `inset` mm behind the ring."""
    ppm = sh["ppm"]
    m = sh["lens_masks"][i]
    # a shield (one lens behind both openings) curves about its own centre
    ys, xs = np.nonzero(sh["opening_masks"][i] if sh.get("step_mask") is None else m)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    H, W = m.shape
    yy, xx = np.mgrid[0:H, 0:W]
    rr = ((xx - cx) ** 2 + (yy - cy) ** 2) / ppm ** 2
    R = cfg["lens"]["radius"]
    half = max(np.ptp(xs), np.ptp(ys)) / 2 / ppm
    edge_sag = half ** 2 / (2 * R)
    z_edge = cfg["depth"] / 2 - cfg["bezel"]["drop"] - cfg["lip_r"] - cfg["lens"]["inset"]
    zf = z_edge + edge_sag - rr / (2 * R)
    zb = zf - cfg["lens"]["thick"]
    return zf, zb


def bend(ob, xm, z, z_shift=0.0):
    """Apply the wrap: every vertex falls back by the profile's z at its x (both mm tables)."""
    me = ob.data
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    co[:, 2] += (np.interp(co[:, 0] / MM, xm, z) + z_shift) * MM
    me.vertices.foreach_set("co", co.ravel())
    me.update()


def loft(name, rings, material=None, cap=True):
    """A closed solid through a list of rings (each a list of 3D points in mm, the same count)."""
    rings = [np.asarray(r, np.float64) for r in rings]
    k = len(rings[0])
    V = np.concatenate(rings) * MM
    F = []
    for j in range(len(rings) - 1):
        for i in range(k):
            a, b = j * k + i, j * k + (i + 1) % k
            F.append((a, b, b + k, a + k))
    if cap:
        F.append(tuple(range(k))[::-1])
        F.append(tuple((len(rings) - 1) * k + i for i in range(k)))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], F)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if material:
        ob.data.materials.append(material)
    return ob


def outward_normals(ob):
    """Face normals pointing out of the solid (a loft's winding depends on its rings' order)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def path_points(ctrl, resolution=24):
    """A NURBS through control points (mm) as a dense polyline (mm), in order along it."""
    cu = bpy.data.curves.new("_path", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("NURBS")
    sp.points.add(len(ctrl) - 1)
    for j, p in enumerate(ctrl):
        sp.points[j].co = (p[0] * MM, p[1] * MM, p[2] * MM, 1.0)
    sp.use_endpoint_u = True
    sp.order_u = 3
    sp.resolution_u = resolution
    ob = bpy.data.objects.new("_path", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    P = np.array([v.co[:] for v in me.vertices], np.float64) / MM
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bpy.data.meshes.remove(me)
    return P


def rounded_rect(w, h, r, n=6):
    """Points (x across, y up) round a w x h mm rectangle whose corners are rounded to r, in order."""
    r = min(r, w / 2 - 1e-3, h / 2 - 1e-3)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                       (w / 2 - r, -h / 2 + r, 270)):
        for k in range(n):
            a = np.radians(a0 + 90 * k / (n - 1))
            pts.append((cx + r * np.cos(a), cy + r * np.sin(a)))
    return np.array(pts)


def sweep(name, P, size, material, radius, up=(0.0, 1.0, 0.0), round_end=0.0, step=0.5, s0=0.0, uv_mm=None,
          offset=None):
    """A bar along the polyline P (mm), resampled every `step` mm: its section a rounded rectangle
    size = (across, up) mm, kept as upright as the path allows; `round_end`: its last mm close to a
    rounded tip. `size` and `radius` may instead be functions of the distance along the bar (mm, from
    `s0` at P's start: a piece of a longer bar keeps that bar's taper). `uv_mm`: a band's size (mm) to
    lay along it (bar_uv). `offset`: a function of the same distance, how far (mm) the section's centre
    stands above the path (F08's temple: its bottom edge waves, its top runs straight)."""
    P = np.asarray(P, np.float64)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    ss = np.r_[np.arange(0, s[-1], step), s[-1]]
    P = np.stack([np.interp(ss, s, P[:, i]) for i in range(3)], 1)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    L = ss[-1]
    upv = np.asarray(up, np.float64)
    rings = []
    for p, t, si in zip(P, T, ss):
        sz = size(s0 + si) if callable(size) else size
        rad = radius(s0 + si) if callable(radius) else radius
        prof = rounded_rect(sz[0], sz[1], rad)
        u = upv - t * np.dot(upv, t)
        u /= np.linalg.norm(u)
        a = np.cross(u, t)
        k = 1.0
        if round_end > 0 and si > L - round_end:
            q = (si - (L - round_end)) / round_end
            k = max(np.sqrt(max(1 - q * q, 0.0)), 0.12)
        oy = offset(s0 + si) if offset else 0.0
        rings.append([p + a * x * k + u * (y * k + oy) for x, y in prof])
    ob = loft(name, rings, material)
    if uv_mm:
        bar_uv(ob, rings, [s0 + si for si in ss], uv_mm)
    outward_normals(ob)
    for pl in ob.data.polygons:
        pl.use_smooth = True
    return ob


def ellipsoid(name, centre, radii, material=None, rot_deg=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0)
    ob = bpy.context.active_object
    ob.name = name
    me = ob.data
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3) * np.asarray(radii)
    R = np.asarray(Matrix.Rotation(np.radians(rot_deg[2]), 3, "Z") @ Matrix.Rotation(np.radians(rot_deg[1]), 3, "Y")
                   @ Matrix.Rotation(np.radians(rot_deg[0]), 3, "X"))
    co = co @ R.T + np.asarray(centre)
    me.vertices.foreach_set("co", (co * MM).ravel())
    me.update()
    for pl in me.polygons:
        pl.use_smooth = True
    if material:
        me.materials.append(material)
    return ob


def planar_uv(ob, tex):
    """The front view's projection as the part's UVs ("frame_uv"): each corner's x, y (mm, the frame's
    coordinates) through the texture's map (frame_texture.py) to its pixel, as a fraction of its size."""
    M = np.asarray(tex["mm_to_px"], np.float64)
    w, h = tex["size"]
    me = ob.data
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3) / MM
    W_ = np.asarray(ob.matrix_world)
    co = co @ W_[:3, :3].T + W_[:3, 3] / MM
    lv = np.zeros(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", lv)
    px = co[lv, :2] @ M[:, :2].T + M[:, 2]
    uv = np.stack([px[:, 0] / w, 1 - px[:, 1] / h], 1)
    layer = me.uv_layers.get("frame_uv") or me.uv_layers.new(name="frame_uv")
    layer.data.foreach_set("uv", uv.astype(np.float32).ravel())


def texture_info(frame):
    t = FRAMES[frame].get("texture")
    if not t:
        return None
    import json
    d = ROOT / t
    info = json.loads((d / "map.json").read_text())
    info["dir"] = str(d)
    return info


def band_mm(frame):
    """The frame's temple band (frame_texture.py --temples): its length and height, mm; None without one."""
    tex = texture_info(frame)
    return tuple(tex["temple"]["mm"]) if tex and tex.get("temple") else None


def _textured(parts, frame, materials):
    """The acetate parts take the frame's own colour (planar UVs from the front view)."""
    tex = texture_info(frame)
    if not tex:
        return
    for p in parts:
        if p.data.materials and p.data.materials[0] == materials["acetate"]:
            planar_uv(p, tex)


def build(frame, materials, tilt=None):
    """The frame's front (with its lenses, nose pads and end pieces): wrapped, leaning as the frame is
    built. Returns the parts and the shapes, plus the two hinge points (mm, the parts' coordinates) where
    the temples start (temples() makes those: as drawn, or bent to the ears once they are known)."""
    cfg = FRAMES[frame]
    sh = front_shapes(frame)
    xm, z = wrap_profile(frame)
    T = cfg["depth"]
    zf, zb = rim_fields(sh, cfg)
    front = field_mesh(f"{frame} front", sh["solid"], zf, zb, sh["origin_px"], sh["ppm"], step=cfg.get("mesh_step", 3))
    bend(front, xm, z, -T / 2)                        # the front's face at z = 0 at its most forward point
    front.data.materials.append(materials["acetate"])
    lenses = []
    for i in range(len(sh["lens_masks"])):
        lf, lb = lens_fields(sh, cfg, i)
        ln = field_mesh(f"{frame} lens {i}", sh["lens_masks"][i], lf, lb, sh["origin_px"], sh["ppm"], step=3)
        bend(ln, xm, z, -T / 2)
        ln.data.materials.append(materials["lens"])
        lenses.append(ln)
    parts = [front] + lenses
    # nose pads: behind the bridge, splayed
    pd = cfg["pads"]
    for side in (-1, 1):
        x = side * pd["x"]
        zc = float(np.interp(x, xm, z)) - T - pd["back"] + pd["r"][2] * 0.6
        # clear acetate pads (F01: glued inside the rims, unseen from the front) or the front's own
        parts.append(ellipsoid(f"{frame} pad {side}", (x, pd["y"], zc), pd["r"],
                               materials["clear"] if pd.get("clear") else materials["acetate"],
                               rot_deg=(-12, side * 25, side * 12)))
    # the front's lean (pantoscopic tilt): a shear, the bottom back, so the top stays level and the front
    # view keeps the drawing's outline
    th_t = np.tan(np.radians(cfg["tilt"] if tilt is None else tilt))
    if th_t:
        for p in parts:
            co = np.zeros(len(p.data.vertices) * 3)
            p.data.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            co[:, 2] += co[:, 1] * th_t
            p.data.vertices.foreach_set("co", co.ravel())
            p.data.update()
    out = sh["outline"]
    ep = cfg["endpiece"]
    if ep.get("kind") == "block":
        hinges, ends = [], []
        for side in (-1, 1):
            ob, end, hinge = block_endpiece(frame, cfg, out, xm, z, side, th_t, materials)
            parts.append(ob)
            ends.append(end)
            hinges.append(hinge)
        sh["ends"] = ends
        _textured(parts, frame, materials)
        return parts, sh, hinges
    if ep.get("outline"):
        ends, hinges = [], []
        for side in (-1, 1):
            obs, end, hinge = side_endpiece(frame, cfg, out, xm, z, side, th_t, materials)
            parts += obs
            ends.append(end)
            hinges.append(hinge)
            g = cfg.get("gcd")
            if g and g.get("on") == "endpiece" and side == g["side"]:
                # on the end piece's outer face, where the side view puts it from the hinge (the apex, where
                # the wire goes in): forward and down by the drawing's mm, along the temple
                xo, ya, za = end["apex"]
                fwd = g["hinge_mm"][0] - g["centre_mm"][0]
                down = g["centre_mm"][1] - g["hinge_mm"][1]
                along = np.array([0.0, 0.0, 1.0 if side < 0 else -1.0])
                parts += gcd_parts(frame, materials, float(product_gcd(frame)["lengthMm"]), (xo, ya - down, za + fwd),
                                   along, np.array([0.0, 1.0, 0.0]), np.array([float(side), 0.0, 0.0]))
        sh["ends"] = ends
        _textured(parts, frame, materials)
        return parts, sh, hinges
    # end pieces: a wedge from the back of the front's ends to the hinge (metal: from a plate over the
    # tab's outer side, its outer face one plane from the front to the hinge)
    top = out[:, 1].max()
    hg = cfg["hinge"]
    tp = cfg["temple"]
    hinges, ends = [], []
    for side in (-1, 1):
        xe = out[:, 0].max() if side > 0 else out[:, 0].min()
        zface = float(np.interp(xe, xm, z))
        ze = zface - T + cfg["back_r"]
        # measured from the front's top at its end (a front higher at the brow than at its wings would
        # otherwise stand the end piece up above the wing)
        top = float(out[np.abs(out[:, 0] - xe) < 3.0][:, 1].max())
        y0, y1 = top - ep["top"], top - ep["bottom"]
        xi = xe - side * ep["inset"]
        hx, hy, hz = xe - side * 1.6, top - hg["down"], zface - hg["back"]
        if ep.get("metal"):
            th = tp.get("height", 3.2) / 2 + 0.15            # the apex just round the temple's section
            tw = tp.get("thick", 2.6) / 2 + 0.3
            zf0 = zface - cfg["edge_r"] * 0.9                 # the plate starts behind the front's rounded edge
            xo0, xo2 = xe + side * ep.get("plate", 0.5), hx + side * tw
            xo1 = xo0 + (xo2 - xo0) * (zf0 - ze) / (zf0 - hz)
            xin = xe - side * 1.2                             # the plate's inside, sunk in the tab
            rings = [[(xin, y0, zf0), (xo0, y0, zf0), (xo0, y1, zf0), (xin, y1, zf0)],
                     [(xi, y0, ze), (xo1, y0, ze), (xo1, y1, ze), (xi, y1, ze)],
                     [(hx - side * tw, hy + th, hz), (xo2, hy + th, hz), (xo2, hy - th, hz), (hx - side * tw, hy - th, hz)]]
            mat = materials.get("endmetal", materials["acetate"])
            # the triangle the end piece forms with the front's side (the GCD's place): the wire joint
            # and the front's outer corners, on the outer face
            ends.append({"side": side, "apex": (xo2, hy, hz), "top": (xo0, y0, zf0), "bottom": (xo0, y1, zf0)})
        else:
            rings = [[(xi, y0, ze), (xe - side * 0.3, y0, ze), (xe - side * 0.3, y1, ze), (xi, y1, ze)],
                     [(hx - side * 1.3, hy + 1.6, hz), (hx + side * 1.3, hy + 1.6, hz), (hx + side * 1.3, hy - 1.6, hz),
                      (hx - side * 1.3, hy - 1.6, hz)]]
            mat = materials["acetate"]
            ends.append({"side": side, "apex": (hx + side * 1.3, hy, hz), "top": (xe, y0, ze), "bottom": (xe, y1, ze)})
        if side < 0:
            rings = [r[::-1] for r in rings]
        parts.append(loft(f"{frame} end {side}", rings, mat))
        outward_normals(parts[-1])
        hinges.append((hx, hy, hz))
    sh["ends"] = ends
    _textured(parts, frame, materials)
    return parts, sh, hinges


def fillet(poly, radii, n=8):
    """A closed polygon (u, v) with the corners rounded to the given radii (0 keeps a corner sharp)."""
    P = np.asarray(poly, np.float64)
    k = len(P)
    pts = []
    for i in range(k):
        a, b, c = P[i - 1], P[i], P[(i + 1) % k]
        r = radii[i]
        if r <= 0:
            pts.append(b)
            continue
        d1, d2 = (a - b) / np.linalg.norm(a - b), (c - b) / np.linalg.norm(c - b)
        ang = np.arccos(np.clip(np.dot(d1, d2), -1, 1))
        t = min(r / np.tan(ang / 2), 0.45 * np.linalg.norm(a - b), 0.45 * np.linalg.norm(c - b))
        r = t * np.tan(ang / 2)
        p1, p2 = b + d1 * t, b + d2 * t
        bis = (d1 + d2) / np.linalg.norm(d1 + d2)
        ctr = b + bis * (r / np.sin(ang / 2))
        a1 = np.arctan2(*(p1 - ctr)[::-1])
        a2 = np.arctan2(*(p2 - ctr)[::-1])
        da = (a2 - a1 + np.pi) % (2 * np.pi) - np.pi
        for s in np.linspace(0, 1, n):
            pts.append(ctr + r * np.array([np.cos(a1 + da * s), np.sin(a1 + da * s)]))
    return np.array(pts)


def prism(name, poly, x0, x1, to_yz, material, bevel=0.0):
    """A solid: the polygon (u, v) mapped by to_yz to (y, z) mm, run across x from x0 to x1 mm; its edges
    bevelled `bevel` mm (a machined part's edges catch the light)."""
    poly = np.asarray(poly, np.float64)
    yz = np.array([to_yz(u, v) for u, v in poly])
    k = len(poly)
    V = np.concatenate([np.c_[np.full(k, x0), yz], np.c_[np.full(k, x1), yz]]) * MM
    F = [tuple(range(k)), tuple(range(2 * k - 1, k - 1, -1))]
    F += [(i, (i + 1) % k, k + (i + 1) % k, k + i) for i in range(k)]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], F)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    outward_normals(ob)
    if bevel > 0:
        m = ob.modifiers.new("bevel", "BEVEL")
        m.width = bevel * MM
        m.segments = 3
        m.limit_method = "ANGLE"
        m.angle_limit = np.radians(25)
        m.harden_normals = True
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        ob.modifiers.clear()
        old = ob.data
        ob.data = me2
        bpy.data.meshes.remove(old)
    ob.data.materials.append(material)
    for pl in ob.data.polygons:
        pl.use_smooth = False
    return ob


def polygon_centroid(P):
    """The area centroid of a simple polygon (u, v)."""
    P = np.asarray(P, np.float64)
    x, y = P[:, 0], P[:, 1]
    x1, y1 = np.roll(x, -1), np.roll(y, -1)
    c = x * y1 - x1 * y
    A = c.sum() / 2
    return np.array([((x + x1) * c).sum() / (6 * A), ((y + y1) * c).sum() / (6 * A)])


def side_endpiece(frame, cfg, out, xm, z, side, th_t, materials):
    """One end piece: the metal triangle behind the acetate tab, from its side outline
    (endpiece["outline"]: u mm back from the tab's back, v mm down from the front's top at the end). Its
    base is the tab's back edge, top to bottom, its top corner flush with the front's top; its outer face
    flush with the tab's side (a hair proud, so the two never share a plane), `thick` mm across; the
    hinge's barrel behind the apex, inside, its screw head on top. Returns the parts, the triangle
    platform (apex, base corners, its centre: where the GCD sits; on the outer face) and the hinge point
    (the temple's start: the apex's centre, on the temple's mid-line)."""
    ep = cfg["endpiece"]
    tp = cfg["temple"]
    xe = out[:, 0].max() if side > 0 else out[:, 0].min()
    near = out[np.abs(out[:, 0] - xe) < 1.5]
    ytop = float(near[:, 1].max()) - 0.03                      # a hair under the top: no coplanar faces
    # the tab's back: the front's back plane at the end, the base set `overlap` mm into the acetate so no
    # gap opens at the back's rounded edge
    zb = float(np.interp(xe, xm, z)) - cfg["depth"] + ep.get("overlap", 0.3) + ytop * th_t
    to_yz = lambda u, v: (ytop - v, zb - u - v * th_t)
    P = {k: np.asarray(v, np.float64) for k, v in ep["outline"].items()}
    # an outline may run level along the front's top before it falls to the apex (`top_flat`, F05)
    flat = ["top_flat"] if "top_flat" in P else []
    poly = [P[k] for k in ["base_top"] + flat + ["apex_top", "apex_bottom", "bottom_flat", "base_bottom"]]
    shape = fillet(poly, [ep["r_top"]] + [ep.get("r_topflat", 1.0)] * len(flat) + [0, 0, ep["r_flat"], ep["r_bottom"]])
    xo = xe + side * ep["proud"]                                # the outer face
    mat = materials.get("endmetal", materials["acetate"])
    obs = [prism(f"{frame} end {side}", shape, xo, xo - side * ep["thick"], to_yz, mat, ep.get("bevel", 0.0))]
    # the hinge: a barrel round a vertical pin just behind the apex, on the inside, its screw head on top
    ua, vt, vb = float(P["apex_top"][0]), float(P["apex_top"][1]), float(P["apex_bottom"][1])
    hb = ep["hinge_barrel"]
    yb0, yb1 = ytop - vb - 0.1, ytop - vt + hb["above"]
    zc = to_yz(ua, (vt + vb) / 2)[1] - hb["behind"]
    xc = xo - side * hb["in"]
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=hb["r"] * MM, depth=(yb1 - yb0) * MM,
                                        location=(xc * MM, (yb0 + yb1) / 2 * MM, zc * MM), rotation=(np.pi / 2, 0, 0))
    bar = bpy.context.active_object
    bar.name = f"{frame} hinge {side}"
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=hb["head_r"] * MM, depth=0.18 * MM,
                                        location=(xc * MM, (yb1 + 0.09) * MM, zc * MM), rotation=(np.pi / 2, 0, 0))
    head = bpy.context.active_object
    head.name = f"{frame} hinge {side} screw"
    for ob in (bar, head):
        # the cylinders' axes along y (their rotation applied), so the parts share the frame's coordinates
        ob.data.transform(ob.matrix_basis)
        ob.matrix_basis.identity()
        ob.data.materials.append(mat)
        for pl in ob.data.polygons:
            pl.use_smooth = True
        obs.append(ob)
    ya, za = to_yz(ua, (vt + vb) / 2)
    # the triangle platform's centre: its area centroid, on the outer face (the founder: the GCD is centred
    # on the triangle, Oct 22 2026)
    cu, cv = polygon_centroid(shape)
    end = {"side": side, "apex": (xo, ya, za), "top": (xo, *to_yz(*P["base_top"])),
           "bottom": (xo, *to_yz(*P["base_bottom"])), "centre": (xo, *to_yz(cu, cv)),
           "normal": (float(side), 0.0, 0.0), "uv_centre": (float(cu), float(cv))}
    return obs, end, (xo - side * tp["thick"] / 2, ya, za)


def block_endpiece(frame, cfg, out, xm, z, side, th_t, materials):
    """An acetate end piece (F03): the temple's own section carried forward from the joint into the
    front's end tab, its outer face flush with the tab's side (`inset` mm inside it, so the two never
    share a plane); its bottom flaring down `flare` mm into the tab. Returns it, its end record (no GCD
    platform: F03's GCD is on the temple) and the hinge point (the temple's start: its section's centre, a
    hair behind the joint)."""
    ep, tp, T = cfg["endpiece"], cfg["temple"], cfg["depth"]
    xe = out[:, 0].max() if side > 0 else out[:, 0].min()
    zface = float(np.interp(xe, xm, z))
    yt = float(out[:, 1].max()) - tp["top_below"]            # the temple's top edge (side view)
    yb = yt - tp["height"]
    yc = (yt + yb) / 2
    th0 = tp["thicks"][0][1] if tp.get("thicks") else tp["thick"]
    xo = xe - side * ep.get("inset", 0.03)
    xc = xo - side * th0 / 2
    z_face = zface + yc * th_t                                # the tab's face at the temple's height
    z_joint = z_face - ep["back"]
    z_in = z_face - T + ep.get("into", 2.0)                    # inside the tab
    r = tp.get("edge_r", 0.9)
    fl = ep.get("flare", 0.0)
    rings = []
    zs = (z_in, z_face - T, z_joint)
    for zz, flare in zip(zs, (fl, fl * 0.6, 0.0)):
        h = tp["height"] + flare
        prof = rounded_rect(th0, h, r)
        rings.append([(xc + x, yc - flare / 2 + y, zz) for x, y in prof])
    band = band_mm(frame) if "temple" in materials else None
    ob = loft(f"{frame} end {side}", rings, materials["temple"] if band else materials["acetate"])
    if band:
        # the temple's acetate carried forward into the tab (u: mm along the temple, before its start)
        bar_uv(ob, rings, [z_joint - zz for zz in zs], band)
    outward_normals(ob)
    for pl in ob.data.polygons:
        pl.use_smooth = True
    end = {"side": side, "apex": (xo, yc, z_joint), "top": (xo, yt, z_joint), "bottom": (xo, yb, z_joint),
           "centre": (xo, yc, z_joint), "normal": (float(side), 0.0, 0.0)}
    return ob, end, (xc, yc, z_joint - 0.05)


def table(pairs):
    """A piecewise-linear function of distance (mm) from (s, value) pairs."""
    s_, v_ = np.asarray(pairs, np.float64).T
    return lambda s: float(np.interp(s, s_, v_))


# The GCD on the product executes one way only (the founder, Oct 26 2026): full size, its own proportions,
# its one placement, on every frame, in every view; never scaled, moved or left off to suit a picture.
# Its length is the product's (content/products/<frame>.json, gcd.lengthMm: 0.98 x the temple face's
# height); on a temple its centre is 0.82 x that height from the hinge seam and 39% down the face,
# parallel to the temple (01-brand-system.md, "Physical scale on the frames").
GCD_FROM_HINGE, GCD_DOWN = 0.82, 0.39


def product_gcd(frame):
    """The frame's GCD as its product file gives it."""
    import json
    return json.loads((ROOT / "content" / "products" / f"{frame.lower()}.json").read_text())["gcd"]


def path_frame(P, s_at, up=(0.0, 1.0, 0.0)):
    """A swept bar's frame `s_at` mm along its path P (mm): the point, the tangent, the section's up and
    its across (as sweep() builds them)."""
    P = np.asarray(P, np.float64)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    i = int(np.searchsorted(s, s_at))
    p = np.array([np.interp(s_at, s, P[:, k]) for k in range(3)])
    t = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
    t /= np.linalg.norm(t)
    u = np.asarray(up, np.float64) - t * np.dot(up, t)
    u /= np.linalg.norm(u)
    return p, t, u, np.cross(u, t)


def gcd_parts(frame, materials, length, centre, along, up, normal, proud=0.02):
    """The GCD (gold band, black onyx inset), built from the vector master (brand/emblems/gcd/svg/
    gcd-geometry.svg) and scaled so the band's outline is exactly `length` mm long, its height the
    master's proportion of that. Its centre at `centre` (mm, on the face it is set
    into), its length along `along` (reading left to right seen from outside), its top towards `up`, its
    face `proud` mm out along `normal`."""
    sys.path.insert(0, str(ROOT / "tools" / "blender"))
    import gcd_render
    svg = gcd_render.GEOM.read_text()
    outer = gcd_render.parse_path(re.search(r'id="outer"\s+d="([^"]+)"', svg).group(1))
    aperture = gcd_render.parse_path(re.search(r'id="aperture"\s+d="([^"]+)"', svg).group(1))
    # the polished edge rounded inside the outline (offset in by its radius), so the band's outer edge is
    # the master's outline exactly: its length and its height the master's proportion of it
    gold = to_mesh(gcd_render.curve_object(f"{frame} gcd gold", outer + aperture, gcd_render.GOLD_DEPTH,
                                           gcd_render.GOLD_BEVEL, 0.0, offset=-gcd_render.GOLD_BEVEL))
    stone = to_mesh(gcd_render.curve_object(f"{frame} gcd onyx", aperture,
                                            gcd_render.GOLD_DEPTH - 2 * gcd_render.STONE_RECESS,
                                            gcd_render.STONE_BEVEL, -gcd_render.STONE_RECESS))

    def local_mm(ob):
        co = np.zeros(len(ob.data.vertices) * 3)
        ob.data.vertices.foreach_get("co", co)
        return co.reshape(-1, 3) / MM + np.asarray(ob.location) / MM
    # the scale from the band as built (the master's canvas is wider than the emblem: scaling the canvas
    # to the length made F03's GCD 3.7% short, 8.47 mm for 8.8)
    cg = local_mm(gold)
    k = length / float(np.ptp(cg[:, 0]))
    mid = (cg.min(0) + cg.max(0)) / 2
    depth = float(np.ptp(cg[:, 2])) * k
    c = np.asarray(centre, np.float64) + np.asarray(normal, np.float64) * (proud - depth / 2)
    R = np.stack([np.asarray(along, np.float64), np.asarray(up, np.float64), np.asarray(normal, np.float64)], 1)
    obs = []
    for ob, mat in ((gold, materials["gold"]), (stone, materials["onyx"])):
        co = (local_mm(ob) - mid * np.array([1.0, 1.0, 0.0])) * k
        ob.location = (0, 0, 0)
        w = co @ R.T + c
        ob.data.vertices.foreach_set("co", (w * MM).ravel())
        ob.data.update()
        ob.data.materials.clear()
        ob.data.materials.append(mat)
        for pl in ob.data.polygons:
            pl.use_smooth = True
        obs.append(ob)
    return obs


def temples(frame, hinges, materials, ears=None, split=False, split_after_mm=0.0):
    """The temples, from each hinge (mm) back to the ear and curving down behind it. `ears`: the point
    on each side where the temple rests on the ear's root, in the same coordinates; without them, the
    drawing's: straight back from the hinge. With `split`, each temple is two objects, the run from the
    hinge to the ear and the part behind the ear (named "... back"), so a front view can leave the
    second out: from the front it is always behind the ear. `split_after_mm` moves that split on past
    the ear's root (acetate and strip temples), for a view in which the ear itself is seen hiding where
    the temple goes in (a three-quarter view: the composite lays the ear over it)."""
    cfg = FRAMES[frame]
    t = cfg["temple"]
    obs = []
    for k, h in enumerate(hinges):
        h = np.asarray(h, np.float64)
        if t.get("kind") == "acetate":
            # a solid acetate temple (F03): its section from the side and top views along its length
            # (`heights`, `thicks`: mm from the joint), edges rounded `edge_r`; straight back from the joint
            # and down behind the ear, as drawn or bent to the ear
            side = 1.0 if h[0] > 0 else -1.0
            if ears is None:
                jt = h + np.array([0.0, 0.0, -t["straight"]])
                tip = path_points([jt + np.array([0.0, -dv, -du]) for du, dv in t["tip_path"]], resolution=16)
                P = np.vstack([h + np.outer(np.linspace(0, 1, 160), jt - h), tip[1:]])
            else:
                e = np.asarray(ears[k], np.float64)
                d = e - h
                d /= np.linalg.norm(d)
                down = np.array([0.0, -1.0, 0.0])
                back = d * 0.35 + np.array([0.0, 0.0, -1.0]) * 0.65
                back /= np.linalg.norm(back)
                tail = [e + back * 14 + down * 6, e + back * 26 + down * 20, e + back * 30 + down * t["drop"]]
                P = path_points([h, h + d * 12, e - d * 10, e] + tail)
            s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
            se = t["straight"] if ears is None else float(s[np.argmin(np.linalg.norm(P - e, axis=1))])
            hf, tf = table(t["heights"]), table(t["thicks"])
            size = lambda s_: (tf(s_), hf(s_))
            rad = lambda s_: min(t.get("edge_r", 0.9), 0.45 * min(tf(s_), hf(s_)))
            # the section's centre below the straight run where the side view's edges are not parallel (F08)
            of = (lambda s_, f_=table(t["offsets"]): -f_(s_)) if t.get("offsets") else None
            rend_ = t.get("round_end", 2.5)
            sc_ = float(s[-1])
            if split:
                sc_ = min(se + split_after_mm, float(s[-1]) - 5.0)
                a_, b_ = s <= sc_ + 1e-6, s >= sc_ - 1e-6
                pieces = [(f"{frame} temple {k}", P[a_], 0.0, 0.0), (f"{frame} temple {k} back", P[b_], float(s[b_][0]), rend_)]
            else:
                pieces = [(f"{frame} temple {k}", P, 0.0, rend_)]
            # in the front's material, laid along the temple (F01's tortoise), the front's plain black, or a
            # translucent acetate of its own (F08's smoke grey)
            band = band_mm(frame) if "temple" in materials else None
            mat = materials["temple_smoke"] if t.get("smoke") else (materials["temple"] if band else materials["acetate"])
            for name, Pp, s0, rend in pieces:
                if len(Pp) >= 2:
                    obs.append(sweep(name, Pp, size, mat, rad, round_end=rend, s0=s0, uv_mm=band, offset=of))
            if t.get("core"):
                # the metal core inside a translucent temple (F08), along its straight run, its end cut as its
                # `ups` and `heights` give it; not on past the ear's root
                c_ = t["core"]
                ch, cu_ = table(c_["heights"]), table(c_.get("ups", [(0.0, 0.0)]))
                sel = (s >= c_["from"] - 1e-6) & (s <= min(c_["to"], sc_) + 1e-6)
                if sel.sum() >= 2:
                    obs.append(sweep(f"{frame} temple {k} core", P[sel], lambda s_: (c_["thick"], ch(s_)),
                                     materials["core"], 0.2, s0=float(s[sel][0]), offset=cu_))
            g = cfg.get("gcd")
            if g and g.get("on") == "temple" and side == g["side"]:
                # on the temple's outer face: centre 0.82 x the face's height from the hinge seam (the path
                # starts at it), 39% down the face, parallel to the temple
                pg = product_gcd(frame)
                face = float(pg["templeFaceHeightMm"])
                sa = GCD_FROM_HINGE * face

                def face_pt(s_):
                    p_, t_, u_, a_ = path_frame(P, s_)
                    n_ = a_ * (1.0 if np.dot(a_, [side, 0, 0]) > 0 else -1.0)
                    return p_ + n_ * tf(s_) / 2, u_, n_
                centre, u_, n_ = face_pt(sa)
                # flat on the face, which turns in as the temple narrows (set square to the temple's mid-line,
                # its front end sat 0.013 mm into the acetate)
                along = face_pt(sa + 1.0)[0] - face_pt(sa - 1.0)[0]
                along -= u_ * np.dot(along, u_)
                along /= np.linalg.norm(along)
                x_e = -along if side < 0 else along           # reading left to right seen from outside
                n_ = np.cross(x_e, u_)                         # out of the face
                centre = centre + u_ * (hf(sa) / 2 - GCD_DOWN * face + (of(sa) if of else 0.0))
                obs += gcd_parts(frame, materials, float(pg["lengthMm"]), centre, x_e, u_, n_)
            continue
        if ears is None and t.get("tip_path"):
            # as drawn and photographed: square to the front, straight back from the hinge to the joint,
            # then the acetate tip along the side drawing's curve; split where the tip starts to bend
            jt = h + np.array([0.0, 0.0, -t["tip_from"]])
            tip = path_points([jt + np.array([0.0, -dv, -du]) for du, dv in t["tip_path"]], resolution=16)
            P = np.vstack([h + np.outer(np.linspace(0, 1, 120), jt - h), tip[1:]])
            s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
            cut = lambda a, b: P[(s >= a - 1e-6) & (s <= b + 1e-6)]
            tf, sb = t["tip_from"], t["tip_from"] + t.get("tip_straight", 12.0)
            strip, tipsz = (t["thick"], t["height"]), (t["tip"][1], t["tip"][0])
            metal = materials.get("endmetal", materials["metal"])
            pieces = [(f"{frame} temple {k}", cut(0, tf), strip, metal, 0.4, 0.0)]
            if split:
                pieces += [(f"{frame} temple {k} tip", cut(tf, sb), tipsz, materials["acetate"], 1.0, 0.0),
                           (f"{frame} temple {k} back", cut(sb, s[-1]), tipsz, materials["acetate"], 1.0, 2.5)]
            else:
                pieces += [(f"{frame} temple {k} tip", cut(tf, s[-1]), tipsz, materials["acetate"], 1.0, 2.5)]
            for name, Pp, size, mat, rad, rend in pieces:
                if len(Pp) >= 2:
                    obs.append(sweep(name, Pp, size, mat, rad, round_end=rend))
            continue
        if ears is None:
            e = h + np.array([0.0, -2.0, -t["straight"]])
        else:
            e = np.asarray(ears[k], np.float64)
        d = e - h
        d /= np.linalg.norm(d)
        down = np.array([0.0, -1.0, 0.0])
        back = d * 0.35 + np.array([0.0, 0.0, -1.0]) * 0.65
        back /= np.linalg.norm(back)
        tail = [e + back * 14 + down * 6, e + back * 26 + down * 20, e + back * 30 + down * t["drop"]]
        if t.get("kind") == "strip":
            # a flat metal bar from the hinge, then the acetate tip from `tip_from` mm along it; split at
            # the ear's root as the wire is
            P = path_points([h, h + d * 12, e - d * 10, e] + tail)
            s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
            se = min(float(s[np.argmin(np.linalg.norm(P - e, axis=1))]) + split_after_mm, float(s[-1]) - 5.0)
            cut = lambda a, b: P[(s >= a - 1e-6) & (s <= b + 1e-6)]
            tf = min(float(t.get("tip_from", s[-1])), s[-1] - 5.0)
            strip, tip = (t["thick"], t["height"]), (t["tip"][1], t["tip"][0])
            pieces = [(f"{frame} temple {k}", cut(0, tf), strip, materials.get("endmetal", materials["metal"]), 0.45, 0.0)]
            if split and se > tf:
                pieces += [(f"{frame} temple {k} tip", cut(tf, se), tip, materials["acetate"], 1.0, 0.0),
                           (f"{frame} temple {k} back", cut(se, s[-1]), tip, materials["acetate"], 1.0, 2.5)]
            else:
                pieces += [(f"{frame} temple {k} tip" if not split else f"{frame} temple {k} back",
                            cut(tf, s[-1]), tip, materials["acetate"], 1.0, 2.5)]
            for name, Pp, size, mat, rad, rend in pieces:
                if len(Pp) >= 2:
                    obs.append(sweep(name, Pp, size, mat, rad, round_end=rend))
            continue
        runs = [(f"{frame} temple {k}", [h, h + d * 12, e - d * 10, e]), (f"{frame} temple {k} back", [e] + tail)] \
            if split else [(f"{frame} temple {k}", [h, h + d * 12, e - d * 10, e] + tail)]
        for name, path in runs:
            cu = bpy.data.curves.new(name, "CURVE")
            cu.dimensions = "3D"
            cu.bevel_depth = t["radius"] * MM
            cu.bevel_resolution = 4
            cu.use_fill_caps = True
            sp = cu.splines.new("NURBS")
            sp.points.add(len(path) - 1)
            for j, p in enumerate(path):
                sp.points[j].co = (p[0] * MM, p[1] * MM, p[2] * MM, 1.0)
            sp.use_endpoint_u = True
            sp.order_u = 3
            sp.resolution_u = 24
            tob = bpy.data.objects.new(cu.name, cu)
            bpy.context.scene.collection.objects.link(tob)
            tob = to_mesh(tob)
            tob.data.materials.append(materials["metal"])
            for pl in tob.data.polygons:
                pl.use_smooth = True
            obs.append(tob)
    return obs


def materials_for(frame, tint=(0.04, 0.04, 0.04)):
    """Black acetate (polished), the temples' wire (black-coated metal) and the lens: dark glass for
    the camera and reflections, a filter of its measured tint for shadows (so a light lens casts a
    tinted shadow, a dark one a full one)."""
    def principled(name, base, rough, metallic=0.0, ior=1.5):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = base
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metallic
        b.inputs["IOR"].default_value = ior
        return m
    lens = bpy.data.materials.new("lens")
    lens.use_nodes = True
    nt = lens.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    outn = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    glass.inputs["Base Color"].default_value = (*[float(v) for v in tint], 1)   # Cycles tints a pass through once
    glass.inputs["Transmission Weight"].default_value = 1.0
    glass.inputs["Roughness"].default_value = 0.0
    glass.inputs["IOR"].default_value = 1.5
    filt = nt.nodes.new("ShaderNodeBsdfTransparent")
    filt.inputs["Color"].default_value = (*[float(v) for v in tint], 1)
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    nt.links.new(glass.outputs[0], mix.inputs[1])
    nt.links.new(filt.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], outn.inputs["Surface"])
    grad = FRAMES.get(frame, {}).get("lens", {}).get("gradient")
    if grad:
        # a gradient lens (F06): its tint by height on the lens, as measured (the lens's own coordinates
        # are the frame's: mm above the openings' centre, in metres)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
        ys = [g[0] for g in grad]
        lo, hi = min(ys), max(ys)
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = lo * MM
        mr.inputs["From Max"].default_value = hi * MM
        mr.clamp = True
        nt.links.new(sep.outputs["Y"], mr.inputs["Value"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        els = ramp.color_ramp.elements
        pts = sorted(((y - lo) / (hi - lo), c) for y, c in grad)
        els[0].position, els[0].color = pts[0][0], (*pts[0][1], 1)
        els[1].position, els[1].color = pts[-1][0], (*pts[-1][1], 1)
        for p_, c_ in pts[1:-1]:
            e_ = els.new(p_)
            e_.color = (*c_, 1)
        nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], glass.inputs["Base Color"])
        nt.links.new(ramp.outputs["Color"], filt.inputs["Color"])
    tex = texture_info(frame)
    ep_cfg = FRAMES.get(frame, {}).get("endpiece", {})
    metal_rough = ep_cfg.get("metal_rough", 0.07)
    acetate = principled("acetate", (0.0015, 0.0015, 0.0017, 1), 0.06, ior=1.49)
    if tex:
        acetate = textured_acetate(tex)
    # polished black metal (F04's end pieces and temples): near black head-on, a mirror at a glancing
    # angle (the founder's desk shots, Oct 22 2026). `coated` (F05): black paint over the metal, a satin
    # dielectric: its product shots, in a white tent, show it black at every angle, where bare metal went
    # silver along a temple seen edge-on in a white studio
    endmetal = (principled("endmetal", (0.008, 0.008, 0.0085, 1), metal_rough, ior=1.5) if ep_cfg.get("coated")
                else principled("endmetal", (0.035, 0.035, 0.038, 1), metal_rough, metallic=1.0))
    extra = {}
    if tex and tex.get("temple"):
        # acetate temples in the front's material (F01): its band laid along each temple (sweep UVs)
        extra["temple"] = band_acetate(pathlib.Path(tex["dir"]) / tex["temple"]["file"])
    tp_cfg = FRAMES.get(frame, {}).get("temple", {})
    if tp_cfg.get("smoke"):
        # translucent temples (F08): smoke grey acetate round a textured metal core (matte, mid grey)
        extra["temple_smoke"] = clear_acetate(tp_cfg["smoke"])
        extra["core"] = principled("core", (0.42, 0.42, 0.40, 1), 0.5, metallic=1.0)
    return {**extra, "acetate": acetate,
            "metal": principled("metal", (0.005, 0.005, 0.0055, 1), 0.6),      # black-coated wire, satin
            "endmetal": endmetal,
            "lens": lens,
            # the GCD set into a temple (F03): brand gold #C6A36A, polished; black onyx (as the texture's)
            "gold": principled("gcd gold", (0.565, 0.366, 0.145, 1), 0.22, metallic=1.0),
            "onyx": principled("gcd onyx", (0.006, 0.006, 0.006, 1), 0.04),
            "clear": clear_acetate(FRAMES.get(frame, {}).get("pads", {}).get("smoke", 1.0))}


def textured_acetate(tex, rough=0.06):
    """Polished acetate in the frame's own colour (albedo.png, linear), with the metal set into the front
    where masks.png marks it: R the GCD's gold band, G its onyx, B pin heads (steel)."""
    m = bpy.data.materials.new("acetate")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    outn = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "frame_uv"
    alb = nt.nodes.new("ShaderNodeTexImage")
    alb.image = bpy.data.images.load(str(pathlib.Path(tex["dir"]) / "albedo.png"))
    alb.image.colorspace_settings.name = "Linear Rec.709"
    alb.interpolation = "Cubic"
    alb.extension = "EXTEND"
    msk = nt.nodes.new("ShaderNodeTexImage")
    msk.image = bpy.data.images.load(str(pathlib.Path(tex["dir"]) / "masks.png"))
    msk.image.colorspace_settings.name = "Non-Color"
    msk.interpolation = "Linear"
    msk.extension = "EXTEND"
    for t_ in (alb, msk):
        nt.links.new(uv.outputs["UV"], t_.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(msk.outputs["Color"], sep.inputs["Color"])

    def bsdf(base, rough_, metallic=0.0):
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        b.inputs["Base Color"].default_value = base
        b.inputs["Roughness"].default_value = rough_
        b.inputs["Metallic"].default_value = metallic
        b.inputs["IOR"].default_value = 1.49
        return b
    ace = bsdf((0.01, 0.01, 0.01, 1), rough)
    nt.links.new(alb.outputs["Color"], ace.inputs["Base Color"])
    gold = bsdf((0.565, 0.366, 0.145, 1), 0.22, 1.0)          # brand gold, #C6A36A
    onyx = bsdf((0.006, 0.006, 0.006, 1), 0.04)
    pin = bsdf((0.85, 0.85, 0.85, 1), 0.32, 1.0)              # domed steel heads: they gather the room
    cur = ace.outputs[0]
    for ch, b in (("Red", gold), ("Green", onyx), ("Blue", pin)):
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(sep.outputs[ch], mx.inputs["Fac"])
        nt.links.new(cur, mx.inputs[1])
        nt.links.new(b.outputs[0], mx.inputs[2])
        cur = mx.outputs[0]
    nt.links.new(cur, outn.inputs["Surface"])
    return m


def clear_acetate(tint=1.0):
    """Clear acetate (F01's nose pads): a polished dielectric that light passes, colourless or smoky grey
    (`tint`: what one pass through it lets by, in at one face and out at the other: F08's light-tent checks
    showed the tent behind a temple at about the tint, not its square; F06's pads, F08's temples; a grey or
    an r, g, b)."""
    m = bpy.data.materials.new("clear acetate")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    rgb = tuple(float(v) for v in tint) if isinstance(tint, (list, tuple)) else (tint,) * 3
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["IOR"].default_value = 1.49
    return m


def band_acetate(path, rough=0.06):
    """Polished acetate coloured by a band image (linear) laid along a swept bar: its "bar_uv" runs u along
    the bar and v round its section, both in the band's own units (sweep(uv_mm=...))."""
    m = bpy.data.materials.new("acetate temple")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    outn = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "bar_uv"
    alb = nt.nodes.new("ShaderNodeTexImage")
    alb.image = bpy.data.images.load(str(path))
    alb.image.colorspace_settings.name = "Linear Rec.709"
    alb.interpolation = "Cubic"
    alb.extension = "REPEAT"
    nt.links.new(uv.outputs["UV"], alb.inputs["Vector"])
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = 1.49
    nt.links.new(alb.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(b.outputs[0], outn.inputs["Surface"])
    return m


def bar_uv(ob, rings, s_of_ring, band_mm):
    """UVs ("bar_uv") for a loft of `rings` (each a list of points, mm): u the distance along the bar
    (`s_of_ring`, mm), v the way round each ring as a share of its perimeter, so the band (`band_mm`: its
    length, its height) wraps once round the section whatever the section's size, with no seam: it repeats
    top to bottom. The end caps take their ring's first point's u."""
    L_mm, _ = band_mm
    k = len(rings[0])
    vfrac = []
    for r in rings:
        r = np.asarray(r, np.float64)
        d = np.linalg.norm(np.diff(np.vstack([r, r[:1]]), axis=0), axis=1)
        c = np.r_[0, np.cumsum(d)]
        vfrac.append(c / c[-1])                         # k + 1 values: the last is 1 (back to the start)
    me = ob.data
    uv = np.zeros((len(me.loops), 2), np.float32)
    lv = np.zeros(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", lv)
    n_side = (len(rings) - 1) * k
    for pi, pl in enumerate(me.polygons):
        ls = range(pl.loop_start, pl.loop_start + pl.loop_total)
        if pi < n_side:
            j, i = divmod(pi, k)
            wrap = (i + 1) % k == 0
            for li in ls:
                vi = int(lv[li])
                jr, ir = divmod(vi, k)
                v = vfrac[jr][ir] if not (wrap and ir == 0) else 1.0
                uv[li] = (s_of_ring[jr] / L_mm, v)
        else:
            for li in ls:
                jr, ir = divmod(int(lv[li]), k)
                uv[li] = (s_of_ring[jr] / L_mm, vfrac[jr][ir])
    layer = me.uv_layers.get("bar_uv") or me.uv_layers.new(name="bar_uv")
    layer.data.foreach_set("uv", uv.ravel())


def check(frame, out, samples=64, tint=None, el_deg=4.0, yaw_deg=0.0):
    """The built frame, upright in a light tent and seen from the front and a little above as the
    product shot was taken, for a side-by-side with the product photo. `tint`: the lens's (a light lens
    shows what is behind it); `yaw_deg`: the frame turned (its right towards the camera for positive), for
    a three-quarter shot."""
    sys.path.insert(0, str(ROOT / "tools" / "blender"))
    import gcd_render
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    gcd_render.setup_scene(1600, samples, light="lightbox")
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
    sc.render.film_transparent = False
    mats = materials_for(frame, tint) if tint else materials_for(frame)
    parts, sh, hinges = build(frame, mats)
    parts += temples(frame, hinges, mats)
    rig = bpy.data.objects.new("rig", None)
    sc.collection.objects.link(rig)
    for p in parts:
        p.parent = rig
    rig.rotation_euler = (np.radians(90), 0, np.radians(yaw_deg))   # the frame's up (y) to the world's up (z)
    # the tent's front is open where the camera looks in: dark in the directions round the camera,
    # which is what the frame's face mirrors (it is why a black frame photographs black in a tent)
    nt = sc.world.node_tree
    bg = nt.nodes["Background"]
    tent = bg.inputs["Color"].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.88
    mr.inputs["From Max"].default_value = -0.96
    nt.links.new(sep.outputs["Y"], mr.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(mr.outputs["Result"], mix.inputs["Factor"])
    nt.links.new(tent, mix.inputs[6])
    mix.inputs[7].default_value = (0.012, 0.012, 0.012, 1)
    nt.links.new(mix.outputs[2], bg.inputs["Color"])
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.lens = 100
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36
    dist = (sh["width"] + 40) * MM * 100 / 36
    el = np.radians(el_deg)
    cam.location = (0, -dist * np.cos(el), dist * np.sin(el))
    cam.rotation_euler = (np.radians(90) - el, 0, 0)
    sc.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("frame")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--tint", default=None, help="the lens's transmission, linear r,g,b (wear3d.lens_tint)")
    ap.add_argument("--el", type=float, default=4.0, help="the camera's height above the frame's centre, degrees")
    ap.add_argument("--yaw", type=float, default=0.0, help="the frame turned about the vertical, degrees")
    a = ap.parse_args()
    if a.check:
        tint = tuple(float(v) for v in a.tint.split(",")) if a.tint else None
        check(a.frame, pathlib.Path(a.out or f"/tmp/{a.frame}-3d-check.png"), tint=tint, el_deg=a.el, yaw_deg=a.yaw)
