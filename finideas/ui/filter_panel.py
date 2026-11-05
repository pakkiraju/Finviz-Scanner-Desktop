"""Finviz-style filter grid for building custom scanners."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from finideas.custom_perf import (
    CUSTOM_PERF2_SENTINEL,
    CUSTOM_PERF_SENTINEL,
    describe_custom_perf_code,
    is_custom_perf_code,
)
from finideas.filter_catalog import (
    CATEGORIES,
    FILTER_FIELDS,
    SIGNAL_OPTIONS,
    SORT_OPTIONS,
    FilterField,
    FilterOption,
    fields_by_category,
)
from finideas.ui.custom_perf_dialog import CustomPerfDialog
from finideas.ui.theme import ACTIVE_TEXT, TEXT_DIM, TEXT_MUTED, combo_stylesheet


class FilterCombo(QComboBox):
    """Combo that stores Finviz codes and highlights when not Any."""

    def __init__(
        self,
        options: tuple[FilterOption, ...],
        parent=None,
        *,
        highlight_when_set: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setMinimumWidth(170)
        self._highlight_when_set = highlight_when_set
        for opt in options:
            self.addItem(opt.label, opt.code)
        self.currentIndexChanged.connect(self._refresh_active_style)
        self._refresh_active_style()

    def code(self) -> str:
        return str(self.currentData() or "")

    def is_active(self) -> bool:
        if not self._highlight_when_set:
            return False
        code = self.code()
        return bool(code) and not code.startswith("__custom_perf")

    def _refresh_active_style(self) -> None:
        active = self.is_active()
        self.setProperty("filterActive", active)
        self.setStyleSheet(combo_stylesheet(active=active))


def _link_combos(a: FilterCombo, b: FilterCombo) -> None:
    def sync(_src: FilterCombo, dst: FilterCombo, idx: int) -> None:
        if dst.currentIndex() != idx:
            dst.blockSignals(True)
            dst.setCurrentIndex(idx)
            dst.blockSignals(False)
            dst._refresh_active_style()

    a.currentIndexChanged.connect(lambda idx: sync(a, b, idx))
    b.currentIndexChanged.connect(lambda idx: sync(b, a, idx))


def _ensure_option(combo: FilterCombo, label: str, code: str) -> int:
    """Ensure combo has item (label, code); return its index."""
    for i in range(combo.count()):
        if str(combo.itemData(i) or "") == code:
            combo.setItemText(i, label)
            return i
    insert_at = combo.count()
    for i in range(combo.count()):
        data = str(combo.itemData(i) or "")
        if data.startswith("__custom_perf"):
            insert_at = i
            break
    combo.insertItem(insert_at, label, code)
    return insert_at


class FilterPanel(QWidget):
    """Tabbed filter builder matching Finviz All / category views."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._masters: dict[str, FilterCombo] = {}
        self._views: dict[str, list[FilterCombo]] = {}
        self._field_labels: dict[str, list[QLabel]] = {}
        self._prev_index: dict[str, int] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        top = QHBoxLayout()
        top.addWidget(self._dim_label("Signal"))
        self.signal_combo = FilterCombo(SIGNAL_OPTIONS)
        self.signal_combo.setMinimumWidth(220)
        self.signal_combo.setMaxVisibleItems(24)
        top.addWidget(self.signal_combo)
        top.addWidget(self._dim_label("Sort"))
        self.sort_combo = FilterCombo(SORT_OPTIONS, highlight_when_set=False)
        top.addWidget(self.sort_combo)
        top.addWidget(self._dim_label("Name"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Custom Scanner")
        self.name_edit.setMinimumWidth(160)
        top.addWidget(self.name_edit)
        top.addStretch(1)
        root.addLayout(top)

        for field in FILTER_FIELDS:
            master = FilterCombo(field.options)
            self._masters[field.id] = master
            self._views[field.id] = []
            self._field_labels[field.id] = []
            self._prev_index[field.id] = 0
            # Masters are not shown; views drive the UI. Still watch masters for programmatic changes.
            master.currentIndexChanged.connect(
                lambda idx, fid=field.id, c=master: self._on_combo_index(fid, c, idx)
            )

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_grid(FILTER_FIELDS), "All")
        for cat in CATEGORIES:
            self.tabs.addTab(self._build_grid(fields_by_category(cat)), cat)
        root.addWidget(self.tabs, 1)

        self.summary = QLabel("No filters selected")
        self.summary.setStyleSheet(f"color: {TEXT_MUTED};")
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)

        self.signal_combo.currentIndexChanged.connect(self._refresh_summary)
        self._refresh_summary()

    @staticmethod
    def _dim_label(text: str) -> QLabel:
        lab = QLabel(text)
        lab.setStyleSheet(f"color: {TEXT_DIM}; font-weight: 600;")
        return lab

    def _build_grid(self, fields: tuple[FilterField, ...]) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        host = QWidget()
        grid = QGridLayout(host)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(6)

        cols = 5
        for i, field in enumerate(fields):
            r, c = divmod(i, cols)
            cell = QWidget()
            form = QFormLayout(cell)
            form.setContentsMargins(0, 0, 0, 0)
            form.setSpacing(2)

            label = QLabel(field.label)
            label.setStyleSheet(f"color: {TEXT_DIM};")

            view = FilterCombo(field.options)
            view.setMinimumWidth(140)
            master = self._masters[field.id]
            view.setCurrentIndex(master.currentIndex())
            view._refresh_active_style()
            _link_combos(master, view)
            # Views are what the user clicks — must handle Custom… here (masters are hidden).
            view.currentIndexChanged.connect(
                lambda idx, fid=field.id, c=view: self._on_combo_index(fid, c, idx)
            )
            self._views[field.id].append(view)
            self._field_labels[field.id].append(label)

            form.addRow(label, view)
            grid.addWidget(cell, r, c)
            self._style_field_label(field.id)

        for c in range(cols):
            grid.setColumnStretch(c, 1)

        scroll.setWidget(host)
        return scroll

    def _on_combo_index(self, field_id: str, combo: FilterCombo, idx: int) -> None:
        # Ignore sync updates that blocked signals on other combos; only react when
        # this combo is the one the user (or apply_settings) actually changed.
        if combo.signalsBlocked():
            return
        code = str(combo.itemData(idx) or "")
        if code in (CUSTOM_PERF_SENTINEL, CUSTOM_PERF2_SENTINEL):
            self._prompt_custom_perf(field_id, code)
            return
        if code.startswith("__custom_perf"):
            return
        self._prev_index[field_id] = idx
        self._style_field_label(field_id)
        self._refresh_summary()

    def _prompt_custom_perf(self, field_id: str, sentinel: str) -> None:
        # Guard against All + category tabs both firing for linked combos.
        if getattr(self, "_custom_dialog_open", False):
            return
        self._custom_dialog_open = True
        try:
            prefix = "ta_perf2" if sentinel == CUSTOM_PERF2_SENTINEL else "ta_perf"
            title = "Custom Performance 2" if prefix == "ta_perf2" else "Custom Performance"
            dlg = CustomPerfDialog(self, title=title, prefix=prefix)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                self._revert_field(field_id)
                return
            self._apply_custom_code(field_id, dlg.result_label, dlg.result_code)
        finally:
            self._custom_dialog_open = False

    def _revert_field(self, field_id: str) -> None:
        prev = self._prev_index.get(field_id, 0)
        master = self._masters[field_id]
        master.blockSignals(True)
        master.setCurrentIndex(prev)
        master.blockSignals(False)
        master._refresh_active_style()
        for view in self._views.get(field_id, []):
            view.blockSignals(True)
            view.setCurrentIndex(prev)
            view.blockSignals(False)
            view._refresh_active_style()
        self._style_field_label(field_id)
        self._refresh_summary()

    def _apply_custom_code(self, field_id: str, label: str, code: str) -> None:
        master = self._masters[field_id]
        combos = [master, *self._views.get(field_id, [])]
        for combo in combos:
            combo.blockSignals(True)
            idx = _ensure_option(combo, label, code)
            combo.setCurrentIndex(idx)
            combo.blockSignals(False)
            combo._refresh_active_style()
        self._prev_index[field_id] = master.currentIndex()
        self._style_field_label(field_id)
        self._refresh_summary()

    def _style_field_label(self, field_id: str) -> None:
        code = self._masters[field_id].code()
        active = bool(code) and not code.startswith("__custom_perf")
        if active:
            style = "color: #fbbf24; font-weight: 700;"
        else:
            style = f"color: {TEXT_DIM}; font-weight: 400;"
        for lab in self._field_labels.get(field_id, []):
            lab.setStyleSheet(style)

    def _refresh_summary(self) -> None:
        parts: list[str] = []
        if self.signal_combo.code():
            parts.append(f"Signal: {self.signal_combo.currentText()}")
        for field in FILTER_FIELDS:
            combo = self._masters[field.id]
            code = combo.code()
            if code and not code.startswith("__custom_perf"):
                parts.append(f"{field.label}: {combo.currentText()}")
        if parts:
            self.summary.setText(" · ".join(parts))
            self.summary.setStyleSheet("color: #fbbf24;")
        else:
            self.summary.setText("No filters selected")
            self.summary.setStyleSheet(f"color: {TEXT_MUTED};")

    def selected_filter_codes(self) -> list[str]:
        out: list[str] = []
        for f in FILTER_FIELDS:
            code = self._masters[f.id].code()
            if code and not code.startswith("__custom_perf"):
                out.append(code)
        return out

    def selected_signal(self) -> str:
        return self.signal_combo.code()

    def selected_sort(self) -> str:
        return self.sort_combo.code() or "-change"

    def scanner_title(self) -> str:
        name = self.name_edit.text().strip()
        if name:
            return name
        bits: list[str] = []
        if self.signal_combo.code():
            bits.append(self.signal_combo.currentText())
        for field_id in ("performance", "performance2", "highlow52w", "gap", "rel_volume", "price"):
            combo = self._masters.get(field_id)
            if combo:
                code = combo.code()
                if code and not code.startswith("__custom_perf"):
                    bits.append(combo.currentText())
        if not bits:
            for field in FILTER_FIELDS:
                combo = self._masters[field.id]
                code = combo.code()
                if code and not code.startswith("__custom_perf"):
                    bits.append(f"{field.label} {combo.currentText()}")
                if len(bits) >= 2:
                    break
        return " · ".join(bits) if bits else "Custom Scanner"

    def has_selection(self) -> bool:
        return bool(self.selected_signal() or self.selected_filter_codes())

    def selected_filters_by_field(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for field in FILTER_FIELDS:
            code = self._masters[field.id].code()
            if code and not code.startswith("__custom_perf"):
                out[field.id] = code
        return out

    def export_settings(self) -> dict:
        return {
            "name": self.name_edit.text().strip() or self.scanner_title(),
            "signal": self.selected_signal(),
            "sort": self.selected_sort(),
            "filters": self.selected_filters_by_field(),
        }

    def apply_settings(
        self,
        *,
        name: str = "",
        signal: str = "",
        sort: str = "-change",
        filters: dict[str, str] | None = None,
    ) -> None:
        self.reset_all()
        if name:
            self.name_edit.setText(name)
        self._set_combo_by_code(self.signal_combo, signal)
        self._set_combo_by_code(self.sort_combo, sort or "-change")
        for field_id, code in (filters or {}).items():
            master = self._masters.get(field_id)
            if not master or not code:
                continue
            if is_custom_perf_code(code):
                label = describe_custom_perf_code(code) or code
                self._apply_custom_code(field_id, label, code)
                continue
            self._set_combo_by_code(master, code)
            for view in self._views.get(field_id, []):
                self._set_combo_by_code(view, code)
            self._prev_index[field_id] = master.currentIndex()
            self._style_field_label(field_id)
        self._refresh_summary()

    @staticmethod
    def _set_combo_by_code(combo: FilterCombo, code: str) -> None:
        target = code or ""
        for i in range(combo.count()):
            if str(combo.itemData(i) or "") == target:
                combo.setCurrentIndex(i)
                combo._refresh_active_style()
                return
        combo.setCurrentIndex(0)
        combo._refresh_active_style()

    def reset_all(self) -> None:
        self.signal_combo.setCurrentIndex(0)
        self.signal_combo._refresh_active_style()
        self.sort_combo.setCurrentIndex(0)
        self.sort_combo._refresh_active_style()
        self.name_edit.clear()
        for field_id, combo in self._masters.items():
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
            combo._refresh_active_style()
            for view in self._views.get(field_id, []):
                view.blockSignals(True)
                view.setCurrentIndex(0)
                view.blockSignals(False)
                view._refresh_active_style()
            self._prev_index[field_id] = 0
            self._style_field_label(field_id)
        self._refresh_summary()
