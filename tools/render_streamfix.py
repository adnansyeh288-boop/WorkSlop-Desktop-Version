#!/usr/bin/env python3
"""Fresh Home render after the live-preview stream fix (no device)."""
import os, sys, tempfile
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="workslop-sf-")
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
app = QApplication([]); app.setApplicationName("WorkSlop Desktop")
_k = QTimer(); _k.timeout.connect(lambda: (QApplication.activeModalWidget().close() if QApplication.activeModalWidget() is not None else None)); _k.start(50)
import src.qt.resources_rc  # noqa
from src.controllers.settings import Settings
from src.controllers.translator import Translator
from src.devicemanagement.device_manager import DeviceManager
from src.gui.main_window import MainWindow
win = MainWindow(device_manager=DeviceManager(), translator=Translator(app, Settings()))
win.resize(1240, 820); win.show(); app.processEvents()
win.show_home()
QTimer.singleShot(400, app.quit); app.exec()
out = os.path.expanduser("~/workspace/home-streamfix-%s.png" % datetime.now().strftime("%H%M%S"))
win.grab().save(out); print("saved", out)
