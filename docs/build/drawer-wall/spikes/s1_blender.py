"""S1 spike (D0): F09 as a GLB with the material conversion, next to a Cycles still from the same camera, both
lit by the same environment (an equirectangular render of the scene's light from the frame's centre).

    python3 s1_blender.py OUTDIR [--mesh-step N] [--samples 48]

Writes: env.exr + env.hdr (the light), cycles.png (the still, film transparent), F09.glb, camera.json, counts.json.
"""
import argparse, json, os, pathlib, sys, time
os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
import numpy as np, bpy, cv2
from mathutils import Vector
ROOT = pathlib.Path("/home/user/darkestshadeswebsite")
sys.path.insert(0, str(ROOT / "tools" / "blender"))
import frame3d
MM = frame3d.MM

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--mesh-step", type=int, default=0); ap.add_argument("--samples", type=int, default=48)
ap.add_argument("--target-tris", type=int, default=60000); ap.add_argument("--size", type=int, default=1024)
a = ap.parse_args()
OUT = pathlib.Path(a.out); OUT.mkdir(parents=True, exist_ok=True)
T0 = time.time()
def lap(msg):
    print(f"[{time.time()-T0:7.1f}s] {msg}", flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = a.samples; sc.cycles.use_denoising = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Base Contrast"
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)

if a.mesh_step:
    frame3d.FRAMES["F09"]["mesh_step"] = a.mesh_step
TINT = (0.06, 0.06, 0.065)   # F09's dark grey, about 6-7% (07-photography.md); lens_tints.py measures it in D4
mats = frame3d.materials_for("F09", TINT)
parts, sh, hinges = frame3d.build("F09", mats)
parts += frame3d.temples("F09", hinges, mats)
lap(f"built F09: {len(parts)} parts")
rig = bpy.data.objects.new("rig", None); sc.collection.objects.link(rig)
for p in parts: p.parent = rig
rig.rotation_euler = (np.radians(90), 0, 0)
bpy.context.view_layer.update()
lo = np.array([1e9]*3); hi = -lo.copy()
for p in parts:
    co = np.array([p.matrix_world @ Vector(v.co) for v in p.data.vertices])
    lo = np.minimum(lo, co.min(0)); hi = np.maximum(hi, co.max(0))
c = Vector(tuple((lo + hi) / 2)); fz = float(lo[2])
print("bounds (m)", lo.round(4), hi.round(4), "centre", tuple(round(v, 4) for v in c))

# the light: emissive panels (visible to a panoramic camera, so the environment map holds exactly them)
def emitter(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0]); return m
def panel(name, loc, target, sx, sy, col, strength):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    ob = bpy.context.object; ob.name = name; ob.scale = (sx, sy, 1)
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("Z", "Y").to_euler()
    ob.data.materials.append(emitter(name, col, strength)); return ob
front = Vector((0, -1, 0))   # the frame's front faces -y after the rig's turn
up = Vector((0, 0, 1)); right = Vector((1, 0, 0))
panels = [
    panel("key", tuple(c - front * -0.45 + up * 0.40), tuple(c), 0.50, 0.18, (1.0, 0.93, 0.84), 9.0),     # warm, high and in front
    panel("rim", tuple(c + front * -0.40 + up * 0.22 + right * 0.25), tuple(c), 0.04, 0.60, (0.90, 0.95, 1.0), 14.0),  # cool strip behind right
    panel("rim2", tuple(c + front * -0.40 + up * 0.22 - right * 0.25), tuple(c), 0.04, 0.60, (0.90, 0.95, 1.0), 10.0),
    panel("fill", tuple(c + up * 0.9), tuple(c), 1.4, 1.4, (0.8, 0.85, 0.9), 0.35),
]
# the frame's centre must be on the panels' "front" (-z of the plane) side: planes track their +Z to the target
bpy.context.view_layer.update()

# 1. the environment: an equirectangular capture from the frame's centre, the frame hidden
for p in parts: p.hide_render = True
pano = bpy.data.objects.new("pano", bpy.data.cameras.new("pano")); sc.collection.objects.link(pano)
pano.data.type = "PANO"
try:
    pano.data.panorama_type = "EQUIRECTANGULAR"
except Exception:
    pano.data.cycles.panorama_type = "EQUIRECTANGULAR"
pano.location = c; pano.rotation_euler = (np.radians(90), 0, 0)
sc.camera = pano
sc.render.resolution_x, sc.render.resolution_y = 1024, 512
sc.render.image_settings.file_format = "OPEN_EXR"; sc.render.image_settings.color_depth = "16"; sc.render.image_settings.color_mode = "RGB"
sc.cycles.samples = 24
sc.render.filepath = str(OUT / "env.exr")
bpy.ops.render.render(write_still=True)
# OpenCV here is built without OpenEXR: read the EXR through Blender (scene linear, float), write the .hdr with OpenCV
_im = bpy.data.images.load(str(OUT / "env.exr")); _im.colorspace_settings.name = "Non-Color"
env = np.array(_im.pixels[:], np.float32).reshape(_im.size[1], _im.size[0], _im.channels)[::-1, :, :3]   # Blender's rows start at the bottom
cv2.imwrite(str(OUT / "env.hdr"), np.ascontiguousarray(env[..., ::-1]))
lap(f"env rendered: max {float(env.max()):.2f}, mean {float(env.mean()):.4f}, {os.path.getsize(OUT/'env.hdr')//1024} KB hdr")

