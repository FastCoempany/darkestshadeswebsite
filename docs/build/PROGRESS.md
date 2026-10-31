# Build progress: darkestshades.com

The memory of the build run (`docs/build/RUN.md`). Re-read after every compaction. Dates are 2026.

## Checks failing for environment reasons

- **Stand-in type.** Owners Wide and Stolzl are not licensed yet (`00-decisions.md` #41, O8). Every screenshot and visual baseline in this run renders their open-licensed stand-ins, Mona Sans and Urbanist (`brand/fonts/README.md`). The font check passes on the stand-ins by design; baselines are remade when the real fonts arrive.
- **The production build refuses by design.** `npm run build` fails the draft-copy gate while any section of `content/copy/en.json` is `draft` or `placeholder` (today: every section). This is the gate working, not a broken build. Review builds (`npm run build:review`) carry production settings and allow drafts; Lighthouse and the screenshots run on them.

- **Pixel comparisons run on this VM, not on GitHub Actions.** The runner renders type differently (hinting, antialiasing), so its screenshots never match baselines made here. RUN.md keeps visual tests on this machine; the CI job runs the same Playwright suite, asserts everything else (fonts, axe, states, behaviour) and records its screenshots as an artifact instead of comparing them (`tests/e2e/helpers.ts`, `expectScreenshot`). The phase 0 merge's CI run failed on exactly these comparisons (and on the typegen bug in the copy gate, fixed in phase 1).

Running the final pass here: free ports 3000 and 6006 first (Playwright reuses whatever is listening), never set `CI` (it turns the pixel comparisons off), and recommit `docs/qa/lighthouse/` after the last Lighthouse run (it rewrites the reports and the date).

(Anything else that cannot pass in this environment is listed here with its reason before a phase is called done.)

## Phases

Each phase's evidence below is as recorded at that phase's merge (its counts of tests, stories and baselines are of that day); the *Final pass* section under "Now and next" is the state of the final tree.

| Phase | State | Branch · PR | Evidence | Date |
|---|---|---|---|---|
| 0 Foundation | **done** | `build/phase-0-foundation` · PR #1 | See *Phase 0 evidence* below | Oct 30 |
| 1 Wireframes | **done** (checkpoint PR #2) | `build/phase-1-wireframes` · PR #2 | See *Phase 1 evidence* below | Oct 30 |
| 2 Base components | **done** | `build/phase-2-base` · PR #3 | See *Phase 2 evidence* below | Oct 30 |
| 3 House layer | **done** | `build/phase-3-house` · PR #4 | See *Phase 3 evidence* below | Oct 31 |
| 4 UI pages | **done** | `build/phase-4-ui` · PR #5 | See *Phase 4 evidence* below | Oct 31 |
| 5 Photography | **done** | `build/phase-5-photography` · PR #6 | See *Phase 5 evidence* below | Oct 31 |
| 6 QA and hand-off | **done** | `build/phase-6-qa` · PR #7 (branched from phase 5's head and rebased on it after phase 5's review; PR #6 merged first, so PR #7 carries phase 6 alone) | See *Phase 6 evidence* below | Oct 31 |

## Now and next

- **Now:** the run is complete. Phases 0–6 are done and merged (PRs #1–#7); the final pass ran every check on the final tree and is recorded below (*Final pass*); PRs #8 and #9 carry the record and the Lighthouse reports.
- **Next:** the founder's part, in "Before launch": the questions, the copy sign-off, the fonts, the drop plan, the store connection.

### Final pass (Oct 31)

One pass, on commit `65503ca` (the final code; the only commits after it are this record and the Lighthouse reports it produced), every check in CI order, each with its exit status. The output as printed:

```
--- npm run checks ---                                                        exit 0
[check:strings] ok: none of 10 banned strings in app, content/copy
[check:hex] ok: no hex colors in app/
[check:schema] ok: 8 product files match product.schema.json
[copy-gate] 21 section(s) of content/copy/en.json are not approved (by design; see the top of this file)
[copy-audit] 7 note(s); ok: no exclamation marks, hype, gendered address or name-dropping; the fixed names and the tagline exact; the price written $100
[check:layers] ok: base imports nothing from house; no route or page component imports mock/fixtures
[flashcheck] sequence.json 1024x768: 40 states over 12.2s, max 1 flashes in any second (pass)
[flashcheck] sequence.json 390x844: 40 states over 12.2s, max 1 flashes in any second (pass)
--- npm run typecheck (react-router typegen && tsc --noEmit) ---              exit 0
--- npm run lint (eslint .) ---                                               exit 0
--- npm test ---                                                              exit 0
 Test Files  5 passed (5)
      Tests  59 passed (59)
--- python3 tools/flashcheck.py --self-test ---                               exit 0
[flashcheck] white-strobe: max 6 flashes in any second (FAIL) at both viewports, as it must
[flashcheck] dark-strobe: max 0 flashes in any second (pass) at both viewports, as it must
[flashcheck] self-test: white-strobe failed as it must; dark-strobe passed as it must -> OK
--- python3 tools/flashcheck.py --report docs/qa/flashcheck.json ---          exit 0
[flashcheck] sequence.json 1024x768 and 390x844: max 1 flashes in any second (pass)
--- npm run build (must refuse) ---                                           refused, as designed
[copy-gate] production build refused: 21 section(s) of content/copy/en.json are not approved
--- npm run build:review ---                                                  exit 0  (✓ built)
--- npm run storybook:build ---                                               exit 0  (Storybook build completed successfully)
--- npx playwright test tests/e2e/axe.spec.ts (16 routes × 390 and 1440) --- exit 0
  32 passed (49.8s); axe violation lines logged: 0
--- npx playwright test ---                                                   exit 0
  883 passed, 3 skipped by design (32.3m): every story at 390 and 1440 in UI and wire mode against the
  committed baselines with axe in UI mode, the fonts, the token sheet, axe on 16 routes, the widths,
  the opening, the house behaviours, the 404 titles, the keyboard pass
--- npm run lighthouse (asserting, on the review build) ---                   exit 0
[lighthouse] / (first visit: the notice over the page): performance 100, accessibility 100, best-practices 100, seo 100 | LCP 1.1 s, CLS 0.002, 312 KiB
[lighthouse] / (returning visitor): performance 100, accessibility 100, best-practices 100, seo 100 | LCP 1.1 s, CLS 0.001, 311 KiB
[lighthouse] /frames: performance 93, accessibility 100, best-practices 100, seo 100 | LCP 3.2 s, CLS 0.001, 375 KiB
[lighthouse] /frames/lou-went-underground: performance 96, accessibility 100, best-practices 100, seo 100 | LCP 2.6 s, CLS 0.002, 446 KiB
```

Lighthouse's performance scores move between runs on this shared machine (simulated throttling): across the passes of this day the frame page scored 96, 95, 96, 96, 90 and 96, and frames 93, 97, 93, 98 and 93; before the drawings moved to the server (phase 6) the frame page swung from 98 to 80 and 77, which is why they moved. The three skipped Playwright tests are the phone-only menu and gallery tests at 1440 and the desktop header test at 390. An earlier run of this pass, before the final tree, had one failure, a race inside the reduced-motion opening test, fixed in `4f53bef` (the test reads the entry's state in one step; the assertions are unchanged).

### Phase 6 evidence (Oct 31)

What was done: Lighthouse mobile on the review build (`checks/lighthouse.mjs`, reports in `docs/qa/lighthouse/`), the keyboard pass as a Playwright spec (`tests/e2e/keyboard.spec.ts`), the copy audit as a check (`checks/copy-audit.mjs`, in `npm run checks`), the honesty tests and the visual baselines confirmed, README "Start here" with how to run the app, and the "Before launch" list below.

| Done criterion | Command | Result |
|---|---|---|
| axe: no serious or critical issues | `npx playwright test` (axe on 16 routes at 390 and 1440; every story in UI mode) | no serious or critical issue in the final pass: 883 passed, 3 skipped by design (31.7m), every story at 390 and 1440 in UI and wire mode against the committed baselines, the fonts, the token sheet, the widths, the opening, the house behaviours, the 404 titles and the keyboard pass |
| Keyboard pass: the entry, menu, bag, gallery, pop-up, sign-up | `npx playwright test tests/e2e/keyboard.spec.ts` | 21 passed, 3 skipped by design (the phone-only menu and gallery tests at 1440, the desktop header test at 390): the notice (Skip intro focused first, Tab wrapping, Enter skipping, Esc skipping), Continue by Enter into the sequence with Skip focused, Tab staying on Skip and Enter skipping from the first frame; the skip link, mark, links and bag by Tab on desktop; the menu opening on Enter, wrapping both ways (Shift+Tab from Close to the last link, Tab from it back to Close), closing on Esc with focus back on its button; the bag from the header (focus inside, Esc, focus back) and a line's quantity up and down and removal by Enter; the gallery's arrow keys on a phone and the zoom control at both widths; the pop-up keeping focus inside, Not now reached by Tab, Esc, focus left on the page, the cookie; the sign-up filled, the consent checked by Space, every stop reached by Tab, sent by Enter |
| Lighthouse mobile ≥ 90 on Home, Frames and a frame page, with real images | `npm run preview:review -- --port 3000`, then `npm run lighthouse` (asserts) | On the final tree: home, first visit: performance 100, accessibility 100, best practices 100, SEO 100 (LCP 1.1 s, CLS 0.002, 312 KiB); home, returning visitor: 100, 100, 100, 100 (LCP 1.1 s, CLS 0.001, 311 KiB); /frames: 98, 100, 100, 100 (LCP 2.4 s, CLS 0.001, 375 KiB); /frames/lou-went-underground: 90, 100, 100, 100 (LCP 3.6 s, CLS 0.002, 446 KiB); the frame page's score ranged 90–96 over five runs of this pass. Home is measured twice: as a first visit, where the photosensitivity notice sits over the page and the opening (which plays only after Continue) is not measured, and as a returning visitor (`ds_entry=seen`), the page every deep link and later visit gets. Reports under `docs/qa/lighthouse/` |
| Entry assets under 1.5 MB | `du -b assets/entry`; the candidate sets from `sequence.json` | 627 KB on disk for every size and format of the 17 stills (69 files); a phone fetches one candidate per still: 93 KB with the smallest AVIFs, 208 KB with the largest AVIFs, 223 KB with the largest WebPs; the flash check on the same sequence passes (`docs/qa/flashcheck.json`) |
| Copy audit against `08` | `npm run check:copy-audit` | ok: no exclamation marks, hype, gendered address or name-dropping; the fixed names and the tagline exact; the price written $100; 7 notes (the S01 scene's "runway", a logged question; six sections without a status, which the gate counts as draft) |
| Honesty tests green; visual baselines committed | `npm test`; `git status` | 59 unit tests (the final pass's count too) (every missing-data case of the drop components, the availability word, the spec sheet, the stage card's pairs, the manifest); 189 stories × 390/1440 × UI/wire baselines committed |
| README "Start here" | `README.md` | how to run the app, Storybook, the checks, the review build and Lighthouse; the copy gate explained |
| "Before launch" | this file | the list below |

Stand-in type throughout.

### Phase 5 evidence (Oct 31)

What was built: the manifest reader is one function of the CSV text (`imagesFromManifest` in `app/lib/mock/manifest.ts`), so a new or replaced final needs no code change and the reader can be tested with rows that do not exist yet; no image or video was generated, no person composited, and the manifest was not hand-edited. No new final reached `main` since phase 4 (the last photography commit is "Cast: the nine approved on-model pictures in the image library"), so nothing new was wired: the 65 rows of `MANIFEST.csv` (56 product finals, 9 cast finals) are the library, and the 11 draft cast shots stay labelled slots.

| Done criterion | Command | Result |
|---|---|---|
| The site reads `MANIFEST.csv`; a new or replaced final needs no code change | `npm test` (`tests/unit/manifest.test.ts`) | A synthetic product row becomes the picture with its AVIF, WebP and JPEG sets from the `widths` column (unsorted widths sorted), its alt text, shot code, ratio and version; a synthetic cast row becomes the shot code the slots use; a draft row and a row for a frame the site does not sell stay out; an unknown angle sorts after the hero; a missing column is named; the folder and the manifest name exactly the same files (777 today) |
| Cast finals that reached `main` are wired; everything else a labelled slot | the same test; `git log origin/main -- assets/photography content/photography dam` | Nine cast pictures wired (W1-S07-F02-A1, W2-S06-F03-A1, W2-S06-F03-A2, W2-S06-F09-A2, M1-S06-F04-A1, M1-S06-F08-A1, M2-S07-F01-A1, M2-S07-F05-A1, NB-S06-F06-A1); the five studio portraits on `/cast` with M3 and W3 as labelled slots; eleven draft shots as slots; no new commit under the photography paths since RUN.md's Oct 28 baseline (the last is 0ed3270, the nine approved on-model pictures) |
| Types, lint, unit tests, checks | `npm run typecheck`, `npm run lint`, `npm test`, `npm run checks` | all exit 0; 59 unit tests |
| The pages | unchanged in this phase | the phase 4 baselines and review sets stand (862 Playwright tests at the phase 4 merge; 883 in the final pass) |

Stand-in type throughout.

### Phase 4 evidence (Oct 31)

What was built: every template in `04` composed from the phase 2 and 3 components with the real copy and the mock data; every product and cast picture through `ShotSlot` from `MANIFEST.csv` (AVIF, then WebP, then JPEG, with the manifest's widths as `srcset`, `sizes` per column, the manifest's alt text, lazy except the first); drafts as labelled slots (M3, W3 and eleven draft cast shots); F08's detail hold from the GCD's render; a title and a description on every route from `en.json` or the data; the home page's h1; the policy, account and 404 rules; stories for every state a route can reach; the UI review set.

| Done criterion | Command | Result |
|---|---|---|
| Every page at 390 and 1440 in UI mode, every state | `npm run capture:ui` | `docs/ui/`: 30 page captures (home, drop, frames, frame F01, frame F08, manifesto, cast, questions, care, policies, policy exchange, accessibility, bag, account, 404 at 390 and 1440) and `docs/ui/states/`: 86 state captures from the Pages and Overlays stories (the drop announced without and with a date, live, sold out, ended, with an archive; frames with a live and a sold-out drop; the frame page live, sold out, ended, without a drop, F08; the bag empty and full as page and drawer; the menu, the pop-up, the notice, the entry's frame list; the paper pages; 404 and 500) |
| Pictures through the manifest | `npm test` (`tests/unit/mock.test.ts`) and a read of the HTML | 65 manifest rows become `StorefrontImage`s with `srcset` per format from the `widths` column and the manifest's alt; every `<picture>` on the pages carries AVIF, WebP, then JPEG |
| Types, lint, unit tests, checks | `npm run typecheck`, `npm run lint`, `npm test`, `npm run checks` | all exit 0; 52 unit tests at the phase 4 merge (59 in the final pass; page meta, the frame description, the list's sentence and the Instagram link added); the copy gate lists the 21 unapproved sections as designed; the flash check passes |
| Every story at 390 and 1440, UI and wire, axe passing; the fonts, tokens, widths, opening and house-behaviour specs | `npm run storybook:build` then `npx playwright test` | 189 stories (57 Base, 89 House, 43 Pages); **862 passed** at the phase 4 merge (883 in the final pass, after phases 5 and 6 added the keyboard pass and the 404-title tests) against the committed baselines (100 baselines re-recorded for this phase's changes and 48 recorded for the twelve new stories); no serious or critical axe issue; no page overflows at 320, 720, 768 or 1024 |
| Independent reviews | a code review against the done criteria, a screenshot review of every capture against Part 1, `01`, `02`, `04`, `06` | code: 3 blocking and 8 should-fix items; screenshots: 3 must-fix, 5 should-fix and 11 notes; every A and B item fixed (decision log), the notes logged as questions or kept for phases 5–6 |
| Verification of the fixes | an adversarial pass: eight skeptics over the groups of fixes and a completeness critic (a workflow of nine agents) | Four residuals found and fixed: the 404 title branches in the leaf routes were dead code (only the root's meta runs when a loader throws; the title now comes from the root, with an end-to-end test over four missing paths), the cast page's `sizes` named 1280 px where this theme's `xl` is 1440, the next-look card inherited the grid's `sizes`, and the stage card's 44 px name link had loosened every card (now padding the margins give back). The critic's items done: the six remaining edge-case questions logged, slots for the frame's line and story, stories for home with a live, sold-out and ended drop and for frames ended and without a drop, the review sets re-captured after every fix, the redirect and the new baselines tracked |
| Screenshots looked at | the captures above, and ad-hoc screenshots at 320, 768 and 1024 against the review build | No horizontal overflow on any page at 320, 768 or 1024; the manifesto line whole at every width; the cast rows with no empty cell at 768, 1024 and 1440; the F08 hold on the canvas; the country select whole at 320 and 390 (the number beneath it under 360 px); the drawings bottom-aligned; the next look a full card |

Stand-in type throughout.

### Phase 3 evidence (Oct 31)

What was built: the opening from real stills (`tools/photo/entry_stills.py` → `assets/entry/`, 17 stills, 69 files, 748 KB, `sequence.json`), `Entry`, `Burst` and `Card` on a frame clock with the notice and skip rules, the detail hold's scroll push, the scale cut's one move, the header's transparent-to-solid change, the list pop-up's trigger and cookies, the list form's mock, film grain over cast photographs, the `surface-entry` role, stories for every house component and state, unit tests for every missing-data case, and Playwright specs for the opening and the house behaviours.

| Done criterion | Command | Result |
|---|---|---|
| The entry with the notice and the flash check | `python3 tools/photo/entry_stills.py --check` then `python3 tools/flashcheck.py --report docs/qa/flashcheck.json` | 17 stills, 28 + 8 cuts, 12.2 s; the phone set 91 KB (budget 1.5 MB); every dark file decodes under the ceiling (brightest pixel sRGB 77, relative luminance 0.074; the rule: 84, 0.09); flash check: max 1 flash in any second at 1024×768 and 390×844, exit 0 |
| The opening's behaviour | `npx playwright test tests/e2e/entry.spec.ts` | first visit: notice → cards → burst (a `/entry/b1-…` still) → logo → burst → end → the home page, cookie `ds_entry=seen`; Esc skips from the first frame; Skip intro; never on `?utm_source`, on `/frames`, or with the cookie; reduced motion shows cards only; the Accessibility page's Off sets the cookie for a year. 12 passed at 390 and 1440 |
| Honesty under unit test | `npm test` | 49 passed: `PairsLeft` (null, undefined, NaN, negative, threshold, no total), `Countdown` (no time, passed, invalid, undefined), `DropStatus` (no drop, no date, with a date, live with and without inventory, pairs made but inventory unknown, sold out, ended), `DropLine` (hidden states, real numbers only, the threshold), the availability word, the spec sheet's null rows, the stage card's pairs, a partial inventory is no total |
| House behaviours | `npx playwright test tests/e2e/behaviour.spec.ts` | the detail hold's `--detail-progress` and scale; the header transparent over the manifesto and solid past it; the pop-up at 60% scroll on a frame page and on home, never on a policy page, closed with Esc, `ds_offer=closed`; the bag drawer's focus trap and return; the list form's validation, consent and mock record. 12 passed at 390 and 1440 |
| Every house component and state as stories, at 390 and 1440, UI and wire, axe passing | `npm run storybook:build` then `npx playwright test` | at the phase 3 merge (the final pass: 189 stories, 883 passed): 177 stories (57 Base, 92 House, 28 Pages); **806 passed** against the committed baselines (177 × 390/1440 × UI/wire with axe in UI mode, the font check, the token sheet, axe on 16 routes at two widths, widths on nine pages at four widths, the opening and house-behaviour specs at two widths). No serious or critical axe issue |
| Types, lint, checks | `npm run typecheck`, `npm run lint`, `npm run checks` | all exit 0; `checks` now ends with the flash check |
| Independent review | a code review against `05`'s House table, `03`, `01`, `04`, `08`, CLAUDE.md | 4 blocking and 16 should-fix items, all fixed (decision log); its notes for phases 4–6 kept |

Stand-in type throughout.

### Phase 2 evidence (Oct 30)

What was built: every component in the Base table of `05` with every variant and state, as stories (57 base stories) that render at 390 and 1440 in UI and wire mode; hover, active and focus-visible as forced states; the phone field's country select (E.164); the gallery's zoom, loading and single states; the sheet's opening, open and closing states with a working focus trap; `ShotSlot`'s loading, loaded, error, empty and sequence states; the bag line's unit price and parked "removing" state; the summary's checkout URL for launch; two color roles for labels on the stage; unit tests for money, the bag's per-customer limit, E.164 and drop times; a widths test (320, 720, 768, 1024, nine pages); CI records screenshots instead of comparing pixels.

| Done criterion | Command | Result |
|---|---|---|
| Everything in the Base table, every state, both sizes, axe passing | `npm run storybook:build` then `npx playwright test` | at the phase 2 merge (the final pass: 189 stories, 883 passed): 97 stories (57 Base, 13 House from phase 0, 27 Pages); **462 passed** against the committed baselines (97 × 390/1440 × UI/wire with axe in UI mode, the font check, the token sheet, axe on 16 routes at two widths, the widths test on nine pages at four widths). No serious or critical axe issue |
| Types, lint, unit tests, checks | `npm run typecheck`, `npm run lint`, `npm test`, `npm run checks` | all exit 0; 31 unit tests at the phase 2 merge (59 in the final pass); `tools/palette.py` passes with the two new roles (`failures: 0`) |
| Independent review | a code review against `05`'s Base table, Behavior rules, `CLAUDE.md` and the done criterion | 4 blocking and 13 should-fix items, all fixed (decision log); its notes for phases 3–4 kept |

Stand-in type throughout.

### Phase 1 evidence (Oct 30)

What was built: the page shell (`PageShell`: skip link, `Header` per breakpoint, `DropLine`, `Footer`, `MenuSheet`, `BagDrawer`), the base bones (`Button`, `TextLink`, `Field`, `Check`, `Price`, `Quantity`, `Gallery`, `Sheet`, `BagLine`, `BagSummary`, `Notice`, `Disclosure`, `SkipLink`, `VisuallyHidden`), the house bones (`LookNumber`, `DropStatus`, `Countdown`, `PairsLeft`, `StageCard`, `SpecSheet`, `LineDrawing`, `Manifesto`, `DetailHold`, `ScaleCut`, `CastFrame`, `ListForm`, `ListOffer`, `SensoryNotice`, `Entry`), the bag as local state in cart-API shape, the entry's gating, wire mode (`?mode=wire` or `ds_mode=wire`), every template in `04` as a page component with a route and a Storybook "Pages" story, and the capture job that makes the review set.

| Done criterion | Command | Result |
|---|---|---|
| Every template in `04` at 390 and 1440 in wire mode, every image a labelled `ShotSlot` | `npm run capture:wire` (Playwright project `capture`, against the review build and the static Storybook) | 92 captures: `docs/wireframes/{page}-{390,1440}.png` for home, drop, frames, frame (F01), frame (F08, the GCD render in the detail hold), manifesto, cast, questions, care, policies, policy (exchange), accessibility, bag, account, 404; and `docs/wireframes/states/` for every Pages story: the drop announced without a date (today's data), announced with a date, live, sold out, ended; frames with a live drop; the frame page with a live drop and sold out; frames with a sold-out drop; the bag empty and with two lines (page and drawer); the menu sheet; the list pop-up; the photosensitivity notice; the entry as a frame list; accessibility with the intro on and off; 404 |
| Real copy and real product data from the start | the routes read `context.store` and `content/copy/en.json` only | numbers for states today's data lacks live in `app/lib/mock/fixtures.ts`, imported by stories and tests only (`checks/layers.mjs` enforces it) |
| A Storybook "Pages" section | `npm run storybook:build` | 44 stories: Pages/Templates (25), Pages/Overlays (6), the phase 0 components (13) |
| Checks | `npm run typecheck`, `npm run lint`, `npm test`, `npm run checks` | all exit 0 at the phase 1 merge; 24 unit tests then (59 in the final pass); the copy gate reports 21 unapproved sections (every new section is marked draft) |
| Playwright | `npx playwright test` | **214 passed** at the phase 1 merge (883 in the final pass; and a second run that day against the committed baselines: 214 passed): the font check; the token sheet at 390 and 1440 in UI and wire; axe on 16 routes (every template) at 390 and 1440, no serious or critical issues; 44 stories × 390/1440 × UI/wire with axe in UI mode. Baselines in `tests/e2e/__screenshots__/` (1×, stand-in type) |
| Independent review | two agents that did not build it: a code review against `CLAUDE.md`, `00-decisions.md`, RUN Part 1 and the done criteria; a screenshot review of the whole set side by side | findings fixed in this phase (see the decision log); the PR carries the review note |

Screenshots looked at: every page at 390 and 1440 in wire mode, and the states above. Header and footer the same on every page; the drop line on every page while announced; one statement per first screen; products on labelled 4:5 slots, heroes 3:2; the frames and drop grids 1 across at 390 and 4 at 1440 with look numbers 01–09 and no 07.

### Phase 0 evidence (Oct 30)

What was built: Hydrogen (create-hydrogen 5.0.40 starter: TypeScript, Tailwind v4, React Router 7.16) at the repo root, with every Shopify call removed (no Storefront, cart or customer-account client, no `storefrontRedirect`, no analytics, no preconnects, no starter routes); `server.ts` runs React Router's request handler with a Shopify-free context (`app/lib/context.ts`: the mock store, settings, the request clock). The mock adapter (`app/lib/mock/`) builds Storefront-shaped products, variants, images, a drop metaobject and the cast from `content/products/`, `content/drops/`, `content/photography/people/` and `assets/photography/MANIFEST.csv`, all imported at build time. Tokens: `design/tokens/build/*.css` through Tailwind v4 with the default palette off and `ds-` role colors. Fonts: the stand-ins from npm, `font-display` sets the variation axes. Marks: `Logo`, `BrandMark`, `Seal` (three size steps), `ShotSlot`. Storybook 10 with mode and theme globals. Playwright 1.63 (the preinstalled Chromium), axe, Vitest 5. `tools/flashcheck.py`. The CI checks in `checks/` and `.github/workflows/ci.yml`. The token sheet at `/dev/tokens` (dev and review builds only).

| Done criterion | Command | Result |
|---|---|---|
| Dev server shows the token page with both fonts loaded | `npm run dev` → `/dev/tokens` | 200; the Playwright font test logs every role rendered by `Mona Sans Variable 200–900` (display) and `Urbanist Variable 100–900` (text, weights 300/350/400/500); no system type |
| Storybook runs | `npm run storybook:build` | 13 stories (Logo ×3, BrandMark ×2, Seal ×4, ShotSlot ×4), `storybook-static/` 42 MB |
| One screenshot test passes at both sizes | `npx playwright test` | **64 passed** at the phase 0 merge (883 in the final pass): `tokens.spec.ts` at 390 and 1440 in UI and wire mode; `fonts.spec.ts`; `axe.spec.ts` on `/`, `/dev/tokens`, the 404 (no serious or critical issues); `storybook.spec.ts`, 13 stories × 390/1440 × UI/wire with axe in UI mode. 56 baselines in `tests/e2e/__screenshots__/` (1×, stand-in type) |
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
| Oct 30 | Hover, active and focus-visible are stories, through `@custom-variant` overrides that also match `data-force="hover"` and the like. | `05` asks for a story per state; a pseudo-class can't be set from a story, and duplicating hover styles would drift. | phase 2 |
| Oct 30 | The phone field is a country select plus the national number; the form sends E.164 (`+14155550123`). | `05` Field: "phone (E.164 with country select)". Eighteen dial codes to start; the provider's list replaces it at launch. | phase 2 |
| Oct 30 | The gallery zooms to 2x inside its frame on a tap or Enter (pan by scrolling); pinch zoom is the browser's. | `05` Gallery states include `zoomed`; a tap is the keyboard-reachable equivalent of a pinch. | phase 2 |
| Oct 30 | `ShotSlot` has four states: loading (stage color, no label), loaded, error (the label in the error tone), empty (the label). A `sequence` variant labels a run of stills with its count. | `05` ShotSlot: image, sequence; loading, loaded, error, wire. | phase 2 |
| Oct 30 | `Sheet` has opening, open and closing states; only the side sheet (the bag) moves, 120 ms on desktop; full and center cut. | `05` Sheet; `05` Behavior rules (the bag drawer 120 ms, everything else a cut). | phase 2 |
| Oct 30 | `BagSummary` takes a `checkoutUrl`: null now (Checkout disabled, "Checkout opens at launch"), a live URL at launch. | `05` BagSummary states: default, checkout-disabled. | phase 2 |
| Oct 30 | Pixel comparisons run here; CI records screenshots and asserts everything else. | GitHub's runner renders type differently; see the top of this file. | phase 2 |
| Oct 30 | Two roles added through `tools/palette.py`: `text-on-stage` (onyx in both themes) for labels on the stage, and `status-error-stage` (error ink) for a failed picture's label. Both checked against the stage at 4.5:1. | The paper theme's `text-inverse` is bone, which would vanish on the stage; the night error tone fails AA on the light stage. | phase 2 |
| Oct 30 | Hover styles apply only where a pointer can hover (`@media (hover: hover)`), with `data-force` for stories. | A tap on a touch screen would otherwise leave hover styles stuck. | phase 2 |
| Oct 30 | Country names in the phone field come from `Intl.DisplayNames`; the component holds only codes and dial strings. | No English in components (CLAUDE.md); the provider's list replaces it at launch. | phase 2 |
| Oct 30 | The entry's stills come from `tools/photo/entry_stills.py`: 17 black-and-white stills from the finals (the eight frames at three-quarter plus F09's hero for burst 1; three cast finals and five product pictures for burst 2), AVIF and WebP at two sizes, into `assets/entry/` with `sequence.json`. Burst 1 is graded so no pixel passes relative luminance 0.09; burst 2 alternates one bright frame with two dark ones at 3 a second. | `03`, Assets and Safety; RUN.md phase 3 notes. The phone set is 93 KB with the smallest AVIFs (208 KB with the largest) (the budget is 1.5 MB). `tools/flashcheck.py` reads the same file: max 1 flash in any second at both viewports. | phase 3 |
| Oct 30 | The sequence file is imported at build time and the files served from `/entry/` (the static plugin and Storybook's static dirs). | MiniOxygen has no file system; the player, the flash check and the stories read one source. | phase 3 |
| Oct 30 | The entry's grounds use the role `surface-entry` (pure black), added through the palette tool. | `01`: pure black is kept for the logo and the entry; the canvas is onyx. | phase 3 |
| Oct 30 | The detail hold's push is `scale(1 + (push − 1) × progress)`, with the section's progress through the viewport set as a CSS variable and the push token 1 under reduced motion. | `03` reference 2 (1.00 to 1.06, scroll-linked); `05` Behavior rules (no push under reduced motion) with no JavaScript check of the preference. | phase 3 |
| Oct 30 | The list pop-up is a hook (`useListOffer`) in the page shell, enabled by the route handle on home, drop and frame pages: once per visitor, at 60% scroll past the first screen, never while the opening plays (`<html data-opening="playing">`), 30 days after closing, a year after signing up. | `04` Overlays; `08` honesty. | phase 3 |
| Oct 30 | Film grain is an SVG noise layer at 3.5% inside the slot of a cast photograph only, hidden under `prefers-reduced-transparency`; product pictures carry none. | `01` patina: over photography only, never the interface, off for product cut-outs. | phase 3 |
| Oct 30 | The luminance ceiling is verified on the files the browser decodes, not on the frames in memory; dark stills are graded with headroom (brightest pixel at 0.06) and encoded near-losslessly, WebP falling back to lossless; a failure writes no sequence and exits 1. | The phase 3 review measured the first lossy files at sRGB 85–108 (ringing). The shipped set now peaks at sRGB 77, relative luminance 0.074 (the rule: 84, 0.09). | phase 3 |
| Oct 30 | The notice and the opening are modal layers: Tab stays within them (Skip intro · Continue; Skip alone), the page behind does not scroll, Esc skips. | `05` Accessibility: the skip control first in the tab order; `03` skip from the first frame. | phase 3 |
| Oct 30 | A card's words come from `en.json` by index; the sequence file keeps the text for the flash check only. | CLAUDE.md: all copy from `en.json`; a sign-off edit must not wait for the stills tool to run again. | phase 3 |
| Oct 30 | The stills are preloaded with the same `srcset` and `sizes` the bursts render, so 2× screens fetch the candidates they will show. | `03` Assets: preloaded during the first card. | phase 3 |
| Oct 30 | The scale cut arms when the small composition is at least 90% on screen and the scroll has settled for 300 ms; the next scroll, swipe, key or tap cuts. | `03` reference 3 and RUN Part 1 "Feel": stillness, then one cut, on the visitor's move inside it. | phase 3 |
| Oct 30 | The header turns solid once the manifesto's bottom has passed the top of the screen. | `04` Navigation: transparent over the entry end card and the manifesto, night surface after. | phase 3 |
| Oct 30 | The drop line applies the pairs-left threshold like `PairsLeft`; a partial inventory record is no total; when a countdown reaches zero the loaders run again and the state comes from data, never flipped client-side. | `05` honesty rules; RUN phase 3 (the threshold); `05` Countdown "stops at zero and switches the state". | phase 3 |
| Oct 30 | The consent texts link to the Privacy and SMS terms pages under the checkbox. | `05` ListForm "consent checkbox and terms link"; `08`. | phase 3 |
| Oct 30 | The phase 3 code review found 4 blocking items (the ceiling verified on the wrong artifact, no focus containment on the overlays, two missing stories, the burst bypassing a labelled slot) and 16 should-fix items; all fixed in this phase. Its notes for phases 4–6 are kept in its report. | RUN.md, Orchestration. | phase 3 |
| Oct 30 | The phase 2 code review found 4 blocking items (story typing, two contrast failures, a load race that left product images invisible on fast loads, a focus trap that never engaged) and 13 should-fix items; all fixed in this phase. The reviewer's notes for phases 3–4 are kept in its report. | RUN.md, Orchestration. | phase 2 |
| Oct 30 | The phase ends with an independent code review (an agent that did not build it) and a screenshot review; its findings are fixed before the PR. | RUN.md, Orchestration. The phase 1 code review found 5 blocking items (the phone header showing both marks, a `<p>` inside the spec `<dl>`, stories needing a data router, a hung image wait at 390, the missing review set) and 8 should-fix items (hard-coded aria labels, the bag line's price, 44 px targets, the sheet's focus effect, the entry's interval, a fixtures guard, 404 and accessibility stories, axe over every route); all fixed in this phase. The screenshot review found 3 must-fix items (the reading measure, the seal's wire label, the 404 shell), 11 should-fix items (the stretched status block, empty columns on live/sold-out/ended, the detail hold's height, floating drawing captions, the story clock at 390, overlay captures, the Drop nav state, Next look's heading, the cast page's top gap, a frame sold-out story) and 13 notes for phase 4; everything but the phase 4 notes fixed here. | phase 1 |
| Oct 31 | The home page's h1 is the first manifesto line, visible and set like the other lines; the manifesto page's statement spans the content width, and every display line's type is capped at 10cqi of its container so no word ever breaks (at 320 px the widest word, "PERFORMANCE.", measures 8.9 em in the stand-in face; re-measure with Owners Wide). | The home page had no h1 (`05` Accessibility); the tagline broke inside "EVERYTHING." in the reading column at 1440 (`01` Type, `02` "type is the image"). | phase 4 |
| Oct 31 | The manifesto page is frontal and centred like the other paper pages: the label, the statement across the content width, the numbered paragraphs in a centred measure. The display line's cap is a component class (`.ds-manifesto-line`) with the token's size first, so a browser without container units keeps the token. | Part 1 Layout "frontal and centered"; the un-centred paragraph column read as a regression next to the reading pages; progressive enhancement. | phase 4 |
| Oct 31 | The frame page carries slots for the frame's `copy.line` (under the descriptor) and `copy.story` (after the detail hold) that render nothing while the data is null. | `02` §1 ("the frame and one line, then the facts"), `01` Type (body large: product story); the founder's words land without a code change; the honesty rule holds. | phase 4 |
| Oct 31 | Next look is a stage card. | The same card anatomy everywhere; $100 wherever a product shows (Part 1 Honesty); the old card described the current frame to screen readers. | phase 4 |
| Oct 31 | Every route ships a title and a description through `pageMeta()`: the page's own where it has one (frames: its statement; a frame: `meta.frameDescription` from its name, descriptor and price; a drop: its status sentence), else the site's. When a loader throws, only the root's meta runs (the matches stop at the error boundary), so the root titles the 404 and the error page. | React Router keeps only the leaf's descriptors, so most pages shipped no description; descriptions come from `en.json` or data, never typed into a route. | phase 4 |
| Oct 31 | Cast captions carry the price; the image disclosure sits under both cast grids; the cast page's `sizes` match its columns. | $100 wherever a product shows; `08` "Image disclosure on on-model images"; images fetched at the width they render. | phase 4 |
| Oct 31 | Seven portraits sit two, three, then four across with the last row centred (an eight-column grid, each portrait two columns wide), so no cell stays empty. | The empty last cell read as a missing picture next to the two real labelled slots (Part 1 Layout, "compositions frontal and centered"). | phase 4 |
| Oct 31 | The bag drawer and page render nothing until the stored bag has been read on the client (`ready`). | The server never knows the lines, so it must never say the bag is empty (honesty; `05` BagLine states). | phase 4 |
| Oct 31 | 44 px hit areas on the stage card's name and the cast caption (padding the margins give back, so the card keeps its rhythm) and on the policy index links (`min-h-11`). | `05` Accessibility: 44 px targets; every other link already had them. | phase 4 |
| Oct 31 | F08's detail hold sets the GCD render straight on the canvas (`ShotSlot surface="bare"`, forced `loaded`) at 70% of the hold's width. | RUN.md Edge cases: the render instead of a photograph; Part 1 Feel: the GCD the only warm color on a dim screen; the slot label is wire mode only. | phase 4 |
| Oct 31 | The phone field's country select takes the width of its longest option. | "United States +1" was cut under the chevron on every list form (`05` Field). | phase 4 |
| Oct 31 | The three drawings are bottom-aligned with the measurements straight under them. | At true scale the top view is far deeper than the front and side; top alignment left an empty block (`04` §5). | phase 4 |
| Oct 31 | A sold-out drop page shows the disabled "Sold out" control on each card, like the frame page. | `04` drop template: the disabled state while sold out. | phase 4 |
| Oct 31 | The gallery offers no zoom control on a labelled slot; a stage-card hover never shows a slot label in UI mode. | There is nothing to zoom; labels are wire mode only. | phase 4 |
| Oct 31 | The cast cells inside a frame's gallery stay on the stage color (the gallery's rule); the "Worn by" pictures sit on the canvas (people on the canvas). | `05` Gallery: images always on the stage; `01` Imagery: people on the canvas. Logged as a question so a cell never changes tone when a final lands. | phase 4 |
| Oct 31 | The drop page keeps no drop line (phase 1 decision) and the home list section keeps its one-sentence body while the footer's form has none; both put to the founder. | Part 1 says the line runs on every page; the drop page's status block says the same thing in full. | phase 4 |
| Oct 31 | `/drops` redirects to `/drop`; the list's sentence comes from one helper (`listBody`); the Instagram link is built from `meta.instagram`. | No dead URL under a live one; one source for the early-access rule (`08`, O6); one source for the handle. | phase 4 |
| Oct 31 | The review set stays at 390 and 1440 (RUN.md); no product grid has three columns at any width, so the three black squares never share a row of three; 1024 is covered by the widths test. | `06` "Telling the three black squares apart"; RUN.md "the review set at 390 and 1440". | phase 4 |
| Oct 31 | The phase 4 code review found 3 blocking items (the Next look link naming the wrong frame, no h1 on home, the bookkeeping) and 8 should-fix items; the screenshot review found 3 must-fix items (the broken tagline on the manifesto page, the F08 hold's label and size, the clipped country select), 5 should-fix items and 11 notes. Every A and B item is fixed in this phase; the fixes were then verified by an adversarial pass (one skeptic per group of fixes and a completeness critic) before the checkpoint PR. The notes for phases 5–6 are kept in the reports and the questions below. | RUN.md, Orchestration. | phase 4 |
| Oct 31 | The manifest reader is a function of the CSV text (`imagesFromManifest`); the module reads the committed manifest through it. | RUN.md phase 5: the site reads `MANIFEST.csv`; a test can prove a row that does not exist yet becomes a picture. | phase 5 |
| Oct 31 | Phase 5 wires nothing new: no final reached `main` since RUN.md's Oct 28 baseline, and the build makes no pictures of its own. | RUN.md phase 5: track 2 is not the build's to make; `tools/photo/export_web.py` writes the manifest. | phase 5 |
| Oct 31 | The reader keeps only `final` rows of the frames the site sells, puts an angle it does not know after the hero (never first, so a new angle cannot become a frame's featured picture), carries the manifest's `version` as a cache key on every URL (`?v=v02`, so a replaced final reaches a returning visitor through the immutable cache), and names a missing column. The tests state invariants (a final has its export, a draft stays a slot, the folder and the manifest name the same files) instead of pinning counts and codes that the next export would break. | The phase 5 review: "a new or replaced final needs no code change" has to hold for the tests too; `CLAUDE.md` Imagery (until finals land, every image is a labelled slot). | phase 5 |
| Oct 31 | The copy audit is a check (`checks/copy-audit.mjs`, in `npm run checks`): it fails on exclamation marks, hype, gendered address, name-dropping, lorem ipsum, a price not written "$100", "ultra-dark" as a spec, Title Case runs, and the fixed names or tagline wrong; a string with a logged question is noted, not failed, until the founder answers; sections without a status are the gate's business and appear as notes. | `08` Voice and Fixed names; `09` phase 6 "copy audit against 08"; RUN.md: never weaken a check (so the audit fails on real violations and notes the rest). | phase 6 |
| Oct 31 | The keyboard pass is a Playwright spec that runs with the suite (`tests/e2e/keyboard.spec.ts`): the opening's notice, the menu, the bag (from the header and a line's quantity), the gallery, the pop-up and the sign-up by keys alone. | `09` phase 6. | phase 6 |
| Oct 31 | Lighthouse runs against the review build with `checks/lighthouse.mjs` (mobile, simulated throttling); the summary and the HTML reports are committed under `docs/qa/lighthouse/`. | RUN.md phase 6: the review build carries production settings and allows drafts. | phase 6 |
| Oct 31 | The copy audit's exemptions are honoured only while PROGRESS.md's questions name the key; it also checks `08`'s legal and safety strings (the notice, the email and SMS consents' required elements, every SMS template starting with the brand and ending with the opt-out, the image disclosure), walks the product files and the drops for the voice rules (and "ultra-dark" never on F01, F03, F06 or F08), flags strings typed in capitals, and the hype list carries the fake-urgency phrases. | The phase 6 review: an allow-list must not be able to silence a finding; `08` Legal and safety copy; `08` Claims. | phase 6 |
| Oct 31 | Cookies carry `Secure` on https; wire mode works only on the dev server and review builds. | The phase 6 review: both were code the build could do now; `04` wire mode is a review tool. | phase 6 |
| Oct 31 | `npm run lighthouse` asserts (exit 1 under 90); home is measured as a first visit and as a returning visitor, and the summary records what each run saw. | The phase 6 review: the documented command could not fail, and the first-visit run measures the notice, not the opening. | phase 6 |
| Oct 31 | The phase 6 review found 3 must-fix items (axe evidence from a run on the branch, the PR bookkeeping, the README's prerequisites), 16 should-fix items (the keyboard pass's coverage of the entry, the wraps, the 1440 zoom, the pop-up and the consent; the copy audit's exemptions, legal strings, product files and capitals; the Lighthouse state and assertion; the entry-asset numbers; the launch list's product-data item and the two code items; the README) and 6 notes; all fixed in this phase but the notes, which are logged below. | RUN.md, Orchestration. | phase 6 |
| Oct 31 | A frame page's three drawings are read on the server for that frame only (`app/lib/drawings.ts`, in the route's loader) instead of all thirty-two inlined in the client chunk; stories keep an eager set of their own. | The frame page's chunk was 433 KiB and its Lighthouse performance swung from 98 to 77 between runs; it is 11 KiB now and the page scores 95–96 run after run (transfer 839 → 446 KiB). | phase 6 |

## Questions for Antaeus

| Question | Default in use | Needed by |
|---|---|---|
| The drop line says "Open" (`drop.line.live`, from RUN Part 1) while the status word says "Live" (`drop.stateWords`, from `04`). Which word? | Both as drafted: "Open" in the one-line status, "Live" as the state word. | The UI pages review (phase 4) |
| `accessibility.body[1]` says the opening never plays with reduced motion; `03` and the player show the text cards only. Reword, or make reduced motion skip the opening entirely? | The player shows cards only; the sentence stays as drafted for sign-off. | The UI pages review (phase 4) |
| Does the header show "Bag (0)" or plain "Bag" when the bag is empty? | Plain "Bag" at zero. | The UI pages review (phase 4) |
| `05` lists a 40 px button size and asks for 44 px targets. Keep the 40 px size? | Kept, with a 44 px hit area around it. | The UI pages review (phase 4) |
| Is a drop's per-customer limit per frame or per order? | Per line (frame): the stepper and the bag clamp each line to the limit. | Launch (with the drop plan) |
| The detail hold shows F09's A6 as it is (a lit print on the dark canvas); `03` describes a dim screen with the GCD as the only warm color. A darker grade would come from the photo pipeline. | The unaltered A6 final on its stage color. | The UI pages review (phase 4) |
| Burst 2's bright frames are the three cast finals on black (W1, M1, W2); the two cast pictures on white backdrops read very bright in black and white. Keep them, or grade them darker? | Kept as graded (one bright frame a second, as `03` allows). | The UI pages review (phase 4) |
| The drop's `statement` and each product's `copy.line` and `copy.story` are `null`, so the drop page shows no statement and the frame pages no line or story. Who writes them, and when? | Nothing shows (RUN.md: copy the data leaves null stays empty). | Launch |
| `{supportEmail}` has no value: `accessibility.body[2]` and the SMS HELP reply stay hidden. Which address? | Hidden. | Launch |
| How many GCDs may a screen show? The interface shows one gold element (the seal, or the "Live" word); a grid of frames shows several in the photographs, because the GCD is never left off a picture. | As stated (RUN.md Edge cases). | The UI pages review (phase 4) |
| F08's pictures show no GCD (`00-decisions.md` #34): its page's detail hold shows the GCD's 3D render on the canvas instead of a photograph. Keep? | The render (RUN.md Edge cases); never a GCD composited onto an F08 picture. | The UI pages review (phase 4) |
| The entry's stills are graded black and white and leave the stage color; they are not product presentations. Keep the stage rule off them? | Off (RUN.md Edge cases). | The UI pages review (phase 4) |
| Motion beyond the cuts: the gallery swipes on a phone and the bag drawer takes 120 ms on desktop; nothing else moves. Keep these two exceptions? | Kept (`04`, `05`). | The UI pages review (phase 4) |
| One picture per person on `/cast`: the five studio finals (W1, W2, M1, M2, NB); M3 and W3 stay labelled slots until their pictures land. | As stated (RUN.md Edge cases). | Phase 5 |
| Disabled text: graphite `#545454` is never text on dark; disabled controls use the disabled-text role (graphite-400). Keep? | Kept (RUN.md Edge cases; WCAG exempts inactive controls). | The UI pages review (phase 4) |
| The drop line without a date shows `drop.states.announcedNoDate` ("Drop 001. Date to be announced."). Keep the wording? | Kept (RUN.md Edge cases). | The UI pages review (phase 4) |
| The drop page shows no drop line (its status block says the same thing in full); Part 1 says the line runs on every page. Keep the exception? | No drop line on `/drops/*`. | The UI pages review (phase 4) |
| On a live drop the gold element is the word "Live"; `01` lists a "drop live" seal placement. The word, or a seal? | The word. | The UI pages review (phase 4) |
| The manifesto page sets the seventh paragraph ("See everything. Reveal nothing.") as the statement and numbers 01–06. Keep, or number all seven? | The seventh as the statement. | The UI pages review (phase 4) |
| The frame page shows the A6 twice: sixth in the gallery and in the detail hold. Keep, or a different crop for the hold (from the photo pipeline)? | Kept as `04` lists both. | The UI pages review (phase 4) |
| A bag line with quantity 2 shows "$100" and the line total "$200" side by side. Keep, or the unit price only with the total in the summary? | Kept (unit price, then the line total from 2). | The UI pages review (phase 4) |
| The reading pages centre their 68-character column while the footer sits at the gutter. Centre, or start the column at the gutter? | Centred. | Phase 6 |
| The home list section carries the one-sentence body; the footer's form has none. One presentation, or two? | Two: the fuller one on home. | Phase 6 |
| The cast cells inside a frame's gallery sit on the stage color; "Worn by" sits on the canvas. Which should the gallery use when a cast final lands? | The stage (the gallery's rule). | Phase 5 |
| `alt.scenes.S01` reads "on a runway" (`08`: no runway references on the site). No S01 picture exists yet, so nothing shows it. Reword? | Unused; the copy audit (phase 6) flags it. | Phase 6 |
| `care.body` is a placeholder ("Care instructions to be confirmed with the factory…") and renders as body copy on review builds; the gate blocks production until real care copy exists. | The placeholder on review builds only. | Launch |
| The consent texts say "Privacy Policy" and "SMS Terms" (Title Case) while the pages are titled "Privacy", "Terms" and "SMS terms". Which spelling? | As drafted (the consent texts name the documents, the pages carry short titles). | Copy sign-off |
| The S01 scene's alt text ("on a runway") describes a set that `07` itself calls a bare runway, while `08` bans runway references. An alt like "on a bare white floor against a black void" would satisfy both. | Unused; the audit notes it. | Copy sign-off |

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
| `list` | `countryLabel` | Country | The phone field's country select, for screen readers. | 2 |
| `product` | `galleryZoomIn`, `galleryZoomOut` | Zoom in · Zoom out | The gallery's zoom control, for screen readers. | 2 |
| `nav` | `opensInNewTab` | Opens in a new tab | Read after external links (Instagram). | 2 |
| `meta` | `frameDescription` | {name}. {descriptor}. {price}. Released in drops. | A frame page's meta description, filled from its data; the alt sentence described the photograph, not the product. | 4 |

## Before launch

What the founder and the launch wiring still need, in order: decisions, credentials and providers, plus the two small code items the build could not finish without them (items 10 and 12).

1. **Copy sign-off.** Every section of `content/copy/en.json` is `draft` or `placeholder` (and six carry no status): `npm run build` refuses until each is `approved`. The words the data still lacks: the drop's statement, each frame's `copy.line` and `copy.story`, the care page (a placeholder today), the support address (`{supportEmail}`), the S01 scene's alt text. The table "Copy to sign off" lists every string the build added.
2. **The questions above**, each with a default in use (Open vs Live, the drop line on the drop page, the gold element on a live drop, the manifesto's seventh paragraph, the A6 twice on a frame page, the bag line's two prices, the reading columns, the list sentence in two places, the gallery's cast cells, the detail hold's grade, burst 2's bright frames, the per-customer limit).
3. **Fonts** (`00-decisions.md` O8): Owners Wide and Stolzl through an Adobe Fonts kit (`PUBLIC_ADOBE_FONTS_KIT`) or the git-ignored local folder (`brand/fonts/README.md`). Then re-measure the manifesto's widest word for the 10cqi cap, re-record the baselines and the review sets.
4. **The drop plan** (O2): `content/drops/drop-001.json` (dates in `America/Chicago`, pairs per frame, the per-customer limit), the pairs-left threshold (`PUBLIC_PAIRS_LEFT_THRESHOLD`, `null` today), and whether the early window is real (O6: the customer-tag gate, else the list keeps its no-early-access sentence).
5. **The store connection.** `createHydrogenContext` and Hydrogen's request handler replace `server.ts`'s plain handler; Storefront API queries replace `app/lib/mock/` in the same shapes (products with `ds.*` metafields, the `drop` metaobject, per-variant inventory as the only source of pairs left, the `manifesto`, `list_offer`, `notice` and `promise` metaobjects); the bag becomes the cart API with the checkout URL on `BagSummary`; `/account/*` goes to Shopify accounts; Shopify's policy pages replace the placeholders; the image library moves to the Shopify CDN (the `/photography/` static route swaps for the CDN URLs the manifest ids map to).
6. **Email and SMS** (O7): `ListForm` posts to the provider instead of the `ds_list` mock (clear it), double opt-in and the `sms.*` templates with the provider's required wording, the support address in the HELP reply.
7. **Product data from the factory** (`content/products/*.json`, only with a source): the GCD's placement on F04's and F05's end-pieces (O3) and its metal and sizes (O4); the drawing numbering per frame (O9; each "Drawn" section shows the drawing stored on the frame); the size markings (O13; the spec sheet's `lens□bridge temple` values are measured from the 1:1 drawings until the factory's own marking replaces them); the production order (O11; the pages run in drop states and never promise stock).
8. **Pictures.** M3's and W3's portraits and the eleven draft cast shots through `tools/photo/export_web.py` (the manifest carries them; nothing in the app changes); the GCD's metal and sizes from the factory (O4) in the copy and the product data; cast stills for the entry's bursts once cast finals exist, then `python3 tools/photo/entry_stills.py --check` and `python3 tools/flashcheck.py` again.
9. **Cookies and privacy.** The site's cookies carry `Secure` whenever the page is served over https (done in phase 6: `cookieFlags` in `app/lib/cookies.ts`); the privacy and SMS terms come from Shopify; no analytics is installed, so no consent banner exists yet (add one with the first script).
10. **Production only.** Wire mode (`?mode=wire`, `ds_mode`) works on the dev server and review builds only (done in phase 6, `app/root.tsx`) and `/dev/tokens` 404s in production. The root's `shouldRevalidate` must revalidate when the search changes or a drop has times (today's data has none).
11. **Performance before launch.** Lighthouse mobile is at or above 90 on every measured page of the review build (the final pass's numbers are in the phase 6 evidence); what is left to tune if the production CDN changes the picture: the stage card's hover picture is lazy (preload it on the first cards), two cards below the first screen are marked priority, and `/frames` sits closest to the line (its first stage picture is the LCP).
12. **The last checks.** `npm run ci` green on the production build (the gate passes once the copy is approved), Lighthouse ≥ 90 on the production URL, axe, the flash check on the final sequence, the real fonts on the review sets. Pixel comparisons stay on this machine (top of this file).
