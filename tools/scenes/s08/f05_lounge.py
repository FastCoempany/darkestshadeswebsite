"""F05 on M4 in the lounge's light: the frame (tools/blender/frame3d.py) at the pose fitted to the stand-in
(pose.json), the GCD on the near end piece, the near temple's metal run to the ear; the lenses dark glass
that shows only what they mirror (the eye behind a dark lens in a dim room is lost).

    python3 f05_lounge.py OUTDIR [--samples 128] [--passes glasses,masks,shadow]

Passes (linear RGBA as .npy, at the output's 4000 x 3000, cropped round the frame: crop.json):
  glasses   the frame lit by the room (alpha);
  masks     R the lenses, G the front's far half (what the nose may hide), B the near temple;
  shadow    the head (a mesh from the portrait's depth, head.npz) under the room's light with the frame
            and without it: shadow.npy is with/without (the frame's shadow and the lenses' tint on the skin).
"""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import REPO, WORK  # noqa: E402,F401
import argparse
import json
import math

import bpy
import cv2
import numpy as np
from mathutils import Matrix, Vector

D = WORK
REPO = str(REPO)
sys.path.insert(0, REPO + "/tools/blender")
import frame3d  # noqa: E402
import lounge_common as LC  # noqa: E402
from gcd_place import add_gcd  # noqa: E402

MM = 0.001
import pathlib  # noqa: E402
LC_HDRI = pathlib.Path(bpy.utils.resource_path("LOCAL")) / "datafiles" / "studiolights" / "world"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument("outdir")
ap.add_argument("--samples", type=int, default=128)
ap.add_argument("--passes", default="glasses,masks,shadow")
ap.add_argument("--pad", type=int, default=60)
ap.add_argument("--rim", type=float, default=0.3, help="the blue rim's power on the glasses, relative")
ap.add_argument("--hdri", default="studio")
ap.add_argument("--hdri-rot", type=float, default=0.0)
ap.add_argument("--hdri-strength", type=float, default=0.25)
ap.add_argument("--hdri-tint", type=float, nargs=3, default=(1.0, 0.42, 0.58))
ap.add_argument("--bounce", type=float, default=4.0, help="the lit floor and seat in front of him, W")
a = ap.parse_args(argv)
os.makedirs(a.outdir, exist_ok=True)

pose = json.load(open(D + "pose.json"))
R = cv2.Rodrigues(np.array(pose["rvec"]))[0]
t = np.array(pose["tvec"])
psi = float(pose["splay"])

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = LC.setup_render(1.0, a.samples, transparent=True)
sc.cycles.film_transparent_glass = False
cam = LC.camera(sc, dof=False)
LC.world(sc)
lights = LC.lights(sc)
lights["rim"].data.energy *= a.rim
# what lies in front of him, low and to the right, where the frame's face (turned right, tipped down) and
# its lenses look: the floor and the chesterfield's seat in the key's pink light, a broad dim glow
bl = bpy.data.lights.new("bounce", "AREA")
bl.shape = "RECTANGLE"
bl.size, bl.size_y = 1.6, 1.0
bl.color = (1.0, 0.22, 0.30)
bl.energy = a.bounce
bo = bpy.data.objects.new("bounce", bl)
sc.collection.objects.link(bo)
bo.location = (0.95, 0.40, -0.62)
LC.aim(bo, (0.10, 0.80, 0.10))
if a.hdri_strength > 0:
    # the room the gloss mirrors (glossy rays only): a dark studio's curtains, floor and lamps, tinted to
    # the lounge's light, darkened, its lamps clamped; every other ray sees the lounge's dim world
    w = sc.world
    nt = w.node_tree
    bgn = nt.nodes["Background"]
    base_col = tuple(bgn.inputs["Color"].default_value)
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(LC_HDRI / (a.hdri + ".exr")))
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(a.hdri_rot))
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    clampn = nt.nodes.new("ShaderNodeMix")
    clampn.data_type = "RGBA"
    clampn.blend_type = "DARKEN"
    clampn.inputs["Factor"].default_value = 1.0
    clampn.inputs[7].default_value = (6.0, 6.0, 6.0, 1)
    nt.links.new(env.outputs["Color"], clampn.inputs[6])
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 0.0
    nt.links.new(clampn.outputs[2], hsv.inputs["Color"])
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    nt.links.new(hsv.outputs["Color"], tint.inputs[6])
    tint.inputs[7].default_value = (*a.hdri_tint, 1)
    bg2 = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(tint.outputs[2], bg2.inputs["Color"])
    bg2.inputs["Strength"].default_value = a.hdri_strength
    bg1 = nt.nodes.new("ShaderNodeBackground")
    bg1.inputs["Color"].default_value = base_col
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Glossy Ray"], mx.inputs["Fac"])
    nt.links.new(bg1.outputs[0], mx.inputs[1])
    nt.links.new(bg2.outputs[0], mx.inputs[2])
    outw = [n_ for n_ in nt.nodes if n_.type == "OUTPUT_WORLD"][0]
    nt.links.new(mx.outputs[0], outw.inputs["Surface"])


