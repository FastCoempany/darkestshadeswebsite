# The real-device checklist (for Antaeus, R2)

The phone build's link is at the top of `WALL-PROGRESS.md`: a private Artifact, which opens for you signed in to claude.ai (or in the Claude app); for anyone else's phone, share it first from the page's Share menu ("anyone with the link", or an email invitation). Run this on an iPhone and on an Android, in their usual browsers (Safari, Chrome), before the usability test. Tick what works; write a line for what doesn't, with the phone, the browser and what you saw. Nothing here needs an account beyond your own or a purchase. The switches are plain names after `#` on the link (`#pull`, `#panel`, `#debug`, joined with hyphens for more than one: `#pull-debug`); reload after adding one.

The first row is the D7 exit the run could not take itself: the VM has no signed-in browser, so the published link was never opened from it. If the wall does not appear at all, say what the page shows instead (a sign-in prompt, a blank page, an error) and the run falls back to GitHub Pages, only with your yes (O18).

## On each phone

| Step | What to do | What should happen | iPhone | Android |
|---|---|---|---|---|
| Open | Open the link; wait for the wall | The wall of eight drawers, each with its look number and name, and no price; the page's background pure black; nothing else on the screen. Take a screenshot | | |
| Scroll | Swipe up and down on the drawers | The wall scrolls; no drawer opens from a swipe | | |
| Tap | Tap a drawer | It comes forward into the drawer view, shut, the name at the top; after a moment, "Pull it toward you" | | |
| Pull | Put a finger on the drawer and pull down slowly, then let go halfway; then pull all the way | It follows the finger; let go early and it slides shut, let go late and it slides open; a short tick on Android at each stop | | |
| Buttons | Tap "Shut the drawer", then "Open the drawer" | The drawer does the same without a pull | | |
| Lift | With the drawer open, tap the frame (or "Lift them out") | The frame rises toward you into the light and turns to a three-quarter view; the drawer behind it empties, dims and softens | | |
| Turn | One finger, any way: sideways, up and down, round in circles, over and upside down; start on the glasses, then start in the dark above the picture, then down near the buttons; then start a drag while they are still rising; then "Turn left", "Tilt up" | It turns the way your finger goes wherever the finger starts (only the buttons themselves are deaf), with no stop in any direction, keeps turning a little after you let go, and the buttons step the same way; a finger that lands while they rise turns them as soon as they rest; stood on end or turned over it stays whole in the view; "Reset" brings it back to where it rose. Two fingers only pinch: a two-finger drag or twist does nothing yet (O21); say if you expect them to | | |
| Pinch | Pinch out; double-tap; pinch in; then "Closer", "Further", "Reset" | It comes closer (up to 3×) and stays sharp; double-tap goes between 1× and 2.2×; the emblem on the frame's right side is readable up close (on the right temple; on F02 the right wing of the front, on F04 and F05 the right end-piece, as each frame's record places it); the buttons do the same | | |
| Photographs | Tap "See the photographs" | The real photographs on their pale ground; pinch and drag down to the pixel; once you are closer, Up, Down, Left and Right move the picture too; the angle buttons switch between them; "Back to the frame" returns | | |
| Smoothness | Pull slowly and fast; turn the lifted frame slowly and fast | Both keep up with the finger with no stutter or frozen moments (the aim is 60 frames a second; the lab could only measure the machine's own speed, not a throttled phone) | | |
| Put back | Tap once on the drawer behind the glasses without moving your finger; lift them again; then tap "Put them back", then "Shut the drawer", then "Close" | The frame settles back into the drawer, the drawer shuts, the wall is there again with that drawer in focus | | |
| Another | Open a second drawer, then come back to the first | The second drawer's first frame appears as it is tapped and the rest of its frames arrive as it opens (the first and the last frame first); a drawer you opened before loads the same way again (the wall keeps nothing between opens; if it comes back faster, your phone's cache did it, and say so) | | |
| Pull first | Add `#pull` to the link and reload; put a finger on a knob and pull down; then swipe on a drawer's face | The drawer view opens under your finger and the pull continues there; the face still scrolls the wall | | |
| Rotate | Turn the phone to landscape with the wall showing, and with a drawer open and a frame lifted | The wall re-lays itself (4 across on a wide screen, 2 across on a narrow one); the drawer view keeps its 4:5 stage centred; the lifted frame redraws at the new size | | |
| Low power | Turn on Low Power Mode (iPhone) or Battery Saver (Android); open, pull, lift, turn | Everything still works; turning may be a little less smooth; nothing breaks | | |
| Weak connection | Turn off Wi-Fi and use a weak signal (or enable data saver / Lite mode); reload | The wall appears (the plate first, then the labels); opening a drawer shows its first frame while the rest loads; with Save-Data on, the lift shows a still instead of the live frame | | |
| Records | Add `#panel` to the link and reload | A panel "Records (example data)"; set one drawer to sold out: only that drawer goes dark with "Sold out" under its name; set it to locked: "Not yet." and it no longer opens; set it to hidden: it goes dark with no label | | |
| Log | Add `#debug`, reload, do a few things, tap "Copy the event log" | A log you can paste somewhere; this is what the usability sessions copy at the end | | |

## What to send back

The table with ticks and notes, the phones and their OS versions, the screenshot from the Open row, and screenshots of anything wrong. R2 is answered on the D7 pull request; O15–O18 and the open questions in `WALL-PROGRESS.md` can be answered there too.
