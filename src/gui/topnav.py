"""WorkSlop Desktop top navigation bar (single-UI rebuild, round 2).

Every tweak family gets its own top-level menu entry — there is no "All
Tweaks" grouping anywhere in the UI. Each entry is a full-capsule pill
(fluid corners per user order); the checked pill is solid gray with
a white icon and label.

The bar is intentionally dumb: it emits ``menu_selected(menu_id)`` and the
main window performs the navigation. All entries are always visible (user
order 2026-10-18 ronde 8) — no device-gating on the top bar. The pills live
in a horizontal scroll area so they scroll instead of being cut off on
narrow screens.
"""
from PySide6.QtCore import Qt, QCoreApplication, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QButtonGroup, QSizePolicy, QScrollArea,
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
        layout.setSpacing(0)

        # Horizontal scroll area (user order 2026-10-18 ronde 8): pills must
        # never be cut off ("kepangkas") on narrow screens — they scroll
        # instead. Scrollbars hidden for a clean look; wheel/drag still scroll.
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        pills = QWidget()
        pills_layout = QHBoxLayout(pills)
        pills_layout.setContentsMargins(0, 0, 0, 0)
        pills_layout.setSpacing(8)
        pills_layout.setAlignment(Qt.AlignCenter)
        scroll.setWidget(pills)
        layout.addWidget(scroll)
        self._scroll = scroll
        # TopNavBar itself stays transparent (set once, not in _retheme).
        self.setStyleSheet("TopNavBar { background-color: transparent; border: none; }")

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = {}
        for menu_id, label, icon_res, legacy_btn in MENUS:
            btn = QPushButton(QCoreApplication.translate("Nugget", label), pills)
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
            pills_layout.addWidget(btn)

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
        # White pills → BLACK icons (user: "TULISAN HITAM"). Both checked
        # and unchecked use black for visibility on white glossy pills.
        btn.setIcon(theme_icon(icon_res, "#0A0A0A"))
        btn.setIconSize(QSize(20, 20))

    def _retheme(self):
        c = ColorThemeManager.instance().colors
        # White GLOSSY pills with BLACK text and VISIBLE SHINE (user order
        # 2026-10-19: "aku belum melihat kilauan cahaya di menu menu").
        # Enhanced gradient: bright white highlight at top for a clear
        # glossy shine, plus a subtle light border for definition.
        # Checked pill: solid white with black text + subtle inner glow.
        # NOTE: the stylesheet is set on the pills container (not TopNavBar)
        # because the QScrollArea viewport breaks TopNavBar-descendant
        # selectors for the :checked state.
        pills = self._scroll.widget()
        pills.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:0.25 #FFFFFF, stop:0.5 #F8F8F8, stop:0.75 #EDEDED, stop:1 #E0E0E0);
                color: #0A0A0A;
                border: 1px solid #C8C8C8;
                border-radius: {PILL_HEIGHT // 2}px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:0.3 #FFFFFF, stop:0.6 #F0F0F0, stop:1 #D8D8D8);
                border: 1px solid #B0B0B0;
            }}
            QPushButton:checked {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:0.4 #FAFAFA, stop:1 #E8E8E8);
                color: #0A0A0A;
                border: 2px solid #FFFFFF;
            }}
            QPushButton:pressed {{
                background-color: #D0D0D0;
            }}
            QPushButton:disabled {{
                color: {c.text_disabled};
                background-color: {c.bg_tertiary};
            }}
        """)
        for menu_id, btn in self._buttons.items():
            self._update_icon(btn, btn.property("ws_icon_res"), btn.isChecked())
