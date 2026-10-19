# Shot settings

One file per lightbox shot that goes through `tools/photo/clean_lightbox.py` (`docs/brief/07-photography.md`). They hold what the tool can't guess. Coordinates are pixels in the original after EXIF orientation.

| Key | What |
|---|---|
| `shot`, `frame`, `angle` | `IMG_3596`, `F08`, `A2` (angle codes in `07-photography.md`) |
| `region` | `[x0, y0, x1, y1]`: the part of the original to work on, frame plus its shadow and some tent |
| `lenses` | One entry per lens, far lenses too (defocused or cut by the edge): `points`, one or more `[x, y]` inside it, for SAM |
| `marks` | One entry per old mark: `poly` (corners), `kind` (`dark` engraving or print, `light` for a ring-light hotspot on acetate), `fill_whole` (rebuild the whole polygon rather than only the detected strokes), and on a temple `temple.top` / `temple.bottom` as `[a, b]` for the edge lines `y = a·x + b` |
| `lens_cleanup` | Optional: `tophat_px`, `threshold` (reflections); `dust_px`, `dust_threshold`, `dust_min` (dust) |
| `gcd` | `view` (Blender camera yaw, e.g. `yaw72`, `yaw-16`), `relief_mm`, `hinge_top` / `hinge_bottom` (the hinge line at the temple's top and bottom edge), `temple_mm` (face height there, from `06-products.md`), `axis` (unit vector along the temple, away from the hinge), `px_per_mm_along`, `length_mm` (from `06-products.md`), `soften_px` (match the focus) |
| `framing` | `box` `[x0, y0, x1, y1]` to keep the photographer's crop, or `aspect`, `fill`, `center_y` |
| `shadow_zone` | Optional: `reach`, `side`, `soft` in px, where the frame's own shadow can fall |
