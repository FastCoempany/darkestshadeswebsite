# 04 · Information architecture and pages

Eight products, so everything is capsule-sized: four top-level destinations, no search, no filters, no mega-menu.

## Sitemap

| Path | Page | Notes |
|---|---|---|
| `/` | Home | The entry plays first, on the first visit to `/` only (`03-references.md`). |
| `/drop` | Current drop | Redirects to `/drops/{number}` of the live or next drop. |
| `/drops/{number}` | Drop | Status, date, pair counts, the frames in it. Past drops stay up as an archive ("Ended"). |
| `/frames` | All frames | The eight frames as numbered looks. Sorted by look number. |
| `/frames/{handle}` | Frame (product page) | Handles are the frame names in kebab case: `/frames/lou-went-underground`. |
| `/manifesto` | Manifesto | The full statement; paper theme for reading. |
| `/cast` | The cast | The seven models and their looks. |
| `/questions` | Questions | Fit, lenses, drops, shipping, exchange, warranty. |
| `/care` | Care | Cleaning, case, onyx and gold care. |
| `/policies/*` | Shipping, exchange (45 days), warranty (6 months), privacy, terms, SMS terms | Shopify policy content, paper theme. |
| `/accessibility` | Accessibility | Includes the photosensitivity note and how to turn the intro off. |
| `/cart` | Bag | Also a drawer from every page. |
| `/account/*` | Account | Shopify customer accounts; out of scope this phase beyond a placeholder. |
| `*` | 404 | One line, the brand mark, a way back. |

## Navigation

- **Header, 1024 px and up**: horizontal logo left · `Drop` `Frames` `Manifesto` center · `Bag (n)` right. 64 px tall, transparent over the entry end card and the manifesto, night surface after.
- **Header, under 1024 px**: brand mark left (the angular mark, per `00-decisions.md` #11) · `Menu` · `Bag (n)` right. 56 px.
- **Menu sheet** (mobile): full-screen night surface; the four destinations in Owners Wide at 32 px, numbered `01`–`04` in camel; the drop status line; small links (Questions, Care, Instagram `@darkestshades`). Opens with a hard cut, no slide.
- **Drop status line**: a single line under the header on every page while a drop is upcoming or live ("Drop 001 · Live · 37 of 120 pairs left"). Only real numbers from inventory; hidden when there's no drop.
- **Footer**: the list sign-up, link columns (Shop: Drop, Frames · House: Manifesto, Cast · Help: Questions, Care, Shipping, Exchange, Warranty · Legal: Privacy, Terms, SMS terms, Accessibility), Instagram `@darkestshades`, the GCD seal, and the horizontal logo edge to edge at the very bottom.

## Page templates

### Home
See `03-references.md`. Sections: Manifesto → The detail → The drop → The cast → The promises → The list → Footer.

### Drop (`/drops/{number}`)
- Opens on one statement and the drop number in Owners Wide ("Drop 001").
- **Status block**: one of `Announced` (date known, not open), `Live`, `Sold out`, `Ended`. Date and time with timezone; pairs per frame and in total, from inventory. A countdown appears only when a real start or end time exists, and it counts to that time.
- The frames in the drop as stage cards (look number, descriptor, price, pairs left).
- `Get notified` (email/SMS sign-up scoped to the drop) when Announced; `Add to bag` per frame when Live; `Sold out` disabled state when gone.

### All frames (`/frames`)
- A statement line, then the eight frames as stage cards in a grid: 1 column at 390, 2 at 768, 3 at 1024, 4 at 1440.
- Card: look number (camel, micro), product image on the stage color (A1 front angle, swaps to A2 three-quarter on hover/focus), name, descriptor, price, availability word ("In Drop 001", "Sold out", "Next drop").

### Frame page (`/frames/{handle}`)
1. **Gallery**: A1 front, A2 three-quarter, A3 side, A4 top, A5 inside, A6 GCD detail, then on-model shots. Mobile: full-width swipe with a numeric index ("3 / 9"); desktop: two-column stack beside a sticky buy panel.
2. **Buy panel**: look number, name, descriptor, **price $100**, drop status and pairs left, `Add to bag` / `Get notified` / `Sold out`, the two promises in one line each (45-day exchange, 6-month warranty).
3. **The detail**: the held GCD view with one line ("The God Cloud Device. Gold, black onyx inset.").
4. **Specs**: size in the standard eyewear notation (lens–bridge–temple, e.g. `54□11 145`), lens height, front width, frame and temple material, lens color and type, UV400, polarized. Every value from `content/products/`.
5. **Drawn**: the technical line drawings (front, side, top) as vector, with the key measurements.
6. **Worn by**: the cast members wearing this frame.
7. **Next look**: the following frame by look number.

### Manifesto (`/manifesto`)
Paper theme. The full text in Owners Wide (statements) and Stolzl (body), numbered paragraphs, one image at most.

### Cast (`/cast`)
The seven, one per screen on mobile: full-bleed photo, first name or initial only if the founder wants, the frame they wear (linked).

### Questions, Care, Policies, Accessibility
Paper theme, long-reading layout (max 68 characters per line), anchored headings.

### Bag (drawer and page)
Line items with stage thumbnails, price, quantity (max per customer if the drop sets one), subtotal, the exchange and warranty lines, `Checkout` (disabled in this phase, labelled "Checkout opens at launch").

### Overlays
- **The list pop-up** (`ScrollOffer`): once per visitor, at 60% scroll on Home, Drop and Frame pages; never on the first screen, never during the entry, never on policy pages; never a discount (`08-copy.md`). Closes with Esc, the close button, or a click outside; doesn't return for 30 days after closing or 365 after signing up.
- **Photosensitivity notice**: before the entry only.

## Breakpoints and layout
- Mobile first: 390, 768, 1024, 1440. Max content width 1440; gutters 16 / 24 / 40 / 56; columns 4 / 8 / 12 / 12.
- Every page works at 320 px wide and at 200% zoom.
