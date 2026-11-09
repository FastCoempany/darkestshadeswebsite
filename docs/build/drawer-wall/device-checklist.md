# The real-device checklist (for Antaeus, R2)

*A draft from D5 (Nov 8 2026); D7 finishes it against the built wall and the phone link.*

The phone build's link is at the top of `WALL-PROGRESS.md`. Run this on an iPhone and on an Android, in their usual browsers (Safari, Chrome), before the usability test. Tick what works; write a line for what doesn't, with the phone, the browser and what you saw. Nothing here needs an account or a purchase.

## On each phone

| Step | What to do | What should happen | iPhone | Android |
|---|---|---|---|---|
| Open | Open the link; wait for the wall | The wall of eight drawers, each with its look number, name and $100; the page's background pure black; nothing else on the screen | | |
| Scroll | Swipe up and down on the drawers | The wall scrolls; no drawer opens from a swipe | | |
| Tap | Tap a drawer | It comes forward into the drawer view, shut, the name and $100 at the top; after a moment, "Pull it toward you" | | |
| Pull | Put a finger on the drawer and pull down slowly, then let go halfway; then pull all the way | It follows the finger; let go early and it slides shut, let go late and it slides open; a short tick on Android at each stop | | |
| Buttons | Tap "Shut the drawer", then "Open the drawer" | The drawer does the same without a pull | | |
| Lift | With the drawer open, tap the frame (or "Lift them out") | The frame rises toward you into the light and turns to a three-quarter view; the drawer dims behind it | | |
| Turn | One finger, left and right, up and down | It turns freely sideways and a little up and down, and keeps turning a little after you let go | | |
| Pinch | Pinch out; double-tap; pinch in | It comes closer (up to 3×) and stays sharp; double-tap goes between 1× and 2.2×; the emblem on the right temple is readable up close | | |
| Photographs | Tap "See the photographs" | The real photographs on their pale ground; pinch and drag down to the pixel; once you are closer, Up, Down, Left and Right move the picture too; the angle buttons switch between them; "Back to the frame" returns | | |
| Smoothness | Pull slowly and fast; turn the lifted frame slowly and fast | Both keep up with the finger with no stutter or frozen moments (the aim is 60 frames a second; the lab could only measure the machine's own speed, not a throttled phone) | | |
| Put back | Tap "Put them back", then "Shut the drawer", then "Close" | The frame settles back into the drawer, the drawer shuts, the wall is there again with that drawer in focus | | |
| Another | Open a second drawer | The same, without a longer wait than the first (its frames were fetched while you looked) | | |
| Pull first | Add `?mech=pull` to the link and reload; put a finger on a knob and pull down; then swipe on a drawer's face | The drawer view opens under your finger and the pull continues there; the face still scrolls the wall | | |
| Rotate | Turn the phone to landscape with the wall showing, and with a drawer open | The wall re-lays itself (4 across on a wide screen, 2 across on a narrow one); the drawer view keeps its 4:5 stage centred | | |
| Low power | Turn on Low Power Mode (iPhone) or Battery Saver (Android); open, pull, lift, turn | Everything still works; turning may be a little less smooth; nothing breaks | | |
| Weak connection | Turn off Wi-Fi and use a weak signal (or enable data saver / Lite mode); reload | The wall appears (the plate first, then the labels); opening a drawer shows its first frame while the rest loads; with Save-Data on, the lift shows a still instead of the live frame | | |
| Records | Add `?panel=1` to the link | A panel "Records (example data)"; set one drawer to sold out: only that drawer goes dark with "Sold out"; set it to locked: "Not yet." and it no longer opens; set it to hidden: it goes dark with no label | | |
| Log | Add `?debug=1`, do a few things, tap "Copy the event log" | A log you can paste somewhere; this is what the usability sessions copy at the end | | |

## What to send back

The table with ticks and notes, the phones and their OS versions, and screenshots of anything wrong. R2 is answered on the D7 pull request; O15–O18 can be answered there too.
