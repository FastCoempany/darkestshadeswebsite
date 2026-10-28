# Build run: darkestshades.com, phases 0 to 6

I'm Antaeus, the founder; where the docs say "the founder", that's me. In this session you build the Darkest Shades site end to end: every phase of `docs/brief/09-build-plan.md`, 0 through 6, without stopping for me.

Part 1 is the brief I approved, the picture of what we're making. Part 2 is how to run the build. This file and `docs/build/PROGRESS.md` (you start it in phase 0) are your memory. Re-read both at the start of every phase and whenever you pick the work back up after a break or a compaction.

---

# Part 1 · The brief

Approved Oct 28 2026. It's the picture; `docs/brief/` has the detail. Where the two seem to disagree, `docs/brief/00-decisions.md` wins; note the conflict in PROGRESS.md.

## The site in one paragraph

darkestshades.com is a dark, still, gallery-like store for eight sunglasses at $100 each, sold in numbered drops. It states a position before it sells anything: the line **See Everything. Reveal Nothing.** set huge, then the frames shown like numbered pieces in an archive, the seven cast models, and the facts said plainly.

The mood is an early-90s Milan runway as it survives on film, held with a museum's restraint, with one decisive move at a time. Under it is a custom Shopify storefront (Hydrogen), dark by default, with every number on it real.

## Look

The site is dark by default. Each product sits on a pale stage, there is one gold accent per view, and type does the work a campaign photo would.

**Color.** It starts from Anastasiia's "Sustainable elegance" swatches and the GCD's gold and onyx, extended for a store. Every color pairing the site uses passes WCAG 2.2 AA.

| Role | Color | Where it goes |
|---|---|---|
| Canvas (night, the default) | Onyx `#050607` | Every page except long reading |
| Text | Bone `#E8E4DC`, a warm film white, not screen white | Body and display on night |
| Secondary text | Ash greys, `#8A8A8A` and lighter | Captions and meta. Graphite `#545454` only draws rules. |
| Stage | `#E4E2DD`, the cleaned lightbox backdrop | Behind every product image, in both themes |
| Gold | `#C6A36A` | One element per view: the GCD seal, a drop going live |
| Camel | `#BF835F` | Look and drop numbers, pull quotes. Never a button. |
| Paper | Bone `#F3F0E9`, onyx text | Manifesto page, questions, care, policies |

In `app/` these are role tokens (`--color-surface-*`, `--color-text-*`, `--color-action-*`, `--color-status-*`, `--color-border-*`, `--color-focus-ring`), never hex values.

**Type.** Only Anastasiia's two faces.

- Owners Wide Medium, uppercase: the manifesto lines (40 px on a phone, 120 px on desktop), section openers, headings.
- Stolzl: body (Book, 16 px), buttons and nav (Regular, Medium), small tracked labels, and the short centered sentences between the opening's bursts.
- Prices and specs use even-width figures at body size, never hidden or greyed down.

**Marks.**

- Anastasiia's horizontal logo goes in the desktop header and across the bottom of the footer.
- Her angular brand mark is the mobile nav and the favicon.
- The GCD is the house seal: footer, drop live, the product's detail view. It appears at most once per screen and never in the nav.

**Imagery.**

- Product: the cleaned lightbox set on the stage color, so each frame reads as a lit print on a dark wall. Cards show the front angle and swap to the three-quarter on hover.
- People: the seven cast members, wearing the real frames in plain studios and bare spaces. The look is film from an early-90s runway: hard flash, fine grain, lifted blacks, warm whites, muted color.
- A 3–4% film grain sits over photography only, never over the interface.
- Each frame's technical drawing is shown as vector line art with its measurements. It works as the archive layer.

**Layout.**

- One idea per screen: one statement, one image or one action.
- Compositions are frontal and centered, with a lot of dark space. Corners are square, and nothing decorative sits behind type.
- The grid is 4, 8, 12 and 12 columns at 390, 768, 1024 and 1440 px. The frames page goes from 1 card across on a phone to 4 on desktop.

## Feel

The site holds still and makes one decisive move at a time. Nothing slides in, loops or begs for attention.

**Stillness, then one cut.** Changes are hard cuts: no carousels, no slide-ins, hover changes instant or 120 ms. A section gets at most one deliberate move:

- **The scale cut.** A small, frontal composition (a frame on the stage, a horizon line, tiny type) cuts to full bleed on the visitor's first scroll. The visitor sets it off, never a timer.
- **The detail hold.** One long view of the temple with the GCD, the only warm color on a dim screen, pushing in slowly as the visitor scrolls (1.00 to 1.06). No arrows, no "new" badge, one line of copy at most.

