import os

from PySide6.QtCore import Qt, QCoreApplication, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QToolButton, QFileDialog, QDialog, QDialogButtonBox,
    QLineEdit, QMessageBox,
)

from src.gui.ios.components import IOSCard
from src.gui.theme import ColorThemeManager, theme_icon, t
from src.gui.dialogs.icon_pack_downloader import IconPackDownloaderDialog
from src.gui.dialogs.app_list_dialog import AppListExportDialog
from src.tweaks.tweaks import tweaks, TweakID
from src.tweaks.icon_themes.icon_theme import IconTheme
from src.controllers.files_handler import get_bundle_files


# ---------------------------------------------------------------------------
# iOS 18 Icon Pack (built-in, user order 2026-10-18 ronde 8)
# ---------------------------------------------------------------------------
# The pack is bundled in the repo again (files/ios18_icons/{Light,Dark,
# Rounded-Light,Rounded-Dark}/) — NOT import-only. Artwork: "iOS 18 App
# Icons by catwithabaloon" (https://github.com/catwithabaloon/iOS-18-icon-pack).
# Catalog: (display name, bundle id, asset slug). 51 apps, Light artwork for
# all; Dark has 50 (the pack ships no Dark Shortcuts).
IOS18_CATALOG = [
    ("Shortcuts", "com.apple.shortcuts", "shortcuts"),
    ("App Store", "com.apple.AppStore", "app-store"),
    ("Settings", "com.apple.Preferences", "settings"),
    ("Numbers", "com.apple.Numbers", "numbers"),
    ("Pages", "com.apple.Pages", "pages"),
    ("Keynote", "com.apple.Keynote", "keynote"),
    ("Books", "com.apple.iBooks", "books"),
    ("Calculator", "com.apple.calculator", "calculator"),
    ("Calendar", "com.apple.mobilecal", "calendar"),
    ("Camera", "com.apple.camera", "camera"),
    ("Music Classical", "com.apple.music.classical", "music-classical"),
    ("Clock", "com.apple.mobiletimer", "clock"),
    ("Compass", "com.apple.compass", "compass"),
    ("Contacts", "com.apple.AddressBook", "contacts"),
    ("FaceTime", "com.apple.facetime", "facetime"),
    ("Files", "com.apple.DocumentsApp", "files"),
    ("Clips", "com.apple.clips", "clips"),
    ("Find My", "com.apple.findmy", "find-my"),
    ("Fitness", "com.apple.Fitness", "fitness"),
    ("GarageBand", "com.apple.mobilegarageband", "garageband"),
    ("Health", "com.apple.Health", "health"),
    ("Home", "com.apple.Home", "home"),
    ("Magnifier", "com.apple.Magnifier", "magnifier"),
    ("Mail", "com.apple.mobilemail", "mail"),
    ("Maps", "com.apple.Maps", "maps"),
    ("Measure", "com.apple.measure", "measure"),
    ("Music", "com.apple.Music", "music"),
    ("News", "com.apple.news", "news"),
    ("Notes", "com.apple.mobilenotes", "notes"),
    ("Passwords", "com.apple.Passwords", "passwords"),
    ("Phone", "com.apple.mobilephone", "phone"),
    ("Photos", "com.apple.mobileslideshow", "photos"),
    ("Podcasts", "com.apple.podcasts", "podcasts"),
    ("Reminders", "com.apple.reminders", "reminders"),
    ("Apple TV Remote", "com.apple.TVRemote", "apple-tv-remote"),
    ("Safari", "com.apple.mobilesafari", "safari"),
    ("Stocks", "com.apple.stocks", "stocks"),
    ("Apple Store", "com.apple.store.Jolly", "apple-store"),
    ("Swift Playgrounds", "com.apple.Playgrounds", "swift-playgrounds"),
    ("TestFlight", "com.apple.TestFlight", "testflight"),
    ("Tips", "com.apple.tips", "tips"),
    ("Translate", "com.apple.Translate", "translate"),
    ("Voice Memos", "com.apple.VoiceMemos", "voice-memos"),
    ("Wallet", "com.apple.Passbook", "wallet"),
    ("Watch", "com.apple.Bridge", "watch"),
    ("Weather", "com.apple.weather", "weather"),
    ("Messages", "com.apple.MobileSMS", "messages"),
    ("iMovie", "com.apple.iMovie", "imovie"),
    ("Apple Sports", "com.apple.sports", "apple-sports"),
    ("TV", "com.apple.tv", "tv"),
    ("Shazam", "com.shazam.Shazam", "shazam"),
]

