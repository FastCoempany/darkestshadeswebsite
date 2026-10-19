# darkestshadeswebsite

The website for **Darkest Shades** (darkestshades.com · [@darkestshades](https://instagram.com/darkestshades)): a Shopify Hydrogen storefront for eight frames, $100 each, released in drops. **See Everything. Reveal Nothing.**

This repo holds the plan and the assets the build starts from. The app itself (`app/`) is scaffolded in phase 0 (`docs/brief/09-build-plan.md`).

## Start here
- **`CLAUDE.md`**: the rules for anyone (human or agent) building this.
- **`docs/brief/`**: the brief, `00-decisions.md` first.

| Doc | About |
|---|---|
| `00-decisions.md` | What's settled, what's open |
| `01-brand-system.md` | Marks, color, type, the SS90 patina |
| `02-raf-lens.md` | The design lens (internal) |
| `03-references.md` | The three reference videos → the entry and the home page |
| `04-ia-and-pages.md` | Sitemap, navigation, page templates |
| `05-components.md` | Base and house components, states, behavior |
| `06-products.md` | The eight frames, measurements, the GCD per frame, drops |
| `07-photography.md` | Lightbox clean-up, the cast, compositing, the DAM |
| `08-copy.md` | Voice, honesty rules, consent and safety copy |
| `09-build-plan.md` | Stack, workspace setup, phases, checks |

## What's here
- `brand/marks/`: Anastasiia's logo, stacked logo and brand mark (masters, web SVGs, favicon set).
- `brand/emblems/gcd/`: the God Cloud Device as vector masters, PNGs and 3D renders.
- `design/tokens/`: palette and base tokens, generated CSS, contrast report.
- `content/`: product data with measurements from the 1:1 drawings, vector line art of every frame, the first drop, the copy deck, the lightbox angle picks.
- `reference/`: the three reference videos and the technical drawings (study only).
- `tools/`: the Python tools that generate all of the above.

## Regenerate
```
pip install --break-system-packages cairosvg pillow numpy pymupdf bpy==5.2.2
python3 tools/palette.py && python3 tools/build_tokens.py
python3 tools/marks.py
python3 tools/drawings.py
python3 tools/blender/gcd_render.py --size 4096 --samples 160 --views front,yaw35,yaw60
```

Lightbox clean-up (old marks out, see-through lenses, the GCD in, re-staged), one shot at a time; `docs/brief/07-photography.md` has the steps:
```
pip install --break-system-packages "rembg[cpu]" opencv-contrib-python-headless scipy
python3 tools/photo/zipget.py --picks content/photography/lightbox-angle-set.json --frames F08
python3 tools/photo/clean_lightbox.py content/photography/shots/IMG_3596.json
```

A cast member wearing a real frame (the person is generated without glasses; the frame is the cleaned photograph, sized from the 1:1 drawing):
```
pip install --break-system-packages insightface onnxruntime
python3 tools/photo/wear.py content/photography/people/W1-S07-F02-A1.json
```

Fonts (Owners Wide, Stolzl) are not in this repo: see `brand/fonts/README.md`.
