"""WorkSlop Desktop LEFT rail — tweak family menus (UI rebuild 2026-10-20).

Vertical rail docked to the LEFT edge, vertically centered. Carries every
tweak family as its own button. Blue like the WorkSlop icon with total
gaussian-blur translucency (not pure color).

Emits ``menu_selected(menu_id)``; the main window performs navigation.
"""
from PySide6.QtCore import Qt, QCoreApplication, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QToolButton, QButtonGroup, QSizePolicy,
)

from src.gui.theme import ColorThemeManager, theme_icon

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
            btn.clicked.connect(
                lambda _=False, m=menu_id: self.menu_selected.emit(m))
            btn.toggled.connect(
                lambda checked, b=btn, r=icon_res: self._update_icon(b, r, checked))
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
    def _update_icon(self, btn, icon_res: str, checked: bool):
        btn.setIcon(theme_icon(icon_res, "#FFFFFF"))
        btn.setIconSize(QSize(26, 26))

    def _retheme(self):
        # No navy container background (user 2026-10-20).
        # Buttons are WorkSlop blue (#5B9BFF) like the WS icon.
        self.setStyleSheet(f"""
            QWidget#leftRail {{
                background-color: transparent;
                border: none;
            }}
            QWidget#leftRail QToolButton {{
                background-color: #5B9BFF;
                color: #FFFFFF;
                border: none;
                border-radius: 18px;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 2px;
            }}
            QWidget#leftRail QToolButton:hover {{
                background-color: #6BABFF;
            }}
            QWidget#leftRail QToolButton:checked {{
                background-color: #3B82F6;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
            }}
            QWidget#leftRail QToolButton:pressed {{
                background-color: #3B82F6;
            }}
            QWidget#leftRail QToolButton:disabled {{
                color: rgba(255, 255, 255, 0.5);
                background-color: #9CA3AF;
            }}
        """)
        for _menu_id, btn in self._buttons.items():
            self._update_icon(btn, btn.property("ws_icon_res"), btn.isChecked())
