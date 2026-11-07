#!/usr/bin/env python3
"""The drawer wall: the cabinet, the drawer, the renders (DRAWER-WALL.md, Assets, D3). Blender as a Python module
(bpy 5.2.2), Cycles on the CPU. The founder-reviewed prototype (docs/build/drawer-wall/prototype/drawer_scene.py)
multiplied into a wall: black calfskin with its grain in world space, piped edges, the knob tilted 28 degrees up
with the GCD on its face (black relief by default, O15), the seam light as state, the rails for the labels.

    python3 tools/blender/drawer_wall.py wall --layout portrait --knob black-relief --variant lit
    python3 tools/blender/drawer_wall.py wall --layout landscape --knob black-relief --variant dark
    python3 tools/blender/drawer_wall.py sequence --frames 24                      # the base sequence, no frame
    python3 tools/blender/drawer_wall.py sequence --frames 24 --frame F09 --region # a frame's region renders (D4)
    python3 tools/blender/drawer_wall.py knob --knob gold                          # a close-up for O15
    python3 tools/blender/drawer_wall.py env                                       # the drawer's light from the lifted pose
    python3 tools/blender/drawer_wall.py cameras                                   # camera/open.json and camera/inspect.json
    python3 tools/blender/drawer_wall.py check --layout portrait --knob black-relief

Renders go to work/wall/ (git-ignored, 16-bit PNG); the web outputs (graded, AVIF and WebP) are made by `export`
from them, and the manifest entries written by tools/blender/wall_export.py. Units: metres, built from millimetres.
Coordinates: x across the wall, y into it (the room is y < 0, the viewer looks along +y), z up. The cabinet's face
is the plane y = 0; a drawer slides toward -y.
"""
import argparse
import json
import math
import os
import pathlib
import sys
import time

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "blender"))
import frame3d  # noqa: E402

MM = 0.001
WORK = ROOT / "work" / "wall"
FRAME_IDS = ["F01", "F02", "F03", "F04", "F05", "F06", "F08", "F09"]

# --- The drawer (mm) --------------------------------------------------------------------------------------------
DRAWER_W, DRAWER_H = 220.0, 122.0      # the front
FRONT_T = 22.0                         # the front's thickness
FRONT_BEVEL = 4.0
CORD_R, CORD_INSET = 1.6, 3.6          # the piping along the front's top and bottom
GAP = 1.6                              # the seam round the front in the cabinet's opening
BOX_DEPTH = 290.0                      # the drawer box behind the front
BOX_WALL = 9.0
BOX_H = 96.0                           # the box's inner height
FLOOR_T = 6.0
KNOB_D, KNOB_DEPTH, KNOB_TILT = 46.0, 22.0, 28.0
GCD_MM = 30.0                          # the knob's GCD
FULL_EXT = 250.0                       # the drawer fully out (the sequence's last frame)

# --- The cabinet (mm) -------------------------------------------------------------------------------------------
LAYOUTS = {
    "portrait": {"cols": 2, "rows": 4, "rail": 114.0, "width_px": 1170},   # a two-line name, 11 px, at 390 px wide
    "landscape": {"cols": 4, "rows": 2, "rail": 56.0, "width_px": 2880},
}
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM, GAP_X = 26.0, 26.0, 26.0, 20.0
CABINET_DEPTH = 340.0
ROOM = 0.035                           # the black room around the cabinet in the plate, as a fraction of its width
GLOW_MM = 16.0                         # how far the seam light reads beyond the front: the dark crops cover it

# --- The drawer view's camera -----------------------------------------------------------------------------------
VIEW_ASPECT = (1200, 1500)
VIEW_FRONT_FRACTION = 0.84             # frame 0: the drawer front spans this much of the view's width
VIEW_CENTER_Y = 0.46                   # frame 0: the front's centre sits here, from the top


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


