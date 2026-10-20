#!/usr/bin/env python3
"""Generate the colored Tinted variants of the bundled iOS 18 icon pack.

User order 2026-10-20: add Tinted in green, yellow, gray, brown,
chocolate, cream and white — each as a Dark and a Light variant.

Method (the same trick iOS's own tinted mode uses): the bundled Tinted
icons are a dark background plus a single-tint glyph whose shading lives
in the luminance. We recover a per-pixel glyph mask from that luminance
and re-render it as a duotone in the target color:

* Dark variant:  near-black neutral background -> full tint color.
* Light variant: light neutral background -> deepened tint color
  (deepened so the glyph stays legible on a light background).

Alpha (the transparent rounded corners) is copied from the source
unchanged. Sources: files/ios18_icons/Tinted/<slug>.png for the 51
catalog slugs in src/gui/ios/icon_themes.py:IOS18_CATALOG.

Run from the repo root:  python3 tools/generate_tinted_variants.py
Requires Pillow. Overwrites the Tinted-<Color>-<Mode> folders in place.
"""

import ast
import os

from PIL import Image


def _catalog_slugs() -> list[str]:
    """Slugs from IOS18_CATALOG in src/gui/ios/icon_themes.py, read via ast
    so this script needs no Qt import (system python has no PySide6)."""
    path = os.path.join(os.path.dirname(__file__), "..",
                        "src", "gui", "ios", "icon_themes.py")
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "IOS18_CATALOG"
                for t in node.targets):
            return [entry[2] for entry in ast.literal_eval(node.value)]
    raise RuntimeError("IOS18_CATALOG not found in icon_themes.py")

BASE = os.path.join(os.path.dirname(__file__), "..", "files", "ios18_icons")
SOURCE_DIR = os.path.join(BASE, "Tinted")

# color name -> (bright tint for Dark variant, deep tint for Light variant)
COLORS = {
    "Green":     ("#34C759", "#1F7A33"),
    "Yellow":    ("#FFD60A", "#B07D00"),
    "Gray":      ("#AEAEB2", "#5A5A5E"),
    "Brown":     ("#C08552", "#7A4E21"),
    "Chocolate": ("#8A5A2B", "#4E2E17"),
    "Cream":     ("#F0E3BC", "#A9853E"),
    "White":     ("#FFFFFF", "#C7C7CC"),
}

DARK_BG = (35, 36, 38)          # near-black neutral
LIGHT_BG = (245, 245, 247)      # light neutral
LIGHT_BG_WHITE = (232, 232, 236)  # slightly deeper so a white glyph reads


def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def glyph_mask(img: Image.Image) -> Image.Image:
    """Per-pixel glyph strength 0..255 from the source Tinted icon.

    The source background sits at luminance ~43; glyph shading rises from
    there. Normalise [43, 235] -> [0, 255] with a soft floor so the
    background maps to a clean 0 and anti-aliased edges stay smooth.
    """
    lum = img.convert("L")
    lut = []
    for v in range(256):
        m = (v - 43) / (235 - 43)
        m = min(1.0, max(0.0, m))
        lut.append(round(255 * m))
    return lum.point(lut)


def render(img: Image.Image, mask: Image.Image,
           bg: tuple[int, int, int], tint: tuple[int, int, int]) -> Image.Image:
    """Duotone: bg -> tint driven by the glyph mask; alpha preserved."""
    w, h = img.size
    m = mask.load()
    out = Image.new("RGBA", (w, h))
    px = out.load()
    alpha = img.convert("RGBA").load()
    for y in range(h):
        for x in range(w):
            t = m[x, y] / 255.0
            px[x, y] = (
                round(bg[0] + (tint[0] - bg[0]) * t),
                round(bg[1] + (tint[1] - bg[1]) * t),
                round(bg[2] + (tint[2] - bg[2]) * t),
                alpha[x, y][3],
            )
    return out


def main() -> int:
    slugs = _catalog_slugs()
    total = 0
    for color, (bright, deep) in COLORS.items():
        for mode, tint_hex, bg in (
            ("Dark", bright, DARK_BG),
            ("Light", deep, LIGHT_BG_WHITE if color == "White" else LIGHT_BG),
        ):
            folder = os.path.join(BASE, f"Tinted-{color}-{mode}")
            os.makedirs(folder, exist_ok=True)
            made = 0
            for slug in slugs:
                src = os.path.join(SOURCE_DIR, f"{slug}.png")
                if not os.path.isfile(src):
                    continue
                img = Image.open(src)
                out = render(img, glyph_mask(img), bg, _hex(tint_hex))
                out.save(os.path.join(folder, f"{slug}.png"))
                made += 1
            print(f"Tinted-{color}-{mode}: {made} icons")
            total += made
    print(f"total: {total} icons in {len(COLORS) * 2} variant folders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
