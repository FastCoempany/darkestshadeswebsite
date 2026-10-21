# Prompt pack

Every on-model image starts as one generated portrait without glasses (`docs/brief/07-photography.md`, track 2): Figma `generate_image`, model `gpt-image-2.5-sunburst`, in the file [Darkest Shades · Casting + Photography](https://www.figma.com/design/0aADcg6X248iXssGmxZ2jj/Darkest-Shades-%C2%B7-Casting---Photography) (`0aADcg6X248iXssGmxZ2jj`). The real frame is composited afterwards with `tools/photo/wear.py`. A prompt is five blocks, pasted in this order and never paraphrased:

1. the **scene block** below;
2. the person's **bible**, word for word from `model-bibles.md`;
3. one **wardrobe** line;
4. the **head** line;
5. the fixed **tail**.

## Scene blocks

**S01 · Runway.** Fashion show photograph on a bare runway. A white floor runs straight toward the camera; behind the model the space is a black void. A row of hard overhead runway lights and a hard frontal flash from the photographers' pit at the end of the runway. The model walks straight toward the camera, mid-stride, centered, framed from the knees up. 200 mm telephoto from the end of the runway, eye level, slight compression.

**S02 · Grey seamless.** Photograph against a mid-grey seamless paper backdrop that curves into the floor. Flat, soft overhead light, even on the face, a soft shadow at the feet. The model stands still, centered, facing the camera, framed from mid-thigh up. 85 mm lens, eye level.

**S03 · Stairwell.** A bare concrete stairwell with worn steps and a plain metal handrail. One hard shaft of daylight from a high window above falls across the landing; the rest is in deep shadow. The model stands on the landing in the shaft of light, facing the camera, framed from the waist up, the stairs rising behind. 50 mm lens, eye level.

**S04 · Corridor.** A long institutional corridor with a pale terrazzo floor and bare painted walls. Fluorescent tubes overhead recede into the distance; a hard on-camera flash lights the model. The model stands in the middle of the corridor facing the camera, framed from the waist up, the corridor converging to a vanishing point behind the head. 50 mm lens, eye level.

**S05 · Doorway.** A dark room with a dark floor. One hard key light comes through an open doorway behind the camera and falls on the model as a sharp wedge of light; everything outside the wedge falls to near black. The model stands in the light at the threshold, facing the camera, framed from the waist up. 85 mm lens, eye level.

**S06 · Studio, black.** Studio portrait against a black backdrop. Head and shoulders, the head centered in the upper half of the frame. One hard key light from the front, a little to the camera's left and a little above eye level, no fill: the far side of the face falls into shadow. 85 mm lens, eye level.

**S07 · Studio, warm white.** Studio portrait photograph against a warm white seamless paper backdrop. Head and shoulders, framed from mid-chest up, the head centered in the upper half of the frame. On-camera flash just above the lens: crisp, even light on the face and a short, hard-edged shadow on the backdrop just behind the head. 85 mm lens, eye level.

## Wardrobe lines

Uniform-like, no logos, nothing that competes with the frame. One per image:

- `Wardrobe: a black nylon jacket zipped to the collar, no logos.`
- `Wardrobe: a crisp white cotton shirt buttoned to the collar, no tie, no logos.`
- `Wardrobe: a fine black merino crew-neck sweater, no logos.`
- `Wardrobe: a navy wool coat over a grey crew-neck sweater, no logos.`
- `Wardrobe: a grey wool suit jacket over a white shirt buttoned to the collar, no tie, no logos.`

## Head line

Every first final is a front view: it wears a frame's A1 cut-out.

- **A1:** `Head facing the camera, chin level, eyes open, looking just past the camera.`

## Tail

```
No glasses or sunglasses, nothing on or near the face, temples and ears clear of hands and objects.
Photograph, natural skin texture, no retouching. No text, no logos.
```

## Sizes

- Portrait finals: request 1536 × 2048 (3:4), so the 4:5 gallery crop and the 9:16 cast crop both fit.
- Drop heroes: 1152 × 2048 (9:16) and 2048 × 1152 (16:9).

The model picks the nearest size it supports; `content/photography/people/<id>.json` records the size it returned.

## What a usable portrait needs

These are checked before a portrait is composited; a portrait that fails one is regenerated, not fixed:

- no glasses, and nothing near the eyes, brows or temples;
- eyes open, head square to the camera (yaw within about 10°), chin level;
- ears and temple line clear where the cut-out's end pieces will sit;
- hands, fingers, teeth and clothing plausible;
- no text, logo or watermark;
- the face big enough for the frame to read: pupils at least about 60 px apart in a 2048-tall image.
