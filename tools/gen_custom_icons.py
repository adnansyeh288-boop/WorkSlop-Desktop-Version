#!/usr/bin/env python3
"""Generate custom WorkSlop menu icons (white monochrome SVGs, 24x24).

BOLD distinctive style — thick strokes, filled shapes, strong silhouettes.
NOT thin generic stroke icons. Each icon has real character.
All icons are white on transparent, recolored at runtime via theme_icon().
"""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "src", "qt", "icon")


def svg(body: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        'viewBox="0 0 24 24" fill="none" stroke="white" '
        'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">'
        + body + "</svg>"
    )


ICONS = {
    # -- tweak family menus (left rail) --
    # home: bold filled house
    "ws2-home": svg(
        '<path d="M12 3.5 3.5 11" />'
        '<path d="M5.5 9.8V20h13V9.8" />'
        '<rect x="10" y="14" width="4" height="6" fill="white" stroke="none"/>'
    ),
    # posterboard: bold wallpaper card with mountain
    "ws2-poster": svg(
        '<rect x="3.5" y="4" width="17" height="16" rx="3" fill="white" fill-opacity="0.15"/>'
        '<path d="M3.5 15.5 9 10l3.5 3.5L16 10l4.5 4.5" />'
        '<circle cx="16.8" cy="8.8" r="1.8" fill="white" stroke="none"/>'
    ),
    # mobile gestalt: bold chip with thick pins
    "ws2-chip": svg(
        '<rect x="6.5" y="6.5" width="11" height="11" rx="2.5" fill="white" fill-opacity="0.15"/>'
        '<rect x="10" y="10" width="4" height="4" fill="white" stroke="none"/>'
        '<path d="M9 3.5v3M15 3.5v3M9 17.5v3M15 17.5v3M3.5 9h3M3.5 15h3M17.5 9h3M17.5 15h3"/>'
    ),
    # status bar: bold signal bars (filled)
    "ws2-signal": svg(
        '<rect x="3.5" y="14" width="3.6" height="6.5" rx="1" fill="white" stroke="none"/>'
        '<rect x="8.6" y="10" width="3.6" height="10.5" rx="1" fill="white" stroke="none"/>'
        '<rect x="13.7" y="6" width="3.6" height="14.5" rx="1" fill="white" stroke="none"/>'
        '<rect x="18.8" y="2.5" width="3.6" height="18" rx="1" fill="white" stroke="none" fill-opacity="0.45"/>'
    ),
    # springboard: bold 2x2 app grid (one filled)
    "ws2-apps": svg(
        '<rect x="3.5" y="3.5" width="7.5" height="7.5" rx="2.2" fill="white" stroke="none"/>'
        '<rect x="13" y="3.5" width="7.5" height="7.5" rx="2.2"/>'
        '<rect x="3.5" y="13" width="7.5" height="7.5" rx="2.2"/>'
        '<rect x="13" y="13" width="7.5" height="7.5" rx="2.2"/>'
    ),
    # internal: bold wrench
    "ws2-sliders": svg(
        '<path d="M14.5 6.5a4.2 4.2 0 0 1 5.6 5.6L21.5 13.5l-2.8 2.8-1.4-1.4a4.2 4.2 0 0 1-5.6-5.6L10.3 8l2.8-2.8 1.4 1.3z" fill="white" fill-opacity="0.2"/>'
        '<circle cx="15.5" cy="9.5" r="1.6" fill="white" stroke="none"/>'
        '<path d="M4 20 9.5 14.5"/>'
    ),
    # liquid glass: bold droplet
    "ws2-glass": svg(
        '<path d="M12 2.8c-4.6 5-7.2 8.4-7.2 12a7.2 7.2 0 0 0 14.4 0c0-3.6-2.6-7-7.2-12z" fill="white" fill-opacity="0.18"/>'
        '<path d="M8.8 14.2a3.4 3.4 0 0 0 2.4 3.1"/>'
    ),
    # daemons: bold stacked servers with lights
    "ws2-daemons": svg(
        '<rect x="3.5" y="3.5" width="17" height="7" rx="2" fill="white" fill-opacity="0.15"/>'
        '<rect x="3.5" y="13.5" width="17" height="7" rx="2"/>'
        '<circle cx="7.5" cy="7" r="1.4" fill="white" stroke="none"/>'
        '<circle cx="7.5" cy="17" r="1.4" fill="white" stroke="none"/>'
        '<path d="M12 7h5.5M12 17h5.5"/>'
    ),
    # icon themes: bold image with sun
    "ws2-wallpaper": svg(
        '<rect x="3" y="4.5" width="18" height="15" rx="3" fill="white" fill-opacity="0.12"/>'
        '<circle cx="9" cy="10" r="2" fill="white" stroke="none"/>'
        '<path d="M3 16.5 10 10.5l4 4 3.5-3.5L21 14.5"/>'
    ),

    # -- utility menus (right rail) --
    # backup: bold cloud upload
    "ws2-backup": svg(
        '<path d="M7 18.5a4.5 4.5 0 0 1-.6-8.96A6 6 0 0 1 18 11a4 4 0 0 1-.5 7.5" />'
        '<path d="M12 12.5V21" />'
        '<path d="M8.8 15.5 12 12.3l3.2 3.2"/>'
    ),
    # apply: bold check in circle
    "ws2-apply": svg(
        '<circle cx="12" cy="12" r="8.5" fill="white" fill-opacity="0.15"/>'
        '<path d="M8 12.3l2.8 2.8L16.5 9"/>'
    ),
    # settings: bold gear (8 teeth, thick)
    "ws2-gear": svg(
        '<circle cx="12" cy="12" r="3.4" fill="white" fill-opacity="0.2"/>'
        '<path d="M12 2.8v3M12 18.2v3M2.8 12h3M18.2 12h3M5.2 5.2l2.1 2.1M16.7 16.7l2.1 2.1M18.8 5.2l-2.1 2.1M7.3 16.7l-2.1 2.1"/>'
    ),
    # recovery mode: bold lightning bolt (filled)
    "ws2-flash": svg(
        '<path d="M13.5 2.5 5 13.5h5.5L10 21.5l8.5-11H13l.5-8z" fill="white" fill-opacity="0.25"/>'
    ),
    # refresh: bold circular arrows
    "ws2-refresh": svg(
        '<path d="M20 12a8 8 0 1 1-2.5-5.8" />'
        '<path d="M20 3.5V8h-4.5"/>'
    ),
    # toolbox: bold toolbox
    "ws2-toolbox": svg(
        '<rect x="3" y="8" width="18" height="12.5" rx="2.5" fill="white" fill-opacity="0.12"/>'
        '<path d="M9 8V6.2A1.7 1.7 0 0 1 10.7 4.5h2.6a1.7 1.7 0 0 1 1.7 1.7V8"/>'
        '<path d="M3 13h18"/>'
        '<circle cx="12" cy="16.8" r="1.3" fill="white" stroke="none"/>'
    ),
    # device: bold phone
    "ws2-device": svg(
        '<rect x="6.5" y="2.5" width="11" height="19" rx="3" fill="white" fill-opacity="0.12"/>'
        '<path d="M10.5 18.8h3"/>'
        '<circle cx="12" cy="6" r="1" fill="white" stroke="none"/>'
    ),
    # beta: bold flask
    "ws2-beta": svg(
        '<path d="M9.5 3h5" />'
        '<path d="M10.5 3v5.2L5.4 17a2.4 2.4 0 0 0 2.1 3.5h9a2.4 2.4 0 0 0 2.1-3.5L13.5 8.2V3"/>'
        '<path d="M7.5 14.5h9"/>'
    ),
    # guide: bold book
    "ws2-guide": svg(
        '<path d="M5 4.5A1.5 1.5 0 0 1 6.5 3H19v15H6.5A1.5 1.5 0 0 0 5 19.5z" fill="white" fill-opacity="0.12"/>'
        '<path d="M5 19.5A1.5 1.5 0 0 1 6.5 18H19v3H6.5A1.5 1.5 0 0 1 5 19.5z"/>'
        '<path d="M5 19.5V4.5"/>'
    ),
}

os.makedirs(OUT, exist_ok=True)
for name, content in ICONS.items():
    path = os.path.join(OUT, f"{name}.svg")
    with open(path, "w") as f:
        f.write(content)
    print(f"wrote {name}.svg")
print(f"Done: {len(ICONS)} icons")
