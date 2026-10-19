# 05 · Components

Built fresh for Darkest Shades. The digs repo is a reference for process (stories per state, wire mode, token discipline), not a source of components: nothing is copied, and no Darkest Shades component should look or behave like a digs one (`00-decisions.md` #21).

Two layers, enforced by folder:

- **`app/components/base/`**: store mechanics (buttons, fields, drawers, bag lines). Role tokens only.
- **`app/components/house/`**: the Darkest Shades layer (entry, manifesto, stage cards, drop status, the GCD seal). May use base components and primitive tokens through roles.

`base` must not import from `house`. Every component has a Storybook story per state, at 390 and 1440 px, in UI mode and wire mode (`<html data-mode="wire">`, greyscale, media slots labelled).

## Base

| Component | Variants | States | Notes |
|---|---|---|---|
| `Button` | `solid` (bone on night, onyx on paper), `outline`, `quiet` (text only, underline on hover) · sizes 40 / 48 / 56 px | default, hover, active, focus-visible, disabled, busy | Square corners. Label in Stolzl Medium, uppercase micro tracking for `solid`/`outline`, sentence case for `quiet`. Never gold-filled. |
| `TextLink` | inline, nav, footer | default, hover, focus-visible | Inline links underlined with 1 px offset 3 px. |
| `Field` | email, phone (E.164 with country select), text | default, focus, filled, invalid, valid, disabled | 1 px `border-control`; label always visible above (no placeholder-as-label). |
| `Check` | consent, plain | unchecked, checked, focus-visible, invalid | Consent variant holds the full consent text as its label (`08-copy.md`); never pre-checked. |
| `Price` | default, compact | — | Always visible, tabular figures, `$100`. No strike-through variant: there are no sales. |
| `Quantity` | — | default, at limit, disabled, updating | Honors a per-customer limit when a drop sets one. |
| `Gallery` | swipe with counter (mobile), stacked column (desktop) | loading, ready, zoomed, single image | Keyboard arrows, pinch zoom, counter "3 / 9". Images always on `surface-stage`. |
| `Sheet` | full (mobile menu), side (bag), center (notices) | opening, open, closing | Opens with a hard cut (no slide) except the bag on desktop (120 ms). Focus trap, Esc closes, returns focus. |
| `BagLine` | drawer, page | default, updating, removing, error | Stage thumbnail, look number, descriptor, price. |
| `BagSummary` | — | default, checkout-disabled | "Checkout opens at launch" in this phase. |
| `Notice` | inline, toast | info, success, error | `aria-live="polite"`; no icons as the only signal. |
| `Disclosure` | — | collapsed, expanded | Questions page and specs on mobile. |
| `ShotSlot` | image, sequence | loading, loaded, error, wire | Fixed ratio from a token; in wire mode shows `shot code · ratio` (e.g. `F01-A2 · 4:5`). Every image goes through it. |
| `SkipLink`, `VisuallyHidden` | — | — | Skip to content on every page. |

## House

| Component | What it is | States / variants | Ref |
|---|---|---|---|
| `SensoryNotice` | The photosensitivity notice before the entry: one line, `Continue`, `Skip intro` | shown, remembered | `03`, `08` |
| `Entry` | The opening sequence player: cards, bursts, end card, built from still images with a frame clock | playing, skipped, finished, reduced-motion (cards only), wire (frame list) | `03` |
| `Burst` | A run of stills at a set rate with a recurring home image and swap pairs; `framed` (small 3:4 with dark margin) or `bleed` | rate 12 or ≤3 per second, luminance-capped | `03` ref 1 |
| `Card` | The small centered sentence with a period that cuts on and off | night, black | `03` ref 1 |
| `Manifesto` | Stacked statements in Owners Wide, one per screen on mobile, with optional numbered body text | home (3 lines), page (full), print | `02` |
| `DetailHold` | The long held image with a scroll-linked push-in (1.00 to 1.06) and one optional line | idle, in view, reduced-motion (static) | `03` ref 2 |
| `ScaleCut` | A small frontal composition that cuts to full bleed on the visitor's first scroll or tap inside it | small, bleed, reduced-motion (bleed only) | `03` ref 3 |
| `LookNumber` | `01`–`09` in camel micro type, the runway-style index | — | `01` patina |
| `StageCard` | A frame on the stage color, like a print on a dark wall; look number, descriptor, price, availability word | default, hover/focus (second angle), sold out, loading, wire | `04` |
| `DropStatus` | Drop number, state word, date and time with timezone, pairs left | announced, live, sold-out, ended, none (renders nothing) | `08` rules |
| `DropLine` | The one-line status under the header | hidden when no drop | `04` |
| `Countdown` | Counts to a real start or end time from drop data; stops at zero and switches the state | running, reached, no-time (renders nothing) | Never resets, never loops, never invents a time |
| `PairsLeft` | Real remaining quantity from inventory | many (hidden above a threshold the founder sets), few, none | Never a made-up number |
| `SpecSheet` | Size notation (`54□11 145`), lens height, front width, materials, lens color, UV400, polarized | full, compact | Values only from `content/products/` |
| `LineDrawing` | The frame's technical drawing (front, side, top) as inline SVG, strokes in `text-primary`, key measurements | single view, triptych, print | `06`, `tools/drawings.py` |
| `Seal` | The GCD as a small seal: flat gold under 48 px, onyx vector above, 3D render for large hero use | night, paper | `01` GCD rules |
| `CastFrame` | Full-bleed model photo with the frame they wear | default, wire | `07` |
| `ListForm` | Email first; SMS optional with the consent checkbox and terms link | idle, submitting, success, error, already-on-list | `08` |
| `ListOffer` | The 60% scroll pop-up wrapping `ListForm` | hidden, open, dismissed, signed-up | `04` overlays, `08` |
| `FilmGrain` | SVG noise overlay for photography | on, off (reduced transparency, cut-outs) | `01` patina |
| `Header` | Logo or brand mark, three links, bag count | transparent, solid, menu-open | `04` |
| `MenuSheet` | Full-screen numbered menu with the drop line | open, closed | `04` |
| `Footer` | List sign-up, link columns, Instagram, GCD seal, edge-to-edge horizontal logo | night | `04` |

## Behavior rules

- **Motion**: cuts, not transitions. Hover and focus changes are instant or 120 ms; the bag drawer 120 ms; the only long motions are `DetailHold`'s scroll-linked push and the entry's frame clock. Under `prefers-reduced-motion` there are no bursts, no push-ins and no scale cuts.
- **Honesty is enforced in code**: `Countdown`, `PairsLeft` and `DropStatus` only render values from drop and inventory data and render nothing when a value is missing. Unit tests cover each missing-data case.
- **Accessibility**: WCAG 2.2 AA; visible focus everywhere (gold ring on night, gold-700 on paper, 2 px with 2 px offset); 44 px targets; the entry and bursts are `aria-hidden` with a text equivalent and the skip control first in the tab order.
- **No hard-coded color** in `app/`. Base components use role tokens only.
- **Images** always go through `ShotSlot` with a ratio token, so layouts never jump and wire mode works.
