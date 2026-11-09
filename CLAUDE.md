# CLAUDE.md: Darkest Shades, the drawer wall

Darkest Shades is a sunglasses brand that sells eight frames at $100 in drops. The work in this repo is **the drawer wall** (`docs/brief/00-decisions.md` #44, #46): the eight frames shown in a wall of drawers, built as one standalone piece in `wall/` by the run in `docs/build/DRAWER-WALL.md`. **It is not a website**: no pages, navigation, bag or checkout. The site build of Oct 30–31 was thrown out (#46). Nothing from it is used; it sits on the `archive/site-build-2026-10-31` branch only so the history is complete.

## Read first, in order
1. `docs/brief/00-decisions.md`: what's settled and what's open. It wins any conflict.
2. `docs/brief/01-brand-system.md`, `02-raf-lens.md`, `06-products.md`, `07-photography.md`, `08-copy.md`. Parked, because they describe a website (#46): `03`, `04`, `05` and `09` (except `09`'s "Workspace setup").
3. `content/products/*.json`, `content/copy/en.json`, `design/tokens/`.
4. During the build run: `docs/build/DRAWER-WALL.md` and `docs/build/WALL-PROGRESS.md` (where it stands). Re-read both after every compaction.

## Non-negotiables

**Brand**
- Tagline: **See Everything. Reveal Nothing.** Prada is the idol; the design lens is "philosophy as manifesto, before product" (`02-raf-lens.md`). **Raf Simons is never named, shown or quoted** anywhere in the wall, its metadata, alt text or shipped code.
- Marks: Anastasiia's logo and angular brand mark are primary; the **GCD** (gold band, black onyx inset) is the secondary insignia. **The favicon uses the brand mark, never the GCD.** Marks come only from `brand/marks/` and `brand/emblems/gcd/`. The Eclipse Silhouette and the old engraved wordmark never appear.
- **The GCD on the product executes one way only**: full size, its own proportion and its one placement (`01-brand-system.md`; per frame in `content/products/`), on every frame in every photo, composite and render, whatever the view. Never scaled, moved or left off to suit a picture.
- Fonts: **Owners Wide** (Medium) and **Stolzl** (Light, Book, Regular, Medium) only. **Never commit font files** (public repo); load them as `brand/fonts/README.md` says. Until they're licensed, the open-licensed stand-ins in that README (Mona Sans, Urbanist) render them; no other fonts.
- Color: **role tokens only** in `wall/src/` (`--color-surface-*`, `--color-text-*`, `--color-action-*`, `--color-status-*`, `--color-border-*`, `--color-focus-ring`); no hex values. Graphite `#545454` is never text on dark. One gold element per view. Product photographs always sit on the stage color; the wall's scenes are dark (#43, #44).

**Honesty**
- **No price appears on the wall** (`00-decisions.md` #47, the founder's "remove pricing", Nov 9 2026): not under a drawer, in the drawer or lifted view, in a drawer's accessible name or in the no-JavaScript list, and the built wall ships none of the frames' `price` fields. The records in `content/products/` keep the price as a product fact (O19).
- The wall shows only what its records hold: no countdowns, quantities or dates it doesn't have; a missing value renders nothing. No discounts, no fake urgency, no invented reviews (`08-copy.md`).

**Products and copy**
- Every product fact comes from `content/products/` (from the 1:1 drawings). **Never invent a spec.** Frames carry the founder's names (`06-products.md`); names are never explained or tied to a real person.
- All copy from `content/copy/en.json` (the wall's own section). No lorem ipsum anywhere. `@darkestshades`, `darkestshades.com`, `#DarkestShades`.

**Imagery**
- Product photos only from the cleaned lightbox set, with the GCD and without the old marks. The wall shows renders of the 3D frames rebuilt from the 1:1 drawings, matched to those photos (#44). No generated glasses, hands or people in the wall. Every image's status (prototype, mockup, final) is tracked in the wall's asset manifest. Reference videos, the reference film (#43) and Prada/runway material never ship.

**Build**
- The wall only, standalone in `wall/`: each drawer its own element with its own record, shaped like a Shopify metaobject. No live Shopify calls, no checkout, nothing from the archived site build.
- Mobile first: 390, then 768, 1024, 1440. WCAG 2.2 AA. Every gesture has a button that does the same.
- Change tokens through `tools/palette.py` and `design/tokens/tokens.base.json`, then `python3 tools/build_tokens.py`; never hand-edit `design/tokens/build/`.
- Free tools only. No purchases, no paid APIs.

## Commands
```
python3 tools/palette.py          # color tokens + contrast report (fails on any contrast failure)
python3 tools/build_tokens.py     # design/tokens/build/*.css
python3 tools/marks.py            # web marks + favicon set from Anastasiia's masters
python3 tools/drawings.py         # vector line art from the technical drawings (needs pymupdf)
python3 tools/blender/gcd_render.py --size 4096 --samples 160 --views front,yaw35,yaw60   # needs bpy==5.2.2
python3 tools/photo/zipget.py --picks content/photography/lightbox-angle-set.json --frames F08   # originals → work/originals/
python3 tools/photo/clean_lightbox.py content/photography/shots/IMG_3596.json   # one shot → work/out/IMG_3596/ (07-photography.md)
python3 tools/photo/export_web.py                                              # every final → assets/photography/ (AVIF, WebP, JPEG) + MANIFEST.csv, masters → dam/product/
python3 tools/photo/temple_gcd.py IMG_3495 --cols 900:1560:50 --band 650:1350 --face-dark 40 --hinge-x 1603 --temple-mm 9 --face-mm 8.5 --length-mm 8.8 --print 1025,982 1228,1013 1232,1060 1030,1028   # GCD placement on a temple, for the shot's settings
python3 tools/photo/wear.py content/photography/people/W1-S07-F02-A1.json      # a cast member wearing a cleaned frame → work/people/
python3 tools/blender/frame3d.py F04 --check --out /tmp/F04.png                 # a frame rebuilt in 3D from its drawings, upright in a light tent
python3 tools/blender/wear3d.py content/photography/people/M1-S06-F04-A1.json   # the cast member wearing the 3D frame in the scene's light → work/people/<id>-3d/ (depth model: work/models/, head3d.py)
python3 tools/photo/cutout.py content/photography/people/M1-S06-F04-A1.json     # that picture cut out: the person wearing the frame on transparency → work/people/<id>-3d/cutout.png
python3 docs/build/drawer-wall/prototype/drawer_scene.py --ext 0,0.25 --outdir work/drawer-proto --samples 40 --size 760   # the founder-reviewed drawer prototype
```
```
cd wall && npm install            # once; the stack is pinned in wall/package.json (Playwright 1.63.0 matches the VM's browsers)
npm run dev                       # the wall at http://127.0.0.1:5173/ (index.html; states.html is the states sheet)
npm run build                     # type-check, then the static wall in wall/dist/ (relative paths, noindex)
npm run test                      # Vitest: the logic
npm run test:e2e                  # Playwright: wall-pixel (Chromium as a Pixel), wall-iphone (WebKit as an iPhone), wall-desktop
npm run check                     # banned strings, literal colors, the record and manifest schemas, the asset budgets
npm run budget                    # after a build: the initial JavaScript <= 60 KB gzipped without three.js; the 3D chunk <= 200 KB, reached only at a lift
npm run lighthouse                # Lighthouse mobile on the built wall: performance >= 90, LCP, CLS, TBT
npm run assets                    # the zoom images from dam/ into wall/public/zoom/ (D4; never committed)
npm run all                       # check, test, build, budget, test:e2e, lighthouse, in that order
node tools/web/phone_set.mjs      # after a build: the phone set for the Artifact link in work/phone/ (D7; never committed): the page without the host's skeleton, 1200 px WebP sequences, .glb/.hdr as .wasm, the manifest rewritten, publish-plan.json
```
```
python3 tools/blender/drawer_wall.py wall --layout portrait --knob black-relief --variant lit   # the wall plate render → work/wall/ (and --variant dark, --layout landscape)
python3 tools/blender/drawer_wall.py sequence --frames 24 [--frame F09 --region --tint r g b]   # the drawer view's 24 frames (the base, or a frame's region renders)
python3 tools/blender/drawer_wall.py knob --knob gold                                           # a knob close-up for O15
python3 tools/blender/drawer_wall.py cameras [--frames F09 --mesh-step 4]; python3 tools/blender/drawer_wall.py env   # camera/open.json, inspect.json (every frame's resting and lifted pose); the drawer's HDR
python3 tools/blender/drawer_wall.py lifted --frame F09 --tint r g b                             # a lifted still
python3 tools/blender/drawer_wall.py check --layout portrait --knob black-relief                 # rects, dark crops, scene black, the 30 mm knob GCD
python3 tools/photo/grade_scene.py in.png out.avif --width 1170 [--edge 0.02 0.06]   # the one grade (cool, exposure 0.3, toe 0.004, the defaults); the edge band per kind as wall_export.EDGE has it
python3 tools/blender/wall_export.py wall --layout portrait | sequence [--frame F09] | cameras | env | stills [--frame F09] | knobs | r1   # the web outputs + manifest entries
bash tools/blender/queue_d3.sh; python3 tools/blender/render_queue.py run d3 --minutes 95        # the D3 render queue, in chunks (status d3)
```
```
python3 tools/photo/lens_tints.py                                                                  # each lens's measured transmission → wall/assets/lens-tints.json and its manifest entry; F04 takes #38's values
python3 tools/blender/frame_glb.py F09 --out work/glb/F09.glb --check --report work/glb/F09.report.json   # a frame as a GLB (needs bpy==5.2.2); --check: triangles, bytes, the GCD's side, length and centre, the front's width
node tools/web3d/optimize.mjs --all --manifest                                                     # every work/glb/F0X.glb → wall/assets/glb/ (meshopt, WebP textures) with its manifest entry carrying the report
bash tools/blender/queue_d4.sh; python3 tools/blender/render_queue.py run d4 --minutes 115         # the D4 render queue: each frame's region renders and lifted still, with its measured tint (TINTS=path reads another tints file)
python3 tools/blender/wall_export.py sequence --frame F09; python3 tools/blender/wall_export.py stills   # a frame's sequence composited over the base; the lifted stills (--frame F09 for one)
python3 tools/photo/zoom_export.py                                                                 # = npm run assets: each frame's A1, A2, A3 and A6 stage masters → wall/public/zoom/ (never committed)
```

## When unsure
If `00-decisions.md` doesn't answer it and it touches brand, product facts, money or legal copy, ask the founder. Otherwise make the call and note it in the PR.
