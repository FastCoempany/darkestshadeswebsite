# 06 · Products

Eight frames, $100 each, sold in drops. Product facts live in `content/products/f0X.json` (schema: `product.schema.json`) and come from the 1:1 technical drawings and the lightbox shots. **Never invent a spec**: a missing value is `null` and the UI leaves the row out.

## The eight

IDs follow the factory and photo-group numbering. F07 ("Hunter Kept Owl Hours", the engraved navigator with the white floral strip) was dropped. Names and descriptors are the founder's (Oct 19 2026); handles are the names in kebab case. Names are never explained or tied to a real person.

| Look | Name · descriptor | Front / temples | Lens | Size (lens□bridge temple) | Lens h. | Front w. | Drawing | Lightbox shots |
|---|---|---|---|---|---|---|---|---|
| 01 | **Lou Went Underground** · Blue navigator | Blue-black tortoise acetate / same | Light blue | 54□22 145 | 44 | 150 | 01 | IMG_3554–3581 (28) |
| 02 | **Holly Wore Them to Breakfast** · Crimson tortoise, wire temples | Red-black tortoise acetate / black metal wire | Dark grey | 45□24 145 | 38 | 142 | 03 | IMG_3410–3441, 3465–3475 (43) |
| 03 | **Roy Forgot the Clear Ones** · Black wayfarer, yellow lens | Gloss black acetate / same | Yellow | 45□24 150 | 38 | 145 | 02 | IMG_3316–3341, 3492–3505 (40) |
| 04 | **K Was Never Here** · Flat-top square, wire temples | Black acetate / metal wire with a 15 mm end-piece | Dark grey | 47□25 148 | 34 | 147 | 05 | IMG_3442–3464 (23) |
| 05 | **Jackie Gave Them Nothing** · Puffy square, wire temples | Gloss black acetate / metal wire with a 15 mm end-piece | Dark grey | 47□25 148 | 34 | 147 | 04 | IMG_3506–3553 (48) |
| 06 | **What Anna Thought** · Flat-top shield | Gloss black acetate / same | Grey gradient | 139□— 150 | 48 | 145 | 06 | IMG_3342–3371, 3482–3491 (40) |
| 08 | **What Arnie Hid** · Black octagon navigator | Black acetate / translucent smoke-grey acetate | Grey gradient | 56□18 153 | 44 | 154 | 08 | IMG_3582–3632 (51) |
| 09 | **What Stevie Saw** · The blackout | Gloss black acetate / wide gloss black acetate | Dark grey | 47□25 145 | 34 | 146 | 09 | IMG_3372–3409, 3477–3481 (43) |

All measurements in mm. The bridge is the distance between the lens openings, the number a size marking uses, measured on the 1:1 front views: the drawings dimension other things there (the gap between the nose pads, F08's opening between its two bridges), so the factory's own size marking wins when it is known (`00-decisions.md` O13). F06 is a one-piece shield lens: 139 mm across, no bridge gap. Frame heights not dimensioned were measured from the 1:1 front views (`measurementNotes` in each file).

### Telling the three black squares apart
F04, F05 and F09 are different designs (`00-decisions.md`), and the site has to show it:
- **F04, K Was Never Here** (flat-top square): square lens, straight flat brow, thinner rims, metal wire temples with a triangular end-piece.
- **F05, Jackie Gave Them Nothing** (puffy square): soft, pillowed corners and the thickest rims, metal wire temples with a triangular end-piece.
- **F09, What Stevie Saw** (the blackout): chunky rounded rectangle, thick rims, wide flat acetate temples.

Rules: their stage cards never sit side by side in a row of three; the A2 three-quarter angle (which shows the temple) is the hover image for all three; their descriptors always name the temple.

## Claims
From the Brand Story, treated as tested (`00-decisions.md` #23): polarized TAC lenses, UV400 (100% UVA/UVB), impact and scratch resistant, premium acetate fronts, universal fit, $100, 45-day exchange, 6-month warranty.
- Per frame, say the lens color as it is. "Ultra-dark" is a brand line, not a per-frame spec: it never appears on F01 (light blue), F03 (yellow), F06 or F08 (gradient).
- "Acetate" describes the fronts. F02, F04 and F05 have metal temples and say so.

## The GCD on each frame
Length = 0.98 × the temple face height where it sits (logo kit placement ratios, `01-brand-system.md`). Heights come from the drawings.

| Frame | Sits on | Face height | GCD length |
|---|---|---|---|
| F01 | Acetate temple | 12 mm (dimensioned) | 11.8 mm |
| F02 | Right wing of the front, over the pin heads (founder, Oct 19 2026); the left wing keeps its pins | flat face about 11 × 10 mm (measured) | 8.8 mm, as F04/F05 |
| F03 | Acetate temple | 9 mm (dimensioned) | 8.8 mm |
| F04 | Triangular end-piece | 15 mm at the hinge, 9 mm at the emblem's centre | 8.8 mm |
| F05 | Triangular end-piece | as F04 | 8.8 mm |
| F06 | Acetate temple | about 9.5 mm (measured) | 9.3 mm |
| F08 | Acetate temple | 10 mm at the hinge (dimensioned) | 9.8 mm |
| F09 | Wide acetate temple | 15 mm (dimensioned) | 14.7 mm |

These are estimates for imagery. The factory confirms the production sizes (`00-decisions.md` O4).

## Line art
`tools/drawings.py` turns each drawing into four clean vector views (front, side, top, three-quarter) at true scale in mm: `content/products/drawings/F0X-{front,side,top,iso}.svg`, black geometry only, `stroke="currentColor"`, non-scaling strokes. They feed `LineDrawing` on the product page and any print or packaging use. This is the frames' vector master: infinitely scalable outlines with real measurements.

## Drops
`content/drops/drop-001.json` holds the first drop. Every field the founder hasn't set is `null`, and the UI shows only what is set (`05-components.md`, honesty rules):

```json
{ "number": "001", "state": "announced", "startsAt": null, "endsAt": null, "timezone": "America/Chicago",
  "frames": ["F01","F02","F03","F04","F05","F06","F08","F09"], "pairsPerFrame": null, "limitPerCustomer": null }
```

In Shopify this becomes a `drop` metaobject (number, state, start, end, frames, limit) and per-variant inventory; "pairs left" is the live inventory quantity, never a stored number.

## Shopify mapping (later, for wiring)
- Product: title (the name), handle (kebab-case name), vendor "Darkest Shades", product type "Sunglasses", tags (`drop-001`, `look-01`).
- One variant per frame (one colorway each). SKU `DS-F01-01` until the factory's codes arrive.
- Metafields (`ds.*`): `look_number`, `descriptor`, `size_notation`, `measurements` (JSON), `lens_color`, `gcd_length_mm`, `line_art` (file references).
- Media: the A1–A6 angle set in order, then on-model images, all from the cleaned set (`07-photography.md`).
