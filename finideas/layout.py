"""Persist scanner window geometry."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

def _layout_path() -> Path:
    from finideas.settings import app_dir

    return app_dir() / "layout.json"


def load_layout() -> dict[str, Any]:
    path = _layout_path()
    if not path.exists():
        return {"windows": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"windows": {}}
        data.setdefault("windows", {})
        return data
    except Exception as e:
        logger.warning("Could not read layout.json: %s", e)
        return {"windows": {}}


def save_layout(data: dict[str, Any]) -> None:
    try:
        _layout_path().write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning("Could not write layout.json: %s", e)


def get_window_geometry(window_key: str) -> dict[str, int] | None:
    data = load_layout()
    geo = data.get("windows", {}).get(window_key)
    if not isinstance(geo, dict):
        return None
    try:
        return {
            "x": int(geo["x"]),
            "y": int(geo["y"]),
            "w": int(geo["w"]),
            "h": int(geo["h"]),
        }
    except (KeyError, TypeError, ValueError):
        return None


def set_window_geometry(window_key: str, x: int, y: int, w: int, h: int) -> None:
    data = load_layout()
    data.setdefault("windows", {})[window_key] = {"x": x, "y": y, "w": w, "h": h}
    save_layout(data)


def screen_name_for_widget(widget) -> str:
    """Return Qt screen name for a widget, or empty string."""
    try:
        scr = widget.screen()
        return scr.name() if scr is not None else ""
    except Exception:
        return ""


def apply_geometry(
    widget,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    screen_name: str = "",
) -> None:
    """Place a window at saved coords, preferring the named screen when available."""
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtCore import QRect

    w = max(400, int(w))
    h = max(300, int(h))
    target = None
    if screen_name:
        for scr in QGuiApplication.screens():
            if scr.name() == screen_name:
                target = scr
                break

    rect = QRect(int(x), int(y), w, h)
    if target is not None:
        # If the saved rect barely intersects the target screen, snap onto it.
        if not target.geometry().intersects(rect.adjusted(20, 20, -20, -20)):
            ag = target.availableGeometry()
            rect = QRect(ag.x() + 40, ag.y() + 40, w, min(h, ag.height() - 80))
    else:
        # Clamp into the virtual desktop so the window is not lost off-screen.
        virtual = QGuiApplication.primaryScreen()
        if virtual is not None:
            vg = QGuiApplication.primaryScreen().virtualGeometry()
            if not vg.intersects(rect):
                ag = virtual.availableGeometry()
                rect = QRect(ag.x() + 40, ag.y() + 40, w, h)

    widget.setGeometry(rect)
