#!/usr/bin/env python3
"""Build the web-ready mark files from Anastasiia's masters in brand/marks/.

Masters (converted from her .ai files, do not edit):
  ds-brand-mark-{black,white}.svg        the angular brand mark, with her clear space
  ds-logo-horizontal-{black,white}.svg   mark + DARKEST SHADES on one line   (her "Primary Logo")
  ds-logo-stacked-{black,white}.svg      mark + DARKEST / SHADES stacked      (her "Secondary Logo")

Outputs:
  brand/marks/web/*.svg        tight viewBox, fill="currentColor" (inline in the app; color comes from tokens)
  brand/marks/favicon/*        favicon.svg (light/dark aware), favicon.ico, apple-touch-icon.png,
                               icon-192.png, icon-512.png, icon-maskable-512.png

Run: python3 tools/marks.py
"""
import io
import pathlib
import re

import cairosvg
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
MARKS = ROOT / "brand" / "marks"
WEB = MARKS / "web"
FAV = MARKS / "favicon"

ONYX = "#050607"   # --ds-onyx-950
BONE = "#E8E4DC"   # --ds-bone-100


def tight_viewbox(svg_text, scale=8):
    """Find the inked bounding box (in viewBox units) by rendering the SVG."""
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg_text).group(1).split()]
    png = cairosvg.svg2png(bytestring=svg_text.encode(), output_width=int(vb[2] * scale))
    a = np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"))[..., 3]
    ys, xs = np.nonzero(a > 8)
    s = a.shape[1] / vb[2]
    x0, x1 = xs.min() / s + vb[0], (xs.max() + 1) / s + vb[0]
    y0, y1 = ys.min() / s + vb[1], (ys.max() + 1) / s + vb[1]
    return tuple(round(float(v), 2) for v in (x0, y0, x1 - x0, y1 - y0))


def paths_of(svg_text):
    return re.findall(r'<path[^>]*\sd="([^"]+)"', svg_text)


def web_svg(master, title):
    s = master.read_text()
    x, y, w, h = tight_viewbox(s)
    body = "\n".join(f'  <path fill="currentColor" d="{d.strip()}"/>' for d in paths_of(s))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" role="img" aria-label="{title}">\n'
            f"  <title>{title}</title>\n{body}\n</svg>\n"), (x, y, w, h)


def square_icon(mark_svg, vb, size, fg, bg, pad):
    """Mark centered on a square; pad = fraction of the side left empty on each edge."""
    x, y, w, h = vb
    side = max(w, h) / (1 - 2 * pad)
    cx, cy = x + w / 2, y + h / 2
    d = paths_of(mark_svg)
    bg_rect = f'<rect x="{cx - side / 2}" y="{cy - side / 2}" width="{side}" height="{side}" fill="{bg}"/>' if bg else ""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{cx - side / 2} {cy - side / 2} {side} {side}">'
           f'{bg_rect}' + "".join(f'<path fill="{fg}" d="{p}"/>' for p in d) + "</svg>")
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def main():
    WEB.mkdir(parents=True, exist_ok=True)
    FAV.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, title in [("ds-brand-mark", "Darkest Shades"),
                        ("ds-logo-horizontal", "Darkest Shades"),
                        ("ds-logo-stacked", "Darkest Shades")]:
        svg, vb = web_svg(MARKS / f"{name}-black.svg", title)
        (WEB / f"{name}.svg").write_text(svg)
        out[name] = vb
        print(f"web/{name}.svg viewBox {vb}")

    mark = (MARKS / "ds-brand-mark-black.svg").read_text()
    vb = out["ds-brand-mark"]
    x, y, w, h = vb
    side = max(w, h) * 1.08
    cx, cy = x + w / 2, y + h / 2
    d = "".join(f'<path d="{p}"/>' for p in paths_of(mark))
    # Browser-tab icon: follows the OS theme (onyx mark on light tabs, bone mark on dark tabs).
    (FAV / "favicon.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{cx - side / 2:.2f} {cy - side / 2:.2f} {side:.2f} {side:.2f}">'
        f'<style>path{{fill:{ONYX}}}@media (prefers-color-scheme:dark){{path{{fill:{BONE}}}}}</style>{d}</svg>\n')

    # Raster fallbacks: bone mark on an onyx square, so the .ico reads on light and dark tab bars.
    ico = [square_icon(mark, vb, s, BONE, ONYX, 0.06) for s in (16, 32, 48)]
    ico[-1].save(FAV / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico[:-1])
    square_icon(mark, vb, 180, BONE, ONYX, 0.18).convert("RGB").save(FAV / "apple-touch-icon.png")
    square_icon(mark, vb, 192, BONE, ONYX, 0.18).save(FAV / "icon-192.png")
    square_icon(mark, vb, 512, BONE, ONYX, 0.18).save(FAV / "icon-512.png")
    square_icon(mark, vb, 512, BONE, ONYX, 0.28).save(FAV / "icon-maskable-512.png")  # safe zone for Android masks
    print("favicon set written to", FAV.relative_to(ROOT))


if __name__ == "__main__":
    main()
