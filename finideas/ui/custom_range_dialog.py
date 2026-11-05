"""Dialogs for Finviz Elite Custom… filter ranges."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from finideas.custom_perf import PERF_PERIODS, build_custom_perf_code, describe_custom_perf_code
from finideas.custom_range import (
    CustomRangeSpec,
    build_highlow_code,
    build_range_code,
    describe_highlow_code,
    describe_range_code,
)
from finideas.ui.theme import TEXT_DIM, TEXT_MUTED, apply_launcher_theme


class CustomRangeDialog(QDialog):
    """From/To (and optional period/mode) builder for Elite custom filters."""

    def __init__(
        self,
        parent=None,
        *,
        title: str,
        spec: CustomRangeSpec,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(380)
        self._spec = spec
        self.result_code = ""
        self.result_label = ""

        apply_launcher_theme(self)

        root = QVBoxLayout(self)
        unit = f" ({spec.unit})" if spec.unit else ""
        hint = QLabel(
            f"Set a custom range{unit}. Leave From or To blank for open-ended "
            "(e.g. From 5 / To blank = at least 5)."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {TEXT_DIM};")
        root.addWidget(hint)

        form = QFormLayout()

        self.period: QComboBox | None = None
        self.mode: QComboBox | None = None

        if spec.kind in ("perf", "perf2"):
            self.period = QComboBox()
            for label, code in PERF_PERIODS:
                self.period.addItem(label, code)
            self.period.setCurrentIndex(0)
            form.addRow("Period", self.period)
        elif spec.kind == "highlow" and spec.modes:
            self.mode = QComboBox()
            for label, code in spec.modes:
                self.mode.addItem(label, code)
            form.addRow("Mode", self.mode)

        self.from_edit = QLineEdit()
        self.from_edit.setPlaceholderText("blank = no minimum")
        form.addRow(f"{spec.from_label}{unit}", self.from_edit)

        self.to_edit = QLineEdit()
        self.to_edit.setPlaceholderText("blank = no maximum")
        form.addRow(f"{spec.to_label}{unit}", self.to_edit)
        root.addLayout(form)

        tip = QLabel("Matches Finviz Elite Custom… on the website screener.")
        tip.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        root.addWidget(tip)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _parse_optional(self, raw: str) -> float | None:
        s = raw.strip().replace("%", "").replace("$", "").replace(",", "")
        if not s:
            return None
        return float(s)

    def _accept(self) -> None:
        try:
            lo = self._parse_optional(self.from_edit.text())
            hi = self._parse_optional(self.to_edit.text())
            kind = self._spec.kind
            if kind in ("perf", "perf2"):
                assert self.period is not None
                period = str(self.period.currentData() or "")
                prefix = "ta_perf2" if kind == "perf2" else "ta_perf"
                code = build_custom_perf_code(period, lo, hi, prefix=prefix)
                label = describe_custom_perf_code(code) or code
            elif kind == "highlow":
                assert self.mode is not None
                mode = str(self.mode.currentData() or "bhx")
                code = build_highlow_code(self._spec.prefix, mode, lo, hi)
                label = describe_highlow_code(self._spec.prefix, code) or code
            else:
                code = build_range_code(self._spec.prefix, lo, hi)
                label = (
                    describe_range_code(self._spec.prefix, code, unit=self._spec.unit)
                    or code
                )
        except ValueError as e:
            QMessageBox.warning(self, "Custom filter", str(e))
            return
        except Exception:
            QMessageBox.warning(self, "Custom filter", "Enter valid numbers for From/To.")
            return
        self.result_code = code
        self.result_label = label
        self.accept()
