# 1985 / The Club: 30-second 9:16 mockup film

Non-commercial mockup, founder's decisions of Oct 27 2026: all shots generated as video in the Runway web app (Gen-4 Turbo, 5 s, 9:16) from the first-frame stills here; glasses generated for this film only (decision #16 waived for the mockup); cast M3 and W1 from the seven; 600-credit cap, no review stops. Nothing in this folder ships on the site.

| Folder | What |
|---|---|
| `pack/shots.json` | the 12-clip plan: still, prompt, frame windows, QC checks, takes budget |
| `pack/RUNWAY_OPERATOR.md` | step-by-step procedure for running the clips in app.runwayml.com and judging takes |
| `pack/stills.json` | the prompts the stills were generated from (Figma, gpt-image-2.5-sunburst) |
| `stills/s01.jpg … s12.jpg` | first frames, 1080x1920, one per clip |
| `post/endcard-01.png`, `post/endcard-02.png` | the two end cards (frames 653-684 and 685-719) |
| `takes/` | downloaded Runway takes go here as `<clip>-t<N>.mp4` plus `LOG.csv`; commit and push them on this branch |

The edit, grade, mix and master are built in the cloud session from `takes/` once the takes are pushed.
