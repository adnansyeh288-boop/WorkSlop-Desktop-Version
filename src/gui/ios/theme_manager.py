"""WorkSlop Desktop UI mode: single interface (user order 2026-10-18).

The three-interface system (WorkSlop Main / WorkSlop 2 / Nugget) was removed.
There is now exactly ONE interface: the rebuilt classic desktop shell
(device bar + sidebar + pages) in the blue-white WorkSlop identity.

``ThemeManager`` is kept as a thin compatibility shim because several
modules reference ``ThemeManager.CLASSIC`` / ``theme_manager.current_theme``.
It always reports the single UI; ``save_theme`` / ``switch_to`` are no-ops
that keep the persisted ``ui/theme`` key at ``"classic"`` so old settings
cannot trap the app in a removed shell.
"""
from PySide6.QtCore import QSettings


class ThemeManager:
    CLASSIC = 0

    _TO_VALUE = {CLASSIC: "classic"}
    _FROM_VALUE = {"classic": CLASSIC}

    def __init__(self, parent):
        self.parent = parent
        self.settings = QSettings("WorkSlop", "WorkSlop")
        # Force-migrate any stale value from the 3-UI era.
        self.settings.setValue("ui/theme", "classic")
        self.current_theme = self.CLASSIC

    @staticmethod
    def is_classic(theme: int) -> bool:
        """Always True — there is only one UI now."""
        return True

    def load_theme(self) -> int:
        return self.CLASSIC

    def save_theme(self, theme: int):
        self.settings.setValue("ui/theme", "classic")
        self.current_theme = self.CLASSIC

    def switch_to(self, theme: int):
        # Container switching is handled by MainWindow.apply_theme().
        self.save_theme(self.CLASSIC)
