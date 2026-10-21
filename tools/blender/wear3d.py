#!/usr/bin/env python3
"""A cast member wearing a frame rebuilt in 3D (tools/blender/frame3d.py), rendered in the scene's light
and composited into the portrait by differential rendering.

    python3 tools/blender/wear3d.py content/photography/people/M1-S06-F04-A1.json [--samples 128]
    python3 tools/blender/wear3d.py <settings> --composite-only      # re-composite the last renders

The flat composites (tools/photo/wear.py) looked pasted on, every version (founder, Oct 21 2026): a
product photo is a flat front view lit by a light tent. Here the frame is a 3D object on a 3D head:

- the camera: the portraits' lens (85 mm on full frame), level at the eyes' height (prompted at eye
  level, the head in the picture's upper half: the picture is cropped below the lens's axis);
- the head: a depth map of the portrait (head3d.py), in millimetres from the face's 3D landmarks at
  the scale the person's pupillary distance gives;
- the frame: built from its 1:1 drawings, turned with the head, its nose pads resting on the nose
  (the depth at which they touch the depth map), its lenses in front of the eyes, its temples running
  back to the ears;
- the light: the scene's key, a softbox (its direction read off the face's shading and its nose
  shadow; head3d.light_scores reports the best Lambertian fits) and a dim room, set so a white card
  at the face reads as the portrait's lit skin would at 40%;
- the renders (Cycles): the head alone, white, and the head with the frame casting its shadows (the
  lenses as filters of their measured tint), whose ratio darkens the portrait where the frame shades
  it (only on the face, and only as far as the portrait is lit there); the front and lenses, the head
  behind them showing the shaded portrait (each lens shows the face through its tint, `through_lens`
  of it where the founder wants dark lenses to all but hide the eyes; the frame's inner edges mirror
  the skin); the temples, hidden behind the head where it is in front of them;
- the composite: the portrait times the shadow ratio, the temples over it, the front and lenses over
  those; the frame layers matched to the photograph (its softness, black level and grain), the scene's
  grade over the whole picture, and the crop (3:4 to the gallery's 4:5), as tools/photo/wear.py does.

Writes work/people/<id>-3d/: composite.png (16-bit, the crop), composite.jpg, compare.jpg (before and
after), zoom.jpg (the frame at 1:1), report.json, layers/ (the renders).
"""
import json
import math
import os
import pathlib
import sys

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import bpy  # noqa: E402
import cv2  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "blender"))
sys.path.insert(0, str(ROOT / "tools" / "photo"))
import frame3d  # noqa: E402
import head3d  # noqa: E402

MM = 0.001
F_MM, SENSOR_H = 85.0, 36.0           # the portraits' lens, prompted (reference/casting/prompt-pack.md)

# The scenes' light: the key's direction seen from the subject (azimuth + to the camera's right,
# elevation + up), its size (m) and distance (m); fill: the room's light on the face against the key's
# (a white card's level); room: how the room's brightness runs from overhead to the floor (what the
# frame's gloss mirrors).
SCENES = {
    "S06": {"key": {"az": -45.0, "el": 25.0, "size": 0.9, "size_y": 1.2, "dist": 1.6}, "fill": 0.03,
            "room": {"top": 2.0, "bottom": 0.1, "camera_side": 0.03}},
}


def lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def face_points(img_bgr):
    from wear import face_of
    return face_of(img_bgr)


def camera_space(L, H, W, f_px, s):
    """InsightFace's 3D landmarks to camera space (mm; x right, y up, the camera looking down -z): each
    point back-projected through the portrait's lens at its own depth."""
    D = f_px / s
    depth = head3d.landmark_depths(L, s, D)
    X = (L[:, 0] - head3d.cx_(W)) / f_px * depth
    Y = (head3d.cy_(H) - L[:, 1]) / f_px * depth
    return np.stack([X, Y, -depth], 1), D


def head_frame(P):
    """The head's axes in camera space: x from the right eye's outer corner to the left's, y up the face
    (chin to brow line), z out of the face."""
    x = P[45] - P[36]
    x /= np.linalg.norm(x)
    up = (P[19] + P[24]) / 2 - P[8]
    y = up - x * np.dot(up, x)
    y /= np.linalg.norm(y)
    z = np.cross(x, y)
    return np.stack([x, y, z], 1)


def project(Pw, H, W, f_px):
    """Camera-space points (mm) to image pixels and depth."""
    d = -Pw[:, 2]
    return head3d.cx_(W) + f_px * Pw[:, 0] / d, head3d.cy_(H) - f_px * Pw[:, 1] / d, d


def setup(W, H, samples):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "32"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    sc.render.use_border = True
    sc.render.use_crop_to_border = False
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.lens = F_MM
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = SENSOR_H
    cam.data.clip_start = 0.05
    return sc, cam


