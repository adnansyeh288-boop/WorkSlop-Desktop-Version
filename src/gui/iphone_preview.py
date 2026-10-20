"""iPhone preview widget — real device frame, not a static sticker.

3 layers (user spec 2026-10-20):
  1. Frame / bezel — outer shape, dark, corner radius per model
  2. Screen area — clipped to corner radius, shows live device info
  3. Cutout — SEPARATE element: notch / dynamic-island / home-button

The frame changes with the detected model:
  notch -> notch, dynamic-island -> dynamic-island, home-button -> home button.
Never one bezel image for all models. Never content pasted onto a bezel.
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath, QFont, QLinearGradient
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect,
)


@dataclass
class ScreenSpec:
    model: str
    display_name: str
    width_pt: int
    height_pt: int
    pixel_ratio: float
    corner_radius: float
    bezel: float
    cutout: str  # "notch" | "dynamic-island" | "home-button" | "none"
    cutout_width: float = 0
    cutout_height: float = 0


DEVICES: dict[str, ScreenSpec] = {
    "iPhone14,7": ScreenSpec(
        model="iPhone14,7", display_name="iPhone 13",
        width_pt=390, height_pt=844, pixel_ratio=3.0,
        corner_radius=47, bezel=12, cutout="notch",
        cutout_width=150, cutout_height=30,
    ),
    "iPhone14,8": ScreenSpec(
        model="iPhone14,8", display_name="iPhone 14",
        width_pt=390, height_pt=844, pixel_ratio=3.0,
        corner_radius=47, bezel=12, cutout="notch",
        cutout_width=150, cutout_height=30,
    ),
    "iPhone15,2": ScreenSpec(
        model="iPhone15,2", display_name="iPhone 14 Pro",
        width_pt=393, height_pt=852, pixel_ratio=3.0,
        corner_radius=55, bezel=12, cutout="dynamic-island",
        cutout_width=126, cutout_height=37,
    ),
    "iPhone14,6": ScreenSpec(
        model="iPhone14,6", display_name="iPhone SE (3rd gen)",
        width_pt=375, height_pt=667, pixel_ratio=2.0,
        corner_radius=6, bezel=18, cutout="home-button",
        cutout_width=46, cutout_height=46,
    ),
}

DEFAULT_MODEL = "iPhone14,7"


class IPhonePreview(QWidget):
    """Live iPhone frame preview. Call set_model(identifier) to switch."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._spec = DEVICES[DEFAULT_MODEL]
        self._device_name = "No Device"
        self._device_info = "Please connect a device."
        # Fixed preview size; internal drawing scales the spec proportionally
        # with explicit padding so the whole phone (frame + home button)
        # is always fully visible, never cut (user 2026-10-20).
        # 200x420 to fit in 820px window without clipping.
        self.setFixedSize(200, 420)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 3D depth: one soft drop shadow under the whole phone slab.
        _shadow = QGraphicsDropShadowEffect(self)
        _shadow.setBlurRadius(24)
        _shadow.setOffset(0, 10)
        _shadow.setColor(QColor(20, 40, 90, 110))
        self.setGraphicsEffect(_shadow)

    # -- public API -----------------------------------------------------
    def set_model(self, identifier: str):
        self._spec = DEVICES.get(identifier, DEVICES[DEFAULT_MODEL])
        self.update()

    def set_device(self, name: str, info: str):
        self._device_name = name or "No Device"
        self._device_info = info or "Please connect a device."
        self.update()

    # -- paint ----------------------------------------------------------
    def paintEvent(self, event):  # noqa: N802
        spec = self._spec
        w, h = self.width(), self.height()

        # PAD reserves room for the bezel + home button on ALL sides, so the
        # whole phone is always 1 utuh (fully visible), never cut off.
        PAD = 14
        aspect = spec.width_pt / spec.height_pt
        sw = min(w - PAD * 2, (h - PAD * 2) * aspect)
        sh = sw / aspect
        ox = (w - sw) / 2
        oy = (h - sh) / 2
        scale = sw / spec.width_pt

        bezel = spec.bezel * scale
        radius = spec.corner_radius * scale

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Layer 1: frame / bezel (dark vertical gradient, rounded per model).
        frame_rect = QRectF(ox - bezel, oy - bezel, sw + bezel * 2, sh + bezel * 2)
        frame_path = QPainterPath()
        frame_path.addRoundedRect(frame_rect, radius + bezel, radius + bezel)
        frame_grad = QLinearGradient(frame_rect.topLeft(), frame_rect.bottomLeft())
        frame_grad.setColorAt(0, QColor("#3A3F4A"))
        frame_grad.setColorAt(1, QColor("#14161A"))
        p.fillPath(frame_path, frame_grad)

        # Layer 2: screen area, clipped to corner radius.
        screen_path = QPainterPath()
        screen_path.addRoundedRect(QRectF(ox, oy, sw, sh), radius, radius)
        p.save()
        p.setClipPath(screen_path)
        # Screen gradient: deep blue like the app theme.
        grad = QLinearGradient(ox, oy, ox, oy + sh)
        grad.setColorAt(0, QColor("#1A3578"))
        grad.setColorAt(1, QColor("#0C1C4E"))
        p.fillRect(QRectF(ox, oy, sw, sh), grad)

        # Diagonal glass gloss: white sheen from the top-left, gone by
        # ~45% of the screen height (still clipped to the screen radius).
        gloss = QLinearGradient(ox, oy, ox + sw * 0.7, oy + sh * 0.45)
        gloss.setColorAt(0, QColor(255, 255, 255, 46))
        gloss.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillRect(QRectF(ox, oy, sw, sh), gloss)

        # Live device info on the screen (not a static sticker).
        p.setPen(QColor("#FFFFFF"))
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        p.setFont(font)
        p.drawText(QRectF(ox + 12, oy + 52, sw - 24, 30),
                   Qt.AlignmentFlag.AlignHCenter, self._device_name)
        font.setPointSize(8)
        font.setBold(False)
        p.setFont(font)
        p.setPen(QColor(184, 201, 240))
        p.drawText(QRectF(ox + 12, oy + 78, sw - 24, 40),
                   Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap,
                   self._device_info)
        # Time top-left, like a real status bar.
        font.setPointSize(9)
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor("#FFFFFF"))
        p.drawText(QRectF(ox + 16, oy + 12, 80, 20),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   "9:41")
        p.restore()

        # Screen edge highlight.
        p.setPen(QColor(255, 255, 255, 40))
        p.drawPath(screen_path)

        # Layer 3: cutout — SEPARATE element above the screen.
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#000000"))
        if spec.cutout == "notch":
            cw = spec.cutout_width * scale
            ch = spec.cutout_height * scale
            notch = QPainterPath()
            notch.moveTo(ox + sw / 2 - cw / 2, oy)
            notch.lineTo(ox + sw / 2 - cw / 2 + 8 * scale, oy + ch)
            notch.lineTo(ox + sw / 2 + cw / 2 - 8 * scale, oy + ch)
            notch.lineTo(ox + sw / 2 + cw / 2, oy)
            notch.closeSubpath()
            p.drawPath(notch)
        elif spec.cutout == "dynamic-island":
            cw = spec.cutout_width * scale
            chh = spec.cutout_height * scale
            island = QPainterPath()
            island.addRoundedRect(
                QRectF(ox + sw / 2 - cw / 2, oy + 10 * scale, cw, chh),
                chh / 2, chh / 2)
            p.drawPath(island)
        elif spec.cutout == "home-button":
            d = spec.cutout_width * scale
            cx = ox + sw / 2
            cy = oy + sh + bezel / 2
            btn = QPainterPath()
            btn.addEllipse(QRectF(cx - d / 2, cy - d / 2, d, d))
            p.setBrush(QColor("#2c2c2e"))
            p.drawPath(btn)
            p.setPen(QColor(255, 255, 255, 60))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(btn)

        p.end()
