# Runway operator guide: 12 clips in the web app, 600-credit cap

For the session on the founder's computer (Claude Desktop with Claude in Chrome, or a person by hand). Everything here is the web app at app.runwayml.com on the founder's existing plan. No API key, no API calls, no uploads anywhere except the still into the Runway generator.

Pack root (absolute, every path below is under it):
`film/1985-the-club/`

| What | Where |
|---|---|
| Clip plan (prompts, windows, QC) | `pack/shots.json` |
| First-frame stills to upload | `stills/<still id>.jpg` (s01 ... s12; made from `pack/stills.json` by the stills builder) |
| Downloaded takes | `takes/<clip id>-t<N>.mp4` (c01-t1.mp4, c01-t2.mp4 ...) |
| Credit and verdict log | `takes/LOG.csv` (create on the first take) |

## 0. Before the first generation

1. Confirm the 12 stills exist and are 9:16: `python3 -I -c "from PIL import Image; import glob; [print(p, Image.open(p).size) for p in sorted(glob.glob('stills/s*.jpg'))]"` from the pack root. A still that is not 9:16 is re-exported or padded locally before upload; the web app will otherwise crop it.
2. Open `pack/shots.json` and keep it visible. Each clip entry has `first_frame_still`, `prompt_text`, `qc`, `takes_budget`, `retake_note`.
3. Note the credit balance shown in the app (top right or Settings > Plan) in `takes/LOG.csv` as the starting balance. The cap for this whole pass is 600 credits of spend, retakes included. Gen-4 Turbo at 5 s costs 25 credits per take; 24 takes is the absolute maximum.
4. Create `takes/LOG.csv` with this header:
   `timestamp,clip,take,still,credits_shown,balance_after,seed,verdict,reason,file`

## 1. Generation order

Do not go in story order. Hero and highest-risk clips first, so a failure of the thesis shots is known before the budget is spent on the walk-ins:

1. c11 (blast two-shot), 2. c12 (final portrait), 3. c03 (emblem macro), 4. c05 (her rise), 5. c09 (table-height tooth), 6. c02 (lever, pocket, unfold), 7. c10 (tooth test, pocket, click), 8. c04 (exit and walk round), 9. c08 (room, table pull), 10. c06 (hallway, greeting), 11. c01 (SUV arrives), 12. c07 (remote slide).

One take of each first (300 credits). Judge every take before the next generation. Only then spend retakes, in the same priority order, within each clip's `takes_budget` and never past 600 total.

## 2. One clip, step by step (web app)

Claude in Chrome: load the chrome-browser skill first; work in a new tab; after `Generate`, poll the tab every 30-60 s rather than spamming clicks. By hand: the same steps.

1. Go to `https://app.runwayml.com` and sign in on the founder's account (already signed in on the founder's Chrome).
2. In the left sidebar choose **Generate Video** (the tool may be labelled "Video" or "Generate video"; any entry that opens the video generator is right).
3. **Model**: open the model selector in the prompt bar and pick **Gen-4 Turbo**. Not Gen-4.5, not Gen-4, not Aleph, not any "Act" model.
4. **Input**: click the image/upload area ("Drop an image", "Upload", or the image icon) and choose `stills/<first_frame_still>.jpg` for the clip. Wait until the thumbnail shows the still. This is image-to-video from a single first frame; there is no last frame and no reference video.
5. **Settings** (gear or the chips beside the prompt): aspect ratio **9:16**; duration **5 s** (never 10 s: that doubles the cost); resolution the highest the app offers for 9:16 (1080x1920 when offered, otherwise 720x1280; do not buy an upscale). Leave seed random on take 1.
6. **Prompt**: paste `prompt_text` exactly as it is in `shots.json`. Do not add the still prompt, the shot number, the brand name or any name of a place. If the app has a "prompt enhancer" or "auto-improve" toggle, leave it off.
7. Check the credit cost shown next to the Generate button. It must read **25**. If it reads anything else, a setting is wrong (duration, resolution or model); fix it before generating.
8. Click **Generate**. Wait for the render (usually 1-3 minutes). Do not queue a second generation of the same clip while one is running.
9. When it finishes, open the result, use the download control (download icon or the "..." menu > Download) and save the MP4. Chrome drops it in Downloads; move it: `mv ~/Downloads/<name>.mp4 takes/<clipid>-t<N>.mp4` (N = 1 for the first take of that clip, 2 for the second).
10. Log the row in `takes/LOG.csv` immediately: timestamp, clip, take, still, credits shown (25), the balance the app shows after, the seed if the app displays one, verdict left blank until judged, file path.
11. Judge the take (section 3). Fill in verdict and reason.
12. Stop generating the moment total spend reaches 600 credits (starting balance minus current balance), whatever is left undone. Record what was not retaken in NOTES.md.

