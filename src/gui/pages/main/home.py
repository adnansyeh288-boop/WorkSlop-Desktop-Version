"""WorkSlop Desktop home page — UI rebuild 2026-10-20.

Layout (user spec):
  LEFT  : blue WorkSlop app-icon + "WorkSlop Desktop" title + credits.
  RIGHT : REAL iPhone preview (device database, frame/screen/cutout layers).
  BELOW : Apply Tweaks (white blur transparent) + Cancel Apply (blue).

No AI slop. No static stickers.
"""
from PySide6.QtCore import Qt, QSize, QCoreApplication
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy,
)

from ..page import Page
from src.qt.mainwindow_ui import Ui_Nugget
from src.gui.preset_widget import PresetWidget
from src.gui.theme import ColorThemeManager
from src.gui.iphone_preview import IPhonePreview
from src.gui.brand_credits import make_credits_label


class HomePage(Page):
    def __init__(self, window, ui: Ui_Nugget):
        super().__init__()
        self.window = window
        self.ui = ui
        self.show_uuid = False
        self.preset_widget = None
        self._preview = None

    def load_page(self):
        self.ui.phoneVersionLbl.linkActivated.connect(self.toggle_version_label)

        from PySide6.QtWidgets import QSizePolicy as _SP
        for _lbl in (self.ui.phoneNameLbl, self.ui.phoneVersionLbl):
            _lbl.setWordWrap(True)
            _lbl.setMinimumWidth(190)
            _lbl.setSizePolicy(_SP.Policy.Expanding, _SP.Policy.Preferred)
        self.ui.verticalWidget_15.setMinimumWidth(220)

        self._build_home()
        self._inject_preset_widget()

    # -- layout ---------------------------------------------------------
    def _build_home(self):
        c0 = ColorThemeManager.instance().colors

        band = getattr(self.ui, "horizontalWidget_14", None)
        host_layout = self.ui.verticalLayout_2
        if band is not None:
            idx = host_layout.indexOf(band)
            band.setVisible(False)
            host_layout.removeWidget(band)
        else:
            idx = 0

        hero = QWidget(self.ui.homePage)
        hero.setObjectName("wsHero")
        hero.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        hero.setStyleSheet("background: transparent;")

        root = QVBoxLayout(hero)
        root.setContentsMargins(24, 12, 24, 12)
        root.setSpacing(18)

        # -- top row: LEFT branding | RIGHT iPhone preview ----------------
        top = QHBoxLayout()
        top.setSpacing(32)

        # LEFT: blue WorkSlop app-icon + title + credits.
        left = QVBoxLayout()
        left.setSpacing(14)
        left.setAlignment(Qt.AlignVCenter)

        icon_lbl = QLabel(hero)
        icon_lbl.setPixmap(QIcon(":/credits/workslop.png").pixmap(QSize(120, 120)))
        icon_lbl.setStyleSheet("background: transparent;")
        left.addWidget(icon_lbl, 0, Qt.AlignLeft)

        title = QLabel("WorkSlop Desktop", hero)
        title.setStyleSheet(
            f"background: transparent; color: {c0.text_primary};"
            " font-size: 34px; font-weight: 800;")
        left.addWidget(title, 0, Qt.AlignLeft)

        self.credits_lbl = make_credits_label(
            hero, c0.text_secondary, c0.accent, align_center=False)
        self.credits_lbl.setStyleSheet(
            "background: transparent; font-size: 14px; font-weight: 500;")
        left.addWidget(self.credits_lbl, 0, Qt.AlignLeft)

        # Apply row under the credits (left column, not overlapping phone).
        apply_row = QHBoxLayout()
        apply_row.setSpacing(12)

        apply_btn = QPushButton(
            QCoreApplication.translate("Nugget", "Apply Tweaks"), hero)
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setFixedHeight(52)
        apply_btn.setMinimumWidth(220)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #5B9BFF;
                border: 1px solid #5B9BFF;
                border-radius: 26px;
                color: #FFFFFF;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #6BABFF;
            }
            QPushButton:pressed {
                background-color: #3B82F6;
            }
        """)
        apply_btn.clicked.connect(self._on_home_apply)
        apply_row.addWidget(apply_btn)

        cancel_btn = QPushButton(
            QCoreApplication.translate("Nugget", "Cancel Apply"), hero)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(52)
        cancel_btn.setMinimumWidth(160)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A3578;
                border: 1px solid #1A3578;
                border-radius: 26px;
                color: #FFFFFF;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #24448F;
            }
            QPushButton:pressed {
                background-color: #122A6B;
            }
        """)
        cancel_btn.clicked.connect(self._on_home_cancel_apply)
        apply_row.addWidget(cancel_btn)
        apply_row.addStretch(1)
        left.addLayout(apply_row)

        left.addStretch(1)
        top.addLayout(left, 1)

        # RIGHT: real iPhone preview (device database driven).
        self._preview = IPhonePreview(hero)
        top.addWidget(self._preview, 0, Qt.AlignRight | Qt.AlignVCenter)

        root.addLayout(top, 1)

        host_layout.insertWidget(idx, hero)

        # Brand the big button icon too (kept for compat, hidden with band).
        hero_btn = getattr(self.ui, "bigNuggetBtn", None)
        if hero_btn is not None:
            hero_btn.setIcon(QIcon(":/credits/workslop.png"))
            hero_btn.setIconSize(QSize(170, 170))
        for name in ("discordBtn", "starOnGithubBtn"):
            btn = getattr(self.ui, name, None)
            if btn is not None:
                btn.setVisible(False)
        credits = getattr(self.ui, "verticalWidget_6", None)
        if credits is not None:
            credits.setVisible(False)

    def _on_home_apply(self):
        """Apply Tweaks from the home page."""
        self.window.on_applyPageBtn_clicked()

    def _on_home_cancel_apply(self):
        """Cancel a running apply (best-effort)."""
        mgr = getattr(self.window, "device_manager", None)
        cancel = getattr(mgr, "cancel_apply", None)
        if callable(cancel):
            try:
                cancel()
            except Exception:
                pass
        try:
            self.window.statusBar().showMessage("Apply cancelled.")
        except Exception:
            pass

    def refresh_preview(self, model_id: str = "", name: str = "", info: str = ""):
        """Push live device data into the iPhone preview."""
        if self._preview is None:
            return
        if model_id:
            self._preview.set_model(model_id)
        self._preview.set_device(name, info)

    def set_full_nugget(self, enabled: bool):
        widget = getattr(self, "preset_widget", None)
        if widget is not None:
            widget.apply_full_nugget_style(enabled)
        credits = getattr(self, "credits_lbl", None)
        if credits is not None:
            from src.gui.brand_credits import credits_html
            if enabled:
                credits.setText(credits_html("#e8e8e8", "#3b82f7"))
            else:
                c = ColorThemeManager.instance().colors
                credits.setText(credits_html(c.text_secondary, c.accent))

    def _inject_preset_widget(self):
        layout = self.ui.verticalLayout_2
        self.preset_widget = PresetWidget(
            window=self.window,
            on_manage=self.window.open_presets_section,
            ios_style=False)
        if hasattr(self.ui, "appVersionLbl"):
            layout.insertWidget(layout.indexOf(self.ui.appVersionLbl),
                                self.preset_widget)
        else:
            layout.addWidget(self.preset_widget)
        self.preset_widget.refresh()

    def refresh_preset_widget(self):
        if self.preset_widget is not None:
            self.preset_widget.refresh()

    ## ACTIONS
    def updatePhoneInfo(self):
        self.ui.phoneNameLbl.setText(self.window.device_manager.get_current_device_name())
        ver = self.window.device_manager.get_current_device_version()
        build = self.window.device_manager.get_current_device_build()
        self.show_uuid = False
        if ver != "":
            self.show_version_text(version=ver, build=build)
        else:
            self.ui.phoneVersionLbl.setText(QCoreApplication.tr("Please connect a device."))
        # Push live data to the iPhone preview.
        try:
            model = ""
            dev = getattr(self.window, "data_singleton", None)
            if dev is not None and getattr(dev, "current_device", None) is not None:
                model = getattr(dev.current_device, "model", "") or ""
            name = self.window.device_manager.get_current_device_name()
            info = f"iOS {ver} ({build})" if ver else "Please connect a device."
            self.refresh_preview(model_id=model, name=name, info=info)
        except Exception:
            pass

    def toggle_version_label(self):
        if self.show_uuid:
            self.show_uuid = False
            ver = self.window.device_manager.get_current_device_version()
            build = self.window.device_manager.get_current_device_build()
            if ver != "":
                self.show_version_text(version=ver, build=build)
        else:
            self.show_uuid = True
            uuid = self.window.device_manager.get_current_device_udid()
            if uuid != "":
                c = ColorThemeManager.instance().colors
                self.ui.phoneVersionLbl.setText(
                    f"<a style=\"text-decoration:none; color: {c.text_secondary};\" href=\"#\">{uuid}</a>")

    def show_version_text(self, version: str, build: str):
        c = ColorThemeManager.instance().colors
        support_str: str = f"<span style=\"color: {c.success};\">" + QCoreApplication.tr("Supported!") + "</span></a>"
        if not self.window.device_manager.get_current_device_is_supported_by_fork():
            support_str = f"<span style=\"color: {c.error};\">" + QCoreApplication.tr("Not Supported.") + "</span></a>"
        elif self.window.device_manager.get_current_device_partially_supported():
            support_str = f"<span style=\"color: {c.warning};\">" + QCoreApplication.tr("Partially Supported") + "</span></a>"
        self.ui.phoneVersionLbl.setText(
            f"<a style=\"text-decoration:none; color: {c.text_secondary};\" href=\"#\">iOS {version} ({build}) {support_str}")
