import os

from PySide6.QtCore import Qt, QCoreApplication, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QGridLayout,
    QPushButton, QToolButton, QFileDialog, QDialog, QDialogButtonBox,
    QLineEdit, QMessageBox,
)

from src.gui.ios.components import IOSCard
from src.gui.theme import ColorThemeManager, theme_icon, t
from src.gui.dialogs.icon_pack_downloader import IconPackDownloaderDialog
from src.gui.dialogs.app_list_dialog import AppListExportDialog
from src.tweaks.tweaks import tweaks, TweakID
from src.tweaks.icon_themes.icon_theme import IconTheme


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
        self.content_layout.setContentsMargins(20, 20, 20, 36)
        self.content_layout.setSpacing(14)

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

        # Quick actions in one row of equal, easy-to-hit buttons (modern
        # layout, user order 2026-10-20 — was three stacked full-width rows).
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)
        download_btn = QPushButton(QCoreApplication.translate(
            "Nugget", "Download Icon Packs"))
        download_btn.setObjectName("downloadIconPacks")
        download_btn.setCursor(Qt.PointingHandCursor)
        download_btn.setMinimumHeight(48)
        download_btn.clicked.connect(self.show_download_packs)
        self._download_btn = download_btn
        actions_row.addWidget(download_btn, 1)

        apps_btn = QPushButton(QCoreApplication.translate(
            "Nugget", "Apps on iPhone"))
        apps_btn.setObjectName("appsOnIphone")
        apps_btn.setCursor(Qt.PointingHandCursor)
        apps_btn.setMinimumHeight(48)
        apps_btn.clicked.connect(self.show_app_list_export)
        self._apps_btn = apps_btn
        actions_row.addWidget(apps_btn, 1)

        reset_btn = QPushButton(QCoreApplication.translate(
            "Nugget", "Reset Icon Themes"))
        reset_btn.setObjectName("resetIconThemes")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setMinimumHeight(48)
        reset_btn.clicked.connect(self._reset_themes)
        self._reset_btn = reset_btn
        actions_row.addWidget(reset_btn, 1)
        self.content_layout.addLayout(actions_row)

        # -- iOS 18 Icon Pack (user order 2026-10-18): the pack choices
        # live directly on this page — Light / Dark / Tinted / more
        # tints — each one imports the variant's folder or .zip straight
        # into the themes via the existing import machinery. The pack
        # files themselves are user-supplied (not bundled in the repo).
        # Modern layout (2026-10-20): one card per variant with a preview
        # thumbnail; tapping the card starts the same import flow.
        pack_title = QLabel(QCoreApplication.translate(
            "Nugget", "iOS 18 Icon Pack"))
        pack_title.setObjectName("packTitle")
        pack_title.setWordWrap(True)
        self._pack_title = pack_title
        self.content_layout.addWidget(pack_title)
        pack_hint = QLabel(QCoreApplication.translate(
            "Nugget",
            "Import the iOS 18-style pack from your own files. Pick a "
            "variant, choose its folder or .zip, and the icons apply "
            "right away."))
        pack_hint.setObjectName("packHint")
        pack_hint.setWordWrap(True)
        self._pack_hint = pack_hint
        self.content_layout.addWidget(pack_hint)
        pack_row = QHBoxLayout()
        pack_row.setSpacing(12)
        self._pack_card_labels = {}
        for variant in ("Light", "Dark", "Tinted", "More Tints"):
            pack_row.addWidget(self._create_pack_card(variant), 1)
        self.content_layout.addLayout(pack_row)

        self.themes_placeholder = QLabel(QCoreApplication.translate(
            "Nugget", "No icon themes yet. Tap + Add Icon or download a pack."))
        self.themes_placeholder.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.themes_placeholder)

        # Applied themes as a clean two-column card grid.
        self._themes_box = QGridLayout()
        self._themes_box.setSpacing(12)
        self._themes_box.setColumnStretch(0, 1)
        self._themes_box.setColumnStretch(1, 1)
        self.content_layout.addLayout(self._themes_box)

        self.content_layout.addStretch()

        self._retheme()
        self.refresh_themes()

    @staticmethod
    def _pack_preview(variant: str) -> QPixmap:
        """Small generated preview swatch for a pack variant card: a
        rounded tile holding a 2x2 mini icon grid in the variant's colors."""
        palettes = {
            "Light": ("#FFFFFF", "#C9D4E2",
                      ("#E9EEF4", "#E9EEF4", "#E9EEF4", "#E9EEF4")),
            "Dark": ("#1D1D20", "#3A3A3E",
                     ("#3A3A3E", "#3A3A3E", "#3A3A3E", "#3A3A3E")),
            "Tinted": ("#D9E7FF", "#A9C8F5",
                       ("#5B9BFF", "#7FB0FF", "#3B82F6", "#9CC2FF")),
            "More Tints": ("#FFFFFF", "#C9D4E2",
                           ("#FF5A5A", "#FFB340", "#34C759", "#5B9BFF")),
        }
        bg, border, squares = palettes.get(variant, palettes["Light"])
        size = 144
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(bg))
        p.setPen(QPen(QColor(border), 3))
        p.drawRoundedRect(4, 4, size - 8, size - 8, 28, 28)
        p.setPen(Qt.NoPen)
        cell, gap, start = 44, 12, 22
        for i, col in enumerate(squares):
            x = start + (i % 2) * (cell + gap)
            y = start + (i // 2) * (cell + gap)
            p.setBrush(QColor(col))
            p.drawRoundedRect(x, y, cell, cell, 12, 12)
        p.end()
        return pm

    def _create_pack_card(self, variant: str) -> QWidget:
        """One tappable pack card: preview thumbnail, name, Import label."""
        card = IOSCard(glass=True)
        card.setCursor(Qt.PointingHandCursor)
        card.setMinimumHeight(168)
        v = QVBoxLayout(card)
        v.setContentsMargins(12, 14, 12, 14)
        v.setSpacing(8)
        prev = QLabel()
        prev.setAlignment(Qt.AlignCenter)
        prev.setAttribute(Qt.WA_TransparentForMouseEvents)
        prev.setPixmap(self._pack_preview(variant).scaled(
            72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        v.addWidget(prev)
        name = QLabel(QCoreApplication.translate("Nugget", variant))
        name.setAlignment(Qt.AlignCenter)
        name.setAttribute(Qt.WA_TransparentForMouseEvents)
        v.addWidget(name)
        imp = QLabel(QCoreApplication.translate("Nugget", "Import"))
        imp.setAlignment(Qt.AlignCenter)
        imp.setAttribute(Qt.WA_TransparentForMouseEvents)
        v.addWidget(imp)
        card.mousePressEvent = (
            lambda e, var=variant: self._import_pack_variant(var))
        self._pack_card_labels[variant] = (name, imp)
        return card

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
        self._download_btn.setStyleSheet("""
            QPushButton#downloadIconPacks {
                background-color: #5B9BFF;
                border: none;
                border-radius: 20px;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
                padding: 12px;
            }
            QPushButton#downloadIconPacks:hover { background-color: #6FA8FF; }
            QPushButton#downloadIconPacks:pressed { background-color: #3B82F6; }
        """)
        self._apps_btn.setStyleSheet("""
            QPushButton#appsOnIphone {
                background-color: #5B9BFF;
                border: none;
                border-radius: 20px;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
                padding: 12px;
            }
            QPushButton#appsOnIphone:hover { background-color: #6FA8FF; }
            QPushButton#appsOnIphone:pressed { background-color: #3B82F6; }
        """)
        self.themes_placeholder.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 15px; padding: 24px 0;")
        self._pack_title.setStyleSheet(
            f"color: {c.text_primary}; font-size: 16px; font-weight: 700; "
            f"padding: 14px 0 0 0; background: transparent;")
        self._pack_hint.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 13px; background: transparent;")
        for name_lbl, imp_lbl in self._pack_card_labels.values():
            name_lbl.setStyleSheet(
                "font-size: 14px; font-weight: 700; color: #FFFFFF;"
                " background: transparent;")
            imp_lbl.setStyleSheet(
                "font-size: 12px; font-weight: 600; "
                "color: rgba(255, 255, 255, 0.9);"
                " background: transparent;")
        self._reset_btn.setStyleSheet("""
            QPushButton#resetIconThemes {
                background-color: #5B9BFF;
                border: none;
                border-radius: 20px;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
                padding: 12px;
            }
            QPushButton#resetIconThemes:hover { background-color: #6FA8FF; }
            QPushButton#resetIconThemes:pressed { background-color: #3B82F6; }
        """)
        # Rebuild the theme cards so their hardcoded label colors follow the
        # current palette too.
        if hasattr(self, "_themes_box"):
            self.refresh_themes()

    def refresh_themes(self):
        tweak = tweaks[TweakID.IconThemes]
        themes = tweak.themes
        self.themes_placeholder.setVisible(not themes)
        # clear the grid
        while self._themes_box.count():
            item = self._themes_box.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        # two-column card grid
        for i, theme in enumerate(themes):
            self._themes_box.addWidget(
                self._create_theme_card(theme), i // 2, i % 2)

    def _create_theme_card(self, theme: IconTheme) -> QWidget:
        c = self._c
        card = IOSCard(glass=True)
        row = QHBoxLayout(card)
        row.setContentsMargins(14, 14, 14, 14)
        row.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(64, 64)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background-color: {c.bg_secondary}; border-radius: 20px;"
            f" color: {c.text_primary};")
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
                60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        row.addWidget(icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        bundle_lbl = QLabel(theme.bundle_id)
        bundle_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #FFFFFF; background: transparent;")
        bundle_lbl.setWordWrap(True)
        text_col.addWidget(bundle_lbl)
        name_text = theme.display_name if theme.display_name else QCoreApplication.translate("Nugget", "Hide label")
        name_lbl = QLabel(name_text)
        name_lbl.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.88); background: transparent;")
        name_lbl.setWordWrap(True)
        text_col.addWidget(name_lbl)
        row.addLayout(text_col, 1)

        del_btn = QToolButton()
        del_btn.setIconSize(QSize(18, 18))
        del_btn.setIcon(theme_icon(":/icon/trash.svg", "#FFFFFF"))
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(
            "QToolButton { background-color: rgba(255, 255, 255, 0.30); color: #FFFFFF; "
            "border: none; border-radius: 20px; padding: 7px; }"
            f"QToolButton:hover {{ background-color: {c.error}; color: #FFFFFF; }}"
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

    def _import_pack_variant(self, variant: str):
        """Import one iOS 18 pack variant from the user's own folder/.zip."""
        from PySide6.QtWidgets import QInputDialog
        tweak = tweaks[TweakID.IconThemes]
        tr = lambda s: QCoreApplication.translate("Nugget", s)
        options = [tr("Pack folder…"), tr("Pack .zip file…")]
        choice, ok = QInputDialog.getItem(
            self.window, tr(f"iOS 18 Pack — {variant}"),
            tr("Import the variant from:"),
            options, 0, False)
        if not ok:
            return
        if options.index(choice) == 0:
            folder = QFileDialog.getExistingDirectory(
                self.window, tr(f"Choose the {variant} pack folder"))
            if not folder:
                return
            added, _skipped = tweak.import_pack(folder)
        else:
            path, _ = QFileDialog.getOpenFileName(
                self.window, tr(f"Choose the {variant} pack .zip"),
                "", "Icon packs (*.zip)")
            if not path:
                return
            added, _skipped = tweak.import_pack_zip(path)
        if added:
            tweak.set_enabled(True)
            self.refresh_themes()
            QMessageBox.information(
                self.window, tr(f"iOS 18 Pack — {variant}"),
                tr("Imported {0} icons ({1}).").format(added, variant))
        else:
            QMessageBox.warning(
                self.window, tr(f"iOS 18 Pack — {variant}"),
                tr("No icons found in the selected {0} pack.").format(variant))


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