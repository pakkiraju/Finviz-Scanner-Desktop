"""Persist open scanner windows + launcher geometry across launches."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SessionScanner:
    title: str
    signal: str = ""
    filters: list[str] = field(default_factory=list)
    sort: str = "-change"
    x: int = 100
    y: int = 100
    w: int = 780
    h: int = 520
    screen: str = ""
    poll_seconds: int = 15
    always_on_top: bool = False
    sound_alerts: bool = False
    alert_volume: int = 70
    order: int = 0


@dataclass
class SessionState:
    launcher: dict[str, int] | None = None
    scanners: list[SessionScanner] = field(default_factory=list)


def _session_path() -> Path:
    from finideas.settings import app_dir

    return app_dir() / "session.json"


def load_session() -> SessionState:
    path = _session_path()
    if not path.exists():
        return SessionState()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return SessionState()
        launcher = data.get("launcher")
        if not isinstance(launcher, dict):
            launcher = None
        else:
            try:
                launcher = {
                    "x": int(launcher["x"]),
                    "y": int(launcher["y"]),
                    "w": int(launcher["w"]),
                    "h": int(launcher["h"]),
                }
            except (KeyError, TypeError, ValueError):
                launcher = None

        scanners: list[SessionScanner] = []
        raw_list = data.get("scanners")
        if isinstance(raw_list, list):
            for i, item in enumerate(raw_list):
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title") or "").strip()
                filters = item.get("filters") or []
                if not isinstance(filters, list):
                    filters = []
                filters = [str(c) for c in filters if c]
                signal = str(item.get("signal") or "")
                if not title and not signal and not filters:
                    continue
                try:
                    scanners.append(
                        SessionScanner(
                            title=title or "Scanner",
                            signal=signal,
                            filters=filters,
                            sort=str(item.get("sort") or "-change"),
                            x=int(item.get("x", 100)),
                            y=int(item.get("y", 100)),
                            w=max(400, int(item.get("w", 780))),
                            h=max(300, int(item.get("h", 520))),
                            screen=str(item.get("screen") or ""),
                            poll_seconds=max(5, min(600, int(item.get("poll_seconds", 15)))),
                            always_on_top=bool(item.get("always_on_top", False)),
                            sound_alerts=bool(item.get("sound_alerts", False)),
                            alert_volume=max(0, min(100, int(item.get("alert_volume", 70)))),
                            order=int(item.get("order", i)),
                        )
                    )
                except (TypeError, ValueError) as e:
                    logger.warning("Skipping bad session scanner entry: %s", e)
        scanners.sort(key=lambda s: s.order)
        return SessionState(launcher=launcher, scanners=scanners)
    except Exception as e:
        logger.warning("Could not read session.json: %s", e)
        return SessionState()


def save_session(state: SessionState) -> None:
    payload: dict[str, Any] = {
        "launcher": state.launcher,
        "scanners": [asdict(s) for s in state.scanners],
    }
    try:
        _session_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning("Could not write session.json: %s", e)


def clear_session_scanners() -> None:
    state = load_session()
    state.scanners = []
    save_session(state)
