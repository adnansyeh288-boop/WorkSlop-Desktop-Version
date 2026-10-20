"""WorkSlop Desktop LEFT sidebar — tweak family menus (clean-light UI).

Flat text sidebar inside the white window card, following the user-picked
Canva reference (2026-10-20): rows with a small tinted ws2 glyph + label,
the active row gets a light-blue fill, blue text and a blue bar on its
left edge. No panels, no shadows, no pills.

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
    ("gestalt", "Mobile Gestalt", ":/icon/ws2-chip.svg", "gestaltPageBtn"),
    ("statusbar", "Status Bar", ":/icon/ws2-signal.svg", "statusBarPageBtn"),
    ("springboard", "SpringBoard", ":/icon/ws2-apps.svg", "springboardOptionsPageBtn"),
    ("internal", "Internal", ":/icon/ws2-internal.svg", "internalOptionsPageBtn"),
    ("liquidglass", "Liquid Glass", ":/icon/ws2-glass.svg", "liquidGlassPageBtn"),
    ("daemons", "Daemons", ":/icon/ws2-daemons.svg", "daemonsPageBtn"),
    ("iconthemes", "Icon Themes", ":/icon/ws2-wallpaper.svg", "iconThemesPageBtn"),
]

RAIL_WIDTH = 216
BTN_HEIGHT = 46

ICON_OFF = "#66707E"
ICON_ON = "#2563EB"


class TopNavBar(QWidget):
    """Flat sidebar section: tweak-family menus (top of the sidebar)."""

    menu_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("leftRail")
        self.setFixedWidth(RAIL_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed,
                           QSizePolicy.Policy.Preferred)
        # Required for stylesheet background-color to paint on plain QWidget.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = {}
        for menu_id, label, icon_res, legacy_btn in MENUS:
            btn = QToolButton(self)
            btn.setText(QCoreApplication.translate("Nugget", label))
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setObjectName(f"rail_{menu_id}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(RAIL_WIDTH - 4, BTN_HEIGHT)
            btn.setIconSize(QSize(20, 20))
            btn.setProperty("ws_icon_res", icon_res)
            btn.setProperty("legacy_btn", legacy_btn)
            btn.clicked.connect(
                lambda _=False, m=menu_id: self.menu_selected.emit(m))
            btn.toggled.connect(
                lambda checked, b=btn, r=icon_res:
                    self._update_icon(b, r, checked))
            self._group.addButton(btn)
            self._buttons[menu_id] = btn
            layout.addWidget(btn)

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
        # Same ws2 glyph set as before, flattened to one tint (slate when
        # idle, accent blue when active) so it reads on the white card.
        btn.setIcon(theme_icon(icon_res, ICON_ON if checked else ICON_OFF))
        btn.setIconSize(QSize(20, 20))

    def _retheme(self):
        self.setStyleSheet("""
            QWidget#leftRail {
                background-color: transparent;
                border: none;
            }
            QWidget#leftRail QToolButton {
                background: transparent;
                color: #374151;
                border: 1px solid transparent;
                border-left: 3px solid transparent;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 500;
                text-align: left;
                padding-left: 10px;
            }
            QWidget#leftRail QToolButton:hover {
                background-color: #F0F3F8;
            }
            QWidget#leftRail QToolButton:checked {
                background-color: #EAF1FE;
                color: #2563EB;
                font-weight: 600;
                border-left: 3px solid #2563EB;
            }
            QWidget#leftRail QToolButton:disabled {
                color: #9AA3B2;
            }
        """)
        for _menu_id, btn in self._buttons.items():
            self._update_icon(btn, btn.property("ws_icon_res"), btn.isChecked())
