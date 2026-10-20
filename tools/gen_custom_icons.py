#!/usr/bin/env python3
"""Generate custom WorkSlop menu icons (MONOCHROME WHITE 3D glyphs, 48x48).

User order 2026-10-20: the full-color set read as emoji / AI slop. The menu
icons are now premium frosted-porcelain glyphs — clean silhouette pictograms
(house, picture, chip, bars, grid, sliders, droplet, server, image,
cloud-upload, check seal, gear, bolt, circular arrow, phone, book, flask,
toolbox) rendered as realistic white 3D:

  * fill   = white linearGradient (#FFFFFF top -> #D7E0EA bottom)
  * depth  = the same silhouette duplicated 1.6px lower in slate
             rgba(70,90,120,0.35) behind the main shape
  * detail = engraved slate (#7E93A8) inner lines / recesses
  * gloss  = soft white highlight near the top of the silhouette

NO colors anywhere. These are NOT monochrome-flat: they must be loaded with
the full-color ``color_icon()`` loader (src/gui/theme), never ``theme_icon()``
— that one flattens any SVG to a single color via a SourceIn tint pass and
would destroy the gradient/shadow.
"""
import math
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "src", "qt", "icon")

WHITE_GRAD = (
    '<linearGradient id="wg" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#FFFFFF"/>'
    '<stop offset="0.55" stop-color="#E9EFF5"/>'
    '<stop offset="1" stop-color="#CBD6E2"/>'
    '</linearGradient>')

SHADOW_PAINT = "rgba(70,90,120,0.35)"
DETAIL_PAINT = "#7E93A8"
GLOSS_PAINT = "#FFFFFF"
NO_PAINT = "rgba(0,0,0,0)"


def svg(body, gloss=""):
    """Assemble one icon: slate shadow copy below, white 3D glyph on top.

    The body template uses paint placeholders: {P} = primary surface paint,
    {D} = engraved detail paint, {G} = gloss paint (main pass only).
    """
    shadow = (body.replace("{P}", SHADOW_PAINT)
                  .replace("{D}", SHADOW_PAINT)
                  .replace("{G}", NO_PAINT))
    main = (body.replace("{P}", "url(#wg)")
                .replace("{D}", DETAIL_PAINT)
                .replace("{G}", GLOSS_PAINT))
    gloss_main = gloss.replace("{G}", GLOSS_PAINT)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" '
            'viewBox="0 0 48 48"><defs>' + WHITE_GRAD + "</defs>"
            f'<g transform="translate(0 1.6)">{shadow}</g>{main}{gloss_main}'
            "</svg>")


def rrect_path(x, y, w, h, r):
    """Rounded-rectangle subpath (absolute commands)."""
    return (
        f"M{x + r:.1f} {y:.1f}H{x + w - r:.1f}"
        f"A{r:.1f} {r:.1f} 0 0 1 {x + w:.1f} {y + r:.1f}"
        f"V{y + h - r:.1f}"
        f"A{r:.1f} {r:.1f} 0 0 1 {x + w - r:.1f} {y + h:.1f}"
        f"H{x + r:.1f}"
        f"A{r:.1f} {r:.1f} 0 0 1 {x:.1f} {y + h - r:.1f}"
        f"V{y + r:.1f}"
        f"A{r:.1f} {r:.1f} 0 0 1 {x + r:.1f} {y:.1f}Z")


def circle_path(cx, cy, r):
    return (f"M{cx - r:.1f} {cy:.1f} a{r:.1f} {r:.1f} 0 1 0 {2 * r:.1f} 0 "
            f"a{r:.1f} {r:.1f} 0 1 0 {-2 * r:.1f} 0 Z")


def gear_points(cx, cy, teeth, r_tip, r_root):
    """Polygon points for a gear outline (alternating tip/root arcs)."""
    pts = []
    step = 2 * math.pi / teeth
    for i in range(teeth):
        a = i * step
        for frac, r in ((0.0, r_root), (0.10, r_tip), (0.50, r_tip),
                        (0.60, r_root)):
            ang = a + frac * step
            pts.append(f"{cx + r * math.cos(ang):.1f},{cy + r * math.sin(ang):.1f}")
    return pts


