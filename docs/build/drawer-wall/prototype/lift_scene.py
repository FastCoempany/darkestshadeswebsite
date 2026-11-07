"""PROTOTYPE (Nov 5 2026), the frame alone on black: the looks the founder saw ("rim", "pool", "halo") and the
pair the touch prototypes used for the lift ("dark" and "lit", three-quarter view "tq": the same camera, the
frame barely lit and fully lit, so a cross-fade between them is a real change of light).

    python3 docs/build/drawer-wall/prototype/lift_scene.py F09 lit tq --out work/lift-proto/tq-lit.png --samples 64

Reference only: in the build the lifted frame is a real-time glTF model (DRAWER-WALL.md, phases D4 and D5).
"""
import argparse, pathlib, sys
import numpy as np, bpy
from mathutils import Vector
ROOT = pathlib.Path(__file__).resolve().parents[4]  # the repo root (docs/build/drawer-wall/prototype/ is four down)
sys.path.insert(0, str(ROOT / "tools" / "blender"))
import frame3d  # noqa
def area(name, loc, target, size, energy, color, shape="RECTANGLE", size_y=None):
    L = bpy.data.lights.new(name, "AREA")
    L.shape = shape
    L.size = size
    if size_y:
        L.size_y = size_y
    L.energy = energy
    L.color = color
    ob = bpy.data.objects.new(name, L)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob



def mat(name, col, rough, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    return m

def emitter_mat(strength, col=(1,1,1)):
    m = bpy.data.materials.new("glow"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0]); return m

def plane(loc, size, rot, m):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=rot)
    ob = bpy.context.object; ob.data.materials.append(m); return ob

ap = argparse.ArgumentParser()
ap.add_argument("frame"); ap.add_argument("look", choices=["rim", "pool", "halo", "dark", "lit"])
ap.add_argument("view", choices=["front", "side", "tq"]); ap.add_argument("--out", required=True)
ap.add_argument("--samples", type=int, default=64)
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = a.samples
sc.cycles.use_denoising = True
sc.render.resolution_x = 1200; sc.render.resolution_y = 1200
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Base Contrast"
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0, 0.0, 0.0, 1)

mats = frame3d.materials_for(a.frame)
parts, sh, hinges = frame3d.build(a.frame, mats)
parts += frame3d.temples(a.frame, hinges, mats)
rig = bpy.data.objects.new("rig", None); sc.collection.objects.link(rig)
for p in parts: p.parent = rig
rig.rotation_euler = (np.radians(90), 0, 0)
bpy.context.view_layer.update()
lo = np.array([1e9]*3); hi = -lo.copy(); g = None
for p in parts:
    co = np.array([p.matrix_world @ Vector(v.co) for v in p.data.vertices])
    lo = np.minimum(lo, co.min(0)); hi = np.maximum(hi, co.max(0))
    if p.name.endswith("gcd gold") or "gcd gold" in p.name: g = (co.min(0)+co.max(0))/2
c = Vector(tuple((lo+hi)/2)); fz = lo[2]
side = 1.0 if g is not None and g[0] > c.x else -1.0
print("bounds", lo, hi, "gcd", g)

# the camera: front from -y (the face looks at -y? check by span), side from the GCD's side
ext = hi - lo
if a.view == "front":
    # the front faces whichever y end is lower (temples run to the other)
    dirv = Vector((0, -1, 0)) if True else None
elif a.view == "side":
    dirv = Vector((side, 0, 0))
else:
    az = np.radians(38); dirv = Vector((side*np.sin(az), -np.cos(az), 0))
el = np.radians(14 if a.view == "tq" else 5)
d = 1.05
camloc = c + Vector((dirv.x*np.cos(el), dirv.y*np.cos(el), np.sin(el))) * d
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_fit = "VERTICAL"; cam.data.sensor_height = 24; cam.data.lens = 100
cam.location = camloc
cam.rotation_euler = (c - camloc).to_track_quat("-Z", "Y").to_euler()
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 8.0
cam.data.dof.focus_distance = (c - camloc).length

back = -dirv  # behind the frame, as seen from the camera
right = Vector((-dirv.y, dirv.x, 0)) if a.view == "front" else Vector((0, side, 0))
right = Vector((dirv.y*-1, dirv.x, 0)).normalized()

