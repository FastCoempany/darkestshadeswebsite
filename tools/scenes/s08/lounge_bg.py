"""The lounge behind M4: the black-painted brick wall with the new art (art.py), a distressed rustic red
leather chesterfield (its back, tufted and rolled, and its right arm), the room's light. M4 himself is a
card that only casts shadows (his cut-out at his depth). Rendered with the portrait's camera and depth of
field.

    python3 lounge_bg.py OUT.exr [--scale 0.25] [--samples 64]
"""
import os
import sys

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__))] + [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", d) for d in ("blender", "photo")]
from paths import REPO, WORK  # noqa: E402,F401
import argparse
import math

import bpy
import numpy as np
from mathutils import Vector

D = WORK
import lounge_common as LC  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--scale", type=float, default=0.25)
ap.add_argument("--samples", type=int, default=64)
ap.add_argument("--no-dof", action="store_true")
ap.add_argument("--no-man", action="store_true")
ap.add_argument("--border", default=None, help="x0,y0,x1,y1 in output px")
a = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = LC.setup_render(a.scale, a.samples)
cam = LC.camera(sc, dof=not a.no_dof)
LC.world(sc)
LC.lights(sc)
rng = np.random.default_rng(3)


# ---------------------------------------------------------------- meshes from grids
def grid_mesh(name, P, attrs=None, smooth=True):
    """A quad mesh from a (rows, cols, 3) grid of points, with optional per-point float attributes."""
    r, c = P.shape[:2]
    V = P.reshape(-1, 3)
    idx = np.arange(r * c).reshape(r, c)
    a_, b_, c_, d_ = idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]
    F = np.stack([a_.ravel(), b_.ravel(), c_.ravel(), d_.ravel()], 1)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.astype(np.float32).ravel())
    me.loops.add(len(F) * 4)
    me.loops.foreach_set("vertex_index", F.astype(np.int32).ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set("loop_start", (np.arange(len(F)) * 4).astype(np.int32))
    me.polygons.foreach_set("loop_total", np.full(len(F), 4, np.int32))
    me.update(calc_edges=True)
    me.validate()
    me.polygons.foreach_set("use_smooth", np.full(len(F), smooth))
    for k, v in (attrs or {}).items():
        at = me.attributes.new(k, "FLOAT", "POINT")
        at.data.foreach_set("value", np.asarray(v, np.float32).ravel())
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    return ob


def fix_normals(ob, toward):
    """Flip the mesh if its normals face away from a world point (the camera, here)."""
    me = ob.data
    n = np.zeros(len(me.polygons) * 3)
    me.polygons.foreach_get("normal", n)
    c = np.zeros(len(me.polygons) * 3)
    me.polygons.foreach_get("center", c)
    d = np.asarray(toward)[None] - c.reshape(-1, 3)
    if (np.sum(n.reshape(-1, 3) * d, 1) < 0).mean() > 0.5:
        me.flip_normals()


def seg_dist(px, py, ax, ay, bx, by):
    """Distance from points to the segment a-b, and the position along it (0..1)."""
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0, 1)
    return np.hypot(px - (ax + t * dx), py - (ay + t * dy)), t


