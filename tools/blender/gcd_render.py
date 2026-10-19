#!/usr/bin/env python3
"""Render the God Cloud Device (GCD) as a physical object: polished gold band, black onyx inlay.

Builds the 3D emblem straight from the vector master (brand/emblems/gcd/svg/gcd-geometry.svg:
id="outer" is the gold outline, id="aperture" the stone) with Blender's Python module (bpy),
then renders with Cycles on a transparent background.

    pip install bpy==5.2.2          # Blender as a Python module (Python 3.13)
    python3 tools/blender/gcd_render.py --size 1024 --samples 64            # quick check
    python3 tools/blender/gcd_render.py --size 4096 --samples 160 --views front,yaw35,yaw60
    python3 tools/blender/gcd_render.py --light lightbox --views yaw72 --anchors --out work/gcd   # for a composite
    python3 tools/blender/gcd_render.py --light lightbox --views yaw-57p31 --anchors --out work/gcd   # turned 57, tilted 31 (seen from above)

Real-world scale: the emblem is 0.98 x the temple face height long (about 11-12 mm on most
frames, see brand/emblems/gcd/README.md). The model is built at 12 mm so bevels and stone
recess read at true scale.
"""
import argparse
import math
import pathlib
import re
import sys

import bpy
import numpy as np
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
GEOM = ROOT / "brand" / "emblems" / "gcd" / "svg" / "gcd-geometry.svg"
PATHS_JSON = pathlib.Path(__file__).with_name("gcd_veins.json")
OUT = ROOT / "brand" / "emblems" / "gcd" / "render"

SVG_W, SVG_H = 1632.0, 589.0
LENGTH_M = 0.012                     # emblem length in metres (12 mm)
S = LENGTH_M / SVG_W                 # metres per SVG px

GOLD_DEPTH = 0.00060                 # gold plate thickness (0.6 mm)
GOLD_BEVEL = 0.00007                 # small polished radius on every edge
STONE_RECESS = 0.00006               # stone face sits 0.06 mm below the gold face
STONE_BEVEL = 0.00004


def srgb_to_linear(h):
    h = h.lstrip("#")
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)) + (1.0,)


