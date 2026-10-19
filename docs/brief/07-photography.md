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

### Pipeline (per selected shot)
1. **Pull** the original from the release zip by byte range (no 1.5 GB download): `tools/photo/zipget.py`.
2. **Normalize**: apply EXIF orientation, convert to sRGB from the embedded profile (iPhone files are usually Display P3), neutralize white balance against the seamless, normalize exposure so the seamless reads `#E4E2DD` (the stage token).
3. **Segment the frame**: a first mask from a background-removal model (rembg with u2net or isnet weights, from GitHub releases), refined against the known seamless with a trimap and closed-form matting (pymatting). Output: a soft alpha for rims and temples.
4. **Find the lenses**: the closed regions inside the rims, cross-checked with the drawing's lens outline (front views) and color.
5. **Fix hotspots**: detect ring-light specular blobs (very bright, desaturated, compact) on acetate and lenses; inpaint them (OpenCV, or LaMa where the network allows); then add back one soft, controlled highlight per surface so the acetate still reads as gloss. The same highlight recipe on all eight frames.
6. **Rebuild the lenses (see-through)**: estimate each lens's transmission from what the seamless looks like through it, then rebuild it as a clean layer: tint color + transmission + one soft reflection. In the stage image the lens shows the stage through it; in the cut-out it is partially transparent (alpha 0.80–0.95 by lens color), so faces and scenes show through when composited. No solid-filled lenses.
7. **Remove the old marks**: the engraved DARKEST SHADES wordmark, the old logo and printed temple text, using per-shot masks (as in `darkestshades/brand/lightbox/onyx-emblem/process/cfgs.py`), inpainted with the material's own texture (tortoise patterns are rebuilt from neighboring texture).
8. **Place the GCD**: measure the temple's top edge, bottom edge and hinge line in the photo; render the GCD in Blender at that orientation (`tools/blender/gcd_render.py`, lighting preset matched to the tent: bright surround, ring light at the lens), at the size in `06-products.md`; composite with a contact shadow, matched focus and grain. Never a flat sticker.
9. **Re-stage**: replace the uneven seamless with a uniform stage (`#E4E2DD`) plus a soft contact shadow generated from the alpha, so every frame sits on the same ground.
10. **Normalize framing**: A1–A5 masters at 4:5; the frame's front spans 78% of the canvas width in A1; horizon and center line identical across frames. Landscape heroes at 3:2.
11. **Export**: master (16-bit PNG, alpha), stage version (sRGB JPEG master), web sizes 640/960/1440/2048 in AVIF, WebP and JPEG; register in `MANIFEST.csv`.

**Resolution and vectors.** Photos stay raster at their native resolution (12 MP originals); upscaling for print uses a free super-resolution model (OpenCV's EDSR from GitHub, or Real-ESRGAN weights) and is marked as upscaled in the manifest. The infinitely scalable masters are vector: the frames' line art at true scale (`tools/drawings.py`) and the GCD (`brand/emblems/gcd/svg/`, plus its 3D model). Tracing photos into vector shapes is not used: glossy acetate traces into thousands of flat blobs.

### Done means
- No hotspot larger than 0.2% of the frame area; no old mark anywhere, including through the lens.
- Lens transmission and reflection consistent across all shots of a frame.
- Same stage color (ΔE < 2 between any two finals), same contact shadow recipe, same framing.
- GCD at the specified size, with a believable reflection and a contact edge; checked at 200% zoom.

## Track 2: people

### The cast
Seven original, generated people (#15): three women, three men, one non-binary person, matching the Brand Story personas' ages and range (24–42). "Prada-esque" is about features and build: defined bone structure, lean or long, an unstyled, serious presence.

**Round 1** (Oct 19 2026): fourteen candidates, two per slot, in a Figma file in the founder's drafts, all in one shared setup so only the person changes. The founder picks seven (`00-decisions.md` O5). The pick becomes `reference/casting/` contact sheets and a **model bible** per person: one fixed paragraph (age, build, skin, hair, brows, jaw, grooming, attitude) reused word for word in every prompt. Record the Figma file link in `reference/casting/README.md` the moment a file is created.

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
4. **Composite the real frame** (`tools/photo/wear.py`, phase 5):
   - face landmarks (MediaPipe Face Mesh, from PyPI) give eye centers, nose bridge, temples and ears;
   - scale so the frame's lens-center distance (lens width + bridge, from product data) sits on the pupils (adult pupillary distance about 63 mm, so a 54□11 frame is 65 mm between lens centers);
   - perspective-warp the matching cut-out (A1, A2 or A3) to the landmarks; the far temple is hidden behind the head, the near one runs to the ear and goes under hair where hair crosses it (hair mask from the segmentation);
   - lens layer: transmission from the cut-out darkens what's behind it, plus a reflection rebuilt for the scene's light (window, runway lights) instead of the ring light;
   - contact shadows: under the nose pads, along the cheek under the lower rim, a thin shadow under the temple on the skin;
   - the GCD stays as in the product master, re-lit to the scene if its angle changed.
5. **Grade everything together**: the SS90 look (`01-brand-system.md`): fine 35 mm grain, lifted blacks, warm paper whites, faint halation, low saturation. One LUT plus grain, applied to the finished composite so person, scene and frame share one surface.
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
