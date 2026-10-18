"""WorkSlop Desktop slim side rail (single-UI rebuild, round 2).

Holds the menus that do not fit the top bar: Backup, Apply, Settings plus
the device-utility and tutorial menus. Narrow icon+label buttons with full
fluid corners. Emits ``menu_selected(menu_id)``; the main window navigates.
"""
from PySide6.QtCore import Qt, QCoreApplication, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QToolButton, QButtonGroup, QSizePolicy,
)

from src.gui.theme import ColorThemeManager, theme_icon

# menu_id -> (label, icon resource)
MENUS = [
    ("backup", "Backup", ":/icon/ws-backup.svg"),
    ("apply", "Apply", ":/icon/ws-backup.svg"),
    ("settings", "Settings", ":/icon/ws-gear.svg"),
    ("rec_enter", "Recovery\nMode", ":/icon/ws-flash.svg"),
    ("rec_exit", "Exit\nRecovery", ":/icon/ws-refresh.svg"),
    ("dfu_guide", "DFU\nGuide", ":/icon/ws-toolbox.svg"),
    ("restore_guide", "Restore\nGuide", ":/icon/ws-device.svg"),
    ("beta_guide", "Beta\niOS", ":/icon/apple.svg"),
    ("app_guide", "WorkSlop\nGuide", ":/icon/ws-apps.svg"),
]

RAIL_WIDTH = 100
BTN_HEIGHT = 68


class SideRail(QWidget):
    """Slim vertical rail for overflow / utility menus."""

    menu_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sideRail")
        self.setFixedWidth(RAIL_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed,
                           QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

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

        layout.addStretch(1)
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
        c = ColorThemeManager.instance().colors
        color = "#FFFFFF" if checked else c.accent
        btn.setIcon(theme_icon(icon_res, color))
        btn.setIconSize(QSize(24, 24))

    def _retheme(self):
        c = ColorThemeManager.instance().colors
        # Fluid rounded buttons (18px on a 68px-wide button reads fully
        # rounded). Blue-white identity, no gradients.
        self.setStyleSheet(f"""
            SideRail {{
                background-color: {c.bg_secondary};
                border: 1px solid {c.card_border};
                border-radius: 22px;
            }}
            SideRail QToolButton {{
                background-color: transparent;
                color: {c.text_primary};
                border: none;
                border-radius: 18px;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 2px;
            }}
            SideRail QToolButton:hover {{
                background-color: {c.surface_hover};
            }}
            SideRail QToolButton:checked {{
                background-color: {c.accent};
                color: #FFFFFF;
            }}
            SideRail QToolButton:pressed {{
                background-color: {c.accent_pressed};
            }}
        """)
        for _menu_id, btn in self._buttons.items():
            self._update_icon(btn, btn.property("ws_icon_res"), btn.isChecked())
