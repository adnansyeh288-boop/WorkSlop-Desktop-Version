from PySide6.QtCore import QCoreApplication
from webbrowser import open_new_tab
from ..page import Page
from src.qt.mainwindow_ui import Ui_Nugget
from src.gui.preset_widget import PresetWidget
from src.gui.theme import ColorThemeManager

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
            vbox = QVBoxLayout(hero)
            vbox.setContentsMargins(0, 8, 0, 8)
            vbox.setSpacing(16)
            vbox.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

            # Search bar at top-right (user order 2026-10-19 ronde 11:
            # "search bar di pojok kanan atas, fluid corner, functional").
            # Moved from ios/home.py (wrong page) to the actual HomePage.
            from PySide6.QtWidgets import QLineEdit
            from PySide6.QtGui import QAction as _QAction
            _search_box = QLineEdit(hero)
            _search_box.setPlaceholderText("Search tweaks...")
            _search_box.setFixedHeight(40)
            _search_box.setMinimumWidth(220)
            _search_box.setMaximumWidth(300)
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
            # Functional: search tweak titles, navigate on Enter.
            _search_box.returnPressed.connect(
                lambda: self.window._on_search_tweak_from_home(_search_box.text()))
            vbox.addWidget(_search_box, 0, Qt.AlignRight)

            # 1. WS icon, centered. FIXED size 120px to prevent cropping
            # (user order 2026-10-19: "icon workslop masih ke potong").
            # The icon was 180px and got clipped by the layout; 120px is
            # safe and leaves breathing room for the title below.
            icon_lbl = QLabel(hero)
            _icon_px = QIcon(":/credits/workslop.png").pixmap(QSize(120, 120))
            icon_lbl.setPixmap(_icon_px)
            icon_lbl.setAlignment(Qt.AlignHCenter)
            icon_lbl.setStyleSheet("background: transparent;")
            icon_lbl.setFixedSize(120, 120)
            vbox.addWidget(icon_lbl, 0, Qt.AlignHCenter)

            # Spacer between icon and title (user order 2026-10-19:
            # "ada spasi jarak lumayan antara icon dan tulisan").
            vbox.addSpacing(32)

            # 2. Title directly below the icon. White GLOWING (user order
            # 2026-10-19 ronde 10: "tulisan workslop desktop bercahaya putih").
            # 38px (down from 42px) to prevent crowding with the icon.
            title = QLabel("WorkSlop Desktop", hero)
            title.setAlignment(Qt.AlignHCenter)
            title.setStyleSheet(
                "background: transparent; color: #FFFFFF;"
                " font-size: 38px; font-weight: 700;")
            # White glow effect via drop shadow.
            from PySide6.QtWidgets import QGraphicsDropShadowEffect
            from PySide6.QtGui import QColor as _QC
            _glow = QGraphicsDropShadowEffect(title)
            _glow.setBlurRadius(20)
            _glow.setColor(_QC(255, 255, 255, 180))
            _glow.setOffset(0, 0)
            title.setGraphicsEffect(_glow)
            vbox.addWidget(title, 0, Qt.AlignHCenter)

            # 3. Developer credit + links below the title.
            self.credits_lbl = make_credits_label(
                hero, c0.text_secondary, c0.accent, align_center=True)
            self.credits_lbl.setStyleSheet(
                "background: transparent; font-size: 17px; font-weight: 500;")
            vbox.addWidget(self.credits_lbl, 0, Qt.AlignHCenter)

            # 4. GitHub credit boxes (user order 2026-10-18 ronde 8): three
            # boxes below the title — Adnan.120hz, awesomenull (GoldenNugget
            # dev), leminlimez (Nugget dev). Icons MUST come from the repo
            # (:/icon/github.svg), not generated. Clicking a box opens the
            # GitHub profile in the browser.
            from PySide6.QtWidgets import QGridLayout
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            from src.gui.ios.components import IOSCard
            from src.gui.theme import theme_icon
            gh_row = QHBoxLayout()
            gh_row.setSpacing(12)
            gh_row.setAlignment(Qt.AlignHCenter)
            gh_profiles = [
                ("Adnan.120hz", "https://github.com/adnan120hz"),
                ("awesomenull", "https://github.com/awesomenull"),
                ("leminlimez", "https://github.com/leminlimez"),
            ]
            for name, url in gh_profiles:
                # White GLOSSY boxes with BLACK text and VISIBLE SHINE (user
                # order 2026-10-19: "menu menu github udah good tapi belum ada
                # pencahayaan kilauan").
                # PURE display boxes (not clickable) EXCEPT Adnan.120hz which
                # opens the GitHub profile when clicked (user order 2026-10-19).
                # Custom QWidget instead of IOSCard for the white glossy style.
                box = QWidget(hero)
                _is_adnan = (name == "Adnan.120hz")
                if _is_adnan:
                    box.setCursor(Qt.PointingHandCursor)
                else:
                    box.setCursor(Qt.ArrowCursor)
                box.setStyleSheet("""
                    QWidget {
                        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #FFFFFF, stop:0.35 #FFFFFF, stop:0.5 #F5F5F5, stop:0.65 #E8E8E8, stop:1 #D0D0D0);
                        border: 1px solid #C8C8C8;
                        border-radius: 16px;
                    }
                    QWidget:hover {
                        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #FFFFFF, stop:0.3 #FFFFFF, stop:0.6 #F0F0F0, stop:1 #D8D8D8);
                        border: 1px solid #B0B0B0;
                    }
                """)
                box_layout = QVBoxLayout(box)
                box_layout.setContentsMargins(16, 12, 16, 12)
                box_layout.setSpacing(8)
                box_layout.setAlignment(Qt.AlignHCenter)
                icon = QLabel(box)
                icon.setPixmap(theme_icon(
                    ":/icon/github.svg", "#0A0A0A").pixmap(40, 40))
                icon.setAlignment(Qt.AlignHCenter)
                icon.setStyleSheet("background: transparent; border: none;")
                box_layout.addWidget(icon)
                lbl = QLabel(name, box)
                lbl.setAlignment(Qt.AlignHCenter)
                lbl.setStyleSheet(
                    "background: transparent; border: none; color: #0A0A0A;"
                    " font-size: 13px; font-weight: 600;")
                box_layout.addWidget(lbl)
                box.setFixedWidth(140)
                # Only Adnan.120hz is clickable; others are pure display.
                if _is_adnan:
                    box.mousePressEvent = (
                        lambda _e, u=url: QDesktopServices.openUrl(QUrl(u)))
                gh_row.addWidget(box)
            gh_container = QWidget(hero)
            gh_container.setLayout(gh_row)
            gh_container.setStyleSheet("background: transparent;")
            vbox.addWidget(gh_container, 0, Qt.AlignHCenter)

            host_layout.insertWidget(idx, hero, 0, Qt.AlignHCenter)

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