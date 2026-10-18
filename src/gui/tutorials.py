"""WorkSlop Desktop tutorials (single-UI rebuild, round 2).

- Model picker (WAJIB, user order): every device-touching tutorial starts
  with choosing the iPhone model — "Dynamic Island" (no Home button) or
  "Home Button" (physical Home button). Steps and the animated iPhone
  drawing adapt to the chosen model. The WorkSlop app-usage tutorial has
  no picker (not device-specific).
- PhoneAnimWidget: QPainter-drawn iPhone (Dynamic Island pill OR Home
  button, correct side buttons per model) with an animated finger that
  moves to each target button and plays a press animation, step by step.
  Next/Back navigation + auto-play.
- Recovery enter/exit pages carry the REAL device action button on top
  of the animated steps (see recovery_tools.RecoveryWorker).

Button sequences verified (do not invent new ones):
  Dynamic Island (Face ID iPhones):
    Recovery enter: Vol Up tap -> Vol Down tap -> hold Side to recovery screen
    Recovery exit:  hold Side to Apple logo
    DFU enter:      Vol Up -> Vol Down -> hold Side 10s -> hold Side+VolDown 5s
                    -> release Side, hold VolDown until screen stays black
  Home Button (Touch ID iPhones):
    Recovery enter: hold Home+Power to recovery screen
    Recovery exit:  hold Home+Power to Apple logo
    DFU enter:      hold Home+Power 10s -> release Power, hold Home to black
"""
from PySide6.QtCore import (
    Qt, QCoreApplication, Signal, QSize, QPointF, QRectF, QTimer,
    QPropertyAnimation, QEasingCurve, Property,
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QSizePolicy,
)

from src.gui.theme import ColorThemeManager
from src.gui.ios.components import IOSCard

MODEL_ISLAND = "island"
MODEL_HOME = "home"

MODELS = [
    (MODEL_ISLAND, "iPhone Dynamic Island",
     "iPhone X and newer\n(no Home button)"),
    (MODEL_HOME, "iPhone Home Button",
     "iPhone 8 and older\n(physical Home button)"),
]

# ---------------------------------------------------------------------------
# Step data: buttons use ids vol_up / vol_down / side / home / power.
# ---------------------------------------------------------------------------
def _s(buttons, text, hold=0):
    return {"buttons": list(buttons), "text": text, "hold": hold}


