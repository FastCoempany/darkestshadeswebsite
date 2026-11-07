# WALL-PROGRESS.md: the drawer wall, run 1

The run's memory (`docs/build/DRAWER-WALL.md`, Part 2). Re-read both at the start of every phase and after every compaction. Run 1 is D0–D7; run 2 (D8, D9) starts from "Now and next".

## Links

| What | Where | Since |
|---|---|---|
| **The phone build (R2)** | not yet (D7) | |
| **The R1 review set** | not yet (D3) | |

## Checks failing for environment reasons

| Check | Reason | Logged |
|---|---|---|
| S2's runtime half (module, GLB fetch, `createImageBitmap`, WebGL 2 inside a published Artifact) | The Artifact is private and the VM has no signed-in browser; the page reports the result on screen for Antaeus | D0, Nov 7 2026 |

## Phases

| Phase | State | Branch / PR | Evidence | Date |
|---|---|---|---|---|
| D0 · Start | done | `wall/d0-start` → PR #11 | the four spikes, with numbers, in "D0 · Start" below; `frame_texture.py --from-dam` run for F01 and F02 | Nov 7 2026 |
| D1 · The project | done | `wall/d1-project` → PR #12 | `npm run all` exit 0 on the empty project (check, Vitest 2/2, build, Playwright 22 passed and 8 skipped across the three projects, Lighthouse 100); the four screens shown in the session; in "D1 · The project" below | Nov 7 2026 |
| D2 · Records and logic | done | `wall/d2-records` → PR #13 | Vitest 286 tests in 9 files (every resolver case, missing and unknown value, every machine transition and every impossible one); `npm run check` validates `data/wall.json` and the manifest; `npm run all` exit 0; in "D2 · Records and logic" below | Nov 7 2026 |
| D3 · The wall and the drawer | in progress | `wall/d3-wall` | lookdev done against the prototype stills; the queue running (below) | Nov 7 2026 |
| D4 · The frames | not started | | | |
| D5 · The elements | not started | | | |
| D6 · The wall, together | not started | | | |
| D7 · On a phone | not started | | | |
| D8 · Feedback and realism | run 2 | | | |
| D9 · Hand-off | run 2 | | | |

### D0 · Start

**Environment (Nov 7 2026, this VM):** 4 CPUs, 15 GB RAM, 28 GB disk free. Node v22.23.4, npm 10.9.9, Python 3.13.18. Playwright 1.63.0 with Chromium 1243 in `/opt/pw-browsers`; WebKit 2359 (WebKit 26.6) and its system libraries installed by D0 at that same Playwright version (`npx playwright@1.63.0 install webkit`, `install-deps webkit`), and launched headless as an iPhone 14: WebGL 2 answered yes and `createImageBitmap` decoded a WebP there, which the e2e projects do not rely on for the live 3D (Part 2, Testing). `bpy` 5.2.2 LTS, pymupdf, scipy, scikit-image, OpenCV 5.0.0 (contrib, headless), jsonschema, cairosvg and pillow-avif installed by D0 (`pip install --break-system-packages`), about 4 minutes. No `/usr/bin/time`, no `blender` binary (bpy is the renderer). GitHub access through the session's tools works for `FastCoempany/darkestshadeswebsite` (admin); the `darkestshades` release repo is not attached to the session.

**The tortoise textures (F01, F02):** `frame_texture.py` reads `work/out/<shot>/cutout.png`, `layers/lens.png` and `stage-full.png`, which this VM does not have. Rebuilding them here would need `zipget.py` (a GitHub token for the `darkestshades` release, which this session's GitHub access does not cover) and `clean_lightbox.py` (rembg's ISNet and SAM models from Hugging Face, and the whole clean-up per shot). Not done: the DAM holds the same cleaned outputs at full resolution (`dam/product/DS-F01-A1-v01-master.png` is the cut-out with the lens filter in its alpha, `…-stage.png` the stage version), so D0 adds `--from-dam` to `frame_texture.py`, which reads those two files and takes the lens openings from the drawing after the same registration. Run on this VM: `frame_texture.py F02 --from-dam` (13.5 s; outline IoU 0.979; gold 2991 px, onyx 4224 px, pins 2107 px found on the front) and `F01 --from-dam --temples` (13.9 s; IoU 0.971; blue coverage 0.20, the temple band laid). Previews checked by eye: F02's crimson tortoise with the GCD on the right wing and the pins on the left; F01's blue blotches on black. Default behaviour (from `work/out/`) unchanged.

