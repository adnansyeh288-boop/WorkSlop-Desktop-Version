#!/usr/bin/env python3
"""Fresh renders for the responsive-text batch: Home at two window
widths + PosterBoard wide. New timestamped filenames, always."""
import os, sys, tempfile, time
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="workslop-rr-")
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
app = QApplication([]); app.setApplicationName("WorkSlop Desktop")
_k = QTimer(); _k.timeout.connect(
    lambda: (QApplication.activeModalWidget().close()
             if QApplication.activeModalWidget() is not None else None))
_k.start(50)
import src.qt.resources_rc  # noqa
from src.controllers.settings import Settings
from src.controllers.translator import Translator
from src.devicemanagement.device_manager import DeviceManager
from src.gui.main_window import MainWindow
from src.gui.ios.posterboard import IOSPosterboardPage

win = MainWindow(device_manager=DeviceManager(), translator=Translator(app, Settings()))
win.show()
stamp = datetime.now().strftime("%H%M%S")


def pump(ms):
    end = time.time() + ms / 1000
    while time.time() < end:
        app.processEvents()
        time.sleep(0.01)


win.show_home()
win.resize(1000, 700); pump(500)
out1 = os.path.expanduser(f"~/workspace/home-responsive-1000-{stamp}.png")
win.grab().save(out1); print("saved", out1)
win.resize(1680, 950); pump(500)
out2 = os.path.expanduser(f"~/workspace/home-responsive-1680-{stamp}.png")
win.grab().save(out2); print("saved", out2)
for i in range(win.ios_pages.count()):
    if isinstance(win.ios_pages.widget(i), IOSPosterboardPage):
        win.content_stack.setCurrentIndex(1)
        win.ios_pages.setCurrentIndex(i)
        break
pump(500)
out3 = os.path.expanduser(f"~/workspace/posterboard-responsive-1680-{stamp}.png")
win.grab().save(out3); print("saved", out3)