def read_exr(path):
    im = bpy.data.images.load(str(path), check_existing=False)
    w, h = im.size
    px = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    return px.reshape(h, w, 4)[::-1].copy()


def emission(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        if n_.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n_)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*rgb, 1)
    nt.links.new(e.outputs[0], [n_ for n_ in nt.nodes if n_.type == "OUTPUT_MATERIAL"][0].inputs["Surface"])
    return m


def lens_mirror():
    """Dark glass in front of a dark eye: its own reflection (Fresnel, smooth) over black."""
    m = bpy.data.materials.new("lens mirror")
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        if n_.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n_)
    out = [n_ for n_ in nt.nodes if n_.type == "OUTPUT_MATERIAL"][0]
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.004, 0.004, 0.0045, 1)
    b.inputs["Roughness"].default_value = 0.015
    b.inputs["IOR"].default_value = 1.5
    b.inputs["Specular IOR Level"].default_value = 0.5
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


mats = frame3d.materials_for("F05")
mats["lens"] = lens_mirror()
# (F05's end pieces and temples are satin black metal: frame3d's FRAMES["F05"]["endpiece"]["metal_rough"])
parts, sh, hinges = frame3d.build("F05", mats)
temples = frame3d.temples("F05", hinges, mats, split=True)
# the near temple splayed about its hinge's vertical pin (the fit), the rest of the temples dropped: the far
# one runs behind his head, the near one's acetate tip behind his ear
hp = np.asarray(hinges[0], np.float64) * MM
Rs = Matrix.Translation(Vector(hp)) @ Matrix.Rotation(psi, 4, "Y") @ Matrix.Translation(-Vector(hp))
keep_t = []
for p in temples:
    if p.name == "F05 temple 0":
        p.matrix_world = Rs @ p.matrix_world
        keep_t.append(p)
    else:
        bpy.data.objects.remove(p)
near_end = [e for e in sh["ends"] if e["side"] == -1][0]
gcd = add_gcd(near_end)
keep = [p for p in parts if not p.name.startswith("F05 pad")] + keep_t + gcd
for p in parts:
    if p.name.startswith("F05 pad"):
        bpy.data.objects.remove(p)
rig = bpy.data.objects.new("rig", None)
sc.collection.objects.link(rig)
for p in keep:
    p.parent = rig
M = LC.cv_to_world_matrix(R, t)
rig.matrix_world = Matrix(M.tolist())
bpy.context.view_layer.update()

# the render region: round the frame's projection
pts = []
for p in keep:
    Mw = np.asarray(p.matrix_world)
    for v in p.bound_box:
        pts.append(Mw[:3, :3] @ np.array(v) + Mw[:3, 3])
pr = LC.project(np.array(pts))
x0, y0 = np.floor(pr.min(0) - a.pad).astype(int)
x1, y1 = np.ceil(pr.max(0) + a.pad).astype(int)
x0, y0, x1, y1 = max(0, x0), max(0, y0), min(LC.W_O, x1), min(LC.H_O, y1)
sc.render.use_border = True
sc.render.use_crop_to_border = True
sc.render.border_min_x, sc.render.border_max_x = x0 / LC.W_O, x1 / LC.W_O
sc.render.border_min_y, sc.render.border_max_y = 1 - y1 / LC.H_O, 1 - y0 / LC.H_O
json.dump({"crop": [int(x0), int(y0), int(x1), int(y1)]}, open(os.path.join(a.outdir, "crop.json"), "w"))
print("crop", x0, y0, x1, y1)


def render(name):
    path = os.path.join(a.outdir, name + ".exr")
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    arr = read_exr(path)
    np.save(os.path.join(a.outdir, name + ".npy"), arr)
    return arr


