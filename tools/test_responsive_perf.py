#!/usr/bin/env python3
"""Responsive text + GUI-thread performance checks (2026-10-21 batch).

1. Home social boxes scale their font with the box width.
2. PosterBoard scales its tab/import text with the page width.
3. _sync_stream NEVER blocks the GUI thread on a stubborn stream
   (the post-apply freeze: stop used to wait up to 4 s inline).
4. Page-switch timings are printed for the record.
"""
import os, re, sys, tempfile, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="workslop-rp-")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QToolButton
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

win = MainWindow(device_manager=DeviceManager(), translator=Translator(app, Settings()))
win.show()
results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond), extra))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))


def pump(ms):
    end = time.time() + ms / 1000
    while time.time() < end:
        app.processEvents()
        time.sleep(0.01)


def font_px(widget):
    m = re.search(r"font-size:\s*(\d+)px", widget.styleSheet())
    return int(m.group(1)) if m else None


# ---- 1. social boxes scale with window width -------------------------
from src.gui.pages.pages_list import Page
home = win.pages[Page.Home]
win.show_home()
social = [b for b in win.findChildren(QToolButton)
          if b.text().startswith("GitHub")]
check("social box found", len(social) == 1)
box = social[0]
win.resize(1000, 700); pump(300)
small = (font_px(box), box.iconSize().width(), box.width())
win.resize(1680, 950); pump(300)
large = (font_px(box), box.iconSize().width(), box.width())
check("social font grows with width", small[0] < large[0],
      f"{small[0]}px@{small[2]}w -> {large[0]}px@{large[2]}w")
check("social icon grows with width", small[1] < large[1],
      f"{small[1]} -> {large[1]}")

# ---- 2. PosterBoard text scale ---------------------------------------
pb = win.ios_posterboard if hasattr(win, "ios_posterboard") else None
if pb is None:
    for attr in dir(win):
        if "poster" in attr.lower():
            pb = getattr(win, attr)
            break
check("posterboard page found", pb is not None)
win.show_ios_page(1)  # PosterBoard index in the clean shell may vary;
# fall back: find the page object among ios_pages stack widgets
try:
    from src.gui.ios.posterboard import IOSPosterboardPage
    if not isinstance(pb, IOSPosterboardPage):
        for i in range(win.ios_pages.count()):
            w = win.ios_pages.widget(i)
            if isinstance(w, IOSPosterboardPage):
                pb = w
                win.ios_pages.setCurrentIndex(i)
                break
except Exception:
    pass
def show_pb(width):
    # Realistic sequence: size the window, then OPEN the page (a page
    # hidden in a QStackedWidget keeps stale geometry until shown).
    win.resize(width, 820); pump(300)
    win.content_stack.setCurrentIndex(0); pump(100)
    win.content_stack.setCurrentIndex(1)
    for i in range(win.ios_pages.count()):
        if win.ios_pages.widget(i) is pb:
            win.ios_pages.setCurrentIndex(i)
    pump(300)
    return font_px(pb.tendies_tab_btn)


tab_narrow = show_pb(1000)
tab_wide = show_pb(1680)
check("posterboard scale reacts", tab_narrow is not None
      and tab_wide is not None and tab_narrow < tab_wide,
      f"tab font {tab_narrow}px @1000w -> {tab_wide}px @1680w")
check("download subtitle wraps", pb._download_subtitle.wordWrap())

# ---- 3. _sync_stream never blocks on a stubborn stream ---------------
import asyncio

import src.devicemanagement.screen_stream as ss_mod

orig_capture = ss_mod._capture_once


async def stubborn(udid, version, emit_frame, emit_status, stop):
    # Ignores the stop flag for ~2.5 s, like a parked tunnel read.
    end = time.time() + 2.5
    while time.time() < end:
        await asyncio.sleep(0.1)


ss_mod._capture_once = stubborn
dm = win.device_manager
state = {"udid": "UDID-AAAA"}
dm.get_current_device_udid = lambda: state["udid"]
dm.get_current_device_version = lambda: "26.6.1"
home._sync_stream()
pump(300)
check("stubborn stream started", home._stream is not None
      and home._stream.isRunning())
state["udid"] = "UDID-BBBB"  # device switch while old stream is parked
t0 = time.time()
home._sync_stream()
elapsed = time.time() - t0
check("_sync_stream returns fast on switch", elapsed < 1.0,
      f"{elapsed:.2f}s (old code waited up to 4s)")
state["udid"] = None
home._sync_stream()
pump(4000)  # old thread exits (~2.5s) + retry cycles clear the refs
check("stream refs cleared after stop", home._stream is None)
ss_mod._capture_once = orig_capture

# ---- 4. page-switch timings (record only) -----------------------------
win.resize(1240, 820)
win.show_home(); pump(100)
n = win.ios_pages.count()
times = []
for i in range(n):
    t0 = time.time()
    win.show_ios_page(i)
    pump(50)
    times.append(int((time.time() - t0) * 1000))
print("page switch ms:", times)
check("no page switch over 2s", all(t < 2000 for t in times),
      f"max {max(times)}ms")

failed = [r for r in results if not r[1]]
print(f"\n{len(results) - len(failed)}/{len(results)} PASS")
sys.exit(1 if failed else 0)
