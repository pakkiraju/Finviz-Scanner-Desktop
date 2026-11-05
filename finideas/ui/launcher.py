"""Main launcher — Finviz filter builder + saved scan presets."""

from __future__ import annotations

import uuid

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finideas.finviz_client import get_api_key
from finideas.saved_scans import (
    SavedScan,
    delete_scan,
    find_by_name,
    load_saved_scans,
    upsert_scan,
)
from finideas.scanners import make_custom_spec
from finideas.settings import get_finviz_api_key, set_finviz_api_key
from finideas.ui.filter_panel import FilterPanel
from finideas.ui.scanner_window import ScannerWindow
from finideas.ui.theme import DANGER, SUCCESS, apply_launcher_theme


class LauncherWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Finviz Scanner Desktop")
        self.setMinimumSize(1400, 900)
        self.resize(1680, 1040)
        self._windows: list[ScannerWindow] = []
        self._next_id = 1
        self._saved: list[SavedScan] = []
        self._closing_app = False

        apply_launcher_theme(self)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        header = QHBoxLayout()
        title = QLabel("Finviz Scanner Desktop")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #e8f1fa;")
        header.addWidget(title)
        header.addStretch(1)
        layout.addLayout(header)

        # API key row
        api_row = QHBoxLayout()
        api_row.addWidget(QLabel("Finviz API key"))
        self.api_edit = QLineEdit()
        self.api_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_edit.setPlaceholderText("Paste your Elite API key")
        self.api_edit.setMinimumWidth(320)
        self.api_edit.setText(get_finviz_api_key())
        api_row.addWidget(self.api_edit, 1)

        show_key = QPushButton("Show")
        show_key.setCheckable(True)
        show_key.setProperty("secondary", True)
        show_key.style().unpolish(show_key)
        show_key.style().polish(show_key)
        show_key.toggled.connect(self._toggle_api_visibility)
        api_row.addWidget(show_key)

        save_key_btn = self._secondary_btn("Save Key")
        save_key_btn.clicked.connect(self.save_api_key)
        api_row.addWidget(save_key_btn)

        self.key_label = QLabel("")
        api_row.addWidget(self.key_label)
        layout.addLayout(api_row)
        self._refresh_key_status()

        # Presets + primary actions (all up top)
        self.filter_panel = FilterPanel()

        presets_row = QHBoxLayout()
        presets_row.addWidget(QLabel("Presets"))
        self.saved_combo = QComboBox()
        self.saved_combo.setMinimumWidth(260)
        self.saved_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        presets_row.addWidget(self.saved_combo)

        open_preset_btn = QPushButton("Open Preset")
        open_preset_btn.clicked.connect(self.open_saved)
        presets_row.addWidget(open_preset_btn)

        edit_btn = self._secondary_btn("Edit Preset")
        edit_btn.clicked.connect(self.load_saved_into_editor)
        presets_row.addWidget(edit_btn)

        delete_btn = self._secondary_btn("Delete Preset")
        delete_btn.clicked.connect(self.delete_saved)
        presets_row.addWidget(delete_btn)

        save_btn = self._secondary_btn("Save Preset")
        save_btn.clicked.connect(self.save_current)
        presets_row.addWidget(save_btn)

        self.open_custom_btn = QPushButton("Open Scanner")
        self.open_custom_btn.setDefault(True)
        self.open_custom_btn.clicked.connect(self.open_custom)
        presets_row.addWidget(self.open_custom_btn)

        reset_btn = self._secondary_btn("Reset Filters")
        reset_btn.clicked.connect(self.filter_panel.reset_all)
        presets_row.addWidget(reset_btn)
        presets_row.addStretch(1)
        layout.addLayout(presets_row)

        layout.addWidget(self.filter_panel, 1)

        self.reload_saved_list()

    def _toggle_api_visibility(self, show: bool) -> None:
        self.api_edit.setEchoMode(
            QLineEdit.EchoMode.Normal if show else QLineEdit.EchoMode.Password
        )

    def _refresh_key_status(self) -> None:
        if get_api_key():
            self.key_label.setText("Key saved")
            self.key_label.setStyleSheet(f"color: {SUCCESS};")
        else:
            self.key_label.setText("No key — enter & Save Key")
            self.key_label.setStyleSheet(f"color: {DANGER};")

    def save_api_key(self) -> None:
        key = self.api_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "API key", "Paste your Finviz Elite API key first.")
            return
        try:
            set_finviz_api_key(key)
        except OSError as e:
            QMessageBox.critical(self, "Save failed", str(e))
            return
        self._refresh_key_status()
        QMessageBox.information(
            self,
            "API key saved",
            "Your Finviz API key was saved locally in settings.json (not committed to git).",
        )

    @staticmethod
    def _secondary_btn(text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setProperty("secondary", True)
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        return btn

    def reload_saved_list(self) -> None:
        selected_id = self._selected_saved_id()
        self._saved = load_saved_scans()
        self.saved_combo.blockSignals(True)
        self.saved_combo.clear()
        self.saved_combo.addItem("— none —", "")
        select_idx = 0
        for i, scan in enumerate(self._saved, start=1):
            tip_parts = []
            if scan.signal:
                tip_parts.append(f"Signal: {scan.signal}")
            if scan.filters:
                tip_parts.append(", ".join(list(scan.filters.values())[:6]))
            self.saved_combo.addItem(scan.name, scan.id)
            self.saved_combo.setItemData(
                i,
                " · ".join(tip_parts) if tip_parts else scan.name,
                Qt.ItemDataRole.ToolTipRole,
            )
            if scan.id == selected_id:
                select_idx = i
        self.saved_combo.setCurrentIndex(select_idx)
        self.saved_combo.blockSignals(False)

    def _selected_saved_id(self) -> str | None:
        sid = str(self.saved_combo.currentData() or "")
        return sid or None

    def _selected_saved(self) -> SavedScan | None:
        sid = self._selected_saved_id()
        if not sid:
            return None
        for s in self._saved:
            if s.id == sid:
                return s
        return None

    def save_current(self) -> None:
        if not self.filter_panel.has_selection():
            QMessageBox.information(
                self,
                "Nothing to save",
                "Select a Signal and/or at least one filter before saving.",
            )
            return

        settings = self.filter_panel.export_settings()
        default_name = settings["name"] or "My Scan"
        name, ok = QInputDialog.getText(
            self,
            "Save scan",
            "Name for this scan:",
            text=default_name,
        )
        if not ok:
            return
        name = name.strip()
        if not name:
            QMessageBox.warning(self, "Name required", "Enter a name to save the scan.")
            return

        existing = find_by_name(self._saved, name)
        scan_id = existing.id if existing else str(uuid.uuid4())
        if existing:
            ans = QMessageBox.question(
                self,
                "Overwrite?",
                f'A saved scan named "{name}" already exists. Overwrite it?',
            )
            if ans != QMessageBox.StandardButton.Yes:
                return

        scan = SavedScan(
            id=scan_id,
            name=name,
            signal=settings["signal"],
            sort=settings["sort"],
            filters=dict(settings["filters"]),
        )
        try:
            self._saved = upsert_scan(scan)
        except OSError as e:
            QMessageBox.critical(self, "Save failed", str(e))
            return

        self.filter_panel.name_edit.setText(name)
        self.reload_saved_list()
        for i in range(self.saved_combo.count()):
            if self.saved_combo.itemData(i) == scan.id:
                self.saved_combo.setCurrentIndex(i)
                break

    def load_saved_into_editor(self) -> None:
        scan = self._selected_saved()
        if not scan:
            QMessageBox.information(self, "No selection", "Pick a saved scan from the dropdown.")
            return
        self.filter_panel.apply_settings(
            name=scan.name,
            signal=scan.signal,
            sort=scan.sort,
            filters=scan.filters,
        )

    def open_saved(self) -> None:
        if not get_api_key():
            QMessageBox.warning(
                self,
                "API key needed",
                "Enter your Finviz API key at the top and click Save Key first.",
            )
            return
        scan = self._selected_saved()
        if not scan:
            QMessageBox.information(self, "No selection", "Pick a saved scan from the dropdown.")
            return
        if not scan.signal and not scan.filter_codes():
            QMessageBox.warning(self, "Empty scan", "That saved scan has no filters.")
            return
        spec = make_custom_spec(
            title=scan.name,
            filters=scan.filter_codes(),
            sort=scan.sort,
            signal=scan.signal,
            instance_id=self._next_id,
        )
        self._open_window(spec)

    def delete_saved(self) -> None:
        scan = self._selected_saved()
        if not scan:
            QMessageBox.information(self, "No selection", "Pick a saved scan from the dropdown.")
            return
        ans = QMessageBox.question(
            self,
            "Delete scan",
            f'Delete saved scan "{scan.name}"?',
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        self._saved = delete_scan(scan.id)
        self.reload_saved_list()

    def open_custom(self) -> None:
        if not get_api_key():
            QMessageBox.warning(
                self,
                "API key needed",
                "Enter your Finviz API key at the top and click Save Key first.",
            )
            return
        if not self.filter_panel.has_selection():
            QMessageBox.information(
                self,
                "No filters",
                "Select a Signal and/or at least one filter (not Any), then open again.",
            )
            return
        spec = make_custom_spec(
            title=self.filter_panel.scanner_title(),
            filters=self.filter_panel.selected_filter_codes(),
            sort=self.filter_panel.selected_sort(),
            signal=self.filter_panel.selected_signal(),
            instance_id=self._next_id,
        )
        self._open_window(spec)

    def _open_window(self, spec) -> None:
        win = ScannerWindow(spec, self._next_id)
        self._next_id += 1
        self._windows.append(win)
        win.destroyed.connect(lambda _=None, w=win: self._on_closed(w))
        win.show()

    def _on_closed(self, win: ScannerWindow) -> None:
        if self._closing_app:
            return
        try:
            self._windows.remove(win)
        except ValueError:
            pass

    def closeEvent(self, event) -> None:
        # Closing the launcher exits the whole app and all scanner windows.
        self._closing_app = True
        for w in list(self._windows):
            w.close()
        self._windows.clear()
        app = QApplication.instance()
        if app is not None:
            app.quit()
        super().closeEvent(event)
