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
| D1 · The project | not started | | | |
| D2 · Records and logic | not started | | | |
| D3 · The wall and the drawer | not started | | | |
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

## Now and next

- D0 done; D1 next: `wall/` with the stack (pin `@playwright/test` 1.63.0 to match the VM's Chromium 1243 and the WebKit 2359 installed in D0's wake, `three` 0.187.0, `lit` 3.3.3, `vite` 8.3.6, `vitest` 5.1.0, `typescript` 7.0.2 unless it breaks the tooling, then 5.9), the `surface-scene` token, the stand-in fonts, the placeholders, the workflow.

## Render queue

| Job | State | Time per frame | Notes |
|---|---|---|---|
| (not started) | | | |

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

## Questions for Antaeus

| Question | Default in use | Where it came up |
|---|---|---|
| Open the S2 test page on your phone (https://claude.ai/artifact/2vxLcc1s6j223jMUt8YfSx) and tell me its status line, the one under the description that starts with "Pass" or "Fail" and lists module, GLB fetch, WebP decode, AVIF decode and WebGL 2. It says whether a published Artifact can run the wall's module scripts, fetch its GLBs and decode its images. | The wall is built as if it passes; if it doesn't, D7 falls back to GitHub Pages, only with your yes (O18) | D0, S2 |

## Copy for sign-off

The `wall` section of `content/copy/en.json` (status `draft`), added in D2. Listed here as it lands.
