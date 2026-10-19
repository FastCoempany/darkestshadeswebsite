# Marks

Anastasiia Glekel's identity files, converted from her `.ai` masters (PDF-compatible) to SVG with `pdftocairo`. Paths only, no fonts.

| File | Her file name | Use |
|---|---|---|
| `ds-logo-horizontal-{black,white}.svg` | Primary Logo | Header on wide screens, footer, email |
| `ds-logo-stacked-{black,white}.svg` | Secondary Logo | Square-ish spaces, entry end card |
| `ds-brand-mark-{black,white}.svg` | Brand Mark | Nav on small screens, favicon, app icons |

The masters keep her clear space. `tools/marks.py` writes the files the app uses:

- `web/ds-logo-horizontal.svg`, `web/ds-logo-stacked.svg`, `web/ds-brand-mark.svg`: tight viewBox, `fill="currentColor"`, with a title for screen readers.
- `favicon/`: `favicon.svg` (onyx mark, bone in dark mode), `favicon.ico` (16/32/48), `apple-touch-icon.png` (180), `icon-192.png`, `icon-512.png`, `icon-maskable-512.png`.

"Secondary" now means the GCD (`brand/emblems/gcd/`), so the stacked logo is never called secondary in the product. The nav and favicon always use the brand mark, never the GCD (`docs/brief/00-decisions.md` #11).