def room(sc, level, top, bottom, camera_side=0.0):
    """The world: a dim room, brighter overhead than at the floor (y is up here), normalised so a white
    card facing the room's middle reads `level`; and the studio behind the camera (the side the
    subject faces, +z), lit by the key's spill: what a lens and the frame's face mirror."""
    world = bpy.data.worlds.new("room")
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = bottom * level / ((top + bottom) / 2)
    mr.inputs["To Max"].default_value = top * level / ((top + bottom) / 2)
    nt.links.new(sep.outputs["Y"], mr.inputs["Value"])
    wall = nt.nodes.new("ShaderNodeMapRange")
    wall.inputs["From Min"].default_value = 0.2
    wall.inputs["From Max"].default_value = 0.6
    wall.inputs["To Min"].default_value = 0.0
    wall.inputs["To Max"].default_value = camera_side
    nt.links.new(sep.outputs["Z"], wall.inputs["Value"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(mr.outputs["Result"], add.inputs[0])
    nt.links.new(wall.outputs["Result"], add.inputs[1])
    bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (1, 1, 1, 1)
    nt.links.new(add.outputs["Value"], bg.inputs["Strength"])
    return world


def key_light(target, k, power):
    az, el = math.radians(k["az"]), math.radians(k["el"])
    d = Vector((math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)))
    li = bpy.data.lights.new("key", "AREA")
    if k.get("size_y"):                   # a softbox
        li.shape = "RECTANGLE"
        li.size, li.size_y = k["size"], k["size_y"]
    else:
        li.shape = "DISK"
        li.size = k["size"]
    li.energy = power
    ob = bpy.data.objects.new("key", li)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(target) + d * k["dist"]
    ob.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    return ob, np.array(d)


def card_value(sc, light_ob, ldir, eye_mid, ax, white, H, W, f_px, s, path):
    """What a white card at the eyes, square to this light, reads at 1 W (everything else hidden)."""
    c = eye_mid + ax[:, 2] * 25
    a1 = np.cross(ldir, [0, 1, 0])
    a1 /= np.linalg.norm(a1)
    a2 = np.cross(ldir, a1)
    card = mesh_object("card", np.array([c + 20 * (sx * a1 + sy * a2) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]),
                       np.array([[0, 1, 2, 3]]))
    card.data.materials.append(white)
    light_ob.data.energy = 1.0
    keep = sc.cycles.samples
    sc.cycles.samples = 16
    u, v, _ = project(c[None], H, W, f_px)
    bw = 12 * s
    sc.render.border_min_x, sc.render.border_max_x = (u[0] - bw) / W, (u[0] + bw) / W
    sc.render.border_min_y, sc.render.border_max_y = 1 - (v[0] + bw) / H, 1 - (v[0] - bw) / H
    cim = render(sc, path)
    sc.cycles.samples = keep
    bpy.data.objects.remove(card)
    return float(np.median(cim[int(v[0] - bw / 2):int(v[0] + bw / 2), int(u[0] - bw / 2):int(u[0] + bw / 2), :3]))


def glint(target, g, white):
    """A strip of light only reflections see (a narrow strip box near the camera, too small and too far
    to light the skin, bright enough to show in a glossy lens and along the frame's edges): `width` x
    `height` m, `dist` m from the face at (az, el) as the key is placed, its brightness `radiance`
    times a lit white card's."""
    az, el = math.radians(g["az"]), math.radians(g["el"])
    d = np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)])
    c = np.asarray(target, np.float64) + d * g["dist"] * 1000
    u = np.cross([0.0, 1.0, 0.0], d)
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    w2, h2 = g["width"] * 500, g["height"] * 500
    ob = mesh_object("glint", np.array([c - u * w2 - v * h2, c + u * w2 - v * h2, c + u * w2 + v * h2, c - u * w2 + v * h2]),
                     np.array([[0, 1, 2, 3]]))
    m = bpy.data.materials.new("glint")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = g["radiance"] * white
    nt.links.new(em.outputs[0], [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0].inputs["Surface"])
    ob.data.materials.append(m)
    ob.visible_camera = False
    ob.visible_diffuse = False
    ob.visible_shadow = False
    ob.visible_transmission = False
    return ob


def read_exr(path):
    """A render, linear RGBA, top row first (Blender reads it; this OpenCV has no EXR)."""
    im = bpy.data.images.load(str(path), check_existing=False)
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(h, w, 4)[::-1]


