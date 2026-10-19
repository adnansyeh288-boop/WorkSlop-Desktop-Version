from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QCoreApplication

try:
    from shiboken6 import isValid as _shiboken_is_valid
except Exception:
    # Non-*/shiboken-less environments (some frozen builds) always report valid.
    _shiboken_is_valid = lambda _obj: True


def _still_running(worker) -> bool:
    """True when ``worker`` is a live QThread still executing.

    These workers all wire ``finished -> deleteLater``, which frees the C++
    object before the window ever drops its stored reference — so a saved
    worker can already be a dead shiboken wrapper. Probing that wrapper
    raises ``RuntimeError`` ("Internal C++ object already deleted"), which
    must never escape from a closeEvent.
    """
    if worker is None:
        return False
    try:
        if not _shiboken_is_valid(worker):
            return False
        return worker.isRunning()
    except RuntimeError:
        return False

from src.qt.mainwindow_ui import Ui_Nugget
import src.gui.pages as Pages

from src.controllers.translator import Translator
from src.controllers.preset_manager import PresetManager

from src.gui.pages.pages_list import Page

if TYPE_CHECKING:
    from src.devicemanagement.device_manager import DeviceManager

from src.gui.ios.theme_manager import ThemeManager
from src.gui.ios.home import IOSHomePage
from src.gui.ios.tweaks import IOSTweaksPage, IOSSectionPage
from src.gui.ios.posterboard import IOSPosterboardPage
from src.gui.ios.daemons import IOSDaemonsPage
from src.gui.ios.mobilegestalt import IOSMobileGestaltPage
from src.gui.ios.apply import IOSApplyPage
from src.gui.ios.settings import IOSSettingsPage
from src.gui.ios.statusbar import IOSStatusBarPage
from src.gui.ios.icon_themes import IOSIconThemesPage
from src.gui.ios.passcode_theme import IOSPasscodeThemePage
from src.tweaks.registry import Section

from src.gui.theme import ColorThemeManager, t, theme_icon, themed_stylesheet

from src.gui.main_window_mixins import (
    ApplyMixin,
    DeviceBarMixin,
    NavigationMixin,
    SettingsMixin,
)

# Classic (Nugget UI) chrome — device bar, sidebar, home toolbar — uses
# the WorkSlop icon set (ws-*.svg, Wave 11, user order 2026-10-03: the
# second UI is the Nugget shell with its icons renamed to the WorkSlop
# set); they are recolored on every theme change. The credit/social
# buttons keep their brand glyphs (a GitHub/Discord mark cannot be
# renamed to a WorkSlop line icon without lying about where they go).
_HIDDEN_THEMED_ICONS = {
    "phoneIconBtn": ":/icon/ws-device.svg",
    "refreshBtn": ":/icon/ws-refresh.svg",
    "homePageBtn": ":/icon/ws-device.svg",
    "gestaltPageBtn": ":/icon/ws-chip.svg",
    "euEnablerPageBtn": ":/icon/ws-flash.svg",
    "statusBarPageBtn": ":/icon/ws-signal.svg",
    "passcodePageBtn": ":/icon/ws-toolbox.svg",
    "springboardOptionsPageBtn": ":/icon/ws-apps.svg",
    "internalOptionsPageBtn": ":/icon/ws-sliders.svg",
    "liquidGlassPageBtn": ":/icon/ws-glass.svg",
    "daemonsPageBtn": ":/icon/ws-sliders.svg",
    "iconThemesPageBtn": ":/icon/ws-wallpaper.svg",
    "applyPageBtn": ":/icon/ws-backup.svg",
    "backupPageBtn": ":/icon/ws-backup.svg",
    "posterboardPageBtn": ":/icon/ws-poster.svg",
    "settingsPageBtn": ":/icon/ws-gear.svg",
    "mainDevBtn": ":/icon/github.svg",
    "discordBtn": ":/icon/discord.svg",
    "starOnGithubBtn": ":/icon/star.svg",
    "leminGithubBtn": ":/icon/github.svg",
    "leminTwitterBtn": ":/icon/twitter.svg",
    "leminKoFiBtn": ":/icon/currency-dollar.svg",
}

# (Removed 2026-10-18 with the 3-UI system: the Full Nugget interface no
# longer exists, so the original-Nugget icon map is dead code.)
_HIDDEN_BORDERED_BTNS = [
    "helpFromBtn", "posterRestoreBtn", "snoolieBtn", "disfordottieBtn",
    "mikasaBtn", "wind0ws11AeroBtn", "translatorsBtn", "libiBtn",
    "duyBtn", "jjtechBtn", "qtBtn",
]