STEPS = {
    # -- Enter Recovery Mode -------------------------------------------------
    "rec_enter": {
        "title": "Enter Recovery Mode",
        "needs_model": True, "animated": True, "action": "enter",
        MODEL_ISLAND: [
            _s(["vol_up"], "Quick-press and release the Volume Up button."),
            _s(["vol_down"], "Quick-press and release the Volume Down button."),
            _s(["side"], "Hold the Side button until the recovery screen "
                         "appears (cable + computer icon), then release."),
        ],
        MODEL_HOME: [
            _s(["home", "power"], "Hold the Home + Power buttons together "
                                  "until the recovery screen appears "
                                  "(cable + computer icon), then release."),
        ],
    },
    # -- Exit Recovery Mode ---------------------------------------------------
    "rec_exit": {
        "title": "Exit Recovery Mode",
        "needs_model": True, "animated": True, "action": "exit",
        MODEL_ISLAND: [
            _s(["side"], "Hold the Side button until the Apple logo appears, "
                         "then release. Your iPhone will boot normally."),
        ],
        MODEL_HOME: [
            _s(["home", "power"], "Hold the Home + Power buttons until the "
                                  "Apple logo appears, then release."),
        ],
    },
    # -- DFU ------------------------------------------------------------------
    "dfu": {
        "title": "How to Enter DFU Mode",
        "needs_model": True, "animated": True, "action": None,
        MODEL_ISLAND: [
            _s(["vol_up"], "Quick-press and release Volume Up."),
            _s(["vol_down"], "Quick-press and release Volume Down."),
            _s(["side"], "Hold the Side button for 10 seconds.", hold=10),
            _s(["side", "vol_down"], "While still holding Side, also hold "
                                     "Volume Down for 5 seconds.", hold=5),
            _s(["vol_down"], "Release the Side button but KEEP holding "
                             "Volume Down until the screen stays black "
                             "(~10 seconds). Black screen = DFU worked.", hold=10),
        ],
        MODEL_HOME: [
            _s(["home", "power"], "Hold the Home + Power buttons together "
                                  "for 10 seconds.", hold=10),
            _s(["home"], "Release the Power button but KEEP holding Home "
                          "until the screen stays black. "
                          "Black screen = DFU worked.", hold=10),
        ],
    },
    # -- Restore iPhone -------------------------------------------------------
    "restore": {
        "title": "How to Restore Your iPhone",
        "needs_model": True, "animated": False, "action": None,
        MODEL_ISLAND: [
            "Put your iPhone into recovery mode first: quick-press Volume Up, "
            "quick-press Volume Down, then hold Side until the recovery "
            "screen appears.",
            "Connect your iPhone to your Mac/PC with a cable.",
            "Open Finder (Mac) or iTunes (Windows), then select your iPhone.",
            'Click "Restore iPhone", then confirm.',
            "Wait for the firmware download and restore to finish — "
            "don't unplug the cable.",
            "Your iPhone will restart. Set it up as new or restore from a backup.",
        ],
        MODEL_HOME: [
            "Put your iPhone into recovery mode first: hold Home + Power "
            "until the recovery screen appears.",
            "Connect your iPhone to your Mac/PC with a cable.",
            "Open Finder (Mac) or iTunes (Windows), then select your iPhone.",
            'Click "Restore iPhone", then confirm.',
            "Wait for the firmware download and restore to finish — "
            "don't unplug the cable.",
            "Your iPhone will restart. Set it up as new or restore from a backup.",
        ],
    },
    # -- Beta program ---------------------------------------------------------
    "beta": {
        "title": "How to Join the iOS Beta Program",
        "needs_model": True, "animated": False, "action": None,
        MODEL_ISLAND: [
            "Open beta.apple.com in Safari and sign in with your Apple Account.",
            "Enroll your device in the beta program.",
            "On your iPhone: Settings > General > Software Update > Beta Updates.",
            'Choose "iOS Developer Beta" or "iOS Public Beta".',
            "Go back, then download and install the beta update.",
            "Important: back up your iPhone before installing the beta.",
        ],
        MODEL_HOME: [
            "Open beta.apple.com in Safari and sign in with your Apple Account.",
            "Enroll your device in the beta program.",
            "On your iPhone: Settings > General > Software Update > Beta Updates.",
            'Choose "iOS Developer Beta" or "iOS Public Beta".',
            "Go back, then download and install the beta update.",
            "Important: back up your iPhone before installing the beta.",
        ],
    },
    # -- WorkSlop app tutorial (no model picker) --------------------------------
    "app": {
        "title": "WorkSlop Tutorial",
        "needs_model": False, "animated": False, "action": None,
        "steps": [
            "Connect your iPhone to the computer with a cable and tap \"Trust\" on your iPhone.",
            "Select your device in the top bar of WorkSlop Desktop.",
            "Open a tweak menu (e.g. Liquid Glass) and turn on the toggles you want.",
            "Open the Backup menu — back up first before applying.",
            "Open the Apply menu to apply the tweaks to your iPhone.",
            "Restart your iPhone if prompted so the tweaks take effect.",
        ],
    },
}


