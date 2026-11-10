# Build run: the drawer wall

I'm Antaeus, the founder; where the docs say "the founder", that's me. This session builds **the drawer wall and nothing else**: the eight frames in a wall of drawers, photoreal and made for touch, good enough to put in people's hands on their phones. It is not a website. There are no pages, no header or footer, no menu, no bag and no checkout. It is built as one standalone piece in `wall/`, so that later it can go into a store as it is: every drawer is its own element with its own record, and the records are shaped like Shopify metaobjects.

The site build of Oct 30–31 was thrown out (`00-decisions.md` #46). Don't read it, reuse it or restore any of it. It sits on the `archive/site-build-2026-10-31` branch only so the history is complete.

Part 1 is what we're making. Part 2 is how to build it. Part 3 is for me: how I start the run. This file and `docs/build/WALL-PROGRESS.md` are your memory; re-read both at the start of every phase and after every break or compaction.

The decisions behind this run: `docs/brief/00-decisions.md` #43 (the look), #44 (the drawer wall), #45 (no added cost), #46 (the wall alone), #47 (no price on the wall) and #48 (the lifted frame turns freely), the founder's two instructions after D7, and the open items O15–O18, O20 and O21.

---

# Part 1 · What we're making

## In one paragraph

A dark room with one cabinet in it: a wall of identical drawers in black calfskin, one frame to a drawer. A thin warm light leaks from the seam of every drawer that holds a frame you can see. Under each drawer: its look number and its name; no price (#47). You tap a drawer and it comes forward; you pull it toward you and it slides out, the frame waiting inside in warm light; you tap the frame and it rises into the light, where it turns and comes closer under your finger. One more tap shows the real photographs at full resolution. You put it back, shut the drawer, and the wall is there again. Every drawer is its own thing: its own element, its own record, its own state. Nothing else is on the screen.

## The look (#43)

Private and intimate. Near-black; the scene is the image.

- **Light.** Cool grey-green outside (the cabinet, the room), warm amber inside (the drawer's interior, the light the frame waits in). Soft sources, never hard flash. Shallow focus in the drawer view. The gold of the frame's GCD is the only gold in any view.
- **Surface.** The prototype grade (`docs/build/drawer-wall/prototype/grade.py`): luminance-weighted film grain about 2.8%, a little halation on the brightest highlights, a soft vignette, a touch of lens softness, made in the image pipeline and identical on every asset. Never CSS filters.
- **Type.** It recedes. Lines in Stolzl Light (the Urbanist stand-in at 300), sentence case, 22 px and up. Labels and hints in Stolzl Medium micro: 11 px, uppercase, tracking +0.12em. No price (`00-decisions.md` #47). No headlines.
- **Controls.** Nearly invisible, never absent. Every gesture has a visible, quiet text button that does the same thing (WCAG 2.2 SC 2.5.1 and 2.5.7), in `text-secondary`, with the gold focus ring.
- **Where the pale stage appears.** Only in the photographs: the real lightbox pictures on their stage color, studied. Everything else sits on `surface-scene` (black).
- **Look references, in the repo:** `docs/build/drawer-wall/prototype/stills/` (the founder-reviewed drawer, shut, half and open; the lift pair, dark and lit). My private links, if your session can read Artifacts: the look mockups `https://claude.ai/artifact/FEiHsc3xekH5HhDXuVyVjv`, "pull toward you" `https://claude.ai/artifact/HNne2t63Vb3Ao3ekCGXqQj`, the leather drawer `https://claude.ai/artifact/8HTpadDkKaHgmoEXQ1SxUz`. The site pages in the look mockups are not part of this.

## The wall

- **The cabinet.** Black calfskin over every face: a fine irregular pebble grain, a coarser crease, a satin sheen with soft mottling, piped edges (a fine cord along the top and bottom of each drawer front). The grain is in world space, so no two drawers carry the same grain. The room around it is black.
- **A drawer.** Front about 220 × 122 mm. One knob, centered: blackened metal, about 46 mm across and 22 mm deep, its face tilted 28° up toward the person opening it. On the knob's face, the GCD as an ornament, 30 mm long: in black relief by default, metal and stone both black, so it reads by light, not color (O15). Inside: a warm brown-black suede lining; the frame sits on it upright, temples open, front toward you.
- **The seam light.** Each drawer has two looks. `lit`: a thin warm light escapes along its seams, because the drawer holds a frame you can look at. `dark`: no light, because the frame is sold out, locked or hidden. The light is state, never decoration, and never a promise the record doesn't make.
- **Layouts.** Two renders of the same cabinet. Portrait (narrower than 1024 px): 2 drawers across, 4 rows. Landscape (1024 px and wider): 4 across, 2 rows. Never a row of three (`06-products.md`: F04, F05 and F09). The drawers are identical; only the cabinet's proportions change: the rail under each row is deep enough for that drawer's label at its width. More drawers means a re-render of the wall, nothing else.
- **The camera.** Orthographic, tilted 15° down: the wall as you'd see it standing in front of a low cabinet, every drawer the same size, the knobs looking up at you.
- **Labels.** Under each drawer, on its rail, in HTML: the look number in camel micro, the name in micro `text-secondary` (wrapping, never truncated, at 320 px too). No price (#47). A sold-out drawer adds `wall.soldOut` under the name. A locked one shows `wall.notYet` in place of the name; its look number stays. A hidden one has no label.
- **Nothing else.** No logo, no navigation, no headline. The page's only heading is `wall.title`, visually hidden.

## One drawer, step by step

The default mechanic is **tap first** (O16). The **pull first** variant (`?mech=pull`) changes only step 2.

1. **The wall.** The wall scrolls normally where it is taller than the screen. Nothing moves on its own.
2. **Open.** Tap a drawer (anywhere on it, or Enter or Space). It comes forward: its part of the wall scales up into the drawer view while the room dims behind it, and the view's first frame, rendered from the wall's own angle, takes over. Pull-first variant: put a finger on the knob itself and pull down; the drawer view opens under your finger and the pull continues there. Anywhere else on the wall, a vertical swipe scrolls.
3. **The drawer view.** One full-screen layer; nothing behind it scrolls. The drawer, shut, barely lit; the hint `wall.hintPull` with a thin falling line. Pull down to slide the drawer out: a scrubbed image sequence, the camera leaning in and down as the drawer comes out, the frame coming into the warm light. Let go and the drawer settles open or shut (velocity first, then position). A quiet button does the same (`wall.open`, `wall.shut`). `wall.close`, Esc, or (on wide screens) a tap on the dim room around the view returns you to the wall, with focus on that drawer.
4. **Lift.** With the drawer open, the hint `wall.hintLift`. Tap the frame (or `wall.lift`). The rendered frame hands over to a live 3D frame in exactly the same place, then rises toward you into the light, turning to a three-quarter view, while the drawer dims and softens behind it.
5. **Turn and come closer.** One finger turns it about any axis, with no limit in any direction (#48): sideways, up and down, over, upside down, round and round; it follows the finger whichever way it already faces. It turns about its own centre, and it stays whole in the view: a turn that would carry its temples past the stage's edge moves it back inside by as much as there is room on the other side (at 1×; not once it is zoomed in, from 1.25×, when the zoom's own anchor holds). Pinch or double-tap brings it closer (to 3×); on desktop, drag and the wheel. Buttons: `wall.turnLeft`, `wall.turnRight`, `wall.tiltUp`, `wall.tiltDown`, `wall.closer`, `wall.further`, `wall.reset`. It stays sharp at every zoom because it is drawn live at the screen's resolution.
6. **The photographs.** `wall.photos` opens the real lightbox photographs (A1, A2, A3 and A6 where they exist) on their stage color, each at full resolution: pinch, drag or double-tap down to one image pixel per screen pixel. `wall.photosClose` goes back to the frame.
7. **Put back.** `wall.putBack`, a tap on the drawer, or Esc. The frame settles back into the drawer the way it rose. Esc again shuts the drawer; again, closes the view.

The name is on screen in the drawer view and the lifted view too; no price (#47). Reduced motion: every move becomes a cross-fade of about 160 ms; the drawer still follows a dragging finger, but it snaps instead of springing; turning has no inertia. Haptics: a 10 ms tick at the drawer's open and shut stops where `navigator.vibrate` exists (Android); never the only signal.

## Every drawer is its own thing

Two kinds of record, shaped like Shopify metaobjects (`{ id, handle, type, fields: [{ key, type, value, reference }] }`), so a store can hold them later and the founder can edit any drawer on its own in Shopify admin. Until then they live in `wall/data/wall.json`, read through one adapter (`wall/src/data/adapter.ts`).

| Record | Field | Type | What it does |
|---|---|---|---|
| `bay_wall` (handle `frames`) | `bays` | list of `drawer_bay` references | The drawers, in wall order |
| | `knob_style` | text, one of `black-relief`, `gold`, `plain` | Which wall render to use (O15) |
| | `render_set` | text | The asset set the wall was rendered as (`wall-v1`) |
| `drawer_bay` | `frame` | text, a frame id (`F09`), later a product reference | The frame in this drawer; its facts come from `content/products/` |
| | `state` | text, one of `available`, `sold_out`, `locked`, `hidden` | What the drawer does and says |
| | `light` | text, one of `auto`, `lit`, `dark` | `auto`: lit while the drawer holds a frame you can see |
| | `note` | multi-line text | Internal; never rendered |

**How a drawer's state is resolved** (`wall/src/lib/resolve.ts`, a pure function of the record and the frame's facts):

1. `hidden`: a dark drawer, no label, not focusable, doesn't open.
2. `locked`: dark, `wall.notYet` with the look number, doesn't open.
3. `sold_out`: dark, the name and `wall.soldOut`; it opens, and the frame can be seen, lifted and turned.
4. `available`: lit, the name; it opens.
5. No frame, an unknown frame id or an unknown value: hidden, and logged.
6. `light` overrides the seam light only; it never changes what a drawer does.
7. The output: the state, the light, `canOpen`, `canLift` (the assets exist), the label. A missing value renders nothing.

Every case, and every missing or unknown value, has a unit test. **The backend, simulated:** the phone build has a panel (`?panel=1`, labelled "Records (example data)") where I can change any drawer's record (its frame, state and light) and see that drawer, and only that drawer, change.

## Honesty and brand

- No price appears anywhere on the wall (`00-decisions.md` #47, Nov 9 2026). The frames' `price` in `content/products/` stays a product fact the wall does not ship.
- The seam light and every label come from the records. No countdowns, no quantities, no dates, no "only a few left": the wall shows none of them.
- The frame's GCD executes one way only: the 3D models carry it at full size, proportion and placement (`frame3d.py`), and the export is checked against `content/products/` (D4). F08's renders show its GCD (the model carries it); its photographs don't (#34).
- The knob GCD is the `gcd-black` variant by default (O15). The only gold in any view is the frame's own GCD; the focus ring is the usual exception.
- Lenses in the renders and the 3D frames take each frame's measured tint (`wall/assets/lens-tints.json`, D4); F04 takes #38's values.
- Renders are matched to the photographs; the photographs are one tap away and never altered here beyond a resize.
- No analytics and no third-party scripts. A local event log behind `?debug=1` serves the tests and the usability sessions.
- The film behind #43 is never named or shown: its title, its maker and the word FOOH are in the banned-strings check.

## Not in this run

Anything that isn't the wall: a website, pages, navigation, a header, a footer, a menu, a bag, a checkout, a store connection, an entry or opening, a sign-up. Nothing from the Oct 30–31 site build, in any form.

## Open questions (mine to decide)

| # | Question | What the build does until then | Needed by |
|---|---|---|---|
| O15 | The GCD on the knobs: black relief, gold, or plain | Black relief; D3 renders a close-up of each for me | R1 |
| O16 | Tap first or pull first | Tap first by default; pull first behind `?mech=pull` | After the usability test |
| O17 | A reshoot | No; the cleaned lightbox set | Before launch |
| O18 | Where testers open the phone build | A private Artifact link | R2 |
| — | The wall's copy (`wall.*` in `en.json`) | Drafts below, marked for sign-off | Launch |

---

# Part 2 · How it's built

## Order of authority

1. `CLAUDE.md` and `docs/brief/00-decisions.md`.
2. This file.
3. `docs/brief/01-brand-system.md`, `06-products.md`, `07-photography.md` and `08-copy.md` for detail; Part 1 above for intent. `03`, `04`, `05` and `09` describe a website and are parked (#46): don't build from them. Only `09`'s "Workspace setup" still applies.

## Where things stand (Nov 7 2026)

- **No wall code yet.** `wall/` doesn't exist; there's no `package.json` anywhere in the repo. D1 makes the project.
- **The site build is gone from `main`** (#46): no `app/`, no site tests, screenshots or tools. Its changes to the copy deck, the color tokens and their tools were undone; those files are as they were on Oct 28.
- **What the wall starts from:** the frames' facts (`content/products/*.json`: `id`, `handle`, `lookNumber`, `name`, `price`, `measurementsMm`, `gcd`, `lens`, …), the copy deck (`content/copy/en.json`; the wall gets its own `wall` section), the color tokens (`design/tokens/`, changed only through `tools/palette.py` and `tools/build_tokens.py`), the marks (`brand/`), the fonts' stand-ins (`brand/fonts/README.md`: Mona Sans and Urbanist from npm).
- **The eight frames in 3D:** `tools/blender/frame3d.py` builds every frame (F01–F06, F08, F09) from its 1:1 drawings, with the GCD at full size on the wearer's right (`frame3d.gcd_parts`), materials from `materials_for()` (procedural acetate; a light-path lens shader that does not export to glTF as it is). `tools/blender/frame_texture.py` gives a tortoise front (F01, F02) its real pattern, read from its cleaned front shot in `work/out/`, which a fresh VM doesn't have (D0 checks how to rebuild it). Other sessions use these tools: add flags and functions, never change what they already produce.
- **The photographs:** 56 finals (`assets/photography/`, up to 2048 px) and their full-resolution stage masters (`dam/product/DS-{frame}-{angle}-v01-stage.png`, about 3700 × 4600 px).
- **The prototypes** (founder-reviewed, Nov 5 2026), in `docs/build/drawer-wall/prototype/`: `drawer_scene.py` (the single leather drawer; about 80 s a frame at 760 × 950 and 40 samples on 2 CPUs), `lift_scene.py` (the frame on black: the dark and lit pair), `grade.py` (the grade), `interaction/drawer.src.html` and `pull.src.html` (the touch prototypes; their placeholders were filled with base64 frames), `stills/`.
- **Research** behind the stack, the mechanics and the budgets: `docs/build/drawer-wall/research-2026-11-06.md`.
- **This VM:** Claude Code's cloud VMs have had about 4 CPUs and 16 GB; the planning workspace measured 2 CPUs and 7 GB. Cycles renders on the CPU. Size the render queue from D0's measurement, not from these numbers.

## The stack

A small project of its own in `wall/`. Install current stable versions in D1 and pin them. All free, all MIT, BSD or Apache.

| Package | Why |
|---|---|
| `vite`, `typescript` | Dev server and the static build |
| `lit` | Custom elements: `<drawer-wall>`, `<drawer-bay>` and the rest. One element per drawer, each fed its own record. Custom elements go into anything later (a Hydrogen app, a Shopify theme section, a plain page) without bringing a framework along |
| `three` | The live frame (WebGL 2, `AgXToneMapping` to match Blender's AgX). No React layer |
| `@use-gesture/vanilla` | Drag, pinch, wheel and the tap-or-drag decision |
| `@fontsource-variable/mona-sans`, `@fontsource-variable/urbanist` | The type stand-ins, as `brand/fonts/README.md` says |
| `vitest` | Logic tests |
| `@playwright/test`, `@axe-core/playwright` | The flows, the screenshots, accessibility |
| `lighthouse` | Performance on the built wall |
| `@gltf-transform/cli` | GLB optimization: meshopt geometry, WebP textures (`EXT_texture_webp`). KTX2 only later, if phones show memory pressure |
| `ajv` | Schema checks for the records and the asset manifest |

The springs are a few lines in `wall/src/lib/spring.ts`, not a library. No OpenSeadragon: the photo zoom is one full-resolution image per angle, which needs no tiles at these sizes. Tiles come later only if older iPhones run short of memory.

## The project

```
wall/
  package.json  vite.config.ts  tsconfig.json  vitest.config.ts  playwright.config.ts
  index.html                 the wall, alone, full screen (?mech=pull, ?open=F09, ?panel=1, ?debug=1)
  states.html                every element in every state, side by side, from fixtures: the review and
                             screenshot sheet (the wall's stand-in for a component catalogue)
  src/
    elements/drawer-wall.ts    lays the drawers over the wall plate from the bay_wall record
    elements/drawer-bay.ts     one drawer: its record, its resolved state, its label, its dark crop, its events
    elements/drawer-view.ts    the full-screen drawer view: sequence, hints, buttons, lift, photographs
    elements/lifted-frame.ts   the live 3D frame (loaded on first open, three.js inside)
    elements/photo-zoom.ts     the photographs at full resolution: pinch, drag, double-tap, wheel, keys
    elements/records-panel.ts  the simulated backend (?panel=1)
    lib/resolve.ts  machine.ts  gestures.ts  spring.ts  tier.ts  sequence-player.ts
    lib/scroll-lock.ts  focus-trap.ts  copy.ts  log.ts
    data/adapter.ts            records in metaobject shape → typed drawers; JSON now, a store later
    styles/                    the tokens (design/tokens/build/*.css) and the wall's CSS, role tokens only
  data/
    wall.json  wall.schema.json   the bay_wall record and the eight drawer_bay records
  assets/                      committed web outputs + manifest.json + manifest.schema.json
    wall/{layout}/{knob}/plate-lit.*, bay-NN-dark.*, rects.json
    seq/{frame}/NNN.{avif,webp} @720, @1200   camera/{open,inspect}.json   env/drawer.hdr
    glb/{frame}.glb   stills/{frame}-lifted.*   lens-tints.json
  public/zoom/                 generated, git-ignored: the full-resolution photographs
  checks/                      strings.mjs  colors.mjs  schema.mjs  assets.mjs  lighthouse.mjs
  tests/unit/  tests/e2e/      (screenshot baselines next to the e2e specs)
tools/blender/drawer_wall.py   the cabinet, the drawer, the renders (+ --check)
tools/blender/frame_glb.py     a frame as a GLB ready to optimize (+ --check)
tools/blender/render_queue.py  resumable render jobs, one frame per job
tools/photo/grade_scene.py     the grade, from the prototype's grade.py
tools/photo/lens_tints.py      measured lens transmission per frame
tools/photo/zoom_export.py     stage masters → wall/public/zoom/
tools/web3d/optimize.mjs       gltf-transform: meshopt + WebP, budgets
docs/build/WALL-PROGRESS.md    the run's memory
docs/build/drawer-wall/        prototype/, research, usability.md, review/R1..R4, launch.md
```

`wall/package.json` scripts: `dev`, `build` (the static wall in `wall/dist/`, relative paths, `noindex`), `preview`, `test` (Vitest), `test:e2e` (Playwright), `check` (strings, colors, schema, assets), `lighthouse` (against the built wall; fails under 90), `assets` (the zoom export), and `all` (everything, in that order). Add each to `CLAUDE.md`'s commands when it exists.

## The drawer's state machine

`wall/src/lib/machine.ts`, a pure reducer, one instance per open drawer view.

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

Esc steps back: `photos` → `lifted` → `open` → `shut` → `wall`. Pull first: `OPEN` carries the pointer, and once the view has entered the same drag continues as `DRAG(p)`, without a second touch. Every transition has a test; so does every impossible one (`LIFT` from `shut`, `OPEN` on a locked drawer). A record changing while its drawer is open (the panel, later a store) closes the view only if the drawer can no longer open; otherwise the view stays and its label updates.

## Interaction constants (`wall/src/lib/gestures.ts`)

| Constant | Value | Note |
|---|---|---|
| Tap | under 8 px of movement and 400 ms | Longer presses do nothing |
| Drawers on the wall, tap first | `touch-action: pan-y` | The wall always scrolls natively |
| Knob, pull first | `touch-action: none` on the knob's rect only, 44 × 44 px or more | The rest of the drawer scrolls |
| Drawer view | `touch-action: none`, `overscroll-behavior: contain`, iOS-safe scroll lock (fixed body, restored scroll position) | |
| Full pull | 45% of the view's height | Rubber band past the ends, at most 12 px |
| Release | velocity over 0.35 px/ms wins; otherwise position ≥ 0.5 opens | |
| Settle spring | stiffness 180, damping 26 | Reduced motion: snap plus a 160 ms cross-fade |
| Lift | spring to the inspect pose, about 900 ms | Reduced motion: 200 ms cross-fade |
| Turn | 0.4°/px about the view's vertical for a sideways drag and about its horizontal for a vertical drag, composed in view space as a quaternion; no limit in any direction (#48); the pivot is the frame's own centre; the fit keeps the whole frame in the view at 1×, fading to none at 1.25×. The buttons step 9.6° (Turn left and right) and 8° (Tilt up and down), the keys 9.6° (← →) and 2° (↑ ↓) | Inertia friction 0.92 a frame; none under reduced motion |
| Zoom | 1× to 3×, pinch direct, double-tap 1× ↔ 2.2× toward the tap, wheel 1.1× a step | |
| Hints | after 1.2 s idle in a state; gone after the first success of that gesture, for the session | One hint at a time; never animated beyond a slow fade |
| Haptics | `navigator.vibrate(10)` at the open and shut stops, where it exists | |

**Keyboard.** Each drawer is a `<button>` in wall order, named "{name}. {wall.openLabel}" (a locked one: "{wall.notYet}"). In the drawer view (`role="dialog"`, `aria-modal`, labelled by the frame's name): ↓ and ↑ (and Page Down and Page Up) pull and push, Enter on the visible button lifts, ← → turn, ↑ ↓ tilt when lifted, + and − zoom, 0 resets, Esc steps back. **Screen readers:** a polite live region says `wall.announce.*`; the live frame is `role="img"` with `wall.model3dLabel` (the frame's `alt.subjects` text from the copy deck as `{subject}`); the photographs carry their manifest alt text from `assets/photography/MANIFEST.csv`.

## Assets

### Principles

- **Commit what is expensive to make, generate what is cheap.** Renders and GLBs are committed as web-ready files with the manifest. Intermediates (EXR, 16-bit PNG, raw bakes) stay in `work/`, git-ignored. The zoom images regenerate from `dam/` in a minute, so they are generated, not committed.
- **One grade.** Every rendered image goes through `tools/photo/grade_scene.py` with the same settings; grain is seeded per output file, so a frame looks the same every time it's built.
- **Every asset in the manifest** (`wall/assets/manifest.json`), with its tool, its command, its source commit, its status (`prototype`, `mockup`, `final`) and its checks. `states.html` shows each asset's status in a corner tag.
- **Scene black is exact.** The outermost 2% of every render and the room around the wall fall to within 1/255 of `surface-scene`. A check samples them.

### The wall (D3)

`tools/blender/drawer_wall.py wall --layout portrait|landscape --knob black-relief|gold|plain --variant lit|dark`. The prototype's drawer, multiplied: world-space grain, piping, the tilted knob with the knob GCD from `frame3d.gcd_parts` (materials per `--knob`), the rails, the seam light (a warm area light inside each drawer box plus the glow along its gaps for `lit`). Light: a broad soft source over the wall, a low warm rake from the left so the grain reads, a cool grey-green fill. Orthographic camera, 15° down.

Outputs per layout and knob style: `plate-lit` (the whole wall, every drawer lit), a `dark` crop per drawer cut from the all-dark render, and `rects.json` (each drawer's face, knob and label rects in % of the plate). Sizes: portrait 1170 px wide, landscape 2880 px. The plate is the page's LCP element: AVIF under 160 KB at 1170 px and under 380 KB at 2880 px, WebP fallback. Each `<drawer-bay>` sits over its rect and shows its own dark crop when its record says `dark`; the plate never changes.

`--check`: rects match the geometry; the dark crops line up with the plate to the pixel; scene black at the edges; the knob GCD is 30 mm and present on every knob (or absent for `plain`).

### The drawer view (D3, D4)

`drawer_wall.py sequence --frames 24 [--frame F09 --region]`. The drawer slides from shut to 250 mm out over 24 frames, spaced more closely at both ends. The camera moves with it: it starts as the wall sees the drawer (15° down, a long lens, far back) and ends leaning in (about 40° down, about 68 mm, f/4, the focus following the drawer and then the frame), so the first frame continues the wall and the last looks into the drawer.

- **Base sequence** (D3): every frame without a frame in the drawer, 1200 × 1500 (4:5), 48 samples, denoised. Its last frame is also the empty drawer that sits behind the lifted frame.
- **Frame sequences** (D4): for each frame, only the region where the drawer's interior is visible, from the frame where it first shows to the end, rendered with the frame in place (same seed and samples), then composited over the base with an 8 px feather. That is about a third of the pixels of a full render.
- `camera/open.json`: the last frame's camera (lens, sensor, resolution, position, rotation) and the frame's transform in the drawer, in Blender's Z-up and in three.js's Y-up, so the live frame starts exactly where the rendered one lies.
- `camera/inspect.json`: the lifted pose (camera and frame transform), shared by Blender (the lifted stills) and three.js (the live view).
- `env/drawer.hdr`: an equirectangular capture of the drawer scene's light from the lifted pose (Cycles panoramic camera, about 1024 × 512), the live frame's environment.
- Exports: 720 px and 1200 px wide, AVIF and WebP. Budget: under 45 KB a frame at 720 px, under 80 KB at 1200 px.

### The frames in 3D (D4)

`tools/blender/frame_glb.py F09 --out work/glb/F09.glb --check`, then `node tools/web3d/optimize.mjs`.

1. Build the frame with `frame3d` as the product views do, temples open, the GCD in place.
2. Triangulate and decimate to the budget while keeping the silhouette: 60k triangles to aim for, 100k at most. The GCD stays at full detail.
3. Materials for glTF: acetate as a clearcoat PBR material (roughness about 0.08, coat 1); procedural color (F01's and F02's tortoise) baked to a 2048 px texture on a fresh UV unwrap; metal as metallic; the lenses as a tinted, alpha-blended glossy material whose opacity is 1 minus the measured transmission (`lens-tints.json`; gradients as a texture); the GCD as two named materials, `gcd_gold` and `gcd_onyx`. Transmission (`KHR_materials_transmission`) is tried only after D0's spike shows the opacity version falls short, and only on tier 2.
4. Export GLB; optimize: meshopt geometry, WebP textures. Budget: 3 MB to aim for, 6 MB at most.
5. `--check`: triangle count; file size; the GCD meshes are present on the wearer's right, their length within 2% of the frame's `gcd.lengthMm`, centred as `01-brand-system.md` says (within 0.5 mm); the front width within 1 mm of `measurementsMm.frontWidth`.

`tools/photo/lens_tints.py`: the median transmission of each lens, per channel, from the A1 stage master (lens sample boxes in a small JSON next to it, chosen by eye and committed), against the stage color. Recorded with its source in `lens-tints.json`; F04 uses #38's values. Lifted stills (`stills/{frame}-lifted.*`): each frame rendered at `inspect.json` in the drawer light: the poster while the GLB loads and the view for tier 1.

### The photographs (D4)

`tools/photo/zoom_export.py`: each frame's A1, A2, A3 and A6 stage masters, long side 4096 px at most, WebP quality 85, into `wall/public/zoom/`, with alt text from `MANIFEST.csv`. Run by `npm run assets`, never committed.

### The render queue

`tools/blender/render_queue.py`: a jobs file in `work/queue/`, one job per frame, each job skipped when its output exists and verifies; runs at `nice -n 19` in the background, in chunks under 100 minutes; prints one line per finished job and one per failure. Size it from D0's timing. Rough order of magnitude on 4 CPUs: the walls under an hour, the base sequence about an hour, the eight frame sequences two to three hours, stills and environment maps under half an hour. Commit and push the web outputs after every chunk: the VM can be reclaimed, and only pushed work survives.

## In the browser

- **Tiers** (`wall/src/lib/tier.ts`): tier 0 (no JavaScript): a `<noscript>` with the wall plate and a plain list of the eight drawers (look number, name; no price), each linking to its A1 photograph. Tier 1 (no WebGL 2, under 4 GB of device memory where reported, Save-Data, or a lost context): everything but the live frame; lifting shows the lifted still, and turning gives way to the photographs. Tier 2: everything.
- **The sequence player:** frames fetched as blobs (encoded, about 1 MB a drawer at 720 px); decoded `ImageBitmap`s kept only for the current frame ± 2 and closed otherwise; the next ones decoded ahead in the direction of travel; cross-fade between neighbours on a 2D canvas sized to the view at the device pixel ratio; AVIF where `createImageBitmap` takes it, WebP otherwise. The first and last frames load first.
- **Prefetch:** opening a drawer prefetches its frame sequence, its GLB and the three.js chunk at idle priority. three.js is never in the initial bundle.
- **The handoff:** at lift, the canvas mounts over the drawer's last frame with the GLB at `open.json`'s transform and a soft contact shadow; the view cross-fades over 120 ms from the rendered frame (with the frame in it) to the empty drawer plus the live frame, then lifts. Until the GLB is ready, the lifted still holds the place.
- **The live frame:** one canvas for the whole wall, rendered only while something changes, AgX tone mapping, the drawer HDR as its environment plus one warm key matched to the scene, disposed when the frame goes back. On `webglcontextlost`: tier 1 for the rest of the visit.
- **Deep link:** `?open=F09` (a frame id or handle) opens that drawer's view on its last frame, not lifted; an unknown value opens nothing.

## Copy (`content/copy/en.json`, a new `wall` section, status `draft`)

```
wall.title              The frames
wall.openLabel          Open the drawer.
wall.notYet             Not yet.
wall.soldOut            Sold out
wall.hintPull           Pull it toward you
wall.hintLift           Tap them to lift them out
wall.hintTurn           Turn them. Pinch to come closer.
wall.open               Open the drawer
wall.shut               Shut the drawer
wall.close              Close
wall.lift               Lift them out
wall.putBack            Put them back
wall.photos             See the photographs
wall.photosClose        Back to the frame
wall.turnLeft           Turn left
wall.turnRight          Turn right
wall.tiltUp             Tilt up
wall.tiltDown           Tilt down
wall.closer             Closer
wall.further            Further
wall.reset              Reset
wall.model3dLabel       {subject}, a view you can turn
wall.announce.open      {name}. The drawer is open.
wall.announce.shut      The drawer is shut.
wall.announce.lifted    {name}, lifted out.
wall.announce.back      {name}, back in the drawer.
```

Names and look numbers come from `content/products/` (never the price, #47); the frames' alt text from the copy deck's `alt` section. Any other string the wall needs goes in the `wall` section as a draft and on WALL-PROGRESS.md's sign-off list. No string is hard-coded in `wall/src/`.

## Budgets

| What | Budget |
|---|---|
| LCP | ≤ 2.5 s, Lighthouse mobile on the built wall; the wall plate is the LCP element |
| CLS | ≤ 0.1 (the plate and every rect have a fixed aspect) |
| INP | ≤ 200 ms; lab: TBT ≤ 200 ms; e2e measures input to next frame on open, pull and turn |
| Lighthouse mobile performance | ≥ 90 |
| Initial JS | ≤ 60 KB gzipped, no three.js |
| 3D chunk | ≤ 200 KB gzipped, after the first open only |
| Wall plate | AVIF ≤ 160 KB (1170 px), ≤ 380 KB (2880 px) |
| Sequence | ≤ 45 KB a frame at 720 px, ≤ 80 KB at 1200 px |
| GLB | ≤ 3 MB aimed, 6 MB hard; ≤ 60k triangles aimed, 100k hard; textures ≤ 2048 px |
| Environment map | ≤ 600 KB |
| Decoded frames held | ≤ 5 |
| Zoom image | ≤ 3 MB, loaded on request only |
| Frame rate | 60 fps pulling and turning on a mid-range phone; never under 30 in a Chromium trace at 4× CPU throttling |

`npm run check` fails on any asset over budget, any manifest entry without its file, or any file without its manifest entry.

## Testing

- **Unit (Vitest):** `resolve.ts` (every state, every override, every missing or unknown value), `machine.ts` (every transition and every impossible one, records changing mid-view), the adapter (metaobject shape in, typed drawers out), the manifest loader, the gesture math (release decisions, rubber band, clamps), the tier choice.
- **The states sheet:** `states.html` shows every element in every state (each drawer state, both lights, both mechanics, the view shut, pulling, open, lifted, turned, zoomed, the photographs, tier 1, reduced motion, 320 px) from fixtures. Playwright screenshots it at 390 and 1440 against committed baselines; the live canvas is masked in the pixel comparison, and a separate test checks that it drew.
- **End to end (Playwright, `wall/tests/e2e/`):** projects `wall-pixel` (Chromium as a Pixel, with touch), `wall-iphone` (WebKit as an iPhone; everything but the live 3D, since headless WebKit's WebGL is not reliable) and `wall-desktop` (Chromium). Touch drags go through CDP `Input.dispatchTouchEvent` (Playwright's touchscreen only taps). The flows: every drawer shows its name and no price; tap first: open, pull, settle both ways, lift, turn (the quaternion changes after Turn right, Tilt up and a drag, and the live frame holds it and has drawn it; on the Pixel two 300 px drags down take it past the old clamp and on round; stood on end its whole box is in the view; at 3× the turn keeps its centre), pinch (two-finger CDP), photographs, put back, shut, close with focus back on the drawer; pull first: a pull on the knob opens and keeps pulling, a swipe on the face scrolls; tap first: a vertical swipe on a drawer scrolls and opens nothing; keyboard only, end to end; reduced motion (no springs, cross-fades); WebGL disabled (tier 1); `?open=`; no JavaScript (tier 0); the records panel changes one drawer and no other.
- **Performance (`perf.spec.ts`):** three.js absent from the initial bundle; at most 5 decoded frames held through a pull; input to the frame after the next on open, pull and turn; the frame rate pulling and turning from the animation-frame gaps at the machine's speed (asserted) and at 4× CPU throttling (recorded). The turn draws the live frame through WebGL, so where the browser presents WebGL through a software renderer (SwiftShader on this VM and on a CI runner, 80 ms or more a frame whatever the canvas) the turn's gaps and latency are recorded, not asserted, and the wall's own share is asserted everywhere: the main thread's time in each pointer event's handlers and in each draw, one draw per event (#48's review).
- **Accessibility:** axe on the wall, the drawer view shut and open, the lifted frame and the photographs; names and live announcements; targets ≥ 44 px; 320 px and 200% zoom; label contrast measured against the plate's pixels under each label (≥ 4.5:1).
- **Performance:** `npm run lighthouse` on the built wall; the bundle sizes; the frame-rate trace; decoded frames counted through the debug log.
- **Asset checks:** `drawer_wall.py --check`, `frame_glb.py --check` for every frame, the manifest check, scene black, lens tints present with sources.
- **The banned-strings check** (`wall/checks/strings.mjs`, over `wall/src/`, `wall/index.html`, `wall/states.html`, `wall/data/` and the copy deck's `wall` section): Raf Simons, Prada, the film's title, its maker and FOOH. **The colors check:** no hex, `rgb()` or named colors in `wall/src/`; role tokens only.

## On a phone

`npm run build` makes `wall/dist/`: static, relative paths, `noindex`, everything the wall needs. With `?panel=1` the records panel opens (Part 1); the `?mech=` choice sits in it too.

- **Default: a private Artifact** (O18), published with its files (each publish takes up to 255 files; a version holds 511 files and 256 MB, so publish in two parts if needed). The Artifact wraps the page in its own document skeleton: strip `<html>`, `<head>` and `<body>` from the built `index.html` and keep scripts and assets as relative files. D0's spike says whether module scripts, GLB fetches and `createImageBitmap` work there.
- **Fallback: GitHub Pages** from a workflow, only after I say yes (it's public).
- Either way the link goes at the top of WALL-PROGRESS.md and in the PR.

## The usability test (I run it; you prepare it in D7)

`docs/build/drawer-wall/usability.md`: five people on their own phones (at least two iPhones and two Androids), 15 minutes each, thinking aloud, in person or on a video call with screen sharing. Half start with tap first, half with pull first; everyone tries both.

1. "Find a frame you like and look at it closely." (Do they find the drawer, the pull, the lift?)
2. "Show me the gold emblem up close."
3. "Put it back and look at another one."
4. Free play, then three questions: what felt natural, what felt in the way, which version they'd keep.

Record per person: time to the first open, accidental opens, accidental scrolls, whether they lifted, turned, zoomed and opened the photographs, and their pick. The template has the table. The rule: the version with fewer misfires and a faster first open wins; a tie goes to tap first. `?debug=1` keeps a local event log the tester can copy at the end.

## Phases

One branch and one pull request per phase (`wall/d0-start`, `wall/d1-project`, …). Every phase ends with a review by agents that didn't build it, against `CLAUDE.md`, `00-decisions.md`, Part 1 and the phase's exit list; fix what they find, then show the exit evidence. Render chunks run in the background while code phases proceed; nothing waits on a render it doesn't need.

**D0 · Start** (no pull request needed if nothing but WALL-PROGRESS.md changes)
- Read this file, `CLAUDE.md`, `00-decisions.md`, `01`, `06`, `07`, `08`. Create `docs/build/WALL-PROGRESS.md` (the layout below).
- Check the environment: `bpy` 5.2.2, Node 22, npm, the Playwright browsers (`$PLAYWRIGHT_BROWSERS_PATH`), WebKit. Install what's missing: the packages in `09-build-plan.md`'s setup script now, WebKit in D1 at the pinned Playwright version. Check what F01's and F02's tortoise needs: `frame_texture.py` reads their cleaned front shots from `work/out/`; find out whether `tools/photo/zipget.py` and `clean_lightbox.py` can rebuild them here, and if they can't, log it and take the pattern from the stage master in `dam/product/`, registered the same way.
- **Spikes, each logged with numbers:** S1 F09 as a GLB with the material conversion, shown in three.js headless next to a Cycles still from the same camera (a side-by-side image and the mean difference); S2 a three-file test Artifact (a page, a JS module, a GLB, a WebP) if the session has the Artifact tool; S3 one drawer-view frame at final settings, seconds per frame, and the queue estimate from it; S4 a CDP touch drag in Chromium.
- **Exit:** the four spike results in WALL-PROGRESS.md.

**D1 · The project**
- `wall/` with the stack above, its scripts, its checks and its Playwright projects; the `surface-scene` role token (black) through `tools/palette.py`, with `text-primary` and `text-secondary` checked on it, and `python3 tools/build_tokens.py`; the fonts' stand-ins; `index.html` and `states.html` showing labelled placeholders where the wall will be; a GitHub Actions workflow running `npm run all` without pixel comparisons, if the token can push workflows (log it if it can't).
- **Exit:** `npm run all` passing on the empty project; screenshots of both pages at 390 and 1440 shown.

**D2 · Records and logic**
- `wall/data/wall.json` and its schema (the eight frames in look-number order, every drawer `available`, `light: auto`); the adapter; `resolve.ts`; `machine.ts`; `gestures.ts`; `spring.ts`; `tier.ts`; the manifest schema and loader; the `wall` copy section.
- **Exit:** Vitest shows every resolver case, missing value and machine transition; the schemas validate in `npm run check`.

**D3 · The wall and the drawer** (Blender, mostly in the background)
- `drawer_wall.py`, `grade_scene.py`, `render_queue.py`. Lookdev on one drawer first, against the prototype stills, then the walls (both layouts; black relief, plus one close-up of the knob in each knob style for O15), the base sequence, `open.json`, `inspect.json`, the environment map.
- **R1, my first look:** `docs/build/drawer-wall/review/R1/` (a contact sheet of both walls lit and dark, the view's frames 0, 8, 16 and 23, the three knob close-ups, one lifted still), linked in the PR, and as an Artifact if you can. Carry on; my answer comes as a PR comment.
- **Exit:** `drawer_wall.py --check` passing; budgets met; the R1 set published.

**D4 · The frames**
- The eight frame sequences, `frame_glb.py` and `optimize.mjs` for every frame, `lens_tints.py`, the lifted stills, `zoom_export.py`.
- **Exit:** eight sequences and eight GLBs within budget; `frame_glb.py --check` passing for all eight (shown); `lens-tints.json` complete with sources; `npm run check` passing.

**D5 · The elements**
- The shared pieces first, in one context (`sequence-player.ts`, `scroll-lock.ts`, `focus-trap.ts`, `copy.ts`), then the elements, fanned out: `drawer-wall`, `drawer-bay`, `drawer-view`, `lifted-frame`, `photo-zoom`, `records-panel`. Both mechanics. `states.html` complete.
- **Exit:** every state on `states.html` at 390 and 1440 against new baselines (the list in the PR); Vitest green; axe clean on the sheet.

**D6 · The wall, together**
- `index.html` runs the whole experience from the records: the tiers, `?open=`, `?mech=`, `?panel=1`, `?debug=1`; every end-to-end flow above.
- **Exit:** `npm run all` green, the three Playwright projects included; axe clean; `npm run lighthouse` passing, with LCP, CLS and TBT recorded against the budgets; three.js shown absent from the initial bundle.

**D7 · On a phone**
- `npm run build` and its publication; `usability.md`; a real-device checklist for me (an iPhone and an Android: open, pull, lift, turn, pinch, photographs, the records panel, rotate the phone, low-power mode, a weak connection).
- **R2, my second look:** the link at the top of WALL-PROGRESS.md and in the PR, with what to try. **Run 1 ends here.** Write "Now and next" so run 2 can start cold.
- **Exit:** the link works from a clean browser at 390 px (screenshots from it shown); WALL-PROGRESS.md complete for D0–D7; every D-phase PR merged.

**D8 · Feedback and realism** (run 2)
- Fold in my R1 and R2 comments and the usability results (R3); apply my answers to O15–O18 and record them in `00-decisions.md`, quoting me. Then the realism list, in this order, as far as it goes: the in-wall slide (each drawer moving a few centimetres in the wall render before its view opens, region renders per drawer and layout); the light and grade against my notes; the lens look; the knob style chosen; the transitions' timing.
- **R4:** a new link and a short note on what changed.
- **Exit:** every R1–R3 item either done or written down with why not; the link republished; checks green.

**D9 · Hand-off**
- `docs/build/drawer-wall/launch.md`: how the wall goes into a store later, written for whoever does it: the metaobject definitions to create in Shopify admin (`bay_wall`, `drawer_bay`: fields, validations, storefront access); how the adapter switches from `wall.json` to the Storefront API; placing `<drawer-wall>` in a Hydrogen app or in a Shopify theme section; how to change a drawer, add a frame (a record plus a render job), swap in a reshoot (O17) or a scanned leather, and load the real fonts.
- **Exit:** the finishing checks below, shown.

## WALL-PROGRESS.md

Sections, in this order: **Checks failing for environment reasons** (each with its reason; never silently skipped); **Phases** (D0–D9: state, branch and PR, evidence, date); **Now and next**; **Render queue** (done, running, left, time per frame); **Review gates** (R1–R4: when, where, my answers); **Usability results**; **Decision log** (date, decision, why, phase); **Questions for Antaeus** (the question, the default in use, where it came up); **Copy for sign-off**.

## Running unattended

- **Don't stop between phases**, and don't wait for me. A question goes to WALL-PROGRESS.md and the PR with the default in use, and the work carries on.
- **Never weaken a check to pass it.** A check that can't pass here for an environment reason is logged with the reason before the phase is called done.
- **Evidence** is the command, its exit status and the output that matters, shown in the session.
- **Commit and push** at every milestone and at least every hour; after every render chunk. Never force-push `main`. Commit messages end with the attribution lines the session's system reminder gives.
- **Renders** run in the background through the queue; watch them with a waiting command that exits when the chunk finishes, not with polling turns. Run Lighthouse and the frame-rate traces when no render chunk is running.
- **The review gates don't block.** R1 posts and carries on. R2 ends run 1.
- **Usage counts against my plan**, and ultracode multiplies it. Fan out only what is independent and worth it; keep mechanical stages on a smaller model. If the session stops for a limit, "Now and next" must be enough to pick up cold.
- **Tools other sessions use** (`frame3d.py`, `frame_texture.py`, `gcd_render.py`, the photo tools): add flags and functions; never change what they already produce.
- **Pull requests:** one per phase, merged by you once its checks pass and its review is done; my comments arrive on them, read them through the GitHub API.

## Orchestration

- **One context, no fan-out:** D1's project, `resolve.ts` and `machine.ts`, D5's shared pieces, the Blender lookdev (one eye on the look), the lift handoff.
- **Fan out:** D2's schema and adapter against D3's tool writing; D5's elements after the shared pieces; D6's end-to-end suites by flow; each phase's reviews.
- **Brief every agent** with `CLAUDE.md`, `00-decisions.md` #43–#48, O15–O18, O20 and O21, Part 1 of this file, the parts of Part 2 its task touches, the paths of what exists and the files it owns. In a fan-out nobody touches `package.json`, shared config, the tokens, the copy deck, the manifest or another agent's files.

## Risks and what to do

| Risk | Plan |
|---|---|
| CPU renders take too long | Region renders, 48 samples plus denoising, the queue in chunks; measure in D0; if the estimate passes 12 hours, render 720 px only for D7 and the 1200 px set in D8 |
| The live frame doesn't match the renders | The drawer's own HDR, AgX on both sides, the S1 comparison; tune the materials before D5 |
| Dark lenses look painted in real time | Opacity from measured transmission plus clearcoat-level gloss; transmission on tier 2 only if S1 says so |
| Drag fights scroll | Tap first by default; pull first only on the knob; the scroll tests |
| iOS Safari: scroll lock, `touch-action`, AVIF decode, WebGL context loss | The fixed-body lock; per-element `touch-action`; WebP fallback; tier 1 on context loss; WebKit in the e2e projects |
| Phone memory | Windowed decoding, one canvas, GLBs disposed, zoom images on request |
| Repo weight (public repo) | Web outputs only; budgets; zoom images generated, not committed |
| The phone link's host refuses something | S2 decides early; GitHub Pages only with my yes |
| The VM is reclaimed | Push after every render chunk; the queue resumes |
| The knobs break the GCD rules | O15's default (black relief) until I decide |
| Drifting into a website | Part 1's "Not in this run"; every review checks for it |

## Never

- Nothing that isn't the wall: no pages, routes, navigation, header, footer, menu, bag, checkout, sign-up or entry.
- Nothing from the Oct 30–31 site build: no code, components, tests, screenshots, copy, tokens or tools from the archive branch, and no pattern copied from it.
- No live Shopify calls; no image or video generation; no generated glasses, hands or people; no paid tools; no font files committed.
- No invented facts: every fact about a frame comes from `content/products/`.
- No Raf Simons, Prada or the film behind #43 anywhere that ships.
- No product photograph altered beyond a resize; no GCD scaled, moved or left off a frame; no gold knob unless O15 says so.
- No state, number or date the records don't hold; no analytics or third-party scripts; no hex colors in `wall/src/`.

## Finishing

**Run 1 (after D7):** `npm run all` and `npm run lighthouse`, each shown; `git status` clean and pushed; a short report for me: what's built, the link, what to try on the phone, the questions for me.

**Run 2 (after D9):** the same checks plus the asset checks for every frame; a short report: what changed since R2, the decisions recorded, what's left before the wall can go into a store (O15–O18 if still open, copy sign-off, the fonts).

---

# Part 3 · Starting the run (for me)

From the **Code** tab of the Claude app, on the phone or the desktop, or at claude.ai/code. The session runs in the cloud, so my computer can be off.

1. **Network access Full** on the environment the session runs in (its name is under the session title): the menu on the title, then **Edit cloud environment**. A running session picks the change up within about a minute. The setup script in `09-build-plan.md` ("Workspace setup", step 2) is optional: it only saves install time, because D0 installs whatever is missing.
2. **The session.** Repository `FastCoempany/darkestshadeswebsite`, branch `main`, permission mode **Auto**: cloud sessions don't offer Bypass, and Auto is what lets goal turns run without stopping to ask. Then send `/model fable`, `/effort xhigh` and `/effort ultracode`, one message each (ultracode doesn't raise the effort level by itself). On Max, Fable is included up to half the weekly limit; if Claude Code asks to bill usage credits, choose the default model instead.
3. **Run 1:** send this as one message.

```
/goal Run docs/build/DRAWER-WALL.md phases D0 to D7: the drawer wall alone, never a website. Done when docs/build/WALL-PROGRESS.md marks D0 to D7 done, each phase's exit evidence has been run and shown in this session (the command, its exit status and the output that matters), every D-phase pull request is merged into main, and the phone link and the R1 review set are at the top of WALL-PROGRESS.md. Hold CLAUDE.md, docs/brief/00-decisions.md and DRAWER-WALL.md throughout, and never weaken a check to get past it. Or stop after 300 turns.
```

4. **While it runs.** `/goal` on its own shows progress; `/goal clear` stops it. If it stops on a usage limit, send `continue` once the limit resets: the goal stays set. Answer R1 as a comment on the D3 pull request. When R2 arrives: open the link on my phone, run the usability test with five people (`docs/build/drawer-wall/usability.md`), and answer O15–O18 in a comment on the D7 pull request.
5. **Run 2:** a new session set up as in step 2, then:

```
/goal Run docs/build/DRAWER-WALL.md phases D8 and D9 with my comments on the D-phase pull requests and the usability results in WALL-PROGRESS.md: the drawer wall alone, never a website. Done when WALL-PROGRESS.md marks D8 and D9 done with their exit evidence run and shown in this session, the run 2 finishing checks have been run and shown passing, all work is merged into main and pushed, and the final report is written. Hold the same rules. Or stop after 200 turns.
```

If `/goal` ever shows no goal (a session reopened after a long pause, or a new one), send the same `/goal` again; WALL-PROGRESS.md carries the state. A rough expectation: run 1 takes a few days of wall-clock time, most of it render time in the background and waiting on usage limits; run 2 a day or two, depending on how much the feedback asks for.
