# Product photography: web exports

The cleaned lightbox finals, sized for the site (`docs/brief/07-photography.md`). One final per frame and angle: `ds-<frame>-<angle>-<width>.<format>`, e.g. `ds-f01-a2-1440.avif`.

- Angles: `a1` front, `a2` three-quarter, `a3` side, `a4` from above, `a5` inside, `a6` the GCD up close (F08, which shows no GCD: the hinge), `h` the landscape hero. A1 to A6 are 4:5; the hero is 3:2.
- Widths 640, 960, 1440 and 2048 px, as far as the master reaches; never upscaled. A close-up cropped smaller than 2048 px (most A6 pictures) also comes at its own full width, the `widths` column in the manifest.
- AVIF, WebP and JPEG, sRGB, no metadata. Serve AVIF first, then WebP, with the JPEG as the fallback.
- `MANIFEST.csv`: one row per final: source shot, frame, angle, version, master size, widths, tool chain, the master's DAM name, status and the alt text (from `content/copy/en.json`, `alt`).

Made by `python3 tools/photo/export_web.py` from `work/out/` (`tools/photo/clean_lightbox.py`). The masters (16-bit cut-out with alpha, 16-bit stage version) are not in this public repo; they belong in the DAM.
