#!/usr/bin/env python3
"""Flash check for the entry sequence (WCAG 2.3.1; docs/brief/03-references.md, Safety).

Renders the sequence at 1024x768 and 390x844, measures relative-luminance change in every 341x256
window (a 10-degree field at a typical viewing distance) and fails on more than three general flashes
in any one-second period.

A general flash is a pair of opposing changes in relative luminance of 0.10 or more (10% of the
maximum) where the darker state is below 0.80. A window registers a change when at least a quarter of
its pixels change that much in the same direction between two consecutive frames, or when the
window's mean luminance does. Consecutive changes in the same direction count once.

Usage:
  python3 tools/flashcheck.py                          # the real sequence, assets/entry/sequence.json
  python3 tools/flashcheck.py --sequence path.json     # another sequence file
  python3 tools/flashcheck.py --synthetic white-strobe # 12 white/black cuts a second: must fail
  python3 tools/flashcheck.py --synthetic dark-strobe  # 12 cuts a second, every frame under 0.09: must pass
  python3 tools/flashcheck.py --self-test              # both synthetic cases, checks the verdicts
  python3 tools/flashcheck.py --report out.json        # also write the measurements

Exit status: 0 pass, 1 fail, 2 usage or missing sequence.

Sequence file (written by tools/photo/entry_stills.py, played by app/components/house/Entry.tsx):
  {"version": 1, "steps": [
    {"type": "card",  "text": "See everything.", "seconds": 1.2, "ground": "surface-overlay"},
    {"type": "burst", "layout": "framed", "fps": 12, "frames": ["assets/entry/burst1/....webp", ...]},
    {"type": "card",  "text": "Reveal nothing.", "seconds": 2.0},
    {"type": "logo",  "seconds": 2.4},
    {"type": "burst", "layout": "bleed", "fps": 3, "frames": [...]},
    {"type": "end",   "seconds": 1.6}]}
Grounds are role tokens from design/tokens/tokens.color.json (night theme); a frame may also be
{"color": "#RRGGBB"} for synthetic tests. Paths are relative to the repo root.
"""
import argparse
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_SEQUENCE = ROOT / "assets" / "entry" / "sequence.json"
VIEWPORTS = [(1024, 768), (390, 844)]
WINDOW = (341, 256)          # a 10-degree field, px
SCALE = 4                    # analysis runs at a quarter of the viewport size
TICKS_PER_SECOND = 24        # the master clock: 1/24 s
CHANGE = 0.10                # 10% of the maximum relative luminance
DARK_BELOW = 0.80            # the darker state of a flash is below this
AREA = 0.25                  # a quarter of the window's pixels
MAX_FLASHES_PER_SECOND = 3


def tokens():
    data = json.loads((ROOT / "design" / "tokens" / "tokens.color.json").read_text())
    prim = {k: v["value"] for k, v in data["primitives"].items()}
    roles = {r: prim[v["ref"]] for r, v in data["roles"]["night"].items()}
    roles["black"] = prim["black"]
    return prim, roles


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(img):
    """Relative luminance (0..1) of an RGB image as a float array."""
    a = np.asarray(img.convert("RGB"), dtype=np.float64) / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]


