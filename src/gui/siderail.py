"""WorkSlop Desktop sidebar utility menus (clean-light UI).

Second section of the single left sidebar, under the tweak families:
Backup, Apply, Settings, recovery + tutorial menus. Same flat row style
as the top section (user-picked Canva reference, 2026-10-20).

Emits ``menu_selected(menu_id)``; the main window navigates.
"""
from PySide6.QtCore import Qt, QCoreApplication, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QToolButton, QButtonGroup, QSizePolicy,
)

from src.gui.theme import ColorThemeManager, theme_icon

# menu_id -> (label, custom icon resource)
MENUS = [
    ("backup", "Backup", ":/icon/ws2-backup.svg"),
    ("apply", "Apply", ":/icon/ws2-apply.svg"),
    ("settings", "Settings", ":/icon/ws2-gear.svg"),
    ("rec_enter", "Recovery Mode Guide", ":/icon/ws2-flash.svg"),
    ("rec_exit", "Exit Recovery Guide", ":/icon/ws2-refresh.svg"),
    ("dfu_guide", "DFU Guide", ":/icon/ws2-toolbox.svg"),
    ("restore_guide", "Restore Guide", ":/icon/ws2-device.svg"),
    ("beta_guide", "Beta iOS", ":/icon/ws2-beta.svg"),
    ("app_guide", "WorkSlop Guide", ":/icon/ws2-guide.svg"),
]

RAIL_WIDTH = 216
BTN_HEIGHT = 46

ICON_OFF = "#66707E"
ICON_ON = "#2563EB"


class SideRail(QWidget):
    """Flat sidebar section: utility menus (below the tweak families)."""

    menu_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("rightRail")
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
        for menu_id, label, icon_res in MENUS:
            btn = QToolButton(self)
            btn.setText(QCoreApplication.translate("Nugget", label))
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setObjectName(f"rail_{menu_id}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(RAIL_WIDTH - 4, BTN_HEIGHT)
            btn.setIconSize(QSize(20, 20))
            btn.setProperty("ws_icon_res", icon_res)
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

    # -- internals ------------------------------------------------------
    def _update_icon(self, btn, icon_res: str, checked: bool):
        btn.setIcon(theme_icon(icon_res, ICON_ON if checked else ICON_OFF))
        btn.setIconSize(QSize(20, 20))

    def _retheme(self):
        self.setStyleSheet("""
            QWidget#rightRail {
                background-color: transparent;
                border: none;
            }
            QWidget#rightRail QToolButton {
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
            QWidget#rightRail QToolButton:hover {
                background-color: #F0F3F8;
            }
            QWidget#rightRail QToolButton:checked {
                background-color: #EAF1FE;
                color: #2563EB;
                font-weight: 600;
                border-left: 3px solid #2563EB;
            }
            QWidget#rightRail QToolButton:disabled {
                color: #9AA3B2;
            }
        """)
        for _menu_id, btn in self._buttons.items():
            self._update_icon(btn, btn.property("ws_icon_res"), btn.isChecked())
