"""PROTOTYPE (Nov 5 2026), the founder-reviewed single drawer: a black calfskin cabinet with piped edges,
one drawer, a blackened knob tilted 28 degrees up toward the viewer with the GCD on its face, What Stevie Saw
(F09) inside on black velvet. Renders the drawer at a list of extensions (metres pulled out).

    python3 docs/build/drawer-wall/prototype/drawer_scene.py --ext 0,0.012,0.03,0.055,0.085,0.115,0.145,0.175,0.205,0.23,0.25 \
        --outdir work/drawer-proto --samples 40 --size 760

Measured on a 2-CPU workspace: about 80 s a frame at 760 x 950 and 40 samples. Known limits, fixed in
tools/blender/drawer_wall.py (DRAWER-WALL.md, phase D3): the knob GCD is gold here (the wall default is black relief,
O15); leather grain is in object space (identical on every drawer of a wall: use world space); one drawer, no wall.
"""
import argparse, pathlib, sys
import numpy as np, bpy
from mathutils import Vector
ROOT = pathlib.Path(__file__).resolve().parents[4]  # the repo root (docs/build/drawer-wall/prototype/ is four down)
sys.path.insert(0, str(ROOT / "tools" / "blender"))
import frame3d  # noqa
MM = frame3d.MM

ap = argparse.ArgumentParser(); ap.add_argument("--ext", default="0"); ap.add_argument("--outdir", required=True)
ap.add_argument("--samples", type=int, default=40); ap.add_argument("--size", type=int, default=1000)
a = ap.parse_args()

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = a.samples; sc.cycles.use_denoising = True
sc.render.resolution_x = a.size; sc.render.resolution_y = int(a.size * 1.25)
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Base Contrast"
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)

def mat(name, col, rough, spec=0.5, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec; b.inputs["Coat Weight"].default_value = coat
    return m

def box(name, x0, x1, y0, y1, z0, z1, m, parent=None, bevel=0.0015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0+x1)/2, (y0+y1)/2, (z0+z1)/2))
    ob = bpy.context.object; ob.name = name; ob.scale = (x1-x0, y1-y0, z1-z0)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bv = ob.modifiers.new("bv", "BEVEL"); bv.width = bevel; bv.segments = 3
    ob.data.materials.append(m)
    if parent: ob.parent = parent
    return ob


