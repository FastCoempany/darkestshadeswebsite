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
| 1 Wireframes | not started | | | |
| 2 Base components | not started | | | |
| 3 House layer | not started | | | |
| 4 UI pages | not started | | | |
| 5 Photography | not started | | | |
| 6 QA and hand-off | not started | | | |

## Now and next

- **Now:** phase 0 is done and merged. Phase 1 (wireframes) starts on `build/phase-1-wireframes` from the new `main`.
- **Next:** the page shell (header, footer, menu sheet, bag drawer), every template in `04` in wire mode at 390 and 1440 with labelled `ShotSlot`s and real copy and data, every page state, `docs/wireframes/{page}-{390|1440}.png`, a Storybook "Pages" section, the checkpoint PR.

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

## Questions for Antaeus

| Question | Default in use | Needed by |
|---|---|---|
| None from phase 0. | | |

## Copy to sign off

Strings added to `content/copy/en.json` during the build, by section.

| Section | Key | String | Why | Phase |
|---|---|---|---|---|
| `error` (new, draft) | `title` | Something went wrong. | The error boundary needs a line for a failure that isn't a 404. | 0 |
| `error` | `link` | Back to Darkest Shades | Same as `notFound.link`, kept separate so each can change. | 0 |
| `alt` | `seal` | The God Cloud Device: a gold band set with black onyx. | Alt text for the GCD seal when it isn't decorative. | 0 |

## Before launch

Filled in during phase 6.