def fbm(shape, cells, octaves, seed):
    r = np.random.default_rng(seed)
    import cv2
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cy, cx = max(2, int(cells[0] * 2 ** o)), max(2, int(cells[1] * 2 ** o))
        g = r.standard_normal((cy, cx)).astype(np.float32)
        out += amp * cv2.resize(g, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= 0.5
    return out / tot


# ---------------------------------------------------------------- the chesterfield
SEAT_Z = -0.43
RECLINE = math.radians(12)
Y0 = 1.20                       # the back's tufted face at the seat
VH = 0.34                       # the tufted face's height along its recline
DX, DV = 0.135, 0.105           # the diamond: button spacing across, rows up
ROWS_V = [0.075, 0.18, 0.285]
ARM_X = 0.45                    # the right arm's inner face
ARM_Y0, ARM_Y1 = 0.50, 1.32


def tufted(u, v, rows, u_off, vmax, A=0.034, sig=0.050, crease=0.009, cw=0.0062, seed=0):
    """Height (m, out of the face) of diamond tufting over (u, v): pillows that are rhombi between the
    folds joining each button to its two neighbours in the row above (and pleats from the outer rows to
    the edges), each pillow rounding up from its folds to its middle, the buttons pulled in deeper; and the
    buttons' places, the fold and wear masks. Buttons in `rows` (v), every DX across, alternate rows offset."""
    rj = np.random.default_rng(seed + 50)
    umin, umax = u.min() - DX, u.max() + DX
    B = []
    for k, vr in enumerate(rows):
        off = u_off + (DX / 2 if k % 2 else 0.0)
        for j in range(int(math.floor((umin - off) / DX)), int(math.ceil((umax - off) / DX)) + 1):
            un = off + j * DX
            B.append((un + rj.normal(0, 0.003), vr + rj.normal(0, 0.003), k, un))   # hand-set: off the grid
    B = np.array(B)
    segs = []
    for b_ in B:
        for c_ in B:
            if c_[2] == b_[2] + 1 and abs(abs(c_[3] - b_[3]) - DX / 2) < 1e-6:
                segs.append((b_[0], b_[1], c_[0], c_[1], 1.0))
        if b_[2] == 0:
            segs.append((b_[0], b_[1], b_[0], -0.03, 0.8))                 # pleats down to the seat
        if b_[2] == len(rows) - 1:
            segs.append((b_[0], b_[1], b_[0], vmax + 0.03, 0.85))          # pleats up into the roll
    dc = np.full(u.shape, np.inf)
    cm = np.zeros(u.shape)
    for (ax, ay, bx, by, wgt) in segs:
        d, t = seg_dist(u, v, ax, ay, bx, by)
        dc = np.minimum(dc, d / wgt)
        cm = np.maximum(cm, wgt * np.exp(-(d / cw) ** 2))
    half = DX * DV / math.hypot(DX / 2, DV) / 2                           # a rhombus's half width across
    mfr = np.clip(dc / half, 0, 1)
    h = A * np.sin(np.pi / 2 * mfr) ** 0.6
    # each pillow filled a little differently
    h *= 1 + 0.18 * fbm(u.shape, (3 * u.shape[0] / 130 + 2, 3 * u.shape[1] / 130 + 2), 2, seed + 3)
    # the buttons pulled in, the leather gathered into each in small folds
    gather = np.zeros(u.shape)
    for (uc, vc, _, _) in B:
        du_, dv_ = u - uc, v - vc
        rr_ = np.hypot(du_, dv_)
        m_ = rr_ < 0.05
        if not m_.any():
            continue
        h[m_] -= 0.010 * np.exp(-(rr_[m_] / 0.011) ** 2)
        ang_ = np.arctan2(dv_[m_], du_[m_])
        ph = rj.uniform(0, 2 * np.pi)
        gather[m_] += np.cos(7 * ang_ + ph) * np.exp(-(rr_[m_] / 0.022) ** 2) * (rr_[m_] / 0.012).clip(0, 1)
    h += 0.0022 * gather
    h = h - crease * cm * 0.35
    # the leather tucks in at the seat
    h *= np.clip(v / 0.035, 0, 1) ** 0.6
    # soft wrinkles across the pillows
    W2 = fbm(u.shape, (u.shape[0] / 30 + 2, u.shape[1] / 30 + 2), 3, seed)
    h += 0.0014 * W2
    wear = np.clip((h - 0.010) / (A - 0.010), 0, 1)
    return h, [(b_[0], b_[1], int(b_[2])) for b_ in B], cm, wear


def back_cushion():
    nu, nv = 640, 130
    u = np.linspace(-1.35, 0.52, nu)[None, :].repeat(nv, 0)
    v = np.linspace(0.0, VH, nv)[:, None].repeat(nu, 1)
    h, B, cm, wear = tufted(u, v, ROWS_V, -0.0, VH, seed=1)
    base = np.stack([u, Y0 + v * math.sin(RECLINE), SEAT_Z + v * math.cos(RECLINE)], -1)
    n = np.array([0.0, -math.cos(RECLINE), math.sin(RECLINE)])
    P = base + n[None, None] * h[..., None]
    ob = grid_mesh("back face", P, {"wear": wear, "crease": cm})
    fix_normals(ob, (0, 0, 0))
    btn = [(uc, Y0 + vc * math.sin(RECLINE), SEAT_Z + vc * math.cos(RECLINE)) for uc, vc, _ in B
           if -1.35 < uc < 0.52 and 0 < vc < VH]
    return ob, btn, n


def back_roll():
    # a fat roll along the top, its front bulging over the tufted face, softly pleated where the top
    # row's pleats run up into it, sagging a little between them
    R = 0.092
    yc, zc = Y0 + VH * math.sin(RECLINE) + 0.032, SEAT_Z + VH * math.cos(RECLINE) + 0.025
    nu, nt = 640, 120
    u = np.linspace(-1.35, 0.52, nu)[None, :].repeat(nt, 0)
    th = np.radians(np.linspace(-75, 200, nt))[:, None].repeat(nu, 1)
    top_buttons = [(-0.0 + (DX / 2 if (len(ROWS_V) - 1) % 2 else 0)) + k * DX for k in range(-20, 20)]
    pleat = np.zeros_like(u)
    for ub in top_buttons:
        pleat = np.maximum(pleat, np.exp(-((u - ub) / 0.016) ** 2))
    front = np.clip(np.cos(th - np.radians(-10)), 0, 1) ** 2          # the pleats show on the lower front
    rr = R * (1 - 0.17 * pleat * front) * (1 + 0.016 * fbm(u.shape, (6, 90), 4, 4))
    sag = 0.004 * np.cos(2 * np.pi * (u - top_buttons[0]) / DX)       # between the pleats the roll puffs
    rr = rr + sag * np.sin(np.clip(th, 0, np.pi))
    Y = yc - rr * np.cos(th)
    Z = zc + rr * np.sin(th)
    P = np.stack([u, Y, Z], -1)
    wear = np.clip(np.sin(th) * 0.8 + 0.2, 0, 1) * (1 - 0.6 * pleat * front)    # the crest is worn
    ob = grid_mesh("back roll", P, {"wear": wear, "crease": 0.7 * pleat * front})
    fix_normals(ob, (0, 0, 0))
    return ob


def arm():
    # inner face: tufted like the back, facing the seat (-X), flaring out a little towards the top
    flare = math.radians(6)
    VA = 0.30
    nw, nv = 420, 110
    w = np.linspace(ARM_Y0, ARM_Y1, nw)[None, :].repeat(nv, 0)
    v = np.linspace(0.0, VA, nv)[:, None].repeat(nw, 1)
    h, B, cm, wear = tufted(w, v, ROWS_V[:2] + [0.27], ARM_Y1 - 0.035, VA, A=0.030, seed=7)
    base = np.stack([ARM_X + v * math.sin(flare), w, SEAT_Z + v * math.cos(flare)], -1)
    n = np.array([-math.cos(flare), 0.0, math.sin(flare)])
    P = base + n[None, None] * h[..., None]
    face = grid_mesh("arm face", P, {"wear": wear, "crease": cm})
    fix_normals(face, (0, 0, 0))
    btn = [(ARM_X + vc * math.sin(flare), wc, SEAT_Z + vc * math.cos(flare)) for wc, vc, _ in B
           if ARM_Y0 < wc < ARM_Y1]
    # the scroll: a roll along the arm, curling outward over its outer side
    R = 0.098
    xc, zc = ARM_X + VA * math.sin(flare) + 0.072, SEAT_Z + VA * math.cos(flare) + 0.03
    nt = 120
    w2 = np.linspace(ARM_Y0, ARM_Y1 + 0.03, nw)[None, :].repeat(nt, 0)
    th = np.radians(np.linspace(-80, 215, nt))[:, None].repeat(nw, 1)
    pleat = np.zeros_like(w2)
    for (wc, vc, k) in B:
        if k == 2:
            pleat = np.maximum(pleat, np.exp(-((w2 - wc) / 0.012) ** 2))
    front = np.clip(np.cos(th - np.radians(-10)), 0, 1) ** 2
    rr = R * (1 - 0.17 * pleat * front) * (1 + 0.016 * fbm(w2.shape, (6, 60), 4, 9))
    X = xc - rr * np.cos(th)
    Z = zc + rr * np.sin(th)
    P = np.stack([X, w2, Z], -1)
    wear2 = np.clip(np.sin(th) * 0.9 + 0.1, 0, 1) * (1 - 0.6 * pleat * front)
    # the arm's front, nearest the camera, is the most handled: worn more
    wear2 = np.clip(wear2 * (1.0 + 0.6 * np.clip((0.9 - w2) / 0.5, 0, 1)), 0, 1)
    roll = grid_mesh("arm roll", P, {"wear": wear2, "crease": 0.7 * pleat * front})
    fix_normals(roll, (0, 0, 0))
    return face, roll, btn, n


def buttons(points, normal, mat, name):
    obs = []
    for i, p in enumerate(points):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.0105, location=p)
        b = bpy.context.active_object
        b.name = f"{name} {i}"
        b.scale = (1.0, 1.0, 0.55)
        # flatten along the face's normal
        b.rotation_euler = Vector(normal).to_track_quat("Z", "Y").to_euler()
        b.location = Vector(p) + Vector(normal) * -0.0075
        b.data.materials.append(mat)
        for pl in b.data.polygons:
            pl.use_smooth = True
        obs.append(b)
    return obs