# ---------------------------------------------------------------------------
# PhoneAnimWidget — QPainter iPhone + animated finger
# ---------------------------------------------------------------------------
class PhoneAnimWidget(QWidget):
    """Draws an iPhone per model with an animated finger pressing buttons.

    Layout (widget ~320x600): phone body centered; side buttons protrude
    from the correct edges; Home button drawn on the bottom bezel for the
    home-button model; Dynamic Island pill for the island model.
    """

    PHONE_W, PHONE_H = 190, 400

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 560)
        self.setSizePolicy(QSizePolicy.Policy.Fixed,
                           QSizePolicy.Policy.Fixed)
        self._model = MODEL_ISLAND
        self._steps = []
        self._step_idx = 0
        self._finger = QPointF(-100, -100)   # animated property
        self._finger_scale = 1.0
        self._pressed = set()                # button ids currently pressed
        self._step_done = False
        self._move_anim = None
        self._seq_timer = QTimer(self)
        self._seq_timer.setSingleShot(True)
        self._seq_timer.timeout.connect(self._seq_advance)
        self._seq_phase = 0
        # Press-pulse timer (member, not singleShot: set_step() must be
        # able to cancel a stale _after_press from the previous step,
        # otherwise the stale callback corrupts the new step's phase and
        # the finger animation never runs.)
        self._press_timer = QTimer(self)
        self._press_timer.setSingleShot(True)
        self._press_timer.timeout.connect(self._after_press)
        self.step_changed = None  # set by TutorialPage: callable(idx)

    # -- animated property ------------------------------------------------
    def _get_finger(self):
        return self._finger

    def _set_finger(self, p):
        self._finger = p
        self.update()

    finger_pos = Property(QPointF, _get_finger, _set_finger)

    # -- public API -------------------------------------------------------
    def set_model(self, model: str):
        self._model = model
        self.update()

    def set_steps(self, steps):
        self._steps = steps
        self.set_step(0)

    def set_step(self, idx: int):
        if not self._steps:
            return
        self._step_idx = max(0, min(idx, len(self._steps) - 1))
        self._pressed = set()
        self._step_done = False
        self._seq_timer.stop()
        self._press_timer.stop()
        if self._move_anim is not None:
            self._move_anim.stop()
        # park finger below the phone, then run the sequence
        phone = self._phone_rect()
        self._finger = QPointF(phone.center().x(), phone.bottom() + 70)
        self._seq_phase = 0
        self.update()
        if self.step_changed:
            self.step_changed(self._step_idx)
        self._seq_timer.start(400)

    # -- animation sequence -----------------------------------------------
    def _seq_advance(self):
        step = self._steps[self._step_idx]
        buttons = step["buttons"]
        if self._seq_phase < len(buttons):
            # move finger to next button
            target = self._button_point(buttons[self._seq_phase])
            self._move_anim = QPropertyAnimation(self, b"finger_pos", self)
            self._move_anim.setEndValue(target)
            self._move_anim.setDuration(550)
            self._move_anim.setEasingCurve(QEasingCurve.InOutQuad)
            self._move_anim.finished.connect(self._on_arrived)
            self._move_anim.start()
        else:
            # all buttons pressed -> hold indicator, then done
            self._step_done = True
            self.update()

    def _on_arrived(self):
        step = self._steps[self._step_idx]
        buttons = step["buttons"]
        btn = buttons[self._seq_phase]
        self._pressed.add(btn)
        # press pulse: quick scale dip
        self._finger_scale = 0.82
        self.update()
        self._press_timer.start(220)

    def _after_press(self):
        self._finger_scale = 1.0
        self._seq_phase += 1
        self.update()
        self._seq_timer.start(350)

    # -- geometry ----------------------------------------------------------
    def _phone_rect(self):
        w, h = self.width(), self.height()
        x = (w - self.PHONE_W) / 2
        y = 30
        return QRectF(x, y, self.PHONE_W, self.PHONE_H)

    def _button_point(self, btn_id: str) -> QPointF:
        """Finger target: just outside the physical button."""
        r = self._phone_rect()
        if btn_id == "vol_up":
            return QPointF(r.left() - 34, r.top() + 96)
        if btn_id == "vol_down":
            return QPointF(r.left() - 34, r.top() + 152)
        if btn_id == "side":
            return QPointF(r.right() + 34, r.top() + 128)
        if btn_id == "power":
            return QPointF(r.right() + 34, r.top() + 80)
        if btn_id == "home":
            return QPointF(r.center().x(), r.bottom() - 34)
        return QPointF(r.center().x(), r.center().y())

    def _button_rect(self, btn_id: str):
        r = self._phone_rect()
        if btn_id == "vol_up":
            return QRectF(r.left() - 7, r.top() + 78, 7, 40)
        if btn_id == "vol_down":
            return QRectF(r.left() - 7, r.top() + 134, 7, 40)
        if btn_id == "side":
            return QRectF(r.right(), r.top() + 100, 7, 64)
        if btn_id == "power":
            return QRectF(r.right(), r.top() + 62, 7, 40)
        if btn_id == "home":
            d = 40
            return QRectF(r.center().x() - d / 2, r.bottom() - d - 14, d, d)
        return QRectF()

    # -- painting -----------------------------------------------------------
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = ColorThemeManager.instance().colors
        accent = QColor(c.accent)

        r = self._phone_rect()
        # phone body
        p.setPen(QPen(QColor("#1a1a1e"), 3))
        p.setBrush(QColor("#2b2b30"))
        p.drawRoundedRect(r, 34, 34)
        # screen
        s = QRectF(r.x() + 10, r.y() + 10, r.width() - 20, r.height() - 20)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#eef3fa"))
        p.drawRoundedRect(s, 26, 26)

        if self._model == MODEL_ISLAND:
            # Dynamic Island
            iw, ih = 64, 20
            p.setBrush(QColor("#0a0a0c"))
            p.drawRoundedRect(QRectF(s.center().x() - iw / 2, s.top() + 12,
                                     iw, ih), 10, 10)
            for b in ("vol_up", "vol_down", "side"):
                self._draw_side_button(p, b, accent)
        else:
            # Home button on the bottom bezel
            hr = self._button_rect("home")
            p.setPen(QPen(QColor("#1a1a1e"), 2))
            p.setBrush(QColor("#3a3a40") if "home" not in self._pressed
                       else accent)
            p.drawEllipse(hr)
            for b in ("vol_up", "vol_down", "power"):
                self._draw_side_button(p, b, accent)

        # finger
        if self._finger.x() >= 0:
            fr = 26 * self._finger_scale
            # press ripple
            if self._pressed:
                p.setPen(QPen(accent, 3))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(self._finger, fr + 10, fr + 10)
            p.setPen(QPen(QColor("#ffffff"), 3))
            p.setBrush(accent)
            p.drawEllipse(self._finger, fr, fr)
            # step badge on the finger
            p.setPen(QPen(QColor("#ffffff")))
            f = QFont()
            f.setBold(True)
            f.setPointSize(13)
            p.setFont(f)
            p.drawText(QRectF(self._finger.x() - fr, self._finger.y() - fr,
                              fr * 2, fr * 2),
                       Qt.AlignCenter, str(self._step_idx + 1))

        # hold indicator
        step = self._steps[self._step_idx] if self._steps else None
        if step and step.get("hold") and self._step_done:
            p.setPen(QPen(accent, 3))
            p.setBrush(QColor("#ffffff"))
            bw, bh = 150, 34
            bx = (self.width() - bw) / 2
            by = r.bottom() + 8
            p.drawRoundedRect(QRectF(bx, by, bw, bh), 17, 17)
            p.setPen(QPen(QColor("#0a0a0a")))
            f2 = QFont()
            f2.setBold(True)
            f2.setPointSize(12)
            p.setFont(f2)
            p.drawText(QRectF(bx, by, bw, bh), Qt.AlignCenter,
                       f"Hold {step['hold']}s")

    def _draw_side_button(self, p, btn_id, accent):
        br = self._button_rect(btn_id)
        p.setPen(QPen(QColor("#1a1a1e"), 2))
        p.setBrush(accent if btn_id in self._pressed else QColor("#3a3a40"))
        p.drawRoundedRect(br, 3, 3)


