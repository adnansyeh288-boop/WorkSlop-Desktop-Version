"""3D surface layer (user order 2026-10-22).

Ships ON in the 3D build so the installed app shows the depth; every
treatment is gated on :func:`enabled`, which reads the environment
variable ``WORKSLOP_3D_UI`` ONCE. Setting it to ``0``/``false``/``no``/
``off`` forces the flat clean-light UI with no rebuild — the escape
hatch while the look is being judged. The layer only deepens shading
that already exists:

* ``IOSCard`` glass slabs get a real vertical gradient (bright top,
  shaded bottom) instead of the faintest two-stop wash, on top of the
  drop shadow the cards already carry;
* ``IOSSwitch`` tracks and knobs get vertical gradients and the knob
  casts a small soft shadow;
* the ``primary_button`` and ``home_tile`` stylesheet templates are
  replaced with gradient variants (same colors, derived shades).

Revert path if the installed build looks bad (user's own fallback):
unset the variable, or revert the commit that introduced this module —
nothing else in the app depends on it.
"""

import os

from PySide6.QtGui import QColor, QLinearGradient

_ENABLED = None


def enabled() -> bool:
    global _ENABLED
    if _ENABLED is None:
        _ENABLED = os.environ.get(
            "WORKSLOP_3D_UI", "").strip().lower() not in ("0", "false", "no", "off")
    return _ENABLED


def card_gradient(rect, base: QColor) -> QLinearGradient:
    """Vertical surface gradient for a card painted in *rect*.

    Top is lifted, the middle keeps the base color, the bottom is
    shaded — the classic raised-slab profile. On white the lift is a
    no-op and the bottom shade (#F0F0F0-ish) carries the depth.
    """
    grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    grad.setColorAt(0.0, base.lighter(104))
    grad.setColorAt(0.5, base)
    grad.setColorAt(1.0, base.darker(106))
    return grad


def switch_track_gradient(rect, track: QColor) -> QLinearGradient:
    grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    grad.setColorAt(0.0, track.lighter(112))
    grad.setColorAt(1.0, track.darker(104))
    return grad


def knob_gradient(rect) -> QLinearGradient:
    grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    grad.setColorAt(0.0, QColor("#FFFFFF"))
    grad.setColorAt(1.0, QColor("#DCE4EE"))
    return grad


def _qss_grad(top_hex: str, bottom_hex: str) -> str:
    return (f"qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            f"stop:0 {top_hex}, stop:1 {bottom_hex})")


def _shades(hex_str: str):
    col = QColor(hex_str)
    return col.lighter(112).name(), col.darker(108).name()


def render_qss_override(style_key: str, payload: dict):
    """Gradient replacement for a STYLES template, or None.

    *payload* is the same color dict ``t()`` formats the flat template
    with, so the override tracks the live accent/theme exactly.
    """
    if style_key == "primary_button":
        top, bot = _shades(payload["accent"])
        htop, hbot = _shades(payload["accent_hover"])
        ptop, pbot = _shades(payload["accent_pressed"])
        return f"""
        QPushButton {{
            background: {_qss_grad(top, bot)};
            border-radius: 12px;
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 600;
            border: 1px solid {bot};
            padding: 12px 20px;
        }}
        QPushButton:hover {{ background: {_qss_grad(htop, hbot)}; color: #FFFFFF; }}
        QPushButton:pressed {{ background: {_qss_grad(ptop, pbot)}; color: #FFFFFF; }}
        QPushButton:disabled {{ background-color: {payload['bg_tertiary']}; color: {payload['text_disabled']}; border: none; }}
    """
    if style_key == "home_tile":
        base = QColor(payload["bg_secondary"])
        return f"""
        IOSCard {{
            background: {_qss_grad(base.lighter(103).name(), base.darker(104).name())};
            border-radius: 18px;
            border: 1px solid {payload['card_border']};
        }}
        IOSCard:hover {{ border-color: {payload['accent']}; }}
    """
    return None
