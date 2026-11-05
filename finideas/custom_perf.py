"""Build Finviz custom Performance filter codes (incl. intraday).

Finviz custom Performance URL form (requires ft=4):
  ta_perf_{from}to-{period}      → at least ``from``% over period
  ta_perf_to{to}-{period}        → at most ``to``% over period
  ta_perf_{from}to{to}-{period}  → between ``from`` and ``to``%

Periods include intraday Elite codes: i1, i2, i3, i5, i15, h, plus d/1w/4w/…
"""

from __future__ import annotations

PERF_PERIODS: tuple[tuple[str, str], ...] = (
    ("1 Minute", "i1"),
    ("2 Minutes", "i2"),
    ("3 Minutes", "i3"),
    ("5 Minutes", "i5"),
    ("15 Minutes", "i15"),
    ("Hour", "h"),
    ("Today", "d"),
    ("Week", "1w"),
    ("Month", "4w"),
    ("Quarter", "13w"),
    ("Half Year", "26w"),
    ("Year", "52w"),
    ("YTD", "ytd"),
)

PERF_PERIOD_LABELS = {code: label for label, code in PERF_PERIODS}

CUSTOM_PERF_SENTINEL = "__custom_perf__"
CUSTOM_PERF2_SENTINEL = "__custom_perf2__"


def _fmt_pct(n: float) -> str:
    if n == int(n):
        return str(int(n))
    return f"{n:g}"


def build_custom_perf_code(
    period: str,
    lo: float | None,
    hi: float | None,
    *,
    prefix: str = "ta_perf",
) -> str:
    """Return a Finviz ``f=`` token for custom performance."""
    period = period.strip()
    if not period:
        raise ValueError("Period is required")
    if lo is None and hi is None:
        raise ValueError("Enter at least a From % or To %")
    if lo is not None and hi is not None and lo > hi:
        raise ValueError("From % cannot be greater than To %")

    if lo is not None and hi is None:
        return f"{prefix}_{_fmt_pct(lo)}to-{period}"
    if lo is None and hi is not None:
        return f"{prefix}_to{_fmt_pct(hi)}-{period}"
    return f"{prefix}_{_fmt_pct(lo)}to{_fmt_pct(hi)}-{period}"


def describe_custom_perf_code(code: str) -> str:
    """Human label for a custom perf code, or empty if not custom-shaped."""
    for prefix, title in (("ta_perf2_", "Perf2"), ("ta_perf_", "Perf")):
        if not code.startswith(prefix):
            continue
        body = code[len(prefix) :]
        if "to" not in body or "-" not in body:
            return ""
        # split period after last '-' that precedes period token
        # forms: 1to-i1 | to-1-i1 | 1to5-i1 | -10to-1-i1
        period = None
        range_part = None
        for label, pcode in PERF_PERIODS:
            suffix = f"-{pcode}"
            if body.endswith(suffix):
                period = pcode
                range_part = body[: -len(suffix)]
                break
        if period is None or range_part is None:
            return ""
        period_label = PERF_PERIOD_LABELS.get(period, period)
        if range_part.endswith("to") and not range_part.endswith("to-"):
            # e.g. "1to" from "1to-i1" after stripping "-i1" → "1to"
            pass
        if range_part.endswith("to"):
            lo = range_part[:-2]
            return f"Custom: {period_label} ≥ {lo}%"
        if range_part.startswith("to"):
            hi = range_part[2:]
            return f"Custom: {period_label} ≤ {hi}%"
        if "to" in range_part:
            lo, hi = range_part.split("to", 1)
            return f"Custom: {period_label} {lo}% to {hi}%"
        return f"Custom: {period_label} ({code})"
    return ""


def is_custom_perf_code(code: str) -> bool:
    return bool(describe_custom_perf_code(code))
