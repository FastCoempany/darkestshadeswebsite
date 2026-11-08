#!/usr/bin/env python3
"""A frame as a GLB ready to optimize (DRAWER-WALL.md, The frames in 3D, D4). Built with frame3d as the product
views are (temples open, the GCD in place at its size and placement), triangulated and decimated to the budget with
the GCD kept dense, its materials converted for glTF, exported Y-up with WebP images; then tools/web3d/optimize.mjs.

    python3 tools/blender/frame_glb.py F09 --out work/glb/F09.glb --check
    python3 tools/blender/frame_glb.py F01 --out work/glb/F01.glb --tint 0.52 0.60 0.72 --check

Materials: acetate as a glossy dielectric (roughness 0.06, IOR 1.49; a coat weight is an option, S1 matched Cycles
better without); a tortoise front (F01, F02) takes its own colour from work/frames3d/<frame>/albedo.png on the
front's planar UVs and the temple band on the temples' UVs; metal as metallic; the lenses as a tinted, alpha-blended
glossy surface whose opacity is 1 minus the measured transmission (the gradient lenses as a texture); the GCD as two
named materials, gcd_gold and gcd_onyx. --check: triangle count, file size, the GCD meshes present on the wearer's
right with their length within 2% of the product's gcd.lengthMm and centred as the build places them (within 0.5 mm),
the front width within 1 mm of measurementsMm.frontWidth.
"""
import argparse
import json
import os
import pathlib
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "blender"))
import frame3d  # noqa: E402

MM = frame3d.MM
TRIS_AIM, TRIS_MAX = 60000, 100000
BYTES_AIM, BYTES_MAX = 3 * 1024 * 1024, 6 * 1024 * 1024
GCD_SHARE = 6          # the GCD keeps about a sixth of the budget: 10k triangles for a 9 to 15 mm emblem, its curves whole


def product(frame):
    return json.loads((ROOT / "content" / "products" / f"{frame.lower()}.json").read_text())


