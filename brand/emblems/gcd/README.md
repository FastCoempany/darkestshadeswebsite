# GCD (God Cloud Device)

Darkest Shades' secondary insignia: a cloud-shaped gold band with a black onyx inset. It sits on every frame (temple or end-piece) and appears on the site as a seal and in product detail views. Rules: `docs/brief/01-brand-system.md`.

## Files

| Folder | What |
|---|---|
| `svg/gcd-geometry.svg` | **Master geometry.** Two closed Bezier paths: `id="outer"` (the band's outline) and `id="aperture"` (the stone). 1632 × 589 units. Everything else is built from this. |
| `svg/gcd-onyx.svg` | Full color: metallic gold band, onyx gradient inset, sparse veins. |
| `svg/gcd-metallic-gold.svg` | Metallic gold band, empty aperture. |
| `svg/gcd-flat-gold.svg` | Flat gold `#C6A36A` band. Use under 48 px. |
| `svg/gcd-gold-black.svg` | Flat gold band, black stone. |
| `svg/gcd-black.svg`, `svg/gcd-white.svg` | One-color versions (emboss, deboss, single-color print, dark and light grounds). |
| `png/1024/`, `png/4096/` | Transparent PNG exports of each SVG. |
| `render/gcd-3d-{front,yaw35,yaw60}-{1024,4096}.png` | Physically based renders (Blender Cycles): polished gold, polished black onyx with faint veins, transparent background. `front` is orthographic; `yaw35` and `yaw60` show the emblem as it sits on a temple seen at an angle. |

## Colors
From the `darkestshades` logo kit (Oct 18 2026), settled by the founder: flat gold `#C6A36A`; metallic gradient `#634722, #B68A4D, #FFF2CD, #EAC999, #A77C46, #CDA974, #86653B, #EDCFA0, #5A442C`; onyx `#2C2C2D, #111214, #050607, #111214, #000000`.

## Provenance
- The geometry was traced from `darkestshades/logo-kit/renders/black-onyx-transparent.png`, the symmetric cloud used on the onyx renders, the placement mockup and the 14 lightbox composites, then checked by overlaying the vector on the render.
- `darkestshades/logo-kit/svg/eclipse-*.svg` is a different, lopsided cloud. Don't use it.

## 3D
`tools/blender/gcd_render.py` builds the emblem from `gcd-geometry.svg` at 12 mm long (0.6 mm gold plate, 0.07 mm polished edge radius, stone recessed 0.06 mm) and renders it. Re-run with `--views` for any angle a composite needs (`07-photography.md`, step 8):
```
pip install bpy==5.2.2
python3 tools/blender/gcd_render.py --size 4096 --samples 160 --views front,yaw35,yaw60
```

## On the frames
Length 0.98 × the temple face height, centre 0.82 × that height from the hinge, 39% down the face, parallel to the temple. Per-frame sizes: `docs/brief/06-products.md`.
