# The usability test: five people, their own phones

*A draft from D5 (Nov 8 2026); D7 finishes it against the built wall and the phone link.*

Run by Antaeus after R2 (DRAWER-WALL.md, The usability test; O16). Five people on their own phones, at least two iPhones and two Androids, 15 minutes each, thinking aloud, in person or on a video call with screen sharing. Half start with tap first, half with pull first; everyone tries both. Nothing is explained before the tasks: the wall has to explain itself.

## Before each session

- Open the phone link (the top of `WALL-PROGRESS.md`) on the tester's phone in their usual browser. Add `?mech=pull` for the pull-first start; without it the wall is tap first. Add `debug=1` to the query (`?debug=1`, or `?mech=pull&debug=1`) so the event log is kept.
- Say only: "This is a page from a sunglasses brand. I'll ask you to do a few things. Say what you're thinking as you go. Nothing you do is wrong."
- Start a stopwatch at the first task.

## The tasks, in order

1. **"Find a frame you like and look at it closely."** Watch for: do they find the drawer, the pull, the lift? How long to the first open?
2. **"Show me the gold emblem up close."** Do they lift, turn, pinch, or go to the photographs?
3. **"Put it back and look at another one."** Do they find put back, shut, close? Any accidental scroll or open on the way?
4. **"What does it cost?"** Is $100 seen without hunting?
5. **Free play, two minutes.** Then the three questions: What felt natural? What felt in the way? Which version would you keep, after trying the other one (switch `?mech=` now and let them try the same first task again)?

## What to record, per person

| Person | Phone, browser | Started with | Time to first open (s) | Accidental opens | Accidental scrolls | Lifted | Turned | Zoomed | Opened the photographs | $100 seen without hunting | Their pick | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | | tap / pull | | | | yes / no | yes / no | yes / no | yes / no | yes / no | tap / pull | |
| 2 | | | | | | | | | | | | |
| 3 | | | | | | | | | | | | |
| 4 | | | | | | | | | | | | |
| 5 | | | | | | | | | | | | |

- **Accidental open:** a drawer view opened when they meant to scroll. **Accidental scroll:** the wall moved when they meant to open or pull.
- At the end of each session, tap "Copy the event log" (shown with `?debug=1`) and paste it into a note named for the person; it holds every open, pull, lift, turn, zoom and the states in between with their times.

## The rule

The version with fewer misfires (accidental opens plus accidental scrolls, summed over the five) and a faster first open wins; a tie goes to tap first. Write the totals here and the decision in `00-decisions.md` O16, quoting what people said.

| | Tap first | Pull first |
|---|---|---|
| Misfires, total | | |
| Time to first open, median (s) | | |
| Picked by | | |

## What to send back

The table above, the five event logs, and three sentences per person in their own words. Those go into `WALL-PROGRESS.md` under "Usability results" (run 2, D8, reads them from there).