def parse_path(d):
    """Absolute M/C/L/Z path -> list of closed subpaths, each a list of cubic segments (p0, c1, c2, p3)."""
    toks = re.findall(r"[MCLZmclz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    i, cmd, subs, cur, start, pt = 0, None, [], [], None, None
    while i < len(toks):
        t = toks[i]
        if t in "MCLZmclz":
            cmd = t
            i += 1
            if cmd in "Zz":
                if cur:
                    if np.linalg.norm(np.array(pt) - np.array(start)) > 1e-6:
                        cur.append((pt, pt, start, start))
                    subs.append(cur)
                cur, pt = [], start
            continue
        if cmd == "M":
            pt = start = (float(toks[i]), float(toks[i + 1]))
            i += 2
            cmd = "L"
        elif cmd == "C":
            c1 = (float(toks[i]), float(toks[i + 1]))
            c2 = (float(toks[i + 2]), float(toks[i + 3]))
            p3 = (float(toks[i + 4]), float(toks[i + 5]))
            cur.append((pt, c1, c2, p3))
            pt = p3
            i += 6
        elif cmd == "L":
            p3 = (float(toks[i]), float(toks[i + 1]))
            cur.append((pt, pt, p3, p3))
            pt = p3
            i += 2
        else:
            raise ValueError(f"unsupported path command {cmd}")
    if cur:
        subs.append(cur)
    return subs


def to_world(p):
    # SVG (x right, y down, origin top-left) -> Blender (x right, y up), centred on the emblem.
    return Vector(((p[0] - SVG_W / 2) * S, (SVG_H / 2 - p[1]) * S, 0.0))


def add_spline(curve, segs):
    sp = curve.splines.new("BEZIER")
    sp.bezier_points.add(len(segs) - 1)
    for k, (p0, c1, c2, p3) in enumerate(segs):
        bp = sp.bezier_points[k]
        bp.co = to_world(p0)
        bp.handle_right_type = bp.handle_left_type = "FREE"
        bp.handle_right = to_world(c1)
        prev = segs[k - 1]
        bp.handle_left = to_world(prev[2])
    sp.use_cyclic_u = True
    sp.resolution_u = 24


def curve_object(name, subpaths, depth, bevel, z, offset=0.0):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    cu.extrude = depth / 2
    cu.bevel_depth = bevel
    cu.bevel_resolution = 6
    cu.offset = offset
    for segs in subpaths:
        add_spline(cu, segs)
    ob = bpy.data.objects.new(name, cu)
    ob.location.z = z
    bpy.context.scene.collection.objects.link(ob)
    return ob


def gold_material():
    m = bpy.data.materials.new("GCD gold")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    # Specular color of a warm yellow gold, tuned so the lit front face averages close to brand
    # flat gold #C6A36A under the studio light below.
    b.inputs["Base Color"].default_value = srgb_to_linear("#D6A964")
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.2
    if "Anisotropic" in b.inputs:
        b.inputs["Anisotropic"].default_value = 0.15
    return m


def onyx_material(vein_png):
    m = bpy.data.materials.new("GCD onyx")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.035
    b.inputs["IOR"].default_value = 1.54
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.15
        b.inputs["Coat Roughness"].default_value = 0.02
    # Polished black onyx: almost no diffuse; what reads is reflection. Veins stay faint.
    base = (0.0002, 0.0002, 0.00025, 1.0)
    vein_col = srgb_to_linear("#2C2C2B")
    if vein_png is None:
        b.inputs["Base Color"].default_value = base
        return m
    # Object coords -> SVG uv so the veins sit where the master puts them.
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    u = nt.nodes.new("ShaderNodeMath"); u.operation = "MULTIPLY_ADD"
    u.inputs[1].default_value = 1 / (SVG_W * S); u.inputs[2].default_value = 0.5
    nt.links.new(sep.outputs["X"], u.inputs[0])
    v = nt.nodes.new("ShaderNodeMath"); v.operation = "MULTIPLY_ADD"
    v.inputs[1].default_value = 1 / (SVG_H * S); v.inputs[2].default_value = 0.5
    nt.links.new(sep.outputs["Y"], v.inputs[0])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(u.outputs[0], comb.inputs["X"])
    nt.links.new(v.outputs[0], comb.inputs["Y"])
    img = nt.nodes.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(str(vein_png))
    img.image.colorspace_settings.name = "Non-Color"
    img.extension = "CLIP"
    nt.links.new(comb.outputs["Vector"], img.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs["A"].default_value = base
    mix.inputs["B"].default_value = vein_col
    nt.links.new(img.outputs["Color"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    return m


def vein_texture(path):
    """Draw the sparse veins from the vector master as a soft greyscale map (0 = stone, 1 = vein)."""
    import json
    from PIL import Image, ImageDraw, ImageFilter
    if not PATHS_JSON.exists():
        return None
    data = json.loads(PATHS_JSON.read_text())
    w, h = int(SVG_W), int(SVG_H)
    im = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(im)
    for line in data["veins"]:
        dr.line([tuple(p) for p in line], fill=110, width=2, joint="curve")
    for line in data["veins"]:
        dr.line([tuple(p) for p in line], fill=200, width=1)
    im = im.filter(ImageFilter.GaussianBlur(1.1))
    im.save(path)
    return path


def setup_scene(size, samples, light="studio"):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.resolution_x = size
    sc.render.resolution_y = int(round(size * SVG_H / SVG_W * 1.12))
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "16"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    if light == "lightbox":
        lightbox_world(sc)
        return
    # Studio HDRI that ships with Blender, for believable metal reflections.
    world = bpy.data.worlds.new("studio")
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(pathlib.Path(bpy.utils.system_resource("DATAFILES")) / "studiolights" / "world" / "studio.exr"))
    bg = nt.nodes["Background"]
    bg.inputs["Strength"].default_value = 0.10
    clamp = nt.nodes.new("ShaderNodeVectorMath")
    clamp.operation = "MINIMUM"
    clamp.inputs[1].default_value = (1.2, 1.2, 1.2)   # keep the HDRI's soft boxes from blowing out polished faces
    nt.links.new(env.outputs["Color"], clamp.inputs[0])
    nt.links.new(clamp.outputs["Vector"], bg.inputs["Color"])


def lightbox_world(sc):
    """A light tent: bright all round, brightest overhead, a grey floor. Matches the lightbox shots."""
    world = bpy.data.worlds.new("lightbox")
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")          # view-direction Z: -1 floor .. +1 overhead -> 0..1
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.30, 0.30, 0.30, 1)
    els[1].position, els[1].color = 1.0, (1.15, 1.15, 1.15, 1)
    mid = els.new(0.5)
    mid.color = (0.78, 0.78, 0.78, 1)
    bg = nt.nodes["Background"]
    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])


