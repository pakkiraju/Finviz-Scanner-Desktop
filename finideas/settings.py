"""User settings (API key, etc.) stored locally — never commit secrets."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def app_dir() -> Path:
    """Writable app data lives in the project folder (settings, saved scans)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def settings_path() -> Path:
    return app_dir() / "settings.json"


def load_settings() -> dict[str, Any]:
    path = settings_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning("Could not read settings.json: %s", e)
        return {}


def save_settings(data: dict[str, Any]) -> None:
    settings_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_finviz_api_key() -> str:
    """Prefer saved settings, then FINVIZ_API_KEY env / .env."""
    key = str(load_settings().get("finviz_api_key") or "").strip()
    if key:
        return key
    return os.environ.get("FINVIZ_API_KEY", "").strip()


def set_finviz_api_key(key: str) -> None:
    data = load_settings()
    data["finviz_api_key"] = key.strip()
    save_settings(data)


def migrate_env_key_if_needed() -> None:
    """Copy .env / env key into settings.json once if settings has no key yet."""
    data = load_settings()
    if str(data.get("finviz_api_key") or "").strip():
        return
    env_key = os.environ.get("FINVIZ_API_KEY", "").strip()
    if env_key:
        set_finviz_api_key(env_key)
