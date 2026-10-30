# Build progress: darkestshades.com

The memory of the build run (`docs/build/RUN.md`). Re-read after every compaction. Dates are 2026.

## Checks failing for environment reasons

- **Stand-in type.** Owners Wide and Stolzl are not licensed yet (`00-decisions.md` #41, O8). Every screenshot and visual baseline in this run renders their open-licensed stand-ins, Mona Sans and Urbanist (`brand/fonts/README.md`). The font check passes on the stand-ins by design; baselines are remade when the real fonts arrive.
- **The production build refuses by design.** `npm run build` fails the draft-copy gate while any section of `content/copy/en.json` is `draft` or `placeholder` (today: every section). This is the gate working, not a broken build. Review builds (`npm run build:review`) carry production settings and allow drafts; Lighthouse and the screenshots run on them.

(Anything else that cannot pass in this environment is listed here with its reason before a phase is called done.)

## Phases

| Phase | State | Branch · PR | Evidence | Date |
|---|---|---|---|---|
| 0 Foundation | **done** | `build/phase-0-foundation` · PR #1 | See *Phase 0 evidence* below | Oct 30 |
| 1 Wireframes | **done** (checkpoint PR #2) | `build/phase-1-wireframes` · PR #2 | See *Phase 1 evidence* below | Oct 30 |
| 2 Base components | not started | | | |
| 3 House layer | not started | | | |
| 4 UI pages | not started | | | |
| 5 Photography | not started | | | |
| 6 QA and hand-off | not started | | | |

## Now and next

- **Now:** phase 1 is done and merged (the first review checkpoint: PR #2 carries the review note). Phase 2 (base components) starts on `build/phase-2-base` from the new `main`.
- **Next:** every base component in `05` with a story per state (hover, active and focus-visible forced for the stories), 390 and 1440, UI and wire, axe passing; unit tests for the bag math, the quantity limit and the price; then phase 3.

### Phase 1 evidence (Oct 30)

What was built: the page shell (`PageShell`: skip link, `Header` per breakpoint, `DropLine`, `Footer`, `MenuSheet`, `BagDrawer`), the base bones (`Button`, `TextLink`, `Field`, `Check`, `Price`, `Quantity`, `Gallery`, `Sheet`, `BagLine`, `BagSummary`, `Notice`, `Disclosure`, `SkipLink`, `VisuallyHidden`), the house bones (`LookNumber`, `DropStatus`, `Countdown`, `PairsLeft`, `StageCard`, `SpecSheet`, `LineDrawing`, `Manifesto`, `DetailHold`, `ScaleCut`, `CastFrame`, `ListForm`, `ListOffer`, `SensoryNotice`, `Entry`), the bag as local state in cart-API shape, the entry's gating, wire mode (`?mode=wire` or `ds_mode=wire`), every template in `04` as a page component with a route and a Storybook "Pages" story, and the capture job that makes the review set.

| Done criterion | Command | Result |
|---|---|---|
| Every template in `04` at 390 and 1440 in wire mode, every image a labelled `ShotSlot` | `npm run capture:wire` (Playwright project `capture`, against the review build and the static Storybook) | 92 captures: `docs/wireframes/{page}-{390,1440}.png` for home, drop, frames, frame (F01), frame (F08, the GCD render in the detail hold), manifesto, cast, questions, care, policies, policy (exchange), accessibility, bag, account, 404; and `docs/wireframes/states/` for every Pages story: the drop announced without a date (today's data), announced with a date, live, sold out, ended; frames with a live drop; the frame page with a live drop and sold out; frames with a sold-out drop; the bag empty and with two lines (page and drawer); the menu sheet; the list pop-up; the photosensitivity notice; the entry as a frame list; accessibility with the intro on and off; 404 |
| Real copy and real product data from the start | the routes read `context.store` and `content/copy/en.json` only | numbers for states today's data lacks live in `app/lib/mock/fixtures.ts`, imported by stories and tests only (`checks/layers.mjs` enforces it) |
| A Storybook "Pages" section | `npm run storybook:build` | 44 stories: Pages/Templates (25), Pages/Overlays (6), the phase 0 components (13) |
| Checks | `npm run typecheck`, `npm run lint`, `npm test`, `npm run checks` | all exit 0; 24 unit tests; the copy gate reports 21 unapproved sections (every new section is marked draft) |
| Playwright | `npx playwright test` | **214 passed** (and a second run against the committed baselines: 214 passed): the font check; the token sheet at 390 and 1440 in UI and wire; axe on 16 routes (every template) at 390 and 1440, no serious or critical issues; 44 stories × 390/1440 × UI/wire with axe in UI mode. Baselines in `tests/e2e/__screenshots__/` (1×, stand-in type) |
| Independent review | two agents that did not build it: a code review against `CLAUDE.md`, `00-decisions.md`, RUN Part 1 and the done criteria; a screenshot review of the whole set side by side | findings fixed in this phase (see the decision log); the PR carries the review note |

Screenshots looked at: every page at 390 and 1440 in wire mode, and the states above. Header and footer the same on every page; the drop line on every page while announced; one statement per first screen; products on labelled 4:5 slots, heroes 3:2; the frames and drop grids 1 across at 390 and 4 at 1440 with look numbers 01–09 and no 07.

### Phase 0 evidence (Oct 30)

What was built: Hydrogen (create-hydrogen 5.0.40 starter: TypeScript, Tailwind v4, React Router 7.16) at the repo root, with every Shopify call removed (no Storefront, cart or customer-account client, no `storefrontRedirect`, no analytics, no preconnects, no starter routes); `server.ts` runs React Router's request handler with a Shopify-free context (`app/lib/context.ts`: the mock store, settings, the request clock). The mock adapter (`app/lib/mock/`) builds Storefront-shaped products, variants, images, a drop metaobject and the cast from `content/products/`, `content/drops/`, `content/photography/people/` and `assets/photography/MANIFEST.csv`, all imported at build time. Tokens: `design/tokens/build/*.css` through Tailwind v4 with the default palette off and `ds-` role colors. Fonts: the stand-ins from npm, `font-display` sets the variation axes. Marks: `Logo`, `BrandMark`, `Seal` (three size steps), `ShotSlot`. Storybook 10 with mode and theme globals. Playwright 1.63 (the preinstalled Chromium), axe, Vitest 5. `tools/flashcheck.py`. The CI checks in `checks/` and `.github/workflows/ci.yml`. The token sheet at `/dev/tokens` (dev and review builds only).

| Done criterion | Command | Result |
|---|---|---|
| Dev server shows the token page with both fonts loaded | `npm run dev` → `/dev/tokens` | 200; the Playwright font test logs every role rendered by `Mona Sans Variable 200–900` (display) and `Urbanist Variable 100–900` (text, weights 300/350/400/500); no system type |
| Storybook runs | `npm run storybook:build` | 13 stories (Logo ×3, BrandMark ×2, Seal ×4, ShotSlot ×4), `storybook-static/` 42 MB |
| One screenshot test passes at both sizes | `npx playwright test` | **64 passed**: `tokens.spec.ts` at 390 and 1440 in UI and wire mode; `fonts.spec.ts`; `axe.spec.ts` on `/`, `/dev/tokens`, the 404 (no serious or critical issues); `storybook.spec.ts`, 13 stories × 390/1440 × UI/wire with axe in UI mode. 56 baselines in `tests/e2e/__screenshots__/` (1×, stand-in type) |
| Flash check | `python3 tools/flashcheck.py --self-test` | white strobe at 12/s: 6 flashes in a second at both viewports, **fails as it must**; dark strobe (every frame under 0.09): 0 flashes, passes → `OK`, exit 0. Without a sequence file it exits 2 and says the stills arrive in phase 3 |
| CI checks | `npm run checks` | strings ok (10 banned patterns over `app/`, `content/copy/`), hex ok, schema ok (8 product files), copy gate reports 17 unapproved sections, layers ok |
| Draft-copy gate | `npm run build` / `npm run build:review` | production build **refused** with `[copy-gate] production build refused: 17 section(s) … not approved`, exit 1; review build exit 0, `dist/client` 35 MB with `/photography/` copied in (777 files) |
| Types and lint | `npm run typecheck`, `npm run lint` | both exit 0 |
| Unit tests | `npm test` | 24 passed (copy gate, `fill`, products, images, cast, drops) |

Screenshots looked at (stand-in type): the token sheet at 390 and 1440 in UI and wire mode, the home placeholder (three manifesto lines) at both widths, the 404 at both widths. The night canvas, bone text, the stage color behind every product slot, square corners; the only golds on the sheet are the seal steps and the swatches, which is what a token sheet is for.

## Decision log

| Date | Decision | Why | PR |
|---|---|---|---|
| Oct 30 | The Hydrogen project root is the repo root (`package.json`, `server.ts`, `app/` at the top), not a nested folder. | `CLAUDE.md` and `09` name `app/routes/`, `app/components/base/` and `app/lib/mock/` as the real paths; RUN.md forbids `app/app/`. | phase 0 |
| Oct 30 | Build-time check scripts live in `checks/` (Node), not in `tools/` (Python) or `app/`. | The string check must sit outside `app/` and `content/copy/` so it never flags itself; `tools/` is the Python pipeline. | phase 0 |
| Oct 30 | The entry sequence is a JSON file (`assets/entry/sequence.json`) that both the player and `tools/flashcheck.py` read. | One source for what plays and what is measured, so the flash check tests the real order of frames. | phase 0 |
| Oct 30 | `server.ts` uses React Router's `createRequestHandler`, not Hydrogen's. | Hydrogen's handler throws without a Storefront client ("Storefront instance is required"), and this phase makes no Shopify calls. At launch, `createHydrogenContext` and Hydrogen's handler take over; the routes don't change. | phase 0 |
| Oct 30 | `@playwright/test` and `playwright-core` pinned to 1.63.0. | The VM's preinstalled Chromium is revision 1243 (Playwright 1.63); axe's newer `playwright-core` would otherwise type `Page` differently. | phase 0 |
| Oct 30 | The image library is served as static files from `/photography/` (a Vite plugin: dev middleware, then a copy into `dist/client`), not imported file by file. | 779 files; stable URLs that swap for the Shopify CDN at launch; `MANIFEST.csv` stays the register, read once at build time. | phase 0 |
| Oct 30 | Storybook has its own Vite config; size and mode are globals (390/1440, UI/wire), and the Playwright matrix renders every story in all four. | One story per state, as `05` asks, without four copies of each story. | phase 0 |
| Oct 30 | The token sheet is a route, `/dev/tokens`, available on the dev server and in review builds only. | The phase 0 done criterion needs it in the app; a production build 404s it. | phase 0 |
| Oct 30 | `tools/build_tokens.py` also emits Tailwind's `--default-font-family`, `--font-display--font-variation-settings`, weights, leading, tracking and aspect ratios. | So utilities like `font-display`, `leading-manifesto`, `tracking-micro` and `aspect-stage` come from the tokens, and no component repeats a value. | phase 0 |
| Oct 30 | Hydrogen's React Router type augmentation is off; `env.d.ts` types the context as `DsLoadContext`. | The starter's types assume `storefront`, `cart` and `customerAccount` on every request. | phase 0 |
| Oct 30 | The frames grid is 1, 2, 4 and 4 columns at 390, 768, 1024 and 1440, not 3 at 1024. | `04` says 3 at 1024, but `06-products.md` says F04, F05 and F09 never sit side by side in a row of three, and the eight in look order put F04 and F05 together in a 3-wide row. Four across keeps look order and the rule. `00-decisions.md` is silent, so `06`'s product rule wins the layout call. | phase 1 |
| Oct 30 | Pages are components (`app/components/pages/`) that routes and Storybook "Pages" stories both render. | The review set needs every state a page can be in; states today's data lacks (a drop with a date, live, sold out, ended, a full bag) come from `app/lib/mock/fixtures.ts` in stories only, never from a route. | phase 1 |
| Oct 30 | The home and drop pages hide the footer's list form. | Both carry their own sign-up (home's list section; the drop's "Get notified"), and the same form twice on one page is noise. Set per route in `handle.footerList`. | phase 1 |
| Oct 30 | Wire mode is `?mode=wire` or the cookie `ds_mode=wire`; the review set is made by `npm run capture:wire` (a Playwright project, `tests/capture/`). | One switch for the whole site; the capture job shares the test runner's servers and viewports. | phase 1 |
| Oct 30 | The bag is client state in Storefront cart shape (`app/lib/cart.tsx`, localStorage), with the drawer as a side sheet and `/cart` as a page. | No checkout and no Shopify cart this phase; the components read the shape Hydrogen's cart handler returns, so the swap at launch is in one file. | phase 1 |
| Oct 30 | The entry's gating lives in `app/lib/entry.ts` and the home loader: first visit to `/` only, no utm/fbclid/gclid, not a bot, no `ds_entry` cookie; the Accessibility page's switch sets `ds_entry=off` for a year. | `03-references.md`; the cookie doubles as the "turn the intro off" control `04` asks for. | phase 1 |
| Oct 30 | The policy pages show their title, the settled promise where one applies, and one draft line; `/policies` lists them. | The legal text comes from Shopify at launch; nothing legal is drafted (RUN.md, phase 4 notes). | phase 1 |
| Oct 30 | `/cast` shows nothing about who the seven are: the portrait and the frame they wear, linked. | The open question's default (RUN.md, Open questions). | phase 1 |
| Oct 30 | The header reads "Bag" when the bag is empty and "Bag (n)" with lines in it. | "Bag (0)" on every first visit is noise; the count appears when it means something. | phase 1 |
| Oct 30 | A bag line shows the unit price ($100) and, from two pairs on, the line total beside it. | The price is always visible (CLAUDE.md); a line total alone would read as a different price. | phase 1 |
| Oct 30 | F08's detail hold shows the GCD's 3D render through a `ShotSlot` labelled `GCD-3D-YAW35 · 3:2`, never an F08 picture. | `00-decisions.md` #34; every image goes through `ShotSlot` (`05`). | phase 1 |
| Oct 30 | The reading measure token is `30em`, not `68ch`. | `ch` is the width of a zero; `68ch` set about 92 letters of Urbanist per line. `30em` is about 68 characters of body text (`04`: no line longer than 68 characters). Changed in `tokens.base.json` and rebuilt. | phase 1 |
| Oct 30 | Wire mode keeps the marks (the seal in greyscale) and labels only photographs; slot labels shrink with the slot and never wrap. | The seal is a drawing, not a shot; a wrapped "GCD · 1632:589" read as debris. Set in `tools/build_tokens.py` (wire.css). | phase 1 |
| Oct 30 | The 404 and any error keep the page shell (header, drop line, footer). | `04` puts the drop line under the header on every page, and the nav and bag stay reachable. Route and story now match. | phase 1 |
| Oct 30 | The drop page shows no drop line: its status block says the same thing in full. | Three statements of one fact in the first screen; `handle.dropLine` per route. | phase 1 |
| Oct 30 | The photosensitivity notice reads Continue · Skip intro in that order; focus starts on Skip intro. | The order is the brief's (`03`, `08`); focusing Skip keeps the safer choice one keypress away. | phase 1 |
| Oct 30 | The detail hold's picture is sized by the viewport height, so the long view fits one screen on desktop. | RUN Part 1: one long held view; a 4:5 picture at 768 px wide ran past a 900 px screen. | phase 1 |
| Oct 30 | The phase ends with an independent code review (an agent that did not build it) and a screenshot review; its findings are fixed before the PR. | RUN.md, Orchestration. The phase 1 code review found 5 blocking items (the phone header showing both marks, a `<p>` inside the spec `<dl>`, stories needing a data router, a hung image wait at 390, the missing review set) and 8 should-fix items (hard-coded aria labels, the bag line's price, 44 px targets, the sheet's focus effect, the entry's interval, a fixtures guard, 404 and accessibility stories, axe over every route); all fixed in this phase. The screenshot review found 3 must-fix items (the reading measure, the seal's wire label, the 404 shell), 11 should-fix items (the stretched status block, empty columns on live/sold-out/ended, the detail hold's height, floating drawing captions, the story clock at 390, overlay captures, the Drop nav state, Next look's heading, the cast page's top gap, a frame sold-out story) and 13 notes for phase 4; everything but the phase 4 notes fixed here. | phase 1 |

## Questions for Antaeus

| Question | Default in use | Needed by |
|---|---|---|
| The drop line says "Open" (`drop.line.live`, from RUN Part 1) while the status word says "Live" (`drop.stateWords`, from `04`). Which word? | Both as drafted: "Open" in the one-line status, "Live" as the state word. | The UI pages review (phase 4) |
| `accessibility.body[1]` says the opening never plays with reduced motion; `03` and the player show the text cards only. Reword, or make reduced motion skip the opening entirely? | The player shows cards only; the sentence stays as drafted for sign-off. | The UI pages review (phase 4) |
| Does the header show "Bag (0)" or plain "Bag" when the bag is empty? | Plain "Bag" at zero. | The UI pages review (phase 4) |

## Copy to sign off

Strings added to `content/copy/en.json` during the build, by section.

| Section | Key | String | Why | Phase |
|---|---|---|---|---|
| `error` (new, draft) | `title` | Something went wrong. | The error boundary needs a line for a failure that isn't a 404. | 0 |
| `error` | `link` | Back to Darkest Shades | Same as `notFound.link`, kept separate so each can change. | 0 |
| `alt` | `seal` | The God Cloud Device: a gold band set with black onyx. | Alt text for the GCD seal when it isn't decorative. | 0 |
| `frames` (new, draft) | `title`, `statement` | Frames · Eight frames. One price: $100. | The frames page's one statement line (`04`); nothing in `en.json` covered it. | 1 |
| `drop` | `heading` | Drop {number} | The display line at the top of the drop page. | 1 |
| `drop` | `stateWords` | Announced · Live · Sold out · Ended | The status block's state word (`04`). | 1 |
| `drop` | `pairsPerFrame`, `pairsTotal` | {pairs} pairs per frame · {total} pairs in all | The status block's quantities, shown only with real numbers. | 1 |
| `drop` | `archive` | Past drops | Heading over earlier drops on a drop page. | 1 |
| `product` | `availability` | In Drop {number} · Sold out · Next drop | The availability word on a stage card (`04`). | 1 |
| `product` | `galleryLabel`, `galleryCounter`, `galleryPrevious`, `galleryNext` | Pictures of {name} · {index} / {total} · Previous picture · Next picture | The gallery's accessible name, counter and arrows. | 1 |
| `product` | `drawnViews` | Front · Side · Top | Captions under the technical drawings. | 1 |
| `nav` | `bagWithCount` | Bag ({count}) | The header's bag control with its count. | 1 |
| `bag` | `checkout`, `quantity` | Checkout · Quantity | The disabled checkout button and the stepper's label. | 1 |
| `questions`, `care`, `accessibility` | `title` | Questions · Care · Accessibility | Page titles. | 1 |
| `accessibility` | `introToggle.saved` | Saved. | Confirmation after the intro switch. | 1 |
| `policies` (new, draft) | `title`, `pending`, `items.*`, `lines.exchange`, `lines.warranty` | Policies · The full text is published at launch. · Shipping, Exchange, Warranty, Privacy, Terms, SMS terms · Exchange within 45 days. · Six months of warranty against defects and scratches. | The policy pages before Shopify's text; the two lines restate settled promises (`00-decisions.md` #26). | 1 |
| `account` (new, draft) | `title`, `pending` | Account · Accounts open at launch. | The `/account/*` placeholder. | 1 |
| `cast` (new, draft) | `title` | Cast | The cast page's title. | 1 |
| `alt` | `lineDrawing`, `views` | Technical drawing of {subject}, {view}. · front view, side view, from above, three-quarter view | Accessible names for the drawings. | 1 |
| `bag` | `quantityFewer`, `quantityMore` | Fewer · More | The stepper's two buttons, for screen readers. | 1 |
| `entry` | `burstLine`, `layouts` | {count} frames at {fps} a second, {layout} · framed, full bleed | The entry's frame list in wire mode. | 1 |
| `footer` | `navLabel` | Footer links | The footer's link columns, for screen readers. | 1 |
| `nav` | `primaryLabel` | Primary | The header's navigation, for screen readers (the menu sheet is "Menu"). | 1 |

## Before launch

Filled in during phase 6.
