#!/usr/bin/env python3
"""Verify the 2026-10-20 evening batch (offscreen, real MainWindow):

1. Recovery menus renamed + "Guide" (siderail labels).
2. WorkSlop Logs button on Home -> live log dialog: seeded from the real
   session file, streams new records live, copy works.
3. Minimize guard: window minimum size enforced + changeEvent runs.
4. Responsive: renders at 1240x820, at the 1180x740 floor, at 1600x1000,
   plus the Logs dialog itself. Timestamped filenames, never cached.
"""
import logging
import os
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="workslop-batch2-")

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication, QPushButton  # noqa: E402

app = QApplication([])
app.setApplicationName("WorkSlop Desktop")

_modal_killer = QTimer()
_modal_killer.timeout.connect(
    lambda: (QApplication.activeModalWidget().close()
             if QApplication.activeModalWidget() is not None else None))
_modal_killer.start(50)

import src.qt.resources_rc  # noqa: F401,E402
from src.controllers.settings import Settings  # noqa: E402
from src.controllers.translator import Translator  # noqa: E402
from src.devicemanagement.device_manager import DeviceManager  # noqa: E402
from src.gui.main_window import MainWindow  # noqa: E402

STAMP = datetime.now().strftime("%H%M%S")
OUT = os.path.expanduser("~/workspace/your_files/ui-clean-r1/")
os.makedirs(OUT, exist_ok=True)

win = MainWindow(device_manager=DeviceManager(),
                 translator=Translator(app, Settings()))
win.resize(1240, 820)
win.show()
app.processEvents()


def settle(ms=300):
    QTimer.singleShot(ms, app.quit)
    app.exec()


def grab(tag, widget=None):
    app.processEvents()
    name = f"batch2-{STAMP}-{tag}.png"
    path = os.path.join(OUT, name)
    ok = (widget or win).grab().save(path)
    print(("saved " if ok else "FAILED ") + path)


fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


win.show_home()
settle()

# --- 1. Guide labels -----------------------------------------------------
rec_in = win.siderail._buttons["rec_enter"].text()
rec_out = win.siderail._buttons["rec_exit"].text()
print("rec labels:", repr(rec_in), repr(rec_out))
check("rec_enter label + Guide", rec_in == "Recovery Mode Guide")
check("rec_exit label + Guide", rec_out == "Exit Recovery Guide")

# --- 3a. Window floor ----------------------------------------------------
check("minimumSize 1180x740",
      (win.minimumWidth(), win.minimumHeight()) == (1180, 740))
win.resize(400, 300)
app.processEvents()
check("resize below floor blocked",
      win.width() >= 1180 and win.height() >= 740)
win.resize(1240, 820)
app.processEvents()

# --- 3b. changeEvent guard runs ------------------------------------------
from PySide6.QtCore import QEvent, QRect  # noqa: E402
win._pre_minimize_geometry = QRect(60, 60, 1240, 820)
try:
    win.changeEvent(QEvent(QEvent.Type.WindowStateChange))
    check("changeEvent no crash", True)
except Exception as e:
    check(f"changeEvent no crash ({e})", False)

def pump(ms=200):
    """Process events for ~ms without app.exec()/quit() (quit poisons
    later loops in this harness and starved the live-log assertions)."""
    import time
    end = time.time() + ms / 1000.0
    while time.time() < end:
        app.processEvents()


# --- 2. Logs button + dialog ----------------------------------------------
logs_btns = [b for b in win.findChildren(QPushButton)
             if b.text() == "WorkSlop Logs"]
check("WorkSlop Logs button on Home", len(logs_btns) == 1)
logs_btns[0].click()
pump(300)

from src.gui.logs_dialog import WorkSlopLogsDialog  # noqa: E402
dlgs = [w for w in QApplication.topLevelWidgets()
        if isinstance(w, WorkSlopLogsDialog)]
check("logs dialog opened", len(dlgs) == 1)
dlg = dlgs[0]

from src.controllers.nugget_logger import get_log_path  # noqa: E402
check("dialog points at real session log", dlg._log_path == get_log_path())
seed_text = dlg._view.toPlainText()
check("view seeded from session file", len(seed_text) > 0)

logging.getLogger("WorkSlop").info("SMOKE-WS-LOG-123 live record")
logging.getLogger().warning("SMOKE-ROOT-LOG-456 live record")
pump(300)
live_text = dlg._view.toPlainText()
check("live WorkSlop record streamed", "SMOKE-WS-LOG-123" in live_text)
check("live root record streamed", "SMOKE-ROOT-LOG-456" in live_text)

dlg._on_copy()
check("copy puts logs on clipboard",
      "SMOKE-WS-LOG-123" in QApplication.clipboard().text())

grab("logsdialog", dlg)
dlg.close()
app.processEvents()

# --- 4. Responsive renders -------------------------------------------------
grab("home-1240x820")
win.resize(1180, 740)
settle()
grab("home-1180x740-floor")
win.resize(1600, 1000)
settle()
grab("home-1600x1000")
win.resize(1240, 820)

print("RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