def pbr(name, base, rough, metallic=0.0, ior=1.5, alpha=1.0, coat=0.0, image=None, uv=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    b.inputs["IOR"].default_value = ior
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat
    if image is not None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = image
        tex.interpolation = "Cubic"
        if uv:
            uvn = nt.nodes.new("ShaderNodeUVMap")
            uvn.uv_map = uv
            nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    if alpha < 1.0:
        m.surface_render_method = "BLENDED"
    return m


def gltf_materials(frame, tint, coat):
    """The glTF materials, by the name of the Cycles material each part carries."""
    tex = frame3d.texture_info(frame)
    tmean = float(np.mean(tint))
    mats = {
        "acetate": pbr("acetate", (0.0015, 0.0015, 0.0017), 0.06, ior=1.49, coat=coat),
        "lens": pbr("lens", (0.01, 0.01, 0.012), 0.0, ior=1.5, alpha=max(0.05, 1.0 - tmean)),
        "gcd gold": pbr("gcd_gold", (0.565, 0.366, 0.145), 0.22, metallic=1.0),
        "gcd onyx": pbr("gcd_onyx", (0.006, 0.006, 0.006), 0.04),
        "clear acetate": pbr("clear_acetate", (0.85, 0.85, 0.85), 0.05, ior=1.49, alpha=0.3),
        "metal": pbr("metal", (0.005, 0.005, 0.0055), 0.6),
        "endmetal": pbr("endmetal", (0.035, 0.035, 0.038), 0.07, metallic=1.0),
        "core": pbr("core", (0.42, 0.42, 0.40), 0.5, metallic=1.0),
        "knob": pbr("acetate_tip", (0.0015, 0.0015, 0.0017), 0.06, ior=1.49),
    }
    if tex:
        # the tortoise front: its own colour on the front's planar UVs (frame3d.planar_uv, "frame_uv"), linear albedo
        alb = bpy.data.images.load(str(pathlib.Path(tex["dir"]) / "albedo.png"))
        alb.colorspace_settings.name = "Linear Rec.709"
        mats["acetate"] = pbr("acetate", (1, 1, 1), 0.06, ior=1.49, coat=coat, image=alb, uv="frame_uv")
        if tex.get("temple"):
            band = bpy.data.images.load(str(pathlib.Path(tex["dir"]) / tex["temple"]["file"]))
            band.colorspace_settings.name = "Linear Rec.709"
            mats["acetate temple"] = pbr("acetate_temple", (1, 1, 1), 0.06, ior=1.49, coat=coat, image=band, uv="bar_uv")
    grad = frame3d.FRAMES.get(frame, {}).get("lens", {}).get("gradient")
    if grad:
        # a gradient lens: the opacity by height as measured, as a 1 x 64 texture on the lens's planar UVs
        ys = [g[0] for g in grad]
        lo, hi = min(ys), max(ys)
        n = 64
        img = bpy.data.images.new(f"{frame} lens gradient", 1, n, alpha=True)
        px = []
        pts = sorted(grad)
        for i in range(n):
            y = lo + (hi - lo) * i / (n - 1)
            # the transmission at y, interpolated between the measured points
            k = max(0, min(len(pts) - 2, next((j for j in range(len(pts) - 1) if pts[j + 1][0] >= y), len(pts) - 2)))
            (y0, c0), (y1, c1) = pts[k], pts[k + 1]
            f = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
            c = [c0[j] + (c1[j] - c0[j]) * f for j in range(3)]
            px += [0.01, 0.01, 0.012, max(0.05, 1.0 - float(np.mean(c)))]
        img.pixels = px
        img.pack()
        m = pbr("lens", (0.01, 0.01, 0.012), 0.0, ior=1.5, alpha=0.5)
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        tex_n = nt.nodes.new("ShaderNodeTexImage")
        tex_n.image = img
        tex_n.interpolation = "Linear"
        tex_n.extension = "EXTEND"
        uvn = nt.nodes.new("ShaderNodeUVMap")
        uvn.uv_map = "lens_uv"
        nt.links.new(uvn.outputs["UV"], tex_n.inputs["Vector"])
        nt.links.new(tex_n.outputs["Alpha"], b.inputs["Alpha"])
        mats["lens"] = m
        mats["_lens_gradient_mm"] = (lo, hi)
    return mats


def lens_uv(ob, lo, hi):
    """Planar UVs on a lens: v runs from the gradient's lowest measured height to its highest (frame3d's y, mm)."""
    me = ob.data
    uv = me.uv_layers.get("lens_uv") or me.uv_layers.new(name="lens_uv")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            v = (co.y / MM - lo) / max(1e-6, hi - lo)
            uv.data[li].uv = (0.5, min(1.0, max(0.0, v)))


def build(frame, tint, mesh_step, coat):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if mesh_step:
        frame3d.FRAMES[frame]["mesh_step"] = mesh_step
    cyc = frame3d.materials_for(frame, tint)
    parts, sh, hinges = frame3d.build(frame, cyc)
    parts += frame3d.temples(frame, hinges, cyc)
    g = gltf_materials(frame, tint, coat)
    grad = g.pop("_lens_gradient_mm", None)
    used = {}
    for p in parts:
        for i, m in enumerate(p.data.materials):
            key = m.name.split(".")[0]
            key = key.replace(f"{frame} ", "")
            gm = g.get(key)
            if gm is None:
                print(f"frame_glb: no glTF material for {m.name} on {p.name}; acetate used", flush=True)
                gm = g["acetate"]
            p.data.materials[i] = gm
            used[gm.name] = used.get(gm.name, 0) + 1
        if grad and p.name.startswith(f"{frame} lens"):
            lens_uv(p, *grad)
    return parts, sh, used


def decimate(frame, parts, target):
    tris = {}
    for p in parts:
        p.data.calc_loop_triangles()
        tris[p.name] = len(p.data.loop_triangles)
    gcd_tris = sum(v for k, v in tris.items() if "gcd" in k)
    gcd_budget = min(gcd_tris, target // GCD_SHARE)
    gcd_ratio = gcd_budget / max(1, gcd_tris)
    rest = sum(v for k, v in tris.items() if "gcd" not in k)
    ratio = min(1.0, (target - gcd_budget) / max(1, rest))
    for p in parts:
        p.modifiers.new("tri", "TRIANGULATE")
        r = gcd_ratio if "gcd" in p.name else ratio
        if r < 1.0:
            d = p.modifiers.new("dec", "DECIMATE")
            d.ratio = r
            d.use_collapse_triangulate = True
    return sum(tris.values()), ratio, gcd_ratio


def export(parts, out):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(out), export_format="GLB", use_selection=True, export_apply=True, export_yup=True,
                              export_materials="EXPORT", export_image_format="WEBP", export_normals=True, export_texcoords=True,
                              export_cameras=False, export_lights=False, export_animations=False)
    return out


def measure(frame, parts, sh):
    """What --check measures on the evaluated (decimated) meshes: the exported triangle count, the front's width, the
    GCD's length, its centre and which side it sits on."""
    dg = bpy.context.evaluated_depsgraph_get()
    total = 0
    gcd = []
    front = None
    for p in parts:
        me = p.evaluated_get(dg).data
        me.calc_loop_triangles()
        total += len(me.loop_triangles)
        co = np.zeros(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3) / MM
        if "gcd gold" in p.name:
            gcd.append(co)
        if p.name == f"{frame} front":
            front = co
    g = np.concatenate(gcd) if gcd else None
    # the band's length along its own longest axis: on a temple it lies nearly along z, on F02's wrapped wing
    # 18 degrees from x (an axis-aligned extent read 8.8 mm as 8.5 there)
    length = None
    if g is not None:
        axis = np.linalg.svd(g - g.mean(0), full_matrices=False)[2][0]
        length = float(np.ptp((g - g.mean(0)) @ axis))
    return {"triangles": total,
            "frontWidthMm": float(np.ptp(front[:, 0])) if front is not None else None,
            "gcdMeshes": len(gcd),
            "gcdLengthMm": length,
            "gcdCentreMm": [float(v) for v in ((g.min(0) + g.max(0)) / 2)] if g is not None else None,
            "gcdOnWearersRight": bool(g is not None and ((g.min(0) + g.max(0)) / 2)[0] < 0)}


def check(frame, out, m, built_tris, expected_centre=None):
    """The checks of DRAWER-WALL.md. Returns the failures."""
    fails = []
    pf = product(frame)
    size = os.path.getsize(out)
    if m["triangles"] > TRIS_MAX:
        fails.append(f"{m['triangles']} triangles, over {TRIS_MAX}")
    if size > BYTES_MAX:
        fails.append(f"{size} bytes, over {BYTES_MAX}")
    if m["gcdMeshes"] < 1:
        fails.append("no GCD mesh")
    else:
        want = float(pf["gcd"]["lengthMm"])
        if abs(m["gcdLengthMm"] - want) > 0.02 * want:
            fails.append(f"GCD {m['gcdLengthMm']:.2f} mm, not within 2% of {want}")
        if not m["gcdOnWearersRight"]:
            fails.append("the GCD is not on the wearer's right")
        if expected_centre is not None:
            d = float(np.linalg.norm(np.array(m["gcdCentreMm"]) - np.array(expected_centre)))
            if d > 0.5:
                fails.append(f"the GCD's centre moved {d:.2f} mm in the export")
    fw = pf["measurementsMm"].get("frontWidth")
    if fw and m["frontWidthMm"] is not None and abs(m["frontWidthMm"] - fw) > 1.0:
        fails.append(f"front width {m['frontWidthMm']:.2f} mm, not within 1 mm of {fw}")
    return fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("frame")
    ap.add_argument("--out", default=None)
    ap.add_argument("--tint", type=float, nargs=3, default=None, help="the lens's transmission, linear r g b (wall/assets/lens-tints.json by default)")
    ap.add_argument("--mesh-step", type=int, default=4, help="frame3d's front grid for the GLB build (D0, S1: 4)")
    ap.add_argument("--target", type=int, default=TRIS_AIM)
    ap.add_argument("--coat", type=float, default=0.0)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", default=None, help="write the measurements as JSON here")
    a = ap.parse_args()
    frame = a.frame.upper()
    tint = tuple(a.tint) if a.tint else None
    if tint is None:
        tints_path = ROOT / "wall" / "assets" / "lens-tints.json"
        if tints_path.exists():
            t = json.loads(tints_path.read_text()).get("frames", {}).get(frame)
            tint = tuple(t["transmission"]) if t and "transmission" in t else None
    if tint is None:
        tint = (0.06, 0.06, 0.065)
        print(f"frame_glb: no measured tint for {frame}; a dark grey placeholder used", flush=True)
    t0 = time.time()
    parts, sh, used = build(frame, tint, a.mesh_step, a.coat)
    # the GCD's centre as built, before decimation (the check compares the export with it)
    pre = measure(frame, parts, sh)
    built, ratio, gcd_ratio = decimate(frame, parts, a.target)
    out = export(parts, a.out or ROOT / "work" / "glb" / f"{frame}.glb")
    m = measure(frame, parts, sh)
    m.update({"frame": frame, "bytes": os.path.getsize(out), "builtTriangles": built, "decimateRatio": round(ratio, 5), "gcdRatio": round(gcd_ratio, 4),
              "materials": used, "tint": list(tint), "meshStep": a.mesh_step, "seconds": round(time.time() - t0, 1)})
    fails = check(frame, out, m, built, pre["gcdCentreMm"]) if a.check else None
    if a.check:
        m["check"] = "0 failures" if not fails else "; ".join(fails)     # the report carries the check's result (optimize.mjs --manifest records it)
    print(json.dumps(m), flush=True)
    if a.report:
        pathlib.Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(a.report).write_text(json.dumps(m, indent=1))
    if a.check:
        for f in fails:
            print(f"check {frame}: {f}", flush=True)
        print(f"check {frame}: {len(fails)} failures", flush=True)
        raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