def mesh_object(name, V, F, UV=None):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", (V * MM).astype(np.float32).ravel())
    me.loops.add(F.size)
    me.loops.foreach_set("vertex_index", F.ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set("loop_start", np.arange(0, F.size, F.shape[1]))
    me.polygons.foreach_set("loop_total", np.full(len(F), F.shape[1]))
    me.update(calc_edges=True)
    me.polygons.foreach_set("use_smooth", np.ones(len(F), bool))
    if UV is not None:
        uvl = me.uv_layers.new(name="photo")
        uvl.data.foreach_set("uv", UV[F.ravel()].astype(np.float32).ravel())
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def white_material():
    m = bpy.data.materials.new("white")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    d = nt.nodes.new("ShaderNodeBsdfDiffuse")
    d.inputs["Color"].default_value = (1, 1, 1, 1)
    nt.links.new(d.outputs[0], [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0].inputs["Surface"])
    return m


def photo_material(rgb, through_lens=1.0):
    """The portrait (linear RGB, top row first) as light given off by the head: what the camera sees of
    the face through a lens, and what the frame's gloss mirrors of it."""
    H, W = rgb.shape[:2]
    im = bpy.data.images.new("photo", W, H, alpha=True, float_buffer=True)
    im.colorspace_settings.name = "Linear Rec.709"
    px = np.concatenate([rgb[::-1], np.ones((H, W, 1), np.float32)], -1).astype(np.float32)
    im.pixels.foreach_set(px.ravel())
    m = bpy.data.materials.new("photo")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = im
    tex.interpolation = "Cubic"
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "photo"
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    # seen through a lens: `through_lens` of it (the founder's direction for dark lenses, Oct 21 2026:
    # they almost completely hide the eyes); mirrored in the frame: all of it
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx = nt.nodes.new("ShaderNodeMapRange")
    mx.inputs["To Min"].default_value = 1.0
    mx.inputs["To Max"].default_value = through_lens
    nt.links.new(lp.outputs["Transmission Depth"], mx.inputs["Value"])     # any path through a lens
    nt.links.new(mx.outputs["Result"], em.inputs["Strength"])
    nt.links.new(em.outputs[0], [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0].inputs["Surface"])
    return m


def set_region(sc, cam, objs, margin, H, W):
    """Render only round these objects' image box, `margin` of its size added on every side."""
    from bpy_extras.object_utils import world_to_camera_view
    xs, ys = [], []
    bpy.context.view_layer.update()
    for p in objs:
        for v in p.bound_box:
            c = world_to_camera_view(sc, cam, p.matrix_world @ Vector(v))
            xs.append(c.x)
            ys.append(c.y)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    mx, my = (x1 - x0) * margin, (y1 - y0) * margin
    sc.render.border_min_x, sc.render.border_max_x = max(0, x0 - mx), min(1, x1 + mx)
    sc.render.border_min_y, sc.render.border_max_y = max(0, y0 - my), min(1, y1 + my)


def render(sc, path):
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return read_exr(path)


def world_points(ob, R, o):
    """An object's vertices (mm) after the rig's rotation R and origin o (mm)."""
    me = ob.data
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3) / MM
    M = np.asarray(ob.matrix_world)
    loc = co @ M[:3, :3].T + M[:3, 3] / MM
    return loc @ R.T + o


def place(parts, P, ax, kps, s, D, box, H, W, f_px, cfg, report):
    """Where the frame sits: square to the head (ax), centred on the nose, its lens centres
    `lens_drop_mm` below the pupils, and as far back as its nose pads go before they touch the nose
    (the depth map); then forward again if the front's back would touch the cheeks or brows."""
    R = ax
    eyes = []
    for (u, v), grp in zip(sorted(kps[:2].tolist()), (range(36, 42), range(42, 48))):
        depth = -P[list(grp), 2].mean()
        eyes.append(np.array([(u - head3d.cx_(W)) / f_px * depth, (head3d.cy_(H) - v) / f_px * depth, -depth]))
    pupil_mid = (eyes[0] + eyes[1]) / 2
    nose = (P[27] + P[28]) / 2
    o0 = pupil_mid + R[:, 0] * np.dot(nose - pupil_mid, R[:, 0]) - R[:, 1] * cfg.get("lens_drop_mm", 3.0)
    pads = [p for p in parts if " pad " in p.name]
    front = [p for p in parts if p.name.endswith(" front")][0]
    lenses = [p for p in parts if " lens " in p.name]
    pad_pts = np.concatenate([world_points(p, np.eye(3), np.zeros(3)) for p in pads])
    front_pts = world_points(front, np.eye(3), np.zeros(3))
    back_pts = front_pts[front_pts[:, 2] < np.percentile(front_pts[:, 2], 30)][::7]
    lens_pts = np.concatenate([world_points(p, np.eye(3), np.zeros(3)) for p in lenses])[::11]

    def penetration(pts, t):
        w = pts @ R.T + o0 + R[:, 2] * t
        u, v, d = project(w, H, W, f_px)
        surf = head3d.sample_depth(D, box, u, v)
        return d - surf                                  # > 0: behind the skin

    lo, hi = -60.0, 80.0
    for _ in range(60):                                  # the pads just touching the nose
        mid = (lo + hi) / 2
        if np.nanmax(penetration(pad_pts, mid)) > 0:
            lo = mid
        else:
            hi = mid
    t_pads = hi
    cornea = pupil_mid + R[:, 2] * 3.0

    def vertex_at(t_):
        lens_c = np.concatenate([world_points(p, R, o0 + R[:, 2] * t_) for p in lenses])
        return float(np.min(np.abs((lens_c - cornea) @ R[:, 2])))

    # seated: the lenses `vertex_mm` from the corneas, as a fitted frame sits (the pads then press into
    # the nose's soft sides a little); not nearer the cheeks or brows than `clearance_mm`
    t = t_pads
    if cfg.get("vertex_mm"):
        t = t_pads - (vertex_at(t_pads) - cfg["vertex_mm"])
    clearance = cfg.get("clearance_mm", 1.5)
    clear = float(-np.nanmax(penetration(back_pts, t)))
    lens_clear = float(-np.nanmax(penetration(lens_pts, t)))
    need = max(clearance - clear, clearance - lens_clear, 0.0)
    t += need
    o = o0 + R[:, 2] * t
    report["placement"] = {"origin_mm": [round(float(v), 1) for v in o], "pads_touch_at_mm": round(t_pads, 1),
                           "seated_at_mm": round(t, 1), "pads_into_nose_mm": round(float(np.nanmax(penetration(pad_pts, t))), 1),
                           "rim_to_skin_mm": round(clear + need, 1), "lens_to_skin_mm": round(lens_clear + need, 1),
                           "vertex_mm": round(vertex_at(t), 1)}
    return o