# ---------------------------------------------------------------------------
# TutorialPage
# ---------------------------------------------------------------------------
class TutorialPage(QWidget):
    """One tutorial: model picker (when needed) + steps + animation."""

    request_recovery = Signal(str)   # "enter" / "exit" -> main window runs worker

    def __init__(self, window, tutorial_id: str, parent=None):
        super().__init__(parent)
        self.window = window
        self.tutorial_id = tutorial_id
        self.spec = STEPS[tutorial_id]
        self._model = None
        self._step_idx = 0
        self._auto = False
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self._auto_next)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(24, 20, 24, 20)
        self._layout.setSpacing(14)

        title = QLabel(self.spec["title"], self)
        title.setObjectName("tutorialTitle")
        title.setStyleSheet("font-size: 22px; font-weight: 700; "
                            "background: transparent;")
        self._layout.addWidget(title)

        # -- model picker --------------------------------------------------
        self._picker = QWidget(self)
        pl = QVBoxLayout(self._picker)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(10)
        plbl = QLabel("Pick your iPhone model first:", self._picker)
        plbl.setStyleSheet("font-size: 15px; font-weight: 600; "
                           "background: transparent;")
        pl.addWidget(plbl)
        cards = QHBoxLayout()
        cards.setSpacing(12)
        self._model_cards = {}
        for mid, name, desc in MODELS:
            card = QPushButton(f"{name}\n{desc}", self._picker)
            card.setCheckable(True)
            card.setCursor(Qt.PointingHandCursor)
            card.setMinimumHeight(86)
            card.clicked.connect(lambda _=False, m=mid: self._choose_model(m))
            self._model_cards[mid] = card
            cards.addWidget(card)
        cards.addStretch(1)
        pl.addLayout(cards)
        pl.addStretch(1)
        self._layout.addWidget(self._picker, 1)
        self._style_picker_cards()

        # -- content (built after model choice / immediately for app) ------
        self._content = QWidget(self)
        self._content.hide()
        self._layout.addWidget(self._content, 1)

        if not self.spec["needs_model"]:
            self._picker.hide()
            self._build_content()
            self._content.show()

    # -- model picker ------------------------------------------------------
    def _style_picker_cards(self):
        c = ColorThemeManager.instance().colors
        for card in self._model_cards.values():
            card.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c.bg_secondary};
                    border: 2px solid {c.card_border};
                    border-radius: 22px;
                    font-size: 15px;
                    font-weight: 600;
                    color: {c.text_primary};
                    padding: 14px 22px;
                    text-align: left;
                }}
                QPushButton:hover {{ border-color: {c.accent}; }}
                QPushButton:checked {{
                    background-color: {c.accent};
                    color: #FFFFFF;
                    border: 2px solid {c.accent};
                }}
            """)

    def _choose_model(self, model: str):
        self._model = model
        for mid, card in self._model_cards.items():
            card.setChecked(mid == model)
        # rebuild content for the chosen model
        self._build_content()
        self._picker.hide()
        self._content.show()

    def reset_picker(self):
        """Show the picker again (called when navigating to the page)."""
        if self.spec["needs_model"]:
            self._content.hide()
            self._picker.show()
            for card in self._model_cards.values():
                card.setChecked(False)
            self._model = None

    # -- content ------------------------------------------------------------
    def _clear_content(self):
        old = self._content.layout()
        if old is not None:
            while old.count():
                it = old.takeAt(0)
                w = it.widget()
                if w is not None:
                    w.deleteLater()
            # detach the old layout so a fresh one can be set
            QWidget().setLayout(old)
        self._content.setLayout(QVBoxLayout())

    def _build_content(self):
        self._clear_content()
        layout = self._content.layout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        c = ColorThemeManager.instance().colors

        if self._model is not None:
            change = QPushButton("Change iPhone model", self._content)
            change.setCursor(Qt.PointingHandCursor)
            change.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {c.accent};
                    font-size: 13px; font-weight: 600; border: none;
                    text-decoration: underline;
                }}""")
            change.clicked.connect(self.reset_picker)
            layout.addWidget(change, 0, Qt.AlignLeft)

        if self.spec["animated"]:
            self._build_animated(layout)
        else:
            self._build_text_steps(layout)

        # real action button for recovery pages
        action = self.spec.get("action")
        if action in ("enter", "exit"):
            btn = QPushButton(
                "ENTER RECOVERY MODE (for real)" if action == "enter"
                else "EXIT RECOVERY MODE (for real)",
                self._content)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(52)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c.accent};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 26px;
                    font-size: 15px;
                    font-weight: 700;
                    padding: 0 28px;
                }}
                QPushButton:hover {{ background-color: {c.accent_hover}; }}
                QPushButton:pressed {{ background-color: {c.accent_pressed}; }}
            """)
            btn.clicked.connect(lambda: self.request_recovery.emit(action))
            layout.addWidget(btn, 0, Qt.AlignCenter)

    def _build_animated(self, layout):
        steps = self.spec[self._model]
        self._anim = PhoneAnimWidget(self._content)
        self._anim.set_model(self._model)
        self._anim.step_changed = self._on_anim_step

        self._step_label = QLabel(self._content)
        self._step_label.setWordWrap(True)
        self._step_label.setStyleSheet("font-size: 15px; background: transparent;")
        self._step_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        nav = QHBoxLayout()
        nav.setSpacing(10)
        self._back_btn = QPushButton("‹ Back", self._content)
        self._next_btn = QPushButton("Next ›", self._content)
        self._auto_btn = QPushButton("Auto-play: OFF", self._content)
        self._auto_btn.setCheckable(True)
        for b in (self._back_btn, self._next_btn, self._auto_btn):
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(44)
        self._back_btn.clicked.connect(self._prev_step)
        self._next_btn.clicked.connect(self._next_step)
        self._auto_btn.toggled.connect(self._toggle_auto)
        self._style_nav_buttons()
        nav.addWidget(self._back_btn)
        nav.addWidget(self._auto_btn)
        nav.addWidget(self._next_btn)

        # Horizontal: phone animation left, step text + nav right.
        # (Vertical stacking overflowed the page and overlapped.)
        row = QHBoxLayout()
        row.setSpacing(24)
        row.addWidget(self._anim, 0, Qt.AlignTop)
        right = QVBoxLayout()
        right.setSpacing(16)
        right.addWidget(self._step_label)
        right.addStretch(1)
        right.addLayout(nav)
        row.addLayout(right, 1)

        layout.addLayout(row, 1)

        self._step_idx = 0
        self._anim.set_steps(steps)
        self._update_step_ui()

    def _build_text_steps(self, layout):
        c = ColorThemeManager.instance().colors
        steps = (self.spec[self._model] if self.spec["needs_model"]
                 else self.spec["steps"])
        scroll = QScrollArea(self._content)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        inner = QWidget()
        il = QVBoxLayout(inner)
        il.setContentsMargins(4, 4, 4, 4)
        il.setSpacing(10)
        for i, text in enumerate(steps, 1):
            # IOSCard paints its rounded surface in paintEvent — Qt ignores
            # stylesheet border-radius on plain QFrames in this window (the
            # sharp inner box seen in round 5).
            card = IOSCard(inner)
            cl = QHBoxLayout(card)
            cl.setContentsMargins(18, 14, 18, 14)
            cl.setSpacing(14)
            num = QLabel(str(i), card)
            num.setFixedSize(36, 36)
            num.setAlignment(Qt.AlignCenter)
            num.setStyleSheet(f"""
                QLabel {{
                    background-color: {c.accent};
                    color: #FFFFFF;
                    border-radius: 18px;
                    font-size: 16px;
                    font-weight: 700;
                }}""")
            txt = QLabel(text, card)
            txt.setWordWrap(True)
            txt.setObjectName("stepText")
            # Belt and suspenders: stylesheet ID selector + translucent
            # attribute, so no Qt quirk can paint an opaque box here.
            txt.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            txt.setStyleSheet("QLabel#stepText { font-size: 14px; background: transparent; }")
            cl.addWidget(num)
            cl.addWidget(txt, 1)
            il.addWidget(card)
        il.addStretch(1)
        scroll.setWidget(inner)
        layout.addWidget(scroll, 1)

    def _style_nav_buttons(self):
        c = ColorThemeManager.instance().colors
        qss = f"""
            QPushButton {{
                background-color: {c.bg_secondary};
                border: 1px solid {c.card_border};
                border-radius: 22px;
                font-size: 14px;
                font-weight: 600;
                color: {c.accent};
                padding: 0 22px;
            }}
            QPushButton:hover {{ background-color: {c.surface_hover}; }}
            QPushButton:checked {{
                background-color: {c.accent};
                color: #FFFFFF;
                border: 1px solid {c.accent};
            }}
            QPushButton:disabled {{ color: {c.text_disabled}; }}
        """
        for b in (self._back_btn, self._next_btn, self._auto_btn):
            b.setStyleSheet(qss)

    # -- step navigation ------------------------------------------------------
    def _on_anim_step(self, idx: int):
        self._step_idx = idx
        self._update_step_ui()

    def _update_step_ui(self):
        steps = self.spec[self._model]
        n = len(steps)
        self._step_label.setText(
            f"<b>Step {self._step_idx + 1} / {n}</b><br/>"
            f"{steps[self._step_idx]['text']}")
        self._back_btn.setEnabled(self._step_idx > 0)
        self._next_btn.setEnabled(self._step_idx < n - 1)

    def _prev_step(self):
        if self._step_idx > 0:
            self._auto_timer.stop()
            self._auto_btn.setChecked(False)
            self._auto = False
            self._anim.set_step(self._step_idx - 1)

    def _next_step(self):
        steps = self.spec[self._model]
        if self._step_idx < len(steps) - 1:
            self._anim.set_step(self._step_idx + 1)

    def _toggle_auto(self, on: bool):
        self._auto = on
        self._auto_btn.setText(f"Auto-play: {'ON' if on else 'OFF'}")
        if on:
            self._auto_timer.start(3500)
        else:
            self._auto_timer.stop()

    def _auto_next(self):
        steps = self.spec[self._model]
        if self._step_idx < len(steps) - 1:
            self._anim.set_step(self._step_idx + 1)
        else:
            self._toggle_auto(False)
            self._auto_btn.setChecked(False)
