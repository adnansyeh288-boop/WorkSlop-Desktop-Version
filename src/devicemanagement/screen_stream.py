"""Live iPhone screen stream for the Home preview (3uTools-style).

The preview shows the REAL device screen, streamed over USB — never a
mockup. Frames are full screenshots pulled in a loop from the device's
own screenshot services via pymobiledevice3:

  iOS 17.4+  DVT screenshot channel over the in-process *userspace*
             tunnel (``UserspaceRsdTunnel`` — no admin/root needed,
             the same route the pymobiledevice3 CLI prefers), then
             ``Screenshot(DvtProvider(rsd)).get_screenshot()``.
  iOS 17.0–17.3
             Same DVT channel, but those versions predate the
             CoreDeviceProxy service, so the RSD must come from a
             running ``pymobiledevice3 remote tunneld`` (admin).
  iOS < 17   ``com.apple.mobile.screenshotr`` over the normal lockdown
             session (needs the developer image mounted).

Honest limits: every frame is a full screenshot, so the stream runs at
screenshot speed (a few fps), NOT the 30–60 fps of the private
QuickTime-USB video protocol 3uTools uses. The content is the live
screen either way. Developer Mode must be ON for the DVT routes.

All device I/O runs on this QThread's own asyncio loop; the GUI thread
only receives finished frames (bytes) and status strings via signals.
"""
from __future__ import annotations

import asyncio
import logging
import threading

from packaging.version import Version
from PySide6.QtCore import QThread, Signal

from src.devicemanagement.session import (
    install_windows_selector_policy,
    lockdown_session,
)

logger = logging.getLogger("GoldenNugget.screen_stream")

# Minimum seconds between frames; the capture itself is the real limit,
# this only stops a fast device from flooding the GUI thread.
_MIN_FRAME_INTERVAL = 0.12
_RETRY_SECONDS = 3.0


class _StreamFailure(Exception):
    """Capture failure carrying a user-readable status line."""

    def __init__(self, status: str):
        super().__init__(status)
        self.status = status


def _friendly_status(exc: Exception) -> str:
    """Map a capture exception to an honest one-line preview status."""
    name = type(exc).__name__
    msg = str(exc).lower()
    if "developer" in name.lower() or "developer mode" in msg:
        return "Live preview: turn ON Developer Mode on the iPhone"
    if name in ("NotPairedError", "PairingError") or "pair" in msg:
        return "Live preview: tap Trust on the iPhone"
    if name == "UserspaceTunnelUnavailableError":
        return "Live preview: USB tunnel unavailable for this iOS"
    if "screenshotr" in msg or "InvalidService" in name:
        return "Live preview unavailable: developer image not mounted"
    return f"Live preview paused: {name}"


async def _pump_frames(shot, emit_frame, stop: threading.Event) -> None:
    """Pull screenshots from an opened DVT Screenshot channel."""
    while not stop.is_set():
        data = await shot.get_screenshot()
        if data:
            emit_frame(data)
        await asyncio.sleep(_MIN_FRAME_INTERVAL)


async def _capture_dvt_userspace(udid, emit_frame, stop) -> None:
    """iOS 17.4+: DVT screenshot over the root-free userspace tunnel."""
    from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel
    from pymobiledevice3.services.dvt.instruments.dvt_provider import (
        DvtProvider,
    )
    from pymobiledevice3.services.dvt.instruments.screenshot import (
        Screenshot,
    )

    tunnel = UserspaceRsdTunnel(
        serial=udid, autopair=True, remotepairing_fallback=False)
    rsd = await tunnel.aopen()
    try:
        async with DvtProvider(rsd) as dvt, Screenshot(dvt) as shot:
            await _pump_frames(shot, emit_frame, stop)
    finally:
        await tunnel.aclose()