# Variant: (display name, folder name)
IOS18_VARIANTS = [
    ("Light", "Light"),
    ("Dark", "Dark"),
    ("Rounded Light", "Rounded-Light"),
    ("Rounded Dark", "Rounded-Dark"),
]


class IOSIconThemesPage(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.setObjectName("iosContainer")

        self._c = ColorThemeManager.instance().colors

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._scroll = scroll
        content = QWidget()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(16, 16, 16, 32)
        self.content_layout.setSpacing(8)

        hint = QLabel(QCoreApplication.translate(
            "Nugget",
            "Theme a home screen icon with a custom image and label without "
            "jailbreaking. Tapping the icon still opens the real app. "
            "WebClips launch \"Add to Home Screen\" shortcuts, so existing "
            "icon shortcuts stay untouched — remove disabled apps before "
            "themes to avoid collisions. Applying icon themes restarts the "
            "iPhone so the new icons appear."))
        hint.setWordWrap(True)
        self._hint = hint
        self.content_layout.addWidget(hint)

        reset_btn = QPushButton(QCoreApplication.translate(
            "Nugget", "Reset Icon Themes"))
        reset_btn.setObjectName("resetIconThemes")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_themes)
        self._reset_btn = reset_btn
        self.content_layout.addWidget(reset_btn)

        download_btn = QPushButton(QCoreApplication.translate(
            "Nugget", "Download Icon Packs"))
        download_btn.setObjectName("downloadIconPacks")
        download_btn.setCursor(Qt.PointingHandCursor)
        download_btn.clicked.connect(self.show_download_packs)
        self._download_btn = download_btn
        self.content_layout.addWidget(download_btn)

        apps_btn = QPushButton(QCoreApplication.translate(
            "Nugget", "Apps on iPhone"))
        apps_btn.setObjectName("appsOnIphone")
        apps_btn.setCursor(Qt.PointingHandCursor)
        apps_btn.clicked.connect(self.show_app_list_export)
        self._apps_btn = apps_btn
        self.content_layout.addWidget(apps_btn)

        # -- iOS 18 Icon Pack (user order 2026-10-18 ronde 8): BUILT-IN again,
        # not import-only. Each variant is an App-Library-style box with an
        # icon grid inside, sized to fit, and its own Apply button below —
        # per-box Apply, not one global Apply.
        pack_title = QLabel(QCoreApplication.translate(
            "Nugget", "iOS 18 Icon Pack"))
        pack_title.setObjectName("packTitle")
        pack_title.setWordWrap(True)
        self._pack_title = pack_title
        self.content_layout.addWidget(pack_title)
        pack_hint = QLabel(QCoreApplication.translate(
            "Nugget",
            "Built-in · iOS 18 App Icons by catwithabaloon. Pick a variant "
            "below and tap its Apply button — the icons are added as icon "
            "themes, ready for the Apply menu."))
        pack_hint.setObjectName("packHint")
        pack_hint.setWordWrap(True)
        self._pack_hint = pack_hint
        self.content_layout.addWidget(pack_hint)
        # Variant boxes in a 2-column grid.
        from PySide6.QtWidgets import QGridLayout
        pack_grid = QGridLayout()
        pack_grid.setSpacing(12)
        pack_grid.setContentsMargins(0, 4, 0, 4)
        self._pack_grid = pack_grid
        self.content_layout.addLayout(pack_grid)
        # NOTE: _build_pack_boxes() is called by _retheme() below — do NOT
        # call it here too (double-build leaves stale boxes via deleteLater).

        self.themes_placeholder = QLabel(QCoreApplication.translate(
            "Nugget", "No icon themes yet. Tap + Add Icon or download a pack."))
        self.themes_placeholder.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.themes_placeholder)

        self._themes_box = QVBoxLayout()
        self._themes_box.setSpacing(8)
        self.content_layout.addLayout(self._themes_box)

        self.content_layout.addStretch()

        self._retheme()
        self.refresh_themes()

    def _reset_themes(self):
        reply = QMessageBox.question(
            self.window,
            QCoreApplication.translate("Nugget", "Reset Icon Themes"),
            QCoreApplication.translate(
                "Nugget",
                "Remove all icon themes from WorkSlop Desktop? The themed "
                "home-screen icons already on the device are not touched."),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.StandardButton.Cancel)
        if reply != QMessageBox.StandardButton.Yes:
            return
        tweak = tweaks[TweakID.IconThemes]
        tweak.themes = []
        tweak.set_enabled(False)
        self.refresh_themes()

    def _build_pack_boxes(self):
        """Build the 4 built-in iOS 18 pack variant boxes (App Library style).

        Each box is an IOSCard sized to fit its icon grid, with the variant
        name, icon count, a preview grid of icons, and its own Apply button
        below the grid — per-box Apply, not one global Apply.
        """
        from PySide6.QtWidgets import QGridLayout
        c = self._c
        # Clear existing boxes.
        while self._pack_grid.count():
            item = self._pack_grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        for col, (variant_name, folder) in enumerate(IOS18_VARIANTS):
            box = IOSCard()
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(14, 14, 14, 14)
            box_layout.setSpacing(8)

            title = QLabel(variant_name)
            title.setStyleSheet(
                f"color: {c.text_primary}; font-size: 15px; font-weight: 700; "
                f"background: transparent;")
            box_layout.addWidget(title)

            # Count how many icons actually exist for this variant.
            available = []
            for _display, _bundle, slug in IOS18_CATALOG:
                path = get_bundle_files(f"files/ios18_icons/{folder}/{slug}.png")
                if path and os.path.isfile(path):
                    available.append(path)
            count = QLabel(f"{len(available)} icons")
            count.setStyleSheet(
                f"color: {c.text_secondary}; font-size: 12px; "
                f"background: transparent;")
            box_layout.addWidget(count)

            # Preview grid: 4 columns x 2 rows of icons (App Library folder
            # style). Box sizes itself to fit the grid.
            grid = QGridLayout()
            grid.setSpacing(6)
            grid.setContentsMargins(0, 4, 0, 4)
            for i, path in enumerate(available[:8]):
                lbl = QLabel()
                lbl.setFixedSize(52, 52)
                lbl.setStyleSheet("background: transparent;")
                pm = QPixmap(path)
                if not pm.isNull():
                    lbl.setPixmap(pm.scaled(
                        48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                grid.addWidget(lbl, i // 4, i % 4)
            box_layout.addLayout(grid)

            apply_btn = QPushButton(QCoreApplication.translate(
                "Nugget", f"Apply {variant_name}"))
            apply_btn.setCursor(Qt.PointingHandCursor)
            apply_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c.accent};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 18px;
                    font-size: 14px;
                    font-weight: 700;
                    padding: 10px;
                }}
                QPushButton:hover {{ background-color: {c.accent_hover}; }}
                QPushButton:pressed {{ background-color: {c.accent_pressed}; }}
            """)
            apply_btn.clicked.connect(
                lambda _=False, v=variant_name, f=folder:
                self._apply_pack_variant(v, f))
            box_layout.addWidget(apply_btn)

            self._pack_grid.addWidget(box, col // 2, col % 2)

    def _apply_pack_variant(self, variant_name: str, folder: str):
        """Add one built-in iOS 18 pack variant as icon themes."""
        tweak = tweaks[TweakID.IconThemes]
        tr = lambda s: QCoreApplication.translate("Nugget", s)
        added = 0
        existing = {t.bundle_id for t in tweak.themes}
        for display_name, bundle_id, slug in IOS18_CATALOG:
            if bundle_id in existing:
                continue
            path = get_bundle_files(f"files/ios18_icons/{folder}/{slug}.png")
            if not path or not os.path.isfile(path):
                continue
            tweak.themes.append(IconTheme(
                bundle_id=bundle_id,
                display_name=display_name,
                icon_path=path))
            existing.add(bundle_id)
            added += 1
        if added:
            tweak.set_enabled(True)
            self.refresh_themes()
            QMessageBox.information(
                self.window, tr(f"iOS 18 Pack — {variant_name}"),
                tr("Added {0} icons ({1}). Open the Apply menu to apply "
                   "them to your iPhone.").format(added, variant_name))
        else:
            QMessageBox.warning(
                self.window, tr(f"iOS 18 Pack — {variant_name}"),
                tr("All {0} icons are already added.").format(variant_name))

    def _retheme(self):
        c = ColorThemeManager.instance().colors
        self._c = c
        # Round 6: no panels — content floats on the Apple-logo watermark.
        self._scroll.setStyleSheet(t("scroll_area"))
        self._scroll.viewport().setStyleSheet("background: transparent;")
        self._scroll.widget().setStyleSheet("background: transparent; border: none;")
        self.setStyleSheet(
            "background: transparent; border: none;"
            " IOSIconThemesPage QWidget { background: transparent; }")
        self._hint.setStyleSheet(f"color: {c.text_secondary}; font-size: 13px;")
        self._download_btn.setStyleSheet(f"""
            QPushButton#downloadIconPacks {{
                background-color: {c.bg_secondary};
                border: 1px solid {c.border};
                border-radius: 20px;
                color: {c.accent};
                font-size: 14px;
                font-weight: 600;
                padding: 12px;
            }}
            QPushButton#downloadIconPacks:hover {{ background-color: {c.surface_hover}; }}
        """)
        self._apps_btn.setStyleSheet(f"""
            QPushButton#appsOnIphone {{
                background-color: {c.bg_secondary};
                border: 1px solid {c.border};
                border-radius: 20px;
                color: {c.accent};
                font-size: 14px;
                font-weight: 600;
                padding: 12px;
            }}
            QPushButton#appsOnIphone:hover {{ background-color: {c.surface_hover}; }}
        """)
        self.themes_placeholder.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 15px; padding: 24px 0;")
        self._pack_title.setStyleSheet(
            f"color: {c.text_primary}; font-size: 16px; font-weight: 700; "
            f"padding: 14px 0 0 0; background: transparent;")
        self._pack_hint.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 13px; background: transparent;")
        # Pack variant boxes rebuild on retheme so their Apply buttons follow
        # the palette.
        if hasattr(self, "_pack_grid"):
            self._build_pack_boxes()
        self._reset_btn.setStyleSheet(f"""
            QPushButton#resetIconThemes {{
                background-color: {c.bg_secondary};
                border: 1px solid {c.border};
                border-radius: 20px;
                color: {c.error};
                font-size: 15px;
                font-weight: 600;
                padding: 12px;
            }}
            QPushButton#resetIconThemes:hover {{ background-color: {c.surface_hover}; }}
        """)
        # Rebuild the theme cards so their hardcoded label colors follow the
        # current palette too.
        if hasattr(self, "_themes_box"):
            self.refresh_themes()

    def refresh_themes(self):
        tweak = tweaks[TweakID.IconThemes]
        themes = tweak.themes
        self.themes_placeholder.setVisible(not themes)
        # clear the box
        while self._themes_box.count():
            item = self._themes_box.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        if not themes:
            return
        for theme in themes:
            self._themes_box.addWidget(self._create_theme_card(theme))

    def _create_theme_card(self, theme: IconTheme) -> QWidget:
        c = self._c
        card = IOSCard()
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 12, 12, 12)
        row.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(56, 56)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background-color: {c.bg_secondary}; border-radius: 20px;")
        pixmap = None
        data = theme.get_icon_data()
        # B18: get_icon_data() returns the actual icon PNG bytes (loading them
        # from disk if needed). The old condition only built a pixmap when
        # `data is None`, so a theme WITH icon data never got a thumbnail and
        # always showed "?". Load from the bytes first, fall back to the path.
        if data:
            try:
                candidate = QPixmap()
                if candidate.loadFromData(data):
                    pixmap = candidate
            except Exception:
                pixmap = None
        if (pixmap is None or pixmap.isNull()) and theme.icon_path and os.path.isfile(theme.icon_path):
            try:
                pixmap = QPixmap(theme.icon_path)
            except Exception:
                pixmap = None
        if pixmap is None or pixmap.isNull():
            icon_lbl.setText(QCoreApplication.translate("Nugget", "?"))
        else:
            icon_lbl.setPixmap(pixmap.scaled(
                52, 52, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        row.addWidget(icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        bundle_lbl = QLabel(theme.bundle_id)
        bundle_lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {c.text_primary};")
        bundle_lbl.setWordWrap(True)
        text_col.addWidget(bundle_lbl)
        name_text = theme.display_name if theme.display_name else QCoreApplication.translate("Nugget", "Hide label")
        name_lbl = QLabel(name_text)
        name_lbl.setStyleSheet(f"font-size: 12px; color: {c.text_secondary};")
        name_lbl.setWordWrap(True)
        text_col.addWidget(name_lbl)
        row.addLayout(text_col, 1)

        del_btn = QToolButton()
        del_btn.setIconSize(QSize(18, 18))
        del_btn.setIcon(theme_icon(":/icon/trash.svg", c.text_secondary))
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(
            f"QToolButton {{ background-color: {c.surface_hover}; color: {c.error}; "
            f"border: 1px solid {c.border}; border-radius: 20px; padding: 7px; }}"
            f"QToolButton:hover {{ background-color: {c.error}; color: {c.text_inverse}; }}"
        )
        del_btn.clicked.connect(lambda: self._remove_theme(theme.bundle_id))
        row.addWidget(del_btn)

        return card

    def _remove_theme(self, bundle_id: str):
        tweak = tweaks[TweakID.IconThemes]
        tweak.remove_theme(bundle_id)
        tweak.set_enabled(not tweak.is_empty())
        self.refresh_themes()

    def show_app_list_export(self):
        dialog = AppListExportDialog(self.window)
        if dialog.exec() == QDialog.Accepted:
            app = dialog.selected_app()
            if app is None:
                return
            self.show_add_icon_dialog(bundle_id=app["bundle_id"],
                                      display_name=app["display_name"],
                                      preset=True)

    def show_add_icon_dialog(self, bundle_id: str = "", display_name: str = "",
                             preset: bool = False):
        dialog = IconThemeDialog(self.window, bundle_id=bundle_id,
                                 display_name=display_name, preset=preset)
        if dialog.exec() == QDialog.Accepted:
            theme = dialog.build_theme()
            if theme is None:
                return
            tweak = tweaks[TweakID.IconThemes]
            if not tweak.store_icon(theme):
                QMessageBox.warning(
                    self.window,
                    QCoreApplication.translate("Nugget", "Warning"),
                    QCoreApplication.translate(
                        "Nugget",
                        "Could not store the icon file in the persistent "
                        "folder. The theme may not apply reliably."))
            tweak.add_theme(theme)
            tweak.set_enabled(True)
            self.refresh_themes()

    def show_download_packs(self):
        dialog = IconPackDownloaderDialog(self.window)
        if dialog.exec() == QDialog.Accepted and dialog.added_bundle_ids:
            self.refresh_themes()

class IconThemeDialog(QDialog):
    """Pick an app bundle id, an icon image and an optional label."""

    def __init__(self, parent=None, bundle_id: str = "",
                 display_name: str = "", preset: bool = False):
        super().__init__(parent)
        self.setWindowTitle(QCoreApplication.translate("Nugget", "Add Icon Theme"))
        self.setModal(True)
        self.setMinimumWidth(380)
        self._icon_path = ""
        self._retheme()

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        bundle_row = QHBoxLayout()
        bundle_row.setSpacing(8)
        bundle_lbl = QLabel(QCoreApplication.translate("Nugget", "App Bundle ID"))
        bundle_lbl.setObjectName("fieldLbl")
        bundle_row.addWidget(bundle_lbl)
        self.bundle_input = QLineEdit()
        self.bundle_input.setObjectName("fieldInput")
        self.bundle_input.setPlaceholderText("com.apple.mobilesafari")
        if bundle_id:
            self.bundle_input.setText(bundle_id)
            if preset:
                self.bundle_input.setReadOnly(True)
        bundle_row.addWidget(self.bundle_input, 1)
        layout.addLayout(bundle_row)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_lbl = QLabel(QCoreApplication.translate("Nugget", "Label"))
        name_lbl.setObjectName("fieldLbl")
        name_row.addWidget(name_lbl)
        self.name_input = QLineEdit()
        self.name_input.setObjectName("fieldInput")
        self.name_input.setPlaceholderText(QCoreApplication.translate(
            "Nugget", "Custom label (empty hides it)"))
        if preset and display_name:
            self.name_input.setText(display_name)
        name_row.addWidget(self.name_input, 1)
        layout.addLayout(name_row)

        hint = QLabel(QCoreApplication.translate(
            "Nugget",
            "The app bundle id is the same identifier the app icon uses "
            "under the hood (e.g. com.instagram.instagram)."))
        if preset:
            hint.setText(QCoreApplication.translate(
                "Nugget",
                "Picked from your iPhone: {0}. Type a custom label or "
                "leave it empty to hide it.").format(bundle_id))
        hint.setObjectName("fieldHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.icon_row = QHBoxLayout()
        self.icon_row.setSpacing(8)
        icon_lbl = QLabel(QCoreApplication.translate("Nugget", "Icon"))
        icon_lbl.setObjectName("fieldLbl")
        self.icon_row.addWidget(icon_lbl)
        self.icon_btn = QPushButton(QCoreApplication.translate("Nugget", "Choose Image (.png)"))
        self.icon_btn.setObjectName("fieldInput")
        self.icon_btn.setCursor(Qt.PointingHandCursor)
        self.icon_btn.clicked.connect(self._choose_icon)
        self.icon_row.addWidget(self.icon_btn, 1)
        layout.addLayout(self.icon_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _retheme(self):
        c = ColorThemeManager.instance().colors
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c.bg_elevated}; }}
            QLabel[objectName="fieldLbl"] {{ color: {c.text_secondary}; font-size: 13px; }}
            QLabel[objectName="fieldHint"] {{ color: {c.text_secondary}; font-size: 12px; }}
            QLineEdit, QPushButton[objectName="fieldInput"] {{
                background-color: {c.bg_input};
                border: none;
                border-radius: 20px;
                color: {c.text_primary};
                font-size: 14px;
                padding: 10px 12px;
            }}
            QPushButton[objectName="fieldInput"]:hover {{ background-color: {c.surface_hover}; }}
            QPushButton {{
                background-color: {c.accent};
                border-radius: 20px;
                color: {c.text_inverse};
                font-size: 14px;
                padding: 10px 20px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {c.accent_hover}; }}
            QPushButton[text="Cancel"] {{ background-color: {c.surface_hover}; color: {c.text_primary}; }}
        """)

    def _choose_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            QCoreApplication.translate("Nugget", "Select Icon Image"),
            "",
            "Images (*.png *.heic *.jpg *.webp)")
        if path:
            self._icon_path = path
            self.icon_btn.setText(os.path.basename(path))

    def _on_accept(self):
        if not self.bundle_input.text().strip():
            QMessageBox.warning(
                self,
                QCoreApplication.translate("Nugget", "Warning"),
                QCoreApplication.translate("Nugget", "Enter the app bundle id."))
            return
        if not self._icon_path:
            QMessageBox.warning(
                self,
                QCoreApplication.translate("Nugget", "Warning"),
                QCoreApplication.translate("Nugget", "Choose an icon image first."))
            return
        self.accept()

    def build_theme(self):
        return IconTheme(
            bundle_id=self.bundle_input.text().strip(),
            display_name=self.name_input.text().strip(),
            icon_path=self._icon_path)