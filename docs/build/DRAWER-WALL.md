# Build run: the drawer wall

I'm Antaeus, the founder; where the docs say "the founder", that's me. This session builds the frames page as a wall of drawers: a working, photoreal mockup on the real stack (Hydrogen, mock data in Storefront API shape), good enough to put in people's hands on their phones, and built so that it becomes the real page at launch. The site itself was built on Oct 30–31 (RUN.md phases 0–6, PRs #1–#9) in the look before Nov 5. This run replaces what `/frames` shows today (the stage-card grid) with the drawer wall, inside that app, with its components, mock store, cart, tests and checks.

Part 1 is what we're making. Part 2 is how to build it. Part 3 is for me: how I start the run. This file and `docs/build/PROGRESS.md` are your memory; re-read both at the start of every phase and after every break or compaction.

The decisions behind this run: `docs/brief/00-decisions.md` #43 (the look), #44 (the drawer wall), #45 (no added cost), and the open items O15–O18. They outrank anything else in `docs/brief/` that describes the earlier look.

---

# Part 1 · What we're making

## In one paragraph

`/frames` is a dark room with one cabinet in it: a wall of identical drawers in black calfskin, one frame to a drawer. A thin warm light leaks from the seam of every drawer that holds a frame you can see. Under each drawer: its look number, its name and $100. You tap a drawer and it comes forward; you pull it toward you and it slides out, the frame waiting inside in warm light; you tap the frame and it rises into the light, where it turns and comes closer under your finger. One more tap shows the real photographs at full resolution. You put it back, shut the drawer, and the wall is there again. Every drawer is its own thing: its own component, its own record in the backend, its own state.

## The look (#43)

Private and intimate. The site is near-black; the scenes are the image.

