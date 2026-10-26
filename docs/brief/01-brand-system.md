# 01 · Brand system

Anastasiia's identity (logotype, brand mark, fonts, "Sustainable elegance" palette) is the base. The God Cloud Device (GCD) is the second mark. Everything else here is an extension for a store, made by Claude as brand strategist (`00-decisions.md` #13, #14).

## Marks

| Mark | Files | Where it goes | Never |
|---|---|---|---|
| **Primary logo, horizontal**: angular brand mark + DARKEST SHADES on one line (Anastasiia's "Primary Logo") | `brand/marks/web/ds-logo-horizontal.svg` (currentColor), masters `brand/marks/ds-logo-horizontal-{black,white}.svg` | Header on wide screens, footer sign-off, email header, order confirmation | Recolored to gold; stretched; set in live type |
| **Primary logo, stacked** (Anastasiia's "Secondary Logo" file) | `brand/marks/web/ds-logo-stacked.svg` | Square-ish spaces: entry end card, packaging inserts, social avatars | Called "secondary" anywhere in the product; that word now belongs to the GCD |
| **Brand mark** (the angular shape alone) | `brand/marks/web/ds-brand-mark.svg`, favicon set in `brand/marks/favicon/` | **Nav on small screens, favicon, app icons**, loading state | Replaced by the GCD at small sizes |
| **GCD** (God Cloud Device): gold band, black onyx inset | Vector: `brand/emblems/gcd/svg/`; 3D renders: `brand/emblems/gcd/render/` | On the product, once, on the wearer's right (right temple, F02's right wing), the product-page detail view, the footer seal, drop "live" seal, packaging | In the nav or favicon; below 24 px wide; more than once per screen; as a pattern or wallpaper |

Retired: the Eclipse Silhouette (`darkestshades` repo, `brand/emblems/eclipse-silhouette/`) and the old engraved DARKEST SHADES wordmark on the frames. Neither appears anywhere on the site, including in photos.

### GCD rules
- **Size steps.** Under 48 px wide: `gcd-flat-gold.svg` (no veins). 48–160 px: `gcd-onyx.svg` (metallic gradient, veins). Above 160 px or in photography: the 3D render (`gcd-3d-front-*.png`) or the emblem as it appears on the product.
- **On light surfaces** use `gcd-gold-black.svg` or the 3D render. Flat gold on paper is 2.1:1, so it is decoration only, never a carrier of meaning.
- **Clear space**: a quarter of the emblem's height on every side.
- **Physical scale on the frames**: one GCD, on the right temple (F02: the right wing; F04, F05: the right end-piece). Length = 0.98 × the temple face height at the hinge; centre 0.82 × that height from the hinge; 39% down the temple face; parallel to the temple; always clear of the lens bay's bevel. Per-frame sizes are in `06-products.md`. It executes one way only (founder, Oct 26 2026): at that size, proportion and placement on every frame, in every photo, composite and 3D render, whatever the view; never scaled, moved or left off to suit a picture.
- The kit's `logo-kit/svg/eclipse-*.svg` files in `darkestshades` are the wrong (lopsided) shape. The master is `brand/emblems/gcd/svg/gcd-geometry.svg`, redrawn from the symmetric render and checked against it.

## Color

Source of truth: `tools/palette.py` → `design/tokens/tokens.color.json`, `tokens.color.css`, `contrast-report.md`. Components use **role tokens only** (`--color-surface-*`, `--color-text-*`, `--color-action-*`, `--color-status-*`); no hex values in `app/`.

### From the identity
| Token | Hex | Origin |
|---|---|---|
| `black` | `#000000` | Logo black, moodboard swatch 1 |
| `graphite-500` | `#545454` | Moodboard swatch 2 |
| `camel-500` | `#BF835F` | Moodboard swatch 3 |
| `gold-500` | `#C6A36A` | GCD flat gold (logo kit) |
| `onyx-950`, `onyx-700` | `#050607`, `#2C2C2D` | GCD onyx gradient (logo kit) |

### Added for the store
- **Onyx surfaces** `onyx-900 #0B0B0C`, `onyx-850 #131416`, `onyx-800 #1C1D1F`: the site is dark by default ("night" theme). Pure black is kept for the logo and the entry.
- **Bone** `bone-100 #E8E4DC` (primary text on night), `bone-50 #F3F0E9` (paper surface): warm slide-film whites from the SS90 patina, not screen white.
- **Ash text greys** `ash-400 #8A8A8A`, `ash-300 #A6A5A1`, `ash-200 #CFCBC3`. This is the fix for grey on black: graphite `#545454` is 2.7:1 on onyx, so it only draws rules and dividers. The smallest text grey on dark is `ash-400` (5.9:1 on the canvas, 4.9:1 on overlays).
- **Stage** `#E4E2DD`: the product backdrop, matched to the cleaned lightbox seamless so cut-outs and full shots sit on the same ground.
- **Ink versions for paper**: `gold-700 #7A5C2E`, `camel-700 #7F5137`.
- **Status** (success, error, info) in a light version for night and a dark version for paper. Drop "live" uses gold.

### Themes and rules
- `night` (default): canvas `onyx-950`, text `bone-100`, secondary `ash-300`, accent `gold-500`.
- `paper`: for long reading (policies, care, the manifesto's printed version, size guide). Canvas `bone-50`, text `onyx-950`.
- **Product images always sit on the stage color**, in both themes. In night, that makes each product a lit print on a dark wall (the framed prints of reference 1).
- Gold is an accent: one gold element per view (focus rings excepted). Camel is editorial (look numbers, drop numbers, pull quotes), never an action color.
- Every pair in `contrast-report.md` passes WCAG 2.2 AA. Adding a pair means adding it to `CHECKS` in `tools/palette.py`.

## Type

Only Owners Wide and Stolzl (`00-decisions.md` #13). Font files are never committed (public repo); see `brand/fonts/README.md`.

| Role | Face | Size (390 → 1440 px) | Notes |
|---|---|---|---|
| Manifesto | Owners Wide Medium, uppercase | 40 → 120 px, line height 0.95 | One statement per screen. |
| Display | Owners Wide Medium, uppercase | 32 → 72 px, 1.0 | Section openers, drop names. |
| H1 / H2 | Owners Wide Medium, uppercase | 28 → 44 / 22 → 30 px | Tracking +0.01em. |
| H3 / label | Owners Wide Medium, uppercase | 13 → 15 px | Tracking +0.08em. |
| Body | Stolzl Book | 16 px, line height 1.6 | Sentence case. |
| Body large | Stolzl Book | 18 px, 1.55 | Product story, manifesto body. |
| UI | Stolzl Regular / Medium | 14–15 px | Buttons, inputs, nav. Medium for buttons. |
| Micro | Stolzl Medium, uppercase | 11–12 px, tracking +0.12em | Drop status, look numbers, spec labels. |
| Card | Stolzl Regular, sentence case with a period | 15 → 17 px | The small centered lines between the strobe bursts (reference 1). |
| Light | Stolzl Light | 22 px and up only | Large quiet lines; Light is too thin for small text on dark. |

- Owners Wide is never used for body text or anything under 13 px.
- Numbers in specs and prices: Stolzl with tabular figures (`font-variant-numeric: tabular-nums`).
- Prices are set at body size, never hidden, never in a lighter grey than `ash-300`.

## Patina: Prada SS90

What we take from an early-90s Milan runway, as it survives on film. These rules apply to photography and image treatment; the UI itself stays clean.

- **Light**: hard frontal flash plus flat overhead runway light. Short, hard-edged shadows. No colored gels, no neon, no golden hour.
- **Film**: 35 mm color negative look. Fine grain, slightly lifted blacks (around `#0B0B0C`, never `#000000` in a photo), warm paper-white highlights (around `bone-50`), mild softness, faint halation on the brightest whites. Applied in the photo pipeline, never with CSS filters.
- **Color**: muted and low-saturation. Wardrobe in black, navy, grey, camel, off-white. Skin natural.
- **People**: neutral expression, no smiles to camera, minimal makeup, hair pulled back or simply worn. Walking, standing, or caught mid-turn.
- **Space**: a plain runway, a seamless, a bare institutional room. Lots of floor and wall. One figure per frame, centered or on a third.
- **Numbers**: runway-style look numbers ("01", "02") identify frames on the site, small and in camel.
- The site adds a 3–4% film-grain overlay on photography only (an SVG noise layer), switched off under `prefers-reduced-transparency` and for product cut-outs.

## Imagery rules
- Product shots: only the cleaned lightbox set (`07-photography.md`), always with the GCD and never the old marks.
- People: only the seven cast models, generated, with the real frames composited in.
- No stock people, no third-party product photos, no Prada or runway photos on the site (they are mood references only and are not stored in this public repo), no generated lettering or generated glasses.