def ears_local(P, ax, o, hinges, cfg):
    """Where each temple rests on the ear's root, in the frame's coordinates (mm): as wide as the face's
    outline at the jaw's ends, `temple_back_mm` behind the hinge and a little below it."""
    half = abs(np.dot(P[16] - P[0], ax[:, 0])) / 2 + 2.0
    back = cfg.get("temple_back_mm", 95.0)
    out = []
    for h in hinges:
        side = np.sign(h[0])
        out.append((side * half, h[1] - 6.0, h[2] - back))
    return out


def main(cfg_path, samples=128):
    cfg = json.loads(pathlib.Path(cfg_path).read_text())
    out = ROOT / "work" / "people" / (cfg["id"] + "-3d")
    (out / "layers").mkdir(parents=True, exist_ok=True)
    k = int(cfg.get("upscale", 2))
    raw = ROOT / cfg["portrait"]
    up = raw.with_name(f"{raw.stem}-x{k}.png")
    img = cv2.imread(str(up if up.exists() else raw), cv2.IMREAD_COLOR)
    H, W = img.shape[:2]
    lin = img[..., ::-1].astype(np.float32) / 255
    lin = np.where(lin <= 0.04045, lin / 12.92, ((lin + 0.055) / 1.055) ** 2.4).astype(np.float32)
    if COMPOSITE_ONLY and (out / "layers" / "front.exr").exists():
        report = json.loads((out / "report.json").read_text())
    else:
        report = render_layers(cfg, out, img, lin, H, W, samples)
    composite(cfg, out, img, lin, H, W, report)