passes = a.passes.split(",")
if "glasses" in passes:
    render("glasses")

if "masks" in passes:
    sc.cycles.samples = 16
    sc.cycles.use_denoising = False
    red, black = emission("lensmask", (1, 0, 0)), emission("blackmask", (0, 0, 0))
    redgreen = emission("farlensmask", (1, 1, 0))
    blue = emission("templemask", (0, 0, 1))
    far = bpy.data.materials.new("far")
    far.use_nodes = True
    nt = far.node_tree
    for n_ in list(nt.nodes):
        if n_.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n_)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    # what the nose can hide: the far side of the keyhole below the bridge's bar (x > 3 mm, y < 12.5 mm),
    # and everything past the bridge (x > 14 mm)
    def cmp(op, a_, b_):
        n_ = nt.nodes.new("ShaderNodeMath")
        n_.operation = op
        nt.links.new(a_, n_.inputs[0])
        n_.inputs[1].default_value = b_
        return n_.outputs[0]
    g1 = nt.nodes.new("ShaderNodeMath")
    g1.operation = "MULTIPLY"
    nt.links.new(cmp("GREATER_THAN", sep.outputs["X"], 0.003), g1.inputs[0])
    nt.links.new(cmp("LESS_THAN", sep.outputs["Y"], 0.0125), g1.inputs[1])
    gmax = nt.nodes.new("ShaderNodeMath")
    gmax.operation = "MAXIMUM"
    nt.links.new(g1.outputs[0], gmax.inputs[0])
    nt.links.new(cmp("GREATER_THAN", sep.outputs["X"], 0.014), gmax.inputs[1])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(gmax.outputs[0], comb.inputs["Y"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(comb.outputs[0], em.inputs["Color"])
    nt.links.new(em.outputs[0], [n_ for n_ in nt.nodes if n_.type == "OUTPUT_MATERIAL"][0].inputs["Surface"])
    saved = {}
    for p in keep:
        saved[p.name] = list(p.data.materials)
        p.data.materials.clear()
        if p.name == "F05 lens 1":
            p.data.materials.append(redgreen)       # the far lens: a lens, and behind the nose
        elif "lens" in p.name:
            p.data.materials.append(red)
        elif p.name == "F05 front":
            p.data.materials.append(far)
        elif p.name.startswith("F05 temple"):
            p.data.materials.append(blue)
        else:
            p.data.materials.append(black)
    vis = {}
    for ob in bpy.data.objects:
        if ob.type == "LIGHT":
            vis[ob.name] = ob.hide_render
            ob.hide_render = True
    render("masks")
    for ob in bpy.data.objects:
        if ob.name in vis:
            ob.hide_render = vis[ob.name]
    for p in keep:
        p.data.materials.clear()
        for m_ in saved[p.name]:
            p.data.materials.append(m_)
    sc.cycles.samples = a.samples
    sc.cycles.use_denoising = True

if "shadow" in passes:
    hd = np.load(D + "head.npz")
    V, F = hd["V"], hd["F"]
    me = bpy.data.meshes.new("head")
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.astype(np.float32).ravel())
    me.loops.add(len(F) * 4)
    me.loops.foreach_set("vertex_index", F.astype(np.int32).ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set("loop_start", (np.arange(len(F)) * 4).astype(np.int32))
    me.polygons.foreach_set("loop_total", np.full(len(F), 4, np.int32))
    me.update(calc_edges=True)
    me.polygons.foreach_set("use_smooth", np.full(len(F), True))
    head = bpy.data.objects.new("head", me)
    sc.collection.objects.link(head)
    wm = bpy.data.materials.new("white")
    wm.use_nodes = True
    wm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
    wm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    head.data.materials.append(wm)
    sc.render.film_transparent = True
    # the lenses cast their tint, not a black shadow: a filter for shadow rays (frame3d's lens material)
    lens_f = frame3d.materials_for("F05")["lens"]
    for p in keep:
        if "lens" in p.name:
            p.data.materials.clear()
            p.data.materials.append(lens_f)
        p.visible_camera = False
    with_ = render("shadow_with")
    for p in keep:
        p.hide_render = True
    without = render("shadow_without")
    ratio = with_[..., :3] / np.maximum(without[..., :3], 1e-5)
    np.save(os.path.join(a.outdir, "shadow.npy"), np.dstack([np.clip(ratio, 0, 1.5), without[..., 3:4]]).astype(np.float32))
print("done")