class Renderer:
    def __init__(self, width, height, roles, prim):
        self.W, self.H = width // SCALE, height // SCALE
        self.roles, self.prim = roles, prim
        self.font = ImageFont.load_default(size=max(6, self.H // 40))
        self.cache = {}

    def ground(self, step):
        name = step.get("ground", "surface-overlay")
        return hex_to_rgb(self.roles.get(name) or self.prim.get(name) or name)

    def canvas(self, step):
        return Image.new("RGB", (self.W, self.H), self.ground(step))

    def card(self, step):
        im = self.canvas(step)
        d = ImageDraw.Draw(im)
        text = step.get("text", "")
        box = d.textbbox((0, 0), text, font=self.font)
        d.text(((self.W - box[2]) / 2, (self.H - box[3]) / 2), text, fill=hex_to_rgb(self.roles["text-primary"]), font=self.font)
        return im

    def logo(self, step):
        # The stacked logo, approximated by its bounding box in bone (brighter than the real letterforms,
        # so the estimate errs on the side of more flash, never less).
        im = self.canvas(step)
        w = int(self.W * 0.36)
        h = max(1, int(w * 162.38 / 859))
        ImageDraw.Draw(im).rectangle([(self.W - w) // 2, (self.H - h) // 2, (self.W + w) // 2, (self.H + h) // 2], fill=hex_to_rgb(self.roles["text-primary"]))
        return im

    def end(self, step):
        im = self.canvas(step)
        d = ImageDraw.Draw(im)
        w = int(self.W * 0.12)
        h = max(1, int(w * 589 / 1632))
        d.rectangle([(self.W - w) // 2, (self.H - h) // 2 - h, (self.W + w) // 2, (self.H + h) // 2 - h], fill=hex_to_rgb(self.roles["text-accent"]))
        text = "Darkest Shades"
        box = d.textbbox((0, 0), text, font=self.font)
        d.text(((self.W - box[2]) / 2, (self.H + h) / 2 + 2), text, fill=hex_to_rgb(self.roles["text-primary"]), font=self.font)
        return im

    def source(self, frame):
        if isinstance(frame, dict) and "color" in frame:
            return Image.new("RGB", (4, 3), hex_to_rgb(frame["color"]))
        path = ROOT / frame
        if path not in self.cache:
            self.cache[path] = Image.open(path).convert("RGB")
        return self.cache[path]

    def burst_frame(self, step, frame):
        im = self.canvas(step)
        src = self.source(frame)
        if step.get("layout") == "framed":
            # A small 3:4 print with dark margins: half the viewport height, centred.
            box_h = int(self.H * 0.5)
            box_w = int(box_h * 3 / 4)
            fitted = fit(src, box_w, box_h, cover=False)
            im.paste(fitted, ((self.W - fitted.width) // 2, (self.H - fitted.height) // 2))
        else:
            im = fit(src, self.W, self.H, cover=True)
        return im


def fit(src, w, h, cover):
    sw, sh = src.size
    scale = max(w / sw, h / sh) if cover else min(w / sw, h / sh)
    nw, nh = max(1, round(sw * scale)), max(1, round(sh * scale))
    out = src.resize((nw, nh), Image.BILINEAR)
    if cover:
        left, top = (nw - w) // 2, (nh - h) // 2
        out = out.crop((left, top, left + w, top + h))
    return out


def timeline(sequence, renderer):
    """The sequence as a list of (ticks, luminance array) states on the 24-tick master clock."""
    states = []
    for step in sequence["steps"]:
        kind = step["type"]
        if kind == "burst":
            fps = float(step.get("fps", 12))
            ticks = max(1, round(TICKS_PER_SECOND / fps))
            for frame in step["frames"]:
                states.append((ticks, luminance(renderer.burst_frame(step, frame))))
        else:
            ticks = max(1, round(float(step.get("seconds", 1.0)) * TICKS_PER_SECOND))
            render = {"card": renderer.card, "logo": renderer.logo, "end": renderer.end}.get(kind, renderer.canvas)
            states.append((ticks, luminance(render(step))))
    return states


def integral(mask):
    s = np.zeros((mask.shape[0] + 1, mask.shape[1] + 1))
    s[1:, 1:] = np.cumsum(np.cumsum(mask.astype(np.float64), axis=0), axis=1)
    return s


def window_fractions(mask, wh, ww, stride):
    s = integral(mask)
    H, W = mask.shape
    ys = list(range(0, max(1, H - wh + 1), stride))
    xs = list(range(0, max(1, W - ww + 1), stride))
    if ys[-1] != max(0, H - wh):
        ys.append(max(0, H - wh))
    if xs[-1] != max(0, W - ww):
        xs.append(max(0, W - ww))
    wh, ww = min(wh, H), min(ww, W)
    out = np.zeros((len(ys), len(xs)))
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            out[i, j] = (s[y + wh, x + ww] - s[y, x + ww] - s[y + wh, x] + s[y, x]) / (wh * ww)
    return out, ys, xs


def analyse(states, viewport):
    """Return (max flashes in any second, where, events per window) for one viewport."""
    wh, ww = max(1, WINDOW[1] // SCALE), max(1, WINDOW[0] // SCALE)
    stride = max(1, min(wh, ww) // 4)
    # Window-level change events: list of (tick, direction) per window position.
    events = None
    tick = 0
    prev = None
    for ticks, lum in states:
        if prev is not None:
            diff = lum - prev
            up = (diff >= CHANGE) & (prev < DARK_BELOW)
            down = (diff <= -CHANGE) & (lum < DARK_BELOW)
            f_up, ys, xs = window_fractions(up, wh, ww, stride)
            f_down, _, _ = window_fractions(down, wh, ww, stride)
            m_prev, _, _ = window_fractions(prev, wh, ww, stride)
            m_now, _, _ = window_fractions(lum, wh, ww, stride)
            mean_up = (m_now - m_prev >= CHANGE) & (m_prev < DARK_BELOW)
            mean_down = (m_prev - m_now >= CHANGE) & (m_now < DARK_BELOW)
            if events is None:
                events = [[[] for _ in xs] for _ in ys]
            for i in range(len(ys)):
                for j in range(len(xs)):
                    d = 0
                    if f_up[i, j] >= AREA or mean_up[i, j]:
                        d = 1
                    elif f_down[i, j] >= AREA or mean_down[i, j]:
                        d = -1
                    if d:
                        ev = events[i][j]
                        if ev and ev[-1][1] == d:
                            ev[-1] = (tick, d)      # a ramp in one direction is one change
                        else:
                            ev.append((tick, d))
        prev = lum
        tick += ticks
    worst, where = 0.0, None
    if events is None:
        return worst, where, 0
    total = 0
    for i, row in enumerate(events):
        for j, ev in enumerate(row):
            total += len(ev)
            for k, (t0, _) in enumerate(ev):
                n = sum(1 for t, _ in ev[k:] if t < t0 + TICKS_PER_SECOND)
                flashes = n / 2
                if flashes > worst:
                    worst, where = flashes, {"second_from": round(t0 / TICKS_PER_SECOND, 3), "window_px": [xs[j] * SCALE, ys[i] * SCALE]}
    return worst, where, total


def synthetic(kind):
    if kind == "white-strobe":
        frames = [{"color": "#FFFFFF" if i % 2 == 0 else "#000000"} for i in range(24)]
    elif kind == "dark-strobe":
        # Both states under relative luminance 0.09 (sRGB grey 84 = 0.0865), so no change can reach 0.10.
        frames = [{"color": "#545454" if i % 2 == 0 else "#000000"} for i in range(24)]
    else:
        raise SystemExit(f"unknown synthetic case: {kind}")
    return {"version": 1, "steps": [
        {"type": "card", "text": "See everything.", "seconds": 1.0, "ground": "surface-overlay"},
        {"type": "burst", "layout": "bleed", "fps": 12, "frames": frames, "ground": "black"},
        {"type": "card", "text": "Reveal nothing.", "seconds": 1.0, "ground": "surface-overlay"},
    ]}


def run(sequence, label):
    prim, roles = tokens()
    results = []
    ok = True
    for (w, h) in VIEWPORTS:
        states = timeline(sequence, Renderer(w, h, roles, prim))
        worst, where, total = analyse(states, (w, h))
        passed = worst <= MAX_FLASHES_PER_SECOND
        ok = ok and passed
        seconds = sum(t for t, _ in states) / TICKS_PER_SECOND
        results.append({"viewport": f"{w}x{h}", "seconds": round(seconds, 2), "frames": len(states),
                        "max_flashes_in_any_second": worst, "where": where, "window_changes": total, "pass": passed})
        print(f"[flashcheck] {label} {w}x{h}: {len(states)} states over {seconds:.1f}s, "
              f"max {worst:g} flashes in any second ({'pass' if passed else 'FAIL'})"
              + (f" at {where}" if where and not passed else ""))
    return ok, results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sequence", type=pathlib.Path, default=None, help="sequence JSON (default: assets/entry/sequence.json)")
    ap.add_argument("--synthetic", choices=["white-strobe", "dark-strobe"], help="run a synthetic case instead of a file")
    ap.add_argument("--self-test", action="store_true", help="prove the check: white-strobe fails, dark-strobe passes")
    ap.add_argument("--report", type=pathlib.Path, help="write the measurements as JSON")
    args = ap.parse_args(argv)

    report = {"threshold": {"change": CHANGE, "dark_below": DARK_BELOW, "area": AREA, "max_flashes_per_second": MAX_FLASHES_PER_SECOND},
              "viewports": [f"{w}x{h}" for w, h in VIEWPORTS], "window_px": list(WINDOW), "runs": {}}
    if args.self_test:
        fail_ok, r1 = run(synthetic("white-strobe"), "white-strobe")
        pass_ok, r2 = run(synthetic("dark-strobe"), "dark-strobe")
        report["runs"] = {"white-strobe": r1, "dark-strobe": r2}
        good = (not fail_ok) and pass_ok
        print(f"[flashcheck] self-test: white-strobe {'failed as it must' if not fail_ok else 'PASSED (wrong)'}; "
              f"dark-strobe {'passed as it must' if pass_ok else 'FAILED (wrong)'} -> {'OK' if good else 'BROKEN'}")
        status = 0 if good else 1
    elif args.synthetic:
        ok, r = run(synthetic(args.synthetic), args.synthetic)
        report["runs"] = {args.synthetic: r}
        status = 0 if ok else 1
    else:
        path = args.sequence or DEFAULT_SEQUENCE
        if not path.exists():
            print(f"[flashcheck] no sequence at {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}; "
                  f"the entry's stills arrive in phase 3 (run --self-test to prove the check itself)")
            return 2
        sequence = json.loads(path.read_text())
        ok, r = run(sequence, path.name)
        report["runs"] = {str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path): r}
        status = 0 if ok else 1
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=1))
        print(f"[flashcheck] report written to {args.report}")
    return status


if __name__ == "__main__":
    sys.exit(main())
