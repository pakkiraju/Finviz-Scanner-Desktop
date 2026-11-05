"""Scanner definitions. Custom builders construct ScannerSpec the same way."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScannerSpec:
    id: str
    title: str
    base_filters: tuple[str, ...] = field(default_factory=tuple)
    sort: str = "-change"
    description: str = ""
    signal: str = ""  # Finviz screener ``s=`` preset (top gainers, etc.)


NEW_52W_HIGH = ScannerSpec(
    id="new_52w_high",
    title="New 52-Week High",
    base_filters=("ta_highlow52w_nh",),
    sort="-change",
    description="Stocks making a new 52-week high today",
)

# Registry for presets
SCANNERS: dict[str, ScannerSpec] = {
    NEW_52W_HIGH.id: NEW_52W_HIGH,
}


def make_custom_spec(
    *,
    title: str,
    filters: list[str] | tuple[str, ...],
    sort: str = "-change",
    signal: str = "",
    instance_id: int = 0,
) -> ScannerSpec:
    codes = tuple(c for c in filters if c)
    return ScannerSpec(
        id=f"custom_{instance_id}",
        title=title or "Custom Scanner",
        base_filters=codes,
        sort=sort or "-change",
        signal=signal or "",
        description="Custom scanner from launcher filters",
    )
