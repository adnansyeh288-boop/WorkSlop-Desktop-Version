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
        layout.setSpacing(0)

        # The rail must never squash its buttons: on short laptop screens
        # the 9 fixed-height buttons would otherwise be compressed and
        # their labels' descenders clipped. A (chromeless) scroll area
        # keeps every button at full height and scrolls instead.
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.viewport().setStyleSheet("background: transparent;")
        scroll.setStyleSheet("background: transparent; border: none;")
        self._scroll = scroll

        holder = QWidget()
        holder.setStyleSheet("background: transparent; border: none;")
        btn_layout = QVBoxLayout(holder)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)
        from PySide6.QtWidgets import QLayout
        btn_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)

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
            btn_layout.addWidget(btn, 0, Qt.AlignHCenter)

        holder.adjustSize()
        # Pin the holder to its full content height: the scroll area must
        # scroll, never compress the fixed-height buttons.
        _full_h = holder.sizeHint().height()
        holder.setFixedHeight(_full_h)
        scroll.setWidget(holder)
        layout.addWidget(scroll, 1)
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
        # White pills → BLACK icons (user: "TULISAN HITAM"). Both checked
        # and unchecked use black for visibility on white glossy pills.
        btn.setIcon(theme_icon(icon_res, "#0A0A0A"))
        btn.setIconSize(QSize(24, 24))

    def _retheme(self):
        c = ColorThemeManager.instance().colors
        # White GLOSSY pills with BLACK text (user order 2026-10-19 ronde 10:
        # "di samakan tambahin pallet pil warna putih kayak menu menu di atas").
        # Same glossy white style as the top nav pills.
        # NOTE: the button stylesheet is set on the holder widget (not
        # SideRail) because the QScrollArea viewport breaks SideRail-
        # descendant selectors for the :checked state (user order
        # 2026-10-18 ronde 8: active menu icon must stay visible).
        self.setStyleSheet(f"""
            SideRail {{
                background-color: {c.bg_secondary};
                border: 1px solid {c.card_border};
                border-radius: 22px;
            }}
        """)
        holder = self._scroll.widget()
        # Full PILL capsules with VISIBLE SHINE (user order 2026-10-19):
        # "pil nya ga kotak tapi pil 1 per 1 seperti pil yang di atas" +
        # "aku belum melihat kilauan cahaya di menu menu".
        # Border-radius = half height for true capsule, enhanced gradient
        # for clear glossy shine, white with black text like top nav.
        holder.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
            }
            QToolButton {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:0.35 #FFFFFF, stop:0.5 #F5F5F5, stop:0.65 #E8E8E8, stop:1 #D0D0D0);
                color: #0A0A0A;
                border: 1px solid #C8C8C8;
                border-radius: 34px;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 2px;
            }
            QToolButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:0.3 #FFFFFF, stop:0.6 #F0F0F0, stop:1 #D8D8D8);
                border: 1px solid #B0B0B0;
            }
            QToolButton:checked {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:0.4 #FAFAFA, stop:1 #E8E8E8);
                color: #0A0A0A;
                border: 2px solid #FFFFFF;
            }
            QToolButton:pressed {
                background-color: #D0D0D0;
            }
        """)
        for _menu_id, btn in self._buttons.items():
            self._update_icon(btn, btn.property("ws_icon_res"), btn.isChecked())
