# Runway takes, pass 1 (Oct 27 2026)

Web app, Gen-4 Turbo, image-to-video from `stills/<id>.jpg`, 9:16, 5 s, 25 credits per take, prompt enhancer untouched, seed random, HDR off (the HDR chip opens a plan upsell on Pro). Output is 720x1280 at 24 fps, 121 frames; the app offered no 1080p option for Gen-4 Turbo on this plan.

## Credits

| | |
|---|---|
| Balance at start | 255 |
| Takes generated | 10 |
| Credits spent | 250 |
| Balance at end | 5 |
| Cap in the brief | 600 |

The account held 255 credits at the start, not the 300 the first pass needs, so the pass stopped after ten first takes: no retakes, and c01 and c07 (last two in the priority order) were never generated. After the tenth take the Generate button turned into a "Buy now, 5,000 credits, $50" purchase prompt, which is the stop condition in the brief. A "credits running low" notice appeared after the third take and was dismissed without action. Nothing was bought and the plan was not changed.

## Verdicts

| Clip | Take | Verdict | Why |
|---|---|---|---|
| c11 | t1 | REJECT | "wall of air" rendered as a white smoke cloud filling the frame f20-f70; hair static; the man slumps forward f80+ |
| c12 | t1 | **ACCEPT** | camera locked, emblem steady at 200 percent on f16/f33/f49, lenses opaque, hair streams back continuously (moderate, not violent) |
| c03 | t1 | REJECT | action reversed: the hand takes the glasses off from f24, eyes readable f40 on |
| c05 | t1 | REJECT | her lenses turn translucent brown f68-f78 during the rise and the eye socket reads through; lens outline rounds; the door never closes. f12-f66 (clasp, chin up, start of rise) is clean |
| c09 | t1 | **ACCEPT-WINDOW 74-119** | hand picks up the tooth f76-f92 and lifts it out of the top; glasses seated and opaque, emblem steady. f28-f70 has an unasked hand-on-glasses beat, excluded by the window. The head never lowers because the still already has it at table height |
| c02 | t1 | REJECT | lever never pulled; wire temples double f60-f100; glasses drop to the lap instead of rising. f10-f47 (folded glasses out of the pocket, hands meet) is clean and could cover shot 03 with a hold |
| c10 | t1 | REJECT | tooth swells into a flat disc f56-f72; pocket and remote beats absent; head turns to camera f88+. f12-f48 covers the tooth test only |
| c04 | t1 | REJECT | he steps out, turns, shuts the door, then walks away along the street side; never rounds the bumper to her door. Facade, SUV and feet clean; f8-f27 covers shot 05 |
| c08 | t1 | REJECT | table pull absent; both stand up and walk toward camera f62+. f8-f52 (settle, hold, head dip) covers shot 12 |
| c06 | t1 | REJECT | continuous walk for all 120 frames, no stop, greeting or head turn; the couple recedes. f8-f44 covers shot 09 |
| c01 | | not generated | credits exhausted |
| c07 | | not generated | credits exhausted |

Accepted: c12, c09 (window 74-119). Every other clip fails pass 1 and holds its still in the edit, as the animatic does. Contact sheets (`<clip>-t1-sheet.jpg`, every 4th frame) are kept beside each take; the per-window slow-motion files were deleted after judging and are rebuilt with the command in the operator guide.

## What the retakes need (for pass 2, 25 credits each)

- **c11**: Gen-4 Turbo reads "wall of air" as smoke. Say "hurricane-force wind on hair and clothing only, no smoke, no fog, no haze, the air stays clear" and keep the furniture lines. Highest priority: the full blast is 122 master frames.
- **c03**: the model reversed the gesture. Say "the glasses are being put on, the temple slides down and back over the ear, the glasses are never lifted or removed" and drop the light sweep.
- **c05**: she rises too fast and the lenses lighten as her face crosses the window lights. Ask for "she rises slowly" and "the lenses stay solid black, no reflections", and consider ending the clip before the door close (shot 08 cut short on the turn, per the retake note).
- **c02**: order the beats ("first the right hand releases the lever, then the left hand enters the pocket") and end on the folded glasses rising, letting c03 carry the unfold.
- **c10**: too dense. Drop the pocket beat from the prompt; ask for the tooth test, then the remote rising and one press; retime in post.
- **c04**: split the ask ("he steps out and walks toward the rear bumper" only) and cut shot 06 from the end of the walk.
- **c08**: "the couple stays seated throughout"; ask only for the lean and the table drag.
- **c06**: lock the camera ("camera static") and ask for the stop at the podium and "a few degrees only" head turn.
- **c01, c07**: first takes still owed.

## Still mismatch

c11's still (s11) renders the woman's frames plain black; the other stills with her (s05, s06, s08) show tortoise. The take was judged against s11 as the guide says. If s11 is regenerated with tortoise frames before pass 2, the c11 retake should use the new still.

## Hygiene

Only the twelve stills were uploaded. Session title in the app was left as the default. Prompts were pasted verbatim from `pack/shots.json`; no venue, brand or person name was added.