def calfskin(name, col=(0.0065, 0.0063, 0.006)):
    """black calfskin: fine irregular pebble, a coarser crease, satin sheen; scaled in metres (object space)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Specular IOR Level"].default_value = 0.55
    b.inputs["Sheen Weight"].default_value = 0.08; b.inputs["Sheen Roughness"].default_value = 0.4
    b.inputs["Coat Weight"].default_value = 0.15; b.inputs["Coat Roughness"].default_value = 0.3
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 650.0; vor.inputs["Randomness"].default_value = 1.0
    vor.feature = "DISTANCE_TO_EDGE"
    noi = nt.nodes.new("ShaderNodeTexNoise"); noi.inputs["Scale"].default_value = 90.0; noi.inputs["Detail"].default_value = 8.0; noi.inputs["Roughness"].default_value = 0.65
    big = nt.nodes.new("ShaderNodeTexNoise"); big.inputs["Scale"].default_value = 18.0; big.inputs["Detail"].default_value = 3.0
    for t in (vor, noi, big): nt.links.new(tc.outputs["Object"], t.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "FLOAT"; mix.inputs[0].default_value = 0.4
    nt.links.new(vor.outputs["Distance"], mix.inputs[2]); nt.links.new(noi.outputs["Fac"], mix.inputs[3])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.8; bump.inputs["Distance"].default_value = 0.0007
    nt.links.new(mix.outputs[0], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = 0.30; rr.inputs["To Max"].default_value = 0.62
    nt.links.new(big.outputs["Fac"], rr.inputs["Value"]); nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    return m

lacquer = calfskin("calf_front")
wood = calfskin("calf_cab", (0.0045, 0.0044, 0.0042))
woodin = mat("wood", (0.006, 0.005, 0.0045), 0.5, 0.35)
velvet = mat("velvet", (0.006, 0.006, 0.007), 1.0, 0.1)
blackmetal = mat("knob", (0.02, 0.02, 0.02), 0.22, 0.6)
inside = mat("carcass", (0.004, 0.004, 0.004), 0.9, 0.1)

# the frame
mats = frame3d.materials_for("F09")
parts, sh, hinges = frame3d.build("F09", mats)
parts += frame3d.temples("F09", hinges, mats)
rig = bpy.data.objects.new("rig", None); sc.collection.objects.link(rig)
for p in parts: p.parent = rig
rig.rotation_euler = (np.radians(90), 0, 0)
bpy.context.view_layer.update()
lo = np.array([1e9]*3); hi = -lo.copy()
for p in parts:
    co = np.array([p.matrix_world @ Vector(v.co) for v in p.data.vertices])
    lo = np.minimum(lo, co.min(0)); hi = np.maximum(hi, co.max(0))
fz = lo[2]

drawer = bpy.data.objects.new("drawer", None); sc.collection.objects.link(drawer)
rig.parent = drawer
rig.location = (0, 0.03, 0)
F = 0.0   # inner face of the drawer front
yF = -0.035
zb = fz - 0.010; zt = fz + 0.060           # drawer front
box("front", -0.20, 0.20, yF-0.022, yF, zb, zt, lacquer, drawer, 0.004)
# piped edges along the drawer front, as on the strap: a fine cord at top and bottom
for zz in (zt-0.0035, zb+0.0035):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0016, depth=0.392, location=(0, yF-0.0222, zz), rotation=(0, np.radians(90), 0), vertices=24)
    cord = bpy.context.object; cord.data.materials.append(calfskin("cord", (0.006,0.006,0.006))); cord.parent = drawer
    bpy.ops.object.shade_smooth()
box("floor", -0.186, 0.186, yF, 0.215, zb, fz-0.0004, velvet, drawer, 0)
for s in (-1, 1):
    box(f"side{s}", s*0.186-0.006, s*0.186+0.006, yF, 0.215, zb, fz+0.046, woodin, drawer)
box("back", -0.192, 0.192, 0.209, 0.221, zb, fz+0.046, woodin, drawer)
# the knob: a short blackened cylinder, the GCD on its face toward you
kz = (zb + zt) / 2; ky0 = yF - 0.022
bpy.ops.mesh.primitive_cylinder_add(radius=0.023, depth=0.022, location=(0, ky0-0.011, kz), rotation=(np.radians(90),0,0), vertices=96)
knob = bpy.context.object; knob.data.materials.append(blackmetal)
pivot = bpy.data.objects.new("pivot", None); sc.collection.objects.link(pivot); pivot.location = (0, ky0, kz); pivot.parent = drawer
bpy.context.view_layer.update()
knob.parent = pivot; knob.matrix_parent_inverse = pivot.matrix_world.inverted()
bv = knob.modifiers.new("bv","BEVEL"); bv.width=0.0025; bv.segments=5
bpy.ops.object.shade_smooth()
face_y = ky0 - 0.022
for g in frame3d.gcd_parts("knob", mats, 30.0, (0, face_y/MM, kz/MM), (1,0,0), (0,0,1), (0,-1,0), proud=0.6):
    g.parent = pivot; g.matrix_parent_inverse = pivot.matrix_world.inverted()
pivot.rotation_euler = (np.radians(-28), 0, 0)

# the cabinet face, flush with the drawer front when shut, and a dark carcass behind the opening
yc0, yc1 = yF-0.022, 0.30
ox0, ox1, oz0, oz1 = -0.203, 0.203, zb-0.003, zt+0.003
box("cab_l", -0.70, ox0, yc0, yc1, zb-0.30, zt+0.45, wood, None, 0)
box("cab_r", ox1, 0.70, yc0, yc1, zb-0.30, zt+0.45, wood, None, 0)
box("cab_t", ox0, ox1, yc0, yc1, oz1, zt+0.45, wood, None, 0)
box("cab_b", ox0, ox1, yc0, yc1, zb-0.30, oz0, wood, None, 0)
box("carcass", ox0, ox1, yc1, yc1+0.01, oz0, oz1, inside, None, 0)

def area(name, loc, target, size, energy, color, size_y=None):
    L = bpy.data.lights.new(name, "AREA"); L.shape = "RECTANGLE"; L.size = size; L.size_y = size_y or size
    L.energy = energy; L.color = color
    ob = bpy.data.objects.new(name, L); sc.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return ob
# one warm strip high and in front: it grazes the shut drawer, and falls into it as it opens
area("top", (0, -0.36, fz+0.55), (0, -0.24, fz), 0.6, 7.0, (1.0, 0.86, 0.68), size_y=0.08)
area("rake", (-0.5, -0.30, fz+0.10), (0, -0.06, fz+0.02), 0.06, 1.4, (1.0, 0.9, 0.78), size_y=0.4)
area("glint", (0.12, -0.38, fz+0.30), (0, -0.08, kz), 0.03, 0.9, (1.0, 0.95, 0.85), size_y=0.03)
area("edge", (0.55, -0.5, fz+0.12), (0, -0.05, kz), 0.05, 1.6, (0.85, 0.9, 1.0), size_y=0.3)

L = bpy.data.lights.new("wait", "SPOT"); L.energy = 11.0; L.spot_size = np.radians(30); L.spot_blend = 0.55
L.shadow_soft_size = 0.04; L.color = (1.0, 0.94, 0.86)
sp = bpy.data.objects.new("wait", L); sc.collection.objects.link(sp); sp.location = (0, -0.21, fz + 0.38)
sp.rotation_euler = (Vector((0, -0.17, fz)) - sp.location).to_track_quat("-Z", "Y").to_euler()
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 68; cam.data.sensor_fit = "HORIZONTAL"; cam.data.sensor_width = 36
cam.location = (0, -0.70, fz + 0.60)
aim = Vector((0, -0.13, fz + 0.0))
cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 5.6

out = pathlib.Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
for i, e in enumerate(float(x) for x in a.ext.split(",")):
    drawer.location = (0, -e, 0)
    cam.data.dof.focus_distance = (Vector((0, -e + 0.03, fz + 0.03)) - cam.location).length
    sc.render.filepath = str(out / f"d{i:02d}.png")
    bpy.ops.render.render(write_still=True)
    print("wrote", sc.render.filepath, e, flush=True)
