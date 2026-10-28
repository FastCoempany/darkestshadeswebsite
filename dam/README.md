# DAM: Darkest Shades photography

This folder is the home of the brand's photography masters: the full-resolution files every web image is made from. It lives in this repo, on `main` (founder, Oct 21 2026, `docs/brief/00-decisions.md` #39). The repo is public, so everything here is public too.

## What's here

| Folder | What | Files |
|---|---|---|
| `product/` | The 56 cleaned lightbox finals: eight frames, angles A1–A6 and the hero (H) | `DS-F01-A1-v01-stage.png`: 16-bit RGB on the stage color `#E4E2DD`, with the frame's own shadow. Every web file in `assets/photography/` is made from it.<br>`DS-F01-A1-v01-master.png`: 16-bit RGBA cut-out, the lenses' tint folded into the alpha (exact over the stage color, close over anything light), for compositing. |
| `people/` | On-model finals: the generated cast wearing the real frames (`docs/brief/07-photography.md`, track 2), added as they are made. Nine since Oct 28 2026, approved by the founder: every frame at least once (F03 twice). | `DS-CAST-W1-S07-F02-v01-master.png`: the picture, 16-bit RGB (cast slot, scene, frame, angle when not A1, version). Every web file in `assets/photography/` is made from it.<br>`DS-CAST-W1-S07-F02-v01-cutout.png`: the same picture cut out, 16-bit RGBA, for setting the person in any scene (`00-decisions.md` #40). |

Angle codes: **A1** front · **A2** three-quarter · **A3** side · **A4** top-down · **A5** inside (from behind) · **A6** GCD detail · **H** landscape hero.

## Where everything else lives

- **Originals**, untouched: the `darkestshades` repo's release `DARKESTSHADES.zip` → `Lighbox shots/`, and the founder's Google Drive folder of the same name. `tools/photo/zipget.py` pulls single shots from the release by byte range.
- **Web exports**: `assets/photography/`, `ds-f01-a1-1440.avif` / `.webp` / `.jpg` at 640, 960, 1440 and 2048 px.
- **Register**: `assets/photography/MANIFEST.csv`, one row per final: id, source shot, frame, angle, version, tool chain, master file and location, status, alt text, crop.
- **What made each master**: the settings in `content/photography/shots/<shot>.json` (product) and `content/photography/people/<id>.json` (people), run by the tools below.

## Making and updating masters

```
python3 tools/photo/clean_lightbox.py content/photography/shots/IMG_3554.json   # one shot -> work/out/IMG_3554/ (not committed)
python3 tools/photo/export_web.py                                              # web files + MANIFEST.csv + masters here
```

- Masters are lossless PNG, 16 bits per channel, sRGB.
- `export_web.py` rewrites a master only when its source in `work/out/` is newer, so an export that changes nothing leaves this folder untouched.
- Versions (`v01`, `v02`, ...; `VERSION` in `export_web.py`): a new version is written under its new name; delete the old file in the same commit, and it stays in git history (`git log -- dam/product/`).
- The product set is about 0.8 GB (112 files, the largest about 20 MB). They are ordinary git files, not Git LFS.
