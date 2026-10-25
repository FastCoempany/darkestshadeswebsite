# S08, the lounge: M4 in F05 (DS-CAST-M4-S08-F05-v01)

M4 (the founder's own generated man, `docs/brief/00-decisions.md` #40) sitting forward on a distressed rustic
red leather chesterfield in the lounge (S08, #41), wearing F05 *Jackie Gave Them Nothing*. Built with free
tools only: Blender 5.2 (Cycles, CPU), OpenCV, scikit-image, pymatting, rembg (ISNet), Depth Anything V2
Small, InsightFace. No image generator.

`run.sh` makes it from start to finish with v01's settings (about an hour on two CPU cores). The founder's
portrait of M4 is not in the repo: it goes in `work/people/raw/M4-founder-01.jpg`. The working files go in
`work/people/DS-CAST-M4-S08-F05-v01/data/` (or `$S08_WORK`), the picture beside them.

## How it is made

1. **M4** (`upscale_man.py`, `man_prep.py`): his portrait (a screenshot) without its white top band,
   doubled (EDSR on the head, FSRCNN elsewhere: `tools/photo/wear.py` `upscaled`), mirrored so the wearer's
   right (the GCD's side) faces the camera, the screenshot's tab cropped off, cut out (ISNet for the shape,
   closed-form matting against the studio's fitted backdrop for the hair and the shearling), his colours
   freed of the backdrop's white.
2. **The stand-in glasses** he arrived in (`standin.py`, `retouch.py`, `retouch2.py`): masked; where F05
   does not cover them (the thick near temple from the ear to the front, slivers past F05's outline) the
   skin and hair are rebuilt: each column of the temple's band filled from just above and below it, the
   hair above it cloned down to a hairline that ends under F05's temple, pores and freckles borrowed from
   the skin nearby. The stand-in's maker's name went with its temple. Then the 1:1 checks: the fold the
   stand-in's heavy top pressed into his brow healed, the far temple above F05's far rim refilled, and the
   photograph kept under the nose's tip (that dark band is his skin in shadow, not the stand-in).
3. **F05's pose** (`fit_f05.py`, kept in `m4_f05_pose.json`): the rebuilt F05 (`tools/blender/frame3d.py`,
   its drawings) fitted to the stand-in: its top edge along the stand-in's, its ends at the stand-in's ends,
   its near temple through the point where the stand-in's temple crosses the ear (68 mm from F05's hinge,
   splayed 3 deg), on the portrait's own lens (85 mm equivalent). Yaw 40 deg, 815 mm from the camera: 7.3 px
   per mm on the face, which agrees with his ear (about 63 mm long) and lower face.
4. **His head in 3D** (`man_geo.py`, `build_head.py`): Depth Anything's depth, put in millimetres against
   F05's own surface where the stand-in lay, the stand-in filled from the face round it, the skin kept at
   least 6 mm behind the frame (but not the nose, which stands in front of the far lens).
5. **The lounge** (`art.py`, `lounge_bg.py`, `lounge_common.py`): the founder's reference room kept, its art
   and couch replaced. The wall: black-painted brick (wobbly joints, the paint thinner in them, old grey
   drips everywhere) with new hand-painted art: a crimson sweep with drips, a cream stroke falling through
   it, a bone veil of dry brushwork, charcoal lines (no words, no faces). The chesterfield: its back's
   diamond tufting built as a height field (rhombus pillows rounding up from the folds between the
   buttons, the buttons pulled in, the leather gathered round them), its rolled top and the right arm's
   scroll pleated where the tufting runs into them; the leather an oxblood dye rubbed through in blotches
   to the paler crust on every high point, crackled where worn, waxier in the folds. The light: a magenta
   key front right (the reference's), a blue rim behind left, a warm wash on the art, a warm lamp beyond
   the arm, candles off to the left, a soft warm fill; the camera is the portrait's own, widened to the
   right, f/5.6, focused on his eyes.
6. **M4 relit** (`relight.py`): his colours divided by the studio's light (a key from the camera's right
   over a strong ambient, read off his skin) and multiplied by the lounge's light at his surface (the depth
   model's normals; each light's position, colour, power and cone; the key's shadows marched over his
   depth and softened along his surface but not across a jump in it), the blue rim along the silhouette's
   edges that face it. For him alone the key is a little less saturated and wraps its terminator as a
   broad source on skin does, the lamp beyond the arm is dimmer, and the fill takes the key's magenta (the
   room's bounce off the red leather and the art): in its absence his shadows read green beside the key.
7. **F05 in the lounge's light** (`f05_lounge.py`, `gcd_place.py`): the frame at the pose, the GCD on the near
   end piece, the near temple's metal run to the ear; gloss black acetate mirroring a dark room (a studio's
   curtains and lamps, tinted to the lounge, glossy rays only), satin black metal (the blue rim only a
   sheen on it); the lenses dark glass showing only what they mirror. Its shadow on his face: his head mesh
   lit with and without the frame.
8. **Composite** (`composite.py`): the lounge (rendered at half size: it is out of focus), M4 relit with
   F05's shadow (where the frame's far side pierces the nose's mesh the shadow pass's line is closed out),
   the near temple's contact shadow and the front's contact shadow, F05 over him; his nose and the skin
   under its tip in front of the frame's far side, his ear in front of the temple's end; where the stand-in
   reached past his outline, the room. Then a light wrap at his edges, a faint bloom, a filmic shoulder, a
   gentle S, grain, a vignette.
