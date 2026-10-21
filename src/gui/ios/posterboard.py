import os

from PySide6.QtCore import Qt, QSize, QRect, QCoreApplication, QUrl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QPushButton, QScrollArea, QToolButton, QStackedWidget,
    QCheckBox, QComboBox, QListWidget, QMessageBox,
    QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QPixmap, QIcon, QImageReader, QColor
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from src.gui.ios.components import (
    IOSCard, IOSPrimaryButton, apply_full_nugget_chrome,
)
from src.gui.theme import ColorThemeManager, t
from src.gui.theme.colors import NUGGET_DARK
from src.tweaks.tweaks import tweaks, TweakID


def _pb_shadow(widget):
    """Soft neutral drop shadow for the page's hero/buttons (clean-light)."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setColor(QColor(15, 23, 42, 26))
    shadow.setBlurRadius(10)
    shadow.setOffset(0, 2)
    widget.setGraphicsEffect(shadow)
    return shadow


class TemplatePreviewCard(QLabel):
    """Clickable preview image that can show full size"""
    def __init__(self, pixmap: QPixmap, preview_name: str, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(200, 200)
        self._original_pixmap = pixmap
        self._preview_name = preview_name
        self._retheme()
        self.setPixmap(pixmap.scaled(190, 190, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _retheme(self):
        # Blue glass frame (user 2026-10-20: no white surfaces left on
        # the PosterBoard page); the page's _retheme overrides this with
        # the Nugget dark QSS in the Full Nugget interface.
        self.setStyleSheet(
            "QLabel { background-color: #F7F9FC;"
            " border-radius: 20px; border: 1px solid #DEE5EE; }"
        )


class IOSPosterboardPage(QWidget):
    """PosterBoard page — 100% layout redo (user order 2026-10-20).

    New flow (visual-first):
      1. IMPORT HERO — big primary import action at the very top.
      2. Tab bar (Tendies / Templates / Video) right under the hero.
      3. Tab stack (wallpaper content).
      4. Delivery mode — compact segmented selector (not a big card).
      5. Database tools — collapsible section (Configurations mode only).
      6. Reset — danger zone pinned at the very bottom.
    """

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.setObjectName("iosContainer")
        self._full_nugget = False
        # Text scale driven by the page width (user 2026-10-21: the tab
        # boxes and import-area text looked messy at other resolutions
        # because every font size was fixed). _px() applies it; the
        # resizeEvent below recomputes it and re-runs _retheme().
        self._ui_scale = 1.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- 1. IMPORT HERO (primary action, top) ----------------------
        hero = IOSCard(glass=True)
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(20, 16, 20, 16)
        hero_layout.setSpacing(16)

        hero_text = QVBoxLayout()
        hero_text.setSpacing(4)
        hero_title = QLabel(QCoreApplication.translate(
            "Nugget", "PosterBoard"))
        hero_title.setObjectName("pbHeroTitle")
        hero_sub = QLabel(QCoreApplication.translate(
            "Nugget", "Wallpapers, templates & video backgrounds"))
        hero_sub.setObjectName("pbHeroSub")
        hero_sub.setWordWrap(True)
        hero_text.addWidget(hero_title)
        hero_text.addWidget(hero_sub)
        hero_layout.addLayout(hero_text, 1)

        self._import_hero_btn = QPushButton(QCoreApplication.translate(
            "Nugget", "Import Wallpapers"))
        self._import_hero_btn.setCursor(Qt.PointingHandCursor)
        self._import_hero_btn.setObjectName("pbImportHero")
        self._import_hero_btn.setFixedHeight(48)
        self._import_hero_btn.setMinimumWidth(200)
        self._import_hero_btn.clicked.connect(self.show_add_tendies_dialog)
        _pb_shadow(self._import_hero_btn)
        hero_layout.addWidget(self._import_hero_btn, 0, Qt.AlignVCenter)

        layout.addWidget(hero)
        self._hero_card = hero
        self._hero_title = hero_title
        self._hero_sub = hero_sub

        # ---- 2. Tab bar (under the hero) -------------------------------
        self._tab_bar = QWidget()
        self._tab_bar.setFixedHeight(56)
        tab_layout = QHBoxLayout(self._tab_bar)
        tab_layout.setContentsMargins(6, 8, 6, 2)
        tab_layout.setSpacing(8)

        self.tendies_tab_btn = self._make_tab_button(
            QCoreApplication.translate("Nugget", "Tendies"),
            ":/icon/wallpaper.svg", 0)
        self.templates_tab_btn = self._make_tab_button(
            QCoreApplication.translate("Nugget", "Templates"),
            ":/icon/photo-stack.svg", 1)
        self.video_tab_btn = self._make_tab_button(
            QCoreApplication.translate("Nugget", "Video"),
            ":/icon/play-circle.svg", 2)

        tab_layout.addWidget(self.tendies_tab_btn, 1)
        tab_layout.addWidget(self.templates_tab_btn, 1)
        tab_layout.addWidget(self.video_tab_btn, 1)
        layout.addWidget(self._tab_bar)

        # ---- 3. Tab stack ----------------------------------------------
        self.tab_stack = QStackedWidget()
        layout.addWidget(self.tab_stack, 1)

        self.tendies_page = self._create_tendies_tab()
        self.tab_stack.addWidget(self.tendies_page)

        self.templates_page = self._create_templates_tab()
        self.tab_stack.addWidget(self.templates_page)

        self.video_page = self._create_video_tab()
        self.tab_stack.addWidget(self.video_page)

        # ---- 4. Delivery mode (compact segmented) ----------------------
        mode_bar = QWidget()
        mode_bar.setObjectName("pbModeBar")
        mode_layout = QHBoxLayout(mode_bar)
        mode_layout.setContentsMargins(16, 8, 16, 8)
        mode_layout.setSpacing(8)

        mode_lbl = QLabel(QCoreApplication.translate("Nugget", "Delivery:"))
        mode_lbl.setObjectName("pbModeLabel")
        mode_layout.addWidget(mode_lbl)

        self._mode_descriptors = QPushButton(QCoreApplication.translate(
            "Nugget", "Descriptors"))
        self._mode_descriptors.setCheckable(True)
        self._mode_descriptors.setChecked(True)
        self._mode_descriptors.setCursor(Qt.PointingHandCursor)
        self._mode_descriptors.setObjectName("pbModeBtn")
        self._mode_descriptors.clicked.connect(
            lambda: self._on_mode_toggled(False, True))
        mode_layout.addWidget(self._mode_descriptors)

        self._mode_configs = QPushButton(QCoreApplication.translate(
            "Nugget", "Configurations"))
        self._mode_configs.setCheckable(True)
        self._mode_configs.setCursor(Qt.PointingHandCursor)
        self._mode_configs.setObjectName("pbModeBtn")
        self._mode_configs.clicked.connect(
            lambda: self._on_mode_toggled(True, True))
        mode_layout.addWidget(self._mode_configs)
        _pb_shadow(self._mode_descriptors)
        _pb_shadow(self._mode_configs)
        mode_layout.addStretch(1)
        layout.addWidget(mode_bar)

        self._mode_caption = QLabel(QCoreApplication.translate(
            "Nugget",
            "Descriptors: wallpapers delivered as files (recommended). "
            "Configurations: also registered in the device database."))
        self._mode_caption.setWordWrap(True)
        self._mode_caption.setObjectName("pbModeCaption")
        self._mode_caption.setContentsMargins(16, 0, 16, 8)
        layout.addWidget(self._mode_caption)

        # ---- 5. Database tools (collapsible, Configurations only) ------
        self._config_card = IOSCard(glass=True)
        config_layout = QVBoxLayout(self._config_card)
        config_layout.setContentsMargins(16, 12, 16, 12)
        config_layout.setSpacing(8)
        self.pb_db_lbl = QLabel(
            QCoreApplication.translate("Nugget", "Database: none selected"),
            self._config_card)
        config_layout.addWidget(self.pb_db_lbl)
        db_btns = QHBoxLayout()
        get_db_btn = QPushButton(QCoreApplication.translate(
            "Nugget", "Get Database from Device"), self._config_card)
        get_db_btn.clicked.connect(self._on_pb_get_db)
        db_btns.addWidget(get_db_btn)
        sel_db_btn = QPushButton(QCoreApplication.translate(
            "Nugget", "Select Database File"), self._config_card)
        sel_db_btn.clicked.connect(self._on_pb_select_db)
        db_btns.addWidget(sel_db_btn)
        db_btns.addStretch(1)
        config_layout.addLayout(db_btns)
        self._saved_ids_lbl = QLabel(QCoreApplication.translate(
            "Nugget", "Saved Configuration IDs"), self._config_card)
        config_layout.addWidget(self._saved_ids_lbl)
        self.saved_ids_list = QListWidget(self._config_card)
        self._saved_ids_list = self.saved_ids_list
        config_layout.addWidget(self.saved_ids_list)
        ids_btns = QHBoxLayout()
        clear_btn = QPushButton(QCoreApplication.translate(
            "Nugget", "Clear"), self._config_card)
        clear_btn.clicked.connect(self._on_clear_saved_ids)
        ids_btns.addWidget(clear_btn)
        remove_btn = QPushButton(QCoreApplication.translate(
            "Nugget", "Remove Selected"), self._config_card)
        remove_btn.clicked.connect(self._on_remove_selected_id)
        ids_btns.addWidget(remove_btn)
        ids_btns.addStretch(1)
        config_layout.addLayout(ids_btns)
        self._pb_db_btns = [get_db_btn, sel_db_btn, clear_btn, remove_btn]
        self._config_card.hide()
        layout.addWidget(self._config_card)
        self._refresh_saved_ids()

        # ---- 6. Reset (danger zone, bottom) -----------------------------
        # Blue-glass card like the rest of the page (user 2026-10-20);
        # the danger identity lives on the red button itself.
        reset_bar = IOSCard(glass=True)
        reset_bar.setObjectName("pbResetBar")
        reset_layout = QHBoxLayout(reset_bar)
        reset_layout.setContentsMargins(16, 8, 16, 12)
        reset_layout.setSpacing(8)
        self._reset_btn = QPushButton(QCoreApplication.translate(
            "Nugget", "Reset PosterBoard"))
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.setObjectName("pbResetBtn")
        self._reset_btn.clicked.connect(self._reset_posterboard)
        reset_layout.addWidget(self._reset_btn)
        self._reset_caption = QLabel(QCoreApplication.translate(
            "Nugget",
            "Recovery: clears delivered descriptors on next apply."))
        self._reset_caption.setWordWrap(True)
        self._reset_caption.setObjectName("pbResetCaption")
        reset_layout.addWidget(self._reset_caption, 1)
        layout.addWidget(reset_bar)

        self._tendie_nam = QNetworkAccessManager(self)
        self._tendie_preview_replies = []

        self._retheme()
        self._switch_tab(0)
        self.refresh_tendies()

        ColorThemeManager.instance().theme_changed.connect(self._retheme)

    def _palette(self):
        """Active colors: upstream Nugget dark in the Full Nugget
        interface, the themed WorkSlop palette everywhere else."""
        if getattr(self, "_full_nugget", False):
            return NUGGET_DARK
        return ColorThemeManager.instance().colors

    def set_full_nugget(self, enabled: bool):
        """Full Nugget (third interface) restyle: this page takes the
        Nugget-original dark palette, exactly like the vendored Nugget
        pages; the other interfaces keep the themed look untouched.
        Widgets and behavior are identical — colors only."""
        self._full_nugget = bool(enabled)
        self._retheme()

    # -- resolution-adaptive text --------------------------------------
    def _px(self, base: int) -> int:
        """Font size for *base* px at the current page-width scale."""
        return max(9, round(base * self._ui_scale))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Reference: the page is ~1000px wide in the standard 1240px
        # window. Scale text 0.88x..1.15x with the actual width and
        # restyle only when the rounded scale actually changes.
        scale = max(0.88, min(1.15, self.width() / 1000.0))
        if abs(scale - self._ui_scale) > 0.02:
            self._ui_scale = scale
            if hasattr(self, "tendies_tab_btn"):
                self._retheme()

    def _tab_sheet(self) -> str:
        return f"""
            QToolButton {{
                background-color: #F1F4F8;
                color: #374151;
                font-size: {self._px(12)}px;
                font-weight: 600;
                padding: 4px 0;
                border: 1px solid #DEE5EE;
                border-radius: 12px;
            }}
            QToolButton:checked {{
                background-color: #2563EB;
                color: #FFFFFF;
                border: 1px solid #2563EB;
            }}
            QToolButton:hover {{
                background-color: #E4E9F0;
                color: #374151;
            }}
            QToolButton:checked:hover {{
                background-color: #1D4ED8;
                color: #FFFFFF;
            }}
        """

    def _retheme(self):
        c = self._palette()
        # Redo 2026-10-20: page floats transparent; hero card + controls
        # get their own surfaces.
        self.setStyleSheet(
            "background: transparent; border: none;"
            " IOSPosterboardPage QWidget { background: transparent; }")
        # Hero — the card is blue glass now, so its text is white in
        # every interface (the Full Nugget chrome darkens the card).
        if hasattr(self, "_hero_title"):
            self._hero_title.setStyleSheet(
                "background: transparent; color: #111827;"
                " font-size: 22px; font-weight: 800;")
        if hasattr(self, "_hero_sub"):
            self._hero_sub.setStyleSheet(
                "background: transparent; color: rgba(17, 24, 39, 0.62);"
                " font-size: 13px;")
        if hasattr(self, "_import_hero_btn"):
            self._import_hero_btn.setStyleSheet(f"""
                QPushButton#pbImportHero {{
                    background-color: {c.accent};
                    border: none;
                    border-radius: 14px;
                    color: #FFFFFF;
                    font-size: 15px;
                    font-weight: 700;
                    padding: 0 24px;
                }}
                QPushButton#pbImportHero:hover {{
                    background-color: {c.accent_hover};
                }}
                QPushButton#pbImportHero:pressed {{
                    background-color: {c.accent_pressed};
                }}
            """)
        # Mode segmented buttons — flat clean-light pills: inactive =
        # light grey with dark text, active = solid accent blue.
        for btn in (self._mode_descriptors, self._mode_configs):
            btn.setStyleSheet("""
                QPushButton#pbModeBtn {
                    background-color: #F1F4F8;
                    border: 1px solid #DEE5EE;
                    border-radius: 12px;
                    color: #374151;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 8px 18px;
                }
                QPushButton#pbModeBtn:checked {
                    background-color: #2563EB;
                    border: 1px solid #2563EB;
                    color: #FFFFFF;
                }
                QPushButton#pbModeBtn:hover {
                    background-color: #E4E9F0;
                }
                QPushButton#pbModeBtn:checked:hover {
                    background-color: #1D4ED8;
                }
            """)
        # Reset: flat red danger button on the white card.
        self._reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #E5484D;
                border: none;
                border-radius: 12px;
                color: #FFFFFF;
                font-size: 15px;
                font-weight: 600;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #D63A35;
            }
            QPushButton:pressed {
                background-color: #B92E2A;
            }
        """)
        self._reset_caption.setStyleSheet(
            "background: transparent; color: rgba(17, 24, 39, 0.66);"
            " font-size: 13px;")
        self._tab_bar.setStyleSheet(
            "background: transparent; border: none;"
        )
        for btn in (self.tendies_tab_btn, self.templates_tab_btn, self.video_tab_btn):
            btn.setStyleSheet(self._tab_sheet())
            # Tab icons: white on the active blue pill, slate when idle.
            try:
                from src.gui.theme import theme_icon
                res = btn.property("_ws_icon_res")
                if res:
                    btn.setIcon(theme_icon(
                        res, "#FFFFFF" if btn.isChecked() else "#5B6472"))
            except Exception:
                pass
        self._retheme_tendies_tab()
        self._retheme_templates_tab()
        self._retheme_video_tab()
        apply_full_nugget_chrome(self, self._full_nugget)
        for card in self.findChildren(TemplatePreviewCard):
            if self._full_nugget:
                card.setStyleSheet(
                    "QLabel { background-color: #3b3b3b; border-radius: 20px;"
                    " border: 1px solid #4B4B4B; }")
            else:
                card._retheme()
        self._retheme_config_card()

    def _retheme_config_card(self):
        c = self._palette()
        dark = self._full_nugget
        # The config card is blue glass (WorkSlop) / dark (Full Nugget):
        # its labels are white either way.
        lbl_qss = (f"color: {c.text_primary}; font-size: 13px;"
                   " background-color: transparent;") if dark else (
                   "color: #111827; font-size: 13px;"
                   " background-color: transparent;")
        self.pb_db_lbl.setStyleSheet(lbl_qss)
        if hasattr(self, "_saved_ids_lbl"):
            self._saved_ids_lbl.setStyleSheet(lbl_qss)
        for btn in getattr(self, "_pb_db_btns", []):
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #F1F4F8;
                    border: 1px solid #DEE5EE;
                    border-radius: 12px;
                    color: #374151;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 8px 12px;
                }
                QPushButton:hover {
                    background-color: #E4E9F0;
                }
            """)
        if hasattr(self, "saved_ids_list"):
            self.saved_ids_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {c.bg_input};
                    border: 1px solid {c.border};
                    border-radius: 18px;
                    color: {c.text_primary};
                    font-size: 13px;
                    padding: 4px;
                }}
                QListWidget::item {{ padding: 6px; }}
                QListWidget::item:selected {{
                    background-color: {c.accent}; color: {c.text_inverse}; }}
            """ if dark else """
                QListWidget {
                    background-color: #F7F9FC;
                    border: 1px solid #DEE5EE;
                    border-radius: 14px;
                    color: #111827;
                    font-size: 13px;
                    padding: 4px;
                }
                QListWidget::item { padding: 6px; }
                QListWidget::item:selected {
                    background-color: #2563EB;
                    color: #FFFFFF;
                }
                QListWidget:disabled { color: rgba(17, 24, 39, 0.4); }
            """)

    def _retheme_tendies_tab(self):
        c = self._palette()
        if hasattr(self, '_tendies_scroll'):
            # Round 6: no panels — content floats on the watermark.
            self._tendies_scroll.setStyleSheet(t("scroll_area"))
            self._tendies_scroll.viewport().setStyleSheet(
                "background: transparent;")
            self._tendies_scroll.widget().setStyleSheet(
                "background: transparent; border: none;")
        if hasattr(self, '_download_icon'):
            self._download_icon.setStyleSheet(
                f"QLabel {{ background-color: {c.accent}; border-radius: 20px; font-size: 24px; color: {c.text_inverse}; }}"
            )
        # Download/add cards are white slabs now: text is dark.
        if hasattr(self, '_download_title'):
            self._download_title.setStyleSheet(
                f"font-size: {self._px(16)}px; font-weight: 600;"
                " color: #111827; background: transparent;"
            )
        if hasattr(self, '_download_subtitle'):
            self._download_subtitle.setStyleSheet(
                f"font-size: {self._px(12)}px;"
                " color: rgba(17, 24, 39, 0.62);"
                " background: transparent;"
            )
        if hasattr(self, '_download_chevron'):
            self._download_chevron.setStyleSheet(
                "font-size: 26px; color: rgba(17, 24, 39, 0.5);"
                " background: transparent;"
            )
        if hasattr(self, '_add_icon'):
            # File-drop tile: dashed border kept, now on the white slab.
            self._add_icon.setStyleSheet(
                "QLabel { background-color: #F7F9FC;"
                " border-radius: 20px; border: 2px dashed #B9C6D6;"
                " font-size: 36px; color: #5B6472; }"
            )
        if hasattr(self, '_add_label'):
            self._add_label.setStyleSheet(
                f"font-size: {self._px(14)}px;"
                " color: rgba(17, 24, 39, 0.75);"
                " text-align: center; background: transparent;"
            )

    def _retheme_templates_tab(self):
        c = self._palette()
        if hasattr(self, '_templates_scroll'):
            # Round 6: no panels — content floats on the watermark.
            self._templates_scroll.setStyleSheet(t("scroll_area"))
            self._templates_scroll.viewport().setStyleSheet(
                "background: transparent;")
            self._templates_scroll.widget().setStyleSheet(
                "background: transparent; border: none;")
        if hasattr(self, 'templates_placeholder'):
            self.templates_placeholder.setStyleSheet(
                f"font-size: 15px; color: {c.text_secondary};"
            )

    def _retheme_video_tab(self):
        c = self._palette()
        if hasattr(self, '_video_scroll'):
            # Round 6: no panels — content floats on the watermark.
            self._video_scroll.setStyleSheet(t("scroll_area"))
            self._video_scroll.viewport().setStyleSheet(
                "background: transparent;")
            self._video_scroll.widget().setStyleSheet(
                "background: transparent; border: none;")
        for lbl in getattr(self, '_video_labels', []):
            lbl.setStyleSheet(f"font-size: 15px; color: {c.text_primary}; min-width: 100px;")
        for btn in (getattr(self, 'thumb_btn', None), getattr(self, 'video_btn', None)):
            if btn is not None:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #F1F4F8;
                        border-radius: 12px;
                        color: #374151;
                        font-size: 15px;
                        font-weight: 600;
                        padding: 12px 24px;
                        border: 1px solid #DEE5EE;
                    }
                    QPushButton:hover {
                        background-color: #E4E9F0;
                    }
                """)
        for chk in (getattr(self, 'loop_chk', None), getattr(self, 'reverse_chk', None),
                     getattr(self, 'foreground_chk', None)):
            if chk is not None:
                chk.setStyleSheet(f"color: {c.text_primary}; font-size: 15px;")
        if hasattr(self, 'calc_mode_drp'):
            self.calc_mode_drp.setStyleSheet("""
                QComboBox {
                    background-color: #FFFFFF;
                    border: 1px solid #DEE5EE;
                    border-radius: 12px;
                    color: #111827;
                    font-size: 10.5pt;
                    padding: 8px 12px;
                }
                QComboBox::drop-down { border: none; width: 24px; }
                QComboBox QAbstractItemView {
                    background-color: #FFFFFF;
                    border: 1px solid #DEE5EE;
                    border-radius: 12px;
                    color: #111827;
                    selection-background-color: #2563EB;
                    selection-color: #FFFFFF;
                }
            """)

    def _make_tab_button(self, text: str, icon_path: str, index: int) -> QToolButton:
        btn = QToolButton()
        btn.setText(text)
        btn.setIconSize(QSize(24, 24))
        # Recolor via theme_icon so the icon is visible on any theme
        # (raw QIcon kept Apple-black CoreSVG invisible on dark).
        try:
            from src.gui.theme import theme_icon, ColorThemeManager
            c = ColorThemeManager.instance().colors
            btn.setIcon(theme_icon(icon_path, c.text_primary))
            btn.setProperty("_ws_icon_res", icon_path)
        except Exception:
            from PySide6.QtGui import QIcon
            btn.setIcon(QIcon(icon_path))
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setCursor(Qt.PointingHandCursor)
        _pb_shadow(btn)
        btn.clicked.connect(lambda: self._switch_tab(index))
        return btn

    def _switch_tab(self, index: int):
        self.tab_stack.setCurrentIndex(index)
        self.tendies_tab_btn.setChecked(index == 0)
        self.templates_tab_btn.setChecked(index == 1)
        self.video_tab_btn.setChecked(index == 2)
        # Icon tint follows the checked state (white on blue, slate idle).
        try:
            from src.gui.theme import theme_icon
            for btn in (self.tendies_tab_btn, self.templates_tab_btn,
                        self.video_tab_btn):
                res = btn.property("_ws_icon_res")
                if res:
                    btn.setIcon(theme_icon(
                        res, "#FFFFFF" if btn.isChecked() else "#5B6472"))
        except Exception:
            pass

    def _create_tendies_tab(self) -> QWidget:
        self._tendies_scroll = QScrollArea()
        self._tendies_scroll.setWidgetResizable(True)
        content = QWidget()
        self._tendies_scroll.setWidget(content)

        self.tendies_grid = QGridLayout(content)
        self.tendies_grid.setContentsMargins(16, 16, 16, 32)
        self.tendies_grid.setSpacing(12)
        self.tendies_grid.setAlignment(Qt.AlignTop)

        self.download_card = self._create_download_card()
        self.tendies_grid.addWidget(self.download_card, 0, 0, 1, 2)

        self.add_tendies_card = self._create_add_tendies_card()
        self.tendies_grid.addWidget(self.add_tendies_card, 1, 0)

        return self._tendies_scroll

    def _create_download_card(self) -> QWidget:
        c = ColorThemeManager.instance().colors
        card = IOSCard(glass=True)
        card.setCursor(Qt.PointingHandCursor)
        card.setMinimumHeight(88)
        card.mousePressEvent = lambda e: self.open_wallpaper_downloader()

        inner = QHBoxLayout(card)
        inner.setContentsMargins(16, 12, 16, 12)
        inner.setSpacing(12)

        self._download_icon = QLabel()
        self._download_icon.setFixedSize(48, 48)
        self._download_icon.setAlignment(Qt.AlignCenter)
        self._download_icon.setText("\u2193")
        inner.addWidget(self._download_icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._download_title = QLabel(QCoreApplication.translate("Nugget", "Download Wallpapers"))
        text_col.addWidget(self._download_title)
        self._download_subtitle = QLabel(QCoreApplication.translate(
            "Nugget",
            "Browse and import wallpapers from Cowabunga and CaPlayground"))
        self._download_subtitle.setWordWrap(True)
        text_col.addWidget(self._download_subtitle)
        inner.addLayout(text_col, 1)

        self._download_chevron = QLabel("\u203A")
        inner.addWidget(self._download_chevron)

        return card

    def _create_add_tendies_card(self) -> QWidget:
        c = ColorThemeManager.instance().colors
        card = IOSCard(glass=True)
        # Same size as the tendie cards so the grid rows stay even.
        card.setFixedSize(self._tendie_card_size()[0])
        card.setCursor(Qt.PointingHandCursor)
        card.mousePressEvent = lambda e: self.show_add_tendies_dialog()

        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 16, 16, 16)
        inner.setSpacing(12)
        inner.setAlignment(Qt.AlignCenter)

        self._add_icon = QLabel()
        self._add_icon.setFixedSize(64, 64)
        self._add_icon.setAlignment(Qt.AlignCenter)
        self._add_icon.setText("+")
        inner.addWidget(self._add_icon, 0, Qt.AlignCenter)

        self._add_label = QLabel(QCoreApplication.translate("Nugget", "  Import Files (.tendies)"))
        self._add_label.setAlignment(Qt.AlignCenter)
        self._add_label.setWordWrap(True)
        inner.addWidget(self._add_label)

        return card

    def _create_templates_tab(self) -> QWidget:
        self._templates_scroll = QScrollArea()
        self._templates_scroll.setWidgetResizable(True)
        self._templates_scroll.setFrameStyle(QScrollArea.NoFrame)

        content = QWidget()
        self.templates_layout = QVBoxLayout(content)
        self.templates_layout.setContentsMargins(16, 16, 16, 32)
        self.templates_layout.setSpacing(12)
        self.templates_layout.setAlignment(Qt.AlignTop)
        self._templates_scroll.setWidget(content)

        import_btn = IOSPrimaryButton(QCoreApplication.translate("Nugget", "  Import Templates (.batter)"))
        import_btn.clicked.connect(self.show_add_templates_dialog)
        self.templates_import_btn = import_btn
        self.templates_layout.addWidget(import_btn)

        self.templates_placeholder = QLabel(QCoreApplication.translate("Nugget", "No templates added yet"))
        self.templates_placeholder.setAlignment(Qt.AlignCenter)
        self.templates_layout.addWidget(self.templates_placeholder)

        self._load_templates_list()

        return self._templates_scroll

    def show_add_templates_dialog(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        selected_files, _ = QFileDialog.getOpenFileNames(
            self.window, QCoreApplication.translate("Nugget", "Select Nugget Template Files"), "", "Zip Files (*.batter)"
        )
        if selected_files:
            templates_tweak = tweaks[TweakID.Templates]
            try:
                device_version = self.window.device_manager.get_current_device_version()
            except Exception:
                device_version = None
            for file in selected_files:
                try:
                    templates_tweak.add_template(file, device_version)
                except Exception as e:
                    QMessageBox.warning(self.window, "Import Failed", f"Failed to load template:\n{file}\n\n{str(e)}")
            self._load_templates_list()

    def _load_templates_list(self):
        from src.tweaks.tweaks import tweaks, TweakID
        templates = tweaks[TweakID.Templates].templates
        if not templates:
            self.templates_placeholder.show()
            return
        self.templates_placeholder.hide()

        for i in reversed(range(self.templates_layout.count())):
            widget = self.templates_layout.itemAt(i).widget()
            if widget is not None and widget not in (self.templates_placeholder, self.templates_import_btn):
                widget.deleteLater()

        widgets = {}
        for template in templates:
            template.create_ui(self.window, tweaks[TweakID.Templates], widgets, self.templates_layout)

    def _create_video_tab(self) -> QWidget:
        c = ColorThemeManager.instance().colors
        self._video_scroll = QScrollArea()
        self._video_scroll.setWidgetResizable(True)
        content = QWidget()
        self._video_scroll.setWidget(content)

        v_layout = QVBoxLayout(content)
        v_layout.setContentsMargins(16, 16, 16, 32)
        v_layout.setSpacing(16)

        self._video_labels = []

        thumb_row = QHBoxLayout()
        thumb_label = QLabel(QCoreApplication.translate("Nugget", "Thumbnail"))
        self._video_labels.append(thumb_label)
        self.thumb_btn = QPushButton(QCoreApplication.translate("Nugget", "Choose Freeze Frame (.HEIC)"))
        self.thumb_btn.setCursor(Qt.PointingHandCursor)
        self.thumb_btn.clicked.connect(self.on_choose_thumb_clicked)
        thumb_row.addWidget(thumb_label)
        thumb_row.addWidget(self.thumb_btn, 1)
        v_layout.addLayout(thumb_row)

        video_row = QHBoxLayout()
        video_label = QLabel(QCoreApplication.translate("Nugget", "Video"))
        self._video_labels.append(video_label)
        self.video_btn = QPushButton(QCoreApplication.translate("Nugget", "Choose Video"))
        self.video_btn.setCursor(Qt.PointingHandCursor)
        self.video_btn.clicked.connect(self.on_choose_video_clicked)
        video_row.addWidget(video_label)
        video_row.addWidget(self.video_btn, 1)
        v_layout.addLayout(video_row)

        v_layout.addWidget(QLabel(QCoreApplication.translate("Nugget", "Options")))
        self.loop_chk = QCheckBox(QCoreApplication.translate("Nugget", "Loop (use CoreAnimation method)"))
        self.loop_chk.setChecked(tweaks[TweakID.PosterBoard].loop_video)
        self.loop_chk.toggled.connect(self.on_loop_toggled)
        v_layout.addWidget(self.loop_chk)

        self.reverse_chk = QCheckBox(QCoreApplication.translate("Nugget", "Reverse on Loop"))
        self.reverse_chk.setChecked(tweaks[TweakID.PosterBoard].reverse_video)
        self.reverse_chk.toggled.connect(self.on_reverse_toggled)
        v_layout.addWidget(self.reverse_chk)

        self.foreground_chk = QCheckBox(QCoreApplication.translate("Nugget", "Make Foreground (hides clock)"))
        self.foreground_chk.setChecked(tweaks[TweakID.PosterBoard].use_foreground)
        self.foreground_chk.toggled.connect(self.on_foreground_toggled)
        v_layout.addWidget(self.foreground_chk)

        calc_row = QHBoxLayout()
        calc_label = QLabel(QCoreApplication.translate("Nugget", "Calculation Mode"))
        self._video_labels.append(calc_label)
        self.calc_mode_drp = QComboBox()
        self.calc_mode_drp.addItem(QCoreApplication.translate("Nugget", "Linear"))
        self.calc_mode_drp.addItem(QCoreApplication.translate("Nugget", "Discrete"))
        self.calc_mode_drp.setCurrentIndex(0 if tweaks[TweakID.PosterBoard].calculationMode == 'linear' else 1)
        self.calc_mode_drp.activated.connect(self.on_calc_mode_selected)
        calc_row.addWidget(calc_label)
        calc_row.addWidget(self.calc_mode_drp, 1)
        v_layout.addLayout(calc_row)

        export_btn = IOSPrimaryButton(QCoreApplication.translate("Nugget", "Export Video Loop (.tendies)"))
        export_btn.clicked.connect(self.on_export_video_clicked)
        v_layout.addWidget(export_btn)

        ext_row = QHBoxLayout()
        discover_btn = IOSPrimaryButton(QCoreApplication.translate("Nugget", "Discover Wallpapers"))
        discover_btn.clicked.connect(self.on_discover_wallpapers)
        help_btn = IOSPrimaryButton(QCoreApplication.translate("Nugget", "Help"))
        help_btn.clicked.connect(self.on_help)
        ext_row.addWidget(discover_btn)
        ext_row.addWidget(help_btn)
        v_layout.addLayout(ext_row)

        v_layout.addStretch()

        self._update_video_labels()

        return self._video_scroll

    def _update_video_labels(self):
        pb = tweaks[TweakID.PosterBoard]
        thumb = pb.videoThumbnail if pb.videoThumbnail else None
        video = pb.videoFile if pb.videoFile else None
        self.thumb_btn.setText(QCoreApplication.translate("Nugget", "Choose Freeze Frame (.HEIC)") if not thumb else thumb)
        self.video_btn.setText(QCoreApplication.translate("Nugget", "Choose Video") if not video else video)
        self.reverse_chk.setVisible(pb.loop_video)
        self.foreground_chk.setVisible(pb.loop_video)

    def on_choose_thumb_clicked(self):
        from PySide6.QtWidgets import QFileDialog
        selected_file, _ = QFileDialog.getOpenFileName(
            self.window, QCoreApplication.translate("Nugget", "Select Image File"), "", "Image Files (*.heic)"
        )
        pb = tweaks[TweakID.PosterBoard]
        if selected_file:
            pb.videoThumbnail = selected_file
        else:
            pb.videoThumbnail = None
        self._update_video_labels()

    def on_choose_video_clicked(self):
        from PySide6.QtWidgets import QFileDialog
        selected_file, _ = QFileDialog.getOpenFileName(
            self.window, QCoreApplication.translate("Nugget", "Select Video File"), "", "Video Files (*.mov *.mp4 *.mkv)"
        )
        pb = tweaks[TweakID.PosterBoard]
        if selected_file:
            pb.videoFile = selected_file
        else:
            pb.videoFile = None
        self._update_video_labels()

    def on_loop_toggled(self, checked: bool):
        tweaks[TweakID.PosterBoard].loop_video = checked
        self.reverse_chk.setVisible(checked)
        self.foreground_chk.setVisible(checked)

    def on_reverse_toggled(self, checked: bool):
        tweaks[TweakID.PosterBoard].reverse_video = checked

    def on_foreground_toggled(self, checked: bool):
        tweaks[TweakID.PosterBoard].use_foreground = checked

    def on_calc_mode_selected(self, index: int):
        tweaks[TweakID.PosterBoard].calculationMode = 'linear' if index == 0 else 'discrete'

    def on_export_video_clicked(self):
        import uuid
        import subprocess
        from shutil import make_archive, rmtree
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        directory = QFileDialog.getExistingDirectory(
            self.window, QCoreApplication.translate("Nugget", "Select Directory"), "",
            QFileDialog.ShowDirsOnly)
        if not directory:
            return
        try:
            path = os.path.join(directory, f"Nugget-Export-{uuid.uuid4()}")
            tweaks[TweakID.PosterBoard].create_video_loop_files(output_dir=path)
            zip_path = path + ".tendies"
            make_archive(path, 'zip', path)
            os.rename(path + '.zip', zip_path)
            rmtree(path)
            print(f"Created at {zip_path}")
            if os.name == 'nt':
                subprocess.Popen(f'explorer "{os.path.normpath(zip_path)}"')
            else:
                subprocess.call(["open", '-R', zip_path])
        except Exception as e:
            QMessageBox.critical(
                self.window, QCoreApplication.translate("QtCore.QCoreApplication", "Error!"),
                type(e).__name__ + ": " + repr(e))

    def on_discover_wallpapers(self):
        self.open_wallpaper_downloader()

    def open_wallpaper_downloader(self):
        from src.gui.dialogs.wallpaper_downloader import WallpaperDownloaderDialog
        dialog = WallpaperDownloaderDialog(self.window, self)
        dialog.exec()

    def on_help(self):
        from src.gui.dialogs import PBHelpDialog
        dialog = PBHelpDialog()
        dialog.exec()

    def show_add_tendies_dialog(self):
        from PySide6.QtWidgets import QFileDialog
        selected_files, _ = QFileDialog.getOpenFileNames(
            self.window, QCoreApplication.translate("Nugget", "Select PosterBoard Files"), "", "Zip Files (*.tendies)"
        )
        if selected_files:
            for file in selected_files:
                if not tweaks[TweakID.PosterBoard].add_tendie(file):
                    break
            self.refresh_tendies()

    def showEvent(self, event):
        super().showEvent(event)
        # Sync the delivery-mode checkboxes with the tweak state.
        try:
            from src.tweaks.tweak_loader import tweaks, TweakID
            pb = tweaks.get(TweakID.PosterBoard)
            if pb is not None:
                for chk, configs in ((self._mode_descriptors, False),
                                     (self._mode_configs, True)):
                    chk.blockSignals(True)
                    chk.setChecked(bool(pb.use_configs) == configs)
                    chk.blockSignals(False)
                if hasattr(self, "_config_card"):
                    self._config_card.setVisible(bool(pb.use_configs))
                self._refresh_saved_ids()
        except Exception:
            pass
        # Cards/widgets created since the last pass (tendies, template
        # previews) pick up the active palette, Full Nugget dark included.
        self._retheme()

    def _on_mode_toggled(self, configs: bool, state):
        # Called from checkable QPushButtons (segmented) — state is True
        # when the button was clicked. Also tolerates the old QCheckBox
        # CheckState for safety.
        if isinstance(state, bool):
            if not state:
                return
        else:
            # stateChanged delivers Qt.CheckState (an enum, not an int, in
            # PySide6 6.x) — normalise via .value so the int comparison holds.
            if getattr(state, "value", state) != 2:  # Qt.CheckState.Checked
                return  # the paired handler re-checks the other box
        try:
            from src.tweaks.tweak_loader import tweaks, TweakID
            pb = tweaks.get(TweakID.PosterBoard)
            if pb is not None:
                pb.use_configs = bool(configs)
            # Segmented behavior: exactly one side checked.
            me = self._mode_configs if configs else self._mode_descriptors
            other = self._mode_descriptors if configs else self._mode_configs
            me.blockSignals(True)
            me.setChecked(True)
            me.blockSignals(False)
            other.blockSignals(True)
            other.setChecked(False)
            other.blockSignals(False)
            if hasattr(self, "_config_card"):
                self._config_card.setVisible(bool(configs))
        except Exception:
            pass

    # -- configurations-mode database tools (moved from Settings) --------
    def _on_pb_get_db(self):
        from src.gui.dialogs import PosterBoardDBWizard
        current = self.window.device_manager.data_singleton.current_device
        if current is None:
            QMessageBox.warning(
                self, QCoreApplication.translate("Nugget", "Get Database"),
                QCoreApplication.translate("QCoreApplication", "Please connect a device."))
            return
        wizard = PosterBoardDBWizard(current.udid, self.pb_db_lbl, self._refresh_saved_ids)
        wizard.exec()

    def _on_pb_select_db(self):
        from PySide6.QtWidgets import QFileDialog as FD
        selected_file, _ = FD.getOpenFileName(
            self, QCoreApplication.translate("Nugget", "Select PBFPosterExtensionDataStoreSQLiteDatabase File"),
            "", "*.sqlite3", options=FD.ReadOnly)
        if selected_file in (None, ""):
            tweaks[TweakID.PosterBoard].config_manager.database = None
            self.pb_db_lbl.setText(
                QCoreApplication.translate("Nugget", "Database: none selected"))
        else:
            if not tweaks[TweakID.PosterBoard].config_manager.update_database_file(
                    selected_file, self.window.device_manager.get_current_device_udid()):
                QMessageBox.critical(
                    self, QCoreApplication.translate("QtCore.QCoreApplication", "Error!"),
                    QCoreApplication.translate("Nugget", "The database is not of the correct format!"))
                return
            self.pb_db_lbl.setText(
                QCoreApplication.translate("Nugget", "Database: selected"))

    def _refresh_saved_ids(self):
        if not hasattr(self, "saved_ids_list"):
            return
        self.saved_ids_list.clear()
        saved_ids = tweaks[TweakID.PosterBoard].config_manager.saved_items
        if len(saved_ids) == 0:
            self.saved_ids_list.setEnabled(False)
            self.saved_ids_list.addItem(QCoreApplication.translate("MainWindow", "None"))
        else:
            self.saved_ids_list.setEnabled(True)
            self.saved_ids_list.addItems([item.to_str() for item in saved_ids])

    def _on_clear_saved_ids(self):
        confirm = QMessageBox.question(
            self, QCoreApplication.translate("Nugget", "Clear Saved IDs"),
            QCoreApplication.translate("Nugget", "Clear all saved configuration IDs?"))
        if confirm != QMessageBox.StandardButton.Yes:
            return
        tweaks[TweakID.PosterBoard].config_manager.saved_items.clear()
        self._refresh_saved_ids()

    def _on_remove_selected_id(self):
        curr_row = self.saved_ids_list.currentRow()
        if curr_row >= 0 and len(tweaks[TweakID.PosterBoard].config_manager.saved_items) > 0:
            tweaks[TweakID.PosterBoard].config_manager.saved_items.pop(curr_row)
            self._refresh_saved_ids()

    def refresh_tendies(self):
        for reply, *_ in self._tendie_preview_replies:
            reply.abort()
        self._tendie_preview_replies = []

        keep = (self.add_tendies_card, self.download_card)
        for i in reversed(range(self.tendies_grid.count())):
            widget = self.tendies_grid.itemAt(i).widget()
            if widget and widget not in keep:
                widget.deleteLater()

        tendies = tweaks[TweakID.PosterBoard].tendies
        if not tendies:
            self.tendies_grid.addWidget(self.download_card, 0, 0, 1, 2)
            self.tendies_grid.addWidget(self.add_tendies_card, 1, 0)
            return

        row = 1
        col = 0
        for tendie in tendies:
            card = self._create_tendie_card(tendie)
            self.tendies_grid.addWidget(card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        self.tendies_grid.addWidget(self.add_tendies_card, row, col)

    def _tendie_card_size(self, name_text: str = ""):
        """(card size, name-label height) for the Tendies grid.

        The height is computed from the real content — 80 px icon, the
        name wrapped at the card's real text width (measured with the
        label's own font metrics, up to three lines), the action-chip
        row — instead of the old fixed 140x160 box, whose contents
        added up to ~182 px and clipped the names (user report
        2026-10-22: the Tendies/Templates/Video box text looked
        broken).
        """
        from PySide6.QtGui import QFont, QFontMetrics
        font = QFont()
        font.setPixelSize(13)
        fm = QFontMetrics(font)
        if name_text:
            rect = fm.boundingRect(
                QRect(0, 0, 150 - 16, 10000),
                int(Qt.TextFlag.TextWordWrap), name_text)
            name_h = min(rect.height(), fm.height() * 3)
        else:
            name_h = fm.height() * 2
        height = 8 + 80 + 8 + name_h + 8 + 34 + 8
        return QSize(150, height), name_h

    def _create_tendie_card(self, tendie) -> QWidget:
        c = self._palette()
        dark = self._full_nugget
        card = IOSCard(glass=True)
        display_name = tendie.name.replace(".tendies", "")
        card_size, name_h = self._tendie_card_size(display_name)
        card.setFixedSize(card_size)
        card.setCursor(Qt.PointingHandCursor)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(8, 8, 8, 8)
        inner.setSpacing(8)
        inner.setAlignment(Qt.AlignTop)

        icon = QLabel()
        icon.setFixedSize(80, 80)
        icon.setAlignment(Qt.AlignCenter)
        # Placeholder behind a missing preview: frosted chip on the
        # glass card (dark chip in the Full Nugget interface).
        icon_fallback = (
            f"background-color: {c.surface_hover}; border-radius: 20px;"
            if dark else
            "background-color: #EEF3FA;"
            " border-radius: 20px;")
        try:
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(tendie.get_icon())
            if not pixmap.isNull():
                icon.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                icon.setStyleSheet(icon_fallback)
        except Exception:
            icon.setStyleSheet(icon_fallback)
        inner.addWidget(icon, 0, Qt.AlignCenter)

        self._load_tendie_preview_by_name(card, icon, tendie.name)

        name = QLabel(display_name)
        name.setStyleSheet(
            f"font-size: 13px; color: {c.text_secondary}; text-align: center;"
            if dark else
            "font-size: 13px; color: #374151;"
            " text-align: center; background: transparent;")
        # Top-anchored: AlignCenter also centers VERTICALLY in Qt, so
        # an over-long name overflowed the label's top AND bottom.
        name.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        name.setWordWrap(True)
        # Pin the label to the card's content width: left to the box
        # layout it collapses to its own sizeHint (measured live: 80 px
        # — the icon's width), so names wrapped far too early and the
        # measured two lines were really four. The card height above
        # was computed for exactly this width.
        name.setFixedWidth(card_size.width() - 16)
        # The card height was computed for exactly this label height,
        # so the name wraps inside its slot instead of pushing the
        # action chips out of the card.
        name.setFixedHeight(name_h)
        inner.addWidget(name)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        actions.setContentsMargins(0, 0, 0, 0)

        # Action chips on the glass card: frosted white (dark palette
        # chips in the Full Nugget interface).
        if dark:
            chip_qss = (
                f"QToolButton {{ background-color: {c.bg_secondary}; color: {c.accent}; "
                f"border: 1px solid {c.border}; border-radius: 20px; padding: 7px; }}"
                f"QToolButton:hover {{ background-color: {c.scrollbar_pressed}; }}")
            del_qss = (
                f"QToolButton {{ background-color: {c.bg_secondary}; color: {c.error}; "
                f"border: 1px solid {c.border}; border-radius: 20px; padding: 7px; }}"
                f"QToolButton:hover {{ background-color: {c.error}; color: {c.text_inverse}; }}")
        else:
            chip_qss = (
                "QToolButton { background-color: #F1F4F8;"
                " border: 1px solid #DEE5EE;"
                " border-radius: 12px; padding: 7px; }"
                "QToolButton:hover { background-color: #E4E9F0; }")
            del_qss = (
                "QToolButton { background-color: #F1F4F8;"
                " border: 1px solid #DEE5EE;"
                " border-radius: 12px; padding: 7px; }"
                "QToolButton:hover { background-color: rgba(229, 72, 77, 0.85); }")

        preview_btn = QToolButton()
        preview_btn.setIconSize(QSize(18, 18))
        preview_btn.setIcon(QIcon(":/icon/wallpaper.svg"))
        preview_btn.setToolTip(QCoreApplication.translate(
            "Nugget", "Lock screen preview"))
        preview_btn.setCursor(Qt.PointingHandCursor)
        preview_btn.setStyleSheet(chip_qss)
        preview_btn.clicked.connect(
            lambda: self._show_tendie_preview(tendie))
        actions.addWidget(preview_btn)

        del_btn = QToolButton()
        del_btn.setIconSize(QSize(18, 18))
        from PySide6.QtGui import QIcon as _QIcon
        del_btn.setIcon(_QIcon(":/icon/trash.svg"))
        del_btn.setStyleSheet(del_qss)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(lambda: self._delete_tendie(tendie))
        actions.addWidget(del_btn)
        inner.addLayout(actions)

        return card

    def _show_tendie_preview(self, tendie):
        from src.gui.dialogs.tendie_preview_dialog import TendiePreviewDialog
        TendiePreviewDialog(tendie, self).exec()

    def _load_tendie_preview_by_name(self, card, icon_lbl, file_name):
        try:
            from src.controllers.wallpaper_api import (
                find_wallpaper_by_name, cached_preview_path,
            )
            wp = find_wallpaper_by_name(file_name)
        except Exception:
            return
        if wp is None:
            return
        path = cached_preview_path(wp.preview_url)
        if os.path.exists(path):
            self._set_tendie_thumbnail(icon_lbl, path)
            return
        reply = self._tendie_nam.get(QNetworkRequest(QUrl(wp.preview_url)))
        self._tendie_preview_replies.append((reply, card, icon_lbl, path))
        reply.finished.connect(
            lambda r=reply, c=card, il=icon_lbl, p=path:
                self._on_tendie_preview(r, c, il, p))

    def _on_tendie_preview(self, reply, card, icon_lbl, path):
        self._tendie_preview_replies = [
            (r, c, i, p) for (r, c, i, p) in self._tendie_preview_replies
            if r is not reply]
        data = bytes(reply.readAll())
        reply.deleteLater()
        if reply.error() != QNetworkReply.NetworkError.NoError or not data:
            return
        if not self._widget_is_valid(icon_lbl):
            return
        try:
            with open(path, "wb") as f:
                f.write(data)
        except OSError:
            return
        self._set_tendie_thumbnail(icon_lbl, path)

    def _set_tendie_thumbnail(self, icon_lbl, path):
        if not self._widget_is_valid(icon_lbl):
            return
        try:
            image = QImageReader(path).read()
            pixmap = QPixmap.fromImage(image) if not image.isNull() else QPixmap(path)
            if pixmap.isNull():
                return
            scaled = pixmap.scaled(
                80, 80, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (scaled.width() - 80) // 2
            y = (scaled.height() - 80) // 2
            icon_lbl.setPixmap(scaled.copy(x, y, 80, 80))
        except Exception:
            pass

    def _widget_is_valid(self, widget) -> bool:
        import shiboken6
        try:
            return shiboken6.isValid(widget)
        except RuntimeError:
            return False

    def _delete_tendie(self, tendie):
        from src.tweaks.tweaks import tweaks, TweakID
        if tendie in tweaks[TweakID.PosterBoard].tendies:
            tweaks[TweakID.PosterBoard].tendies.remove(tendie)
        self.refresh_tendies()

    def _reset_posterboard(self):
        c = self._palette()
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QLabel, QCheckBox, QDialogButtonBox, QMessageBox,
        )

        dialog = QDialog(self.window)
        dialog.setWindowTitle(QCoreApplication.translate("Nugget", "Reset PosterBoard"))
        dialog.setMinimumWidth(350)
        dialog.setStyleSheet(f"""
            QDialog {{ background-color: {c.bg_primary}; }}
            QLabel {{ color: {c.text_primary}; font-size: 15px; }}
            QCheckBox {{ color: {c.text_primary}; font-size: 14px; spacing: 8px; }}
            QCheckBox::indicator {{ width: 20px; height: 20px; }}
            QDialogButtonBox QPushButton {{
                background-color: {c.accent};
                border-radius: 20px;
                color: {c.text_primary};
                font-size: 14px;
                font-weight: 600;
                padding: 10px 20px;
                border: none;
                min-width: 80px;
            }}
            QDialogButtonBox QPushButton:hover {{ background-color: {c.accent_hover}; }}
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        desc = QLabel(QCoreApplication.translate(
            "Nugget",
            "If a wallpaper misbehaves after an apply, reset the items "
            "below and apply again — the descriptors are cleared and "
            "PosterBoard rebuilds its store itself. \"Everything\" clears "
            "the whole descriptor store."
        ))
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {c.text_secondary}; font-size: 13px;")
        layout.addWidget(desc)

        reset_all = QCheckBox(QCoreApplication.translate(
            "Nugget", "Everything — all PosterBoard descriptors"))
        reset_all.setChecked(False)
        layout.addWidget(reset_all)

        reset_collections = QCheckBox(QCoreApplication.translate("Nugget", "Collections"))
        reset_collections.setChecked(True)
        layout.addWidget(reset_collections)

        reset_suggested = QCheckBox(QCoreApplication.translate("Nugget", "Suggested Photos"))
        reset_suggested.setChecked(True)
        layout.addWidget(reset_suggested)

        reset_gallery = QCheckBox(QCoreApplication.translate("Nugget", "Gallery Cache"))
        reset_gallery.setChecked(True)
        layout.addWidget(reset_gallery)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        if dialog.exec() == QDialog.Accepted:
            if reset_all.isChecked():
                tweaks[TweakID.PosterBoard].resetModes = ["All"]
                QMessageBox.information(
                    self.window,
                    QCoreApplication.translate("Nugget", "Reset Scheduled"),
                    QCoreApplication.translate(
                        "Nugget",
                        "A full PosterBoard descriptor reset has been "
                        "scheduled. All delivered wallpapers will be cleared "
                        "on the next apply. Apply your tweaks to execute "
                        "the reset."))
                return
            selected = []
            if reset_collections.isChecked():
                selected.append("Collections")
            if reset_suggested.isChecked():
                selected.append("Suggested Photos")
            if reset_gallery.isChecked():
                selected.append("Gallery Cache")
            tweaks[TweakID.PosterBoard].resetModes = selected
            QMessageBox.information(
                self.window,
                QCoreApplication.translate("Nugget", "Reset Scheduled"),
                QCoreApplication.translate(
                    "Nugget",
                    "PosterBoard reset has been scheduled. The selected items "
                    "will be cleared on the next apply. Apply your tweaks to "
                    "execute the reset.")
            )
