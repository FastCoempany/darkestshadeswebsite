# CLAUDE.md: Darkest Shades storefront (darkestshades.com)

You are building the **Darkest Shades** website: a custom Shopify storefront (Hydrogen) for a sunglasses brand that sells eight frames at $100 in drops. This phase is **wireframes, UI and components**. No payments, no live store connection.

## Read first, in order
1. `docs/brief/00-decisions.md`: what's settled and what's open. It wins any conflict.
2. `docs/brief/01-brand-system.md` → `09-build-plan.md`.
3. `content/products/*.json`, `content/drops/*.json`, `content/copy/en.json`, `design/tokens/`.

## Non-negotiables

**Brand**
- Tagline: **See Everything. Reveal Nothing.** Prada is the idol; the design lens is "philosophy as manifesto, before product" (`02-raf-lens.md`). **Raf Simons is never named, shown or quoted** anywhere in the site, metadata, alt text or shipped code.
- Marks: Anastasiia's logo and angular brand mark are primary; the **GCD** (gold band, black onyx inset) is the secondary insignia. **Nav and favicon use the brand mark, never the GCD.** Marks come only from `brand/marks/` and `brand/emblems/gcd/`. The Eclipse Silhouette and the old engraved wordmark never appear.
- Fonts: **Owners Wide** (Medium) and **Stolzl** (Light, Book, Regular, Medium) only. **Never commit font files** (public repo); load them as `brand/fonts/README.md` says.
- Color: **role tokens only** in `app/` (`--color-surface-*`, `--color-text-*`, `--color-action-*`, `--color-status-*`); no hex values. Graphite `#545454` is never text on dark. One gold element per view. Product images always sit on the stage color.

**Honesty**
- The price ($100) is always visible.
- Countdowns only count to real times from drop data; pair counts only come from inventory; a missing value renders nothing. No discounts, no exit offers, no fake urgency, no invented reviews (`08-copy.md`).

**Opening experience**
- Sound off by design; built from still images, not video; photosensitivity notice first; skippable from frame 1; never on deep links or for returning visitors; no bursts under `prefers-reduced-motion`. `tools/flashcheck.py` must pass (`03-references.md`).

**Products and copy**
- Every product fact comes from `content/products/` (from the 1:1 drawings). **Never invent a spec**; `null` hides the row. Frames carry the founder's names (`06-products.md`); names are never explained or tied to a real person.
- All copy from `content/copy/en.json`. No lorem ipsum anywhere. `@darkestshades`, `darkestshades.com`, `#DarkestShades`.

**Imagery**
- Product photos only from the cleaned lightbox set, with the GCD and without the old marks. People only from the seven-person generated cast, wearing the real frames (composited, never generated). Until finals land, every image is a labelled `ShotSlot`. Reference videos and Prada/runway material never ship.

**Build**
- Mobile first: 390, then 768, 1024, 1440. WCAG 2.2 AA.
- `app/components/base/` must not import from `app/components/house/`. Components are Darkest Shades' own; don't copy digs components.
- Every component has a Storybook story per state, at 390 and 1440, in UI and wire mode.
- Data goes through `app/lib/mock/` in Storefront API shape. No live Shopify calls, no checkout wiring in this phase.
- Change tokens through `tools/palette.py` and `design/tokens/tokens.base.json`, then `python3 tools/build_tokens.py`; never hand-edit `design/tokens/build/`.
- Free tools only. No purchases, no paid APIs.

## Commands
```
python3 tools/palette.py          # color tokens + contrast report (fails on any contrast failure)
python3 tools/build_tokens.py     # design/tokens/build/*.css
python3 tools/marks.py            # web marks + favicon set from Anastasiia's masters
python3 tools/drawings.py         # vector line art from the technical drawings (needs pymupdf)
python3 tools/blender/gcd_render.py --size 4096 --samples 160 --views front,yaw35,yaw60   # needs bpy==5.2.2
```
App commands (`npm run dev`, `npm run storybook`, `npm run test:visual`) are added in phase 0.

## When unsure
If `00-decisions.md` doesn't answer it and it touches brand, product facts, money or legal copy, ask the founder. Otherwise make the call and note it in the PR.