def anchors(gold, cam):
    """2D pixel positions of the emblem's bounding-box anchors on its front face (for compositing)."""
    from bpy_extras.object_utils import world_to_camera_view
    pts = []
    for segs in parse_path(re.search(r'id="outer"\s+d="([^"]+)"', GEOM.read_text()).group(1)):
        for p0, c1, c2, p3 in segs:
            for t in np.linspace(0, 1, 9):
                pts.append((1 - t) ** 3 * np.array(p0) + 3 * (1 - t) ** 2 * t * np.array(c1)
                           + 3 * (1 - t) * t ** 2 * np.array(c2) + t ** 3 * np.array(p3))
    pts = np.array(pts)
    (x0, y0), (x1, y1) = pts.min(axis=0), pts.max(axis=0)
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    named = {"center": (xm, ym), "left": (x0, ym), "right": (x1, ym), "top": (xm, y0), "bottom": (xm, y1)}
    bpy.context.view_layer.update()
    sc = bpy.context.scene
    W, H = sc.render.resolution_x, sc.render.resolution_y
    out = {}
    for k, (x, y) in named.items():
        local = to_world((x, y)) + Vector((0, 0, GOLD_DEPTH / 2))
        co = world_to_camera_view(sc, cam, gold.matrix_world @ local)
        out[k] = [round(co.x * W, 2), round((1 - co.y) * H, 2)]
    out["bbox_svg"] = [round(float(v), 2) for v in (x0, y0, x1, y1)]
    out["length_m"] = LENGTH_M
    return out


def look_at(ob, target, up=(0.0, 0.0, 1.0)):
    """Point an object's -Z at target with its +Y as close to `up` as possible (no accidental roll)."""
    f = (Vector(target) - ob.location).normalized()
    r = f.cross(Vector(up)).normalized()
    u = r.cross(f)
    from mathutils import Matrix
    m = Matrix((r, u, -f)).transposed()
    ob.rotation_euler = m.to_euler()


def add_area(name, loc, size, energy, aim=(0, 0, 0), size_y=None, color=(1, 1, 1)):
    li = bpy.data.lights.new(name, "AREA")
    li.shape = "RECTANGLE"
    li.size = size
    li.size_y = size_y or size
    li.energy = energy
    li.color = color
    ob = bpy.data.objects.new(name, li)
    ob.location = loc
    bpy.context.scene.collection.objects.link(ob)
    look_at(ob, aim)
    return ob


def add_camera(view):
    """Camera on -Y looking at the emblem: orthographic for "front", a 100 mm lens for "yawNN"."""
    cam = bpy.data.cameras.new("cam")
    ob = bpy.data.objects.new("cam", cam)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    if view == "front":
        cam.type = "ORTHO"
        cam.ortho_scale = LENGTH_M * 1.06
        ob.location = (0.0, -0.2, 0.0)
    else:
        cam.lens = 100
        cam.sensor_width = 36
        cam.clip_start = 0.001
        ob.location = (0.0, -0.05, 0.0)
    look_at(ob, (0.0, 0.0, 0.0))
    return ob


PHONE_DEG = 6.0                      # angular radius of the phone body seen from the frame
RING_MIN_YAW = 12.0                  # below this a flat face mirrors the ring light: glare


def phone_and_ring(cam, view):
    """The phone as the emblem sees it: a black disk around the lens that only reflections see
    (camera, shadow and diffuse rays pass through it), and the ring light around it. A face turned
    nearly to the camera would mirror the ring as glare, so near-frontal views go without it; the
    tent's light carries them."""
    d = (cam.location - Vector((0, 0, 0))).length
    bpy.ops.mesh.primitive_circle_add(vertices=48, fill_type="NGON", radius=d * math.tan(math.radians(PHONE_DEG)),
                                      location=cam.location + Vector((0, 0.002, 0)), rotation=(math.radians(90), 0, 0))
    body = bpy.context.active_object
    mat = bpy.data.materials.new("phone")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1)
    bsdf.inputs["Roughness"].default_value = 0.6
    body.data.materials.append(mat)
    body.visible_camera = False
    body.visible_shadow = False
    body.visible_diffuse = False
    body.visible_transmission = False
    if math.degrees(math.hypot(yaw_of(view), pitch_of(view))) >= RING_MIN_YAW:
        ring = bpy.data.lights.new("ring", "AREA")
        ring.shape = "DISK"
        ring.size = 0.02
        ring.energy = 0.25
        ob = bpy.data.objects.new("ring", ring)
        ob.location = cam.location
        bpy.context.scene.collection.objects.link(ob)
        look_at(ob, (0, 0, 0))