def render_layers(cfg, out, img, lin, H, W, samples):
    face = face_points(img)
    eyes = np.array(sorted(face.kps[:2].tolist()), np.float64)
    s = float(np.linalg.norm(eyes[1] - eyes[0])) / cfg.get("pd_mm", 62.0)
    f_px = H * F_MM / SENSOR_H
    head3d.PP = (W / 2, float(eyes[:, 1].mean()) if cfg.get("eye_level", True) else H / 2)
    L = face.landmark_3d_68.astype(np.float64)
    P, D_eyes = camera_space(L, H, W, f_px, s)
    ax = head_frame(P)
    report = {"id": cfg["id"], "px_per_mm": round(s, 3), "distance_mm": round(D_eyes, 1)}
    D, box, fit = head3d.depth_map(img, face, s, f_px)
    report["depth_fit"] = fit
    sc_ = head3d.light_scores(lin, face, D, box, f_px, H, W)
    best = sorted(sc_.items(), key=lambda t: -t[1])[:3]
    report["light_fit"] = [{"az": a, "el": e, "r": round(r, 3)} for (a, e), r in best]

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc, cam = setup(W, H, samples)
    cam.data.shift_x = (head3d.cx_(W) - W / 2) / max(W, H)
    cam.data.shift_y = -(H / 2 - head3d.cy_(H)) / max(W, H)
    report["principal_point"] = [round(head3d.cx_(W), 1), round(head3d.cy_(H), 1)]
    spec = json.loads(json.dumps(SCENES[cfg["scene"]]))
    for k_, v_ in cfg.get("scene_spec", {}).items():
        spec[k_] = dict(spec.get(k_, {}), **v_) if isinstance(v_, dict) and isinstance(spec.get(k_), dict) else v_
    spec["key"] = dict(spec["key"], **cfg.get("key", {}))
    report["key_used"] = spec["key"]

    # the frame
    tint = cfg.get("lens_tint") or lens_tint(cfg)
    report["lens_tint"] = [round(float(v), 4) for v in tint]
    mats = frame3d.materials_for(cfg["frame"], tint)
    parts, sh, hinges = frame3d.build(cfg["frame"], mats, tilt=cfg.get("tilt"))
    o = place(parts, P, ax, face.kps, s, D, box, H, W, f_px, cfg, report)
    ears = ears_local(P, ax, o, hinges, cfg)
    creases = ear_creases(L, s, cfg)
    for k_, h in enumerate(hinges):
        side = "left" if h[0] < 0 else "right"           # as the camera sees it
        if creases.get(side) is not None:
            ears[k_] = crease_point(creases[side], h, ax, o, H, W, f_px, cfg.get("ear_depth_mm", 85.0))
    report["ear_creases"] = {k_: (None if v is None else [round(float(c), 1) for c in v]) for k_, v in creases.items()}
    tmpl = frame3d.temples(cfg["frame"], hinges, mats, ears=ears, split=True)
    rig = bpy.data.objects.new("glasses", None)
    sc.collection.objects.link(rig)
    for p in parts + tmpl:
        p.parent = rig
    rig.matrix_world = Matrix.Translation(Vector(o * MM)) @ Matrix(ax.tolist()).to_4x4()
    front_objs = parts                                  # front, lenses, pads, end pieces

    # the head
    V, F, UV = head3d.mesh(D, box, H, W, f_px)
    head = mesh_object("head", V, F, UV)
    white = white_material()
    head.data.materials.append(white)

    # the light, calibrated on a white card facing the key at the eyes
    eye_mid = (P[36:42].mean(0) + P[42:48].mean(0)) / 2
    key, kdir = key_light(eye_mid * MM, spec["key"], 1.0)
    room(sc, 0.0, spec["room"]["top"], spec["room"]["bottom"])
    for p in front_objs + tmpl + [head]:
        p.hide_render = True
    card_val = card_value(sc, key, kdir, eye_mid, ax, white, H, W, f_px, s, out / "layers" / "card.exr")
    eu, ev = eye_mid_px(eye_mid, H, W, f_px)
    skin_box = lin[int(ev - 40 * s):int(ev + 40 * s), int(eu - 60 * s):int(eu + 60 * s)]
    skin = float(np.percentile(lum(skin_box), 90))
    target = skin / cfg.get("skin_albedo", 0.4)
    power = target / max(card_val, 1e-9)
    key.data.energy = power
    room(sc, spec["fill"] * target, spec["room"]["top"], spec["room"]["bottom"],
         spec["room"].get("camera_side", 0.0) * target)
    report["light"] = {"card_at_1W": round(card_val, 6), "skin_lin": round(skin, 3), "key_W": round(power, 1),
                       "room": round(spec["fill"] * target, 4)}

    # a window: the key only through a hole in a black card between it and the face (a band of light
    # across the eyes, a patch on one side), everything else falling to `dark` of what it was. Its
    # light on the face: the head lit by the key alone, through the card over without it.
    win_light = None
    if spec.get("window"):
        wn = spec["window"]
        cards = window_card(eye_mid, kdir, spec["key"]["dist"] * 1000, wn)
        for g in cards:
            g.hide_render = True
        room(sc, 0.0, 1.0, 1.0)
        head.hide_render = False
        sc.cycles.samples = max(16, samples // 2)
        set_region(sc, cam, [head], 0.0, H, W)
        k_open = render(sc, out / "layers" / "key_open.exr")
        for g in cards:
            g.hide_render = False
        k_win = render(sc, out / "layers" / "key_window.exr")
        dark = wn.get("dark", 0.06)
        lit_ = lum(k_open[..., :3]) > 1e-4
        win_frac = np.zeros((H, W), np.float32)            # how much of the key gets through, 0..1
        win_frac[lit_] = np.clip(lum(k_win[..., :3])[lit_] / lum(k_open[..., :3])[lit_], 0, 1)
        win_factor = win_frac + dark * (1 - win_frac)
        off = dark
        if wn.get("relight"):
            # the portrait relit: its own light divided out (the head under the portrait's light: the
            # scene's key and room, calibrated on the same white card as the new key) and the new light
            # multiplied in: the hard key through the window, and outside it only the room's dim, flat
            # light (`ambient`, against a lit white card), not the old light turned down
            base = SCENES[cfg["scene"]]
            soft, sdir = key_light(eye_mid * MM, base["key"], 1.0)
            key.hide_render = True
            head.hide_render = True
            for g in cards:
                g.hide_render = True
            soft.data.energy = target / max(card_value(sc, soft, sdir, eye_mid, ax, white, H, W, f_px, s,
                                                       out / "layers" / "card_portrait.exr"), 1e-9)
            room(sc, base["fill"] * target, base["room"]["top"], base["room"]["bottom"],
                 base["room"].get("camera_side", 0.0) * target)
            head.hide_render = False
            set_region(sc, cam, [head], 0.0, H, W)
            e_old = lum(render(sc, out / "layers" / "portrait_light.exr")[..., :3])
            bpy.data.objects.remove(soft)
            key.hide_render = False
            for g in cards:
                g.hide_render = False
            e_ = np.maximum(e_old, 0.06 * target)          # never lift the portrait's own shadows
            # the new key's shading only on the lit face; elsewhere (the far ear, the hair) the depth
            # map's head lets in light the portrait shows never reached: there, the key as it falls
            # through the window on the portrait's own shading. Outside the window, `dark` of the
            # portrait as it was (dividing its old light out there, by the depth map's estimate of it,
            # printed that estimate's errors on the face as blotches)
            w_key = face_mask(L, s, H, W) * lit_weight(lin, s, skin)
            key_part = w_key * lum(k_win[..., :3]) / e_ + (1 - w_key) * win_frac
            win_factor = np.where(e_old > 1e-4, np.clip(key_part + dark * (1 - win_frac), 0, 1.6), dark)
        # where the head's mesh has gaps (it leaves out the steps in depth at the ears' and hair's edges),
        # the light carries on from round them, so the window's edge does not cut there
        cov = k_open[..., 3] > 0.5
        near = cv2.dilate(cov.astype(np.uint8), np.ones((31, 31), np.uint8)) > 0
        gaps = (near & ~cov).astype(np.uint8)
        scale = max(float(win_factor.max()), 1e-6)
        win_factor = cv2.inpaint(np.clip(win_factor / scale * 255, 0, 255).astype(np.uint8), gaps, 7,
                                 cv2.INPAINT_TELEA).astype(np.float32) / 255 * scale
        win_factor[~near] = off
        win_light = cv2.GaussianBlur(win_factor, (0, 0), 1.5)
        win_key = cv2.GaussianBlur(win_frac, (0, 0), 1.5)
        room(sc, spec["fill"] * target, spec["room"]["top"], spec["room"]["bottom"],
             spec["room"].get("camera_side", 0.0) * target)
        report["window"] = wn

    for g_ in ([spec["glint"]] if spec.get("glint") else []) + spec.get("glints", []):
        glint(eye_mid, g_, target)
    if spec.get("glint") or spec.get("glints"):
        report["glints"] = ([spec["glint"]] if spec.get("glint") else []) + spec.get("glints", [])

    # 1, 2: the head alone, white; and with the frame casting its shadows (not seen itself)
    head.hide_render = False
    sc.cycles.samples = samples
    set_region(sc, cam, front_objs, 0.7, H, W)
    bare = render(sc, out / "layers" / "bare.exr")
    edge = region_feather(sc, H, W, 0.25)
    for p in front_objs + tmpl:
        p.hide_render = False
        p.visible_camera = False
    for p in tmpl:
        p.visible_shadow = False          # they fall on the head's side, which the depth map flattens
    shaded = render(sc, out / "layers" / "shaded.exr")
    for p in tmpl:
        p.visible_shadow = True
    ratio = np.ones((H, W, 3), np.float32)
    lit = lum(bare[..., :3]) > 1e-5
    ratio[lit] = np.clip(shaded[..., :3][lit] / np.maximum(bare[..., :3][lit], 1e-7), 0, 1.0)
    w = shadow_weight(lin, L, s, skin, win_key if win_light is not None else None) * edge
    ratio = 1 - w[..., None] * (1 - ratio)
    if win_light is not None:
        ratio = ratio * win_light[..., None]          # the window's factor (its light, or the relit skin)
    np.save(out / "layers" / "ratio.npy", ratio.astype(np.float16))

    # 3: the front and lenses; the head shows the shaded portrait (through the lenses, in the gloss)
    head.data.materials.clear()
    head.data.materials.append(photo_material((lin * ratio).astype(np.float32), cfg.get("through_lens", 1.0)))
    head.visible_camera = False
    for p in front_objs:
        p.visible_camera = True
    set_region(sc, cam, front_objs, 0.04, H, W)
    render(sc, out / "layers" / "front.exr")

    # 4: the temples, the run from each hinge to where it goes in behind the ear, over the hair (the
    # depth map flattens the head's sides too much to hide them right); the part behind the ear is
    # never seen from the front
    for p in front_objs:
        p.visible_camera = False
    for p in tmpl:
        p.visible_camera = " back" not in p.name
    head.hide_render = True
    set_region(sc, cam, front_objs + tmpl, 0.04, H, W)
    render(sc, out / "layers" / "temples.exr")
    (out / "report.json").write_text(json.dumps(report, indent=1))
    return report


def window_card(target, kdir, light_mm, wn):
    """Black flags between the key and the face, square to the light, leaving a window that lets
    through a `width_mm` x `height_mm` patch of light at the face (centred on `target`, moved by
    `offset_mm`: right and up as the camera sees it). The flags above and below stand `dist_mm` in
    front of the face, those at the sides `side_dist_mm` (nearer the light, softer edges). Not seen by
    the camera."""
    d = np.asarray(kdir, np.float64) / np.linalg.norm(kdir)
    # the flags' edges run along the picture's horizontal as the light sees it, so a band of light
    # lies level across the face whatever the light's height (an edge square to the light would tilt)
    u = np.array([1.0, 0.0, 0.0]) - d[0] * d
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    black = bpy.data.materials.new("card")
    black.use_nodes = True
    black.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1)
    black.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
    big = 1500.0
    obs = []
    for which, gd in (("rows", wn.get("dist_mm", 250.0)), ("sides", wn.get("side_dist_mm", wn.get("dist_mm", 250.0)))):
        k = (light_mm - gd) / light_mm                   # the light's cone, flag to face
        w2, h2 = wn["width_mm"] / 2 * k, wn["height_mm"] / 2 * k
        ox, oy = [o * k for o in wn.get("offset_mm", (0.0, 0.0))]
        c = np.asarray(target, np.float64) + d * gd + u * ox + v * oy
        rects = ((-big, big, h2, big), (-big, big, -big, -h2)) if which == "rows" else \
            ((-big, -w2, -big, big), (w2, big, -big, big))
        for (x0, x1, y0, y1) in rects:
            V = np.array([c + u * x0 + v * y0, c + u * x1 + v * y0, c + u * x1 + v * y1, c + u * x0 + v * y1])
            ob = mesh_object("card", V, np.array([[0, 1, 2, 3]]))
            ob.data.materials.append(black)
            # they only cut the key: in a studio the flags stand by the lamp, out of the gloss's view
            ob.visible_camera = False
            ob.visible_glossy = False
            ob.visible_diffuse = False
            ob.visible_transmission = False
            obs.append(ob)
    return obs


