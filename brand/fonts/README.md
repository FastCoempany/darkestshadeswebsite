# Fonts

Darkest Shades uses two families, in the styles Anastasiia's files use:

| Family | Styles used | Foundry | Role |
|---|---|---|---|
| **Owners Wide** (a width of the Owners family) | Medium | MCKL (Jeremy Mickel) | Display, headings, labels |
| **Stolzl** | Light, Book, Regular, Medium | Inhouse Type (Mariya Lish) | Body, UI, cards, micro labels |

The style list comes from the fonts referenced in the Graphic Elements Figma file and the Brand Guidelines. No font file is in this repo, and none may be committed: the repo is public (`docs/brief/00-decisions.md` #20). `brand/fonts/private/` is git-ignored for local copies.

## Where they are
- **Adobe Fonts** has both families with desktop sync and web use: [Owners](https://fonts.adobe.com/fonts/owners) (98 styles, which covers the widths, including Wide) and [Stolzl](https://fonts.adobe.com/fonts/stolzl) (6 weights). This is the most likely place Anastasiia activated them. It needs an Adobe account with Adobe Fonts (Creative Cloud).
- **MCKL** sells Owners licenses (desktop, web, self-hosting, apps) at mckltype.com and gives free trial versions with a limited character set after sign-up ([announcement](https://legacy.mckltype.com/news/announcement)). Stolzl's self-hosting license is sold by Inhouse Type.

Web licensing for darkestshades.com is settled later (`00-decisions.md` O8). For now the fonts are used in the build environment only.

## Loading them in the build environment
Pick one; the app supports both.

**A. Adobe Fonts web project** (simplest)
1. In Adobe Fonts, add Owners Wide Medium and Stolzl Light, Book, Regular, Medium to a web project.
2. Copy the project ID (the `xxxxxxx` in `https://use.typekit.net/xxxxxxx.css`).
3. Set `PUBLIC_ADOBE_FONTS_KIT=xxxxxxx` in the cloud environment's variables (it's not a secret; it ships in page HTML).
4. Network access must allow `use.typekit.net` and `p.typekit.net` (Full, or Custom with those hosts).
5. Check the kit's CSS for the family names and weights it assigns, and map them in `app/styles/fonts.css` to the token families `'Owners Wide'` and `'Stolzl'` (Book is 350 in our tokens).

**B. Local files** (trial or licensed)
Put these in `brand/fonts/private/` (git-ignored), WOFF2 preferred:
```
OwnersWide-Medium.woff2
Stolzl-Light.woff2   Stolzl-Book.woff2   Stolzl-Regular.woff2   Stolzl-Medium.woff2
```
`app/styles/fonts.local.css` declares them as `'Owners Wide'` 500 and `'Stolzl'` 300 / 350 / 400 / 500 and is only included when the files exist. In a cloud session, add them through the environment's setup script from private storage, never from the repo.

## Checks
A Playwright test asserts `document.fonts.check('500 16px "Owners Wide"')` and the four Stolzl weights before any screenshot is taken, so a missing font fails loudly instead of falling back to system type.
