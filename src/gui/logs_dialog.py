"""WorkSlop Logs — live viewer for the app's real session log.

User order 2026-10-20: a "WorkSlop Logs" button beside Cancel Apply on
Home. The viewer shows what WorkSlop is actually doing, in real time, and
the text can be copied or saved so the user can send the log when an
error happens.

Honest wiring: the text comes from the app's real logging pipeline —
the session file written by ``src/controllers/nugget_logger.py`` (the
same file the crash handler tails) seeds the view, and a logging handler
attached to the root logger and the ``WorkSlop`` logger streams new
records in live while the dialog is open. Nothing here is simulated.
"""

from __future__ import annotations

import logging
import os

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
    QVBoxLayout,
)

from src.controllers.nugget_logger import get_log_path, get_log_tail, init_logging

# Seed size: enough history for a bug report without loading megabytes.
_SEED_CHARS = 512 * 1024


class _LogBridge(QObject):
    """Queued signal hop: logging runs on worker threads, widgets don't."""

    record = Signal(str)


class _QtLogHandler(logging.Handler):
    def __init__(self, bridge: _LogBridge):
        super().__init__(level=logging.DEBUG)
        self._bridge = bridge
        self.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._bridge.record.emit(self.format(record))
        except Exception:
            pass  # logging must never take the app down


class WorkSlopLogsDialog(QDialog):
    """Modeless live log viewer (stays open while tweaks are applied)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WorkSlop Logs")
        self.setModal(False)
        self.resize(880, 580)
        self.setMinimumSize(560, 360)

        # Make sure the session log exists before we point at it.
        init_logging()
        self._log_path = get_log_path()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        path_lbl = QLabel(f"Log file: {self._log_path}", self)
        path_lbl.setStyleSheet(
            "background: transparent; color: #5B6472; font-size: 12px;")
        path_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(path_lbl)

        self._view = QPlainTextEdit(self)
        self._view.setReadOnly(True)
        self._view.setFont(
            QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self._view.setStyleSheet(
            "QPlainTextEdit { background-color: #0F172A; color: #E2E8F0;"
            " border: 1px solid #E2E8F0; border-radius: 10px;"
            " font-size: 12px; padding: 8px; }")
        # Keep the in-view buffer bounded; the full log stays in the file.
        self._view.setMaximumBlockCount(8000)
        layout.addWidget(self._view, 1)

        seed = get_log_tail(_SEED_CHARS)
        if seed:
            self._view.setPlainText(seed.rstrip("\n"))
            self._scroll_to_bottom()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        copy_btn = QPushButton("Copy Logs", self)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(self._on_copy)
        save_btn = QPushButton("Save Logs…", self)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        close_btn = QPushButton("Close", self)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        for b in (copy_btn, save_btn, close_btn):
            b.setFixedHeight(38)
            b.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    border: 1px solid #D9E0EA;
                    border-radius: 10px;
                    color: #111827;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 0 16px;
                }
                QPushButton:hover { background-color: #F0F3F8; }
                QPushButton:pressed { background-color: #E4E9F0; }
            """)
        btn_row.addWidget(copy_btn)
        btn_row.addWidget(save_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)
        self._copy_btn = copy_btn

        # Live stream: root catches almost everything; "WorkSlop" has
        # propagate=False (see nugget_logger) so it needs its own hook.
        self._bridge = _LogBridge(self)
        self._bridge.record.connect(self._append_record)
        self._handler = _QtLogHandler(self._bridge)
        self._loggers = [logging.getLogger(), logging.getLogger("WorkSlop")]
        for lg in self._loggers:
            lg.addHandler(self._handler)

    # -- live feed ------------------------------------------------------
    def _append_record(self, text: str) -> None:
        bar = self._view.verticalScrollBar()
        at_bottom = bar.value() >= bar.maximum() - 4
        self._view.appendPlainText(text)
        if at_bottom:
            self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        bar = self._view.verticalScrollBar()
        bar.setValue(bar.maximum())

    # -- actions --------------------------------------------------------
    def _on_copy(self) -> None:
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._view.toPlainText())
        self._copy_btn.setText("Copied ✓")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self._copy_btn.setText("Copy Logs"))

    def _on_save(self) -> None:
        default = os.path.basename(self._log_path) or "workslop-logs.txt"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save WorkSlop Logs", default,
            "Log files (*.log *.txt);;All files (*)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._view.toPlainText())

    # -- lifecycle ------------------------------------------------------
    def closeEvent(self, event) -> None:
        for lg in self._loggers:
            try:
                lg.removeHandler(self._handler)
            except Exception:
                pass
        super().closeEvent(event)
