# Fonts

Darkest Shades uses two families, in the styles Anastasiia's files use:

| Family | Styles used | Foundry | Role |
|---|---|---|---|
| **Owners Wide** (a width of the Owners family) | Medium | MCKL (Jeremy Mickel) | Display, headings, labels |
| **Stolzl** | Light, Book, Regular, Medium | Inhouse Type (Mariya Lish) | Body, UI, cards, micro labels |

The style list comes from the fonts referenced in the Graphic Elements Figma file and the Brand Guidelines. No font file is in this repo, and none may be committed: the repo is public (`docs/brief/00-decisions.md` #20). `brand/fonts/private/` is git-ignored for local copies.

## Until they're licensed: stand-ins

The build doesn't have the real fonts yet (`00-decisions.md` #41). There's no Adobe Fonts subscription, Stolzl has no free or trial version, and the free copies passed around online are pirated, so they aren't used. Until the founder licenses the real fonts (`00-decisions.md` O8), two fonts under the SIL Open Font License 1.1 render them. They were picked by setting candidates beside the specimen in Anastasiia's font-pairs deck (Option 01: Owners Wide and Stolzl) and measuring stroke weight against it.

| Role | Real font | Stand-in | Settings |
|---|---|---|---|
| Display | Owners Wide Medium | Mona Sans | `font-variation-settings: var(--font-variation-display)`, which is `"wdth" 125, "wght" 640`: its widest, at Owners Wide Medium's stroke weight |
| Text | Stolzl Light, Book, Regular, Medium | Urbanist | The same weights (300, 350, 400, 500). At Light, the one weight the deck shows, Urbanist's stroke is within 10% of Stolzl's |

- **Install** them from npm: `npm i @fontsource-variable/mona-sans @fontsource-variable/urbanist`. Import `@fontsource-variable/mona-sans/standard.css` (the width and weight axes) and `@fontsource-variable/urbanist/index.css`. They are served from the app itself, so no Content-Security-Policy change and no network route is needed.
- **The token stacks** list them after the real names (`'Owners Wide', 'owners-wide', 'Mona Sans Variable', …` and `'Stolzl', 'stolzl', 'Urbanist Variable', …`). When the real fonts load (route A or B below), they take over with nothing else to change.
- **Display text** always sets `font-variation-settings: var(--font-variation-display)`. A static Owners Wide ignores it, so it stays when the real font arrives.
- The type sizes in the tokens were set for the real fonts. Don't retune them for the stand-ins.
- Screenshots and visual baselines made with the stand-ins are marked "stand-in type" in `docs/build/PROGRESS.md` and in the PRs, and are remade when the real fonts arrive.

## Where the real fonts are

- **Adobe Fonts** has both families with desktop sync and web use: [Owners](https://fonts.adobe.com/fonts/owners) (98 styles, which covers the widths, including Wide) and [Stolzl](https://fonts.adobe.com/fonts/stolzl) (6 weights). It needs an Adobe account with Adobe Fonts (Creative Cloud).
- **MCKL** sells Owners licenses (desktop, web, self-hosting, apps) at mckltype.com and gives free trial versions with a limited character set after sign-up ([announcement](https://legacy.mckltype.com/news/announcement)).
- **Stolzl** licenses (desktop, web, self-hosting) are sold by Inhouse Type and resellers such as [MyFonts](https://myfonts.com/collections/stolzl-font-inhouse-type). No free or trial version turned up (Oct 2026).

Web licensing for darkestshades.com is settled later (`00-decisions.md` O8).

## Loading the real fonts, once licensed

Pick one; the app supports both. Either one replaces the stand-ins on its own.

**A. Adobe Fonts web project**
1. In Adobe Fonts, add Owners Wide Medium and Stolzl Light, Book, Regular, Medium to a web project.
2. Copy the project ID (the `xxxxxxx` in `https://use.typekit.net/xxxxxxx.css`).
3. Set `PUBLIC_ADOBE_FONTS_KIT=xxxxxxx` in the cloud environment's variables (it's not a secret; it ships in page HTML).
4. Network access must allow `use.typekit.net` and `p.typekit.net` (Full, or Custom with those hosts), and so must the app's Content-Security-Policy; Hydrogen's default policy blocks them.
5. Check the kit's CSS for the family names and weights it assigns, and map them in `app/styles/fonts.css` to the token families `'Owners Wide'` and `'Stolzl'` (Book is 350 in our tokens).

**B. Local files** (trial or licensed)
Put these in `brand/fonts/private/` (git-ignored), WOFF2 preferred:
```
OwnersWide-Medium.woff2
Stolzl-Light.woff2   Stolzl-Book.woff2   Stolzl-Regular.woff2   Stolzl-Medium.woff2
```
`app/styles/fonts.local.css` declares them as `'Owners Wide'` 500 and `'Stolzl'` 300 / 350 / 400 / 500 and is only included when the files exist. In a cloud session, add them through the environment's setup script from private storage, never from the repo.

## Checks

Before any screenshot, a Playwright test checks that each role has a loaded `FontFace` at every weight it uses:
- display: Owners Wide 500, or the Mona Sans stand-in;
- text: Stolzl 300, 350, 400 and 500, or the Urbanist stand-in;
- the kit's family names `owners-wide` and `stolzl` count as the real fonts.

The test logs which font rendered each role, and fails on system type.

`document.fonts.check('500 16px "Owners Wide"')` alone can't do this: it returns true when no `@font-face` for the family exists at all.
