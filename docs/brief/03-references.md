# 03 · References: the three videos

The founder chose three screen recordings as the foundation for the entry and the home page (`00-decisions.md` #6). Copies are in `reference/videos/` for study. They are third-party footage: never shipped, never quoted on the site, never used as frames in our sequences. What carries over is structure, cadence and attitude.

## 1. The strobe of editorial stills (`01-strobe-editorial-stills.mp4`)

**How it runs.** An 11.6-second loop. A small text card, one single-frame flash at 1.1 s, a burst of about 28 photos, a long text hold (about 5.4 s, with a bigger line held for 5 s), then a second burst of about 30 photos. About 58% of every loop is text on an empty dark screen; that stillness is what makes the bursts hit.

**Mechanics worth keeping**
- Every photo holds exactly 1/12 s ("on twos" at 24 fps). Hard cuts only: no dissolves, zooms or pans.
- A **home image** keeps returning between new ones (A-B-A-C-A-D), so the burst pulses around one picture instead of reading as a slideshow.
- **Back-and-forth pairs**: two photos swap 2–4 times in a row, a flicker.
- First burst: photos sit small in a 3:4 frame with dark margins, like prints on a wall. Second burst: the photos fill the screen.
- Black-and-white, one hard light per shot, concrete architecture with tiny figures, studio portraits on plain backdrops, faces mostly hidden, plain basics.
- Type: small, plain sans, centered, sentence case with a period. It cuts on and off; it never animates. The ground is charcoal, not pure black.

**What we do with it.** The entry sequence (below) and the "card" type style (`01-brand-system.md`).

**What we don't.** White frames at 12 per second. That is a seizure risk under WCAG 2.3.1 (more than three flashes a second). See "Safety" below.

## 2. The Bloodsport janitor (`02-bloodsport-janitor-long-take.mov`)

**How it runs.** 22 seconds, two shots. A gold tooth left on a white mat after a fight; a janitor crouched at mat level stares at it for nine seconds, rises, looks around, picks it up, bites it to test the gold, grins, and starts wiping up the blood. A man in the background never notices.

**Mechanics worth keeping**
- **One long fixed take.** The camera doesn't move; the subject's face and one small object carry the scene.
- **A tiny, precious detail is the whole subject.** In a dim brick-and-black frame, the only warm color is the gold.
- **Theft in plain view.** It happens in the open and nobody sees it: see everything, reveal nothing.
- The sound gets quieter (about 10 dB) as his focus narrows. Deadpan, silent-film comedy that works with the sound off.

**What we do with it.** The GCD is our gold tooth. On the home page and the product page, one long held view of the temple with the GCD, the only warm color on a dim screen, with a slow scroll-linked push-in (scale 1.00 to 1.06, nothing else moves). No arrows, no "new" badge, no caption pointing at it. One line of copy at most.

## 3. The 1983 Maxell commercial (`03-maxell-1983-silence-then-blast.mov`)

**How it runs.** A bare room shot straight on like a stage set: grey wall, white baseboard, a lamp, a speaker, a man in a black leather chair. A butler: "The usual, sir?" "Please." A calm voiceover. About 13 seconds of near-silence, half a second of total silence, then a wall of orchestra, and the camera slides from the speaker to the listener as his hair and tie stream back. Four shots in 25 seconds.

**Mechanics worth keeping**
- **Frontal, centered staging.** The camera faces the wall; the baseboard is one long horizontal line; very few props.
- **Patience, then one huge move.** Polite and quiet right up to the blast; the contrast is the joke and the claim.
- One exaggerated image carries the whole argument. No specs on screen.

**What we do with it.** Sound off first (`00-decisions.md` #19): silence becomes stillness, and the blast becomes **one hard cut in scale**. A page holds a small, frontal, centered composition (a frame on the stage, a horizon line, tiny type), then the visitor's first scroll cuts to the same subject at full bleed. Triggered by the visitor, never on a timer. Sound may be added later as an opt-in tap; nothing depends on it.

## The entry sequence

First visit to `/` only. Built from still images in the page (`<Entry/>`), not a video file.

| Time | Screen | Notes |
|---|---|---|
| Before | **Photosensitivity notice** (`08-copy.md`): Continue · Skip intro | Shown once; the choice is remembered. |
| 0.0–1.2 s | Charcoal ground, card: "See everything." | Card type, centered. |
| 1.2–3.6 s | **Burst 1**: about 28 frames at 12 per second inside a small 3:4 frame with dark margins; a home image recurs (A-B-A-C) and two pairs swap back and forth | All frames graded dark (see Safety). |
| 3.6–8.0 s | Card: "Reveal nothing." then the stacked logo held | The long hold. |
| 8.0–10.4 s | **Burst 2**: full bleed, at most 3 frames per second, one bright frame at most per second | Frames: cast and product, black-and-white. |
| 10.4–12.0 s | End card: the GCD in gold (the only color in the whole sequence) above "Darkest Shades" | Then a hard cut to the home page. |

- **Skip** is visible from the first frame (button, Esc, any scroll or swipe). Skipping or finishing sets `ds_entry=seen` for 30 days.
- **Never shown** on deep links (any path other than `/`, or any `utm_*`, `fbclid` or `gclid` parameter), to returning visitors, to crawlers, or when `prefers-reduced-motion` is set (that gets the cards and the end card only, no bursts).
- **Assets**: black-and-white versions of the lightbox shots and, once cast, the model photos, exported as AVIF/WebP at two sizes and preloaded during the first card. Under 1.5 MB total on mobile.

### Safety (WCAG 2.3.1)
- A general flash is a pair of opposing changes of 10% or more of maximum relative luminance where the darker state is below 0.80.
- **Burst 1 runs at 12 per second only because every frame is graded so no pixel's relative luminance exceeds 0.09** (sRGB grey ≤ 84). No change can reach 10%, so nothing in it counts as a flash at any size.
- **Burst 2 (full bleed) stays at or below 3 cuts per second** and at most one bright frame per second.
- `tools/flashcheck.py` (phase 0) renders the sequence at 1024×768 and 390×844, measures luminance change over every 341×256 window (a 10° field) and fails the build on more than three flashes in any second.

## The home page, in order

1. **Manifesto** (reference 1's cards, the Raf lens): a few huge lines in Owners Wide, sentence fragments, nothing for sale yet.
2. **The detail** (reference 2): the held GCD view.
3. **The drop** (reference 3): the drop's real status and date, small and frontal; the first scroll cuts to the eight frames as numbered prints on stage cards against the dark wall.
4. **The cast**: the seven models, SS90 patina, one per screen on mobile.
5. **The promises**: a plain spec sheet ($100, UV, polarized, TAC, acetate, 45-day exchange, 6-month warranty).
6. **The list**: email and SMS sign-up with consent wording.
7. **Footer**: horizontal logo, the GCD seal, the few links.
