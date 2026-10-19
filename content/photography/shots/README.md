# Shot settings

One file per lightbox shot that goes through `tools/photo/clean_lightbox.py` (`docs/brief/07-photography.md`). They hold what the tool can't guess. Coordinates are pixels in the original after EXIF orientation.

| Key | What |
|---|---|
| `shot`, `frame`, `angle` | `IMG_3596`, `F08`, `A2` (angle codes in `07-photography.md`) |
| `region` | `[x0, y0, x1, y1]`: the part of the original to work on, frame plus its shadow and some tent |
| `lenses` | One entry per lens, far lenses too (defocused or cut by the edge): `points`, one or more `[x, y]` inside it, for SAM. `convex: true` for a lens with no concave edge (round, square, octagon; never F06's shield): the mask becomes its convex hull, so a reflection or a temple seen through the lens can't bite into it |
| `marks` | One entry per old mark: `poly` (corners), `kind` (`dark` engraving or print, `light` for a ring-light hotspot or a light print), `fill_whole` (rebuild the whole polygon rather than only the detected strokes), and on a temple `temple.top` / `temple.bottom` as `[a, b]` for the edge lines `y = a·x + b` (the polygon stays between them) |
| `lens_cleanup` | Optional: `tophat_px`, `threshold` (reflections); `dust_px`, `dust_threshold`, `dust_min` (dust); `paint`, polygons of reflections too big to detect, refilled as clean lens; `smooth`, `flat` (one tint per lens) or `gradient` (gradient lenses), which also drops whatever is seen through the lens |
| `gcd` | `view` (Blender camera yaw of the face it sits on, e.g. `yaw72`, `yaw-16`; positive when the face recedes to the right), `relief_mm`, `length_mm` (from `06-products.md`), `soften_px` (match the focus), and one of three placements. On a temple: `hinge_top` / `hinge_bottom` (the hinge line at the temple's top and bottom edge), `temple_mm` (face height there), `axis` (unit vector along the temple, away from the hinge), `px_per_mm_along`. Measured directly (F02's wing): `center`, `axis`, `down`, `px_per_mm_along`, `px_per_mm_down`. In perspective: `anchors_px` with `center`, `left`, `right`, `top`, `bottom` |
| `framing` | `box` `[x0, y0, x1, y1]` to keep the photographer's crop (a frame running off the picture keeps its shadow to the edge), or `aspect`, `fill`, `center_y` |
| `shadow_zone` | Optional, where the frame's own shadow can fall: `reach`, `side`, `soft` in px (below the frame in the picture); `around` in px for a view from straight above, where the shadow lies all round the frame |

## Placing F02's GCD

F02's GCD replaces the two pin heads on the right wing. The approved front shot (IMG_3423) fixes it: centered between the pins, 8.8 mm long, the pins 2.64 mm apart and 1.68 mm across. On any other angle, measure the pins: their midpoint is the center, the line through them the axis, their spacing gives `px_per_mm_along` and their height `px_per_mm_down`, and the ratio of the two gives the yaw (`cos yaw = along / down`). Where the wing is too blurred to show the pins, they sit about 39% and 61% across the wing's flat face and 53% down.
