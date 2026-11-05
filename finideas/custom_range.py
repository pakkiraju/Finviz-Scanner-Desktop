"""Finviz Elite custom From/To range codes for numeric filters.

Standard form (most Under/Over filters):
  {prefix}{from}to{to}   → between
  {prefix}{from}to       → at least from
  {prefix}to{to}         → at most to

High/Low distance form:
  {prefix}{from}to{to}-bhx  → % below high
  {prefix}{from}to{to}-alx  → % above low
  (also open-ended with missing from/to where Finviz allows)
"""

from __future__ import annotations

from dataclasses import dataclass


CUSTOM_SENTINEL = "__custom__"


@dataclass(frozen=True)
class CustomRangeSpec:
    """How to build a Custom… value for a filter field."""

    kind: str  # "range" | "perf" | "perf2" | "highlow"
    prefix: str
    unit: str = ""  # shown in dialog, e.g. "%", "$", "x", "K", "M", "$B"
    from_label: str = "From"
    to_label: str = "To"
    # highlow modes: (("Below High", "bhx"), ("Above Low", "alx"))
    modes: tuple[tuple[str, str], ...] = ()


def _fmt(n: float) -> str:
    if n == int(n):
        return str(int(n))
    return f"{n:g}"


def build_range_code(prefix: str, lo: float | None, hi: float | None) -> str:
    if lo is None and hi is None:
        raise ValueError("Enter at least a From or To value")
    if lo is not None and hi is not None and lo > hi:
        raise ValueError("From cannot be greater than To")
    if lo is not None and hi is None:
        return f"{prefix}{_fmt(lo)}to"
    if lo is None and hi is not None:
        return f"{prefix}to{_fmt(hi)}"
    return f"{prefix}{_fmt(lo)}to{_fmt(hi)}"


def build_highlow_code(
    prefix: str,
    mode: str,
    lo: float | None,
    hi: float | None,
) -> str:
    """mode is bhx (below high) or alx (above low)."""
    if mode not in ("bhx", "alx"):
        raise ValueError("Pick Below High or Above Low")
    if lo is None and hi is None:
        raise ValueError("Enter at least a From % or To %")
    if lo is not None and hi is not None and lo > hi:
        raise ValueError("From % cannot be greater than To %")
    if lo is not None and hi is None:
        body = f"{_fmt(lo)}to"
    elif lo is None and hi is not None:
        body = f"to{_fmt(hi)}"
    else:
        body = f"{_fmt(lo)}to{_fmt(hi)}"
    return f"{prefix}{body}-{mode}"


def describe_range_code(prefix: str, code: str, *, unit: str = "") -> str:
    if not code.startswith(prefix):
        return ""
    body = code[len(prefix) :]
    if "to" not in body:
        return ""
    # Skip plain under/over tokens (u5, o10) — no "to"
    u = f" {unit}" if unit else ""
    if body.endswith("to"):
        return f"Custom: ≥ {body[:-2]}{u}"
    if body.startswith("to"):
        return f"Custom: ≤ {body[2:]}{u}"
    lo, hi = body.split("to", 1)
    return f"Custom: {lo}{u} to {hi}{u}"


def describe_highlow_code(prefix: str, code: str) -> str:
    if not code.startswith(prefix):
        return ""
    body = code[len(prefix) :]
    mode = ""
    for suffix, label in (("-bhx", "below High"), ("-alx", "above Low")):
        if body.endswith(suffix):
            mode = label
            body = body[: -len(suffix)]
            break
    if not mode or "to" not in body:
        return ""
    if body.endswith("to"):
        return f"Custom: ≥ {body[:-2]}% {mode}"
    if body.startswith("to"):
        return f"Custom: ≤ {body[2:]}% {mode}"
    lo, hi = body.split("to", 1)
    return f"Custom: {lo}% to {hi}% {mode}"


def looks_like_custom_range(prefix: str, code: str) -> bool:
    """True if code is a from/to custom under this prefix (not a simple u/o token)."""
    if not code.startswith(prefix):
        return False
    body = code[len(prefix) :]
    return "to" in body