- **Light.** Cool grey-green outside (the cabinet, the room), warm amber inside (the drawer's interior, the light the frame waits in). Soft sources, never hard flash. Shallow focus in the drawer view. The gold of the frame's GCD is the only gold in any view.
- **Surface.** The prototype grade (`docs/build/drawer-wall/prototype/grade.py`): luminance-weighted film grain about 2.8%, a little halation on the brightest highlights, a soft vignette, a touch of lens softness, made in the image pipeline and identical on every asset. Never CSS filters.
- **Type.** It recedes. Scene lines in Stolzl Light (the Urbanist stand-in at 300), sentence case, 22 px and up. Labels and hints in Stolzl Medium micro: 11 px, uppercase, tracking +0.12em. Prices in tabular figures at body size (`01-brand-system.md`). No headlines on this page.
- **Interface.** Nearly invisible, never absent. Every gesture has a visible, quiet text button that does the same thing (WCAG 2.2 SC 2.5.1 and 2.5.7), in `text-secondary`, with the gold focus ring.
- **Where the pale stage appears.** Only in the photo zoom: the real photographs on their stage color, studied. Everything else sits on `surface-scene` (black).
- **Look references, in the repo:** `docs/build/drawer-wall/prototype/stills/` (the founder-reviewed drawer, shut, half and open; the lift pair, dark and lit). My private links, if your session can read Artifacts: the look mockups `https://claude.ai/artifact/FEiHsc3xekH5HhDXuVyVjv`, "pull toward you" `https://claude.ai/artifact/HNne2t63Vb3Ao3ekCGXqQj`, the leather drawer `https://claude.ai/artifact/8HTpadDkKaHgmoEXQ1SxUz`.

## The wall

- **The cabinet.** Black calfskin over every face: a fine irregular pebble grain, a coarser crease, a satin sheen with soft mottling, piped edges (a fine cord along the top and bottom of each drawer front). The grain is in world space, so no two drawers carry the same grain. The room is black.
- **A drawer.** Front about 220 × 122 mm. One knob, centered: blackened metal, about 46 mm across and 22 mm deep, its face tilted 28° up toward the person opening it. On the knob's face, the GCD as an ornament, 30 mm long: in black relief by default, metal and stone both black, so it reads by light, not color (O15). Inside: a warm brown-black suede lining; the frame sits on it upright, temples open, front toward you.
- **The seam light.** Each drawer has two looks. `lit`: a thin warm light escapes along its seams, because the drawer holds a frame you can look at. `dark`: no light, because the frame is sold out, locked or hidden. The light is state, never decoration, and never a promise the data doesn't make.
- **Layouts.** Two renders of the same cabinet. Portrait (under 1024 px): 2 drawers across, 4 rows. Landscape (1024 px and up): 4 across, 2 rows. Never a row of three (`06-products.md`: F04, F05 and F09). The drawers are identical; only the cabinet's proportions change: the rail under each row is deep enough for that drawer's label at its breakpoint. More bays means a re-render of the wall, nothing else.
- **Above the wall:** `frames.statement`, receding, in Stolzl Light; `frames.title` stays the page's hidden heading.
- **The camera.** Orthographic, tilted 15° down: the wall as you'd see it standing in front of a low cabinet, every drawer the same size, the knobs looking up at you.
- **Labels.** Under each drawer, on its rail, in HTML: the look number in camel micro, the name in micro `text-secondary` (wrapping, never truncated, at 320 px too), and `$100` at body size on the next line. A sold-out drawer adds `product.soldOut`. A locked one shows `drawer.notYet` in place of the name; its look number and `$100` stay. A hidden one has no label.

## One drawer, step by step

The default mechanic is **tap first** (O16). The **pull first** variant (`?mech=pull`) changes only step 2.

1. **The wall.** The page scrolls normally. Nothing moves on its own.
2. **Open.** Tap a drawer (anywhere on it, or Enter or Space). It comes forward: its part of the wall scales up into the drawer view while the room dims behind it, and the view's first frame, rendered from the wall's own angle, takes over. Pull-first variant: put a finger on the knob itself and pull down; the drawer view opens under your finger and the pull continues there. Anywhere else on the wall, a vertical swipe scrolls the page.
3. **The drawer view.** One full-screen layer, nothing behind it scrolls. The drawer, shut, barely lit; the hint `drawer.hintPull` with a thin falling line. Pull down to slide the drawer out: a scrubbed image sequence, the camera leaning in and down as the drawer comes out, the frame coming into the warm light. Let go and the drawer settles open or shut (velocity first, then position). A quiet button does the same (`drawer.open`, `drawer.shut`). Close (`nav.close`, Esc, or on wide screens a tap on the dim room around the view) returns you to the wall with focus on that drawer.
4. **Lift.** With the drawer open, the hint `drawer.hintLift`. Tap the frame (or `drawer.lift`). The rendered frame hands over to a live 3D frame at exactly the same place, then rises toward you into the light, turning to a three-quarter view, while the drawer dims and softens behind it.
5. **Turn and come closer.** One finger turns it: freely around, a little up and down. Pinch or double-tap brings it closer (to 3×); on desktop, drag and the wheel. Buttons: `drawer.turnLeft`, `drawer.turnRight`, `drawer.closer`, `drawer.further`, `drawer.reset`. The view keeps its full sharpness at every zoom because it is drawn live at the screen's resolution.
6. **The photographs.** `drawer.photos` opens the real lightbox photographs (A1, A2, A3, A6 where they exist) on their stage color in the existing `Gallery`, whose zoomed state now loads each photograph at full resolution, pinch and drag to one image pixel per screen pixel. `drawer.photosClose` goes back to the frame. `drawer.framePage` links to the frame's own page (`/frames/{handle}`: the full gallery, specs, drawings, worn by).
7. **Buy.** In the drawer view and the lifted view: the name, `$100`, and the buy row the data allows: `product.addToBag` while the drop is live and the frame is in stock; `product.soldOut` when it isn't; the drop line from `drop.states.*` before the drop, with real values only ("Drop 001. Date to be announced." today). Add to bag updates `Bag (n)` and announces it.
8. **Put back.** `drawer.putBack`, a tap on the drawer, or Esc. The frame settles back into the drawer the way it rose. Esc again shuts the drawer; again, closes the view.

Reduced motion: every move becomes a cross-fade of about 160 ms; the drawer still follows a dragging finger, but it snaps instead of springing; no inertia when turning. Haptics: a 10 ms tick at the drawer's open and shut stops where `navigator.vibrate` exists (Android); never the only signal.

## Every drawer is its own entity

At launch these are Shopify metaobjects the founder edits in Shopify admin; until then `app/lib/mock/` serves the same shapes, seeded from `content/drawers/frames-wall.json`.

| Metaobject | Field | Type | What it does |
|---|---|---|---|
| `bay_wall` (handle `frames`) | `bays` | list of `drawer_bay` references | The drawers, in wall order |
| | `knob_style` | text, one of `black-relief`, `gold`, `plain` | Which wall render to use (O15) |
| | `render_set` | text | The asset set the wall was rendered as (`wall-v1`) |
| `drawer_bay` | `product` | product reference | The frame in this drawer |
| | `state` | text, one of `auto`, `available`, `coming_soon`, `sold_out`, `locked`, `hidden` | `auto` follows the drop and inventory; the rest override it |
| | `light` | text, one of `auto`, `lit`, `dark` | `auto`: lit while the drawer holds a frame you can see |
| | `note` | multi-line text | Internal; never rendered |

**How a drawer's state is resolved** (`app/lib/drawer/resolve.ts`, on the server, from the bay, the product, the drop and the time):

1. `hidden` stays hidden: a dark drawer, no label, not focusable.
2. `locked` stays locked: dark, `drawer.notYet`, does not open.
3. No product: hidden, and logged.
4. An override can never make a frame buyable that isn't: `available` on a product that isn't for sale resolves to `sold_out`.
5. `auto`: drop live and in stock → `available`; drop live or ended and not in stock → `sold_out`; drop announced, no drop or drop ended with stock → `coming_soon`.
6. The output: the state, the light, `canOpen`, `canLift` (assets present), the buy row, and the drop line with real values only. A missing value renders nothing.

Every case, and every missing-data case (no date, no quantity, no product, no assets, an unknown enum), has a unit test.

## Honesty and brand on this page

- `$100` is visible under every drawer except a hidden one, and in every view of a frame.
- The seam light, the buy row, the drop line and any number come from data. States the real data doesn't have (live, sold out, locked) appear only in tests, stories and the phone build's labelled fixture panel, never in a route.
- The frame's GCD executes one way only: the 3D models carry it at full size, proportion and placement (`frame3d.py`), and the export is checked against `content/products/` (D4). F08's renders show its GCD (the model carries it); its photographs don't (#34).
- The knob GCD is the `gcd-black` variant by default (O15). The only gold in any view is the frame's own GCD; the focus ring is the usual exception.
- Lenses in the renders and the 3D frames take each frame's measured tint (`assets/drawer-wall/lens-tints.json`, D4); F04 takes #38's values.
- Renders are matched to the photographs; the photographs stay one tap away and are never altered here beyond a resize.
- No analytics or third-party scripts. A local event log behind `?debug=1` serves the tests and the usability sessions.
- The film behind #43 is never named or shown: its title, its maker and the word FOOH join the CI string check.

## Not in this run

Every other page stays as built on Oct 30–31, in the earlier look, until it is redesigned (#43): the home page and the opening, the drop pages, the frame page `/frames/{handle}` (the drawer view links to it), manifesto, cast, the list, questions, care, policies, the bag, the header, the menu and the footer. This run changes `/frames` and adds what the wall needs to the shared code; no other page changes, and their visual baselines must not move. No checkout and no store connection.

## Open questions (mine to decide)

| # | Question | What the build does until then | Needed by |
|---|---|---|---|
| O15 | The GCD on the knobs: black relief, gold, or plain on the wall | Black relief; D3 renders a close-up of each variant for me | R1 |
| O16 | Tap first or pull first | Tap first on the route; pull first behind `?mech=pull` | After the usability test |
| O17 | A reshoot | No; the cleaned lightbox set | Before launch |
| O18 | Where testers open the phone build | A private Artifact link | R2 |
| — | The copy this run adds (`drawer.*` in `en.json`) | Drafts below, marked for sign-off | Launch |

---

# Part 2 · How it's built

## Order of authority

1. `CLAUDE.md` and `docs/brief/00-decisions.md`.
2. This file for this run. Where it departs from RUN.md or `09-build-plan.md`, this file wins.
3. RUN.md Part 2 for how a run operates (running unattended, orchestration, git and pull requests, PROGRESS.md, verification, edge cases, never), except where this file says otherwise.
4. `docs/brief/01`–`09` for detail; Part 1 above for intent.

## Where things stand (Nov 6 2026)

- **The app is built** (RUN.md phases 0–6, Oct 30–31, PRs #1–#9; `docs/build/PROGRESS.md` holds the record, the decision log and the questions). Hydrogen 2026.4.7, React 18.3, React Router 7.16, Tailwind 4, Storybook, Vitest, Playwright with axe (every story at 390 and 1440 in UI and wire mode against committed baselines; pixel comparisons run on the VM only, not on GitHub Actions, as PROGRESS.md explains), Lighthouse asserting 90 (`checks/lighthouse.mjs`), and `npm run checks` (banned strings, hex colors, product schema, copy gate, copy audit, layers, flash check). `npm run ci` runs them all in CI order.
- **What the wall reuses:** the mock store (`app/lib/mock/`: `createStore`, `effectiveState`, the drop and inventory `fixtures`), the cart (`app/lib/cart.tsx`) and `BagDrawer`, the copy accessor (`app/lib/copy.ts`), `PageShell`, `Header`, `Footer`, and the base components (`Button`, `Price`, `Sheet`, `ShotSlot` with its `sequence` variant, `Gallery` with its zoomed state, `VisuallyHidden`, `Notice`).
- **What `/frames` is today:** `app/routes/frames._index.tsx` → `app/components/pages/FramesPage.tsx`, the statement and eight `StageCard`s (1, 2, 4 and 4 across). `StageCard` stays: the home page and the drop pages use it. `/frames/{handle}` is the frame page (`FramePage.tsx`) and stays as it is.
- **Products, drops, copy, tokens, marks:** as RUN.md's "Where things stand" says; `en.json` has a `frames` section (`title`, `statement`).
- **The eight frames in 3D:** `tools/blender/frame3d.py` builds every frame (F01–F06, F08, F09) from its 1:1 drawings, with the GCD at full size on the wearer's right (`frame3d.gcd_parts`), materials from `materials_for()` (procedural acetate; a light-path lens shader that does not export to glTF as it is). `tools/blender/frame_texture.py` gives a tortoise front (F01, F02) its real pattern, read from its cleaned front shot in `work/out/`, which a fresh VM doesn't have (D0 checks how to rebuild it). Other sessions use these tools: add flags and functions, never change what they already produce.
- **The photographs:** 56 finals (`assets/photography/`, up to 2048 px) and their full-resolution stage masters (`dam/product/DS-{frame}-{angle}-v01-stage.png`, about 3700 × 4600 px).
- **The prototypes** (founder-reviewed, Nov 5 2026), in `docs/build/drawer-wall/prototype/`: `drawer_scene.py` (the single leather drawer; about 80 s a frame at 760 × 950 and 40 samples on 2 CPUs), `lift_scene.py` (the frame on black: the dark and lit pair), `grade.py` (the grade), `interaction/drawer.src.html` and `pull.src.html` (the touch prototypes; their placeholders were filled with base64 frames), `stills/`.
- **Research** behind the stack, the mechanics and the budgets: `docs/build/drawer-wall/research-2026-11-06.md`.
- **This VM:** about 4 CPUs and 16 GB per RUN.md; the planning workspace measured 2 CPUs and 7 GB. Cycles renders on the CPU. Size the render queue from D0's measurement, not from these numbers.

## Stack additions

Install the current stable versions in D1 and pin them in `package.json`. All MIT or Apache, all free.

| Package | Why |
|---|---|
| `three` | The live frame (WebGL 2, `AgXToneMapping` to match Blender's AgX) |
| `@react-three/fiber`, `@react-three/drei` | The lifted frame in React. The app is on React 18.3, so fiber v8 and the drei that goes with it |
| `@use-gesture/react` | Drag, pinch, wheel and the tap-or-drag decision |
| `@react-spring/web` | The drawer's settle and the lift |
| `@gltf-transform/cli` (dev) | GLB optimization: meshopt geometry, WebP textures (`EXT_texture_webp`). KTX2 only later, if phones show memory pressure |

No OpenSeadragon: the photo zoom is one full-resolution image per angle, which needs no tiles at these sizes. Tiles come at launch only if older iPhones run short of memory.

## Files this run adds

New, unless marked *(changed)*:

```
content/drawers/frames-wall.json         the seed of bay_wall + drawer_bay (product per bay, overrides)
content/drawers/wall.schema.json         (checked by npm run check:schema)
app/lib/drawer/resolve.ts                bay state from bay + product + drop + now (pure; tested)
app/lib/drawer/machine.ts                the per-drawer state machine (pure reducer; tested)
app/lib/drawer/manifest.ts               typed access to assets/drawer-wall/manifest.json
app/lib/drawer/gestures.ts               every threshold and spring in one place
app/lib/drawer/tier.ts                   capability tier (0, 1, 2)
app/lib/mock/                            (changed) the store gains bay_wall and drawer_bay in Storefront API shape
app/components/base/SequencePlayer.tsx   scrubbed image sequence on a canvas
app/components/base/Sheet.tsx            (changed) a `scene` variant: full screen, scroll-locked, no hard cut;
                                         the same focus trap, Esc and focus return
app/components/base/ShotSlot.tsx         (changed) a `model` variant for the live frame (wire-mode label)
app/components/base/Gallery.tsx          (changed) the zoomed state loads a full-resolution source when given one
app/components/house/drawer/             DrawerWall, DrawerBay, BayLabel, DrawerView, StageHint, BuyRow,
                                         LiftedFrame (lazy), with stories
app/components/pages/FramesPage.tsx      (changed) the statement and the wall instead of the stage cards
app/routes/frames._index.tsx             (changed) loads the wall; ?open={handle} opens that drawer
assets/drawer-wall/                      committed web outputs + manifest.json + manifest.schema.json
  wall/{layout}/{knob}/plate-lit.*, bay-NN-dark.*, rects.json
  seq/{frame}/NNN.{avif,webp} @720, @1200   camera/{open,inspect}.json   env/drawer.hdr
  glb/{frame}.glb   stills/{frame}-lifted.*   lens-tints.json
public/zoom/                             generated, git-ignored: full-resolution photo zoom images
checks/assets.mjs                        check:assets, added to npm run checks
checks/strings.mjs                       (changed) the film's title, its maker and FOOH join the list
tools/blender/drawer_wall.py             the cabinet, the drawer, the renders (+ --check)
tools/blender/frame_glb.py               a frame as a GLB ready to optimize (+ --check)
tools/blender/render_queue.py            resumable render jobs, one frame per job
tools/photo/grade_scene.py               the grade, from the prototype's grade.py
tools/photo/lens_tints.py                measured lens transmission per frame
tools/photo/zoom_export.py               stage masters → public/zoom/
tools/web3d/optimize.mjs                 gltf-transform: meshopt + WebP, budgets
phone/                                   the static phone build's entry (npm run phone:build → dist-phone/)
tests/unit/drawer-*.test.ts              resolver, machine, manifest, gestures, tier
tests/e2e/drawer.spec.ts                 the flows (touch, mouse, keyboard), in new Playwright projects
docs/build/drawer-wall/                  prototype/, research, usability.md, review/R1..R4, launch.md
```

`DrawerView` is the drawer's full-screen view (Part 1, steps 3–8), built on `Sheet`'s `scene` variant: one focus trap in the codebase, not two.

## The drawer's state machine

`app/lib/drawer/machine.ts`, a pure reducer, one instance per open drawer view.

| State | Events → next |
|---|---|
| `wall` | `OPEN` (tap, Enter, knob pull) → `entering` (only if `canOpen`) |
| `entering` | `ENTERED` → `shut` |
| `shut` | `DRAG(p)` → `pulling`; `OPEN_DRAWER` → `opening`; `CLOSE` → `leaving` |
| `pulling` | `DRAG(p)` → `pulling`; `RELEASE(v, p)` → `opening` or `shutting` |
| `opening` / `shutting` | `SETTLED` → `open` / `shut` |
| `open` | `DRAG(p)` → `pulling`; `LIFT` → `lifting` (only if `canLift`); `CLOSE` → `leaving` |
| `lifting` | `LIFTED` → `lifted` |
| `lifted` | `TURN`, `ZOOM`, `RESET` → `lifted`; `PHOTOS` → `photos`; `PUT_BACK` → `returning` |
| `photos` | `BACK` → `lifted` |
| `returning` | `RETURNED` → `open` |
| `leaving` | `LEFT` → `wall` (focus back on the drawer) |

Esc maps to the step back: `photos` → `lifted` → `open` → `shut` → `wall`. Pull first: `OPEN` carries the pointer, and once the view has entered the same drag continues as `DRAG(p)`, without a second touch. Every transition has a test; so does every impossible one (`LIFT` from `shut`, `OPEN` on a locked drawer).

## Interaction constants (`app/lib/drawer/gestures.ts`)

| Constant | Value | Note |
|---|---|---|
| Tap | under 8 px of movement and 400 ms | Longer presses do nothing |
| Wall drawers, tap first | `touch-action: pan-y` | The page always scrolls natively |
| Knob, pull first | `touch-action: none` on the knob's rect only, 44 × 44 px or more | The rest of the drawer scrolls |
| Drawer view | `touch-action: none`, `overscroll-behavior: contain`, iOS-safe scroll lock (fixed body, restored scroll position) | |
| Full pull | 45% of the view's height | Rubber band past the ends, at most 12 px |
| Release | velocity over 0.35 px/ms wins; otherwise position ≥ 0.5 opens | |
| Settle spring | stiffness 180, damping 26 | Reduced motion: snap plus a 160 ms cross-fade |
| Lift | spring to the inspect pose, about 900 ms | Reduced motion: 200 ms cross-fade |
| Turn | yaw 0.4°/px unbounded; pitch 0.25°/px, −30° to +35° | Inertia friction 0.92 a frame; none under reduced motion |
| Zoom | 1× to 3×, pinch direct, double-tap 1× ↔ 2.2× toward the tap, wheel 1.1× a step | |
| Hints | after 1.2 s idle in a state; gone after the first success of that gesture, for the session | One hint at a time; never animated beyond a slow fade |
| Haptics | `navigator.vibrate(10)` at the open and shut stops, where it exists | |

**Keyboard.** Each drawer is a `<button>` in wall order, named "{name}, $100. {drawer.openLabel}". In the drawer view (`role="dialog"`, `aria-modal`, labelled by the frame's name): ↓ and ↑ (and Page Down and Page Up) pull and push, Enter on the visible button lifts, ← → turn, ↑ ↓ tilt when lifted, + and − zoom, 0 resets, Esc steps back. **Screen readers:** a polite live region says `drawer.announce.*`; the live frame is `role="img"` with `drawer.model3dLabel` and the frame's `alt.subjects` text; the photographs carry their manifest alt text.

## Assets

### Principles

- **Commit what is expensive to make, generate what is cheap.** Renders and GLBs are committed as web-ready files with the manifest. Intermediates (EXR, 16-bit PNG, raw bakes) stay in `work/`, git-ignored. The zoom images regenerate from `dam/` in a minute, so they are generated, not committed.
- **One grade.** Every rendered image goes through `tools/photo/grade_scene.py` with the same settings; grain is seeded per output file, so a frame looks the same every time it's built.
- **Every asset in the manifest**, with its tool, its command, its source commit, its status (`prototype`, `mockup`, `final`) and its checks.
- **Scene black is exact.** The outermost 2% of every render and the room around the wall fall to within 1/255 of `surface-scene`. A check samples them.

### The wall (D3)

`tools/blender/drawer_wall.py wall --layout portrait|landscape --knob black-relief|gold|plain --variant lit|dark`. The prototype's drawer, multiplied: world-space grain, piping, the tilted knob with the knob GCD from `frame3d.gcd_parts` (materials per `--knob`), the rails, the seam light (a warm area light inside each drawer box plus the glow along its gaps for `lit`). Light: a broad soft source over the wall, a low warm rake from the left so the grain reads, a cool grey-green fill. Orthographic camera, 15° down.

Outputs per layout and knob style: `plate-lit` (the whole wall, every drawer lit), a `dark` crop per drawer cut from the all-dark render, and `rects.json` (each drawer's face, knob and label rects in % of the plate). Sizes: portrait 1170 px wide, landscape 2880 px. The plate is the page's LCP element: AVIF under 160 KB at 1170 px and under 380 KB at 2880 px, WebP fallback.

`--check`: rects match the geometry; the dark crops line up with the plate to the pixel; scene black at the edges; the knob GCD is 30 mm and present on every knob (or absent for `plain`).

### The drawer view (D3, D4)

`drawer_wall.py sequence --frames 24 [--frame F09 --region]`. The drawer slides from shut to 250 mm out over 24 frames, spaced more closely at both ends. The camera moves with it: it starts as the wall sees the drawer (15° down, a long lens, far back) and ends leaning in (about 40° down, about 68 mm, f/4, the focus following the drawer and then the frame), so the first frame continues the wall and the last looks into the drawer.

- **Base sequence** (D3): every frame without a frame in the drawer, 1200 × 1500 (4:5), 48 samples, denoised. Its last frame is also the empty drawer that sits behind the lifted frame.
- **Product sequences** (D4): for each frame, only the region where the drawer's interior is visible, from the frame where it first shows to the end, rendered with the frame in place (same seed and samples), then composited over the base with an 8 px feather. That is about a third of the pixels of a full render.
- `camera/open.json`: the last frame's camera (lens, sensor, resolution, position, rotation) and the frame's transform in the drawer, in Blender's Z-up and in three.js's Y-up, so the live frame starts exactly where the rendered one lies.
- `camera/inspect.json`: the lifted pose (camera and frame transform), shared by Blender (the lifted stills) and three.js (the live view).
- `env/drawer.hdr`: an equirectangular capture of the drawer scene's light from the lifted pose (Cycles panoramic camera, about 1024 × 512), the live frame's environment.
- Exports: 720 px and 1200 px wide, AVIF and WebP. Budget: under 45 KB a frame at 720 px, under 80 KB at 1200 px.

### The frames in 3D (D4)

`tools/blender/frame_glb.py F09 --out work/glb/F09.glb --check`, then `node tools/web3d/optimize.mjs`.

1. Build the frame with `frame3d` as the product views do, temples open, the GCD in place.
2. Triangulate and decimate to the budget while keeping the silhouette: 60k triangles to aim for, 100k at most. The GCD stays at full detail.
3. Materials for glTF: acetate as a clearcoat PBR material (roughness about 0.08, coat 1); procedural color (F01's and F02's tortoise; F02 from `frame_texture.py`) baked to a 2048 px texture on a fresh UV unwrap; metal as metallic; the lenses as a tinted, alpha-blended glossy material whose opacity is 1 minus the measured transmission (`lens-tints.json`; gradients as a texture); the GCD as two named materials, `gcd_gold` and `gcd_onyx`. Transmission (`KHR_materials_transmission`) is tried only after D0's spike shows the opacity version falls short, and only on tier 2.
4. Export GLB; optimize: meshopt geometry, WebP textures. Budget: 3 MB to aim for, 6 MB at most.
5. `--check`: triangle count; file size; the GCD meshes are present on the wearer's right, their length within 2% of the product's `gcd.lengthMm`, centred as `01-brand-system.md` says (within 0.5 mm); the front width within 1 mm of `measurementsMm.frontWidth`.

`tools/photo/lens_tints.py`: the median transmission of each lens, per channel, from the A1 stage master (lens sample boxes in a small JSON next to it, chosen by eye and committed), against the stage color. Recorded with its source in `lens-tints.json`; F04 uses #38's values. Lifted stills (`stills/{frame}-lifted.*`): each frame rendered at `inspect.json` in the drawer light: the poster while the GLB loads and the view for tier 1.

### The photographs (D4)

`tools/photo/zoom_export.py`: each frame's A1, A2, A3 and A6 stage masters, long side 4096 px at most, WebP quality 85, into `public/zoom/`, with alt text from `MANIFEST.csv`. Run by `npm run assets`, never committed.

### The render queue

`tools/blender/render_queue.py`: a jobs file in `work/queue/`, one job per frame, each job skipped when its output exists and verifies; runs at `nice -n 19` in the background, in chunks under 100 minutes; prints one line per finished job and one per failure. Size it from D0's timing. Rough order of magnitude on 4 CPUs: the walls under an hour, the base sequence about an hour, the eight product sequences two to three hours, stills and environment maps under half an hour. Commit and push the web outputs after every chunk: the VM can be reclaimed, and only pushed work survives.

## On the page

- **Tiers** (`app/lib/drawer/tier.ts`): tier 0 (no JS, or Save-Data): the wall as an image, each drawer a link to its frame page `/frames/{handle}`, which works without JS. Tier 1 (no WebGL 2, under 4 GB of device memory where reported, or a lost context): everything but the live frame; lifting shows the lifted still, and turning gives way to the photographs. Tier 2: everything.
- **SequencePlayer:** frames fetched as blobs (encoded, about 1 MB a drawer at 720 px); decoded `ImageBitmap`s kept only for the current frame ± 2 and closed otherwise; the next ones decoded ahead in the direction of travel; cross-fade between neighbours on a 2D canvas sized to the view at the device pixel ratio; AVIF where `createImageBitmap` takes it, WebP otherwise. The first and last frames load first.
- **Prefetch:** opening a drawer prefetches its product sequence, its GLB and the three.js chunk at idle priority. The three.js chunk is never in the initial bundle.
- **The handoff:** at lift, the canvas mounts over the drawer's last frame with the GLB at `open.json`'s transform and a soft contact shadow; the view cross-fades over 120 ms from the rendered frame (with the frame) to the empty drawer plus the live frame, then lifts. Until the GLB is ready, the lifted still holds the place.
- **The live frame:** one `<Canvas>`, `frameloop="demand"`, AgX tone mapping, the drawer HDR as its environment plus one warm key matched to the scene, disposed when the frame goes back. On `webglcontextlost`: tier 1 for the rest of the visit.
- **Deep links:** `/frames?open={handle}` opens the wall with that drawer's view open on its last frame, not lifted; an unknown handle opens nothing. `/frames/{handle}` stays the frame page.

## Copy (`en.json`, a new `drawer` section, status `draft`)

```
drawer.openLabel      Open the drawer.
drawer.notYet         Not yet.
drawer.hintPull       Pull it toward you
drawer.hintLift       Tap them to lift them out
drawer.hintTurn       Turn them. Pinch to come closer.
drawer.open           Open the drawer
drawer.shut           Shut the drawer
drawer.lift           Lift them out
drawer.putBack        Put them back
drawer.photos         See the photographs
drawer.photosClose    Back to the frame
drawer.framePage      Specs and drawings
drawer.turnLeft       Turn left
drawer.turnRight      Turn right
drawer.closer         Closer
drawer.further        Further
drawer.reset          Reset
drawer.model3dLabel   {subject}, a view you can turn
drawer.announce.open    {name}. The drawer is open.
drawer.announce.shut    The drawer is shut.
drawer.announce.lifted  {name}, lifted out.
drawer.announce.back    {name}, back in the drawer.
drawer.announce.added   {name} is in your bag.
```

Reuse what exists (`frames.title`, `frames.statement`, `nav.close`, `nav.bag`, `product.addToBag`, `product.soldOut`, `drop.states.*`, `alt.*`). Any other string you need goes in the same section as a draft and on PROGRESS.md's sign-off list. Never hard-code copy.

## Budgets

| What | Budget |
|---|---|
| LCP | ≤ 2.5 s, Lighthouse mobile on the review build; the wall plate is the LCP element |
| CLS | ≤ 0.1 (the plate and every rect have a fixed aspect) |
| INP | ≤ 200 ms; lab: TBT ≤ 200 ms; e2e measures input to next frame on open, pull and turn |
| Lighthouse mobile performance | ≥ 90 on `/frames` |
| Initial JS | ≤ 170 KB gzipped, no three.js |
| 3D chunk | ≤ 260 KB gzipped, after the first open only |
| Wall plate | AVIF ≤ 160 KB (1170 px), ≤ 380 KB (2880 px) |
| Sequence | ≤ 45 KB a frame at 720 px, ≤ 80 KB at 1200 px |
| GLB | ≤ 3 MB aimed, 6 MB hard; ≤ 60k triangles aimed, 100k hard; textures ≤ 2048 px |
| Environment map | ≤ 600 KB |
| Decoded frames held | ≤ 5 |
| Zoom image | ≤ 3 MB, loaded on request only |
| Frame rate | 60 fps pulling and turning on a mid-range phone; never under 30 in a Chromium trace at 4× CPU throttling |

`npm run check:assets` fails on any asset over budget, any manifest entry without its file, or any file without its manifest entry.

## Testing

- **Unit (Vitest):** `resolve.ts` (every state, override, missing value and the honesty guard), `machine.ts` (every transition and every impossible one), the manifest loader, the gesture math (release decisions, rubber band, clamps), the tier choice.
- **Stories:** every component and state at 390 and 1440, UI and wire, with mock data and the real assets (prototype stills while the renders are pending, marked `prototype` in the manifest); the existing Storybook suite picks them up and makes their baselines. WebGL stories are pixel-tested in wire mode only; in UI mode a smoke test checks the canvas drew.
- **End to end (Playwright, `tests/e2e/drawer.spec.ts`):** the `drawer-pixel` and `drawer-desktop` projects (Chromium) for everything; `drawer-iphone` (WebKit) for everything but the live 3D (headless WebKit's WebGL is not reliable). On GitHub Actions they run like the rest: everything asserted, screenshots recorded, not compared. Touch drags go through CDP `Input.dispatchTouchEvent` (Playwright's touchscreen only taps). The flows: the wall shows every drawer with its name and `$100`; tap first: open, pull, settle both ways, lift, turn (yaw changes), pinch (two-finger CDP), photographs, put back, shut, close with focus back on the drawer; pull first: a pull on the knob opens and keeps pulling, a swipe on the face scrolls the page; tap first: a vertical swipe on a drawer scrolls the page and opens nothing; keyboard only, end to end; reduced motion (no springs, cross-fades); WebGL disabled (tier 1); a deep link; no JS (tier 0).
- **Accessibility:** axe on the wall, the drawer view shut and open, the lifted frame and the photographs; names and live announcements; targets ≥ 44 px; 320 px and 200% zoom; label contrast measured against the plate's pixels under each label (≥ 4.5:1).
- **Performance:** Lighthouse on the review build; the bundle check; the frame-rate trace; decoded frames counted through the debug log.
- **Asset checks:** `drawer_wall.py --check`, `frame_glb.py --check` for every frame, `check:assets`, scene black, lens tints present with sources.
- **The CI string check:** RUN.md's list plus the film's title, its maker and FOOH, in `app/` and `content/copy/`.

## The phone preview

`npm run phone:build` builds `phone/` (the same components, the mock data, the real assets) into `dist-phone/` (git-ignored), static, with relative paths, `noindex`, and a panel labelled "Fixture states (example data)" that switches the drop between today's data, live, sold out and locked, plus the `?mech=` choice. It is a testing harness, not a route of the site.

- **Default: a private Artifact** (O18), published with its files (each publish takes up to 255 files; a version holds 511 files and 256 MB, so publish in two parts if needed). The artifact wraps the page in its own document skeleton: strip `<html>`, `<head>` and `<body>` from the built page and keep scripts as relative files. D0's spike says whether module scripts, GLB fetches and `createImageBitmap` work there.
- **Fallback: GitHub Pages** from a workflow, only after I say yes (it's public).
- Either way the link goes at the top of PROGRESS.md and in the PR.

## The usability test (I run it; you prepare it in D7)

`docs/build/drawer-wall/usability.md`: five people on their own phones (at least two iPhones and two Androids), 15 minutes each, thinking aloud, in person or on a video call with screen sharing. Half start with tap first, half with pull first; everyone tries both.

1. "Find a frame you like and look at it closely." (Do they find the drawer, the pull, the lift?)
2. "Show me the gold emblem up close."
3. "Put it back and look at another one."
4. "What does it cost?" (Is $100 seen without hunting?)
5. Free play, then three questions: what felt natural, what felt in the way, which version they'd keep.

Record per person: time to the first open, accidental opens, accidental scrolls, whether they lifted, turned, zoomed and opened the photographs, and their pick. The template has the table. The rule: the version with fewer misfires and a faster first open wins; a tie goes to tap first. `?debug=1` keeps a local event log the tester can copy at the end.

## Phases

One branch and one pull request per phase (`build/drawer-d0-start`, `build/drawer-d1-foundation`, …). Every phase ends with a review by agents that didn't build it, against `CLAUDE.md`, `00-decisions.md`, Part 1 and the phase's exit list; fix what they find, then show the exit evidence. Render chunks run in the background while code phases proceed; nothing waits on a render that it doesn't need.

**D0 · Start** (no pull request needed if nothing but PROGRESS.md changes)
- Read this file, RUN.md Part 2, `CLAUDE.md`, `00-decisions.md`, `01`, `04`, `05`, `06`, `08`. Add a "Drawer wall" section to `docs/build/PROGRESS.md` (the phase table, the render queue, the review gates, the usability results; questions and decisions go in its existing logs). The full-site record above it stays as it is.
- Check the environment: `bpy` 5.2.2, Node, npm, the Playwright browsers (`$PLAYWRIGHT_BROWSERS_PATH`), WebKit. Check what F01's and F02's tortoise needs: `frame_texture.py` reads their cleaned front shots from `work/out/`; find out whether `tools/photo/zipget.py` and `clean_lightbox.py` can rebuild them here, and if they can't, log it and take the pattern from the stage master in `dam/product/` registered the same way.
- **Spikes, each logged with numbers:** S1 F09 as a GLB with the material conversion, shown in three.js headless next to a Cycles still from the same camera (a side-by-side image and the mean difference); S2 a three-file test Artifact (a page, a JS module, a GLB, a WebP) if the session has the Artifact tool; S3 one drawer-view frame at final settings, seconds per frame, and the queue estimate from it; S4 a CDP touch drag in Chromium.
- **Exit:** the four spike results in PROGRESS.md.

**D1 · Additions to the foundation**
- The stack additions; the `surface-scene` role token (black) through `tools/palette.py`, with `text-primary` and `text-secondary` checked on it; the string check's additions; `checks/assets.mjs` in `npm run checks` (passing on an empty manifest); `npm run assets`; the new Playwright projects (`drawer-pixel`, Chromium as a Pixel with touch; `drawer-iphone`, WebKit as an iPhone; `drawer-desktop`), WebKit installed if the VM allows it (log it if not).
- **Exit:** `npm run ci` passing as it did on Oct 31, with nothing else changed.

**D2 · Data and logic**
- `content/drawers/frames-wall.json` and its schema (the eight frames in look-number order, every override `auto`); the metaobject mock; `resolve.ts`; `machine.ts`; `gestures.ts`; `tier.ts`; the manifest schema and loader; the `drawer` copy section.
- **Exit:** Vitest shows every resolver case, missing-data case and machine transition; the schemas validate in CI.

**D3 · The wall and the drawer** (Blender, mostly in the background)
- `drawer_wall.py`, `grade_scene.py`, `render_queue.py`. Lookdev on one drawer first, against the prototype stills, then the walls (both layouts; black relief for the route, plus one close-up of the knob in each knob style for O15), the base sequence, `open.json`, `inspect.json`, the environment map.
- **R1, my first look:** `docs/build/drawer-wall/review/R1/` (a contact sheet of both walls lit and dark, the view's frames 0, 8, 16 and 23, the three knob close-ups, one lifted still), linked in the PR, and as an Artifact if you can. Carry on; my answer comes as a PR comment.
- **Exit:** `drawer_wall.py --check` passing; budgets met; the R1 set published.

**D4 · The frames**
- The eight product sequences, `frame_glb.py` and `optimize.mjs` for every frame, `lens_tints.py`, the lifted stills, `zoom_export.py`.
- **Exit:** eight sequences and eight GLBs within budget; `frame_glb.py --check` passing for all eight (shown); `lens-tints.json` complete with sources; `check:assets` passing.

**D5 · Components**
- Base first, in one context (`SequencePlayer`, `Sheet`'s `scene` variant, `ShotSlot`'s `model` variant, `Gallery`'s full-resolution zoom), then the house components, fanned out: `DrawerWall`, `DrawerBay`, `BayLabel`, `DrawerView`, `StageHint`, `BuyRow`, `LiftedFrame`. Both mechanics. Every state in Storybook at 390 and 1440, UI and wire.
- **Exit:** the story list complete (one line per component and state in the PR); Vitest and the component tests green; axe clean on every story.

**D6 · The page**
- `FramesPage` renders the statement and the wall in place of the stage cards; the route loads the wall and honours `?open=`; Add to bag goes through the existing cart and `BagDrawer`; the tiers; the meta (`noindex` on review builds and the phone build); every end-to-end flow above.
- **Exit:** `npm run ci` green (the drawer projects included); visual baselines changed only for `/frames` and the new or changed stories, listed in the PR, every other page's baselines untouched; axe clean; `npm run lighthouse` passing, with LCP, CLS and TBT on `/frames` recorded against the budgets; the three.js chunk shown absent from the initial bundle.

**D7 · On a phone**
- The phone build (`npm run phone:build`) and its publication; `usability.md`; a real-device checklist for me (an iPhone and an Android: open, pull, lift, turn, pinch, photographs, rotate the phone, low-power mode, a weak connection).
- **R2, my second look:** the preview link at the top of PROGRESS.md and in the PR, with what to try. **Run 1 ends here.** Write "Now and next" so run 2 can start cold.
- **Exit:** the link works from a clean browser at 390 px (screenshots from it shown); PROGRESS.md complete for D0–D7; every D-phase PR merged.

**D8 · Feedback and realism** (run 2)
- Fold in my R1 and R2 comments and the usability results (R3); apply my answers to O15–O18 and record them in `00-decisions.md`, quoting me. Then the realism list, in this order, as far as it goes: the in-wall slide (each drawer moving a few centimetres in the wall render before its view opens, region renders per drawer and layout); the light and grade against my notes; the lens look; the knob style chosen; the transitions' timing.
- **R4:** a new preview and a short note on what changed.
- **Exit:** every R1–R3 item either done or written down with why not; the preview republished; checks green.

**D9 · Hand-off**
- `docs/build/drawer-wall/launch.md`: the metaobject definitions to create in Shopify admin (types, fields, validations, storefront access), how to change a drawer, how to add a frame (a bay record plus a render job), how to swap in a reshoot (O17) and a scanned leather, and what the store connection replaces in `app/lib/mock/`. Update RUN.md's "Where things stand" for the work this run did.
- **Exit:** the finishing checks below, shown.

## Running unattended

RUN.md's rules hold: don't stop between phases, my questions go to PROGRESS.md and the PR with the default in use, never weaken a check, commit and push at every milestone and at least every hour. In addition:

- **Renders** run in the background through the queue; watch them with a waiting command that exits when the chunk finishes, not with polling turns. Run Lighthouse and the frame-rate traces when no render chunk is running.
- **The review gates don't block.** R1 posts and carries on. R2 ends run 1.
- **Usage counts against my plan**, and ultracode multiplies it. Fan out only what is independent and worth it; keep mechanical stages on a smaller model. If the session stops for a limit, PROGRESS.md's "Now and next" must be enough to pick up cold.
- **Tools other sessions use** (`frame3d.py`, `frame_texture.py`, `gcd_render.py`, the photo tools): add flags and functions; never change what they already produce. Run their own checks after any change.

## Orchestration

- **One context, no fan-out:** D1's additions, `resolve.ts` and `machine.ts`, the base components of D5, the Blender lookdev (one eye on the look), the lift handoff.
- **Fan out:** D2's schema and mock against D3's tool writing; D5's house components after the base; D6's end-to-end suites by flow; each phase's reviews.
- **Brief every agent** with `CLAUDE.md`, `00-decisions.md` #43–#45 and O15–O18, Part 1 of this file, the parts of Part 2 its task touches, the paths of what exists and the files it owns. In a fan-out nobody touches `package.json`, shared config, tokens, `en.json`, the manifest or another agent's files.

## Risks and what to do

| Risk | Plan |
|---|---|
| CPU renders take too long | Region renders, 48 samples plus denoising, the queue in chunks; measure in D0; if the estimate passes 12 hours, render 720 px only for D7 and the 1200 px set in D8 |
| The live frame doesn't match the renders | The drawer's own HDR, AgX on both sides, the S1 comparison; tune the materials before D5's stories |
| Dark lenses look painted in real time | Opacity from measured transmission plus clearcoat-level gloss; transmission on tier 2 only if S1 says so |
| Drag fights scroll | Tap first by default; pull first only on the knob; the scroll tests |
| iOS Safari: scroll lock, `touch-action`, AVIF decode, WebGL context loss | The fixed-body lock; per-element `touch-action`; WebP fallback; tier 1 on context loss; WebKit in the e2e projects |
| Phone memory | Windowed decoding, one canvas, GLBs disposed, zoom images on request |
| Repo weight (public repo) | Web outputs only; budgets; zoom images generated, not committed |
| The preview host refuses something | S2 decides early; GitHub Pages only with my yes |
| The VM is reclaimed | Push after every render chunk; the queue resumes |
| The knobs break the GCD rules | O15's default (black relief) until I decide |

## Never

RUN.md's "Never" holds (no Shopify calls, no image or video generation, no paid tools, no font files, no invented facts, no Raf Simons or Prada in `app/` or copy, no copies of digs components, no hex in `app/`). In addition:

- No generated glasses, hands or people anywhere in this run; the frames come from `frame3d.py` and the photographs.
- No product photograph altered here beyond a resize.
- No GCD scaled, moved or left off a frame; no gold knob unless O15 says so.
- No state, number or date in a route that the data doesn't hold.
- No analytics or third-party scripts.
- The film behind #43: no title, maker or footage anywhere that ships.

## Finishing

**Run 1 (after D7):** `npm run ci` and `npm run lighthouse`, each shown; `git status` clean and pushed; a short report for me: what's built, the preview link, what to try on the phone, the questions for me.

**Run 2 (after D9):** the same checks plus the asset checks for every frame; RUN.md's "Where things stand" updated; a short report: what changed since R2, the decisions recorded, what's left before launch (O15–O18 if still open, copy sign-off, the store connection, fonts).

---

# Part 3 · Starting the run (for me)

1. **Environment.** In Claude Code on the web, on `FastCoempany/darkestshadeswebsite`: network access **Full** and the setup script from `09-build-plan.md` ("Workspace setup", step 2), as for RUN.md.
2. **A new session with Fable**, then `/effort ultracode`.
3. **Run 1:** send this as one message.

```
/goal Run docs/build/DRAWER-WALL.md phases D0 to D7. Done when docs/build/PROGRESS.md marks D0 to D7 done, each phase's exit evidence has been run and shown in this session (the command, its exit status and the output that matters), every D-phase pull request is merged into main, and the phone preview link and the R1 review set are at the top of PROGRESS.md. Hold CLAUDE.md, docs/brief/00-decisions.md and DRAWER-WALL.md throughout, and never weaken a check to get past it. Or stop after 300 turns.
```

4. **While it runs.** `/goal` on its own shows progress; `/goal clear` stops it. Answer R1 as a comment on the D3 pull request. When R2 arrives: open the link on my phone, run the usability test with five people (`docs/build/drawer-wall/usability.md`), and answer O15–O18 in a comment on the D7 pull request.
5. **Run 2:** a new session, `/effort ultracode`, then:

```
/goal Run docs/build/DRAWER-WALL.md phases D8 and D9 with my comments on the D-phase pull requests and the usability results in PROGRESS.md. Done when PROGRESS.md marks D8 and D9 done with their exit evidence run and shown in this session, the run 2 finishing checks have been run and shown passing, all work is merged into main and pushed, and the final report is written. Hold the same rules. Or stop after 200 turns.
```

If a session stops for my plan's usage limit, start it again later with the same `/goal`; PROGRESS.md carries the state. A rough expectation: run 1 takes a few days of wall-clock time, most of it render time in the background and waiting on usage limits; run 2 a day or two, depending on how much the feedback asks for.
