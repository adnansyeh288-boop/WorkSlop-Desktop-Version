#!/usr/bin/env python3
"""Offline proof for the Home live-preview wiring (no real device).

Phase A: a fake capture session feeds stage statuses + one PNG frame
         through the REAL ScreenStreamThread into the REAL HomePage —
         the preview must end up LIVE (frame set, status cleared), and
         a second refresh for the same device must NOT restart it.
Phase B: disconnect clears the frame and stops the thread.
Phase C: the REAL capture path with a tunnel whose aopen() hangs —
         the new timeout must surface the "timed out" status on the
         preview instead of silence (the field bug: static blue screen
         forever, nothing reported).

Run: QT_QPA_PLATFORM=offscreen python tools/test_stream_preview.py
"""
import asyncio
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="workslop-stream-")

from PySide6.QtCore import QBuffer, QIODevice, QTimer  # noqa: E402
from PySide6.QtGui import QColor, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

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
from src.devicemanagement import screen_stream  # noqa: E402
from src.devicemanagement.device_manager import DeviceManager  # noqa: E402
from src.gui.main_window import MainWindow  # noqa: E402
from src.gui.pages.pages_list import Page  # noqa: E402

FAILURES = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {extra}" if extra else ""))
    if not cond:
        FAILURES.append(name)


def pump(seconds):
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.02)


def make_png():
    img = QImage(360, 740, QImage.Format.Format_RGB32)
    img.fill(QColor("#7C3AED"))
    p = QPainter(img)
    p.setPen(QColor("white"))
    p.drawText(60, 360, "SYNTHETIC TEST FRAME")
    p.end()
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.ReadWrite)
    img.save(buf, "PNG")
    return bytes(buf.data())


win = MainWindow(device_manager=DeviceManager(),
                 translator=Translator(app, Settings()))
win.resize(1240, 820)
win.show()
pump(0.6)
home = win.pages[Page.Home]
preview = home._preview
check("preview widget exists", preview is not None)

dm = win.device_manager
REAL_UDID = ["FAKE-UDID-1234"]
dm.get_current_device_udid = lambda: REAL_UDID[0]
dm.get_current_device_version = lambda: "26.6.1"

# ---------------------------------------------------------------- Phase A
real_capture_once = screen_stream._capture_once


async def fake_capture(udid, version, emit_frame, emit_status, stop):
    emit_status("Live preview: opening USB tunnel…")
    await asyncio.sleep(0.05)
    emit_status("Live preview: starting screen channel…")
    await asyncio.sleep(0.05)
    emit_frame(make_png())
    while not stop.is_set():
        await asyncio.sleep(0.05)


screen_stream._capture_once = fake_capture
home.refresh_preview(model_id="iPhone17,1", name="Test iPhone",
                     info="iOS 26.6.1 (23G82)")
pump(1.5)
check("A: stream thread created", home._stream is not None)
check("A: stream thread running",
      home._stream is not None and home._stream.isRunning())
check("A: preview holds a live frame",
      preview._frame is not None and not preview._frame.isNull())
check("A: status cleared once live", preview._stream_status == "",
      f"status={preview._stream_status!r}")
first_thread = home._stream
grab = os.path.expanduser(
    "~/workspace/stream-preview-frame-%s.png" % time.strftime("%H%M%S"))
preview.grab().save(grab)
print("saved preview grab:", grab)

home.refresh_preview(model_id="iPhone17,1", name="Test iPhone",
                     info="iOS 26.6.1 (23G82)")
pump(0.4)
check("A: same-device refresh does NOT restart the stream",
      home._stream is first_thread and home._stream.isRunning())

# ---------------------------------------------------------------- Phase B
REAL_UDID[0] = ""
home.refresh_preview(name="", info="")
pump(1.0)
check("B: stream stopped on disconnect", home._stream is None)
check("B: frame cleared on disconnect", preview._frame is None)

# ---------------------------------------------------------------- Phase C
screen_stream._capture_once = real_capture_once
screen_stream._TUNNEL_OPEN_TIMEOUT = 0.4

import pymobiledevice3.remote.userspace_tunnel as ust  # noqa: E402


class HangingTunnel:
    def __init__(self, **kwargs):
        pass

    async def aopen(self):
        await asyncio.sleep(60)

    async def aclose(self):
        return None


real_tunnel_cls = ust.UserspaceRsdTunnel
ust.UserspaceRsdTunnel = HangingTunnel
try:
    REAL_UDID[0] = "FAKE-UDID-1234"
    statuses = []
    home.refresh_preview(model_id="iPhone17,1", name="Test iPhone",
                         info="iOS 26.6.1 (23G82)")
    pump(0.3)
    if home._stream is not None:
        home._stream.status_changed.connect(statuses.append)
    pump(2.5)
    check("C: hanging tunnel produces a status, not silence",
          any("tunnel" in s.lower() for s in statuses),
          f"statuses={statuses!r}")
    check("C: timeout status reaches the preview widget",
          "timed out" in (preview._stream_status or ""),
          f"preview status={preview._stream_status!r}")
finally:
    REAL_UDID[0] = ""
    home.refresh_preview(name="", info="")
    pump(1.0)
    ust.UserspaceRsdTunnel = real_tunnel_cls

print("RESULT:", "ALL PASS" if not FAILURES else f"{len(FAILURES)} FAILURES")
sys.exit(1 if FAILURES else 0)