# 2. the Cycles still: lit by that environment only (panels hidden), film transparent
for p in parts: p.hide_render = False
for p in panels: p.hide_render = True
envn = w.node_tree.nodes.new("ShaderNodeTexEnvironment"); envn.image = bpy.data.images.load(str(OUT / "env.exr"))
w.node_tree.links.new(envn.outputs["Color"], w.node_tree.nodes["Background"].inputs["Color"])
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
az, el, dist = np.radians(38), np.radians(14), 1.05
side = -1.0   # the GCD is on the wearer's right: x negative in frame3d's coordinates (x to the wearer's left)
dirv = Vector((side * np.sin(az), -np.cos(az), 0))
camloc = c + Vector((dirv.x * np.cos(el), dirv.y * np.cos(el), np.sin(el))) * dist
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_fit = "VERTICAL"; cam.data.sensor_height = 24; cam.data.lens = 100
cam.location = camloc; cam.rotation_euler = (c - camloc).to_track_quat("-Z", "Y").to_euler()
cam.data.dof.use_dof = False
sc.render.resolution_x = sc.render.resolution_y = a.size
sc.render.film_transparent = True
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_depth = "8"; sc.render.image_settings.color_mode = "RGBA"
sc.cycles.samples = a.samples
sc.render.filepath = str(OUT / "cycles.png")
t = time.time(); bpy.ops.render.render(write_still=True); lap(f"cycles still rendered in {time.time()-t:.1f}s")
fov = float(np.degrees(2 * np.arctan(12.0 / 100.0)))
def y_up(v): return [float(v[0]), float(v[2]), -float(v[1])]
(OUT / "camera.json").write_text(json.dumps({
    "blender": {"position": list(map(float, camloc)), "target": list(map(float, c)), "lens_mm": 100, "sensor_height_mm": 24, "fit": "VERTICAL"},
    "three": {"position": y_up(camloc), "target": y_up(c), "fov_deg": fov, "up": [0, 1, 0]},
    "lens_tint_linear": TINT}, indent=1))

# 3. the GLB: glTF materials in place of the Cycles ones
def pbr(name, base, rough, metallic=0.0, ior=1.5, alpha=1.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic; b.inputs["IOR"].default_value = ior
    b.inputs["Alpha"].default_value = alpha; b.inputs["Coat Weight"].default_value = coat
    if alpha < 1.0:
        m.surface_render_method = "BLENDED"
    return m
tmean = float(np.mean(TINT))
G = {"acetate": pbr("acetate", (0.0015, 0.0015, 0.0017), 0.06, ior=1.49),
     "lens": pbr("lens", (0.01, 0.01, 0.012), 0.0, ior=1.5, alpha=1.0 - tmean),
     "gcd gold": pbr("gcd_gold", (0.565, 0.366, 0.145), 0.22, metallic=1.0),
     "gcd onyx": pbr("gcd_onyx", (0.006, 0.006, 0.006), 0.04),
     "clear acetate": pbr("clear_acetate", (0.9, 0.9, 0.9), 0.05, ior=1.49, alpha=0.3),
     "metal": pbr("metal", (0.005, 0.005, 0.0055), 0.6),
     "endmetal": pbr("endmetal", (0.035, 0.035, 0.038), 0.07, metallic=1.0)}
used = {}
for p in parts:
    for i, m in enumerate(p.data.materials):
        key = m.name.split(".")[0]
        g = G.get(key) or G.get(key.replace("F09 ", ""))
        if g is None:
            print("no glTF material for", m.name, "on", p.name); g = G["acetate"]
        p.data.materials[i] = g; used[g.name] = used.get(g.name, 0) + 1
print("materials used", used)
# triangulate, then decimate the big parts toward the budget (the GCD stays whole)
tris0 = {}
for p in parts:
    p.data.calc_loop_triangles(); tris0[p.name] = len(p.data.loop_triangles)
total0 = sum(tris0.values())
# the GCD keeps its detail (decimated gently, to about a sixth of the budget); the rest shares what is left
gcd_tris = sum(v for k, v in tris0.items() if "gcd" in k)
gcd_budget = min(gcd_tris, a.target_tris // 6)
gcd_ratio = gcd_budget / max(1, gcd_tris)
big = {k: v for k, v in tris0.items() if "gcd" not in k}
ratio = min(1.0, (a.target_tris - gcd_budget) / max(1, sum(big.values())))
lap(f"triangles as built: {total0} (frame ratio {ratio:.5f}, gcd ratio {gcd_ratio:.3f})")
for p in parts:
    tri = p.modifiers.new("tri", "TRIANGULATE")
    r = gcd_ratio if "gcd" in p.name else ratio
    if r < 1.0:
        d = p.modifiers.new("dec", "DECIMATE"); d.ratio = r; d.use_collapse_triangulate = True
bpy.ops.object.select_all(action="DESELECT")
for p in parts: p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
t = time.time()
bpy.ops.export_scene.gltf(filepath=str(OUT / "F09.glb"), export_format="GLB", use_selection=True, export_apply=True,
                          export_yup=True, export_materials="EXPORT", export_image_format="WEBP", export_normals=True,
                          export_texcoords=True, export_cameras=False, export_lights=False)
lap(f"glb exported in {time.time()-t:.1f}s: {os.path.getsize(OUT/'F09.glb')/1e6:.2f} MB")
# count the exported triangles
dg = bpy.context.evaluated_depsgraph_get(); total1 = 0
for p in parts:
    me = p.evaluated_get(dg).data; me.calc_loop_triangles(); total1 += len(me.loop_triangles)
(OUT / "counts.json").write_text(json.dumps({"triangles_built": total0, "triangles_exported": total1, "per_part_built": tris0,
                                              "glb_bytes": os.path.getsize(OUT / "F09.glb"), "materials": used}, indent=1))
lap(f"done: {total1} triangles exported")