**The opening** plays on the first visit to the home page only, about 12 seconds, built from still images rather than video:

1. Photosensitivity notice: Continue · Skip intro.
2. "See everything." on a charcoal screen.
3. A burst of about 28 dark-graded stills in a small frame, like prints on a wall, one image returning between the others.
4. "Reveal nothing.", then the stacked logo, held.
5. A second burst, full bleed, at most 3 cuts a second.
6. The GCD in gold, the only color in the sequence, above "Darkest Shades". Hard cut to the home page.

Skip works from the first frame (button, Esc, any scroll). The opening never plays for returning visitors, on links from Instagram or ads, or on links straight to a frame. With reduced motion turned on, visitors see the text cards only. A flash check in the build fails it on more than three flashes in any second.

**Sound** is off by design. Nothing depends on it; an opt-in sound can come later.

**The home page** runs in this order: manifesto, the detail, the drop, the cast, the promises, the list, the footer.

**The voice** uses short declaratives, plain nouns and sentence case. No exclamation marks, no hype, no name-dropping. The draft home lines: "We don't make noise." · "Presence is not a performance." · "See everything. Reveal nothing."

**Honesty on the page:**

- $100 is always on the page.
- Countdowns run only to real times, and pair counts come only from inventory. A missing number shows nothing.
- No discounts, no exit offers, no "12 people viewing".
- The list pop-up appears once, at 60% scroll. It offers drop news, plus early access only when the store really gates it.

## Where inspiration comes from

Prada sets the standard, Raf Simons' way of working sets the lens, and three reference videos set the motion. None of them ever appears on the site: we take structure and attitude, never names, layouts or footage.

| Source | What we take | What we never take |
|---|---|---|
| **Prada** (the idol) | Restraint, intelligence, the price on the page. Its wordmark-plus-emblem system is the model for our logo plus the GCD. | Its layouts, wordmark style, triangle shapes or campaign images. Its name on the site. |
| **Raf Simons' way of working** (the design lens, internal only) | "Philosophy as manifesto, before product": a position before a product, one idea per screen, type as the image, real people with a point of view, an archive rather than a catalog, stillness then one cut. | His name, likeness, quotes, collections or collaborators' artwork, anywhere on the site, in metadata, alt text or shipped code. |
| **Prada's SS90 runway** (the patina) | The photographs' surface: hard frontal flash, 35 mm film grain, lifted blacks, warm paper whites, muted color, one figure in a bare space, runway-style look numbers. | Runway photos. CSS filters (the look is made in the photo pipeline). |
| **Video 1: a strobe of editorial stills** | The opening's structure: text cards, then bursts at a fixed rhythm around one returning image, small framed prints first, then full bleed. The small centered "card" sentences. | White frames at 12 a second (a seizure risk). The footage itself. |
| **Video 2: the Bloodsport janitor long take** | One long, fixed view where a tiny precious detail is the whole subject. The gold tooth becomes our GCD. See everything, reveal nothing. | The footage. |
| **Video 3: the 1983 Maxell commercial** | Patience, then one huge move: stillness, then a hard cut in scale. Frontal, centered staging with very few props. | Sound that plays on its own. Moves on a timer. |
| **Anastasiia's identity** | The logotype, the angular brand mark, Owners Wide and Stolzl, the "Sustainable elegance" palette. | Recolored or stretched marks. The retired Eclipse Silhouette and the old engraved wordmark. |
| **The Brand Story and Voice & Tone guide** | The community (DJs, filmmakers, digital artists, designers) in the casting; the five voice pillars; the promises. | Slang or hype in the copy. |
| **digs** | Process: a story for every component state, wire mode, token discipline. | Its components or their look. |

Ruled out across the board: streetwear hype, logo-mania, fashion-week pastiche, stock photos, and generated glasses.

## The pages

Eight products keep the site capsule-sized: four top-level destinations, no search, no filters, no mega-menu.

