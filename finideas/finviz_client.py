"""Finviz Elite screener CSV export client."""

from __future__ import annotations

import csv
import io
import logging
import os
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from finideas.filters import (
    MinFilters,
    build_finviz_filter_codes,
    parse_finviz_number,
    parse_market_cap_usd,
    row_passes_mins,
)
from finideas.scanners import ScannerSpec

logger = logging.getLogger(__name__)

# Extensionless paths avoid an extra 301 redirect from the legacy *.ashx URLs.
_EXPORT_HOST = "https://elite.finviz.com/export"
_SCREENER_HOST = "https://elite.finviz.com/screener"

# Compact trading columns: Ticker, Company, Market Cap, ATR, Rel Vol, Price, Change, Volume, Avg Volume
_EXPORT_COLUMNS = "1,2,6,49,64,65,66,67,63"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


def get_api_key() -> str | None:
    from finideas.settings import get_finviz_api_key

    key = get_finviz_api_key()
    return key or None


def _screen_params(spec: ScannerSpec, mins: MinFilters) -> dict[str, str]:
    codes = build_finviz_filter_codes(list(spec.base_filters), mins)
    params: dict[str, str] = {
        "v": "152",
        "ft": "4",
        "o": spec.sort or "-change",
    }
    if codes:
        params["f"] = ",".join(codes)
    if spec.signal:
        params["s"] = spec.signal
    return params


def build_export_url(spec: ScannerSpec, mins: MinFilters, *, api_key: str) -> str:
    params = _screen_params(spec, mins)
    params["c"] = _EXPORT_COLUMNS
    params["auth"] = api_key
    return f"{_EXPORT_HOST}?{urlencode(params)}"


def build_screener_url(spec: ScannerSpec, mins: MinFilters) -> str:
    return f"{_SCREENER_HOST}?{urlencode(_screen_params(spec, mins))}"


def _cell(row: dict, *names: str) -> str:
    for n in names:
        if n in row and str(row[n]).strip() not in ("", "-", "—"):
            return str(row[n]).strip()
        # case-insensitive fallback
    lower = {k.lower(): v for k, v in row.items()}
    for n in names:
        v = lower.get(n.lower())
        if v is not None and str(v).strip() not in ("", "-", "—"):
            return str(v).strip()
    return ""


def normalize_row(raw: dict) -> dict[str, Any]:
    ticker = _cell(raw, "Ticker", "ticker").upper()
    price_s = _cell(raw, "Price", "price")
    change_s = _cell(raw, "Change", "change")
    volume_s = _cell(raw, "Volume", "volume")
    rel_s = _cell(raw, "Relative Volume", "Rel Volume", "Rel Vol")
    atr_s = _cell(raw, "Average True Range", "ATR", "atr")
    mcap_s = _cell(raw, "Market Cap", "Market Cap.", "market_cap")
    company = _cell(raw, "Company", "company")
    avg_vol_s = _cell(raw, "Average Volume", "Avg Volume", "Avg Vol")

    price_num = parse_finviz_number(price_s)
    atr_num = parse_finviz_number(atr_s)
    rel_vol_num = parse_finviz_number(rel_s)
    # v=152 custom export volume columns are full share counts (not thousands).
    volume_shares = parse_finviz_number(volume_s)
    market_cap_usd = parse_market_cap_usd(mcap_s)

    if rel_vol_num is None and volume_shares is not None:
        avg = parse_finviz_number(avg_vol_s)
        if avg and avg > 0:
            rel_vol_num = volume_shares / avg

    return {
        "ticker": ticker,
        "company": company,
        "price": price_s,
        "price_num": price_num,
        "change": change_s,
        "change_num": parse_finviz_number(change_s),
        "volume": volume_s,
        "volume_shares": volume_shares,
        "rel_vol": f"{rel_vol_num:.2f}" if rel_vol_num is not None else rel_s,
        "rel_vol_num": rel_vol_num,
        "atr": atr_s,
        "atr_num": atr_num,
        "market_cap": mcap_s,
        "market_cap_usd": market_cap_usd,
    }


def _parse_csv(text: str) -> list[dict]:
    text = text.strip().lstrip("\ufeff")
    if not text or text.startswith("<"):
        return []
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


class FinvizClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout
        self._client = httpx.Client(headers=_HEADERS, timeout=timeout, follow_redirects=True)

    def close(self) -> None:
        self._client.close()

    def fetch(
        self,
        spec: ScannerSpec,
        mins: MinFilters | None = None,
        *,
        api_key: str | None = None,
    ) -> tuple[list[dict], float, str]:
        """Fetch and filter rows.

        Returns ``(rows, elapsed_sec, screener_url)``.
        Retries with base filters only if the custom filter URL fails, then applies
        mins locally.
        """
        mins = mins or MinFilters()
        key = api_key or get_api_key()
        if not key:
            raise RuntimeError("FINVIZ_API_KEY is not set")

        screener = build_screener_url(spec, mins)
        urls = [build_export_url(spec, mins, api_key=key)]
        # Fallback: base 52w high only (local mins still apply)
        if mins.any_set():
            urls.append(build_export_url(spec, MinFilters(), api_key=key))

        last_err: Exception | None = None
        raw_rows: list[dict] = []
        t0 = time.perf_counter()

        for i, url in enumerate(urls):
            try:
                raw_rows = self._get_csv(url)
                if raw_rows:
                    if i > 0:
                        logger.info("Custom filter URL empty/failed; used base filter + local mins")
                    break
            except Exception as e:
                last_err = e
                logger.warning("Export attempt %d failed: %s", i + 1, e)
                continue
        else:
            if last_err:
                raise last_err

        elapsed = time.perf_counter() - t0
        rows: list[dict] = []
        seen: set[str] = set()
        for raw in raw_rows:
            norm = normalize_row(raw)
            t = norm.get("ticker") or ""
            if not t or t in seen:
                continue
            if not row_passes_mins(norm, mins):
                continue
            seen.add(t)
            rows.append(norm)

        rows.sort(key=lambda r: (r.get("change_num") is not None, r.get("change_num") or 0.0), reverse=True)
        return rows, elapsed, screener

    def _get_csv(self, url: str) -> list[dict]:
        for attempt in range(4):
            resp = self._client.get(url)
            if resp.status_code == 429:
                wait = (2**attempt) * 5
                logger.warning("429 rate limit, sleeping %ss", wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            text = resp.text
            if text.lstrip().startswith("<"):
                low = text[:2000].lower()
                if "login" in low or "sign in" in low:
                    raise RuntimeError("Finviz returned a login page — check FINVIZ_API_KEY")
                raise RuntimeError("Finviz returned HTML instead of CSV")
            return _parse_csv(text)
        raise RuntimeError("Finviz rate-limited after retries")