# ---------------------------------------------------------------- materials
def leather_material():
    """Distressed rustic red leather: an oxblood dye rubbed through in blotches to the paler crust on
    every high point (the pillows, the rolls' crests), darker and waxier in the folds; pebbled grain,
    a fine crackle where it is worn, soft creasing."""
    m = bpy.data.materials.new("leather")
    m.use_nodes = True
    nt = m.node_tree
    N = nt.nodes
    L = nt.links
    for n_ in list(N):
        if n_.type != "OUTPUT_MATERIAL":
            N.remove(n_)
    out = [n_ for n_ in N if n_.type == "OUTPUT_MATERIAL"][0]
    bs = N.new("ShaderNodeBsdfPrincipled")
    tc = N.new("ShaderNodeTexCoord")
    wear = N.new("ShaderNodeAttribute"); wear.attribute_name = "wear"
    crease = N.new("ShaderNodeAttribute"); crease.attribute_name = "crease"

    def vec(scale_xyz):
        mp_ = N.new("ShaderNodeMapping")
        mp_.inputs["Scale"].default_value = scale_xyz
        L.new(tc.outputs["Object"], mp_.inputs["Vector"])
        return mp_.outputs["Vector"]

    def noise(scale, detail=6.0, rough=0.55, dist=0.0, v=None):
        t = N.new("ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = scale
        t.inputs["Detail"].default_value = detail
        t.inputs["Roughness"].default_value = rough
        t.inputs["Distortion"].default_value = dist
        L.new(v if v is not None else tc.outputs["Object"], t.inputs["Vector"])
        return t.outputs["Fac"]

    def math_(op, a_, b_=None, clamp=False):
        n_ = N.new("ShaderNodeMath")
        n_.operation = op
        n_.use_clamp = clamp
        for i, x in enumerate((a_, b_)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n_.inputs[i].default_value = x
            else:
                L.new(x, n_.inputs[i])
        return n_.outputs[0]

    def ramp(x, lo, hi):
        mr = N.new("ShaderNodeMapRange")
        mr.clamp = True
        mr.inputs["From Min"].default_value = lo
        mr.inputs["From Max"].default_value = hi
        L.new(x, mr.inputs["Value"])
        return mr.outputs["Result"]

    def mixc(fac, c1, c2):
        n_ = N.new("ShaderNodeMix")
        n_.data_type = "RGBA"
        for sock, x in ((0, fac), (6, c1), (7, c2)):
            if isinstance(x, (tuple, list)):
                n_.inputs[sock].default_value = (*x, 1) if len(x) == 3 else x
            elif isinstance(x, (int, float)):
                n_.inputs[sock].default_value = x
            else:
                L.new(x, n_.inputs[sock])
        return n_.outputs[2]

    W_ = wear.outputs["Fac"]
    C_ = crease.outputs["Fac"]
    blot = noise(7.0, 10, 0.62, 0.6)                  # where the dye is gone: blotches
    blot2 = noise(23.0, 8, 0.6, 1.2)
    rub = math_("MULTIPLY", ramp(math_("ADD", math_("MULTIPLY", W_, 0.55), math_("MULTIPLY", blot, 0.6)), 0.55, 0.85),
                ramp(blot2, 0.35, 0.65))
    rub = math_("MAXIMUM", rub, ramp(math_("MULTIPLY", W_, math_("ADD", blot, 0.2)), 0.72, 0.95))
    dye = mixc(noise(3.0, 4, 0.5), (0.095, 0.018, 0.010), (0.16, 0.032, 0.016))
    crust = mixc(noise(40.0, 6, 0.5), (0.27, 0.075, 0.035), (0.38, 0.13, 0.06))
    col = mixc(rub, dye, crust)
    col = mixc(math_("MULTIPLY", C_, 0.85), col, (0.028, 0.006, 0.004))
    # the crackle on worn leather
    vor = N.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 220.0
    vor.inputs["Randomness"].default_value = 1.0
    L.new(tc.outputs["Object"], vor.inputs["Vector"])
    crk = math_("MULTIPLY", ramp(vor.outputs["Distance"], 0.045, 0.012), math_("ADD", math_("MULTIPLY", rub, 0.8), 0.15))
    col = mixc(math_("MULTIPLY", crk, 0.75), col, (0.035, 0.008, 0.006))
    L.new(col, bs.inputs["Base Color"])
    # wax in the dye, dry where it is rubbed through
    rough = math_("ADD", math_("MULTIPLY", rub, 0.24), 0.36)
    rough = math_("ADD", rough, math_("MULTIPLY", noise(90.0, 3, 0.5), 0.08))
    rough = math_("SUBTRACT", rough, math_("MULTIPLY", C_, 0.08))
    L.new(rough, bs.inputs["Roughness"])
    bs.inputs["Specular IOR Level"].default_value = 0.42
    bs.inputs["Coat Weight"].default_value = 0.0
    # relief: pebble grain, the crackle, long soft creases
    grain = N.new("ShaderNodeTexVoronoi")
    grain.feature = "SMOOTH_F1"
    grain.inputs["Scale"].default_value = 700.0
    L.new(tc.outputs["Object"], grain.inputs["Vector"])
    b1 = N.new("ShaderNodeBump")
    b1.inputs["Strength"].default_value = 0.22
    b1.inputs["Distance"].default_value = 0.0003
    L.new(grain.outputs["Distance"], b1.inputs["Height"])
    b2 = N.new("ShaderNodeBump")
    b2.inputs["Strength"].default_value = 0.5
    b2.inputs["Distance"].default_value = 0.0005
    L.new(math_("SUBTRACT", 1.0, crk), b2.inputs["Height"])
    L.new(b1.outputs["Normal"], b2.inputs["Normal"])
    wr1 = noise(18.0, 6, 0.6, 0.0, vec((1.0, 1.0, 6.0)))
    wr2 = noise(18.0, 6, 0.6, 0.0, vec((6.0, 1.0, 1.0)))
    wrk = math_("ADD", ramp(wr1, 0.45, 0.55), ramp(wr2, 0.47, 0.53))
    b3 = N.new("ShaderNodeBump")
    b3.inputs["Strength"].default_value = 0.35
    b3.inputs["Distance"].default_value = 0.0007
    L.new(wrk, b3.inputs["Height"])
    L.new(b2.outputs["Normal"], b3.inputs["Normal"])
    L.new(b3.outputs["Normal"], bs.inputs["Normal"])
    L.new(bs.outputs[0], out.inputs["Surface"])
    return m


def wall_material():
    m = bpy.data.materials.new("wall")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    for n_ in list(N):
        if n_.type != "OUTPUT_MATERIAL":
            N.remove(n_)
    out = [n_ for n_ in N if n_.type == "OUTPUT_MATERIAL"][0]
    bs = N.new("ShaderNodeBsdfPrincipled")
    tc = N.new("ShaderNodeTexCoord")
    # brick in the wall's own coordinates (object space: x along, z up)
    mp = N.new("ShaderNodeMapping")
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    mp.inputs["Rotation"].default_value = (math.radians(90), 0, 0)   # object xz -> texture xy
    br = N.new("ShaderNodeTexBrick")
    br.offset = 0.5
    br.squash = 1.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.006
    br.inputs["Mortar Smooth"].default_value = 0.65
    br.inputs["Brick Width"].default_value = 0.150
    br.inputs["Row Height"].default_value = 0.053
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = (1, 1, 1, 1)
    br.inputs["Color2"].default_value = (0.8, 0.8, 0.8, 1)
    br.inputs["Mortar"].default_value = (0, 0, 0, 1)
    wob = N.new("ShaderNodeTexNoise")
    wob.inputs["Scale"].default_value = 6.0
    wob.inputs["Detail"].default_value = 3.0
    L.new(tc.outputs["Object"], wob.inputs["Vector"])
    wsub = N.new("ShaderNodeVectorMath"); wsub.operation = "SUBTRACT"
    L.new(wob.outputs["Color"], wsub.inputs[0]); wsub.inputs[1].default_value = (0.5, 0.5, 0.5)
    wsc = N.new("ShaderNodeVectorMath"); wsc.operation = "SCALE"
    L.new(wsub.outputs[0], wsc.inputs[0]); wsc.inputs["Scale"].default_value = 0.009
    wadd = N.new("ShaderNodeVectorMath"); wadd.operation = "ADD"
    L.new(mp.outputs["Vector"], wadd.inputs[0]); L.new(wsc.outputs[0], wadd.inputs[1])
    L.new(wadd.outputs[0], br.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 45.0
    nz.inputs["Detail"].default_value = 10.0
    nz.inputs["Roughness"].default_value = 0.65
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    nz2 = N.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 3.0
    nz2.inputs["Detail"].default_value = 4.0
    L.new(tc.outputs["Object"], nz2.inputs["Vector"])
    # the art, mapped over the wall plane's UV (the plane spans the art's extents)
    img = N.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(D + "art_rgba.png")
    img.image.colorspace_settings.name = "Linear Rec.709"
    img.image.alpha_mode = "STRAIGHT"
    img.interpolation = "Cubic"
    uvn = N.new("ShaderNodeUVMap")
    L.new(uvn.outputs["UV"], img.inputs["Vector"])

    def math_(op, a_, b_=None, clamp=False):
        n_ = N.new("ShaderNodeMath")
        n_.operation = op
        n_.use_clamp = clamp
        for i, x in enumerate((a_, b_)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n_.inputs[i].default_value = x
            else:
                L.new(x, n_.inputs[i])
        return n_.outputs[0]

    mortar = math_("SUBTRACT", 1.0, br.outputs["Fac"])           # 1 in the joints
    # paint coverage: thinner in the joints and where the brush skipped the brick's pits
    cov = math_("MULTIPLY", img.outputs["Alpha"],
                math_("MULTIPLY", math_("SUBTRACT", 1.0, math_("MULTIPLY", mortar, 0.55)),
                      math_("ADD", math_("MULTIPLY", nz.outputs["Fac"], 0.6), 0.72), clamp=True), clamp=True)
    # the black: a satin black paint, a little grey where it is thin, the joints deeper
    blk = N.new("ShaderNodeMix"); blk.data_type = "RGBA"
    L.new(nz2.outputs["Fac"], blk.inputs[0])
    blk.inputs[6].default_value = (0.008, 0.008, 0.009, 1)
    blk.inputs[7].default_value = (0.020, 0.019, 0.020, 1)
    jm = N.new("ShaderNodeMix"); jm.data_type = "RGBA"
    L.new(mortar, jm.inputs[0])
    L.new(blk.outputs[2], jm.inputs[6])
    jm.inputs[7].default_value = (0.0045, 0.0045, 0.0048, 1)
    cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"
    L.new(cov, cm.inputs[0])
    L.new(jm.outputs[2], cm.inputs[6])
    L.new(img.outputs["Color"], cm.inputs[7])
    L.new(cm.outputs[2], bs.inputs["Base Color"])
    rough = math_("ADD", math_("MULTIPLY", mortar, 0.05), math_("ADD", math_("MULTIPLY", cov, -0.06), 0.62))
    L.new(rough, bs.inputs["Roughness"])
    bs.inputs["Specular IOR Level"].default_value = 0.45
    # relief: the joints recessed, the bricks' faces pitted, the paint a hair proud
    hgt = math_("ADD", math_("MULTIPLY", br.outputs["Fac"], 1.0), math_("MULTIPLY", nz.outputs["Fac"], 0.35))
    hgt = math_("ADD", hgt, math_("MULTIPLY", cov, 0.08))
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.22
    bump.inputs["Distance"].default_value = 0.0025
    L.new(hgt, bump.inputs["Height"])
    L.new(bump.outputs["Normal"], bs.inputs["Normal"])
    L.new(bs.outputs[0], out.inputs["Surface"])
    return m


def wall(mat):
    X0, X1, Z0, Z1 = -1.5, 2.0, -0.9, 1.2
    me = bpy.data.meshes.new("wall")
    V = [(X0, WALL, Z0), (X1, WALL, Z0), (X1, WALL, Z1), (X0, WALL, Z1)]
    me.from_pydata(V, [], [(0, 3, 2, 1)])
    me.update()
    uv = me.uv_layers.new(name="UVMap")
    uvs = {0: (0, 0), 1: (1, 0), 2: (1, 1), 3: (0, 1)}
    for li, lp in enumerate(me.loops):
        uv.data[li].uv = uvs[lp.vertex_index]
    ob = bpy.data.objects.new("wall", me)
    sc.collection.objects.link(ob)
    ob.data.materials.append(mat)
    # subdivide finely enough for the bump's coordinates to be stable (object coords are exact anyway)
    return ob


WALL = LC.WALL_Y
leather = leather_material()
btn_mat = leather
back, bbtn, bn = back_cushion()
back.data.materials.append(leather)
roll = back_roll()
roll.data.materials.append(leather)
af, ar, abtn, an = arm()
af.data.materials.append(leather)
ar.data.materials.append(leather)
buttons(bbtn, bn, btn_mat, "button")
buttons(abtn, an, btn_mat, "arm button")
wall(wall_material())

# the floor, unseen, for the light it bounces
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 1.5, LC.FLOOR))
fl = bpy.context.active_object
fm = bpy.data.materials.new("floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.02, 0.03, 1)
fl.data.materials.append(fm)

# M4 as a shadow-casting card at his depth
if not a.no_man:
    import cv2
    alpha = np.load(D + "man_alpha.npy")
    Hm, Wm = alpha.shape
    am = cv2.resize(alpha, (Wm // 2, Hm // 2), interpolation=cv2.INTER_AREA)
    rgba = np.dstack([np.ones_like(am)] * 3 + [am])[::-1].astype(np.float32)
    im = bpy.data.images.new("man_alpha", am.shape[1], am.shape[0], alpha=True, float_buffer=True)
    im.pixels.foreach_set(rgba.ravel())
    Yc = 0.92
    xw, hw = Wm * LC.S_M, Hm * LC.S_M
    corners = [(0, hw), (xw, hw), (xw, 0), (0, 0)]
    V = [((x - LC.CX) * Yc / LC.F_PX, Yc, -(y - LC.CY) * Yc / LC.F_PX) for x, y in corners]
    me = bpy.data.meshes.new("man card")
    me.from_pydata(V, [], [(0, 1, 2, 3)])
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for li, lp in enumerate(me.loops):
        uvl.data[li].uv = {0: (0, 0), 1: (1, 0), 2: (1, 1), 3: (0, 1)}[lp.vertex_index]
    card = bpy.data.objects.new("man card", me)
    sc.collection.objects.link(card)
    cm_ = bpy.data.materials.new("card")
    cm_.use_nodes = True
    nt = cm_.node_tree
    for n_ in list(nt.nodes):
        if n_.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n_)
    o_ = [n_ for n_ in nt.nodes if n_.type == "OUTPUT_MATERIAL"][0]
    it = nt.nodes.new("ShaderNodeTexImage")
    it.image = im
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    df.inputs["Color"].default_value = (0.05, 0.05, 0.05, 1)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(it.outputs["Alpha"], mx.inputs["Fac"])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(df.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], o_.inputs["Surface"])
    card.data.materials.append(cm_)
    card.visible_camera = False
    card.visible_glossy = False
    card.visible_diffuse = True
    card.visible_transmission = False
    card.visible_volume_scatter = False
    card.visible_shadow = True

if a.border:
    x0, y0, x1, y1 = [float(v) for v in a.border.split(",")]
    sc.render.use_border = True
    sc.render.use_crop_to_border = True
    sc.render.border_min_x, sc.render.border_max_x = x0 / LC.W_O, x1 / LC.W_O
    sc.render.border_min_y, sc.render.border_max_y = 1 - y1 / LC.H_O, 1 - y0 / LC.H_O
sc.render.filepath = a.out
bpy.ops.render.render(write_still=True)
print("saved", a.out)
im = bpy.data.images.load(a.out, check_existing=False)
w_, h_ = im.size
px = np.empty(w_ * h_ * 4, np.float32)
im.pixels.foreach_get(px)
np.save(a.out.replace(".exr", ".npy"), px.reshape(h_, w_, 4)[::-1])