| Page | Path | What's on it, and its one move |
|---|---|---|
| Home | `/` | The opening (first visit only), then the manifesto, the GCD detail hold, the drop (its first scroll cuts to the eight frames as numbered prints), the cast, the promises, the list. |
| Drop | `/drops/001` (`/drop` points to the current one) | "Drop 001" and one statement. A status block: Announced, Live, Sold out or Ended, with date, time zone and pairs left from inventory. The frames in the drop as stage cards. Past drops stay up as an archive. |
| Frames | `/frames` | One statement line, then the eight as numbered stage cards, 1 across on a phone and 4 on desktop. Each card: look number, front angle (three-quarter on hover), name, descriptor, $100, availability. |
| Frame page | `/frames/lou-went-underground` and the rest | Gallery (front, three-quarter, side, top, inside, GCD close-up (the hinge on F08), then on-model) beside a sticky buy panel. Then the detail hold, specs, the technical drawings, "Worn by", next look. |
| Manifesto | `/manifesto` | Paper theme. The full statement in numbered paragraphs, one image at most. |
| Cast | `/cast` | The seven, one per screen on a phone, full bleed, each linked to the frame they wear. |
| Questions, care, policies, accessibility | `/questions`, `/care`, `/policies/*`, `/accessibility` | Paper theme for reading, lines no longer than 68 characters. |
| Bag | drawer on every page, and `/cart` | Lines on stage thumbnails, $100, the exchange and warranty lines. Checkout reads "Checkout opens at launch" in this phase. |
| 404 | any other path | One line, the brand mark, a way back. |

**Navigation.**

- Desktop header: the logo, then Drop · Frames · Manifesto, then Bag.
- Phone header: the brand mark, Menu and Bag. The menu is a full-screen sheet with the destinations numbered 01–04 in camel. It opens with a hard cut.
- While a drop is announced or live, one line runs under the header on every page, for example "Drop 001 · Open · 37 of 120 pairs left". It shows only real numbers.
- Footer: the list sign-up, link columns, @darkestshades, the GCD seal, and the logo edge to edge.

## What stays fixed in the build

These are the rules to hold without asking. Most are in `CLAUDE.md`; the rest come from the brief docs.

**Brand**

- The tagline is See Everything. Reveal Nothing.
- Raf Simons is never named, shown or quoted on the site, in metadata, alt text or shipped code.
- Marks come only from the repo's brand folders. The nav and favicon use the angular brand mark, never the GCD. The GCD appears at most once per screen.
- The Eclipse Silhouette and the old engraved wordmark never appear.
- Fonts are Owners Wide and Stolzl only, rendered by open-licensed stand-ins until they're licensed. Font files are never committed: the repo is public.
- The app uses role color tokens only, with no hex values. Graphite `#545454` is never text on dark. One gold element per view. Product images always sit on the stage color.

**Honesty**

- $100 is always visible.
- Countdowns run only to real times from drop data, and pair counts come only from inventory. A missing value renders nothing, with a unit test for each case.
- No discounts, exit offers, fake urgency or invented reviews.

**The opening**

- The photosensitivity notice comes first, skip works from the first frame, and the sequence is built from stills.
- It never plays on deep links or for returning visitors, and there are no bursts under reduced motion.
- The flash check must pass.

**Products and copy**

- Every product fact comes from the product files, which come from the 1:1 drawings. An empty value hides its row; no spec is ever invented.
- All copy comes from the copy file, with no lorem ipsum anywhere. Frame names are never explained or tied to a real person.

**Imagery**

- Product photos come only from the cleaned lightbox set, carrying the GCD.
- People come only from the seven-person cast, wearing the real frames.
- Until a final image lands, its place is a labelled slot (for example "F01-A2 · 4:5").
- Reference videos and Prada or runway material never ship.

**Build**

- Mobile first at 390, 768, 1024 and 1440 px, to WCAG 2.2 AA.
- The store mechanics never depend on the Darkest Shades layer. Every component has a Storybook story for each state, at phone and desktop width, in finished and wireframe modes.
- Data comes from local mock files shaped like Shopify's. This phase has no live store and no checkout.
- Colors change only through the palette tool, which fails on any contrast failure.
- Free tools only.

## Open questions (mine to decide)

None of these blocks the build: each has a default the site uses until I decide. They're sorted by when I need to answer.

| Question | What the build does until then | Needed by |
|---|---|---|
| The pairs-left threshold: above what count is the number hidden? | Shows the count only when the inventory number is real | The house components |
| Sign-off on the copy: entry, manifesto, home, drop, product, list, SMS, questions and accessibility are drafts; care is a placeholder; sections without a status count as drafts | Review builds show the drafts; no draft or placeholder copy can reach a production build | The UI pages review |
| Cast page: show first names, initials or nothing? | Nothing; each person links to the frame they wear | The UI pages review |
| Drop 001: which frames, how many pairs, when | "Date to be announced"; no number is ever invented | Launch |
| A per-customer limit on a drop | No limit | Launch |
| The list pop-up's early access: will the store really gate 24 hours for list members? | Ships the line without early access | Launch |
| SMS provider: Shopify Messaging, Klaviyo, Postscript or Attentive | Provider-neutral consent wording | Launch |
| Web licenses for Owners Wide and Stolzl: Adobe Fonts, or self-hosting licenses | Renders with open-licensed stand-ins (Mona Sans for Owners Wide, Urbanist for Stolzl) until the real fonts load | Launch |
| Factory sign-off on the GCD's metal and sizes, and each frame's size marking | Copy says "gold" as a color only; sizes are measured from the 1:1 drawings | Launch |

