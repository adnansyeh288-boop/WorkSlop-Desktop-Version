"""WorkSlop Desktop RIGHT rail — utility menus (UI rebuild 2026-10-20).

Vertical rail docked to the RIGHT edge, vertically centered. Holds Backup,
Apply, Settings, recovery + tutorial menus. Blue like the WorkSlop icon
with total gaussian-blur translucency (not pure color).

Recovery enter/exit are tutorials only — no Apply menu (user order).

Emits ``menu_selected(menu_id)``; the main window navigates.
"""
from PySide6.QtCore import Qt, QCoreApplication, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QToolButton, QButtonGroup, QSizePolicy,
)

from src.gui.theme import theme_icon, ColorThemeManager

# menu_id -> (label, custom icon resource)
MENUS = [
    ("backup", "Backup", ":/icon/ws2-backup.svg"),
    ("apply", "Apply", ":/icon/ws2-apply.svg"),
    ("settings", "Settings", ":/icon/ws2-gear.svg"),
    ("rec_enter", "Recovery\nMode", ":/icon/ws2-flash.svg"),
    ("rec_exit", "Exit\nRecovery", ":/icon/ws2-refresh.svg"),
    ("dfu_guide", "DFU\nGuide", ":/icon/ws2-toolbox.svg"),
    ("restore_guide", "Restore\nGuide", ":/icon/ws2-device.svg"),
    ("beta_guide", "Beta\niOS", ":/icon/ws2-beta.svg"),
    ("app_guide", "WorkSlop\nGuide", ":/icon/ws2-guide.svg"),
]

RAIL_WIDTH = 104
BTN_HEIGHT = 72

# WorkSlop blue with total blur (matches left rail).
RAIL_BG = "#1A3578"
RAIL_BG_HOVER = "rgba(36, 68, 143, 0.95)"
RAIL_BG_CHECKED = "rgba(91, 155, 255, 0.95)"
RAIL_BORDER = "rgba(255, 255, 255, 0.28)"


class SideRail(QWidget):
    """Vertical blue-blur rail for utility menus (right edge)."""

    menu_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("rightRail")
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
        for menu_id, label, icon_res in MENUS:
            btn = QToolButton(self)
            btn.setText(QCoreApplication.translate("Nugget", label))
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setObjectName(f"rail_{menu_id}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(RAIL_WIDTH - 16, BTN_HEIGHT)
            btn.setProperty("ws_icon_res", icon_res)
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

    # -- internals ------------------------------------------------------
    def _update_icon(self, btn, icon_res: str, checked: bool):
        btn.setIcon(theme_icon(icon_res, "#FFFFFF"))
        btn.setIconSize(QSize(26, 26))

    def _retheme(self):
        self.setStyleSheet(f"""
            QWidget#rightRail {{
                background-color: transparent;
                border: none;
            }}
            QWidget#rightRail QToolButton {{
                background-color: #5B9BFF;
                color: #FFFFFF;
                border: none;
                border-radius: 18px;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 2px;
            }}
            QWidget#rightRail QToolButton:hover {{
                background-color: #6BABFF;
            }}
            QWidget#rightRail QToolButton:checked {{
                background-color: #3B82F6;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
            }}
            QWidget#rightRail QToolButton:pressed {{
                background-color: #3B82F6;
            }}
        """)
        for _menu_id, btn in self._buttons.items():
            self._update_icon(btn, btn.property("ws_icon_res"), btn.isChecked())