## 3. Judging a take

Each clip has `qc` (two or three rejection checks) and `covers` (the frame windows that will be cut). Judge only the frames that will be used, plus a margin of 6 frames on each side; a flaw outside the window does not reject the take.

Local checks from the pack root (ffmpeg and ffprobe are present):

```
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames -of csv=p=0 takes/c11-t1.mp4
# contact sheet, every 4th frame, 6 columns
ffmpeg -y -i takes/c11-t1.mp4 -vf "select=not(mod(n\,4)),scale=270:-1,tile=6x5" -frames:v 1 takes/c11-t1-sheet.jpg
# first, middle and last used frame at full size (use_frames from shots.json)
ffmpeg -y -i takes/c11-t1.mp4 -vf "select=eq(n\,0)+eq(n\,60)+eq(n\,119)" -vsync 0 takes/c11-t1-f%03d.jpg
# 4x slow motion of the used window, for the eyewear checks
ffmpeg -y -i takes/c03-t1.mp4 -vf "trim=start_frame=24:end_frame=48,setpts=4*PTS" takes/c03-t1-slow.mp4
```

Checklist, in order, for every take:

1. **Eyes**: at no used frame is an eye, eyelid or eye socket readable through or around the lenses. Zoom to 200 percent on the lens region of the first, middle and last used frame. Any eye = reject.
2. **Frame shape**: the sunglasses on the last used frame match the still: same width, same lens shape, same bridge, temples not thickened, emblem still on the right end-piece (man) or right wing (woman), not mirrored, not doubled. Any drift = reject.
3. **Seat**: the glasses move with the head and never independently of it (slipping, rattling, floating off the nose, clipping into skin). Any independent motion = reject.
4. **The clip's own `qc` list** (building warps, hands wrong, furniture warps, hair not moving on the blast, camera shake on c11/c12). Any hit = reject.
5. **Motion fits the window**: the action the `covers` list needs happens inside `use_frames`, or inside another contiguous window of the same length that can be slid to. If the action is there but elsewhere, accept and note the new window in `LOG.csv` (reason column: "window 30-61").
6. **Nothing extra**: no text, logo, badge, watermark, readable sign, or a face where none was asked for (c01, c07).

Verdicts: `ACCEPT`, `ACCEPT-WINDOW <in>-<out>` (usable with a slid window), `REJECT <qc item>`.

Judging rules from the brief: a failing take is regenerated, never fixed; a take with a head turn that reveals an eye is never rescued in post; the camera must not shake on the blast; the glasses must be the most stable thing in c11 and c12.

## 4. When a take fails

1. Read the clip's `retake_note` in `shots.json`; it says what to change.
2. Retake only if the clip's `takes_budget` allows a second take and total spend stays under 600. Priority order is in `shots.json` > `summary.retake_priority`.
3. Keep the same still. Change only the prompt, by the retake note: tighten the order of actions, slow the action, or drop the failing beat. Never ask for motion on the glasses. If the app shows a seed, do not reuse the failed seed.
4. If the app refuses a generation on content grounds, do not resubmit the same input unchanged: reword the physics (sound pressure, wind, force) and avoid "explosion" or "detonate"; log the refusal with its credit charge if any.
5. If a clip fails twice, mark it `FAILED` in the log and move on; the editor holds the still for that clip's frames (the animatic already does this) and NOTES.md records it for the founder.
6. A rejected take still cost 25 credits: it counts toward the 600.

## 5. Naming and hygiene

- Takes: `takes/c07-t1.mp4`, `takes/c07-t2.mp4`. Never rename a take after it is logged. Derived files (sheets, frames, slow-motion) carry the take name plus a suffix, as in section 3.
- Stills: `stills/s07.jpg`, exactly the `first_frame_still` id of the clip.
- Nothing in the app's prompt, project name or file names may contain a venue name, a street address, a person's real name, a third-party film or brand name, or the designer's name the website rules forbid. Project title in the app, if it asks: "DS film pass 1".
- Never upload reference photos, the two study recordings, product photographs or cast portraits to the app. The still is the only upload.
- After the pass, copy `takes/LOG.csv` totals into NOTES.md: takes made, credits spent, clips accepted, clips failed.

## 6. Hand-off to the editor

Accepted takes and their windows go to the edit exactly as `covers` says: `use_frames` from the take, placed at `place_at_frames` on the 720-frame 24 fps master. c11's 120 frames fill 122 master frames by holding the last frame for 2 frames. The conform step (`ffprobe`, then `fps=24` and trims by frame) is in `pack/NOTES.md`.