# --- Materials ---------------------------------------------------------------------------------------------------
def principled(name, base, rough, metallic=0.0, spec=0.5, coat=0.0, coat_rough=0.3, sheen=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = coat_rough
    b.inputs["Sheen Weight"].default_value = sheen
    return m


def calfskin(name, col=(0.0065, 0.0063, 0.006)):
    """Black calfskin, the prototype's: a fine irregular pebble (Voronoi distance to edge), a coarser crease (noise),
    a satin sheen with soft mottling in the roughness; every texture read in world space (the Geometry node's
    Position), so no two drawers carry the same grain."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Specular IOR Level"].default_value = 0.55
    b.inputs["Sheen Weight"].default_value = 0.08
    b.inputs["Sheen Roughness"].default_value = 0.4
    b.inputs["Coat Weight"].default_value = 0.15
    b.inputs["Coat Roughness"].default_value = 0.3
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    # the grain is fixed to the leather, not to the room: the world position less the object's `slide` (a property
    # build_drawer sets on the parts that move with a drawer; absent, so zero, on everything else). No two drawers
    # match, as in world space, and a sliding front keeps its grain from frame to frame instead of crawling
    slide = nt.nodes.new("ShaderNodeAttribute")
    slide.attribute_type = "OBJECT"
    slide.attribute_name = "slide"
    anchored = nt.nodes.new("ShaderNodeVectorMath")
    anchored.operation = "SUBTRACT"
    nt.links.new(geo.outputs["Position"], anchored.inputs[0])
    nt.links.new(slide.outputs["Vector"], anchored.inputs[1])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 650.0
    vor.inputs["Randomness"].default_value = 1.0
    vor.feature = "DISTANCE_TO_EDGE"
    noi = nt.nodes.new("ShaderNodeTexNoise")
    noi.inputs["Scale"].default_value = 90.0
    noi.inputs["Detail"].default_value = 8.0
    noi.inputs["Roughness"].default_value = 0.65
    big = nt.nodes.new("ShaderNodeTexNoise")
    big.inputs["Scale"].default_value = 18.0
    big.inputs["Detail"].default_value = 3.0
    for t in (vor, noi, big):
        nt.links.new(anchored.outputs["Vector"], t.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs[0].default_value = 0.4
    nt.links.new(vor.outputs["Distance"], mix.inputs[2])
    nt.links.new(noi.outputs["Fac"], mix.inputs[3])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.8
    bump.inputs["Distance"].default_value = 0.0007
    nt.links.new(mix.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.30
    rr.inputs["To Max"].default_value = 0.62
    nt.links.new(big.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    return m


def suede(name="suede", col=(0.0034, 0.0023, 0.0015)):
    """The drawer's lining: a warm brown-black suede, matte with a soft nap (a little sheen, a fine world-space
    noise in the roughness)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = 0.95
    b.inputs["Specular IOR Level"].default_value = 0.08
    b.inputs["Sheen Weight"].default_value = 0.10
    b.inputs["Sheen Roughness"].default_value = 0.7
    b.inputs["Sheen Tint"].default_value = (0.9, 0.75, 0.55, 1)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    noi = nt.nodes.new("ShaderNodeTexNoise")
    noi.inputs["Scale"].default_value = 900.0
    noi.inputs["Detail"].default_value = 4.0
    nt.links.new(geo.outputs["Position"], noi.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.0002
    nt.links.new(noi.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def emission(name, col, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


def knob_materials(style):
    """The knob's GCD materials per style (O15): black relief (metal and stone both black, read by light), gold (the
    frames' own gold and onyx), plain (no GCD)."""
    if style == "gold":
        return {"gold": principled("knob gcd gold", (0.565, 0.366, 0.145), 0.22, metallic=1.0),
                "onyx": principled("knob gcd onyx", (0.006, 0.006, 0.006), 0.04)}
    return {"gold": principled("knob gcd black metal", (0.02, 0.02, 0.021), 0.28, metallic=1.0),
            "onyx": principled("knob gcd black stone", (0.004, 0.004, 0.0045), 0.06)}


class Materials:
    def __init__(self, knob_style):
        self.front = calfskin("calf front")
        self.cabinet = calfskin("calf cabinet", (0.0045, 0.0044, 0.0042))
        self.cord = calfskin("calf cord", (0.006, 0.006, 0.006))
        self.suede = suede()
        self.box = principled("box", (0.012, 0.0095, 0.007), 0.75, spec=0.25)
        self.carcass = principled("carcass", (0.004, 0.004, 0.004), 0.9, spec=0.1)
        self.knob = principled("knob", (0.02, 0.02, 0.02), 0.22, spec=0.6)
        self.gcd = knob_materials(knob_style)
        self.seam = emission("seam glow", (1.0, 0.62, 0.30), 0.7)
        self.seam_dark = principled("seam dark", (0.004, 0.004, 0.004), 0.9, spec=0.05)


# --- Geometry ----------------------------------------------------------------------------------------------------
def box(name, x0, x1, y0, y1, z0, z1, mat, parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    ob = bpy.context.object
    ob.name = name
    ob.scale = (x1 - x0, y1 - y0, z1 - z0)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bv = ob.modifiers.new("bv", "BEVEL")
        bv.width = bevel
        bv.segments = 3
    ob.data.materials.append(mat)
    if parent:
        ob.parent = parent
    return ob


def cylinder(name, radius, depth, location, rotation, mat, vertices=96, parent=None, bevel=0.0, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation, vertices=vertices)
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(mat)
    if bevel:
        bv = ob.modifiers.new("bv", "BEVEL")
        bv.width = bevel
        bv.segments = 5
    if smooth:
        bpy.ops.object.shade_smooth()
    if parent:
        ob.parent = parent
    return ob


def slot_centre(layout, col, row):
    """The centre of a drawer's front (x, z) in metres for a slot of the layout; the cabinet's face is y = 0 and
    its outer top-left corner sits at (-W/2, +H/2) about the origin."""
    L = LAYOUTS[layout]
    W, H = cabinet_size(layout)
    x = -W / 2 + MARGIN_X + DRAWER_W / 2 + col * (DRAWER_W + GAP_X)
    z = H / 2 - MARGIN_TOP - DRAWER_H / 2 - row * (DRAWER_H + L["rail"])
    return x * MM, z * MM


def cabinet_size(layout):
    L = LAYOUTS[layout]
    W = 2 * MARGIN_X + L["cols"] * DRAWER_W + (L["cols"] - 1) * GAP_X
    H = MARGIN_TOP + L["rows"] * (DRAWER_H + L["rail"]) + MARGIN_BOTTOM
    return W, H


def build_drawer(name, mats, centre, ext_mm=0.0, lit=True, with_gcd=True, frame_parts=None):
    """One drawer at `centre` (x, z, metres; the front flush with the cabinet's face when shut), pulled `ext_mm`
    toward the viewer. Returns the drawer's root (an empty: move it to slide the drawer) and the knob's pivot."""
    cx, cz = centre
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root.location = (cx, -ext_mm * MM, cz)
    w, h = DRAWER_W * MM / 2, DRAWER_H * MM / 2
    t = FRONT_T * MM
    # the front: calfskin, bevelled, its face at y = 0 (local), its back at y = t
    slide = [0.0, -ext_mm * MM, 0.0]                # how far the drawer's parts have moved from rest (the grain stays with them)
    front = box(f"{name} front", -w, w, 0.0, t, -h, h, mats.front, root, FRONT_BEVEL * MM)
    front["slide"] = slide
    for zz in (h - CORD_INSET * MM, -h + CORD_INSET * MM):
        cord = cylinder(f"{name} cord", CORD_R * MM, DRAWER_W * MM - 2 * FRONT_BEVEL * MM, (0, -0.0002, zz), (0, math.radians(90), 0), mats.cord, 24, root)
        cord["slide"] = slide
    # the box behind the front: suede floor and walls inside, dark wood outside
    bw = w - BOX_WALL * MM
    zb = -h + 10 * MM                               # the floor's top, a little above the front's bottom
    box(f"{name} floor", -bw, bw, t, t + BOX_DEPTH * MM, zb - FLOOR_T * MM, zb, mats.suede, root)
    for s in (-1, 1):
        box(f"{name} side", s * bw - (BOX_WALL * MM if s < 0 else 0), s * bw + (BOX_WALL * MM if s > 0 else 0),
            t, t + BOX_DEPTH * MM, zb - FLOOR_T * MM, zb + BOX_H * MM, mats.suede, root)
    box(f"{name} back", -w + 2 * MM, w - 2 * MM, t + BOX_DEPTH * MM - BOX_WALL * MM, t + BOX_DEPTH * MM, zb - FLOOR_T * MM, zb + BOX_H * MM, mats.suede, root)
    # the knob: a blackened cylinder on a pivot at the front's face, tilted up toward the viewer
    pivot = bpy.data.objects.new(f"{name} pivot", None)
    bpy.context.scene.collection.objects.link(pivot)
    pivot.parent = root
    pivot.location = (0, 0, 0)
    pivot.rotation_euler = (math.radians(-KNOB_TILT), 0, 0)
    knob = cylinder(f"{name} knob", KNOB_D * MM / 2, KNOB_DEPTH * MM, (0, -KNOB_DEPTH * MM / 2, 0), (math.radians(90), 0, 0), mats.knob, 96, pivot, 2.5 * MM)
    knob.matrix_parent_inverse = Matrix.Identity(4)
    if with_gcd:
        face_y = -KNOB_DEPTH * MM
        for g in frame3d.gcd_parts(f"{name} knob", mats.gcd, GCD_MM, (0, face_y / MM, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0), proud=0.6):
            g.parent = pivot
            g.matrix_parent_inverse = Matrix.Identity(4)
    # the seam light: a warm area light inside the box just behind the front, and a faint glow on the box's lip
    if lit:
        # the light the frame waits in: a warm pool on the suede from a small source under the box's top edge,
        # behind the front, pointing down and a little forward
        L = bpy.data.lights.new(f"{name} seam", "AREA")
        L.shape = "RECTANGLE"
        L.size = 90 * MM
        L.size_y = 50 * MM
        L.energy = 0.42
        L.color = (1.0, 0.66, 0.36)
        L.spread = math.radians(110)
        lob = bpy.data.objects.new(f"{name} seam light", L)
        bpy.context.scene.collection.objects.link(lob)
        lob.parent = root
        lob.location = (0, t + 60 * MM, zb + BOX_H * MM - 4 * MM)
        lob.rotation_euler = (Vector((0, t + 150 * MM, zb)) - Vector(lob.location)).to_track_quat("-Z", "Y").to_euler()
    # the seam light's glow: the opening's walls, just behind the face, carry a faint warm emission when the drawer is
    # lit, and stay dark otherwise (the light is state, never decoration)
    sm = mats.seam if lit else mats.seam_dark
    g = GAP * MM
    sd = 0.5 * MM                                   # the strip's thickness, flush with the opening's wall
    y0s, y1s = 1.0 * MM, 14.0 * MM
    fixed = bpy.data.objects.new(f"{name} opening", None)   # the opening is the cabinet's: it does not slide
    bpy.context.scene.collection.objects.link(fixed)
    fixed.location = (cx, 0, cz)
    box(f"{name} seam top", -w - g, w + g, y0s, y1s, h + g - sd, h + g, sm, fixed)
    box(f"{name} seam bottom", -w - g, w + g, y0s, y1s, -h - g, -h - g + sd, sm, fixed)
    box(f"{name} seam left", -w - g, -w - g + sd, y0s, y1s, -h - g, h + g, sm, fixed)
    box(f"{name} seam right", w + g - sd, w + g, y0s, y1s, -h - g, h + g, sm, fixed)
    # the frame inside, upright on the suede, temples open, front toward the viewer
    if frame_parts:
        rig, lo, hi = frame_parts
        rig.parent = root
        fy = t + (BOX_DEPTH * MM - (hi[1] - lo[1])) / 2 - lo[1]
        rig.location = (-(lo[0] + hi[0]) / 2, fy, zb - lo[2] + 0.0002)
    return root, pivot


def build_frame(frame_id, tint=(0.06, 0.06, 0.065)):
    """A frame from frame3d, upright (y up → z up), its front toward -y; returns the rig and its bounds (metres,
    the rig at the origin)."""
    mats = frame3d.materials_for(frame_id, tint)
    parts, sh, hinges = frame3d.build(frame_id, mats)
    parts += frame3d.temples(frame_id, hinges, mats)
    rig = bpy.data.objects.new(f"{frame_id} rig", None)
    bpy.context.scene.collection.objects.link(rig)
    for p in parts:
        p.parent = rig
    rig.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.view_layer.update()
    lo = np.array([1e9] * 3)
    hi = -lo.copy()
    for p in parts:
        co = np.array([p.matrix_world @ Vector(v.co) for v in p.data.vertices])
        lo = np.minimum(lo, co.min(0))
        hi = np.maximum(hi, co.max(0))
    return rig, lo, hi, parts


def build_cabinet(layout, mats, drawers_lit, knob_style, exts=None, frame_parts=None, frame_slot=None):
    """The whole cabinet for a layout: the calfskin face with an opening per drawer (a seam round each front), the
    dark carcass behind, the drawers in their slots. `drawers_lit[i]` is each drawer's seam light; `exts[i]` its
    pull in mm. Returns the drawer roots and the geometry of each slot for rects.json."""
    L = LAYOUTS[layout]
    W, H = cabinet_size(layout)
    Wm, Hm = W * MM, H * MM
    D = CABINET_DEPTH * MM
    slots = []
    for row in range(L["rows"]):
        for col in range(L["cols"]):
            slots.append(slot_centre(layout, col, row))
    # the face as four boxes around each opening would multiply quickly; instead one face slab with the openings
    # cut by a boolean, then the carcass behind
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, D / 2, 0))
    face = bpy.context.object
    face.name = "cabinet"
    face.scale = (Wm, D, Hm)
    bpy.ops.object.transform_apply(scale=True)
    face.data.materials.append(mats.cabinet)
    ow, oh = (DRAWER_W + 2 * GAP) * MM / 2, (DRAWER_H + 2 * GAP) * MM / 2
    cutters = []
    for i, (cx, cz) in enumerate(slots):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, (D - 0.01) / 2 + 0.005 - 0.02, cz))
        c = bpy.context.object
        c.name = f"cut {i}"
        c.scale = (2 * ow, D + 0.04, 2 * oh)
        bpy.ops.object.transform_apply(scale=True)
        c.display_type = "WIRE"
        c.hide_render = True
        cutters.append(c)
    for c in cutters:
        m = face.modifiers.new("cut", "BOOLEAN")
        m.operation = "DIFFERENCE"
        m.object = c
        m.solver = "EXACT"
    bpy.context.view_layer.objects.active = face
    for m in list(face.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    for c in cutters:
        bpy.data.objects.remove(c)
    bv = face.modifiers.new("bv", "BEVEL")
    bv.width = 2.0 * MM
    bv.segments = 2
    bv.limit_method = "ANGLE"
    # the dark inside of each opening: a lining box (the seam's walls) so the gap shows the box, not the room
    roots = []
    for i, (cx, cz) in enumerate(slots):
        lit = drawers_lit[i]
        ext = (exts or [0.0] * len(slots))[i]
        root, pivot = build_drawer(f"drawer {i:02d}", mats, (cx, cz), ext, lit, with_gcd=knob_style != "plain",
                                   frame_parts=frame_parts if frame_slot == i else None)
        roots.append(root)
    return roots, slots, (W, H)


# --- Lights, camera, scene ---------------------------------------------------------------------------------------
def area(name, loc, target, size, energy, color, size_y=None, spread=None):
    L = bpy.data.lights.new(name, "AREA")
    L.shape = "RECTANGLE"
    L.size = size
    L.size_y = size_y or size
    L.energy = energy
    L.color = color
    if spread is not None:
        L.spread = math.radians(spread)
    ob = bpy.data.objects.new(name, L)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


def room_lights(W_m, H_m, scale=1.0):
    """The room's light on the cabinet (DRAWER-WALL.md, "The wall"): a broad soft source over the wall, a low warm
    rake from the left so the grain reads, a cool grey-green fill from in front."""
    area("over", (0, -0.55 * W_m - 0.2, H_m * 0.5 + 0.9), (0, 0.05, 0), 1.6 * W_m, 12 * scale, (0.86, 0.93, 0.90), size_y=0.35)
    area("rake", (-0.9 * W_m - 0.25, -0.22, -H_m * 0.35), (0, 0.02, -H_m * 0.1), 0.08, 4.0 * scale, (1.0, 0.88, 0.72), size_y=1.6 * H_m, spread=120)
    area("fill", (0.25 * W_m, -1.3 * W_m - 0.4, 0.05), (0, 0, 0), 1.8 * W_m, 1.5 * scale, (0.80, 0.90, 0.86), size_y=1.6 * H_m)
    area("glint", (0.15 * W_m, -0.9 * W_m, H_m * 0.5 + 0.5), (0, 0, -H_m * 0.05), 0.05, 2.2 * scale, (1.0, 0.95, 0.86), size_y=0.05)


def new_scene(samples, size, denoise=True):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = denoise
    sc.cycles.seed = 7
    sc.render.resolution_x, sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "16"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    return sc


def ortho_camera(sc, W_m, H_m, tilt_deg=15.0):
    """The wall's camera: orthographic, tilted 15 degrees down, framing the cabinet with the room around it. Returns
    the camera and the plate's size in metres (its ortho width and height)."""
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    tilt = math.radians(tilt_deg)
    plate_w = W_m * (1 + 2 * ROOM)
    # the cabinet's face is foreshortened by the tilt and its top shows above the face by the depth's sine; the two
    # together sit centred on the plate, with the same black room above and below as beside, so the plate's edges
    # hold nothing but the room (drawer_wall.py check measures the renders for that)
    top = CABINET_DEPTH * MM * math.sin(tilt)
    plate_h = H_m * math.cos(tilt) + top + 2 * ROOM * W_m
    cam.data.sensor_fit = "HORIZONTAL" if plate_w >= plate_h else "VERTICAL"
    cam.data.ortho_scale = plate_w if plate_w >= plate_h else plate_h
    cam.data.clip_start, cam.data.clip_end = 0.01, 20.0
    dist = 3.0
    up = Vector((0, math.sin(tilt), math.cos(tilt)))                   # the camera's up, on the plate
    cam.location = Vector((0, -dist * math.cos(tilt), dist * math.sin(tilt))) + up * (top / 2)
    cam.rotation_euler = (math.radians(90) - tilt, 0, 0)
    return cam, (plate_w, plate_h)


def project(sc, cam, p):
    """A world point to plate coordinates (0..1 from the top-left)."""
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()      # the camera's world matrix, in case it was just placed
    v = world_to_camera_view(sc, cam, Vector(p))
    return (float(v.x), float(1 - v.y))


def rects_for(sc, cam, slots, W, H, layout):
    """Each drawer's face, knob, label and crop rects in % of the plate, from the geometry."""
    L = LAYOUTS[layout]
    out = []
    w, h = DRAWER_W * MM / 2, DRAWER_H * MM / 2
    for i, (cx, cz) in enumerate(slots):
        def rect(points):
            uv = [project(sc, cam, p) for p in points]
            xs = [u for u, _ in uv]
            ys = [v for _, v in uv]
            return {"x": round(min(xs) * 100, 4), "y": round(min(ys) * 100, 4), "w": round((max(xs) - min(xs)) * 100, 4), "h": round((max(ys) - min(ys)) * 100, 4)}
        face = rect([(cx + sx * w, 0, cz + sz * h) for sx in (-1, 1) for sz in (-1, 1)])
        r = KNOB_D * MM / 2
        kd = KNOB_DEPTH * MM
        tilt = math.radians(KNOB_TILT)
        knob_pts = []
        for ang in np.linspace(0, 2 * math.pi, 24, endpoint=False):
            for dy in (0, -kd):
                # the knob's circle in the pivot's tilted frame: local (x, y, z) → world
                lx, ly, lz = r * math.cos(ang), dy, r * math.sin(ang)
                wy = ly * math.cos(tilt) - lz * math.sin(tilt)
                wz = ly * math.sin(tilt) + lz * math.cos(tilt)
                knob_pts.append((cx + lx, wy, cz + wz))
        knob = rect(knob_pts)
        rail = L["rail"] * MM
        label = rect([(cx - w, 0, cz - h - 5 * MM), (cx + w, 0, cz - h - 5 * MM), (cx - w, 0, cz - h - rail + 5 * MM), (cx + w, 0, cz - h - rail + 5 * MM)])
        g = GLOW_MM * MM
        crop = rect([(cx + sx * (w + g), 0, cz + sz * (h + g)) for sx in (-1, 1) for sz in (-1, 1)])
        out.append({"index": i, "col": i % L["cols"], "row": i // L["cols"], "face": face, "knob": knob, "label": label, "crop": crop})
    return out


def render(sc, path, border=None):
    """Render to `path` (16-bit PNG). `border`: (x0, y0, x1, y1) in 0..1 of the frame renders that region only and
    crops the output to it."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if border:
        sc.render.use_border = True
        sc.render.use_crop_to_border = True
        sc.render.border_min_x, sc.render.border_max_x = border[0], border[2]
        sc.render.border_min_y, sc.render.border_max_y = 1 - border[3], 1 - border[1]
    else:
        sc.render.use_border = False
    sc.render.filepath = str(path)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"rendered {path} in {time.time() - t:.0f}s", flush=True)


# --- Commands ----------------------------------------------------------------------------------------------------
def cmd_wall(a):
    L = LAYOUTS[a.layout]
    n = L["cols"] * L["rows"]
    mats_probe = cabinet_size(a.layout)
    W_m, H_m = mats_probe[0] * MM, mats_probe[1] * MM
    sc = new_scene(a.samples, (16, 16), denoise=True)
    mats = Materials(a.knob)
    lit = [a.variant == "lit"] * n
    roots, slots, (W, H) = build_cabinet(a.layout, mats, lit, a.knob)
    room_lights(W_m, H_m, a.light)
    cam, (pw, ph) = ortho_camera(sc, W_m, H_m)
    width = a.size or L["width_px"]
    height = int(round(width * ph / pw))
    sc.render.resolution_x, sc.render.resolution_y = width, height
    out = pathlib.Path(a.out) if a.out else WORK / f"{a.layout}-{a.knob}-{a.variant}.png"
    rects = {"layout": a.layout, "knob": a.knob, "plate": {"width": width, "height": height, "cabinetMm": [W, H]},
             "view": {"frontFraction": VIEW_FRONT_FRACTION, "centerY": VIEW_CENTER_Y, "aspect": list(VIEW_ASPECT)},
             "drawers": rects_for(sc, cam, slots, W, H, a.layout)}
    (out.with_suffix(".rects.json")).parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".rects.json").write_text(json.dumps(rects, indent=1))
    if a.dry:
        print(json.dumps(rects["plate"]), f"{n} drawers")
        return
    render(sc, out)


def view_camera(sc, t, slot_centre_m, lens0=200.0, lens1=68.0):
    """The drawer view's camera at progress t (0: as the wall sees the drawer, 15 degrees down, a long lens, far back;
    1: leaning in, about 40 degrees down, 68 mm, f/4, looking into the drawer). Perspective, 4:5."""
    cx, cz = slot_centre_m
    s = smoothstep(t)
    tilt = math.radians(15 + (40 - 15) * s)
    lens = lens0 + (lens1 - lens0) * s
    cam = sc.camera
    cam.data.type = "PERSP"
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36.0
    cam.data.lens = lens
    # the aim: the front's centre at t=0, the drawer's interior (its middle, at the floor) at t=1
    aim0 = Vector((cx, 0.0, cz))
    aim1 = Vector((cx, -FULL_EXT * MM + (FRONT_T + BOX_DEPTH * 0.40) * MM, cz - DRAWER_H * MM / 2 + 34 * MM))
    aim = aim0.lerp(aim1, s)
    # the distance that frames the front at VIEW_FRONT_FRACTION of the width at t=0, closing in toward t=1
    width0 = DRAWER_W * MM / VIEW_FRONT_FRACTION
    dist0 = width0 * lens0 / 36.0
    dist1 = 0.62
    dist = dist0 + (dist1 - dist0) * s
    back = Vector((0, -math.cos(tilt), math.sin(tilt)))
    # at t=0 the front's centre sits at VIEW_CENTER_Y from the top: shift the aim down the view a little
    view_h0 = width0 * VIEW_ASPECT[1] / VIEW_ASPECT[0]
    aim = aim + Vector((0, 0, (0.5 - VIEW_CENTER_Y) * view_h0)) * (1 - s)
    cam.location = aim + back * dist
    cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 11.0 + (4.0 - 11.0) * s
    cam.data.dof.focus_distance = dist
    cam.data.clip_start = 0.02
    return cam


def cmd_sequence(a):
    """The drawer view: one drawer of the portrait wall (its neighbours in place), sliding from shut to 250 mm out
    over `frames` frames (eased at both ends), the camera moving with it."""
    layout = "portrait"
    L = LAYOUTS[layout]
    n = L["cols"] * L["rows"]
    slot = a.slot
    W_m, H_m = [v * MM for v in cabinet_size(layout)]
    frames = list(range(a.frames)) if not a.only else [int(x) for x in a.only.split(",")]
    if a.mesh_step and a.frame:
        frame3d.FRAMES[a.frame]["mesh_step"] = a.mesh_step
    for i in frames:
        t = i / (a.frames - 1)
        ext = FULL_EXT * smoothstep(t)
        size = (a.size, int(round(a.size * VIEW_ASPECT[1] / VIEW_ASPECT[0]))) if a.size else VIEW_ASPECT
        sc = new_scene(a.samples, size, denoise=True)
        mats = Materials(a.knob)
        frame_parts = None
        if a.frame and not a.dry:
            rig, lo, hi, parts = build_frame(a.frame, tuple(a.tint))
            frame_parts = (rig, lo, hi)
        exts = [0.0] * n
        exts[slot] = ext
        if a.dry:
            # nothing built: the camera and the region come from the slot's geometry alone
            slots = [slot_centre(layout, c, r) for r in range(L["rows"]) for c in range(L["cols"])]
            roots = [None] * n
        else:
            roots, slots, (W, H) = build_cabinet(layout, mats, [True] * n, a.knob, exts, frame_parts, slot)
            room_lights(W_m, H_m, a.light)
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
        sc.collection.objects.link(cam)
        sc.camera = cam
        view_camera(sc, t, slots[slot])
        name = a.frame or "base"
        out = pathlib.Path(a.out) if a.out else WORK / "seq" / name
        border = None
        if a.region and a.frame:
            border = interior_region(sc, cam, roots[slot], slots[slot], ext)
            if border is None:
                print(f"frame {i:03d}: the interior is not visible yet; skipped", flush=True)
                continue
            (out / f"{i:03d}.region.json").parent.mkdir(parents=True, exist_ok=True)
            (out / f"{i:03d}.region.json").write_text(json.dumps({"border": border, "ext_mm": ext}))
        if a.dry:
            print(f"frame {i:03d}: ext {ext:.1f} mm, lens {cam.data.lens:.0f} mm, f/{cam.data.dof.aperture_fstop:.1f}, cam {tuple(round(v, 3) for v in cam.location)}, border {border}")
            continue
        render(sc, out / (f"{i:03d}.region.png" if border else f"{i:03d}.png"), border)
        if i == a.frames - 1 and not a.frame:
            write_cameras(sc, cam, roots[slot], slots[slot], out.parent)


def interior_region(sc, cam, root, centre, ext_mm):
    """The part of the view where the drawer's interior (and a frame in it) can show, in 0..1 of the frame, with a
    margin for the 8 px feather; None while the drawer is shut enough that nothing inside shows."""
    if ext_mm < 6.0:
        return None
    cx, cz = centre
    w = DRAWER_W * MM / 2
    zb = -DRAWER_H * MM / 2 + 10 * MM
    y0 = -ext_mm * MM + FRONT_T * MM
    pts = [(cx + sx * w, y, cz + z) for sx in (-1, 1) for y in (y0, y0 + BOX_DEPTH * MM) for z in (zb, zb + BOX_H * MM)]
    pts += [(cx + sx * w, -ext_mm * MM, cz + z) for sx in (-1, 1) for z in (-DRAWER_H * MM / 2, DRAWER_H * MM / 2)]
    uv = [project(sc, cam, p) for p in pts]
    m = 0.02
    x0 = max(0.0, min(u for u, _ in uv) - m)
    x1 = min(1.0, max(u for u, _ in uv) + m)
    y0_ = max(0.0, min(v for _, v in uv) - m)
    y1 = min(1.0, max(v for _, v in uv) + m)
    if x1 <= x0 or y1 <= y0_:
        return None
    return [round(x0, 4), round(y0_, 4), round(x1, 4), round(y1, 4)]


def y_up(v):
    return [float(v[0]), float(v[2]), -float(v[1])]


def matrix_y_up(m):
    """A Blender world matrix (Z up) as a three.js one (Y up): columns in the Y-up basis."""
    R = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    out = R @ m @ R.inverted()
    return [[float(out[r][c]) for c in range(4)] for r in range(4)]


LIFT_UP_M, LIFT_TOWARD_M, LIFT_YAW_DEG = 0.13, 0.12, 35.0   # the lifted pose: up, toward the camera, turned to a three-quarter view
LIFT_KEY_W, LIFT_RIM_W = 12.0, 3.0                           # the lifted frame's own light: a warm key from the side, a cool rim from above
LIFT_LEAN_SHORT_DEG = 8.0
CAMERA_TINT = (0.0443, 0.0444, 0.0567)         # the bounds do not depend on the tint; F09's, for the build


def frame_place(centre, lo, hi):
    """Where build_drawer puts a frame rig in a drawer open to FULL_EXT (world, metres), by the same arithmetic: the
    frame's bounding box centred across the drawer and in the box's depth, its bottom on the suede."""
    cx, cz = centre
    t = FRONT_T * MM
    zb = -DRAWER_H * MM / 2 + 10 * MM
    fy = t + (BOX_DEPTH * MM - (hi[1] - lo[1])) / 2 - lo[1]
    return Vector((cx - (lo[0] + hi[0]) / 2, -FULL_EXT * MM + fy, cz + zb - lo[2] + 0.0002))


def frame_poses(cam, centre, lo, hi):
    """The open pose (resting in the drawer) and the lifted pose as Blender world matrices. Lifted: the frame turns
    about its own centre, 35 degrees about the vertical so the wearer's right (the GCD's side, the frame's -x) comes
    to the camera, and tilts about the camera's right by the camera's own downward angle so its front faces the lens;
    then it rises 130 mm and comes 120 mm toward the camera."""
    open_loc = frame_place(centre, lo, hi)
    upright = Euler((math.radians(90), 0, 0)).to_matrix().to_4x4()
    open_m = Matrix.Translation(open_loc) @ upright
    pivot = open_loc + Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2))   # the frame's centre, open
    toward = cam.location - pivot
    toward.z = 0
    toward.normalize()
    cam_right = Vector((0, 0, 1)).cross(toward)
    fwd = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))               # how far the camera looks down, from its forward axis
    tilt = math.asin(max(-1.0, min(1.0, -fwd.z)))
    lift = Vector((0, 0, LIFT_UP_M)) + toward * LIFT_TOWARD_M
    # Rz(+35) takes the frame's -x, (-1, 0, 0), to (-0.82, -0.57, 0): toward -y, where the camera is. A negative turn
    # about the camera's right (+x for a camera at -y) leans the top away from the camera, which turns the front's
    # normal (-y) upward: by the camera's own angle it points straight back up the line of sight
    lean = -(tilt - math.radians(LIFT_LEAN_SHORT_DEG))              # negative about the camera's right: the top leans away, the front looks up at the lens
    lift_m = (Matrix.Translation(lift + pivot) @ Matrix.Rotation(lean, 4, cam_right) @ Matrix.Rotation(math.radians(LIFT_YAW_DEG), 4, "Z")
              @ Matrix.Translation(-pivot) @ open_m)
    return open_m, lift_m


def pose_json(m):
    return {"matrix_blender": [[float(m[r][c]) for c in range(4)] for r in range(4)], "matrix_three": matrix_y_up(m),
            "position_blender": [float(v) for v in m.to_translation()], "position_three": y_up(m.to_translation())}


def write_cameras(sc, cam, root, centre, outdir, frame_ids=None, mesh_step=4, default="F09"):
    """camera/open.json: the last frame's camera and, for every frame, its transform resting in the drawer (where
    build_drawer put it in the render); camera/inspect.json: the same camera and every frame's lifted pose. Each frame
    is built (at `mesh_step`) for its bounds, then removed."""
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    fov = 2 * math.degrees(math.atan((36.0 / 2) * (VIEW_ASPECT[1] / VIEW_ASPECT[0]) / cam.data.lens))
    camj = {"lens_mm": cam.data.lens, "sensor_width_mm": 36.0, "fit": "HORIZONTAL", "resolution": list(VIEW_ASPECT),
            "fstop": cam.data.dof.aperture_fstop, "focus_distance_m": cam.data.dof.focus_distance,
            "position": list(map(float, cam.location)), "rotation_euler_xyz_rad": list(map(float, cam.rotation_euler)),
            "three": {"position": y_up(cam.location), "fov_deg": fov, "near": 0.02, "far": 10.0,
                      "quaternion_xyzw": quaternion_y_up(cam.matrix_world.to_quaternion())}}
    cx, cz = centre
    zb = cz - DRAWER_H * MM / 2 + 10 * MM
    placement = {"note": "the rule build_drawer places a frame by: its bounding box centred on x, centred in the box's depth, its bottom on the suede; Blender Z up, metres",
                 "x_m": float(cx), "y_box_front_m": float(-FULL_EXT * MM + FRONT_T * MM), "y_box_back_m": float(-FULL_EXT * MM + FRONT_T * MM + BOX_DEPTH * MM),
                 "z_floor_m": float(zb), "three": {"x": float(cx), "y_floor": float(zb), "z_box_front": float(FULL_EXT * MM - FRONT_T * MM), "z_box_back": float(FULL_EXT * MM - FRONT_T * MM - BOX_DEPTH * MM)}}
    opens, lifts = {}, {}
    for fid in frame_ids or sorted(frame3d.FRAMES):
        was = frame3d.FRAMES[fid].get("mesh_step")
        frame3d.FRAMES[fid]["mesh_step"] = mesh_step
        rig, lo, hi, parts = build_frame(fid, CAMERA_TINT)
        if was is None:
            frame3d.FRAMES[fid].pop("mesh_step", None)
        else:
            frame3d.FRAMES[fid]["mesh_step"] = was
        open_m, lift_m = frame_poses(cam, centre, lo, hi)
        opens[fid] = pose_json(open_m)
        opens[fid]["bounds_mm"] = {"lo": [float(v) / MM for v in lo], "hi": [float(v) / MM for v in hi]}
        lifts[fid] = pose_json(lift_m)
        for ob in list(parts) + [rig]:
            bpy.data.objects.remove(ob, do_unlink=True)
    (outdir / "open.json").write_text(json.dumps({
        "camera": camj, "placement": placement,
        "frame": {"note": f"{default}'s resting pose (the `frames` entry); the rig's origin is the frame's bounding-box centre on x, its y as frame3d builds it, its bottom on z",
                  **opens[default]},
        "frames": opens}, indent=1))
    (outdir / "inspect.json").write_text(json.dumps({
        "camera": camj,
        "frame": {"note": f"{default}'s lifted pose (the `frames` entry): turned {LIFT_YAW_DEG:.0f} degrees about its centre to a three-quarter view and tilted to face the camera, {LIFT_UP_M * 1000:.0f} mm up and {LIFT_TOWARD_M * 1000:.0f} mm toward the camera",
                  **lifts[default]},
        "frames": lifts}, indent=1))
    print("wrote", outdir / "open.json", outdir / "inspect.json", f"({len(opens)} frames)", flush=True)


def quaternion_y_up(q):
    """A Blender rotation (Z up) as a three.js quaternion (Y up), x y z w."""
    R = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))
    m = R @ q.to_matrix() @ R.inverted()
    qq = m.to_quaternion()
    return [float(qq.x), float(qq.y), float(qq.z), float(qq.w)]


def cmd_knob(a):
    """A close-up of one knob in a knob style, for O15: the drawer shut, 20 degrees down, 100 mm."""
    layout = "portrait"
    L = LAYOUTS[layout]
    n = L["cols"] * L["rows"]
    W_m, H_m = [v * MM for v in cabinet_size(layout)]
    sc = new_scene(a.samples, (a.size, a.size), denoise=True)
    mats = Materials(a.knob)
    roots, slots, _ = build_cabinet(layout, mats, [True] * n, a.knob)
    room_lights(W_m, H_m, a.light)
    cx, cz = slots[a.slot]
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.lens = 100.0
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36.0
    aim = Vector((cx, -KNOB_DEPTH * MM * 0.6, cz))
    tilt = math.radians(20)
    dist = 0.42
    cam.location = aim + Vector((0.06, -math.cos(tilt) * dist, math.sin(tilt) * dist))
    cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 5.6
    cam.data.dof.focus_distance = (aim - cam.location).length
    out = pathlib.Path(a.out) if a.out else WORK / f"knob-{a.knob}.png"
    render(sc, out)


def cmd_env(a):
    """The drawer scene's light from the lifted pose (DRAWER-WALL.md, Assets): an equirectangular capture at the
    lifted frame's centre, the drawer open, no frame; the live frame's environment."""
    layout = "portrait"
    L = LAYOUTS[layout]
    n = L["cols"] * L["rows"]
    W_m, H_m = [v * MM for v in cabinet_size(layout)]
    sc = new_scene(a.samples, (1024, 512), denoise=True)
    mats = Materials(a.knob)
    exts = [0.0] * n
    exts[a.slot] = FULL_EXT
    roots, slots, _ = build_cabinet(layout, mats, [True] * n, a.knob, exts)
    room_lights(W_m, H_m, a.light)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    view_camera(sc, 1.0, slots[a.slot])
    inspect = json.loads((pathlib.Path(a.cameras) / "inspect.json").read_text()) if a.cameras else None
    pos = Vector(inspect["frame"]["position_blender"]) if inspect else Vector((slots[a.slot][0], -FULL_EXT * MM + 0.17, slots[a.slot][1] + 0.08))
    pano = bpy.data.objects.new("pano", bpy.data.cameras.new("pano"))
    sc.collection.objects.link(pano)
    pano.data.type = "PANO"
    try:
        pano.data.panorama_type = "EQUIRECTANGULAR"
    except Exception:
        pano.data.cycles.panorama_type = "EQUIRECTANGULAR"
    pano.location = pos
    pano.rotation_euler = (math.radians(90), 0, 0)
    sc.camera = pano
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "16"
    sc.view_settings.view_transform = "Standard"
    out = pathlib.Path(a.out) if a.out else WORK / "env" / "drawer.exr"
    render(sc, out)
    # the .hdr next to it, through Blender's own reader (OpenCV here has no OpenEXR)
    import cv2
    im = bpy.data.images.load(str(out))
    im.colorspace_settings.name = "Non-Color"
    px = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], im.channels)[::-1, :, :3]
    cv2.imwrite(str(out.with_suffix(".hdr")), np.ascontiguousarray(px[..., ::-1]))
    print("wrote", out.with_suffix(".hdr"), "max", float(px.max()), "mean", float(px.mean()), flush=True)


def cmd_lifted(a):
    """A lifted still (DRAWER-WALL.md, The frames in 3D): the frame at the inspect pose in the drawer's light, from
    the view's last camera; the poster while the GLB loads and the view for tier 1. Needs camera/inspect.json."""
    layout = "portrait"
    L = LAYOUTS[layout]
    n = L["cols"] * L["rows"]
    W_m, H_m = [v * MM for v in cabinet_size(layout)]
    size = (a.size, int(round(a.size * VIEW_ASPECT[1] / VIEW_ASPECT[0])))
    sc = new_scene(a.samples, size, denoise=True)
    mats = Materials(a.knob)
    exts = [0.0] * n
    exts[a.slot] = FULL_EXT
    roots, slots, _ = build_cabinet(layout, mats, [True] * n, a.knob, exts)
    room_lights(W_m, H_m, a.light)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    view_camera(sc, 1.0, slots[a.slot])
    inspect = json.loads((pathlib.Path(a.cameras) / "inspect.json").read_text())
    if a.mesh_step:
        frame3d.FRAMES[a.frame]["mesh_step"] = a.mesh_step
    rig, lo, hi, parts = build_frame(a.frame, tuple(a.tint))
    pose = inspect.get("frames", {}).get(a.frame) or inspect["frame"]
    m = Matrix([row[:] for row in pose["matrix_blender"]])
    rig.matrix_world = m
    bpy.context.view_layer.update()
    # the still is the frame alone on transparency, over the view's dimmed drawer: the cabinet and the drawers stay
    # for the light they reflect and bounce but are invisible to the camera
    sc.render.film_transparent = True
    sc.cycles.film_transparent_glass = True        # what the lenses transmit counts toward alpha: the drawer shows through them, as in the live view
    sc.cycles.film_transparent_roughness = 0.2
    sc.render.image_settings.color_mode = "RGBA"
    frame_names = {p.name for p in parts}
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name not in frame_names:
            ob.visible_camera = False
            ob.visible_transmission = False     # nor through the lenses: the drawer shows through them from the view's own frame, as it does live
    # the lifted frame is what the camera focuses on
    centre = m @ Vector(((lo[0] + hi[0]) / 2, 0, (hi[2] - lo[2]) / 2))
    cam.data.dof.focus_distance = (centre - cam.location).length
    # the lifted frame's own light: the warm key from the drawer's side and a soft cool rim from above, as the live
    # frame gets them (the environment map plus one warm key)
    area("lift key", (slots[a.slot][0] + 0.20, -0.50, slots[a.slot][1] + 0.44), tuple(centre), 0.30, LIFT_KEY_W * a.light, (1.0, 0.86, 0.68), size_y=0.16)
    area("lift rim", (slots[a.slot][0] - 0.25, -0.05, slots[a.slot][1] + 0.40), tuple(centre), 0.05, LIFT_RIM_W * a.light, (0.86, 0.93, 1.0), size_y=0.5)
    out = pathlib.Path(a.out) if a.out else WORK / "stills" / f"{a.frame}-lifted.png"
    render(sc, out)


def cmd_cameras(a):
    """camera/open.json and camera/inspect.json without a render: the last frame's camera built the same way."""
    layout = "portrait"
    L = LAYOUTS[layout]
    n = L["cols"] * L["rows"]
    sc = new_scene(4, VIEW_ASPECT, denoise=False)
    mats = Materials(a.knob)
    exts = [0.0] * n
    exts[a.slot] = FULL_EXT
    roots, slots, _ = build_cabinet(layout, mats, [True] * n, a.knob, exts)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    view_camera(sc, 1.0, slots[a.slot])
    bpy.context.view_layer.update()
    write_cameras(sc, cam, roots[a.slot], slots[a.slot], pathlib.Path(a.out) if a.out else WORK / "camera", a.frames, a.mesh_step or 4)


def cmd_check(a):
    """The checks (DRAWER-WALL.md, The wall): rects match the geometry; the dark crops line up with the plate to the
    pixel; scene black at the edges; the knob GCD is 30 mm and on every knob (or absent for plain). Reads the web
    outputs in wall/assets/wall/<layout>/<knob>/ and the full dark render in work/wall/."""
    from PIL import Image
    import pillow_avif  # noqa: F401
    fails = []
    assets = ROOT / "wall" / "assets" / "wall" / a.layout / a.knob
    rects_path = assets / "rects.json"
    if not rects_path.exists():
        print(f"check: {rects_path} missing")
        return 1
    rects = json.loads(rects_path.read_text())
    L = LAYOUTS[a.layout]
    n = L["cols"] * L["rows"]
    # 1. rects against the geometry, rebuilt here
    W_m, H_m = [v * MM for v in cabinet_size(a.layout)]
    sc = new_scene(1, (16, 16), denoise=False)
    mats = Materials(a.knob)
    roots, slots, (W, H) = build_cabinet(a.layout, mats, [True] * n, a.knob)
    cam, (pw, ph) = ortho_camera(sc, W_m, H_m)
    width = rects["plate"]["width"]
    sc.render.resolution_x, sc.render.resolution_y = width, int(round(width * ph / pw))
    fresh = rects_for(sc, cam, slots, W, H, a.layout)
    for r0, r1 in zip(rects["drawers"], fresh):
        for key in ("face", "knob", "label", "crop"):
            for k in ("x", "y", "w", "h"):
                if abs(r0[key][k] - r1[key][k]) > 0.05:
                    fails.append(f"drawer {r0['index']} {key}.{k}: {r0[key][k]} in rects.json, {r1[key][k]} from the geometry")
    # 4. the knob GCD: 30 mm long, on every knob, or absent for plain
    gcd = [o for o in bpy.data.objects if "knob gcd gold" in o.name]
    if a.knob == "plain":
        if gcd:
            fails.append(f"{len(gcd)} knob GCDs on a plain wall")
    else:
        if len(gcd) != n:
            fails.append(f"{len(gcd)} knob GCDs for {n} drawers")
        for g in gcd:
            co = np.array([g.matrix_world @ Vector(v.co) for v in g.data.vertices])
            length = float(np.ptp(co[:, 0])) / MM
            if abs(length - GCD_MM) > GCD_MM * 0.01:
                fails.append(f"{g.name}: {length:.2f} mm, not {GCD_MM}")
    # 2. scene black: the outermost 2% of the width, on every side, of every web output (plates, sequence frames) is
    # within 1/255 of black; and the renders themselves, before the grade, are black there too, so the cabinet is
    # clear of the band (the grade's edge mask only tidies the film curve's floor and the encoders' ringing)
    band = 0.02

    def edge_max(img):
        mm = max(1, int(round(band * img.shape[1])))
        return int(max(img[:mm].max(), img[-mm:].max(), img[:, :mm].max(), img[:, -mm:].max()))

    def read(path):
        return np.asarray(Image.open(path).convert("RGB")).astype(np.int16)

    outputs = sorted(assets.glob("plate-*.avif")) + sorted(assets.glob("plate-*.webp"))
    seq_dir = ROOT / "wall" / "assets" / "seq"
    if seq_dir.exists():
        outputs += sorted(q for q in seq_dir.rglob("*") if q.suffix in (".avif", ".webp"))
    for q in outputs:
        v = edge_max(read(q))
        if v > 1:
            fails.append(f"{q.relative_to(ROOT)}: the outermost 2% reaches {v}/255, not within 1/255 of scene black")
    print(f"check: scene black sampled on {len(outputs)} web outputs (the plates, the sequence frames)")
    skipped = []
    for variant in ("lit", "dark"):
        raw = WORK / f"{a.layout}-{a.knob}-{variant}.png"
        if raw.exists():
            v = edge_max(read(raw))
            if v > 2:
                fails.append(f"{raw.name}: the render's own outermost 2% reaches {v}/255: the cabinet reaches into the edge band")
        else:
            skipped.append(f"the {variant} render's edges ({raw.name} is not on this machine)")
    # 3. the dark crops against the plate's surroundings and the dark render; lit and dark differ only inside the crops
    plate_path = assets / "plate-lit.avif"
    if plate_path.exists():
        plate = read(plate_path)
        h, w = plate.shape[:2]
        dark_full = WORK / f"{a.layout}-{a.knob}-dark.graded.png"
        if not dark_full.exists():
            skipped.append(f"the dark crops against the dark render ({dark_full.name} is not on this machine)")
        for r in rects["drawers"]:
            crop_path = assets / f"bay-{r['index']:02d}-dark.avif"
            if not crop_path.exists():
                fails.append(f"{crop_path.name} missing")
                continue
            c = r["crop"]
            x0, y0 = int(round(c["x"] / 100 * w)), int(round(c["y"] / 100 * h))
            x1, y1 = int(round((c["x"] + c["w"]) / 100 * w)), int(round((c["y"] + c["h"]) / 100 * h))
            crop = read(crop_path)
            if crop.shape[0] != y1 - y0 or crop.shape[1] != x1 - x0:
                fails.append(f"{crop_path.name}: {crop.shape[1]}x{crop.shape[0]}, the rect is {x1 - x0}x{y1 - y0}")
                continue
            # the crop's outer ring must match the lit plate (the leather round the seam is the same in both renders)
            ring = 3
            region = plate[y0:y1, x0:x1]
            ring_diff = np.abs(np.concatenate([(region[:ring] - crop[:ring]).ravel(), (region[-ring:] - crop[-ring:]).ravel(),
                                               (region[:, :ring] - crop[:, :ring]).ravel(), (region[:, -ring:] - crop[:, -ring:]).ravel()]))
            if ring_diff.mean() > 2.0:
                fails.append(f"{crop_path.name}: its edge differs from the plate by {ring_diff.mean():.2f}/255 on average")
            if dark_full.exists():
                full = read(dark_full)
                d = np.abs(full[y0:y1, x0:x1] - crop).mean()
                if d > 2.5:
                    fails.append(f"{crop_path.name}: differs from the dark render by {d:.2f}/255 on average")
        lit_g = WORK / f"{a.layout}-{a.knob}-lit.graded.png"
        if lit_g.exists() and dark_full.exists():
            li, da = read(lit_g), read(dark_full)
            if li.shape != da.shape:
                fails.append(f"the graded lit and dark renders differ in size: {li.shape} and {da.shape}")
            else:
                outside = np.ones(li.shape[:2], bool)
                hh, ww = outside.shape
                for r in rects["drawers"]:
                    c = r["crop"]
                    outside[int(round(c["y"] / 100 * hh)):int(round((c["y"] + c["h"]) / 100 * hh)), int(round(c["x"] / 100 * ww)):int(round((c["x"] + c["w"]) / 100 * ww))] = False
                d = np.abs(li - da).max(-1)[outside]
                print(f"check: lit against dark outside the crops: mean {d.mean():.2f}/255, max {int(d.max())}/255")
                if d.mean() > 1.5:
                    fails.append(f"the lit and dark plates differ outside the crops by {d.mean():.2f}/255 on average: the crops miss some of the light")
        else:
            skipped.append("lit against dark outside the crops (the graded renders are not on this machine)")
    else:
        fails.append(f"{plate_path} missing")
    for sk in skipped:
        print("check: skipped:", sk)
    for f in fails:
        print("check:", f)
    print(f"check {a.layout} {a.knob}: {len(fails)} failures")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("wall")
    p.add_argument("--light", type=float, default=1.0, help="the room lights' energy, as a multiple of the tool's")
    p.add_argument("--layout", choices=list(LAYOUTS), required=True)
    p.add_argument("--knob", choices=["black-relief", "gold", "plain"], default="black-relief")
    p.add_argument("--variant", choices=["lit", "dark"], default="lit")
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--size", type=int, default=None, help="the plate's width in px (the layout's by default)")
    p.add_argument("--out", default=None)
    p.add_argument("--dry", action="store_true", help="write rects.json and the sizes, render nothing")
    p = sub.add_parser("sequence")
    p.add_argument("--light", type=float, default=1.0, help="the room lights' energy, as a multiple of the tool's")
    p.add_argument("--frames", type=int, default=24)
    p.add_argument("--frame", default=None, help="a frame id in the drawer (F09); none for the base sequence")
    p.add_argument("--region", action="store_true", help="render only where the interior shows (with --frame)")
    p.add_argument("--tint", type=float, nargs=3, default=[0.06, 0.06, 0.065], help="the lens transmission, linear r g b")
    p.add_argument("--slot", type=int, default=2, help="which drawer of the portrait wall opens (0..7)")
    p.add_argument("--knob", choices=["black-relief", "gold", "plain"], default="black-relief")
    p.add_argument("--samples", type=int, default=48)
    p.add_argument("--only", default=None, help="frame indices to render, comma-separated")
    p.add_argument("--size", type=int, default=None, help="the view's width in px (1200 by default)")
    p.add_argument("--mesh-step", type=int, default=4, help="frame3d's front grid for the frame in the drawer (4: a 0.2 mm grid, as the GLB)")
    p.add_argument("--out", default=None)
    p.add_argument("--dry", action="store_true")
    p = sub.add_parser("knob")
    p.add_argument("--light", type=float, default=1.0, help="the room lights' energy, as a multiple of the tool's")
    p.add_argument("--knob", choices=["black-relief", "gold", "plain"], required=True)
    p.add_argument("--slot", type=int, default=2)
    p.add_argument("--samples", type=int, default=96)
    p.add_argument("--size", type=int, default=1024)
    p.add_argument("--out", default=None)
    p = sub.add_parser("env")
    p.add_argument("--light", type=float, default=1.0, help="the room lights' energy, as a multiple of the tool's")
    p.add_argument("--knob", choices=["black-relief", "gold", "plain"], default="black-relief")
    p.add_argument("--slot", type=int, default=2)
    p.add_argument("--samples", type=int, default=48)
    p.add_argument("--cameras", default=None, help="the folder with inspect.json (the lifted pose)")
    p.add_argument("--out", default=None)
    p = sub.add_parser("lifted")
    p.add_argument("--frame", required=True)
    p.add_argument("--tint", type=float, nargs=3, default=[0.06, 0.06, 0.065])
    p.add_argument("--cameras", default=str(WORK / "camera"))
    p.add_argument("--knob", choices=["black-relief", "gold", "plain"], default="black-relief")
    p.add_argument("--slot", type=int, default=2)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--size", type=int, default=1200)
    p.add_argument("--light", type=float, default=1.0)
    p.add_argument("--mesh-step", type=int, default=4)
    p.add_argument("--out", default=None)
    p = sub.add_parser("cameras")
    p.add_argument("--knob", choices=["black-relief", "gold", "plain"], default="black-relief")
    p.add_argument("--slot", type=int, default=2)
    p.add_argument("--out", default=None)
    p.add_argument("--frames", nargs="*", default=None, help="the frames to place (every frame by default)")
    p.add_argument("--mesh-step", type=int, default=4, help="the frames are built at this step for their bounds (the GLBs' 4)")
    p = sub.add_parser("check")
    p.add_argument("--layout", choices=list(LAYOUTS), required=True)
    p.add_argument("--knob", choices=["black-relief", "gold", "plain"], default="black-relief")
    a = ap.parse_args()
    code = {"wall": cmd_wall, "sequence": cmd_sequence, "knob": cmd_knob, "env": cmd_env, "lifted": cmd_lifted, "cameras": cmd_cameras, "check": cmd_check}[a.cmd](a)
    raise SystemExit(code or 0)


if __name__ == "__main__":
    main()