async def _capture_dvt_tunneld(udid, emit_frame, stop) -> None:
    """iOS 17.0–17.3: DVT screenshot over an admin tunneld's RSD."""
    from pymobiledevice3.remote.remote_service_discovery import (
        RemoteServiceDiscoveryService,  # noqa: F401  (type anchor)
    )
    from pymobiledevice3.services.dvt.instruments.dvt_provider import (
        DvtProvider,
    )
    from pymobiledevice3.services.dvt.instruments.screenshot import (
        Screenshot,
    )
    from pymobiledevice3.tunneld.api import (
        TUNNELD_DEFAULT_ADDRESS,
        get_tunneld_devices,
    )

    rsds = await get_tunneld_devices(TUNNELD_DEFAULT_ADDRESS)
    rsd = next((r for r in rsds if r.udid == udid), None)
    for other in rsds:
        if other is not rsd:
            await other.close()
    if rsd is None:
        raise _StreamFailure(
            "Live preview: start 'pymobiledevice3 remote tunneld' "
            "(admin) for iOS 17.0–17.3")
    try:
        async with DvtProvider(rsd) as dvt, Screenshot(dvt) as shot:
            await _pump_frames(shot, emit_frame, stop)
    finally:
        await rsd.close()


async def _capture_screenshotr(udid, emit_frame, stop) -> None:
    """iOS < 17: screenshotr over the normal lockdown session."""
    from pymobiledevice3.services.screenshot import ScreenshotService

    async with lockdown_session(udid) as lockdown:
        svc = ScreenshotService(lockdown)
        try:
            while not stop.is_set():
                data = await svc.take_screenshot()
                if data:
                    emit_frame(data)
                await asyncio.sleep(_MIN_FRAME_INTERVAL)
        finally:
            await svc.close()


async def _capture_once(udid: str, version: str, emit_frame, stop) -> None:
    """Run one capture session on the route the iOS version dictates."""
    try:
        ver = Version(version or "0")
    except Exception:
        ver = Version("0")
    if ver >= Version("17.4"):
        try:
            await _capture_dvt_userspace(udid, emit_frame, stop)
        except Exception as exc:
            if type(exc).__name__ == "UserspaceTunnelUnavailableError":
                await _capture_dvt_tunneld(udid, emit_frame, stop)
            else:
                raise
    elif ver >= Version("17.0"):
        await _capture_dvt_tunneld(udid, emit_frame, stop)
    else:
        await _capture_screenshotr(udid, emit_frame, stop)


class ScreenStreamThread(QThread):
    """Owns the capture loop for one device at a time.

    Signals:
      frame_ready(bytes)   — one screenshot (PNG) from the device
      status_changed(str)  — honest one-line state for the preview
    """

    frame_ready = Signal(object)
    status_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._udid = ""
        self._version = ""
        self._stop = threading.Event()
        self._live_announced = False

    # -- GUI-thread API ---------------------------------------------------
    def start_stream(self, udid: str, version: str) -> None:
        self._udid = udid or ""
        self._version = version or ""
        self._stop = threading.Event()
        self._live_announced = False
        self.start()

    def stop_stream(self) -> None:
        self._stop.set()
        if self.isRunning():
            self.wait(2500)

    # -- worker -----------------------------------------------------------
    def _emit_frame(self, data: bytes) -> None:
        if not self._live_announced:
            self._live_announced = True
            self.status_changed.emit("live")
        self.frame_ready.emit(data)

    async def _supervise(self) -> None:
        while not self._stop.is_set():
            try:
                await _capture_once(
                    self._udid, self._version, self._emit_frame, self._stop)
            except _StreamFailure as exc:
                self.status_changed.emit(exc.status)
                logger.info("screen stream: %s", exc.status)
            except Exception as exc:  # device I/O — never kill the thread
                status = _friendly_status(exc)
                self.status_changed.emit(status)
                logger.info("screen stream: %s (%r)", status, exc)
            self._live_announced = False
            # Interruptible retry wait.
            for _ in range(int(_RETRY_SECONDS * 10)):
                if self._stop.is_set():
                    break
                await asyncio.sleep(0.1)

    def run(self) -> None:  # noqa: D102 — QThread entry point
        install_windows_selector_policy()
        try:
            asyncio.run(self._supervise())
        except Exception:
            logger.exception("screen stream loop crashed")
