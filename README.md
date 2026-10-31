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

### Run the app

Node 22 and Python 3 (the tools). Then:

```bash
npm install
npm run dev            # http://localhost:3000 (MiniOxygen); ?mode=wire for the wireframes; /dev/tokens for the token sheet
npm run storybook      # http://localhost:6006: every component and page state, UI and wire mode, 390 and 1440 in the toolbar
```

Before a pull request:

```bash
npm run checks         # banned strings, hex colors in app/, the product schema, the copy gate, the layer rule, the flash check
npm run typecheck && npm run lint && npm test
npm run test:e2e       # Playwright: fonts, screenshots at 390 and 1440 against the committed baselines, axe, the Storybook matrix
npm run preview:review -- --port 3000   # then, in another shell: npm run lighthouse
```

`npm run build` refuses while any section of `content/copy/en.json` is `draft` or `placeholder` (every section today): that is the copy gate, not a broken build. `npm run build:review` is the same build with drafts allowed; Lighthouse and the review screenshots run on it. The review sets are in `docs/wireframes/` (wire mode) and `docs/ui/` (UI mode); `docs/build/PROGRESS.md` is where the build stands, with the questions for the founder and the copy awaiting sign-off.

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
python3 tools/photo/temple_gcd.py IMG_3495 --cols 900:1560:50 --band 650:1350 --face-dark 40 --hinge-x 1603 \
    --temple-mm 9 --face-mm 8.5 --length-mm 8.8 --print 1025,982 1228,1013 1232,1060 1030,1028
python3 tools/photo/export_web.py      # every final -> assets/photography/ (AVIF, WebP, JPEG) + MANIFEST.csv
```

A cast member wearing a real frame (the person is generated without glasses; the frame is the cleaned photograph, sized from the 1:1 drawing):
```
pip install --break-system-packages insightface onnxruntime
python3 tools/photo/wear.py content/photography/people/W1-S07-F02-A1.json
```

Fonts (Owners Wide, Stolzl) are not in this repo: see `brand/fonts/README.md`.
