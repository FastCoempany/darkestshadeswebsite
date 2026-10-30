#!/usr/bin/env python3
"""Darkest Shades palette: primitives, semantic roles, contrast report.

Writes design/tokens/tokens.color.json, design/tokens/tokens.color.css and
design/tokens/contrast-report.md. Run: python3 tools/palette.py
Change colors here, never in the generated files.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "design" / "tokens"

# --- Primitives -------------------------------------------------------------
# source: "anastasiia" = brand identity files (logo + moodboard Option 03
# "Sustainable elegance"), "logo-kit" = darkestshades logo-kit (GCD gold/onyx),
# "extended" = added for the store (Oct 19 2026).
PRIMITIVES = {
    "black":        ("#000000", "anastasiia", "Logo black"),
    "onyx-950":     ("#050607", "logo-kit",   "Onyx core (GCD inset gradient)"),
    "onyx-900":     ("#0B0B0C", "extended",   "Base surface"),
    "onyx-850":     ("#131416", "extended",   "Raised surface"),
    "onyx-800":     ("#1C1D1F", "extended",   "Overlay surface"),
    "onyx-700":     ("#2C2C2D", "logo-kit",   "Onyx highlight; hairlines"),
    "graphite-600": ("#3D3D3E", "extended",   "Dividers on dark"),
    "graphite-500": ("#545454", "anastasiia", "Moodboard graphite. Rules on dark; text on light only"),
    "graphite-400": ("#6B6B6C", "extended",   "Control borders on dark (3:1); disabled text"),
    "ash-400":      ("#8A8A8A", "extended",   "Smallest text grey allowed on dark"),
    "ash-300":      ("#A6A5A1", "extended",   "Secondary text on dark"),
    "ash-200":      ("#CFCBC3", "extended",   "Muted text on dark, large type"),
    "bone-100":     ("#E8E4DC", "extended",   "Primary text on dark; slide-film white"),
    "bone-50":      ("#F3F0E9", "extended",   "Paper surface"),
    "stage":        ("#E4E2DD", "extended",   "Product stage (matches cleaned lightbox seamless)"),
    "gold-300":     ("#D9BB82", "logo-kit",   "Gold hover / light gold"),
    "gold-500":     ("#C6A36A", "logo-kit",   "GCD flat gold"),
    "gold-700":     ("#7A5C2E", "extended",   "Gold ink for light surfaces"),
    "camel-500":    ("#BF835F", "anastasiia", "Moodboard camel"),
    "camel-700":    ("#7F5137", "extended",   "Camel ink for light surfaces"),
    "success-300":  ("#8DB596", "extended",   "Success on dark"),
    "success-700":  ("#2F6B44", "extended",   "Success on light"),
    "error-300":    ("#E0796A", "extended",   "Error on dark"),
    "error-700":    ("#A3392C", "extended",   "Error on light"),
    "info-300":     ("#9DB4D1", "extended",   "Info on dark"),
    "info-700":     ("#33557F", "extended",   "Info on light"),
    "white":        ("#FFFFFF", "anastasiia", "Logo white"),
}

GRADIENTS = {
    "metal": ["#634722", "#B68A4D", "#FFF2CD", "#EAC999", "#A77C46", "#CDA974", "#86653B", "#EDCFA0", "#5A442C"],
    "onyx":  ["#2C2C2D", "#111214", "#050607", "#111214", "#000000"],
}

# --- Semantic roles ---------------------------------------------------------
# "night" is the default theme (dark). "paper" is for editorial/policy pages and
# the product stage. Components use roles only, never primitives or hex.
ROLES = {
    "night": {
        "surface-canvas": "onyx-950", "surface-base": "onyx-900", "surface-raised": "onyx-850",
        "surface-overlay": "onyx-800", "surface-inverse": "bone-100", "surface-stage": "stage",
        "text-primary": "bone-100", "text-secondary": "ash-300", "text-tertiary": "ash-400",
        "text-disabled": "graphite-400", "text-inverse": "onyx-950", "text-accent": "gold-500",
        "text-editorial": "camel-500", "text-on-stage": "onyx-950",
        "border-hairline": "onyx-700", "border-rule": "graphite-500", "border-control": "graphite-400",
        "focus-ring": "gold-500",
        "action-primary-bg": "bone-100", "action-primary-text": "onyx-950",
        "action-primary-bg-hover": "white",
        "action-secondary-border": "bone-100", "action-secondary-text": "bone-100",
        "action-quiet-text": "ash-300", "action-quiet-text-hover": "bone-100",
        "status-success": "success-300", "status-error": "error-300", "status-info": "info-300",
        "status-live": "gold-500", "status-error-stage": "error-700",
    },
    "paper": {
        "surface-canvas": "bone-50", "surface-base": "bone-50", "surface-raised": "white",
        "surface-overlay": "stage", "surface-inverse": "onyx-950", "surface-stage": "stage",
        "text-primary": "onyx-950", "text-secondary": "onyx-700", "text-tertiary": "graphite-500",
        "text-disabled": "ash-400", "text-inverse": "bone-100", "text-accent": "gold-700",
        "text-editorial": "camel-700", "text-on-stage": "onyx-950",
        "border-hairline": "ash-200", "border-rule": "ash-400", "border-control": "graphite-500",
        "focus-ring": "gold-700",
        "action-primary-bg": "onyx-950", "action-primary-text": "bone-100",
        "action-primary-bg-hover": "black",
        "action-secondary-border": "onyx-950", "action-secondary-text": "onyx-950",
        "action-quiet-text": "onyx-700", "action-quiet-text-hover": "onyx-950",
        "status-success": "success-700", "status-error": "error-700", "status-info": "info-700",
        "status-live": "gold-700", "status-error-stage": "error-700",
    },
}

# Pairs that must pass. (role, background role, minimum ratio)
CHECKS = [
    ("text-primary", "surface-canvas", 4.5), ("text-primary", "surface-overlay", 4.5),
    ("text-secondary", "surface-canvas", 4.5), ("text-secondary", "surface-overlay", 4.5),
    ("text-tertiary", "surface-canvas", 4.5), ("text-tertiary", "surface-overlay", 4.5),
    ("text-accent", "surface-canvas", 4.5), ("text-editorial", "surface-canvas", 4.5),
    ("status-success", "surface-canvas", 4.5), ("status-error", "surface-canvas", 4.5),
    ("status-info", "surface-canvas", 4.5), ("status-live", "surface-canvas", 4.5),
    ("border-control", "surface-canvas", 3.0), ("focus-ring", "surface-canvas", 3.0),
    ("action-primary-text", "action-primary-bg", 4.5),
    ("text-on-stage", "surface-stage", 4.5),  # slot labels on the stage, in both themes
    ("status-error-stage", "surface-stage", 4.5),  # a failed picture's label on the stage
    ("text-primary", "surface-stage", 0.0),  # informational: stage is light, text on it uses paper roles
]


def lum(hexv):
    h = hexv.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    hexof = {k: v[0] for k, v in PRIMITIVES.items()}
    data = {
        "primitives": {k: {"value": v[0], "source": v[1], "use": v[2]} for k, v in PRIMITIVES.items()},
        "gradients": GRADIENTS,
        "roles": {t: {r: {"ref": p, "value": hexof[p]} for r, p in roles.items()} for t, roles in ROLES.items()},
    }
    (OUT / "tokens.color.json").write_text(json.dumps(data, indent=2) + "\n")

    css = ["/* Generated by tools/palette.py. Do not edit by hand. */", ":root {"]
    css += [f"  --ds-{k}: {v[0]};" for k, v in PRIMITIVES.items()]
    for name, stops in GRADIENTS.items():
        n = len(stops) - 1
        parts = ", ".join(f"{s} {round(i * 100 / n)}%" for i, s in enumerate(stops))
        css.append(f"  --ds-gradient-{name}: linear-gradient(160deg, {parts});")
    css.append("}")
    for theme, roles in ROLES.items():
        sel = ":root, [data-theme=\"night\"]" if theme == "night" else "[data-theme=\"paper\"]"
        css.append(f"{sel} {{")
        css += [f"  --color-{r}: var(--ds-{p});" for r, p in roles.items()]
        css.append("}")
    (OUT / "tokens.color.css").write_text("\n".join(css) + "\n")

    lines = ["# Contrast report", "", "Generated by `tools/palette.py`. WCAG 2.2: 4.5:1 for body text, 3:1 for large text and UI boundaries.", ""]
    lines += ["## Brand greys on dark", "",
              "| Grey | on onyx-950 | on onyx-800 | Allowed use on dark |", "|---|---|---|---|"]
    for k in ["graphite-500", "graphite-400", "ash-400", "ash-300", "ash-200", "bone-100"]:
        r1, r2 = ratio(hexof[k], hexof["onyx-950"]), ratio(hexof[k], hexof["onyx-800"])
        use = "text" if r2 >= 4.5 else ("UI borders, large text" if r1 >= 3 else "rules and decoration only")
        lines.append(f"| `{k}` {hexof[k]} | {r1:.2f} | {r2:.2f} | {use} |")
    fails = 0
    for theme, roles in ROLES.items():
        lines += ["", f"## Theme: {theme}", "", "| Foreground | Background | Ratio | Needs | Result |", "|---|---|---|---|---|"]
        for fg, bg, need in CHECKS:
            a, b = hexof[roles[fg]], hexof[roles[bg]]
            r = ratio(a, b)
            ok = r >= need
            if need and not ok:
                fails += 1
            res = "pass" if ok else "FAIL"
            if need == 0:
                res = "info"
            lines.append(f"| `{fg}` {a} | `{bg}` {b} | {r:.2f} | {need or '-'} | {res} |")
    lines += ["", f"Failures: {fails}"]
    (OUT / "contrast-report.md").write_text("\n".join(lines) + "\n")
    print(f"wrote tokens; failures: {fails}")
    return fails


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