ICONS = {
    # -- tweak family menus (left rail) --
    # home: house silhouette, door knocked out (evenodd)
    "ws2-home": svg(
        '<path fill-rule="evenodd" fill="{P}" d="'
        "M24 3.5 44.5 21.5h-6.4V40a2.5 2.5 0 0 1-2.5 2.5H12.4"
        "A2.5 2.5 0 0 1 9.9 40V21.5H3.5Z"
        "M20.6 42.5V32.2a3.4 3.4 0 0 1 6.8 0v10.3Z"
        '"/>',
        '<ellipse cx="24" cy="11" rx="8.5" ry="3.2" fill="{G}" opacity="0.30"/>'
    ),
    # posterboard: picture frame ring (evenodd) + sun & mountain inside
    "ws2-poster": svg(
        '<path fill-rule="evenodd" fill="{P}" d="'
        + rrect_path(4.5, 5.5, 39, 37, 4.5)
        + rrect_path(10.5, 11.5, 27, 25, 2)
        + '"/>'
        '<circle cx="31.5" cy="18" r="3.3" fill="{P}"/>'
        '<path d="M10.5 36.5 19.5 24.5 25.5 31.5 30 26.5 37.5 33.5v3Z" fill="{P}"/>'
    ),
    # mobile gestalt: CPU body + pins, engraved die
    "ws2-chip": svg(
        '<g fill="{P}">'
        '<rect x="17" y="3" width="3.6" height="7" rx="1.4"/><rect x="27" y="3" width="3.6" height="7" rx="1.4"/>'
        '<rect x="17" y="38" width="3.6" height="7" rx="1.4"/><rect x="27" y="38" width="3.6" height="7" rx="1.4"/>'
        '<rect x="3" y="17" width="7" height="3.6" rx="1.4"/><rect x="3" y="27" width="7" height="3.6" rx="1.4"/>'
        '<rect x="38" y="17" width="7" height="3.6" rx="1.4"/><rect x="38" y="27" width="7" height="3.6" rx="1.4"/>'
        '</g>'
        '<rect x="10" y="10" width="28" height="28" rx="5.5" fill="{P}"/>'
        '<rect x="17.5" y="17.5" width="13" height="13" rx="3" fill="{D}" opacity="0.55"/>'
        '<rect x="20.7" y="20.7" width="6.6" height="6.6" rx="1.8" fill="{P}"/>',
        '<ellipse cx="24" cy="14" rx="9" ry="3" fill="{G}" opacity="0.30"/>'
    ),
    # status bar: four ascending bars with gloss caps
    "ws2-signal": svg(
        '<g fill="{P}">'
        '<rect x="4.5" y="33" width="8" height="10" rx="2.4"/>'
        '<rect x="15" y="25" width="8" height="18" rx="2.4"/>'
        '<rect x="25.5" y="16" width="8" height="27" rx="2.4"/>'
        '<rect x="36" y="6" width="8" height="37" rx="2.4"/>'
        '</g>'
        '<g fill="{G}" opacity="0.5">'
        '<rect x="6.3" y="34.6" width="4.4" height="3" rx="1.5"/>'
        '<rect x="16.8" y="26.6" width="4.4" height="3" rx="1.5"/>'
        '<rect x="27.3" y="17.6" width="4.4" height="3" rx="1.5"/>'
        '<rect x="37.8" y="7.6" width="4.4" height="3" rx="1.5"/></g>'
    ),
    # springboard: 2x2 app tiles with gloss
    "ws2-apps": svg(
        '<g fill="{P}">'
        '<rect x="5" y="5" width="17" height="17" rx="5"/>'
        '<rect x="26" y="5" width="17" height="17" rx="5"/>'
        '<rect x="5" y="26" width="17" height="17" rx="5"/>'
        '<rect x="26" y="26" width="17" height="17" rx="5"/>'
        '</g>'
        '<g fill="{G}" opacity="0.5">'
        '<rect x="8" y="7.6" width="11" height="5" rx="2.5"/>'
        '<rect x="29" y="7.6" width="11" height="5" rx="2.5"/>'
        '<rect x="8" y="28.6" width="11" height="5" rx="2.5"/>'
        '<rect x="29" y="28.6" width="11" height="5" rx="2.5"/></g>'
    ),
    # internal: control panel, engraved tracks, raised knobs
    "ws2-sliders": svg(
        '<rect x="3.5" y="8" width="41" height="32" rx="8" fill="{P}"/>'
        '<g fill="{D}" opacity="0.6">'
        '<rect x="10" y="15.8" width="28" height="3.6" rx="1.8"/>'
        '<rect x="10" y="24.3" width="28" height="3.6" rx="1.8"/>'
        '<rect x="10" y="32.8" width="28" height="3.6" rx="1.8"/></g>'
        '<g fill="{P}" stroke="{D}" stroke-opacity="0.6">'
        '<circle cx="31" cy="17.6" r="5"/>'
        '<circle cx="18" cy="26.1" r="5"/>'
        '<circle cx="34.5" cy="34.6" r="5"/></g>'
        '<g fill="{G}" opacity="0.8">'
        '<circle cx="29.4" cy="16" r="1.6"/><circle cx="16.4" cy="24.5" r="1.6"/>'
        '<circle cx="32.9" cy="33" r="1.6"/></g>'
    ),
    # liquid glass: droplet with inner gloss and bottom shade
    "ws2-glass": svg(
        '<path d="M24 2.8C24 2.8 9.8 19.6 9.8 29.4a14.2 13.8 0 0 0 28.4 0'
        'C38.2 19.6 24 2.8 24 2.8Z" fill="{P}"/>'
        '<ellipse cx="17.5" cy="26" rx="4.2" ry="7.2" fill="{G}" opacity="0.55" transform="rotate(-16 17.5 26)"/>'
        '<ellipse cx="30.5" cy="39" rx="6.6" ry="3.2" fill="{D}" opacity="0.30"/>'
    ),
    # daemons: two server units, engraved LEDs and vents
    "ws2-daemons": svg(
        '<rect x="5" y="6" width="38" height="16" rx="4" fill="{P}"/>'
        '<rect x="5" y="26" width="38" height="16" rx="4" fill="{P}"/>'
        '<g fill="{D}">'
        '<circle cx="12" cy="14" r="2.5"/><circle cx="12" cy="34" r="2.5"/>'
        '<rect x="21" y="12.2" width="6" height="3.6" rx="1.8"/><rect x="29.5" y="12.2" width="6" height="3.6" rx="1.8"/>'
        '<rect x="21" y="32.2" width="6" height="3.6" rx="1.8"/><rect x="29.5" y="32.2" width="6" height="3.6" rx="1.8"/></g>'
        '<g fill="{G}" opacity="0.45">'
        '<rect x="8" y="8.4" width="32" height="3" rx="1.5"/>'
        '<rect x="8" y="28.4" width="32" height="3" rx="1.5"/></g>'
    ),
    # icon themes: solid photo, engraved sun & hills
    "ws2-wallpaper": svg(
        '<rect x="4.5" y="7.5" width="39" height="33" rx="5.5" fill="{P}"/>'
        '<circle cx="33" cy="19" r="4.2" fill="{D}"/>'
        '<path d="M4.5 33.5 16 24l7.5 6L31 25l12.5 8v7.5h-39Z" fill="{D}" opacity="0.8"/>'
        '<path d="M4.5 40.5v-4L15 30.5l8 5.4 6.5-4.4 14 7.5v1.5Z" fill="{D}"/>',
        '<ellipse cx="22" cy="12" rx="13" ry="3" fill="{G}" opacity="0.35"/>'
    ),

    # -- utility menus (right rail) --
    # backup: cloud silhouette, up-arrow knocked out (evenodd)
    "ws2-backup": svg(
        '<path fill-rule="evenodd" fill="{P}" d="'
        "M15.5 38.5c-5.2 0-9.5-3.8-9.5-8.6 0-4.5 3.4-8.2 7.8-8.7"
        "C9.1 15.9 13.3 12 18.9 12c6.3 0 11.5 4.8 12 11 4 .5 7 3.6 7 7.4"
        " 0 4.5-3.7 8.1-8.4 8.1Z"
        "M24 19.8 29.6 26.2h-3.3v6.6h-4.6v-6.6h-3.3Z"
        '"/>',
        '<ellipse cx="19" cy="15.5" rx="8" ry="3" fill="{G}" opacity="0.30"/>'
    ),
    # apply: check seal, check knocked out (evenodd)
    "ws2-apply": svg(
        '<path fill-rule="evenodd" fill="{P}" d="'
        + circle_path(24, 24, 19.5)
        + "M15.3 24.6 18.7 21.4 21.7 24.5 29.7 16.1 33.1 19.3 "
          "L22 31.2Z"
        + '"/>'
        '<circle cx="24" cy="24" r="15.4" fill="none" stroke="{D}" '
        'stroke-opacity="0.4" stroke-width="1.3"/>',
        '<ellipse cx="17" cy="13" rx="11" ry="5.4" fill="{G}" opacity="0.35"/>'
    ),
    # settings: gear with center hole (evenodd) + engraved ring
    "ws2-gear": svg(
        '<path fill-rule="evenodd" fill="{P}" d="M'
        + " L".join(gear_points(24, 24, 8, 20.5, 15.6)) + "Z "
        + circle_path(24, 24, 6.8)
        + '"/>'
        '<circle cx="24" cy="24" r="11" fill="none" stroke="{D}" '
        'stroke-opacity="0.5" stroke-width="1.6"/>',
        '<ellipse cx="19.5" cy="12.5" rx="8" ry="3.4" fill="{G}" opacity="0.35" transform="rotate(-24 19.5 12.5)"/>'
    ),
    # recovery mode: lightning bolt silhouette
    "ws2-flash": svg(
        '<path d="M28.5 2.5 10.5 28h9.6L17.5 45.5 37.5 19.5H27.6Z" fill="{P}"/>'
        '<path d="M27 6.5 15.5 24.5h5.4L27 6.5Z" fill="{G}" opacity="0.5"/>'
    ),
    # exit recovery: circular arrow (stroke + arrowhead), white porcelain
    "ws2-refresh": svg(
        '<path d="M33.2 10.4A15 15 0 1 0 39.5 25.5" fill="none" stroke="{P}" '
        'stroke-width="6.4" stroke-linecap="round"/>'
        '<path d="M41.8 4.2 34 12.6 25.9 9.4Z" fill="{P}"/>'
    ),
    # DFU guide: toolbox, engraved handle seam + latch
    "ws2-toolbox": svg(
        '<path d="M17 10.5V8.2A3.2 3.2 0 0 1 20.2 5h7.6A3.2 3.2 0 0 1 31 8.2v2.3" '
        'fill="none" stroke="{D}" stroke-width="3.4"/>'
        '<rect x="4.5" y="10.5" width="39" height="10" rx="3.5" fill="{P}"/>'
        '<rect x="4.5" y="19" width="39" height="22" rx="3.5" fill="{P}"/>'
        '<rect x="4.5" y="19.4" width="39" height="2.6" fill="{D}" opacity="0.4"/>'
        '<rect x="20.4" y="17.2" width="7.2" height="8.6" rx="1.8" fill="{D}"/>',
        '<rect x="8" y="12.4" width="32" height="3.4" rx="1.7" fill="{G}" opacity="0.45"/>'
    ),
    # restore guide: iPhone body, engraved screen, gloss sweep
    "ws2-device": svg(
        '<rect x="14" y="3.5" width="20" height="41" rx="5.5" fill="{P}"/>'
        '<rect x="17" y="9" width="14" height="27.5" rx="2.8" fill="{D}" opacity="0.5"/>'
        '<path d="M17 9h14L21 36.5H17Z" fill="{G}" opacity="0.35"/>'
        '<rect x="21.4" y="10.8" width="5.2" height="1.9" rx="0.95" fill="{D}" opacity="0.7"/>'
        '<rect x="20.8" y="39.8" width="6.4" height="1.8" rx="0.9" fill="{D}"/>'
    ),
    # beta iOS: flask silhouette, engraved liquid + bubbles
    "ws2-beta": svg(
        '<path d="M20.8 8h6.4v9.4l7.2 15.4a5 5 0 0 1-4.5 7.2H18.1'
        'a5 5 0 0 1-4.5-7.2l7.2-15.4Z" fill="{P}"/>'
        '<rect x="18.6" y="4.4" width="10.8" height="3.4" rx="1.7" fill="{P}"/>'
        '<path d="M16.9 27.5h14.2l3.3 5.3a3.6 3.6 0 0 1-3.2 5.4H16.8'
        'a3.6 3.6 0 0 1-3.2-5.4Z" fill="{D}" opacity="0.5"/>'
        '<g fill="{G}">'
        '<circle cx="21" cy="33" r="1.9" opacity="0.85"/><circle cx="27.5" cy="36.2" r="1.4" opacity="0.8"/>'
        '<circle cx="24.6" cy="30.4" r="1.1" opacity="0.9"/></g>'
        '<rect x="16.9" y="12" width="3" height="19" rx="1.5" fill="{G}" opacity="0.45"/>'
    ),
    # guide: book with engraved ribbon + text lines
    "ws2-guide": svg(
        '<rect x="9.5" y="5" width="28" height="38" rx="3.2" fill="{P}"/>'
        '<rect x="9.5" y="5" width="5" height="38" rx="2.5" fill="{D}" opacity="0.45"/>'
        '<path d="M28.5 5v13.5l-3.6-2.8-3.6 2.8V5Z" fill="{D}"/>'
        '<g fill="{D}" opacity="0.55">'
        '<rect x="18.5" y="24" width="12.5" height="2.6" rx="1.3"/>'
        '<rect x="18.5" y="30" width="9.5" height="2.6" rx="1.3"/></g>',
        '<path d="M12 5h24.5L24 20H12Z" fill="{G}" opacity="0.22"/>'
    ),
}

os.makedirs(OUT, exist_ok=True)
for name, content in ICONS.items():
    path = os.path.join(OUT, f"{name}.svg")
    with open(path, "w") as f:
        f.write(content)
    print(f"wrote {name}.svg")
print(f"Done: {len(ICONS)} icons")
