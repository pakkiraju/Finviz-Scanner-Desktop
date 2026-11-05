"""Persist named scanner filter presets across app restarts."""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

def _saved_scans_path() -> Path:
    from finideas.settings import app_dir

    return app_dir() / "saved_scans.json"


@dataclass
class SavedScan:
    id: str
    name: str
    signal: str = ""
    sort: str = "-change"
    # field_id -> finviz filter code (only non-Any selections)
    filters: dict[str, str] = field(default_factory=dict)
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "signal": self.signal,
            "sort": self.sort,
            "filters": dict(self.filters),
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> SavedScan | None:
        try:
            name = str(raw.get("name", "")).strip()
            sid = str(raw.get("id", "")).strip() or str(uuid.uuid4())
            if not name:
                return None
            filters_raw = raw.get("filters") or {}
            filters: dict[str, str] = {}
            if isinstance(filters_raw, dict):
                for k, v in filters_raw.items():
                    code = str(v or "").strip()
                    if code:
                        filters[str(k)] = code
            return cls(
                id=sid,
                name=name,
                signal=str(raw.get("signal") or "").strip(),
                sort=str(raw.get("sort") or "-change").strip() or "-change",
                filters=filters,
                updated_at=str(raw.get("updated_at") or ""),
            )
        except Exception as e:
            logger.warning("Bad saved scan entry: %s", e)
            return None

    def filter_codes(self) -> list[str]:
        return [c for c in self.filters.values() if c]


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_saved_scans() -> list[SavedScan]:
    path = _saved_scans_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("Could not read saved_scans.json: %s", e)
        return []
    items = data.get("scans") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []
    out: list[SavedScan] = []
    for raw in items:
        if isinstance(raw, dict):
            scan = SavedScan.from_dict(raw)
            if scan:
                out.append(scan)
    out.sort(key=lambda s: s.name.lower())
    return out


def save_saved_scans(scans: list[SavedScan]) -> None:
    payload = {"scans": [s.to_dict() for s in scans]}
    try:
        _saved_scans_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning("Could not write saved_scans.json: %s", e)
        raise


def find_by_id(scans: list[SavedScan], scan_id: str) -> SavedScan | None:
    for s in scans:
        if s.id == scan_id:
            return s
    return None


def find_by_name(scans: list[SavedScan], name: str) -> SavedScan | None:
    key = name.strip().lower()
    for s in scans:
        if s.name.lower() == key:
            return s
    return None


def upsert_scan(scan: SavedScan) -> list[SavedScan]:
    scans = load_saved_scans()
    existing = find_by_id(scans, scan.id) or find_by_name(scans, scan.name)
    scan.updated_at = _now_iso()
    if existing:
        scan.id = existing.id
        scans = [scan if s.id == existing.id else s for s in scans]
    else:
        if not scan.id:
            scan.id = str(uuid.uuid4())
        scans.append(scan)
    scans.sort(key=lambda s: s.name.lower())
    save_saved_scans(scans)
    return scans


def delete_scan(scan_id: str) -> list[SavedScan]:
    scans = [s for s in load_saved_scans() if s.id != scan_id]
    save_saved_scans(scans)
    return scans


def slugify_name(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return s or "scan"