if a.look in ("dark", "lit"):
    plane((c.x, c.y, fz-0.0002), 4, (0,0,0), mat("floor", (0.004,0.004,0.004), 0.18, 0.6))
    k = 0.12 if a.look == "dark" else 1.0
    for s_ in (-1, 1):
        area(f"strip{s_}", tuple(c + back*0.25 + right*s_*0.32 + Vector((0,0,0.05))), tuple(c), 0.03, 14.0*(0.35 if a.look=="dark" else 1), (0.95,0.97,1.0), size_y=0.6)
    if a.look == "lit":
        area("key", tuple(c - back*0.45 + Vector((0,0,0.4))), tuple(c), 0.5, 9.0, (1,0.96,0.9), size_y=0.18)
        area("sheen", tuple(c - back*0.5 + right*0.25 + Vector((0,0,0.12))), tuple(c), 0.3, 2.5, (1,0.95,0.88), size_y=0.05)
elif a.look == "rim":
    # black glossy floor, two tall strips behind left and right, a faint top strip: the edges draw the frame
    plane((c.x, c.y, fz-0.0002), 4, (0,0,0), mat("floor", (0.004,0.004,0.004), 0.12, 0.6))
    for s in (-1, 1):
        area(f"strip{s}", tuple(c + back*0.25 + right*s*0.32 + Vector((0,0,0.05))), tuple(c), 0.03, 14.0, (0.95,0.97,1.0), size_y=0.6)
    area("top", tuple(c + Vector((0,0,0.5)) + back*0.1), tuple(c), 0.6, 2.5, (1,1,1), size_y=0.04)
    area("kick", tuple(c - back*0.6 + Vector((0,0,0.08))), tuple(c), 0.5, 1.2, (1,0.95,0.9), size_y=0.5)
elif a.look == "pool":
    # matte near-black floor, one tight overhead spot: the frame sits in its own pool of light
    plane((c.x, c.y, fz-0.0002), 4, (0,0,0), mat("floor", (0.02,0.019,0.018), 0.55, 0.3))
    L = bpy.data.lights.new("spot", "SPOT"); L.energy = 9.0; L.spot_size = np.radians(26); L.spot_blend = 0.6
    L.shadow_soft_size = 0.05; L.color = (1.0, 0.93, 0.84)
    ob = bpy.data.objects.new("spot", L); sc.collection.objects.link(ob)
    ob.location = tuple(c + Vector((0,0,0.55)) + back*0.12)
    ob.rotation_euler = (c - ob.location).to_track_quat("-Z","Y").to_euler()
    area("edge", tuple(c + back*0.4 + right*0.3 + Vector((0,0,0.15))), tuple(c), 0.05, 4.0, (0.85,0.9,1.0), size_y=0.3)
else:
    # graphite seamless with a soft halo behind the frame; the frame reads dark against light grey smoke
    plane((c.x, c.y, fz-0.0002), 4, (0,0,0), mat("floor", (0.03,0.03,0.031), 0.6, 0.3))
    wall = plane(tuple(c + back*0.35), 2, (0,0,0), mat("wall", (0.05,0.05,0.052), 0.9, 0.1))
    wall.rotation_euler = back.to_track_quat("Z","Y").to_euler(); wall.rotation_euler = (-back).to_track_quat("Z","Y").to_euler()
    bpy.context.view_layer.update()
    L = bpy.data.lights.new("halo", "SPOT"); L.energy = 6.0; L.spot_size = np.radians(40); L.spot_blend = 1.0
    L.shadow_soft_size = 0.1; L.color = (0.9, 0.93, 0.95)
    ob = bpy.data.objects.new("halo", L); sc.collection.objects.link(ob)
    ob.location = tuple(c + back*0.08 + Vector((0,0,-0.005)))
    tgt = c + back*0.35 + Vector((0,0,0.01))
    ob.rotation_euler = (tgt - ob.location).to_track_quat("-Z","Y").to_euler()
    area("key", tuple(c - back*0.3 + right*0.35 + Vector((0,0,0.3))), tuple(c), 0.35, 3.0, (1,0.96,0.92), size_y=0.12)
    area("rim", tuple(c + back*0.2 - right*0.3 + Vector((0,0,0.1))), tuple(c), 0.03, 5.0, (1,1,1), size_y=0.3)

if a.look in ("pool","halo"):
    area("sheen2", tuple(c - back*0.5 + right*0.2 + Vector((0,0,0.25))), tuple(c), 0.25, 2.2, (1,0.95,0.88), size_y=0.06)
sc.render.filepath = a.out
bpy.ops.render.render(write_still=True)
print("wrote", a.out)
