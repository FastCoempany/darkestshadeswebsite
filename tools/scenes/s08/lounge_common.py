"""The lounge (S08) for M4 in F05: camera, lights and room shared by the background render and the glasses'
render. Blender world: metres, the camera at the origin looking down +Y, Z up; OpenCV camera space of the
portrait (x right, y down, z ahead) maps to it as (x, z, -y).

The camera is the portrait's own: 85 mm-equivalent on the original 2412 px width (f = 5695 px on the
doubled, mirrored, cropped portrait; principal point at its original centre), its picture widened to
the right for the room. The output is 4000 x 3000; the portrait sits at its left edge at 0.97025."""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import REPO, WORK  # noqa: E402,F401
import math

import bpy
import numpy as np
from mathutils import Vector

W_O, H_O = 4000, 3000
S_M = 3000.0 / 3092.0                  # the portrait's scale in the output
F_PX = 5695.0 * S_M                    # 5525.6
CX, CY = 1056.0 * S_M, 1546.0 * S_M    # 1024.6, 1500.0
FOCUS = 0.81                           # the eyes, metres along the axis
FSTOP = 5.6

# the room, metres
FLOOR = -0.85
WALL_Y = 1.55
HEAD = Vector((0.08, 0.81, 0.115))     # between the eyes

# lights: colour (linear), power (W), position, size (m), what they point at
LIGHTS = {
    # the reference room's magenta key, front right, above the eyes: on his face's front
    "key": {"color": (1.0, 0.20, 0.52), "power": 70.0, "pos": (1.05, 0.22, 0.62), "size": 0.6,
            "aim": (0.10, 0.88, 0.0), "spot": 38.0},
    # the blue from behind left (the scene's blue on the couch's far arm)
    "rim": {"color": (0.16, 0.30, 1.0), "power": 60.0, "pos": (-0.75, 1.10, 0.70), "size": 0.30,
            "aim": (0.05, 0.90, 0.0), "spot": 34.0},
    # the warm light on the wall's art, from above
    "wash": {"color": (1.0, 0.70, 0.42), "power": 34.0, "pos": (0.45, 1.10, 1.35), "size": 0.25,
             "aim": (0.40, WALL_Y, 0.20), "spot": 70.0},
}
# a warm lamp off to the right, low, beyond the arm: the chesterfield's red, read in a warm light
LIGHTS["lamp"] = {"color": (1.0, 0.62, 0.32), "power": 26.0, "pos": (1.30, 0.70, 0.05), "size": 0.06,
                  "aim": (0.30, 1.15, -0.25), "point": True}
# a small warm lamp above and to his right, a little behind him (over the couch): a kicker on his hair
# and his profile, and the highlight that runs along F05's top rims
LIGHTS["top"] = {"color": (1.0, 0.82, 0.62), "power": 14.0, "pos": (0.94, 1.07, 0.90), "size": 0.12,
                 "aim": (0.08, 0.81, 0.12)}
# a soft warm fill from beside the camera, low: the candles' and the room's glow on his near side
LIGHTS["fill"] = {"color": (1.0, 0.80, 0.66), "power": 3.0, "pos": (-0.30, -0.20, 0.30), "size": 1.2,
                  "aim": (0.08, 0.81, 0.10)}
CANDLES = [(-1.15, 1.30, -0.08), (-1.22, 1.42, -0.02), (-1.08, 1.45, 0.05)]


def setup_render(scale=1.0, samples=128, transparent=False):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.01
    sc.cycles.use_denoising = True
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.max_bounces = 6
    sc.render.film_transparent = transparent
    sc.render.resolution_x, sc.render.resolution_y = int(W_O * scale), int(H_O * scale)
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "32"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    return sc


def camera(sc, dof=True):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.rotation_euler = (math.radians(90), 0, 0)
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36.0
    cam.data.lens = F_PX * 36.0 / W_O
    cam.data.shift_x = -(CX - W_O / 2) / W_O
    cam.data.shift_y = (CY - H_O / 2) / W_O
    cam.data.clip_start = 0.02
    cam.data.dof.use_dof = dof
    cam.data.dof.focus_distance = FOCUS
    cam.data.dof.aperture_fstop = FSTOP
    cam.data.dof.aperture_blades = 7
    return cam


def world(sc, color=(0.0035, 0.0025, 0.0065)):
    w = bpy.data.worlds.new("lounge")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = 1.0
    return w


def aim(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def lights(sc, scale=1.0, only=None):
    obs = {}
    for name, L in LIGHTS.items():
        if only and name not in only:
            continue
        if L.get("point"):
            ld = bpy.data.lights.new(name, "POINT")
            ld.shadow_soft_size = L["size"]
        elif L.get("spot"):
            ld = bpy.data.lights.new(name, "SPOT")
            ld.spot_size = math.radians(L["spot"])
            ld.spot_blend = 0.6
            ld.shadow_soft_size = L["size"]
        else:
            ld = bpy.data.lights.new(name, "AREA")
            ld.shape = "DISK"
            ld.size = L["size"]
        ld.color = L["color"]
        ld.energy = L["power"] * scale
        ob = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(ob)
        ob.location = L["pos"]
        aim(ob, L["aim"])
        obs[name] = ob
    if not only or "candles" in only:
        for i, p in enumerate(CANDLES):
            ld = bpy.data.lights.new(f"candle{i}", "POINT")
            ld.color = (1.0, 0.46, 0.14)
            ld.energy = 2.2 * scale
            ld.shadow_soft_size = 0.015
            ob = bpy.data.objects.new(f"candle{i}", ld)
            sc.collection.objects.link(ob)
            ob.location = p
            obs[f"candle{i}"] = ob
    return obs


def cv_to_world_matrix(R, t_mm):
    """Frame mm (OpenCV pose R, t) -> Blender world metres, as a 4x4 for parts built in metres."""
    C = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], np.float64)
    M = np.eye(4)
    M[:3, :3] = C @ R
    M[:3, 3] = C @ np.asarray(t_mm, np.float64) * 0.001
    return M


def project(P):
    """World points (N, 3) -> output pixels (N, 2)."""
    P = np.asarray(P, np.float64)
    return np.stack([CX + F_PX * P[:, 0] / P[:, 1], CY - F_PX * P[:, 2] / P[:, 1]], 1)
