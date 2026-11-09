# The usability test: five people, their own phones

Run by Antaeus after R2 (DRAWER-WALL.md, The usability test; O16). Five people on their own phones, at least two iPhones and two Androids, 15 minutes each, thinking aloud, in person or on a video call with screen sharing. Half start with tap first, half with pull first; everyone tries both. Nothing is explained before the tasks: the wall has to explain itself.

## The link and its switches

The phone link is at the top of `WALL-PROGRESS.md`: a private Artifact, so the tester's phone needs to be signed in to claude.ai (or Antaeus opens it on his own phone and hands it over). The wall takes its switches as a plain name after `#` on that link, hyphens joining more than one:

| Switch | On the phone link | On a plain web host |
|---|---|---|
| Pull first (the knob opens the drawer) | `#pull` | `?mech=pull` |
| Keep the event log, with its copy button | `#debug` | `?debug=1` |
| Both | `#pull-debug` | `?mech=pull&debug=1` |
| The records panel (not for the testers) | `#panel` | `?panel=1` |

Without a switch the wall is tap first.

## Before each session

- Open the phone link on the tester's phone in their usual browser. For a tap-first start add `#debug`; for a pull-first start add `#pull-debug`. Reload once so the switch takes.
- Say only: "This is a page from a sunglasses brand. I'll ask you to do a few things. Say what you're thinking as you go. Nothing you do is wrong."
- Start a stopwatch at the first task.

## The tasks, in order

1. **"Find a frame you like and look at it closely."** Watch for: do they find the drawer, the pull, the lift? How long to the first open?
2. **"Show me the gold emblem up close."** Do they lift, turn, pinch, or go to the photographs?
3. **"Put it back and look at another one."** Do they find put back, shut, close? Any accidental scroll or open on the way?
4. **"What does it cost?"** Is $100 seen without hunting?
5. **Free play, two minutes.** Then the three questions: What felt natural? What felt in the way? Which version would you keep, after trying the other one (switch the start now, `#pull-debug` or `#debug`, reload, and let them try the first task again)?

## What to record, per person

| Person | Phone, browser | Started with | Time to first open (s) | Accidental opens | Accidental scrolls | Lifted | Turned | Zoomed | Opened the photographs | $100 seen without hunting | Their pick | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | | tap / pull | | | | yes / no | yes / no | yes / no | yes / no | yes / no | tap / pull | |
| 2 | | | | | | | | | | | | |
| 3 | | | | | | | | | | | | |
| 4 | | | | | | | | | | | | |
| 5 | | | | | | | | | | | | |

- **Accidental open:** a drawer view opened when they meant to scroll. **Accidental scroll:** the wall moved when they meant to open or pull.
- At the end of each session, tap "Copy the event log" (shown with `#debug`) and paste it into a note named for the person; it holds every open, pull, lift, turn, zoom and the states in between with their times. If the copy button does nothing on that phone, the log is also printed to the browser's console under `[wall]`.

## The rule

The version with fewer misfires (accidental opens plus accidental scrolls, summed over the five) and a faster first open wins; a tie goes to tap first. Write the totals here and the decision in `00-decisions.md` O16, quoting what people said.

| | Tap first | Pull first |
|---|---|---|
| Misfires, total | | |
| Time to first open, median (s) | | |
| Picked by | | |

## What to send back

The table above, the five event logs, and three sentences per person in their own words. Those go into `WALL-PROGRESS.md` under "Usability results" (run 2, D8, reads them from there).