---

# Part 2 · How to run the build

## Order of authority

1. The non-negotiables in `CLAUDE.md`, and `docs/brief/00-decisions.md`.
2. This part, for how the run operates. Where it departs from `09-build-plan.md` (where the Hydrogen project goes, the review stops, branches and merging, phase 5) or from `CLAUDE.md`'s "ask the founder" (here: log the question and keep going on the default), this part wins.
3. `docs/brief/01`–`09` for the detail.
4. Part 1 for intent: where the docs are silent, choose what fits the picture.

## Where things stand (Oct 28 2026)

- **No app yet.** No `app/`, no `package.json`, no CI. Phase 0 starts from zero.
- **Tokens:** `design/tokens/` (`tokens.color.*`, `tokens.base.json`, `contrast-report.md`, generated CSS in `build/`), made by `tools/palette.py` and `tools/build_tokens.py`.
- **Marks:** `brand/marks/` (logo, stacked logo, brand mark; `web/` holds the currentColor SVGs; `favicon/` the icon set) and `brand/emblems/gcd/` (`svg/`, `png/`, `render/`).
- **Products:** `content/products/f01.json` … `f09.json`, checked against `product.schema.json`, with `drawings/` (vector line art at 1:1 mm). Eight frames: F01–F06, F08, F09. There is no F07 (`00-decisions.md` #7), so look numbers skip 07. Drop membership comes from `content/drops/*.json`; each product's `drop` field stays `null`.
- **Drop:** `content/drops/drop-001.json`: announced, all eight frames, every date and quantity `null`, early access off. With this data the site shows "Date to be announced", no countdown and no pair counts.
- **Fonts:** the real Owners Wide and Stolzl aren't available to the build: there's no Adobe Fonts subscription, and Stolzl has no free or trial version. Until I license them, the open-licensed stand-ins in `brand/fonts/README.md` render them: Mona Sans and Urbanist, installed from npm (`00-decisions.md` #41). The token stacks already name them.
- **Copy:** `content/copy/en.json`. Most sections carry a status: `draft` (entry, home, manifesto, drop, product, list, sms, questions, accessibility) or `placeholder` (care). Sections without one (meta, nav, bag, footer, notFound, alt) count as draft until I sign them off.
- **Product photography is finished:** 56 finals (eight frames × A1–A6 and the hero H) in `assets/photography/` as AVIF, WebP and JPEG, at the widths in the manifest's `widths` column (up to 2048 px). `MANIFEST.csv` registers each one with its alt text and crop. The masters sit in `dam/product/` (0.8 GB); the app never reads `dam/`.
- **On-model pictures:** nine are approved finals (`00-decisions.md` #42): masters and 16-bit cut-outs in `dam/people/`, web files and manifest rows (`ds-cast-…`, 640 to 1920 px) in `assets/photography/`. Every frame has at least one and F03 has two; they're worn by M1, M2, NB, W1 and W2. `content/photography/people/*.json` lists all 20 planned shots: the nine marked `final`, eleven still `draft`, including every M3 and W3 shot. A draft shot is a labelled slot with its id and ratio, for example `W3-S02-F09-A1 · 4:5`. If more finals reach `main` during the run, wire them in. A people final's manifest id is the shot's `id` without `-vNN`, lowercased: `ds-cast-w1-s07-f02` (A1 shots carry no angle), `ds-cast-w2-s06-f09-a2`.
- **The cast:** seven, W1, W2, W3, M1, M2, M3 and NB (`reference/casting/`). The codes are internal labels, not names.
- **Not part of this build:** `takes/` (a separate film project; nothing ships from it), `reference/` (study only), and the photography pipeline that other sessions run: `tools/blender/`, the existing tools in `tools/photo/`, `content/photography/`, `dam/` and `assets/photography/`. Read any of it; change none of it, apart from adding the entry-stills tool in phase 3.

## Running unattended

- Don't stop between phases and don't wait for me. I'll read the PRs and PROGRESS.md as they come.
- **The two reviews become checkpoints.** After phase 1 and after phase 4, publish the review set (09's deliverables), open the PR with a short review note (what to look at, what you decided, what you need from me), and carry straight on.
- **Read my feedback.** At the start of every phase, read new comments and reviews on the open PRs through the REST API (`issues/<n>/comments`, `pulls/<n>/comments`, `pulls/<n>/reviews`); the GitHub proxy blocks `gh pr`. Fold my feedback in at the next sensible point. It outranks your own calls.
- **Questions that are mine** (brand, product facts, money and legal copy): use the documented default (the open items in `00-decisions.md`, the open questions in Part 1, the edge cases below), log the question in PROGRESS.md under "Questions for Antaeus" and in the PR, and keep going. Never settle one by inventing a fact.
- **Everything else:** decide, and log the decision in PROGRESS.md and the PR.
- **Stop** only for a step that can't be undone and that no rule or default covers. Under these rules that shouldn't come up.
- **Never weaken a check to get past it**: the font check, the flash check, contrast, the draft-copy gate, axe, the honesty tests. If one can't pass in this environment, leave it failing, write why at the top of PROGRESS.md and in the PR, and build on.
- **Deleting files:** use literal paths, and guard variables (`${DIR:?}`). Claude Code refuses some `rm` commands even with permissions bypassed; when it does, rewrite the command rather than stop.

## Orchestration

Use workflows and subagents where they pay.

- **One phase per workflow**, or a short chain (build, then verify). Never one workflow for the whole build. Between phases, check the done criteria yourself against the evidence, update PROGRESS.md, merge, then start the next phase.
- **Fan out what's independent:** base components (phase 2), house components (phase 3), page templates (phases 1 and 4), audits (phase 6). **Don't fan out** phase 0's foundation (Hydrogen, Tailwind, tokens, fonts, Storybook, Playwright, CI) or the shared pieces everything else uses (`ShotSlot`, the page shell, header and footer, the mock adapter, the copy accessor). Build those first, in one context.
- **Brief every builder and reviewer the same way:** `CLAUDE.md`, `00-decisions.md`, `01-brand-system.md`, the relevant rows of `04` and `05` and the docs in their Ref column (`03`, `06`, `08`), Part 1, this part's "Edge cases" and "Never", the paths of what's already built, and the files it owns.
- **In a fan-out** no agent touches `package.json`, shared config, tokens, `en.json` or another agent's files. Add dependencies before the fan-out. Builders hand back the strings they need, and you add them to `en.json` in one pass.
- **End every phase with a review by agents that didn't build it.** One checks the work against `CLAUDE.md`, `00-decisions.md`, Part 1 and the phase's done criteria, and reports file and line. For phases 1 and 4, another looks at every page's screenshots side by side for consistency: type scale, spacing, dark space, one gold element per view, the stage color behind every product. Fix what they find, then verify again.
- **One VM:** about 4 CPUs, 16 GB of memory and 30 GB of disk. Fan out the writing; run the heavy jobs one at a time (one dev server, one Storybook build, one Playwright or Lighthouse run).
- **Worktrees** start from a commit, so commit before each fan-out. Put Claude Code's worktree settings in `.claude/settings.local.json`, git-ignored, so the photography sessions on `main` keep their own; recreate it after a fresh VM.
  - `worktree.baseRef`: `"head"`, so agents start from the phase branch, not `main`.
  - `worktree.sparsePaths`: the folders to check out: `.claude`, `.github`, `.storybook`, `app`, `assets`, `brand`, `content`, `design`, `docs`, `public`, `tests`, `tools`, plus any new top-level folder. That leaves `dam/` (0.8 GB), `takes/` and `reference/` out of every worktree.
  - `worktree.symlinkDirectories`: `node_modules`.
  - Add `.claude/worktrees/` to `.gitignore`, a `.worktreeinclude` for `.env` and the font files in `brand/fonts/private/`, and `.claude/` to ESLint's ignores.
  - Each builder commits on its worktree branch, and you merge those branches into the phase branch.
  - Check the exact setting formats in the Claude Code docs.
- **Usage counts against my plan.** Size fan-outs to the work, and don't start a workflow for a one-file change. Mechanical stages (running suites, capturing screenshots, grep audits) can run on a smaller model; design, code and review stay on yours.

## Git and pull requests

- Pull `main` at the start of every phase. Other sessions push photography work to `main` while you build. Never rewrite `main`'s history, force-push it, or revert their commits.
- One branch and one PR per phase (`build/phase-0-foundation`, `build/phase-1-wireframes`, …), with screenshots in every PR that changes the interface.
- **Merging.** A phase merges when every check passes except those listed at the top of PROGRESS.md as environment failures, and its review findings are fixed. Merge the PR into `main` yourself and branch the next phase from the new `main`. On a merge conflict, merge `main` into the branch, resolve it, run the checks again and retry. If the API or your permissions refuse the merge, base the next branch on the last one and say so in both PRs and in PROGRESS.md.
- In this cloud session `gh pr …` fails, because the GitHub proxy blocks GraphQL. Open and merge PRs with the built-in GitHub tools or the REST API: `gh api -X POST repos/FastCoempany/darkestshadeswebsite/pulls` (with title, head, base and body) to open one, `gh api -X PUT repos/FastCoempany/darkestshadeswebsite/pulls/<number>/merge` to merge it. The proxy also refuses tags and branch deletions; leave merged branches where they are.
- Put `.github/workflows/` in a commit of its own, last on its branch. If GitHub refuses the push (the session's credential may not be allowed to write workflows), drop that commit and keep the checks runnable as an npm script.
- Commit and push at every milestone and at least every hour. The VM can be reclaimed, and only pushed work survives.
- Write PRs and PROGRESS.md in short, plain sentences: what changed, what to look at, what you decided, what you need from me.

## PROGRESS.md

Create `docs/build/PROGRESS.md` in phase 0, keep it current, and commit it with the work.

- **Checks failing for environment reasons**, at the top, with the reason.
- **Phases:** a table of phase, state, branch and PR, the evidence for each done criterion (the command and its result, the screenshot sets you looked at), and the date.
- **Now and next:** the current step and the one after it, enough for a fresh session to pick up cold.
- **Decision log:** date, decision, why, PR.
- **Questions for Antaeus:** the question, the default in use, when I need to answer.
- **Copy to sign off:** strings you added to `en.json`.
- **Before launch:** what's left for me (copy sign-off, the drop plan, font licenses, the SMS provider, the early-access gate, the M3 and W3 pictures, the store connection).

## Verification

- A phase is done when each of its done criteria (09's, plus the notes below) has been run and shown: the command, its exit status, the output that matters. "Should pass" isn't done.
- **Look at your screenshots.** Open every page at 390 and 1440 before calling a phase done, and hold each one against Part 1 and the edge cases below: the night canvas (paper on the reading pages), products on the stage color, one gold element per view (focus rings excepted), the display and text faces (the stand-ins for now) at the sizes in `01-brand-system.md`, square corners, a lot of dark space, one idea per screen, no graphite `#545454` text on dark, nothing behind type.
- Check 768, 1024 and 320 px and 200% zoom as well (`04`), even though the deliverables are 390 and 1440.
- Visual tests run here, with Playwright against the app and Storybook. No Chromatic or other hosted service. Keep baselines lean: 1× pixel ratio, updated only for an intended change (the real fonts arriving is one).

## Phase notes

Only what isn't in 09 or is easy to get wrong.

### Phase 0 · Foundation

- **Scaffold Hydrogen in a scratch folder**, then copy in only what the app needs: `package.json`, `server.ts`, `vite.config.ts`, `react-router.config.ts`, `tsconfig.json`, `env.d.ts`, `eslint.config.js`, `public/` and `app/` (the starter's names as of create-hydrogen 5.0.40). Never copy its `CLAUDE.md`, `AGENTS.md`, `README.md`, `CHANGELOG.md`, `.cursor/` or `guides/`: they would replace this repo's rules. Keep the repo's `.gitignore`, adding what the app needs.
- The source folders that `CLAUDE.md` and 09's layout name must be the real ones: `app/routes/`, `app/components/base/`, `app/components/house/`, `app/lib/mock/`. No nested `app/app/`.
- **Remove every Shopify call**, in loaders and outside them: `storefrontRedirect` in `server.ts`; the analytics (`getShopAnalytics`, `Analytics.Provider`) and the preconnects to cdn.shopify.com and shop.app in `root.tsx`; the Storefront, cart and customer-account clients in `app/lib/context.ts`; and the starter routes the site doesn't have (discount codes, blogs, collections, search, sitemaps; `/account/*` is a placeholder, `04`). Remove any discount-code or gift-card form: there are no discounts.
- **The mock:** loaders read `app/lib/mock/`, built from `content/products/`, `content/drops/` and `assets/photography/MANIFEST.csv`, shaped like Storefront API responses, in one module to swap at launch. Loaders run in MiniOxygen, which has no file system, so the mock imports the JSON and CSV at build time. No store credentials; `.env.example` documents the variables. The cart is local state in the cart API's shape, and checkout stays disabled.
- Keep `dam/`, `work/`, `takes/` and `reference/` out of the dev server's file watcher and out of the bundle.
- **Tokens:** Tailwind v4 with its default palette off and `ds-` color names pointing at the role variables (09). Change tokens only through the tools; fixing a generator in `tools/` is fine, hand-editing `design/tokens/build/` isn't.
- **Fonts:** install the stand-ins as `brand/fonts/README.md` says (`@fontsource-variable/mona-sans`, `@fontsource-variable/urbanist`), and have display text set `font-variation-settings: var(--font-variation-display)`.
  - The check must find a loaded `FontFace` for each role and weight: Owners Wide 500 or the Mona Sans stand-in; Stolzl 300, 350, 400 and 500 or the Urbanist stand-in. It fails on system type. `document.fonts.check()` alone isn't enough: it returns true when no `@font-face` for the family exists.
  - Put "Stand-in type" at the top of PROGRESS.md and in each checkpoint PR.
  - If real font files or a kit appear (`brand/fonts/README.md`, routes A and B), they take over. Never fetch the real fonts from anywhere else.
- **Playwright:** check `$PLAYWRIGHT_BROWSERS_PATH` before installing anything. Pin `@playwright/test` to the version that matches the installed browser or, with Full network access, install Chromium for the version you use. Point Lighthouse at a browser with `CHROME_PATH`.
- **The draft-copy gate** (09): the production build refuses while any copy section is draft or placeholder, so it refuses today. Add a review build with production settings that allows drafts; Lighthouse and the review screenshots run on it. CI runs the review build, plus a test that the production build refuses with today's `en.json`.
- **The CI string check** bans `Raf`, `Simons`, `Prada` and the rest of 09's list in `app/` and `content/copy/`. Keep the check's own source outside those folders so it doesn't flag itself. Match the names as whole words in any case, and don't call a `requestAnimationFrame` handle `raf`. Exclude Hydrogen's generated API types (they mention discounts) rather than loosening the check.
- Prove `tools/flashcheck.py` before the entry exists: a synthetic 12-per-second white strobe must fail it, and a dark-graded one must pass.
- Add the app commands to the Commands section of `CLAUDE.md`.

### Phase 1 · Wireframes

- Wire mode is `<html data-mode="wire">`: greyscale, every media slot labelled with its shot code and ratio (`F01-A2 · 4:5`, `F01-H · 3:2`, `W2-S06-F09-A2 · 4:5`).
- Real copy (the drafts) and real product data from the start.
- Cover every template in `04` and every state a page can be in: the drop page announced without a date (today's data), announced with a date, live, sold out and ended; the bag empty and full; the menu sheet; the list pop-up; the photosensitivity notice; the entry as a frame list. Numbers for states the real data doesn't have live only in test and story fixtures, never in a route.
- Checkpoint: the review set and the PR, then on to phase 2.

### Phase 2 · Base components

- `05`'s base table: every state, 390 and 1440, UI and wire mode, axe passing.

### Phase 3 · House layer

- `05`'s house table. `Countdown`, `PairsLeft`, `DropStatus` and `DropLine` get a unit test for every missing-data case.
- The pairs-left threshold is mine to set: make it a setting, `null` by default, meaning no threshold.
- **The entry's stills don't exist yet.** Write a tool in `tools/photo/` that makes them from the product finals into a folder of their own (for example `assets/entry/`), as the entry section of `03-references.md` (Assets, Safety) requires: every still black and white; burst 1 also graded so no pixel's relative luminance exceeds 0.09; burst 2 with at most one bright frame a second; AVIF and WebP at two sizes; under 1.5 MB in all on mobile. The grade happens in the tool, never in CSS. Cast stills join when cast finals land. Run the flash check on the real sequence.
- `ListForm` and `ListOffer` submit to a mock that records state; no email or SMS provider. Consent text comes from `en.json` word for word; SMS stays optional and never pre-checked.
- `Seal`: flat gold under 48 px, the onyx vector from 48 to 160 px, the 3D render above that (`01-brand-system.md`).

### Phase 4 · UI pages

- Compose the pages from phases 2 and 3 with real copy and mock data. Product and cast images come through the manifest: AVIF, then WebP, then JPEG, with srcset from the `widths` column and the manifest's alt text.
- Review builds show the draft copy as it is. Its status lives in the data and the review notes, not as labels on the page.
- **Policy pages:** the legal text comes from Shopify at launch. Until then each page shows its title, the settled promises where they apply (45-day exchange, 6-month warranty; `00-decisions.md` #26) and one draft line saying the full text is published at launch. Never draft legal terms.
- **Missing copy.** An interface string `en.json` lacks (a label, a state line, a statement a page needs) goes into `en.json` in the voice of `08-copy.md`, marked for sign-off in PROGRESS.md. Never hard-code copy. Copy the data leaves `null` (the drop's statement, each product's `copy.line` and `copy.story`) stays empty and goes on the questions list; don't write it.
- Checkpoint: the review set and the PR, then on to phase 5.

### Phase 5 · Photography

- Track 1 is done. Make the site read `MANIFEST.csv`, so a new or replaced final needs no code change. Never hand-edit the manifest; `tools/photo/export_web.py` writes it.
- Track 2 isn't yours to make: no image or video generation of any kind, no Runway, no compositing of people. Wire cast finals that reach `main`; everything else stays a labelled slot.

### Phase 6 · QA and hand-off

- 09's list. Lighthouse runs on the review build (production settings, drafts allowed): the production build's refusal of draft and placeholder copy is expected until I sign it off, not something to fix.
- Finish PROGRESS.md's "Before launch" list, and update the "Start here" section of `README.md` with how to run the app.

## Edge cases with a default

Log each in PROGRESS.md as a question for me.

- **How many GCDs a screen shows.** "Once per screen" and "one gold element per view" govern the interface: the seal and the gold accents. The GCD in a product photograph is part of the product, and `CLAUDE.md` says it is never left off a picture, so a grid of frames can show several.
- **The detail hold's picture.** An A6 final on its stage color, unaltered, set in the night canvas. The home page uses F09's (`ds-f09-a6`: a black temple, where the gold reads clearest). `03` describes a dim screen with the GCD as its only warm color; a darker grade would have to be made in the photo pipeline, so log it as a question rather than making one.
- **F08's detail hold.** F08's pictures show no GCD (`00-decisions.md` #34). Its page's detail hold uses the GCD's 3D render (`brand/emblems/gcd/render/`) instead of a photograph of F08. Never composite a GCD onto an F08 picture.
- **The entry's stills** are graded black and white, so they leave the stage color. They aren't product presentations; the stage rule doesn't apply to them.
- **Motion beyond the cuts.** The gallery swipes on a phone (`04`) and the bag drawer takes 120 ms on desktop (`05`). Those are the only exceptions.
- **One picture per person on `/cast`:** their studio shot, all five of them finals (`W1-S07-F02-A1`, `W2-S06-F03-A1`, `M1-S06-F04-A1`, `M2-S07-F01-A1`, `NB-S06-F06-A1`). M3 and W3 have no pictures yet, so their grey-seamless shots (`M3-S02-F02-A1`, `W3-S02-F09-A1`) stay labelled slots.
- **Disabled text.** Graphite `#545454` is never text on dark. Disabled controls use the disabled-text token (graphite-400, `#6B6B6C`), because WCAG exempts inactive controls from contrast.
- **`{supportEmail}`** has no value yet, and an address is a fact you can't invent. The sentences that need it stay hidden until I give one.
- **The drop line without a date** shows `drop.states.announcedNoDate`.

## Never

- Shopify calls of any kind (Storefront API, mock.shop, Admin API), checkout, payments, a store connection, an Oxygen deploy.
- Image or video generation of any kind, including with Figma's included AI credits; paid tools, paid APIs or credits; hosted services beyond GitHub and the fonts kit.
- Font files in git, or fonts from anywhere but the routes in `brand/fonts/README.md`: the stand-ins now, the licensed fonts later. No third-party scripts besides a fonts kit.
- A product fact, price, drop date, quantity or review that doesn't come from the data. Product JSON changes only with a source (the drawings, the factory, me); flag anything that looks wrong.
- Raf Simons' or Prada's name in `app/`, `content/copy/`, metadata, alt text or shipped comments.
- A copy of a digs component.
- Hex colors in `app/`, or hand edits in `design/tokens/build/`.

## Finishing

When phase 6 is merged, run every check once more and show the output: typecheck, lint, Vitest, Playwright, axe, the flash check, Lighthouse and the CI checks. Make sure `git status` is clean and everything is pushed. Then end with a short report for me: what's built, where the review sets are, the questions for me, and what's left before launch.
