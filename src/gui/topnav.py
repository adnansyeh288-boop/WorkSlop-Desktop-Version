"""WorkSlop Desktop LEFT rail — tweak family menus (UI rebuild 2026-10-20).

Vertical rail docked to the LEFT edge, vertically centered. Carries every
tweak family as its own button. Blue like the WorkSlop icon with total
gaussian-blur translucency (not pure color).

Emits ``menu_selected(menu_id)``; the main window performs navigation.
"""
from PySide6.QtCore import Qt, QCoreApplication, Signal, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QToolButton, QButtonGroup, QSizePolicy,
    QGraphicsDropShadowEffect,
)

from src.gui.theme import ColorThemeManager, color_icon

# menu_id -> (label, custom icon resource, legacy sidebar button objectName)
MENUS = [
    ("home", "Home", ":/icon/ws2-home.svg", "homePageBtn"),
    ("posterboard", "Posterboard", ":/icon/ws2-poster.svg", "posterboardPageBtn"),
    ("gestalt", "Mobile\nGestalt", ":/icon/ws2-chip.svg", "gestaltPageBtn"),
    ("statusbar", "Status\nBar", ":/icon/ws2-signal.svg", "statusBarPageBtn"),
    ("springboard", "Spring\nBoard", ":/icon/ws2-apps.svg", "springboardOptionsPageBtn"),
    ("internal", "Internal", ":/icon/ws2-sliders.svg", "internalOptionsPageBtn"),
    ("liquidglass", "Liquid\nGlass", ":/icon/ws2-glass.svg", "liquidGlassPageBtn"),
    ("daemons", "Daemons", ":/icon/ws2-daemons.svg", "daemonsPageBtn"),
    ("iconthemes", "Icon\nThemes", ":/icon/ws2-wallpaper.svg", "iconThemesPageBtn"),
]

RAIL_WIDTH = 104
BTN_HEIGHT = 78

# WorkSlop blue with total blur: deep blue, heavily translucent so the
# animated Apple-logo background bleeds through (gaussian-blur glass).
RAIL_BG = "#1A3578"
RAIL_BG_HOVER = "rgba(36, 68, 143, 0.95)"
RAIL_BG_CHECKED = "rgba(91, 155, 255, 0.95)"
RAIL_BORDER = "rgba(255, 255, 255, 0.28)"


class TopNavBar(QWidget):
    """Vertical blue-blur rail for tweak-family menus (left edge)."""

    menu_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("leftRail")
        self.setFixedWidth(RAIL_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed,
                           QSizePolicy.Policy.Expanding)
        # Required for stylesheet background-color to paint on plain QWidget.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 0, 8, 0)
        outer.addStretch(1)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(6)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = {}
        self._shadows = {}
        for menu_id, label, icon_res, legacy_btn in MENUS:
            btn = QToolButton(self)
            btn.setText(QCoreApplication.translate("Nugget", label))
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setObjectName(f"rail_{menu_id}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(RAIL_WIDTH - 16, BTN_HEIGHT)
            btn.setProperty("ws_icon_res", icon_res)
            btn.setProperty("legacy_btn", legacy_btn)
            # 3D depth: soft drop shadow under every rail button; the
            # checked button swaps to a tighter shadow (pressed-in look).
            shadow = QGraphicsDropShadowEffect(btn)
            shadow.setColor(QColor(30, 60, 140, 90))
            shadow.setBlurRadius(14)
            shadow.setOffset(0, 4)
            btn.setGraphicsEffect(shadow)
            self._shadows[btn] = shadow
            btn.clicked.connect(
                lambda _=False, m=menu_id: self.menu_selected.emit(m))
            btn.toggled.connect(
                lambda checked, b=btn, r=icon_res:
                    self._on_toggled(checked, b, r))
            self._group.addButton(btn)
            self._buttons[menu_id] = btn
            layout.addWidget(btn, 0, Qt.AlignHCenter)

        outer.addLayout(layout)
        outer.addStretch(1)

        self._retheme()
        ColorThemeManager.instance().theme_changed.connect(self._retheme)

    # -- public API -----------------------------------------------------
    def select(self, menu_id: str):
        btn = self._buttons.get(menu_id)
        if btn is not None:
            btn.setChecked(True)

    def set_menu_visible(self, menu_id: str, visible: bool):
        btn = self._buttons.get(menu_id)
        if btn is not None:
            btn.setVisible(visible)

    def menu_ids(self):
        return list(self._buttons.keys())

    # -- internals ------------------------------------------------------
    def _on_toggled(self, checked: bool, btn, icon_res: str):
        self._update_icon(btn, icon_res, checked)
        self._apply_shadow(btn, checked)

    def _apply_shadow(self, btn, checked: bool):
        """Checked = pressed-in: tighter, shorter shadow."""
        eff = self._shadows.get(btn)
        if eff is None:
            return
        if checked:
            eff.setBlurRadius(5)
            eff.setOffset(0, 1)
        else:
            eff.setBlurRadius(14)
            eff.setOffset(0, 4)

    def _update_icon(self, btn, icon_res: str, checked: bool):
        # Full-color 3D-style icons: color_icon keeps the SVG's own colors
        # (theme_icon would flatten them to a single tint).
        btn.setIcon(color_icon(icon_res, 30))
        btn.setIconSize(QSize(30, 30))

    def _retheme(self):
        # No navy container background (user 2026-10-20).
        # Buttons are WorkSlop blue (#82B1FF) like the WS icon, with a
        # vertical gradient for 3D depth (user order 2026-10-20).
        self.setStyleSheet(f"""
            QWidget#leftRail {{
                background-color: transparent;
                border: none;
            }}
            QWidget#leftRail QToolButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #A5C8FF, stop:0.5 #82B1FF, stop:1 #6B99EC);
                color: #FFFFFF;
                border: none;
                border-radius: 30px;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 2px;
            }}
            QWidget#leftRail QToolButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #94BEFF, stop:0.5 #93BFFF, stop:1 #558FF0);
            }}
            QWidget#leftRail QToolButton:checked {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6B99EC, stop:1 #5B93F5);
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
            }}
            QWidget#leftRail QToolButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6B99EC, stop:1 #5B93F5);
            }}
            QWidget#leftRail QToolButton:disabled {{
                color: rgba(255, 255, 255, 0.5);
                background-color: #9CA3AF;
            }}
        """)
        for _menu_id, btn in self._buttons.items():
            self._update_icon(btn, btn.property("ws_icon_res"), btn.isChecked())
            self._apply_shadow(btn, btn.isChecked())
