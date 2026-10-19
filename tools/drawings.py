#!/usr/bin/env python3
"""Turn the 2D technical drawings into clean vector line art, one SVG per view, in millimetres.

The drawings (reference/technical-drawings/drawing-NN.pdf) are A3 at 1:1 scale, so the PDF's own
vector geometry is the frame's true outline. This script keeps the black geometry, drops the green
dimension lines, title block and border, splits the page into its four views, and writes:

    content/products/drawings/{F0X}-{front,side,top,iso}.svg   viewBox in mm, stroke="currentColor"
    content/products/drawings/measurements.json                 overall size of each view, in mm

Drawing numbers differ from frame IDs for two pairs (00-decisions.md O9): drawing 02 is F03,
03 is F02, 04 is F05, 05 is F04.

    pip install pymupdf
    python3 tools/drawings.py
"""
import json
import pathlib

import numpy as np
import pymupdf

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "reference" / "technical-drawings"
OUT = ROOT / "content" / "products" / "drawings"
MM = 25.4 / 72.0                      # PDF points to millimetres

FRAME_OF_DRAWING = {"01": "F01", "02": "F03", "03": "F02", "04": "F05",
                    "05": "F04", "06": "F06", "08": "F08", "09": "F09"}


def view_of(rect):
    cx, cy = (rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2
    if cx < 580:
        return "top" if cy < 560 else "front"
    return "iso" if cy < 470 else "side"


def is_geometry(d):
    c = d.get("color")
    return d["type"] == "s" and c is not None and max(c) < 0.2


def path_d(items, ox, oy):
    out = []
    pen = None

    def p(pt):
        return f"{(pt.x - ox) * MM:.3f} {(pt.y - oy) * MM:.3f}"

    for it in items:
        kind = it[0]
        if kind == "l":
            a, b = it[1], it[2]
            if pen is None or abs(pen.x - a.x) > 1e-3 or abs(pen.y - a.y) > 1e-3:
                out.append("M" + p(a))
            out.append("L" + p(b))
            pen = b
        elif kind == "c":
            a, c1, c2, b = it[1], it[2], it[3], it[4]
            if pen is None or abs(pen.x - a.x) > 1e-3 or abs(pen.y - a.y) > 1e-3:
                out.append("M" + p(a))
            out.append("C" + " ".join(p(q) for q in (c1, c2, b)))
            pen = b
        elif kind == "re":
            r = it[1]
            out.append(f"M{p(r.tl)}L{p(r.tr)}L{p(r.br)}L{p(r.bl)}Z")
            pen = None
        elif kind == "qu":
            q = it[1]
            out.append(f"M{p(q.ul)}L{p(q.ur)}L{p(q.lr)}L{p(q.ll)}Z")
            pen = None
    return "".join(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for pdf in sorted(SRC.glob("drawing-*.pdf")):
        num = pdf.stem.split("-")[1]
        fid = FRAME_OF_DRAWING[num]
        page = pymupdf.open(pdf)[0]
        views = {}
        for d in page.get_drawings():
            if is_geometry(d):
                views.setdefault(view_of(d["rect"]), []).append(d)
        rec = {"drawing": num, "views": {}}
        for view, ds in views.items():
            x0 = min(d["rect"].x0 for d in ds); y0 = min(d["rect"].y0 for d in ds)
            x1 = max(d["rect"].x1 for d in ds); y1 = max(d["rect"].y1 for d in ds)
            pad = 1.0 / MM  # 1 mm
            ox, oy = x0 - pad, y0 - pad
            w, h = (x1 - x0 + 2 * pad) * MM, (y1 - y0 + 2 * pad) * MM
            body = "\n".join(f'    <path vector-effect="non-scaling-stroke" d="{path_d(d["items"], ox, oy)}"/>' for d in ds)
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.3f} {h:.3f}" width="{w:.2f}mm" height="{h:.2f}mm">\n'
                   f'  <title>{fid} {view} view, 1:1, from technical drawing {num}</title>\n'
                   f'  <g fill="none" stroke="currentColor" stroke-width="0.25" stroke-linecap="round" stroke-linejoin="round">\n'
                   f'{body}\n  </g>\n</svg>\n')
            (OUT / f"{fid}-{view}.svg").write_text(svg)
            rec["views"][view] = {"width_mm": round((x1 - x0) * MM, 1), "height_mm": round((y1 - y0) * MM, 1), "paths": len(ds)}
        report[fid] = rec
        print(fid, "drawing", num, {v: (r["width_mm"], r["height_mm"]) for v, r in rec["views"].items()})
    (OUT / "measurements.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
