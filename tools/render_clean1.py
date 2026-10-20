#!/usr/bin/env python3
"""Render clean-light UI ronde 1 (offscreen).

Real MainWindow, isolated QSettings. Navigates by clicking the actual
sidebar rail buttons (like a user), never the on_* handlers directly.

Screens: home, liquidglass, posterboard, iconthemes, settings.
Filenames carry a timestamp so they can never be a stale cache hit.
"""
import os
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="workslop-clean1-")

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])
app.setApplicationName("WorkSlop Desktop")

# No usbmuxd here: device refresh ends in a modal error dialog;
# auto-dismiss it like a user would.
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


def settle(ms=350):
    QTimer.singleShot(ms, app.quit)
    app.exec()


def grab(tag):
    app.processEvents()
    name = f"clean1-{STAMP}-{tag}.png"
    path = os.path.join(OUT, name)
    ok = win.grab().save(path)
    print(("saved " if ok else "FAILED ") + path)


# ---- 1. Home -----------------------------------------------------------
win.show_home()
settle()
grab("home")

# ---- 2. Liquid Glass ---------------------------------------------------
win.topnav._buttons["liquidglass"].click()
settle()
grab("liquidglass")

# ---- 3. PosterBoard ----------------------------------------------------
win.topnav._buttons["posterboard"].click()
settle()
grab("posterboard")

# ---- 4. Icon Themes ----------------------------------------------------
win.topnav._buttons["iconthemes"].click()
settle()
grab("iconthemes")

# ---- 5. Settings -------------------------------------------------------
win.siderail._buttons["settings"].click()
settle()
grab("settings")

print("Done.")
