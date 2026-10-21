"""Single-instance guard (user bug report 2026-10-22: three windows).

The frozen app cold-starts slowly on modest hardware, so a second or
third double-click used to spawn a whole extra process — several
WorkSlop windows and device managers fighting over the same settings
store, backup cache and connected device. The first process now owns
a QLocalServer; later launches connect to it, ask it to raise its
window, and exit before doing any heavy work.

Failure policy: the guard must never keep the app from starting. Any
unexpected socket error degrades to "no guard" — a duplicate window
is recoverable, an app that refuses to open is not.
"""

from PySide6.QtNetwork import QLocalServer, QLocalSocket

_SERVER_NAME = "WorkSlopDesktop-single-instance-v1"
_TIMEOUT_MS = 350


class SingleInstanceGuard:
    """Owns the "primary instance" role for this process, if free."""

    def __init__(self):
        self._server = None
        self._pending = set()
        # Set by the owner once the main window exists; called on the
        # GUI thread whenever a later launch asks us to come forward.
        self.on_raise_requested = None

    def try_become_primary(self) -> bool:
        """True when this process is the primary (serve + continue).

        False when another instance is already running: it has been
        asked to raise its window and this process should exit.
        """
        try:
            probe = QLocalSocket()
            probe.connectToServer(_SERVER_NAME)
            if probe.waitForConnected(_TIMEOUT_MS):
                try:
                    probe.write(b"show")
                    probe.flush()
                    probe.waitForBytesWritten(_TIMEOUT_MS)
                finally:
                    probe.disconnectFromServer()
                return False
        except Exception:
            pass  # fall through and try to own the name instead
        # Nobody answered: clear a stale socket left by a crashed run,
        # then take the name. Losing a race here still starts the app.
        try:
            QLocalServer.removeServer(_SERVER_NAME)
            server = QLocalServer()
            server.newConnection.connect(self._on_new_connection)
            if not server.listen(_SERVER_NAME):
                return True
            self._server = server
        except Exception:
            return True
        return True

    def _on_new_connection(self):
        try:
            sock = self._server.nextPendingConnection()
        except Exception:
            return
        if sock is None:
            return
        self._pending.add(sock)
        sock.disconnected.connect(lambda: self._pending.discard(sock))

        def _handle():
            try:
                data = bytes(sock.readAll()).decode("utf-8", "ignore")
            except Exception:
                data = ""
            if "show" in data and self.on_raise_requested is not None:
                try:
                    self.on_raise_requested()
                except Exception:
                    pass
            try:
                sock.disconnectFromServer()
            except Exception:
                pass

        sock.readyRead.connect(_handle)
        if sock.bytesAvailable():
            _handle()