def yaw_of(view):
    """"yaw35", "yaw-16", or with a pitch, "yaw-20p55" (a temple seen from above: its face tilted
    away at the top as well as turned)."""
    m = re.match(r"yaw(-?[\d.]+)", view)
    return math.radians(float(m.group(1))) if m else 0.0


def pitch_of(view):
    m = re.search(r"p(-?[\d.]+)$", view)
    return math.radians(float(m.group(1))) if m else 0.0


def stand_up(gold, view):
    """Turn the emblem upright, front face toward the camera on -Y, then turn it by the view's yaw
    (a temple seen at an angle) and tilt it back by the pitch (seen from above). The stone is
    parented to the gold."""
    gold.rotation_euler = (math.radians(90.0) + pitch_of(view), 0.0, yaw_of(view))
    gold.location = (0.0, 0.0, 0.0)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    svg = GEOM.read_text()
    outer = re.search(r'id="outer"\s+d="([^"]+)"', svg).group(1)
    aperture = re.search(r'id="aperture"\s+d="([^"]+)"', svg).group(1)
    outer_sp, ap_sp = parse_path(outer), parse_path(aperture)
    gold = curve_object("gold", outer_sp + ap_sp, GOLD_DEPTH, GOLD_BEVEL, 0.0)
    stone = curve_object("onyx", ap_sp, GOLD_DEPTH - 2 * STONE_RECESS, STONE_BEVEL, -STONE_RECESS, offset=0.0)
    stone.parent = gold
    gold.data.materials.append(gold_material())
    vein_png = vein_texture(OUT / "_veins.png")
    stone.data.materials.append(onyx_material(vein_png))
    return gold, stone


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--views", default="front")
    ap.add_argument("--light", choices=["studio", "lightbox"], default="studio",
                    help="studio: dark product table (catalog masters); lightbox: bright tent, for composites on the lightbox shots")
    ap.add_argument("--out", default=str(OUT), help="output folder (default brand/emblems/gcd/render)")
    ap.add_argument("--anchors", action="store_true", help="also write <name>.json with the 2D anchors used for compositing")
    ap.add_argument("--relief", type=float, default=None,
                    help="mm the gold stands proud of the temple in a composite (default: the full 0.6 mm plate)")
    a = ap.parse_args(argv)
    global GOLD_DEPTH
    if a.relief is not None:
        GOLD_DEPTH = a.relief / 1000.0 + 2 * STONE_RECESS
    out_dir = pathlib.Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for view in a.views.split(","):
        gold, stone = build()
        setup_scene(a.size, a.samples, a.light)
        stand_up(gold, view)
        if a.light == "lightbox":
            # retoucher's choice for catalog images: keep polished onyx reading black under the
            # tent's bright surround (half the specular, a touch of satin)
            for m in stone.data.materials:
                bsdf = m.node_tree.nodes["Principled BSDF"]
                bsdf.inputs["Specular IOR Level"].default_value = 0.22
                bsdf.inputs["Roughness"].default_value = 0.12
                if "Coat Weight" in bsdf.inputs:
                    bsdf.inputs["Coat Weight"].default_value = 0.0
            cam = add_camera(view)
            phone_and_ring(cam, view)
            name = f"gcd-3d-{view}-lightbox-{a.size}"
            render_to(out_dir / f"{name}.png")
            if a.anchors:
                import json
                (out_dir / f"{name}.json").write_text(json.dumps(anchors(gold, cam), indent=1))
            continue
        # Product-table lighting: big soft box overhead and slightly in front (gradient down the
        # gold face). For the straight-on master, a narrow strip on the right for a clean edge
        # line and a dim fill from below-left.
        add_area("top", (0.0, -0.03, 0.08), 0.10, 3.0, size_y=0.04)
        if view == "front":
            add_area("strip", (0.07, -0.035, 0.01), 0.008, 2.5, size_y=0.08)
            add_area("fill", (-0.06, -0.06, -0.03), 0.06, 0.6)
        # A dim card where the flat gold face mirrors the camera ray, a little high, so every
        # view gets the same soft gradient on the face instead of a random hot spot.
        t = 2 * yaw_of(view)
        add_area("card", (0.12 * math.sin(t), -0.12 * math.cos(t), 0.035), 0.14, 0.035, size_y=0.06)
        cam = add_camera(view)
        name = f"gcd-3d-{view}-{a.size}"
        render_to(out_dir / f"{name}.png")
        if a.anchors:
            import json
            (out_dir / f"{name}.json").write_text(json.dumps(anchors(gold, cam), indent=1))
    (OUT / "_veins.png").unlink(missing_ok=True)


def render_to(path):
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print("wrote", path)


if __name__ == "__main__":
    main(sys.argv[1:])
