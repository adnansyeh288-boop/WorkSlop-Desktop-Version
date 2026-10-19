#!/usr/bin/env python3
"""Render ronde-9 dark theme proof screenshots (offscreen).

Real MainWindow, isolated HOME / QSettings. Renders:
* t213100-01-home.png        Home page (dark theme #1e1e1e, white WS icon)
* t213100-02-liquidglass.png Liquid Glass tweaks page (dark)
* t213100-03-iconthemes.png  Icon Themes page (Light/Dark/Tinted)
* t213100-04-settings.png    Settings page (dark)

Run: QT_QPA_PLATFORM=offscreen HOME=<tmp> python tools/render_ronde10_dark.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="workslop-t213100-")

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])
app.setApplicationName("WorkSlop Desktop")

# With no usbmuxd in this environment, device refresh ends in a modal
# "failed to get device list" dialog; auto-dismiss it like a user would.
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

# Output to your_files with unique ronde-9 names (screenshot cache rule).
OUT = os.path.expanduser("~/workspace/your_files/ui-rebuild-r10/")
os.makedirs(OUT, exist_ok=True)

win = MainWindow(device_manager=DeviceManager(),
                 translator=Translator(app, Settings()))
win.resize(1240, 820)
win.show()
app.processEvents()


def grab(name):
    app.processEvents()
    path = os.path.join(OUT, name)
    ok = win.grab().save(path)
    print(("saved " if ok else "FAILED ") + name)
    return path


# ---- 1. Home (dark theme) ---------------------------------------------
win.show_home()
grab("t213100-01-home-dark.png")

# ---- 2. Liquid Glass tweaks -------------------------------------------
win.on_liquidGlassPageBtn_clicked()
grab("t213100-02-liquidglass-dark.png")

# ---- 3. Icon Themes (Light/Dark/Tinted) --------------------------------
win.on_iconThemesPageBtn_clicked()
grab("t213100-03-iconthemes-dark.png")

# ---- 4. Settings -------------------------------------------------------
win.on_settingsPageBtn_clicked()
grab("t213100-04-settings-dark.png")

print("Done.")