def region_feather(sc, H, W, frac):
    """1 inside the rendered region, falling to 0 at its edges over `frac` of its smaller side (so the
    soft occlusion of the room's light, which runs on far below the frame, ends without a seam)."""
    x0, x1 = sc.render.border_min_x * W, sc.render.border_max_x * W
    y0, y1 = (1 - sc.render.border_max_y) * H, (1 - sc.render.border_min_y) * H
    f = frac * min(x1 - x0, y1 - y0)
    xx = np.arange(W)[None, :]
    yy = np.arange(H)[:, None]
    d = np.minimum(np.minimum(xx - x0, x1 - xx), np.minimum(yy - y0, y1 - yy))
    t = np.clip(d / f, 0, 1)
    return (t * t * (3 - 2 * t)).astype(np.float32)


def ear_creases(L, s, cfg):
    """Where each temple goes in behind the ear, as the camera sees it ("left", "right"): where the ear's
    top meets the head, 5 mm above the jaw line's top point (InsightFace's first and last contour
    points sit at the ear's root) and 1.5 mm out from it; or as the settings place it by hand
    (`ear_crease_px`, the 2x portrait's pixels)."""
    given = cfg.get("ear_crease_px", {})
    return {"left": tuple(given.get("left", (L[0, 0] - 1.5 * s, L[0, 1] - 5 * s))),
            "right": tuple(given.get("right", (L[16, 0] + 1.5 * s, L[16, 1] - 5 * s)))}


