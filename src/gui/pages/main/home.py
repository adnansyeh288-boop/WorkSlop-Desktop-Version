from PySide6.QtCore import QCoreApplication
from webbrowser import open_new_tab
from ..page import Page
from src.qt.mainwindow_ui import Ui_Nugget
from src.gui.preset_widget import PresetWidget
from src.gui.theme import ColorThemeManager, theme_icon

class HomePage(Page):
    def __init__(self, window, ui: Ui_Nugget):
        super().__init__()
        self.window = window
        self.ui = ui
        self.show_uuid = False
        self.preset_widget = None

    def load_page(self):
        ## HOME PAGE ACTIONS
        self.ui.phoneVersionLbl.linkActivated.connect(self.toggle_version_label)
        self.ui.discordBtn.clicked.connect(lambda: open_new_tab("https://discord.gg/Rm6r4zeE3y"))

        # The device identity labels ("No Device / Please connect a
        # device.", a phone name, ...) were clipped to a few characters
        # by the generated layout; give the label column room and let
        # long lines wrap instead of cutting mid-word.
        from PySide6.QtWidgets import QSizePolicy
        for _lbl in (self.ui.phoneNameLbl, self.ui.phoneVersionLbl):
            _lbl.setWordWrap(True)
            _lbl.setMinimumWidth(190)
            _lbl.setSizePolicy(QSizePolicy.Policy.Expanding,
                               QSizePolicy.Policy.Preferred)
        self.ui.verticalWidget_15.setMinimumWidth(220)

        self._trim_to_logo_header()
        self._inject_preset_widget()
        # (Full Nugget restyle removed 2026-10-18 with the 3-UI system.)

    def set_full_nugget(self, enabled: bool):
        """Full Nugget (third interface) restyle of the preset block:
        Nugget-color preset text on the dark Home, the "UI reference:
        Nugget UI" credit with its GitHub button above the banner.
        Other interfaces keep the themed look untouched."""
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

    def _trim_to_logo_header(self):
        """Round 2 (user order 2026-10-18): vertical-centered hero.

        Layout from top to bottom, all centered:
          1. WorkSlop (WS) icon
          2. "WorkSlop Desktop" title directly below the icon
          3. "Developer Adnan.120hz · TikTok · GitHub · Official Website"
             below the title.
        The old horizontal band (horizontalWidget_14) is hidden and
        replaced in place. The generated file is not edited.
        """
        from PySide6.QtCore import Qt, QSize
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget
        from src.gui.brand_credits import make_credits_label

        c0 = ColorThemeManager.instance().colors

        # Hide the old horizontal band.
        band = getattr(self.ui, "horizontalWidget_14", None)
        host_layout = self.ui.verticalLayout_2
        hero = None
        if band is not None:
            idx = host_layout.indexOf(band)
            band.setVisible(False)
            host_layout.removeWidget(band)

            hero = QWidget(self.ui.homePage)
            hero.setObjectName("wsHero")
            # Expand so the hero block sits in the vertical middle of the
            # content area (user order 2026-10-18: bigger + more centered).
            from PySide6.QtWidgets import QSizePolicy
            hero.setSizePolicy(QSizePolicy.Policy.Expanding,
                               QSizePolicy.Policy.Expanding)

            # HORIZONTAL hero (user order 2026-10-19): WS icon on the LEFT
            # with text beside it (like the old days), 3 GitHub boxes on
            # the right. Liquid glass style, anti-AI-slop.
            hero_layout = QHBoxLayout(hero)
            hero_layout.setContentsMargins(32, 16, 32, 16)
            hero_layout.setSpacing(32)
            hero_layout.setAlignment(Qt.AlignVCenter)

            # LEFT: WS icon + title side by side.
            left_box = QHBoxLayout()
            left_box.setSpacing(20)
            left_box.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

            icon_lbl = QLabel(hero)
            _icon_px = QIcon(":/credits/workslop.png").pixmap(QSize(100, 100))
            icon_lbl.setPixmap(_icon_px)
            icon_lbl.setStyleSheet("background: transparent;")
            icon_lbl.setFixedSize(100, 100)
            left_box.addWidget(icon_lbl)

            title_box = QVBoxLayout()
            title_box.setSpacing(4)
            title = QLabel("WorkSlop Desktop", hero)
            title.setStyleSheet(
                "background: transparent; color: #FFFFFF;"
                " font-size: 32px; font-weight: 600;")
            title_box.addWidget(title)

            self.credits_lbl = make_credits_label(
                hero, c0.text_secondary, c0.accent, align_center=False)
            self.credits_lbl.setStyleSheet(
                "background: transparent; font-size: 14px; font-weight: 500;")
            title_box.addWidget(self.credits_lbl)
            left_box.addLayout(title_box)

            hero_layout.addLayout(left_box)
            hero_layout.addStretch(1)

            # 4. GitHub credit boxes (user order 2026-10-18 ronde 8): three
            # boxes below the title — Adnan.120hz, awesomenull (GoldenNugget
            # dev), leminlimez (Nugget dev). Icons MUST come from the repo
            # (:/icon/github.svg), not generated. Clicking a box opens the
            # GitHub profile in the browser.
            from PySide6.QtWidgets import QGridLayout
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            from src.gui.ios.components import IOSCard
            # RIGHT: 3 GitHub boxes — liquid glass, not white glossy.
            # Adnan.120hz clickable, others pure display.
            gh_row = QHBoxLayout()
            gh_row.setSpacing(12)
            gh_row.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
            gh_profiles = [
                ("Adnan.120hz", "https://github.com/adnan120hz"),
                ("awesomenull", "https://github.com/awesomenull"),
                ("leminlimez", "https://github.com/leminlimez"),
            ]
            for name, url in gh_profiles:
                box = QWidget(hero)
                _is_adnan = (name == "Adnan.120hz")
                if _is_adnan:
                    box.setCursor(Qt.PointingHandCursor)
                else:
                    box.setCursor(Qt.ArrowCursor)
                box.setStyleSheet("""
                    QWidget {
                        background-color: rgba(35, 64, 150, 0.55);
                        border: 1px solid rgba(150, 180, 255, 0.4);
                        border-radius: 16px;
                    }
                    QWidget:hover {
                        background-color: rgba(35, 64, 150, 0.75);
                    }
                """)
                box_layout = QVBoxLayout(box)
                box_layout.setContentsMargins(16, 12, 16, 12)
                box_layout.setSpacing(8)
                box_layout.setAlignment(Qt.AlignHCenter)
                icon = QLabel(box)
                icon.setPixmap(theme_icon(
                    ":/icon/github.svg", "#FFFFFF").pixmap(40, 40))
                icon.setAlignment(Qt.AlignHCenter)
                icon.setStyleSheet("background: transparent; border: none;")
                box_layout.addWidget(icon)
                lbl = QLabel(name, box)
                lbl.setAlignment(Qt.AlignHCenter)
                lbl.setStyleSheet(
                    "background: transparent; border: none; color: #FFFFFF;"
                    " font-size: 13px; font-weight: 600;")
                box_layout.addWidget(lbl)
                box.setFixedWidth(140)
                if _is_adnan:
                    box.mousePressEvent = (
                        lambda _e, u=url: QDesktopServices.openUrl(QUrl(u)))
                gh_row.addWidget(box)
            hero_layout.addLayout(gh_row)

            # Search bar at top-right (user order 2026-10-19 ronde 11).
            # Placed in its own container ABOVE the hero, not inside the
            # centered vbox (which broke the layout).
            from PySide6.QtWidgets import QLineEdit
            from PySide6.QtGui import QAction as _QAction
            _search_container = QWidget(self.ui.homePage)
            _search_container.setStyleSheet("background: transparent;")
            _search_hbox = QHBoxLayout(_search_container)
            _search_hbox.setContentsMargins(0, 0, 16, 8)
            _search_box = QLineEdit(_search_container)
            _search_box.setPlaceholderText("Search tweaks...")
            _search_box.setFixedHeight(40)
            _search_box.setFixedWidth(280)
            _search_box.setStyleSheet("""
                QLineEdit {
                    background-color: rgba(255, 255, 255, 240);
                    border-radius: 20px;
                    border: 1px solid #C8C8C8;
                    padding-left: 40px;
                    padding-right: 12px;
                    color: #0A0A0A;
                    font-size: 13px;
                }
            """)
            _search_icon = _QAction(_search_box)
            _search_icon.setIcon(QIcon(":/icon/ws-search.svg"))
            _search_box.addAction(_search_icon, QLineEdit.ActionPosition.LeadingPosition)
            _search_box.returnPressed.connect(
                lambda: self.window._on_search_tweak_from_home(_search_box.text()))
            _search_hbox.addStretch(1)
            _search_hbox.addWidget(_search_box)
            host_layout.insertWidget(idx, _search_container)

            host_layout.insertWidget(idx + 1, hero, 0, Qt.AlignHCenter)

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

    def _inject_preset_widget(self):
        """Add the active-preset banner at the bottom of the home page."""
        layout = self.ui.verticalLayout_2
        self.preset_widget = PresetWidget(
            window=self.window,
            on_manage=self.window.open_presets_section,
            ios_style=False)
        # Place it above the version label at the very bottom, then keep the
        # version label pinned below it.
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
        # name label
        self.ui.phoneNameLbl.setText(self.window.device_manager.get_current_device_name())
        # version label
        ver = self.window.device_manager.get_current_device_version()
        build = self.window.device_manager.get_current_device_build()
        self.show_uuid = False
        if ver != "":
            self.show_version_text(version=ver, build=build)
        else:
            self.ui.phoneVersionLbl.setText(QCoreApplication.tr("Please connect a device."))

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