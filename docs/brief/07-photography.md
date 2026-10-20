# 07 · Photography

Two tracks, one look:

- **Product**: the 317 real lightbox shots, cleaned to a consistent catalog set with the GCD in place of the old marks (`00-decisions.md` #8, #9).
- **People**: seven generated models in generated SS90-patina scenes, wearing the **real** frames, composited from the product cut-outs (#15–#17).

Everything runs on free tools (#24). Tool availability in the cloud workspace is in `09-build-plan.md` (network access must be **Full** for Hugging Face, Figma asset downloads and Adobe Fonts).

## Where files live (the DAM)

This repo is public and is not the DAM (#20). Masters live in private storage; the repo only carries web exports and a manifest.

| Stage | Where | Naming |
|---|---|---|
| Originals (untouched) | `darkestshades` release `DARKESTSHADES.zip` → `Lighbox shots/` (and the founder's Google Drive folder of the same name) | `IMG_3554.jpg` as shot |
| Masters (cleaned, full resolution, 16-bit PNG with alpha) | Google Drive `Darkest Shades/DAM/masters/` (or a private `darkestshades` release `dam-masters-v1`) | `DS-F01-A2-v01-master.png` |
| People masters | Google Drive `Darkest Shades/DAM/people/` | `DS-CAST-W1-S03-F05-v01-master.png` (cast slot, scene, frame) |
| Web exports | this repo, `assets/photography/` (created when finals land) | `ds-f01-a2-1440.avif` / `.webp` / `.jpg` |
| Delivery | Shopify Files / product media (CDN) | same names |
| Register | `assets/photography/MANIFEST.csv`: id, source shot(s), frame, angle, version, tool chain, master location, status, alt text | one row per final |

Angle codes: **A1** front · **A2** three-quarter · **A3** side · **A4** top-down · **A5** inside (from behind) · **A6** GCD detail · **H** landscape hero.

## Track 1: product (lightbox → catalog)

### The source set
One iPhone session (Apr 15 2025): 317 JPGs, 248 portrait and 69 landscape, at three resolutions, on a light seamless in a light tent with a ring light. Shot group per frame in `06-products.md`. The ring light leaves hotspots on gloss acetate and lenses; some frames show the tent floor edge or the room. `content/photography/lightbox-angle-set.json` holds the first-pass picks per frame and angle (picked from thumbnails; confirmed at full resolution as each frame is cleaned), alternates, rejects, gaps and the four shots that look misfiled.

**Which side.** The GCD is on the wearer's right only, so the three-quarter, the GCD detail and the hero use right-side shots wherever the set has them (re-picked Oct 19 2026); the side view keeps a true left profile where the set has no right one (F01, F03, F05, F09). `lightbox-angle-set.json` records the side of each pick. Seen from the front, the wearer's right is on the image's left. On an outside view, the front at the image's right with the temple running left is the right side; a view from behind flips that, so those are told by the hinge hardware (it sits on the inside) and by the old print reading the right way round (it sits on the outside). F08 was never shot from its right side outside (`00-decisions.md` #34: its images show no GCD).

### Pipeline (per selected shot)
`tools/photo/clean_lightbox.py` does steps 2–10 and has cleaned all seven angles of all eight frames (56 shots). Each shot has a settings file, `content/photography/shots/<shot>.json`, with the measurements the tool can't guess: the working region, a point inside each lens, a polygon per old mark with the temple's top and bottom edge lines, the hinge line and temple axis for the GCD, and the framing.

```
python3 tools/photo/zipget.py --picks content/photography/lightbox-angle-set.json --frames F08
python3 tools/photo/clean_lightbox.py content/photography/shots/IMG_3596.json [--debug]
```

1. **Pull** the original from the release zip by byte range (no 1.5 GB download): `tools/photo/zipget.py`.
2. **Load**: EXIF orientation, Display P3 → sRGB from the embedded profile; all the math below runs in linear light.
3. **Segment**: a soft alpha for rims and temples from ISNet (rembg); each lens from SAM with the shot's point prompts (each model runs in its own process: together they need more memory than the workspace gives one process). A lens mask gets its holes filled and small notches closed (what SAM leaves out is something seen through the lens), and a lens with no concave edge can be made convex (`"convex": true`). Masks are cached in `work/out/<shot>/masks/`.
4. **Model the tent**: a robust smooth fit, plus the tent's own structure the fit misses (the sweep's horizon, light falloff), measured right up to the frame wherever its shadow can't fall and carried under it.
5. **Keep the frame's own shadow**: image ÷ tent inside the shadow zone (below the frame and a little to the sides, since the tent is lit from above and the camera looks down), fading out by 450 px. Seen from straight above (A4), the shadow lies all round the frame (`shadow_zone.around`). Everywhere else the new stage is one even color.
6. **See-through lenses**: transmission per color channel = image ÷ tent, so a lens is a color filter (F01's blue and F03's yellow keep their color on any background). Ring-light reflections (bright top-hat spots) and dust (small dips, deeper than the noise in absolute and relative terms) are painted out of the transmission. No solid-filled lenses; transmission is measured, not set (median: F08 about 12–14%, F09 about 6–7%, F02 about 3%, a little higher in blue). Where what the lens sees (the tent's horizon, a nose pad, a temple behind it) would come out in fragments, each lens is refilled with its own measured tint (`smooth`: `flat`, or `gradient` for gradient lenses), its grain put back; on a light lens (F01, F03) what is clearly darker than the tint, a temple behind it, stays (`keep_behind`). Every shot keeps the lens as its own photograph shows it: the yellow, the blue and the greys are measured in that shot, never set or carried over from another angle (founder, Oct 19 2026). Seen at a steep angle (F06's three-quarter and detail), a lens shows its own edge as a band along the rim; it is kept exactly as shot, without the refill, which stopped short of the rim with a ragged edge.
7. **Remove the old marks**: per-shot polygons (from `darkestshades/brand/lightbox/onyx-emblem/process/cfgs.py` where they exist). On a temple, the face is straightened between its measured top and bottom edges and rebuilt row by row, so the acetate, the core wire and the bevel continue through the patch; grain is added back. Where the stripes inside a temple are not parallel to its edges (F08's grained metal core runs at a slant inside the clear acetate), the rows follow every stripe's own measured edge instead (`temple.guides`), or the core comes out doubled. A textured face (gloss acetate that mirrors the tent's dimpled wall on the F06 hero, F08's grained core) would come out streaked: there the rebuilt rows give only the smooth shading, and the texture comes from the clean face further along the same temple (`texture_dx`, `texture_from`). Gloss highlights on acetate stay as shot; a ring-light hotspot on acetate, where a shot has one, is listed as a mark with `"kind": "light"`.
8. **Place the GCD**, once, on the wearer's right (`00-decisions.md` #31): shots of the left side get the old marks removed and nothing added. `tools/blender/gcd_render.py --light lightbox` renders it at the face's yaw (bright surround, the phone's dark body in the reflections, the ring light on angled views only; made on first use into `work/gcd/` with its 2D anchors), at the size in `06-products.md`, centered 0.82 × the temple height from the hinge and 39% down the face (on F02's wing: over the two pin heads; on F04's and F05's end-pieces: centered on the triangle each forms with the front's side), always reading left to right, clear of the lens bay's bevel; warped onto the measured face, with a contact occlusion and focus-matched softening. Never a flat sticker. On a temple the placement is physically measured (founder, Oct 19 2026) with `tools/photo/temple_gcd.py`, from measurements of the picture, never by eye: the temple's edges (column profiles), the hinge line (the seam where the temple's face meets the end-piece, not the front's edge: on F03 the end-piece's side runs about 7 mm on from the seam), the seam's slant across the face from the side drawing (F01 1.9 mm, F06 0.97, F09 3.19 from the temple's top to its bottom; the old print's letters stand square to the temple and lean off the seam in the picture just as much), and the old print's first line, DARKEST, located from its strokes. Per frame, the temple's face is modelled in 3D on the shot where its edges converge most: the edges are parallel on the frame, so where they meet in the picture gives the temple's direction (the focal length is in the EXIF), and the hinge line gives the face's down direction and its distance. That model also locates the old print (F01 26.1 to 42.5 mm from the hinge, F03 23.7 to 38.4, F06 26.3 to 41.4); where a profile shows the temple square on, its height the same along its length, the print's distances are read straight off it instead (F09 24.1 to 39.9, from the left profile). On the frame's other shots the print is the ruler: the hinge and the print's two ends are three points at known distances along the temple, which fixes its perspective. The print's proportions alone (its first line about 7 times as long as tall) are a last resort: its height is too small to measure well, and they drew the GCD up to a third too short. The tool writes `view` (the render's turn and tilt, e.g. `yaw-57p31`) and `anchors_px` into the shot's settings, with the command in `gcd.measured_with`. Judged by eye, the turn of a temple is easy to underestimate: the first placements on F01, F03 and the F09 hero drew the GCD 40% to 100% too long for the angle; and the hinge is easy to misplace: the first F03 hero and detail placements had the GCD on the end-piece.
9. **Re-stage and frame**: the frame over (stage `#E4E2DD` × shadow × lens transmission). A soft edge is unmixed against the tent seen just outside it, not against the model under the frame (filled in from all round, it is brighter wherever the tent darkens toward the frame), so it fades into the stage without a grey halo, a step or a ragged line; the frame's own shadow, and the blur of a part the model missed (a defocused far temple, F01's blue, F02's red), are not taken for tent.
10. **Frame by angle** (`content/photography/framing.json`): one rule per angle, applied to the frame's own extent (lenses included), so an angle has the same size and the same height on the page in every frame's set. All at 4:5: the frame spans 78% of the canvas width in A1 and 84% in the others; its lowest point sits at 62% of the height in A1, 68% in A2, 65% in A3 and 69% in A5, with the contact shadow below; A4 is centred. Where a temple runs off a side of the photograph, the visible width isn't the frame's, so its height sets the scale instead (29% of the canvas height in A2, 27% in A3), unless the frame would then fill less than 75% of the width; that side stays the photograph's edge, the temple running off the picture with its shadow. The A6 close-ups keep the photographer's crop at 4:5; the photographed heroes keep the photographer's full width at 3:2, the stage carried above and below; F04's hero, which the shoot doesn't have, is its front shot on a 3:2 stage, the frame spanning 78% of the width.
11. **Export** (next): master (16-bit PNG), stage version, web sizes 640/960/1440/2048 in AVIF, WebP and JPEG; register in `MANIFEST.csv`.

Outputs in `work/out/<shot>/` (git-ignored; finals go to the DAM): `stage.jpg` (2000 wide) and `stage-full.png` (16-bit); `cutout.png`, one 16-bit RGBA file with the lens filter folded into the alpha (the master); `layers/frame.png`, `layers/lens.png` and `layers/shadow.png`, the exact decomposition for compositing on anything (multiply the background by shadow and lens, then the frame on top; exact in linear light, close in an ordinary sRGB document); `compare.jpg`; `report.json` (lens transmission per channel, pixels cleaned, GCD size and position).

**Resolution and vectors.** Photos stay raster at their native resolution (12 MP originals); upscaling for print uses a free super-resolution model (OpenCV's EDSR from GitHub, or Real-ESRGAN weights) and is marked as upscaled in the manifest. The infinitely scalable masters are vector: the frames' line art at true scale (`tools/drawings.py`) and the GCD (`brand/emblems/gcd/svg/`, plus its 3D model). Tracing photos into vector shapes is not used: glossy acetate traces into thousands of flat blobs.

### Done means
- No hotspot larger than 0.2% of the frame area; no old mark anywhere, including through the lens.
- Each lens as its own photograph shows it: transmission measured in that shot, never evened out across a frame (`00-decisions.md` #32); ring-light reflections and dust cleaned the same way on every shot.
- Same stage color (ΔE < 2 between any two finals), same contact shadow recipe, same framing.
- GCD at the specified size, with a believable reflection and a contact edge; checked at 200% zoom.

## Track 2: people

### The cast
Seven original, generated people (#15): three women, three men, one non-binary person, matching the Brand Story personas' ages and range (24–42). "Prada-esque" is about features and build: defined bone structure, lean or long, an unstyled, serious presence.

**Round 1** (Oct 19 2026): fourteen candidates, two per slot, in a Figma file in the founder's drafts, all in one shared setup so only the person changes. The seven are picked (`00-decisions.md` #30): **W1A, W2A, W3A, M1A, M2B, M3A, NBA**. Each has a **model bible** in `reference/casting/model-bibles.md`: one fixed paragraph (age, build, skin, hair, face, grooming, attitude) reused word for word in every prompt. Record the Figma file link in `reference/casting/README.md` the moment a file is created.

| Slot | Candidate A | Candidate B |
|---|---|---|
| W1 | Korean, 24 | Japanese, 23 |
| W2 | West African, 29 | Ethiopian, 30 |
| W3 | Italian, 40 | Spanish, 42 |
| M1 | Northern European, 26 | Eastern European, 25 |
| M2 | Caribbean, 32 | Nigerian, 34 |
| M3 | South Asian, 38 | Middle Eastern, 37 |
| NB | Mexican / Indigenous, 27 | East Asian / white, 26 |

### Best path, and why
The generator is **Figma `generate_image` with `gpt-image-2.5-sunburst`** on the Starter plan's included AI credits (2 credits an image; 500 a month, 150 a day; generation stops at the cap and nothing is charged). It is text-only, so:

1. **Generate the person and the scene together, without glasses.** One image per shot, so light and perspective agree. Eyes open, looking past the camera, nothing touching the face or temples, hair clear of the ears where a temple must sit.
2. **Pose to match the cut-outs.** The frames exist at three head angles (A1 front, A2 three-quarter, A3 side), so every prompt fixes the head angle to one of them ("head turned three-quarters to the left, chin level"). The composite then needs a small warp, not a re-render.
3. **Hold the face with the model bible plus the glasses.** The frames cover the eyes and brows, the most identity-defining part of a face, so a fixed description of hair, skin, jaw, lips and build carries identity across shots. Cast faces without glasses appear only in the casting sheets.
4. **Composite the real frame** (`tools/photo/wear.py`, settings per image in `content/photography/people/`):
   - face landmarks and head pose from InsightFace (`pip install insightface onnxruntime`; its models download from GitHub releases; MediaPipe's models sit on a host this workspace can't reach);
   - scale from the pupils (an assumed pupillary distance, about 62 mm), then fit the photographed lens openings onto the 1:1 drawing's lens openings at that scale and the head's pose (a homography from eight points), so the frame is as big on the face as it is in life (a 45□24 frame has its lens centres 69 mm apart, so the pupils sit a little inside them);
   - the cut-out comes from the cleaned shot of the matching angle (A1 for a face to camera); in A2 and A3 the far temple is hidden behind the head and the near one runs to the ear, under hair where hair crosses it;
   - lens layer: each lens's measured tint, flat, multiplies what's behind it; nothing the product shot saw through the lens (temples, the tent) comes along. One soft reflection per lens for the scene's light;
   - the frame's contact shadow on the skin, offset and softened for the scene's light;
   - the frame lit like the scene: its color and level scaled by the scene's backdrop against the tent it was shot in;
   - the GCD comes with the frame, as placed on the product shot.
5. **Grade everything together**: the SS90 look (`01-brand-system.md`): fine grain, lifted blacks, warm paper whites, faint halation, low saturation, applied to the finished composite in `wear.py` so person, scene and frame share one surface.
6. **Check** each final against a list: scale against the face, nose-pad contact, temple to ear, no glasses artifacts from the generator, hands and fingers plausible, no text or logos in the scene, the GCD correct and once.

Why not the alternatives: generating people *with* glasses would invent the product, which the founder's own AI-photography guide rules out; separate person and background generations never quite agree on light; local open models (SDXL, Flux) are too slow and too large for this workspace's CPU; the Gemini app holds faces from references but its free output carries a visible watermark, so it can only make references, never finals; Weave and every paid route are out (#24).

### Scenes (SS90 patina)
Simple, striking, institutional. One figure per frame. Each scene has a code and a fixed prompt block in the prompt pack (`reference/casting/prompt-pack.md`, phase 5):

| Code | Scene | Light |
|---|---|---|
| S01 | Bare runway, white floor, black void behind | Hard frontal flash + overhead runway cans |
| S02 | Grey seamless, full length, mid-stride | Flat overhead |
| S03 | Concrete stairwell, figure small in frame | One hard shaft from above |
| S04 | Long institutional corridor, terrazzo floor | Fluorescent overhead, hard flash fill |
| S05 | Doorway wedge of light on a dark floor | One hard key through the door |
| S06 | Studio portrait against black, head and shoulders | Hard key, no fill |
| S07 | Studio portrait against warm white, three-quarter | Flash, short hard shadow |

Wardrobe: uniform-like, no logos: black or navy nylon, crisp white or grey shirting, fine knits, tailored trousers, a long coat. Nothing that competes with the frame.

### Shot list (first finals)
- Each of the seven in two scenes: 14 editorials.
- Each frame on at least two people: product pages get 2–3 on-model shots per frame.
- One hero per breakpoint (9:16 and 16:9) for the drop.
- Budget about three generations per final; spread across days to stay under the 150-a-day credit cap.

## Disclosure
Until real photos of production pairs replace them, on-model images carry a small line in the gallery: "Images made with generated models and the real frame." Product shots are real photographs and need no line.