**Spikes:**

- **S4 · CDP touch drag in Chromium:** pass. `Input.dispatchTouchEvent` (touchStart, 12 touchMoves, touchEnd) through a Playwright CDP session, Chromium as a Pixel 7. On a `touch-action: none` pad: 1 pointerdown, 12 pointermoves following the finger (y 177 → 360 px), 1 pointerup. On a `touch-action: pan-y` box: the page scrolled 0 → 568 px, the element saw 1 pointermove then a pointercancel. So the e2e suites can drag with CDP and can tell a drag from a native scroll.
- **S3 · one drawer-view frame at final settings:** the prototype drawer (`drawer_scene.py`, F09 inside, the drawer 250 mm out) at 1200 × 1500, 48 samples, denoised, Cycles on 4 CPUs at `nice 19`: **158 s wall** (`spikes/s3-render.log`: the command and Blender's log), of which about 34 s is building F09 from its drawings (the same build timed in S1's log) and so about 125 s the render. Peak memory not measured (no `/usr/bin/time`). **Queue estimate from it:** base sequence 24 × 125 s ≈ 50 min; eight frame sequences as region renders (about a third of the pixels) 8 × 24 × 45 s ≈ 2.4 h; the two wall plates lit and dark (1170 and 2880 px wide, about 2.5× a sequence frame each) plus three knob close-ups ≈ 40 min; lifted stills and the environment map ≈ 20 min. About 4 h in all, well under the 12 h limit, so both the 720 px and the 1200 px sets are made in run 1.
- **S1 · F09 as a GLB next to Cycles:** done (`docs/build/drawer-wall/spikes/s1_blender.py`, `s1-three.html`, `s1-render.mjs`, `s1-compare.py`; the side-by-side `s1-f09-cycles-vs-three.jpg`: Cycles, three.js, the difference ×4). F09 built with `frame3d`, its Cycles materials swapped for glTF ones (acetate: base near black, roughness 0.06, IOR 1.49; lens: base near black, roughness 0, alpha = 1 − mean transmission, blended; `gcd_gold` metallic, roughness 0.22; `gcd_onyx`), triangulated and decimated (the GCD gently, to a sixth of the budget), exported with Blender's glTF exporter (Y-up, WebP images). Both renderers lit by the same environment: an equirectangular Cycles render of three emissive panels from the frame's centre (1024 × 512, saved as `.hdr`), the Cycles still film-transparent, AgX in both, the same camera (three-quarter from the GCD's side, 100 mm, 1024 px). Numbers, mean absolute difference in 8-bit sRGB over the pixels where either image is brighter than 5/255: as built (5.42 M triangles, decimated to 59,990, GLB 1.20 MB, export 49 s) **31.6**; built at `mesh_step` 4 (0.97 M triangles, decimated to 59,990, GLB 1.26 MB, build 10 s, export 5 s) **24.6**; over the whole image 0.32. three.js is brighter over those pixels (mean luminance 39 against Cycles's 22, out of 255), and by eye the extra light sits along the rims: the decimated mesh's normals scatter the panels' reflections where Cycles's smooth surface shows one thin highlight. Build times: 34 s for F09 as built, 10 s at `mesh_step` 4 (`spikes/s1-blender.log`). The environment's orientation was checked by brute force (`spikes/s1-sweep.sh`: four rotations, mirrored or not): the map as saved, unrotated, is the best. GLB load in three.js 25 ms; WebGL 2 through SwiftShader in headless Chromium. **What D4 takes from it:** build for the GLB at `mesh_step` 4 and decimate less brutally (the triangle budget holds either way); keep smooth normals; the lens as an alpha-blended glossy surface reads right at this size; the match is close enough to go on, and the materials are tuned against the drawer's own HDR before D5 (the risk table). The GLB's `KHR_materials_ior` was not written (1.49 rounds to glTF's default 1.5), so no extension is needed.
- **S2 · a test Artifact (page, module, GLB, WebP):** published, private: https://claude.ai/artifact/2vxLcc1s6j223jMUt8YfSx (`spikes/s2-index.html`, `s2-probe.js`). Six files served with their types: `index.html`, `probe.js` (text/javascript), `still.webp` (image/webp, 15 KB), `still.avif` (image/avif, 12 KB), `data.json`, and the GLB. **The host serves no `.glb`, `.hdr`, `.exr` or `.bin` under any content type** (the served types: html, css, js, mjs, wasm, json, map, txt, md, csv, xml, svg, png, jpg, gif, webp, avif, ico, woff, woff2, ttf, otf, mp3, wav, ogg, mp4, webm, pdf), so the GLB went up as `F09.glb.wasm` (application/wasm, 1.2 MB) and the page fetches it as bytes. From this VM the link answers "Sign in to view this page" (private, as intended), so the runtime half is reported by the page itself: a status line "Pass" or "Fail" followed by module, GLB fetch, WebP decode, AVIF decode and WebGL 2, each yes or no (Pass needs the first three; AVIF and WebGL 2 have fallbacks in the wall), and the full report under a copy button; Antaeus confirms it on a phone (question below). The publication plan for D7 follows from this: the built wall's binary assets that the host will not serve by their own names (the GLBs, the HDR) are published under a served name and loaded as bytes, recorded in the manifest; everything else keeps its name.

### D1 · The project

**The stack, pinned** (`wall/package.json`, all devDependencies, exact versions): vite 8.3.6, typescript 7.0.2 (type-checks the Lit decorators with `experimentalDecorators`), lit 3.3.3, three 0.187.0, @use-gesture/vanilla 10.3.1, @fontsource-variable/mona-sans and urbanist 5.3.0, vitest 5.1.0, @playwright/test 1.63.0 with playwright and playwright-core 1.63.0 (the VM's Chromium 1243 and WebKit 2359 belong to that version; @axe-core/playwright 4.14.0 then shares it), lighthouse 13.6.0 with chrome-launcher 1.2.3, @gltf-transform/{cli,core,functions,extensions} 4.5.1, meshoptimizer 1.3.0, ajv 8.20.0, ajv-formats 3.0.1, @types/three, @types/node.

**What's there:** the scripts (`dev`, `build` = type-check then `vite build` to `wall/dist/` with relative paths and `noindex`, `preview`, `test`, `test:e2e` with `--trace off`, `check`, `lighthouse`, `assets`, `all`); `vite.config.ts` (two pages, three.js in its own chunk, `virtual:fonts-local` for licensed font files in `brand/fonts/private/`, `PUBLIC_ADOBE_FONTS_KIT` for a kit); `playwright.config.ts` with the three projects (wall-pixel: Chromium as a Pixel 7; wall-iphone: WebKit as an iPhone 14; wall-desktop: Chromium at 1440 × 900) against the built wall served by `vite preview`, baselines next to the specs, `WALL_NO_PIXELS=1` for CI; the checks (`checks/strings.mjs`: the banned names over `wall/src`, the pages, `wall/data` and the copy deck's `wall` section; `colors.mjs`: no hex, color functions or named colors in any CSS the wall ships; `schema.mjs`: the records and the manifest against their schemas, a data file without a schema fails; `assets.mjs`: every manifest entry on disk, every file in the manifest, every file within its kind's budget; `lighthouse.mjs`: mobile, performance ≥ 90, LCP ≤ 2.5 s, CLS ≤ 0.1, TBT ≤ 200 ms, the report to `test-results/lighthouse.json`); the empty asset manifest and its schema (kinds, statuses, budgets); `index.html` and `states.html` with labelled placeholders where the wall and the sheet will be, the brand mark as favicon, `noindex`, the scene black; `src/styles/base.css` (the tokens, type that recedes, the focus ring, `.visually-hidden`), `fonts.css` (the stand-ins); the e2e specs `fonts.spec.ts` (each role's faces loaded at its weights, in all three browsers), `pages.spec.ts` (both pages load without errors, carry `noindex`, sit on black, pass axe at WCAG 2.2 AA tags) and `screens.spec.ts` (both pages at 390 and 1440, to `test-results/screens-*/`); `.github/workflows/wall.yml` running `npm run all` without pixel comparisons.

**The token:** `surface-scene` (black) added through `tools/palette.py` in both themes, with `text-primary`, `text-secondary`, `text-tertiary` (4.5:1) and `focus-ring` (3:1) checked on it in night, the theme the wall renders in (`CHECKS` entries may now name their themes; the paper theme never shows the wall), then `python3 tools/build_tokens.py` (`design/tokens/build/*.css` regenerated; wire mode maps it to white). Contrast report: 16.56, 8.52, 6.08 and 8.85.

**The review's fixes** (an agent that did not build it, against the docs): the colors check now reads every string and numeric literal in the TypeScript too (a three.js `Color('#…')`, a canvas `fillStyle`, `0xffffff`), `.svg` files under `src`, every attribute in the pages, and ties the pages' `theme-color` meta to the `surface-scene` token's built value; named colors count only in CSS and markup, so a knob style called `gold` in the records is not a color. The WebP allowance is gone: AVIF and WebP meet the same budget. `WALL_NO_PIXELS` is wired to Playwright's `ignoreSnapshots` and to nothing else. Lighthouse fails when a metric is missing. The banned-strings patterns take any punctuation between their parts, and the check also reads the manifest, `wall/public` and a built `wall/dist`. Route B for the licensed fonts (files in `brand/fonts/private/`) now injects the `@font-face` rules into each page's head, serves the files in dev and copies them to `dist/fonts/` with relative URLs.

**Exit evidence (Nov 7 2026, rerun after the review's fixes, the D2 drafts out of the tree):** `cd wall && npm run all` → exit 0: strings 15 files, 0 banned; colors 7 files, 0 literal; schema: `assets/manifest.json` validates, `data/wall.json` not there yet (D2); assets 0 entries, 0 failures; Vitest 2 passed; build 100 ms (initial JS 0.05 kB + 0.67 kB, no three.js chunk yet, fonts 189 kB of woff2); Playwright 30 tests: 22 passed, 8 skipped (the review screens run once, from desktop Chromium); Lighthouse mobile performance 100, LCP 752 ms, CLS 0.000, TBT 0 ms. Screens of `index.html` and `states.html` at 390 and 1440 taken by `screens.spec.ts` and shown in the session (stand-in type: Urbanist for the micro labels).

### D2 · Records and logic

**The records** (`wall/data/wall.json`, `wall.schema.json`): nine metaobject-shaped records, one `bay_wall` (handle `frames`; `bays` a JSON list of the eight `drawer_bay` ids in look-number order F01, F02, F03, F04, F05, F06, F08, F09; `knob_style` `black-relief`; `render_set` `wall-v1`) and eight `drawer_bay` (`frame`, `state` `available`, `light` `auto`, `note` empty). The schema holds the field keys, the Shopify field types and the value enums; `npm run check` now requires both data files and fails without them.

**The logic** (`wall/src/`): `data/adapter.ts` (`readRecords`: metaobject shape in, typed drawers out; a missing field null, an unknown value kept for the resolver, a broken `bays` reference or a duplicate reported; `withRecord` replaces one drawer and no other); `lib/resolve.ts` (the seven rules of "How a drawer's state is resolved", `priceText` from the record's amount and currency, `resolveWall`); `lib/machine.ts` (the reducer: every transition of the table, impossible ones return the same object, Esc stepping back, the knob pull carried as a pointer, `RECORD` mid-view); `lib/gestures.ts` (every constant of the table and the pure math: tap, rubber band, pull position, release, turn, inertia, zoom); `lib/spring.ts` (the settle spring at 180/26 in 16 ms substeps); `lib/tier.ts` (tier 1 or 2 from WebGL 2, device memory, Save-Data, a lost context); `lib/manifest.ts` (the asset index: plate, rects, dark crops, sequences per width, GLB, stills, env, cameras, tints; `hasSequence` and `hasLift` for the resolver); `lib/types.ts`; `data/extract.ts` with `virtual:wall-frames` and `virtual:wall-copy` in `vite.config.ts`, so the built wall ships only the eight frames' facts (id, handle, look number, name, descriptor, price, GCD length and placement, front width, lens color) and the copy deck's `wall` section with the alt phrases and the brand's names, nothing of the site's sections.

**The copy** (`content/copy/en.json`, `wall`, status `draft`): the strings DRAWER-WALL.md lists, plus `announce.photo`, the records panel's labels (`panel.*`, "Records (example data)" as Part 1 names it) and the event log's two (`debug.*`); all on the sign-off list below.

**The review's fixes** (an agent that did not build it): the records schema moved to draft 2020-12 so each record carries each key exactly once (`contains` with `minContains`/`maxContains`), `reference` is allowed on a field as the Storefront API returns it, and `checks/schema.mjs` cross-checks the records after validation (every id a `bays` list names is a `drawer_bay`, none twice, every `frame` is a product in `content/products/`). The shipped frame facts are trimmed to what the wall shows (id, handle, look number, name, price): the GCD placement notes, measurements, lens color and descriptor no longer ship, and a value the record lacks is null, never filled in (the handle fallback is gone). Four resolver tests added (locked with no price, sold out without lift assets, hidden with an unknown frame, null name and look number).

**What the run added beyond Part 2's table, kept and recorded** (decision log): a `DRAG` in `opening` or `shutting` catches the settling drawer (Part 1 step 3: the drawer follows a dragging finger); `SHUT_DRAWER`, the quiet button's reverse of `OPEN_DRAWER` (Part 1: `wall.shut`); Esc while pulling settles the drawer shut; Esc during a transition (`entering`, `opening`, `shutting`, `lifting`, `returning`, `leaving`) does nothing, so D5's elements must always emit the completion event; `canLift` turning false while a frame is lifted leaves the view where it is (the doc closes the view only when the drawer can no longer open); `priceText` formats a non-USD price as "EUR 100" and shows cents only when there are any (the records hold $100, so neither case is reached). The resolver and the adapter return their problems; `log.ts` (D5) writes them to the debug log, so "and logged" lands with the elements.

**Exit evidence (Nov 7 2026, after the review's fixes):** `npx vitest run` → 9 files, 286 tests passed: resolve 27 (available, sold out, locked, hidden; no frame, unknown frame, a prototype-property frame id, no state, unknown state, unknown light, missing light, several problems; light overrides on each state; assets missing; a missing price or name renders nothing; price formatting), machine 210 (the happy path, each state's transitions, all 158 impossible transitions by identity, Esc from every state, the carried pointer, a record changing mid-view), adapter 10, gestures 14, spring 5, tier 4, manifest 7, extract 7, project 2. `npm run check` → strings 28 files 0 banned, colors 17 files 0 literal, schema 2 files validated and 9 records cross-checked against 8 products, 0 failures, assets 0 failures. `npm run all` → exit 0: the checks as above, Vitest 282, build 140 ms (the initial JS still 0.05 kB + 0.67 kB: nothing of the logic is imported by the pages yet, that is D5 and D6), Playwright 22 passed and 8 skipped in the three projects, Lighthouse performance 100, LCP 753 ms, CLS 0.000, TBT 0 ms.

### D3 · The wall and the drawer

**The tools:** `tools/blender/drawer_wall.py` (the cabinet and the drawers from the prototype: world-space calfskin grain, piping, the knob tilted 28° with the 30 mm GCD as black relief, gold or plain; the seam light as state, a warm pool of light on the suede inside; the two layouts, orthographic 15° down, `rects.json` projected from the geometry; the 24-frame drawer-view sequence with the camera moving from the wall's angle to looking in, region renders for a frame; the knob close-ups; `cameras`; `env`; `lifted`; `--check`), `tools/photo/grade_scene.py` (the prototype's grade as the one grade, grain seeded per output, scene black exact at the edges, `--toe`), `tools/blender/render_queue.py` (resumable jobs in chunks), `tools/blender/wall_export.py` (the web outputs within budget, the dark crops with the plate's own grain, the manifest entries, `r1`), `tools/blender/queue_d3.sh`.

**Lookdev** (`work/wall/lookdev*.png`, against `prototype/stills/`): the room's light brought down to the prototype's level; the seam glow as a thin amber line; the drawer's suede darkened to brown-black with a warm pool on its floor; the view's end pose moved back so the cabinet shows above the open drawer. The grade measured against the founder-reviewed still: its cabinet sits at about 36/255, so the wall's grade is the cool cast at exposure 0.3 with a 0.004 toe (the leather lands at 38/255); one grade for every image, the drawer's warmth from the scene's own light so the view continues the wall at its first frame. The portrait rail went from 96 to 114 mm after the first wall build showed a two-line name pushing its price into the drawer below at 390 px.

**Exit evidence (Nov 7 2026):** (filled in as the queue lands)

## Now and next

- D2 done; D3 next: `tools/blender/drawer_wall.py` (the cabinet, the drawer, the walls, the sequence, `--check`), `tools/photo/grade_scene.py`, `tools/blender/render_queue.py`; lookdev on one drawer against the prototype stills, then the walls, the base sequence, `open.json`, `inspect.json`, the environment map; the R1 set.

## Render queue

`work/queue/d3.json`, filled by `tools/blender/queue_d3.sh`, run by `tools/blender/render_queue.py run d3 --minutes 95` in the background at `nice 19`; `status d3` lists every job. Jobs whose outputs exist are skipped, so a reclaimed VM resumes where it stopped (the web outputs are committed after every chunk).

| Job | State | Time | Notes |
|---|---|---|---|
| wall portrait lit, dark (1170 px, 64 samples) | running | | `drawer_wall.py wall` |
| wall landscape lit, dark (2880 px) | queued | | |
| knob close-ups: black-relief, gold, plain (1024 px, 96 samples) | queued | | for O15 (R1) |
| base sequence, 24 frames (1200 × 1500, 48 samples, denoised) | queued | about 2 min a frame from S3 | one job per frame |
| cameras (open.json, inspect.json), env (1024 × 512), the F09 lifted still | queued | | |
| the eight frame sequences, region renders | D4 | | |

## Review gates

| Gate | When | Where | Antaeus's answer |
|---|---|---|---|
| R1 | D3 | | |
| R2 | D7 | | |
| R3 | run 2 | | |
| R4 | run 2 | | |

## Usability results

Not yet (the founder runs the test after R2; template in `docs/build/drawer-wall/usability.md`, written in D7).

## Decision log

| Date | Decision | Why | Phase |
|---|---|---|---|
| Nov 7 2026 | F01's and F02's textures come from the DAM masters (`--from-dam`), not from a rebuilt `work/out/` | The release zip and the segmentation models are out of this session's reach; the DAM holds the same cleaned outputs | D0 |
| Nov 7 2026 | Asset budgets the Budgets table does not name, set by the run in `wall/checks/assets.mjs`: a dark crop 60 KB, a lifted still 200 KB, a JSON asset (camera, rects, tints) 20 KB; AVIF and WebP meet the same budget | The check must fail on something for every kind; these sit under the table's neighbours | D1 |
| Nov 7 2026 | The wall renders in the night theme only; `surface-scene` is black in both themes and its contrast pairs are checked in night | The scene is the image (#43); nothing of the wall appears on paper | D1 |
| Nov 7 2026 | The state machine carries three transitions Part 2's table does not list: `DRAG` catching a settling drawer, `SHUT_DRAWER` (the quiet button's reverse), Esc while pulling settling shut; Esc does nothing mid-transition | Part 1 step 3 (the drawer follows the finger; `wall.shut`); a transition always ends in its completion event | D2 |
| Nov 7 2026 | The built wall ships only the eight frames' id, handle, look number, name and price, and the copy deck's `wall`, `alt` and `meta.brand` entries | Part 1 shows nothing else of a frame; internal notes and the site's sections stay in the repo | D2 |
| Nov 7 2026 | The one grade: the cool cast at exposure 0.3 and a 0.004 toe, on every image of the wall and the drawer view alike | The founder-reviewed prototype still's cabinet measures about 36/255; the prototype's own toe lifted the room off black, which the exact-black edges forbid; the drawer's warmth comes from the scene's light so the view continues the wall | D3 |
| Nov 7 2026 | The portrait rail is 114 mm (the landscape 56 mm) | A two-line name at 11 px with its price needs it at 390 px; "deep enough for that drawer's label at its width" | D3 |
| Nov 7 2026 | The knob's GCD keeps about a sixth of the GLB's triangle budget (around 10 000), not its full curve density (about 90 000 as built) | S1: the full-density GCD alone nearly fills the 100 000 hard limit; its length and centre are checked within 2% and 0.5 mm after decimation | D4 |

## Questions for Antaeus

| Question | Default in use | Where it came up |
|---|---|---|
| Open the S2 test page on your phone (https://claude.ai/artifact/2vxLcc1s6j223jMUt8YfSx) and tell me its status line, the one under the description that starts with "Pass" or "Fail" and lists module, GLB fetch, WebP decode, AVIF decode and WebGL 2. It says whether a published Artifact can run the wall's module scripts, fetch its GLBs and decode its images. | The wall is built as if it passes; if it doesn't, D7 falls back to GitHub Pages, only with your yes (O18) | D0, S2 |

## Copy for sign-off

The `wall` section of `content/copy/en.json`, status `draft`, added in D2. Every string below is Claude's draft in the brand voice and needs Antaeus's yes before launch.

| Key | Draft | Where it shows |
|---|---|---|
| `wall.title` | The frames | The page's only heading, visually hidden |
| `wall.openLabel` | Open the drawer. | Each drawer's accessible name: "{name}, $100. Open the drawer." |
| `wall.notYet` | Not yet. | A locked drawer's label, in place of the name |
| `wall.soldOut` | Sold out | A sold-out drawer's label |
| `wall.hintPull` | Pull it toward you | The drawer view, shut, after 1.2 s |
| `wall.hintLift` | Tap them to lift them out | The drawer view, open, after 1.2 s |
| `wall.hintTurn` | Turn them. Pinch to come closer. | The lifted view, after 1.2 s |
| `wall.open` / `wall.shut` | Open the drawer / Shut the drawer | The quiet buttons that do what the pull does |
| `wall.close` | Close | Back to the wall |
| `wall.lift` / `wall.putBack` | Lift them out / Put them back | The lift and its reverse |
| `wall.photos` / `wall.photosClose` | See the photographs / Back to the frame | The photographs and back |
| `wall.turnLeft`, `wall.turnRight`, `wall.closer`, `wall.further`, `wall.reset` | Turn left, Turn right, Closer, Further, Reset | The lifted view's buttons |
| `wall.model3dLabel` | {subject}, a view you can turn | The live frame's accessible name |
| `wall.announce.open` | {name}. The drawer is open. | The live region |
| `wall.announce.shut` | The drawer is shut. | The live region |
| `wall.announce.lifted` | {name}, lifted out. | The live region |
| `wall.announce.back` | {name}, back in the drawer. | The live region |
| `wall.announce.photo` | {name}, photograph {n} of {count}: {alt} | The live region, in the photographs (added by the run) |
| `wall.panel.title` | Records (example data) | The simulated backend, `?panel=1` (Part 1 names it) |
| `wall.panel.frame`, `.state`, `.light` | Frame, State, Light | The panel's fields (added by the run) |
| `wall.panel.mechanic`, `.tapFirst`, `.pullFirst` | How a drawer opens, Tap first, Pull first | The panel's `?mech=` choice (added by the run) |
| `wall.panel.close` | Close the records | The panel (added by the run) |
| `wall.debug.copy`, `.copied` | Copy the event log, Copied. | `?debug=1`, for the usability sessions (added by the run) |
