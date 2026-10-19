# 08 · Copy

All site copy lives in `content/copy/en.json`; product facts in `content/products/`. Strings marked `draft` are Claude's drafts in the brand voice and need the founder's yes; strings marked `placeholder` never ship. No lorem ipsum anywhere, including stories and tests.

## Voice
From the Voice & Tone Guide's five pillars: **Powerfully Minimalist** (every word earns its place), **Elegantly Rebellious** (edge with poise), **Mystique as a Strategy** (let people lean in), **Culture-Driven and Creative** (insider, never trying too hard), **Confidently Direct** (sure, calm, editorial; leading, not pitching).

On the site that means:
- Short declaratives and the occasional fragment. One idea per line.
- Plain nouns over adjectives: "Polarized TAC lenses. UV400." not "incredible crystal-clear protection".
- Sentence case everywhere except Owners Wide display lines, which are set uppercase by style, not typed in caps.
- No gendered address (no "bro", "babe", "girlboss", "dude"); no hype ("must-have", "obsessed", "run, don't walk", "tag your bestie", "you NEED these"); no exclamation marks.
- No name-dropping: no Prada, Raf Simons, runway or celebrity references on the site.

## Honesty rules (from `00-decisions.md` #18)
- **Price is always shown**: "$100".
- **Countdowns only to real times** set in drop data. No evergreen timers, no resets, no "ends tonight" unless it does.
- **Quantities only from inventory.** "37 of 120 pairs left" only when both numbers are real; otherwise nothing.
- **No discounts in any overlay.** No exit-intent offer. The list pop-up gives information and access, not money.
- **Early access only if it's real.** The "24 hours before everyone else" line ships only when the store gates the drop for list members (customer tag); otherwise use `list.bodyNoEarlyAccess`.
- **No fake social proof**: no invented reviews, counts of people viewing, or "sold in the last hour".

## Claims
Allowed (Brand Story, treated as tested): polarized TAC lenses; UV400 / 100% UVA and UVB; impact resistant; scratch resistant; premium acetate fronts; universal fit; $100; 45-day exchange; 6-month warranty (scratches and defects). Per frame, lens color is stated as it is; "ultra-dark" is never applied to F01, F03, F06 or F08 (`06-products.md`). The GCD's metal is "gold" as a color word until the factory confirms the metal (`00-decisions.md` O4).

## Fixed typos and names
- `#DarkestShade` → **`#DarkestShades`**.
- "Zara in in Chicago" (voice guide) → not used on the site; the Brand Story puts Zara in Toronto.
- Instagram **`@darkestshades`**, site **`darkestshades.com`**.
- Source paths keep their spelling ("Lighbox shots"); only what we make is corrected.

## Legal and safety copy
Exact strings are in `en.json`; summary:

- **Photosensitivity notice** (`entry.notice`): "This opening uses rapidly changing images. If flashing images affect you, skip it." Buttons: Continue · Skip intro.
- **Email consent** (`list.emailConsent`): what they'll get, unsubscribe any time, privacy link.
- **SMS consent** (`list.smsConsent`): the standard US disclosure next to an unchecked checkbox: recurring automated marketing texts, consent not a condition of purchase, frequency varies, message and data rates may apply, HELP and STOP, links to SMS Terms and Privacy Policy. Phone is optional; email alone is enough to join.
- **SMS flows** (`sms.*`): double opt-in confirm, welcome, HELP and STOP replies, and a drop-live template, each starting with the brand name and ending with the opt-out.
- **Image disclosure** on on-model images (`product.imageDisclosure`).

The SMS provider (`00-decisions.md` O7) may require its own wording; keep its required elements and our tone.

## Where copy is edited after launch
In Shopify admin, through metaobjects the storefront reads (`00-decisions.md` #22):

| Metaobject | Fields |
|---|---|
| `manifesto` | lines (list), paragraphs (rich text) |
| `drop` | number, state, starts at, ends at, frames, limit per customer, early access hours, statement |
| `list_offer` | title, body, body without early access, button, consent texts |
| `notice` | entry notice text and buttons |
| `promise` | label, detail (exchange, warranty, lens, price) |

Product copy (name, descriptor, line, story) lives on the product and its `ds.*` metafields. Policies use Shopify's policy pages. `en.json` stays the seed and the source for tests and stories.