def crease_point(px, h, ax, o, H, W, f_px, back_mm):
    """A temple's rest on the ear in the frame's coordinates: on the camera's ray through the ear's
    crease, `back_mm` deeper than the hinge."""
    hw = ax @ np.asarray(h, np.float64) + o
    r = np.array([(px[0] - head3d.cx_(W)) / f_px, (head3d.cy_(H) - px[1]) / f_px, -1.0])
    e_w = r * (-hw[2] + back_mm)
    return tuple(ax.T @ (e_w - o))


def face_mask(L, s, H, W):
    """The face (its landmarks' outline and the forehead above the brows), 8 mm round, feathered."""
    m = np.zeros((H, W), np.uint8)
    pts = L[:, :2].copy()
    brow = L[17:27, :2].copy()
    brow[:, 1] -= 30 * s
    cv2.fillConvexPoly(m, cv2.convexHull(np.concatenate([pts, brow]).astype(np.int32)), 1)
    r = int(8 * s)
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1,) * 2)).astype(np.float32)
    return np.clip(cv2.GaussianBlur(m, (0, 0), 6 * s), 0, 1)


def lit_weight(lin, s, skin):
    """How lit the portrait is, read broadly (an 8 mm blur, so eyes, brows and nostrils count as lit
    skin): 1 from a quarter of the lit skin's level up."""
    return np.clip(cv2.GaussianBlur(lum(lin), (0, 0), 8 * s) / (0.25 * skin), 0, 1)


def shadow_weight(lin, L, s, skin, light=None):
    """Where the frame's shadows are believed (0..1): on the face, and as far as light falls there:
    the portrait's own light, or the window's (`light`, 0..1). The depth map has no back to the head,
    so in it the key reaches the far ear and cheek, which the portrait shows in the head's own shadow;
    a frame can take no key light from where none falls."""
    lw = lit_weight(lin, s, skin)
    if light is not None:
        lw = np.maximum(lw, light)
    return face_mask(L, s, *lin.shape[:2]) * lw


def eye_mid_px(eye_mid, H, W, f_px):
    u, v, _ = project(eye_mid[None], H, W, f_px)
    return float(u[0]), float(v[0])


def noise_level(img):
    """The portrait's grain: the spread of its fine detail in the flattest dark parts (sRGB, 0-1)."""
    g = img.mean(-1).astype(np.float32) / 255
    hp = g - cv2.GaussianBlur(g, (0, 0), 1.2)
    loc = cv2.GaussianBlur(np.abs(cv2.Sobel(cv2.GaussianBlur(g, (0, 0), 2.0), cv2.CV_32F, 1, 1)), (0, 0), 4)
    sel = (g < 0.25) & (loc < np.percentile(loc, 20))
    return float(np.std(hp[sel])) if sel.sum() > 1000 else 0.004


