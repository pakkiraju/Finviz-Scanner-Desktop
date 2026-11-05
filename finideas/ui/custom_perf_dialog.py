"""Dialog to build a Finviz custom Performance filter (incl. 1m/2m/5m)."""

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
from finideas.ui.theme import TEXT_DIM, TEXT_MUTED, apply_launcher_theme


class CustomPerfDialog(QDialog):
    def __init__(self, parent=None, *, title: str = "Custom Performance", prefix: str = "ta_perf") -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(360)
        self._prefix = prefix
        self.result_code = ""
        self.result_label = ""

        apply_launcher_theme(self)

        root = QVBoxLayout(self)
        hint = QLabel(
            "Set period and % range. Leave From or To blank for open-ended "
            "(e.g. From 1, To blank = at least +1%). Use 1/2/5 Minute for intraday."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {TEXT_DIM};")
        root.addWidget(hint)

        form = QFormLayout()
        self.period = QComboBox()
        for label, code in PERF_PERIODS:
            self.period.addItem(label, code)
        # Default to 1 Minute for daytrading use case
        self.period.setCurrentIndex(0)
        form.addRow("Period", self.period)

        self.from_edit = QLineEdit()
        self.from_edit.setPlaceholderText("e.g. 1  (blank = no min)")
        form.addRow("From %", self.from_edit)

        self.to_edit = QLineEdit()
        self.to_edit.setPlaceholderText("e.g. blank for open, or -1 for losers")
        form.addRow("To %", self.to_edit)
        root.addLayout(form)

        examples = QLabel(
            "Examples: 1m ≥1% → From 1 / To blank · 5m ≥2% → Period 5 Minutes, From 2 · "
            "1m ≤-1% → From blank / To -1"
        )
        examples.setWordWrap(True)
        examples.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        root.addWidget(examples)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _parse_optional(self, raw: str) -> float | None:
        s = raw.strip().replace("%", "")
        if not s:
            return None
        return float(s)

    def _accept(self) -> None:
        try:
            lo = self._parse_optional(self.from_edit.text())
            hi = self._parse_optional(self.to_edit.text())
            period = str(self.period.currentData() or "")
            code = build_custom_perf_code(period, lo, hi, prefix=self._prefix)
        except ValueError as e:
            QMessageBox.warning(self, "Custom Performance", str(e))
            return
        except Exception:
            QMessageBox.warning(self, "Custom Performance", "Enter valid numbers for From/To %.")
            return
        self.result_code = code
        self.result_label = describe_custom_perf_code(code) or code
        self.accept()
