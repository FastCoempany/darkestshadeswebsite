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
# mm behind the ring; tilt: pantoscopic tilt as worn; pads: the nose pads behind the bridge (top
# and side views: centre x, y, how far behind the front's back, radii); hinge: where the temple
# starts, behind the front's face and below its top (side view); endpiece: the wedge from the front's
# back to the hinge, from `top` to `bottom` mm below the front's top; temple: "wire" (round, radius)
# running `straight` mm back from the hinge, then curving `drop` mm down behind the ear.
FRAMES = {
    "F04": {"depth": 7.0, "edge_r": 3.2, "back_r": 0.9, "dome": 0.9,
            "bezel": {"width": 3.5, "step": 1.6, "drop": 1.3, "bump": 0.35}, "lip_r": 0.9,
            "lens": {"radius": 260.0, "thick": 1.6, "inset": 1.4},
            "tilt": 10.0,
            "pads": {"x": 10.8, "y": -4.0, "back": 4.5, "r": (1.6, 5.0, 3.0)},
            "hinge": {"back": 23.0, "down": 9.5}, "endpiece": {"top": 1.5, "bottom": 17.0, "inset": 4.0},
            "temple": {"kind": "wire", "radius": 1.05, "straight": 75.0, "drop": 36.0}},
}


# ---------- reading the drawings ----------
def render_view(frame, view, ppm=20):
    import cairosvg
    svg = (DRAW / f"{frame}-{view}.svg").read_text()
    svg = svg.replace("currentColor", "#000").replace('stroke-width="0.25"', 'stroke-width="0.06"')
    svg = svg.replace('vector-effect="non-scaling-stroke"', "")
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=int(vb[2] * ppm), output_height=int(vb[3] * ppm),
                           background_color="white")
    return cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_GRAYSCALE), ppm


def front_shapes(frame, ppm=20):
    """The front view's outline and lens openings as polygons in mm (origin midway between the two
    lens-box centres, x right as drawn, y up)."""
    from scipy import ndimage as ndi
    im, ppm = render_view(frame, "front", ppm)
    free = 1 - cv2.dilate((im < 200).astype(np.uint8), np.ones((3, 3), np.uint8))
    lab, n = ndi.label(free)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    sizes = ndi.sum(np.ones_like(lab), lab, range(1, n + 1))
    inner = [(sizes[i - 1], i) for i in range(1, n + 1) if i not in border]
    lenses = [i for _, i in sorted(inner, reverse=True)[:2]]
    lens_masks = sorted([lab == i for i in lenses], key=lambda m: np.nonzero(m)[1].mean())
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
    return {"outline": poly(silhouette), "openings": [poly(m, 1) for m in lens_masks],
            "opening_masks": [cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0 for m in lens_masks],
            "lenses": [poly(m, int(1.0 * ppm)) for m in lens_masks],
            "width": float(np.ptp(np.nonzero(silhouette)[1]) / ppm),
            "solid": silhouette & ~openings, "lens_masks": [cv2.dilate(m.astype(np.uint8),
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(1.2 * ppm) * 2 + 1,) * 2)) > 0 for m in lens_masks],
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
    for _ in range(4):
        newP = P.copy()
        for v in bv:
            newP[v] = 0.5 * P[v] + 0.5 * P[nb[v]].mean(0)
        P = newP
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
    me.polygons.foreach_set("use_smooth", np.ones(len(F), bool))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def rounded(d, r):
    """A quarter circle of radius r: 0 at d = 0 rising to r at d >= r (the height a rounded edge has
    gained d mm in from the edge)."""
    t = np.clip(d, 0, r)
    return np.sqrt(np.maximum(r * r - (r - t) ** 2, 0))


def rim_fields(sh, cfg):
    """The front's face and back as height fields over the front view (mm; z = 0 mid-thickness): the
    face rounded at the outer edge, stepping down to the ring round each lens and rounding into the
    lens; the back flat, its edges rounded."""
    from scipy import ndimage as ndi
    ppm = sh["ppm"]
    solid = sh["solid"]
    openings = np.zeros_like(solid)
    for m in sh["opening_masks"]:
        openings |= m
    sil = ndi.binary_fill_holes(solid | openings)
    d_out = ndi.distance_transform_edt(sil) / ppm
    d_in = ndi.distance_transform_edt(~openings) / ppm
    T = cfg["depth"]
    r = cfg["edge_r"]
    z_out = T / 2 - r + rounded(d_out, r)
    bz = cfg["bezel"]
    w, st, dr, lr = bz["width"], bz["step"], bz["drop"], cfg["lip_r"]
    # the ring: up from the lens groove round the lip, a low rounded band, then the step's shoulder up
    # to the front's face
    u = np.clip((d_in - (w - st / 2)) / st, 0, 1)
    z_in = T / 2 - dr * (1 - u * u * (3 - 2 * u))
    band = np.clip((d_in - lr) / max(w - st / 2 - lr, 1e-3), 0, 1)
    z_in = z_in + bz.get("bump", 0.0) * np.sin(np.pi * band) * (d_in < w)
    z_lip = T / 2 - dr - lr + rounded(d_in, lr)
    # the face itself domed across the rim (a pillow, not a plate): highest midway between the outer
    # edge and the ring's step
    d_step = np.maximum(d_in - (w + st / 2), 0)
    t = d_out / np.maximum(d_out + d_step, 1e-3)
    z_dome = T / 2 - cfg.get("dome", 0.0) * (1 - np.sin(np.pi * np.clip(t, 0, 1)) ** 0.5)
    zf = np.minimum(np.minimum(np.minimum(z_out, z_in), z_lip), z_dome)
    rb = cfg["back_r"]
    zb = -(T / 2 - rb) - rounded(np.minimum(d_out, d_in), rb)
    # a polished part has no creases: the distance fields kink along the middle of every band (the
    # bridge's centre, each rim's midline), which showed as lines in the gloss; smoothed out within
    # the front (a blur that takes nothing from outside it)
    def smooth(z, sig_mm):
        m = solid.astype(np.float64)
        return ndi.gaussian_filter(z * m, sig_mm * ppm) / np.maximum(ndi.gaussian_filter(m, sig_mm * ppm), 1e-6)
    return smooth(zf, 0.5), smooth(zb, 0.3)


