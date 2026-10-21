"""WorkSlop Desktop home page — UI rebuild 2026-10-20.

Layout (user spec):
  LEFT  : blue WorkSlop app-icon + "WorkSlop Desktop" title + credits.
  RIGHT : REAL iPhone preview (device database, frame/screen/cutout layers).
  BELOW : Apply Tweaks (white blur transparent) + Cancel Apply (blue).

No AI slop. No static stickers.
"""
from PySide6.QtCore import Qt, QSize, QCoreApplication, QUrl
from PySide6.QtGui import QIcon, QColor, QDesktopServices, QImage
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QToolButton,
    QSizePolicy, QGraphicsDropShadowEffect,
)

from ..page import Page
from src.qt.mainwindow_ui import Ui_Nugget
from src.gui.preset_widget import PresetWidget
from src.gui.theme import ColorThemeManager, theme_icon
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
        # Live screen stream (real device screen over USB); owned here,
        # started/stopped by _sync_stream() as the device changes.
        self._stream = None
        self._stream_udid = None

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
        root.setContentsMargins(24, 30, 24, 12)
        root.setSpacing(18)

        # -- top row: LEFT branding | RIGHT iPhone preview ----------------
        top = QHBoxLayout()
        top.setSpacing(32)

        # LEFT: blue WorkSlop app-icon + title + credits.
        left = QVBoxLayout()
        left.setSpacing(14)
        left.setAlignment(Qt.AlignVCenter)

        # Icon + title side by side (user order 2026-10-20: the
        # "WorkSlop Desktop" text sits right beside the app icon).
        brand_row = QHBoxLayout()
        brand_row.setSpacing(18)
        icon_lbl = QLabel(hero)
        icon_lbl.setPixmap(QIcon(":/credits/workslop.png").pixmap(QSize(120, 120)))
        icon_lbl.setStyleSheet("background: transparent;")
        brand_row.addWidget(icon_lbl, 0, Qt.AlignVCenter)

        title = QLabel(hero)
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setText(
            "<span style='color:#2563EB;'>WorkSlop</span>"
            " <span style='color:#111827;'>Desktop</span>")
        title.setStyleSheet(
            "background: transparent; font-size: 34px; font-weight: 800;")
        brand_row.addWidget(title, 0, Qt.AlignVCenter)
        brand_row.addStretch(1)
        left.addLayout(brand_row)

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
                background-color: #2563EB;
                border: 1px solid #2563EB;
                border-radius: 14px;
                color: #FFFFFF;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
                border-color: #1D4ED8;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
                border-color: #1E40AF;
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
                background-color: #FFFFFF;
                border: 1px solid #D9E0EA;
                border-radius: 14px;
                color: #111827;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F0F3F8;
            }
            QPushButton:pressed {
                background-color: #E4E9F0;
            }
        """)
        cancel_btn.clicked.connect(self._on_home_cancel_apply)
        apply_row.addWidget(cancel_btn)

        # WorkSlop Logs (user order 2026-10-20): live view of the app's
        # real session log, copyable/savable for bug reports.
        logs_btn = QPushButton(
            QCoreApplication.translate("Nugget", "WorkSlop Logs"), hero)
        logs_btn.setCursor(Qt.PointingHandCursor)
        logs_btn.setFixedHeight(52)
        logs_btn.setMinimumWidth(170)
        logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #D9E0EA;
                border-radius: 14px;
                color: #111827;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F0F3F8;
            }
            QPushButton:pressed {
                background-color: #E4E9F0;
            }
        """)
        logs_btn.clicked.connect(self._on_home_logs)
        apply_row.addWidget(logs_btn)
        apply_row.addStretch(1)
        left.addLayout(apply_row)

        # Social boxes (user order 2026-10-20): three LARGE blue boxes
        # filling the middle band under the Apply/Cancel row — GitHub,
        # TikTok, and the WorkSlop website — each with its platform
        # icon, each opening the matching link. They expand across the
        # column width with gaps between them.
        def _make_social_box(_res, _label, _url, _icon_size=26,
                             _font_px=13):
            # QToolButton with the icon ABOVE the text, so the longer
            # captions fit the box unclipped. One builder for every box
            # in both rows: identical size, color, and behaviour. An
            # empty label makes an icon-only box, an empty resource a
            # text-only box — in both cases the single element sits
            # centered in the box.
            _box_btn = QToolButton(hero)
            _box_btn.setText(_label)
            _box_btn.setCursor(Qt.PointingHandCursor)
            _box_btn.setMinimumSize(140, 92)
            _box_btn.setMaximumSize(220, 92)
            _box_btn.setSizePolicy(QSizePolicy.Policy.Expanding,
                                   QSizePolicy.Policy.Fixed)
            _box_btn.setToolButtonStyle(
                Qt.ToolButtonStyle.ToolButtonTextUnderIcon if _res and _label
                else Qt.ToolButtonStyle.ToolButtonTextOnly if _label
                else Qt.ToolButtonStyle.ToolButtonIconOnly)
            if _res:
                _box_btn.setIcon(theme_icon(_res, "#FFFFFF"))
                _box_btn.setIconSize(QSize(_icon_size, _icon_size))
            _box_btn.setAttribute(
                Qt.WidgetAttribute.WA_StyledBackground, True)
            _box_btn.setStyleSheet("""
                QToolButton {
                    background-color: #2563EB;
                    border: 1px solid #2563EB;
                    border-radius: 14px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 600;
                }
                QToolButton:hover {
                    background-color: #1D4ED8;
                    border-color: #1D4ED8;
                }
                QToolButton:pressed {
                    background-color: #1E40AF;
                    border-color: #1E40AF;
                }
            """.replace("font-size: 13px;",
                        f"font-size: {_font_px}px;"))
            _box_btn.clicked.connect(
                lambda _checked=False, u=_url:
                    QDesktopServices.openUrl(QUrl(u)))
            return _box_btn

        social_row = QHBoxLayout()
        social_row.setSpacing(14)
        _social_boxes = (
            (":/icon/github.svg", "GitHub\nAdnan.120hz",
             "https://github.com/adnan120hz"),
            (":/icon/tiktok.svg", "TikTok\nAdnan.120hz",
             "https://www.tiktok.com/@adnan.120hz"),
            (":/icon/globe.svg", "Website\nWorkSlop Desktop",
             "https://workslop-nu.vercel.app"),
        )
        for _res, _label, _url in _social_boxes:
            social_row.addWidget(_make_social_box(_res, _label, _url))
        left.addLayout(social_row)

        # Second row (user order 2026-10-20): Apple Website, Xcode,
        # License — same blue boxes, same exact size, directly under the
        # first row (the left column's 14px spacing keeps the gap even).
        # The license box names the app's real license (AGPL-3.0, see the
        # repo LICENSE file) with the GNU emblem, and opens that file.
        social_row2 = QHBoxLayout()
        social_row2.setSpacing(14)
        _social_boxes2 = (
            (":/icon/apple.svg", "Apple\napple.com",
             "https://www.apple.com"),
            (":/icon/xcode.svg", "Xcode\nApple Developer",
             "https://developer.apple.com/xcode/"),
            (":/icon/gnu.svg", "License\nAGPL-3.0",
             "https://github.com/adnan120hz/WorkSlop-Desktop-Version/blob/main/LICENSE"),
        )
        for _entry in _social_boxes2:
            social_row2.addWidget(_make_social_box(*_entry))
        left.addLayout(social_row2)

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

    def _on_home_logs(self):
        """Open the WorkSlop Logs viewer (live session log, modeless)."""
        dlg = getattr(self, "_logs_dialog", None)
        if dlg is None:
            from src.gui.logs_dialog import WorkSlopLogsDialog
            dlg = WorkSlopLogsDialog(self.window)
            self._logs_dialog = dlg
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def refresh_preview(self, model_id: str = "", name: str = "", info: str = ""):
        """Push live device data into the iPhone preview."""
        if self._preview is None:
            return
        if model_id:
            self._preview.set_model(model_id)
        self._preview.set_device(name, info)
        self._sync_stream()

    # -- live screen stream ----------------------------------------------
    def _sync_stream(self):
        """Keep the live screen stream pointed at the current device.

        Starts the capture thread when a device is (or becomes)
        current, restarts it when the device changes, and stops it +
        clears the frame when no device is connected.
        """
        try:
            dm = self.window.device_manager
            udid = dm.get_current_device_udid() or None
            version = dm.get_current_device_version() or ""
        except Exception:
            udid, version = None, ""
        if udid is None:
            if self._stream is not None:
                self._stream.stop_stream()
                self._stream = None
                self._stream_udid = None
            if self._preview is not None:
                self._preview.clear_frame()
            return
        if self._stream is not None and self._stream_udid == udid:
            return
        if self._stream is not None:
            self._stream.stop_stream()
        from src.devicemanagement.screen_stream import ScreenStreamThread
        self._stream = ScreenStreamThread(self)
        self._stream.frame_ready.connect(self._on_stream_frame)
        self._stream.status_changed.connect(self._on_stream_status)
        self._stream_udid = udid
        self._stream.start_stream(udid, version)

    def _on_stream_frame(self, data):
        if self._preview is None:
            return
        img = QImage.fromData(data)
        if img.isNull():
            return
        if img.width() > 400:
            img = img.scaledToWidth(
                400, Qt.TransformationMode.SmoothTransformation)
        self._preview.set_frame(img)

    def _on_stream_status(self, status: str):
        if self._preview is not None:
            self._preview.set_stream_status(status)

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
        elif self.window.device_manager.get_current_device_support_level() == "partial":
            support_str = f"<span style=\"color: {c.warning};\">" + QCoreApplication.tr("Partially Supported") + "</span></a>"
        self.ui.phoneVersionLbl.setText(
            f"<a style=\"text-decoration:none; color: {c.text_secondary};\" href=\"#\">iOS {version} ({build}) {support_str}")