class MainWindow(QtWidgets.QMainWindow, DeviceBarMixin, SettingsMixin,
                 NavigationMixin, ApplyMixin):
    def __init__(self, device_manager: "DeviceManager", translator: Translator):
        super(MainWindow, self).__init__()
        self.device_manager = device_manager
        self.translator = translator
        # WorkSlop app icon (flask). Falls back silently when running from a
        # source tree without the generated icon next to the repo root.
        try:
            import sys as _sys
            from pathlib import Path as _Path
            _candidates = [
                _Path(__file__).resolve().parents[2] / "workslop_icon.png",
            ]
            # PyInstaller bundle: data files land under sys._MEIPASS.
            _meipass = getattr(_sys, "_MEIPASS", None)
            if _meipass:
                _candidates.insert(0, _Path(_meipass) / "workslop_icon.png")
            for _icon_path in _candidates:
                if _icon_path.is_file():
                    self.setWindowIcon(QtGui.QIcon(str(_icon_path)))
                    break
        except Exception:
            pass
        self.settings = self.translator.settings
        self.ui = Ui_Nugget()
        self.ui.setupUi(self)
        # Snapshot the classic shell's as-generated stylesheets BEFORE any
        # WorkSlop theming touches them: Full Nugget mode restores these
        # verbatim (only the app name/icon are WorkSlop there).
        self._orig_classic_qss = {
            "sidebar": self.ui.sidebar.styleSheet(),
            "phoneNameLbl": self.ui.phoneNameLbl.styleSheet(),
        }
        for _btn_name in _HIDDEN_BORDERED_BTNS:
            _w = getattr(self.ui, _btn_name, None)
            if _w is not None:
                self._orig_classic_qss[_btn_name] = _w.styleSheet()
        # The generated UI pins setMaximumSize(1000, 600), which on Windows
        # disables the normal maximize button and can keep showFullScreen()
        # from covering the screen. Lift the clamp here (the generated file
        # itself stays untouched, per AGENTS.md) so maximize and F11
        # fullscreen both work.
        self.setMaximumSize(16777215, 16777215)
        self.noneText = self.tr("None")
        self.apply_in_progress = False
        self.refresh_in_progress = False
        self._cache_restore_in_progress = False
        self._cache_restore_thread = None
        self.threadpool = QtCore.QThreadPool()

        self.preset_manager = PresetManager()
        self._preset_autosave_pending = False

        self.loadSettings()
        self._load_last_preset()
        self._register_tweak_autosave()

        self.initial_load = True

        # hide every page
        self.ui.posterboardPageBtn.hide()
        self.ui.euEnablerPageBtn.hide()
        self.ui.statusBarPageBtn.hide()
        self.ui.springboardOptionsPageBtn.hide()
        self.ui.internalOptionsPageBtn.hide()
        self.ui.liquidGlassPageBtn.hide()
        self.ui.daemonsPageBtn.hide()
        self.ui.iconThemesPageBtn.hide()
        self.ui.passcodePageBtn.hide()
        self.ui.applyPageBtn.hide()
        self.ui.sidebarDiv1.hide()
        self.ui.sidebarDiv2.hide()

        # Backup entry for the classic sidebar (the two Nugget shells):
        # the generated UI has no Backup button (the main UI's rail has
        # one), so — like the other runtime chrome — it is created here
        # instead of editing the generated file. It sits right above
        # Apply, follows the menu order of the main UI (Backup before
        # Apply), and opens the same Backup & Apply page (iOS page 13).
        # Its icon follows the active flavor through the
        # _HIDDEN_THEMED_ICONS / _CLASSIC_ORIGINAL_ICONS maps above, and
        # the device-refresh flow shows/hides it together with Apply.
        backup_btn = QtWidgets.QToolButton(self.ui.sidebar)
        backup_btn.setObjectName("backupPageBtn")
        backup_btn.setSizePolicy(self.ui.applyPageBtn.sizePolicy())
        backup_btn.setCursor(QtCore.Qt.PointingHandCursor)
        backup_btn.setCheckable(True)
        backup_btn.setAutoExclusive(True)
        backup_btn.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        backup_btn.setProperty("cls", "sidebarBtn")
        backup_btn.setText(QCoreApplication.translate("Nugget", "Backup"))
        self.ui.verticalLayout.insertWidget(
            self.ui.verticalLayout.indexOf(self.ui.applyPageBtn),
            backup_btn)
        backup_btn.hide()
        self.ui.backupPageBtn = backup_btn

        # pre-load the pages
        self.pages = {
            Page.Home: Pages.Home(window=self, ui=self.ui),
            Page.Daemons: Pages.Daemons(ui=self.ui, window=self)
        }

        # theme manager stores the active UI mode (classic sidebar shell vs
        # full-screen iOS); apply_theme() below applies it
        self.theme_manager = ThemeManager(self)

        # Color theme manager (dark/light + accent)
        self._color_theme = ColorThemeManager.instance()
        self._color_theme.theme_changed.connect(self._on_color_theme_changed)

        # build the iOS-style pages stack
        # 0 = home, 1 = tweaks, 2 = posterboard, 3 = daemons, 4 = settings,
        # 5 = statusbar, 6 = apply, 7 = springboard, 8 = internal, 9 = liquidglass,
        # 10 = icon themes, 11 = passcode themes
        self.ios_pages = QtWidgets.QStackedWidget(self)
        self.ios_pages.setStyleSheet(t("page_bg"))
        self.ios_home = IOSHomePage(self)
        self.ios_tweaks = IOSTweaksPage(self)
        self.ios_posterboard = IOSPosterboardPage(self)
        self.ios_daemons = IOSDaemonsPage(self)
        self.ios_settings = IOSSettingsPage(self)
        self.ios_statusbar = IOSStatusBarPage(self)
        self.ios_apply = IOSApplyPage(self)
        self.ios_springboard = IOSSectionPage(self, Section.SPRINGBOARD)
        self.ios_internal = IOSSectionPage(self, Section.INTERNAL)
        self.ios_liquidglass = IOSSectionPage(self, Section.LIQUID_GLASS)
        self.ios_iconthemes = IOSIconThemesPage(self)
        self.ios_passthemes = IOSPasscodeThemePage(self)
        self.ios_gestalt = IOSMobileGestaltPage(self)
        from src.gui.ios.backup import IOSBackupPage
        from src.gui.ios.themes_hub import IOSThemesHubPage
        from src.gui.ios.appdata import IOSAppDataPage
        self.ios_backup = IOSBackupPage(self)
        self.ios_themes_hub = IOSThemesHubPage(self)
        self.ios_appdata = IOSAppDataPage(self)
        self.ios_pages.addWidget(self.ios_home)
        self.ios_pages.addWidget(self.ios_tweaks)
        self.ios_pages.addWidget(self.ios_posterboard)
        self.ios_pages.addWidget(self.ios_daemons)
        self.ios_pages.addWidget(self.ios_settings)
        self.ios_pages.addWidget(self.ios_statusbar)
        self.ios_pages.addWidget(self.ios_apply)
        self.ios_pages.addWidget(self.ios_springboard)
        self.ios_pages.addWidget(self.ios_internal)
        self.ios_pages.addWidget(self.ios_liquidglass)
        self.ios_pages.addWidget(self.ios_iconthemes)
        self.ios_pages.addWidget(self.ios_passthemes)
        self.ios_pages.addWidget(self.ios_gestalt)
        # WorkSlop menus: appended at the end so no existing page index shifts.
        # 13 = backup, 14 = themes hub, 15 = app data.
        self.ios_pages.addWidget(self.ios_backup)
        self.ios_pages.addWidget(self.ios_themes_hub)
        self.ios_pages.addWidget(self.ios_appdata)
        # Round 2 tutorials (user order 2026-10-18): 16 = recovery enter,
        # 17 = recovery exit, 18 = DFU guide, 19 = restore guide,
        # 20 = beta guide, 21 = WorkSlop app guide.
        from src.gui.tutorials import TutorialPage
        self.tut_rec_enter = TutorialPage(self, "rec_enter")
        self.tut_rec_exit = TutorialPage(self, "rec_exit")
        self.tut_dfu = TutorialPage(self, "dfu")
        self.tut_restore = TutorialPage(self, "restore")
        self.tut_beta = TutorialPage(self, "beta")
        self.tut_app = TutorialPage(self, "app")
        for _tp in (self.tut_rec_enter, self.tut_rec_exit, self.tut_dfu,
                    self.tut_restore, self.tut_beta, self.tut_app):
            self.ios_pages.addWidget(_tp)
            _tp.request_recovery.connect(self._on_tutorial_recovery_action)
        self._tut_pages = {
            "rec_enter": (self.tut_rec_enter, 16),
            "rec_exit": (self.tut_rec_exit, 17),
            "dfu_guide": (self.tut_dfu, 18),
            "restore_guide": (self.tut_restore, 19),
            "beta_guide": (self.tut_beta, 20),
            "app_guide": (self.tut_app, 21),
        }

        # Shared reusable header: one instance for every iOS subpage,
        # reconfigured on page change (title / back / right action).
        from src.gui.ios.components import IOSNavBar
        self.ios_nav = IOSNavBar("", on_back=self._go_back)
        self._ios_page_titles = {
            0: "WorkSlop Desktop",
            1: QtCore.QCoreApplication.translate("Nugget", "Tweaks"),
            2: "PosterBoard",
            3: QtCore.QCoreApplication.translate("Nugget", "Daemons"),
            4: QtCore.QCoreApplication.translate("Nugget", "Settings"),
            5: QCoreApplication.translate("Nugget", "Status Bar"),
            6: QCoreApplication.translate("Nugget", "Apply"),
            7: QtCore.QCoreApplication.translate("Nugget", "SpringBoard"),
            8: QtCore.QCoreApplication.translate("Nugget", "Internal"),
            9: QtCore.QCoreApplication.translate("Nugget", "Liquid Glass"),
            10: QtCore.QCoreApplication.translate("Nugget", "Icon Themes"),
            11: QCoreApplication.translate("Nugget", "Passcode Themes"),
            12: QCoreApplication.translate("Nugget", "MobileGestalt"),
            13: QCoreApplication.translate("Nugget", "Backup"),
            14: QCoreApplication.translate("Nugget", "Themes"),
            15: QCoreApplication.translate("Nugget", "App Data"),
        }
        self._nav_right_actions = {
            2: ("+ Add Tendies", self.ios_posterboard.show_add_tendies_dialog),
            10: (QtCore.QCoreApplication.translate("Nugget", "+ Add Icon"),
                 self.ios_iconthemes.show_add_icon_dialog),
            11: (QCoreApplication.translate("Nugget", "+ Theme"),
                 self.ios_passthemes.choose_theme_dialog),
        }
        self.ios_pages.currentChanged.connect(self._update_shared_nav)

        ios_root = QtWidgets.QWidget(self)
        ios_root_layout = QtWidgets.QVBoxLayout(ios_root)
        ios_root_layout.setContentsMargins(0, 0, 0, 0)
        ios_root_layout.setSpacing(0)
        ios_root_layout.addWidget(self.ios_nav)
        ios_root_layout.addWidget(self.ios_pages)

        # Unified dual shell (Wave 11, user order 2026-10-03). The content
        # stack holds the classic Nugget Home (0), the iOS-style page root
        # (1), and the classic Daemons page (2). Around it, two chromes:
        # the WorkSlop v4 Sky shell (sidebar rail + shared nav header) is
        # the main UI (IOS mode), and the classic Nugget shell (generated
        # sidebar + classic pages, iOS pages hosted as actions) is the
        # second UI (CLASSIC mode). apply_theme() switches between them.
        # The generated Ui_Nugget object still exists for the device-bar
        # widgets that background flows (device refresh, picker signals)
        # reference.
        self.ui.centralwidget.setParent(None)
        self.ui.homePage.setParent(None)
        self.ui.sidebar.setParent(None)
        self.ui.daemonsPage.setParent(None)
        # the top device bar (phone icon + picker) serves both shells
        self.ui.deviceBar.setParent(None)
        self.content_stack = QtWidgets.QStackedWidget(self)
        self.content_stack.addWidget(self.ui.homePage)     # 0 = classic home
        self.content_stack.addWidget(ios_root)             # 1 = iOS pages
        self.content_stack.addWidget(self.ui.daemonsPage)  # 2 = classic daemons
        self.content_stack.setStyleSheet("background: transparent;")
        # (Removed 2026-10-18 with the 3-UI system: the Full Nugget
        # interface no longer exists, so there is no nugget page stack.)
        shell = QtWidgets.QWidget(self)
        shell.setProperty("cls", "central")
        # Wave 11 shell: animated blue Apple-logo background behind the
        # content. White cards/panels sit above it, like the v4 shell.
        from src.gui.ios.sky_bg import SkyBackground
        self._sky_bg = SkyBackground(shell)
        self._sky_bg.start()  # v4: drifting logos animate from window start
        self._shell = shell
        content = QtWidgets.QWidget(shell)
        content.setStyleSheet("background: transparent; border: none;")
        shell_layout = QtWidgets.QStackedLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.setStackingMode(QtWidgets.QStackedLayout.StackAll)
        shell_layout.addWidget(self._sky_bg)
        shell_layout.addWidget(content)
        self._sky_bg.lower()
        self.shell_layout = QtWidgets.QVBoxLayout(content)
        self.shell_layout.setContentsMargins(0, 0, 0, 0)
        self.shell_layout.setSpacing(0)
        self.shell_layout.addWidget(self.ui.deviceBar)
        # Round 2 (user order 2026-10-18): menus move to the TOP. The top
        # nav bar carries every tweak family as its own pill (no "All
        # Tweaks" grouping); a slim side rail holds the overflow menus
        # (Backup/Apply/Settings + recovery & tutorial menus).
        from src.gui.topnav import TopNavBar
        from src.gui.siderail import SideRail
        self.topnav = TopNavBar(self)
        self.topnav.menu_selected.connect(self._on_topnav_menu)
        self.shell_layout.addWidget(self.topnav)
        self.body_row = QtWidgets.QHBoxLayout()
        self.body_row.setContentsMargins(12, 10, 12, 12)
        self.body_row.setSpacing(12)
        # Legacy sidebars are retired from the layout (round 2): their
        # button objects stay alive as the visibility source of truth for
        # the device-refresh flow, but they are no longer shown.
        self.ui.sidebar.hide()
        # WorkSlop v4 sidebar rail: retired as well (round 2 top-nav).
        from src.gui.ios.sidebar import WorkSlopSidebar
        self.workslop_sidebar = WorkSlopSidebar(self)
        self.workslop_sidebar.menu_selected.connect(self._on_workslop_menu)
        self.workslop_sidebar.hide()
        self.body_row.addWidget(self.content_stack, 1)
        self.siderail = SideRail(self)
        self.siderail.menu_selected.connect(self._on_rail_menu)
        self.body_row.addWidget(self.siderail)
        self._style_device_pill()
        self.shell_layout.addLayout(self.body_row)
        self.setCentralWidget(shell)

        # WorkSlop Desktop branding (the generated .ui still says GoldenNugget;
        # overriding here keeps mainwindow_ui.py untouched).
        self.setWindowTitle("WorkSlop Desktop")

        # Animated blue Apple-logo background is instantiated above as
        # the shell underlay (self._sky_bg).
        self._backdrop = self._sky_bg

        self.apply_theme(self.theme_manager.current_theme)

        # Back navigation: ESC key and mouse back button go to the home page
        QtWidgets.QApplication.instance().installEventFilter(self)
        # F11/ESC fullscreen via real window shortcuts (the app-wide event
        # filter alone does not reliably deliver F11 on Windows).
        self._install_fullscreen_shortcuts()

        # Update the app version/build number label
        self.updateAppVersionLabel()
        self.pages[Page.Home].load()
        
        ## DEVICE BAR
        self.refresh_devices()

        self.ui.refreshBtn.clicked.connect(self.refresh_devices)
        self.ui.devicePicker.currentIndexChanged.connect(self.change_selected_device)

        ## SIDE BAR ACTIONS
        self.ui.homePageBtn.clicked.connect(self.on_homePageBtn_clicked)
        self.ui.statusBarPageBtn.clicked.connect(self.on_statusBarPageBtn_clicked)
        self.ui.springboardOptionsPageBtn.clicked.connect(self.on_springboardOptionsPageBtn_clicked)
        self.ui.internalOptionsPageBtn.clicked.connect(self.on_internalOptionsPageBtn_clicked)
        self.ui.liquidGlassPageBtn.clicked.connect(self.on_liquidGlassPageBtn_clicked)
        self.ui.daemonsPageBtn.clicked.connect(self.on_daemonsPageBtn_clicked)
        self.ui.gestaltPageBtn.clicked.connect(self.on_mobileGestaltPageBtn_clicked)
        self.ui.iconThemesPageBtn.clicked.connect(self.on_iconThemesPageBtn_clicked)
        self.ui.posterboardPageBtn.clicked.connect(self.on_posterboardPageBtn_clicked)
        self.ui.applyPageBtn.clicked.connect(self.on_applyPageBtn_clicked)
        self.ui.backupPageBtn.clicked.connect(self.on_backupPageBtn_clicked)
        self.ui.settingsPageBtn.clicked.connect(self.on_settingsPageBtn_clicked)

        # Apply the initial themed global stylesheet
        self._apply_global_stylesheet()

    def run_first_launch_prompts(self):
        """Present the first-launch dialogs AFTER the window is on screen.

        Running them inside __init__ (before show()) opens them over an
        unmapped parent, which on several platforms renders them transparent
        and stuttering. Called from main_app right after widget.show().
        """
        # First launch: the 3-UI picker was removed (user order 2026-10-18).
        # There is exactly one interface now; nothing to choose.
        if not self.theme_manager.settings.contains("ui/theme"):
            self.theme_manager.save_theme(ThemeManager.CLASSIC)

        # First launch: remind the user to back up the device before tweaking
        # (keeps asking until they confirm a backup was made)
        if not self.settings.value("backup_prompt_done", False, type=bool):
            if self.prompt_first_launch_backup():
                self.settings.setValue("backup_prompt_done", True)
                self._sync_settings()

    def on_footer_check_update_clicked(self):
        """Footer "Check Update": run the update checker off the GUI thread
        via the shared UpdateCheckRunner and report on the GUI thread.

        The runner owns the QThread lifecycle (fresh thread per check,
        references dropped on finished, result delivered by queued signal);
        calling this repeatedly — including while a check is running or
        after one finished — cannot touch a deleted C++ QThread again.
        """
        runner = getattr(self, "_footer_update_runner", None)
        if runner is None:
            from src.gui.update_check import UpdateCheckRunner
            runner = UpdateCheckRunner(self)
            runner.result_ready.connect(self._report_footer_update_result)
            self._footer_update_runner = runner
        runner.start()

    def _report_footer_update_result(self, result):
        if result is not None and result.outcome == "update_available":
            from src.gui.dialogs import UpdateAppDialog
            UpdateAppDialog(result, self).exec()
        elif result is not None and result.outcome == "up_to_date":
            QtWidgets.QMessageBox.information(
                self, "Check for Updates", "You are up to date.")
        else:
            QtWidgets.QMessageBox.warning(
                self, "Check for Updates",
                "Couldn't check for updates. Please try again later.")

    def eventFilter(self, obj, event):
        # Delegate explicitly: with QMainWindow first in the MRO, Python
        # attribute lookup would otherwise resolve QObject.eventFilter and
        # the NavigationMixin handler (ESC/back/F11) would never run.
        return NavigationMixin.eventFilter(self, obj, event)

    # ---- Color theme reactivity ------------------------------------------

    def _apply_global_stylesheet(self):
        """Re-apply the global stylesheet using the current color theme."""
        self.setStyleSheet(t("global"))
        # Also update the QPalette so native widgets pick up the colors
        QtWidgets.QApplication.instance().setPalette(self._color_theme.build_palette())
        # Re-style the ios_pages stack transparently so the animated shell
        # background shows around the white page surfaces.
        self.ios_pages.setStyleSheet("background: transparent;")
        if hasattr(self, "_shell"):
            self._shell.setStyleSheet(
                "background: transparent; border: none;")
        # Re-style the classic chrome (sidebar icons, device bar, home toolbar)
        self._retheme_classic()

    def _style_device_pill(self):
        """Restyle the top device bar as a clean status pill.

        The picker group moves to the right; the old title text becomes a
        plain expanding spacer.
        """
        # The picker group moves to the right and the old title text is
        # blanked first (every flavor shares this layout fixup).
        bar = self.ui.deviceBar
        layout = self.ui.horizontalLayout_4
        # Tidy the device bar (user order 2026-10-18 ronde 8): even spacing
        # and margins so the device pill + refresh button sit neatly.
        layout.setSpacing(8)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
        layout.insertWidget(0, self.ui.titleBar)
        self.ui.titleBar.setText("")
        self.ui.titleBar.setStyleSheet(
            "background-color: transparent; border: none;")
        # Search box in device bar (user order 2026-10-19): top-right corner,
        # above the Home nav pill, with spacing. Cobalt glass style.
        # Guard against double-add on re-theme (method can run multiple times).
        if not hasattr(self, "_device_search_box") or self._device_search_box is None:
            from PySide6.QtWidgets import QLineEdit
            from PySide6.QtGui import QAction as _QAction
            from PySide6.QtGui import QIcon as _QIcon
            _search_box = QLineEdit(bar)
            _search_box.setPlaceholderText("Search tweaks...")
            _search_box.setFixedHeight(36)
            _search_box.setFixedWidth(240)
            _search_box.setStyleSheet("""
                QLineEdit {
                    background-color: rgba(35, 64, 150, 0.55);
                    border-radius: 18px;
                    border: 1px solid rgba(150, 180, 255, 0.4);
                    padding-left: 36px;
                    padding-right: 12px;
                    color: #FFFFFF;
                    font-size: 13px;
                }
            """)
            _search_icon = _QAction(_search_box)
            _search_icon.setIcon(_QIcon(":/icon/ws-search.svg"))
            _search_box.addAction(_search_icon, QLineEdit.ActionPosition.LeadingPosition)
            _search_box.returnPressed.connect(
                lambda: self._on_search_tweak_from_home(_search_box.text()))
            layout.addWidget(_search_box)
            self._device_search_box = _search_box

        c = self._color_theme.colors
        bar.setStyleSheet("background-color: transparent;")
        pill = self.ui.horizontalWidget_2
        pill.setStyleSheet(f"""
            QWidget#horizontalWidget_2 {{
                background-color: rgba(35, 64, 150, 0.55);
                border: 1px solid rgba(150, 180, 255, 0.4);
                border-radius: 19px;
            }}
        """)
        self.ui.devicePicker.setStyleSheet(f"""
            QComboBox {{
                background-color: transparent;
                border: none;
                color: {c.text_primary};
                font-size: 13px;
                font-weight: 500;
                min-height: 36px;
                padding-left: 10px;
            }}
            QComboBox::drop-down {{ border: none; width: 22px; }}
            QComboBox::down-arrow {{
                image: url(:/icon/caret-down-fill.svg);
                width: 12px; height: 12px; margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c.bg_tertiary};
                border: 1px solid {c.border};
                border-radius: 20px;
                color: {c.text_primary};
                selection-background-color: {c.accent};
            }}
        """)
        self.ui.refreshBtn.setStyleSheet(f"""
            QToolButton {{
                background-color: {c.accent};
                border: none;
                border-radius: 17px;
                color: #FFFFFF;
            }}
            QToolButton:hover {{ background-color: {c.accent_hover}; }}
            QToolButton:pressed {{ background-color: {c.accent_pressed}; }}
        """)
        self.ui.phoneIconBtn.setStyleSheet(
            "background-color: transparent; border: none;")

    def _retheme_classic(self):
        """Re-color the classic shell: chrome icons, device picker, version
        link and the hardcoded-dark credit buttons.
        """
        try:
            self._shell.layout().itemAt(1).widget().setStyleSheet(
                "background: transparent;")
        except Exception:
            pass
        for _page_name in ("homePage", "daemonsPage"):
            _page = getattr(self.ui, _page_name, None)
            if _page is not None:
                _page.setStyleSheet("")
        c = self._color_theme.colors

        # Recolor white SVG chrome icons to the current text color.
        # The resource is stored on each button so _sync_sidebar_selection
        # can re-tint to white when the button is checked (blue bg).
        for obj_name, res in _HIDDEN_THEMED_ICONS.items():
            widget = getattr(self.ui, obj_name, None)
            if widget is not None:
                widget.setIcon(theme_icon(res, c.text_primary))
                widget.setProperty("_ws_icon_res", res)
        # The refresh button sits on solid blue — its icon stays white.
        if self.ui.refreshBtn is not None:
            self.ui.refreshBtn.setIcon(
                theme_icon(":/icon/ws-refresh.svg", "#FFFFFF"))
            self.ui.refreshBtn.setProperty("_ws_icon_res", None)

        # Device picker keeps its Designer stylesheet untouched (classic look).

        # Version link inherits white from the .ui — restyle to text_secondary
        self.ui.phoneNameLbl.setStyleSheet(f"color: {c.text_primary};")
        self.ui.phoneVersionLbl.setText(
            f'<a style="text-decoration:none; color:{c.text_secondary}" href="#">Version</a>')

        # Always-visible shell chrome: the sidebar and device bar are shown on
        # every page/tab, so their text color must be themed explicitly
        # (otherwise it falls back to whatever the .ui bundled).
        #
        # WorkSlop Blue Desk (single-UI rebuild 2026-10-18): white sidebar
        # card with fluid 16px corners, blue section kicker, nav buttons
        # with 12px corners — light-blue hover, solid blue + white text
        # when checked. No sharp corners anywhere.
        chrome = f"""
            #sidebar {{
                background-color: #FFFFFF;
                border: 1px solid {c.card_border};
                border-radius: 16px;
            }}
            #sidebar QToolButton {{
                color: {c.text_primary};
                background-color: transparent;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
                text-align: left;
                padding: 10px 12px;
                icon-size: 20px;
            }}
            #sidebar QToolButton:hover {{
                color: {c.text_primary};
                background-color: {c.surface_hover};
            }}
            #sidebar QToolButton:checked {{
                color: #FFFFFF;
                background-color: {c.accent};
                font-weight: 700;
            }}
            #sidebar QToolButton:pressed {{
                background-color: {c.accent_pressed};
                color: #FFFFFF;
            }}
            #sidebar QToolButton:disabled {{
                color: {c.text_disabled};
                background-color: transparent;
            }}
            #sidebar QLabel {{ color: {c.text_primary}; background: transparent; }}
            #sidebar QLabel[cls=dim] {{ color: {c.text_secondary}; }}
        """
        self.ui.sidebar.setStyleSheet(chrome)

        # Credit buttons hardcode #3b3b3b borders in the generated .ui
        bordered_style = themed_stylesheet("classic_bordered_btn")
        for obj_name in _HIDDEN_BORDERED_BTNS:
            widget = getattr(self.ui, obj_name, None)
            if widget is not None:
                widget.setStyleSheet(bordered_style)

    # (Removed 2026-10-18 with the 3-UI system: _apply_full_nugget_chrome
    # deleted — the Full Nugget interface no longer exists.)

    def _on_color_theme_changed(self):
        """Called when the color theme (dark/light or accent) changes."""
        self._apply_global_stylesheet()
        # Repaint the sky backdrop against the current palette (v4
        # SkyBackground paints from the sky tints; a repaint is all it
        # needs — the Wave 10 set_colors API is gone with its backdrop).
        try:
            self._backdrop.update()
        except Exception:
            pass
        # Keep the device pill themed too.
        try:
            self._style_device_pill()
        except Exception:
            pass
        # Force re-render of all iOS page stylesheets by re-applying them
        for i in range(self.ios_pages.count()):
            page = self.ios_pages.widget(i)
            if page and hasattr(page, '_retheme'):
                page._retheme()

    def closeEvent(self, event):
        """Guard window close so device threads never get destroyed mid-run.

        Destroying a QThread object while its native thread is still running
        is what produces the "QThread: Destroyed while thread '' is still
        running" crash — and for a restore/apply it can cut the device
        operation short right in the middle of a Manifest.db write, leaving
        the backup corrupted (the reported MBErrorDomain/205 fallout).
        """
        terminating = []
        if getattr(self, "apply_in_progress", False):
            terminating.append("apply/reset")
        if getattr(self, "_cache_restore_in_progress", False):
            terminating.append("data restore")
        pt_worker = getattr(getattr(self, "ios_passthemes", None), "_worker", None)
        if _still_running(pt_worker):
            terminating.append("passcode theme write")
        pairing_worker = getattr(
            getattr(self, "ios_settings", None), "_reset_pairing_thread", None)
        if _still_running(pairing_worker):
            terminating.append("pairing reset")
        if terminating:
            reply = QtWidgets.QMessageBox.question(
                self,
                QCoreApplication.tr("Background device operation"),
                QCoreApplication.translate(
                    "Nugget",
                    "A device %1 is running. Closing now can interrupt it "
                    "mid-write and leave the protective backup corrupted.\n\n"
                    "Close anyway?").replace(
                        "%1", " and ".join(terminating)),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            # User insisted: let the operation wind down on its own so the
            # thread is not destroyed mid-run. Device loops all have bounded
            # timeouts, so this terminates.
            for worker in (
                getattr(self, "worker_thread", None),
                getattr(self, "_cache_restore_thread", None),
                pairing_worker,
                pt_worker,
            ):
                if _still_running(worker):
                    try:
                        worker.wait()
                    except RuntimeError:
                        pass
        scan_worker = getattr(self, "refresh_worker_thread", None)
        if _still_running(scan_worker):
            try:
                scan_worker.wait(8000)
            except RuntimeError:
                pass
        super().closeEvent(event)