def lens_fields(sh, cfg, i):
    """Lens i as a thin spherical shell set in the front: its front face curved to the base curve
    about the lens box's centre, its edge `inset` mm behind the ring."""
    ppm = sh["ppm"]
    m = sh["lens_masks"][i]
    ys, xs = np.nonzero(sh["opening_masks"][i])
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


def build(frame, materials, tilt=None):
    """The frame's front (with its lenses, nose pads and end pieces), as worn: wrapped, tilted. Returns
    the parts and the shapes, plus the two hinge points (mm, the parts' coordinates) where the temples
    start (temples() makes those, once the ears are known)."""
    cfg = FRAMES[frame]
    sh = front_shapes(frame)
    xm, z = wrap_profile(frame)
    T = cfg["depth"]
    zf, zb = rim_fields(sh, cfg)
    front = field_mesh(f"{frame} front", sh["solid"], zf, zb, sh["origin_px"], sh["ppm"], step=3)
    bend(front, xm, z, -T / 2)                        # the front's face at z = 0 at its most forward point
    front.data.materials.append(materials["acetate"])
    lenses = []
    for i in range(2):
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
        parts.append(ellipsoid(f"{frame} pad {side}", (x, pd["y"], zc), pd["r"], materials["acetate"],
                               rot_deg=(-12, side * 25, side * 12)))
    # end pieces: a wedge from the back of the front's ends to the hinge
    out = sh["outline"]
    top = out[:, 1].max()
    ep, hg = cfg["endpiece"], cfg["hinge"]
    hinges = []
    for side in (-1, 1):
        xe = out[:, 0].max() if side > 0 else out[:, 0].min()
        ze = float(np.interp(xe, xm, z)) - T + cfg["back_r"]
        y0, y1 = top - ep["top"], top - ep["bottom"]
        xi = xe - side * ep["inset"]
        hx, hy, hz = xe - side * 1.6, top - hg["down"], float(np.interp(xe, xm, z)) - hg["back"]
        rings = [[(xi, y0, ze), (xe - side * 0.3, y0, ze), (xe - side * 0.3, y1, ze), (xi, y1, ze)],
                 [(hx - side * 1.3, hy + 1.6, hz), (hx + side * 1.3, hy + 1.6, hz), (hx + side * 1.3, hy - 1.6, hz),
                  (hx - side * 1.3, hy - 1.6, hz)]]
        if side < 0:
            rings = [r[::-1] for r in rings]
        parts.append(loft(f"{frame} end {side}", rings, materials["acetate"]))
        hinges.append((hx, hy, hz))
    R = Matrix.Rotation(np.radians(-(cfg["tilt"] if tilt is None else tilt)), 4, "X")
    for p in parts:
        p.matrix_world = R @ p.matrix_world
    Rn = np.asarray(R.to_3x3())
    hinges = [tuple(Rn @ np.asarray(h)) for h in hinges]
    return parts, sh, hinges


def temples(frame, hinges, materials, ears=None, split=False):
    """The temples, from each hinge (mm) back to the ear and curving down behind it. `ears`: the point
    on each side where the temple rests on the ear's root, in the same coordinates; without them, the
    drawing's: straight back from the hinge. With `split`, each temple is two objects, the run from the
    hinge to the ear and the part behind the ear (named "... back"), so a front view can leave the
    second out: from the front it is always behind the ear."""
    cfg = FRAMES[frame]
    t = cfg["temple"]
    obs = []
    for k, h in enumerate(hinges):
        h = np.asarray(h, np.float64)
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
    return {"acetate": principled("acetate", (0.0015, 0.0015, 0.0017, 1), 0.035, ior=1.49),
            "metal": principled("metal", (0.005, 0.005, 0.0055, 1), 0.6),      # black-coated wire, satin
            "lens": lens}


def check(frame, out, samples=64):
    """The built frame, upright in a light tent and seen from the front and a little above as the
    product shot was taken, for a side-by-side with the product photo."""
    sys.path.insert(0, str(ROOT / "tools" / "blender"))
    import gcd_render
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    gcd_render.setup_scene(1600, samples, light="lightbox")
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
    sc.render.film_transparent = False
    mats = materials_for(frame)
    parts, sh, hinges = build(frame, mats)
    parts += temples(frame, hinges, mats)
    rig = bpy.data.objects.new("rig", None)
    sc.collection.objects.link(rig)
    for p in parts:
        p.parent = rig
    rig.rotation_euler = (np.radians(90), 0, 0)        # the frame's up (y) to the world's up (z)
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
    el = np.radians(4.0)
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
    a = ap.parse_args()
    if a.check:
        check(a.frame, pathlib.Path(a.out or f"/tmp/{a.frame}-3d-check.png"))