def composite(cfg, out, img, lin, H, W, report):
    ratio = np.load(out / "layers" / "ratio.npy").astype(np.float32)
    fr = read_exr(out / "layers" / "front.exr")
    tp = read_exr(out / "layers" / "temples.exr")
    look = cfg.get("look3d", {})
    sigma = look.get("soften_px", 0.6)
    black = np.percentile(lin.reshape(-1, 3), 0.2, axis=0).astype(np.float32)
    rng = np.random.default_rng(7)
    grain = look.get("grain", noise_level(img))

    def matched(layer):
        """A render made to sit in the photograph: as soft, the same black floor (the lens's flare in
        the whole picture), the same grain."""
        rgb, a = layer[..., :3], layer[..., 3:4]
        if sigma > 0:
            rgb = cv2.GaussianBlur(rgb, (0, 0), sigma)
            a = cv2.GaussianBlur(a, (0, 0), sigma)[..., None]
        rgb = rgb + black * a
        return rgb, a

    base = lin * ratio
    t_rgb, t_a = matched(tp)
    f_rgb, f_a = matched(fr)
    # the temples' own shadow where they lie along the head (the depth map's flattened sides cannot take
    # it in 3D): each visible temple's outline, moved away from the key by the gap between wire and hair
    # (about 2 mm), softened, darkening what lies under it
    k_ = report.get("key_used", {})
    if t_a.max() > 0.05 and k_:
        gap = look.get("temple_gap_mm", 2.0) * report["px_per_mm"]
        dx = -gap * math.tan(math.radians(k_.get("az", -45.0)))
        dy = gap * math.tan(math.radians(k_.get("el", 25.0)))
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        sh_ = cv2.warpAffine(t_a[..., 0], M, (W, H))
        sh_ = cv2.GaussianBlur(sh_, (0, 0), max(0.6 * gap / 2, 1.0))
        base = base * (1 - look.get("temple_shadow", 0.7) * np.clip(sh_, 0, 1))[..., None]
    comp = base * (1 - t_a) + t_rgb
    comp = comp * (1 - f_a) + f_rgb
    sys.path.insert(0, str(ROOT / "tools" / "photo"))
    from clean_lightbox import lin_to_srgb
    from wear import ss90
    srgb = lin_to_srgb(np.clip(comp, 0, 1))
    # grain where the renders are (the photograph has its own)
    cover = np.clip(np.maximum(f_a, t_a)[..., 0], 0, 1)
    n = rng.normal(0, grain, (H, W)).astype(np.float32)
    srgb = np.clip(srgb + (n * cover)[..., None], 0, 1)
    g = cfg.get("grade", True)
    gk = g if isinstance(g, dict) else {}
    final = ss90(srgb, size=H / 1280, **gk) if g else srgb
    before = ss90(lin_to_srgb(np.clip(lin, 0, 1)), size=H / 1280, **gk) if g else lin_to_srgb(lin)
    # the crop: a 3:4 portrait cut to the gallery's 4:5, a quarter of what goes from the top and the rest
    # from the bottom (the head sits in the upper half), as tools/photo/wear.py does
    x0, y0, x1, y1 = 0, 0, W, H
    k = int(cfg.get("upscale", 2))
    if cfg.get("crop"):
        x0, y0, x1, y1 = [int(round(v * k)) for v in cfg["crop"]]
    elif cfg.get("format") == "4:5" and H > round(W * 5 / 4):
        th = round(W * 5 / 4)
        y0 = round(0.25 * (H - th))
        y1 = y0 + th
    final, before = final[y0:y1, x0:x1], before[y0:y1, x0:x1]
    report["crop"] = [x0, y0, x1, y1]
    cv2.imwrite(str(out / "composite.png"), cv2.cvtColor((final * 65535 + 0.5).astype(np.uint16), cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(out / "composite.jpg"), cv2.cvtColor((final * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 94])
    hh = 1280
    ww = int(round(final.shape[1] * hh / final.shape[0]))
    sheet = np.hstack([cv2.resize(before, (ww, hh), interpolation=cv2.INTER_AREA), np.ones((hh, 16, 3), np.float32),
                       cv2.resize(final, (ww, hh), interpolation=cv2.INTER_AREA)])
    cv2.imwrite(str(out / "compare.jpg"), cv2.cvtColor((sheet * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 90])
    yy, xx = np.nonzero(f_a[..., 0] > 0.05)
    yy, xx = yy - y0, xx - x0
    pad = int(0.2 * np.ptp(xx))
    z = final[max(0, yy.min() - pad):yy.max() + pad, max(0, xx.min() - pad):xx.max() + pad]
    cv2.imwrite(str(out / "zoom.jpg"), cv2.cvtColor((z * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 94])
    report["frame_box"] = [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())]
    report["look"] = {"soften_px": sigma, "black": [round(float(v), 5) for v in black], "grain": round(grain, 4)}
    (out / "report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report))


def lens_tint(cfg):
    """The lens's measured transmission (median of the cleaned product shot's lens layer), per channel."""
    from PIL import Image
    po = ROOT / "work" / "out" / cfg["product_shot"]
    T = np.asarray(Image.open(po / "layers" / "lens.png"), np.float32) / 255
    T = np.where(T <= 0.04045, T / 12.92, ((T + 0.055) / 1.055) ** 2.4)
    l = lum(T)
    sel = l < 0.95
    vals = T[sel]
    keep = lum(vals) > 0.5 * np.median(l[sel])
    return np.median(vals[keep], axis=0)[:3].tolist()


COMPOSITE_ONLY = "--composite-only" in sys.argv

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--") and not a.isdigit()]
    samples = 128
    if "--samples" in sys.argv:
        samples = int(sys.argv[sys.argv.index("--samples") + 1])
    main(args[0], samples)
