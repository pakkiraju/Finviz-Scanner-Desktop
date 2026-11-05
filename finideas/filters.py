"""Blank-safe min filters and FinViz ``f=`` filter codes."""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from typing import Any


@dataclass
class MinFilters:
    """Optional minimums. ``None`` means the field is not filtered."""

    price: float | None = None
    atr: float | None = None
    current_volume: float | None = None  # shares
    relative_volume: float | None = None
    market_cap: float | None = None  # USD

    def any_set(self) -> bool:
        return any(getattr(self, f.name) is not None for f in fields(self))


def parse_optional_number(raw: str | None, *, volume: bool = False, market_cap: bool = False) -> float | None:
    """Parse a filter box. Empty / whitespace → ``None`` (no filter)."""
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "").replace("$", "")
    if not s:
        return None

    if volume or market_cap:
        m = re.match(r"^([\d.]+)\s*([KMBTkmbt])?$", s)
        if not m:
            try:
                return float(s)
            except ValueError:
                return None
        val = float(m.group(1))
        suffix = (m.group(2) or "").upper()
        mult = {"": 1.0, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}[suffix]
        return val * mult

    try:
        return float(s)
    except ValueError:
        return None


def parse_filters_from_text(
    *,
    price: str = "",
    atr: str = "",
    current_volume: str = "",
    relative_volume: str = "",
    market_cap: str = "",
) -> MinFilters:
    return MinFilters(
        price=parse_optional_number(price),
        atr=parse_optional_number(atr),
        current_volume=parse_optional_number(current_volume, volume=True),
        relative_volume=parse_optional_number(relative_volume),
        market_cap=parse_optional_number(market_cap, market_cap=True),
    )


def _fmt_num(n: float) -> str:
    if n == int(n):
        return str(int(n))
    return f"{n:g}"


def market_cap_over_code(usd: float) -> str | None:
    """Nearest FinViz market-cap 'over' bucket for the server-side filter."""
    if usd <= 0:
        return None
    # FinViz buckets: microover $50M+, smallover $300M+, midover $2B+, largeover $10B+
    if usd >= 10e9:
        return "cap_largeover"
    if usd >= 2e9:
        return "cap_midover"
    if usd >= 300e6:
        return "cap_smallover"
    if usd >= 50e6:
        return "cap_microover"
    # Below micro: no reliable "over" preset; rely on local filter only.
    return None


def build_finviz_filter_codes(base: list[str], mins: MinFilters) -> list[str]:
    """Merge scanner base filters with optional min codes for the export URL."""
    codes = list(base)
    if mins.price is not None and mins.price > 0:
        codes.append(f"sh_price_o{_fmt_num(mins.price)}")
    if mins.atr is not None and mins.atr > 0:
        codes.append(f"ta_averagetruerange_o{_fmt_num(mins.atr)}")
    if mins.current_volume is not None and mins.current_volume > 0:
        # FinViz sh_curvol_o is in thousands of shares.
        thousands = max(1, int(round(mins.current_volume / 1000.0)))
        codes.append(f"sh_curvol_o{thousands}")
    if mins.relative_volume is not None and mins.relative_volume > 0:
        codes.append(f"sh_relvol_o{_fmt_num(mins.relative_volume)}")
    if mins.market_cap is not None:
        cap = market_cap_over_code(mins.market_cap)
        if cap:
            codes.append(cap)
    # Preserve order, drop duplicates
    seen: set[str] = set()
    out: list[str] = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def parse_finviz_number(raw: Any) -> float | None:
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "").replace("$", "").replace("%", "")
    if not s or s in ("-", "—", "N/A"):
        return None
    m = re.match(r"^([\d.-]+)\s*([KMBTkmbt])?$", s)
    if not m:
        try:
            return float(s)
        except ValueError:
            return None
    val = float(m.group(1))
    suffix = (m.group(2) or "").upper()
    if suffix == "K":
        val *= 1e3
    elif suffix == "M":
        val *= 1e6
    elif suffix == "B":
        val *= 1e9
    elif suffix == "T":
        val *= 1e12
    return val


def parse_market_cap_usd(raw: Any) -> float | None:
    """Parse Market Cap cell. Plain numbers without suffix are millions of USD (FinViz style)."""
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "").replace("$", "")
    if not s or s in ("-", "—"):
        return None
    m = re.match(r"^([\d.-]+)\s*([KMBTkmbt])?$", s)
    if not m:
        try:
            return float(s) * 1e6
        except ValueError:
            return None
    val = float(m.group(1))
    suffix = (m.group(2) or "").upper()
    if not suffix:
        return val * 1e6
    if suffix == "K":
        return val * 1e3
    if suffix == "M":
        return val * 1e6
    if suffix == "B":
        return val * 1e9
    if suffix == "T":
        return val * 1e12
    return val


def row_passes_mins(row: dict, mins: MinFilters) -> bool:
    """Local exact filter pass after CSV parse. Blank mins never reject."""
    if mins.price is not None:
        p = row.get("price_num")
        if p is None or p < mins.price:
            return False
    if mins.atr is not None:
        a = row.get("atr_num")
        if a is None or a < mins.atr:
            return False
    if mins.current_volume is not None:
        v = row.get("volume_shares")
        if v is None or v < mins.current_volume:
            return False
    if mins.relative_volume is not None:
        rv = row.get("rel_vol_num")
        if rv is None or rv < mins.relative_volume:
            return False
    if mins.market_cap is not None:
        mc = row.get("market_cap_usd")
        if mc is None or mc < mins.market_cap:
            return False
    return True
