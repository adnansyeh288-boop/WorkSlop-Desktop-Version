"""WorkSlop Desktop top navigation bar (single-UI rebuild, round 2).

Every tweak family gets its own top-level menu entry — there is no "All
Tweaks" grouping anywhere in the UI. Each entry is a full-capsule pill
(fluid corners per user order); the checked pill is solid Apple blue with
a white icon and label.

The bar is intentionally dumb: it emits ``menu_selected(menu_id)`` and the
main window performs the navigation. Visibility of entries (device-gated
features like Status Bar on iOS 27) is mirrored from the legacy sidebar
buttons, which remain the source of truth in the device-refresh flow.
"""
from PySide6.QtCore import Qt, QCoreApplication, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QButtonGroup, QSizePolicy,
)

from src.gui.theme import ColorThemeManager, theme_icon

# menu_id -> (label, icon resource, legacy sidebar button objectName)
MENUS = [
    ("home", "Home", ":/icon/ws-device.svg", "homePageBtn"),
    ("posterboard", "Posterboard", ":/icon/ws-poster.svg", "posterboardPageBtn"),
    ("gestalt", "Mobile Gestalt", ":/icon/ws-chip.svg", "gestaltPageBtn"),
    ("statusbar", "Status Bar", ":/icon/ws-signal.svg", "statusBarPageBtn"),
    ("springboard", "SpringBoard", ":/icon/ws-apps.svg", "springboardOptionsPageBtn"),
    ("internal", "Internal", ":/icon/ws-sliders.svg", "internalOptionsPageBtn"),
    ("liquidglass", "Liquid Glass", ":/icon/ws-glass.svg", "liquidGlassPageBtn"),
    ("daemons", "Daemons", ":/icon/ws-sliders.svg", "daemonsPageBtn"),
    ("iconthemes", "Icon Themes", ":/icon/ws-wallpaper.svg", "iconThemesPageBtn"),
]

PILL_HEIGHT = 44


class TopNavBar(QWidget):
    """Horizontal pill navigation bar for the single-UI shell."""

    menu_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topNavBar")
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Fixed)
        self.setFixedHeight(PILL_HEIGHT + 20)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = {}
        for menu_id, label, icon_res, legacy_btn in MENUS:
            btn = QPushButton(QCoreApplication.translate("Nugget", label), self)
            btn.setObjectName(f"topnav_{menu_id}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(PILL_HEIGHT)
            btn.setSizePolicy(QSizePolicy.Policy.Preferred,
                              QSizePolicy.Policy.Fixed)
            btn.setProperty("ws_icon_res", icon_res)
            btn.setProperty("legacy_btn", legacy_btn)
            btn.clicked.connect(
                lambda _=False, m=menu_id: self.menu_selected.emit(m))
            btn.toggled.connect(
                lambda checked, b=btn, r=icon_res: self._update_icon(b, r, checked))
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
        c = ColorThemeManager.instance().colors
        color = "#FFFFFF" if checked else c.accent
        btn.setIcon(theme_icon(icon_res, color))
        btn.setIconSize(QSize(20, 20))

    def _retheme(self):
        c = ColorThemeManager.instance().colors
        # Full-capsule pills: radius = half of PILL_HEIGHT. Checked pill is
        # solid blue with white text; idle pills are white with blue text.
        # No gradients, no translucency — opaque, crisp, blue-white identity.
        self.setStyleSheet(f"""
            TopNavBar {{
                background-color: transparent;
                border: none;
            }}
            TopNavBar QPushButton {{
                background-color: {c.bg_secondary};
                color: {c.accent};
                border: 1px solid {c.card_border};
                border-radius: {PILL_HEIGHT // 2}px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 12px;
            }}
            TopNavBar QPushButton:hover {{
                background-color: {c.surface_hover};
            }}
            TopNavBar QPushButton:checked {{
                background-color: {c.accent};
                color: #FFFFFF;
                border: 1px solid {c.accent};
            }}
            TopNavBar QPushButton:pressed {{
                background-color: {c.accent_pressed};
            }}
            TopNavBar QPushButton:disabled {{
                color: {c.text_disabled};
                background-color: {c.bg_tertiary};
            }}
        """)
        for menu_id, btn in self._buttons.items():
            self._update_icon(btn, btn.property("ws_icon_res"), btn.isChecked())
