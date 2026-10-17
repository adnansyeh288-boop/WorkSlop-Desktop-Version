"""Real device recovery-mode operations for WorkSlop Desktop.

Enter Recovery: sends the lockdownd ``EnterRecovery`` request over the
active lockdown session (the exact equivalent of ``ideviceenterrecovery``).

Exit Recovery: talks to the device in recovery/DFU mode over USB with the
irecovery protocol (pymobiledevice3.irecv) and sends the ``reboot`` command
(the exact equivalent of ``irecovery -c reboot``).

Both run off the GUI thread via RecoveryWorker. Nothing here is a stub:
if the device is not in the expected state the real library raises and the
error is reported to the user.
"""
import asyncio
import traceback

from PySide6.QtCore import QThread, Signal


class RecoveryWorker(QThread):
    """Off-GUI-thread worker for enter/exit recovery.

    mode: "enter" -> EnterRecovery via lockdown (needs a booted, paired device)
          "exit"  -> reboot via irecovery (needs a device in recovery/DFU mode)
    """
    finished = Signal(bool, str)   # ok, message
    progress = Signal(str)

    def __init__(self, mode: str, udid: str = "", parent=None):
        super().__init__(parent)
        self._mode = mode
        self._udid = udid or None

    def run(self):
        try:
            if self._mode == "enter":
                msg = _enter_recovery_sync(self._udid, self.progress.emit)
            elif self._mode == "exit":
                msg = _exit_recovery_sync(self.progress.emit)
            else:
                raise ValueError(f"unknown recovery mode: {self._mode}")
            self.finished.emit(True, msg)
        except Exception as e:  # noqa: BLE001 - report everything to the UI
            self.finished.emit(False, f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=3)}")


def _enter_recovery_sync(udid, progress_cb) -> str:
    """Blocking wrapper around the async lockdown EnterRecovery request."""
    from src.devicemanagement.session import lockdown_session

    async def _go():
        progress_cb("Connecting to device via lockdown...")
        async with lockdown_session(udid) as ld:
            progress_cb("Sending EnterRecovery request...")
            resp = await ld.enter_recovery()
            return resp

    resp = asyncio.run(_go())
    # lockdownd answers; the device then reboots into recovery on its own.
    return ("EnterRecovery request sent. The iPhone should now reboot "
            "into recovery mode (cable + computer screen). "
            f"lockdownd response: {resp}")


def _exit_recovery_sync(progress_cb) -> str:
    """Find the device in recovery/DFU mode over USB and send 'reboot'."""
    from pymobiledevice3.irecv import IRecv
    from pymobiledevice3.exceptions import IRecvNoDeviceConnectedError

    progress_cb("Looking for a device in recovery/DFU mode over USB...")
    try:
        recv = IRecv(timeout=10)
    except IRecvNoDeviceConnectedError:
        raise RuntimeError(
            "No device in recovery/DFU mode found over USB. "
            "Put the iPhone into recovery mode first, then try again.")
    mode = recv.mode
    progress_cb(f"Found device in {mode.name}; sending reboot command...")
    recv.reboot()
    return ("Reboot command sent via the recovery protocol. "
            "The iPhone should now restart normally (Apple logo).")
