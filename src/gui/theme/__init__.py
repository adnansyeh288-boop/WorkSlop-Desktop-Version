import os
import sys

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from src.gui.theme.theme_manager import ColorThemeManager
from src.gui.theme.colors import DARK, SKY, WORKBENCH, WS_BLUE, ACCENT_PRESETS
from src.gui.theme.styles import STYLES, FONT_FAMILY, mono_family
from src.gui.theme.accent_picker import AccentPicker


def t(style_key: str) -> str:
    """Render a named stylesheet template with the current theme colors."""
    payload = dict(ColorThemeManager.instance().colors.__dict__)
    payload["font_family"] = mono_family()
    return STYLES[style_key].format_map(payload)


def themed_stylesheet(style_key: str, **extra) -> str:
    """Render a stylesheet template with the current colors plus runtime
    extras (e.g. a generated caret image path passed as ``caret=...``)."""
    payload = dict(ColorThemeManager.instance().colors.__dict__)
    payload["font_family"] = mono_family()
    payload.update(extra)
    return STYLES[style_key].format_map(payload)


def theme_icon(resource_path: str, color_hex: str) -> QIcon:
    """Recolor a monochrome (white) SVG icon to *color_hex* using its alpha.

    SVGs are rasterized through QSvgRenderer (via :func:`theme_pixmap`),
    NOT QImage: the QImage route goes through the qsvg image-format
    plugin, which in the frozen Windows build silently returns a null
    image for some bundled icons — the sidebar glyphs for Mobile Gestalt,
    Status Bar, SpringBoard and Daemons vanished (their menu rows rendered
    text-only) while other icons loaded fine. QSvgRenderer ships inside
    the QtSvg module itself and renders the same files reliably (it is
    what the Home tiles/social glyphs already use). Non-SVG inputs keep
    the legacy QImage path below.
    """
    if str(resource_path).lower().endswith(".svg"):
        return QIcon(theme_pixmap(resource_path, color_hex, 48))
    img = QImage(resource_path)
    img = img.convertToFormat(QImage.Format.Format_ARGB32)
    painter = QPainter(img)
    painter.setCompositionMode(
        QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(img.rect(), QColor(color_hex))
    painter.end()
    return QIcon(QPixmap.fromImage(img))


def _svg_file_candidates(resource_path: str):
    """Loose-file locations for a ``:/icon/...`` resource.

    The frozen build ships ``src/qt`` as loose files (PyInstaller
    --add-data), so every bundled SVG also exists on disk next to the
    code; in a source checkout they sit in ``src/qt/icon`` as usual.
    """
    name = os.path.basename(str(resource_path))
    if not name:
        return []
    out = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        out.append(os.path.join(meipass, "src", "qt", "icon", name))
    here = os.path.dirname(os.path.abspath(__file__))  # src/gui/theme
    out.append(os.path.normpath(
        os.path.join(here, "..", "..", "qt", "icon", name)))
    out.append(os.path.join(os.getcwd(), "src", "qt", "icon", name))
    return out


# Rendered-icon cache: (resource_path, size, dpr) -> raw pixmap.
# Sidebar/menu icons are re-requested on every page switch and retheme;
# without this cache each request re-rasterized the SVG, re-ran the
# full-image empty scan, and — in the frozen build — re-attempted the
# broken Qt resource first (see _render_svg_raw), which flooded the log
# with "Cannot open file ':/icon/ws2-*.svg' Input/output error" lines and
# cost real time on every navigation. QPixmap is implicitly shared, so
# handing out the cached handle is cheap; the one painter caller
# (theme_pixmap) deep-copies before its tint pass.
_RAW_PIXMAP_CACHE: dict = {}

# Resource paths that already failed to open once in this process.
_DEAD_RESOURCES: set = set()


def _render_svg_raw(resource_path: str, size: int, dpr: float) -> QPixmap:
    """Rasterize an SVG untinted, viewBox fit into the square, centered.

    In the frozen Windows build the Qt resource copy of the bundled
    ``ws2-*`` icons cannot be opened at all (``QSvgRenderer(':/icon/…')``
    logs an Input/output error and yields an invalid renderer), while
    the byte-identical loose file shipped next to the code renders fine —
    so frozen builds go straight to the loose files and never touch the
    resource (zero log spam). Source checkouts keep resource-first, with
    the loose-file retry as before; a resource that fails once is marked
    dead for the rest of the process. Results are cached per
    (path, size, dpr), so repeat renders (page switches, rethemes) are
    free after the first.
    """
    cache_key = (str(resource_path), int(size), float(dpr))
    cached = _RAW_PIXMAP_CACHE.get(cache_key)
    if cached is not None:
        return cached

    scale = max(1.0, float(dpr))
    px = int(round(size * scale))

    def _draw(renderer):
        pm = QPixmap(px, px)
        pm.setDevicePixelRatio(scale)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        # Fit the viewBox into the square, centered, keeping the aspect
        # ratio. (QIcon.pixmap() also keeps aspect, but
        # drawPixmap(rect, pixmap) would stretch the result to fill the
        # square — that squished the 3:4 Apple logo ~33% wider.)
        vb = renderer.viewBoxF()
        if vb.isValid() and vb.width() > 0 and vb.height() > 0:
            s = min(size / vb.width(), size / vb.height())
            w, h = vb.width() * s, vb.height() * s
            target = QRectF((size - w) / 2.0, (size - h) / 2.0, w, h)
        else:
            target = QRectF(0, 0, size, size)
        renderer.render(painter, target)
        painter.end()
        return pm

    def _is_empty(pm):
        img = pm.toImage()
        for y in range(img.height()):
            for x in range(img.width()):
                if img.pixelColor(x, y).alpha() > 0:
                    return False
        return True

    def _from_files():
        for path in _svg_file_candidates(resource_path):
            if os.path.isfile(path):
                alt = QSvgRenderer(path)
                if alt.isValid():
                    pm2 = _draw(alt)
                    if not _is_empty(pm2):
                        return pm2
        return None

    def _from_resource():
        if str(resource_path) in _DEAD_RESOURCES:
            return None
        renderer = QSvgRenderer(resource_path)
        if renderer.isValid():
            pm = _draw(renderer)
            if not _is_empty(pm):
                return pm
        _DEAD_RESOURCES.add(str(resource_path))
        return None

    frozen = bool(getattr(sys, "frozen", False)
                  or getattr(sys, "_MEIPASS", None))
    result = (_from_files() if frozen else _from_resource()) \
        or (_from_resource() if frozen else _from_files())
    if result is None:
        # Nothing rendered anywhere: a transparent pixmap of the right
        # size (same as the old failure mode, never a crash).
        result = QPixmap(px, px)
        result.setDevicePixelRatio(scale)
        result.fill(Qt.GlobalColor.transparent)
    _RAW_PIXMAP_CACHE[cache_key] = result
    return result


def theme_pixmap(resource_path: str, color_hex: str, size: int,
                 dpr: float = 1.0) -> QPixmap:
    """Rasterize a monochrome SVG at *size* logical pixels, tinted to a color.

    The SVG is scaled to *fit* the square (aspect ratio preserved, centered)
    via QSvgRenderer — never stretched. ``dpr`` renders extra device pixels
    on HiDPI screens and sets the pixmap's device pixel ratio accordingly.
    """
    # Deep copy: the raw render is cached and shared with color_icon
    # callers, and painting on the shared pixmap does NOT reliably
    # detach — a tint pass here would corrupt the cached raw render
    # for every later caller.
    pm = _render_svg_raw(resource_path, size, dpr).copy()
    painter = QPainter(pm)
    painter.setCompositionMode(
        QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pm.rect(), QColor(color_hex))
    painter.end()
    return pm


def color_icon(resource_path: str, size: int, dpr: float = 1.0) -> QIcon:
    """Render a full-color SVG at *size* logical pixels, WITHOUT tinting.

    Same fit logic as :func:`theme_pixmap` (viewBox scaled to fit the
    square, aspect preserved, centered) but the SVG's own colors and
    gradients survive — used for the 3D-style ``ws2-*`` menu icons, which
    ``theme_icon``/``theme_pixmap`` would flatten to a single color via
    their SourceIn tint pass.
    """
    return QIcon(_render_svg_raw(resource_path, size, dpr))


__all__ = [
    "ColorThemeManager", "DARK", "SKY", "WORKBENCH", "WS_BLUE", "ACCENT_PRESETS", "STYLES", "FONT_FAMILY",
    "AccentPicker", "t", "themed_stylesheet", "theme_icon",
    "theme_pixmap", "color_icon",
]
