"""Independent scanner window with filters, table, and background polling."""

from __future__ import annotations

import logging
from datetime import datetime

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from finideas.filters import MinFilters
from finideas.finviz_client import FinvizClient, get_api_key
from finideas.layout import apply_geometry, get_window_geometry, set_window_geometry
from finideas.scanners import ScannerSpec
from finideas.ui.theme import SCANNER_NEW_ROW, TEXT_MUTED, apply_scanner_theme

# Day change colors (readable on dark navy)
_GREEN = QColor("#22c55e")
_RED = QColor("#ef4444")
_FLAT = QColor("#d6e4f0")

logger = logging.getLogger(__name__)

COLUMNS = [
    ("ticker", "Ticker"),
    ("price", "Price"),
    ("change", "Change %"),
    ("volume_display", "Volume"),
    ("rel_vol", "Rel Vol"),
    ("atr", "ATR"),
    ("market_cap", "Market Cap"),
]

_SORT_KEYS = {
    "ticker": "ticker",
    "price": "price_num",
    "change": "change_num",
    "volume_display": "volume_shares",
    "rel_vol": "rel_vol_num",
    "atr": "atr_num",
    "market_cap": "market_cap_usd",
}


def _fmt_shares(n: float | None) -> str:
    if n is None:
        return ""
    if n >= 1e9:
        return f"{n / 1e9:.2f}B"
    if n >= 1e6:
        return f"{n / 1e6:.2f}M"
    if n >= 1e3:
        return f"{n / 1e3:.1f}K"
    return f"{int(n):,}"


class ScannerTableModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict] = []
        self._highlight: set[str] = set()
        self._hi_brush = QBrush(QColor(SCANNER_NEW_ROW))

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return COLUMNS[section][1]
        return section + 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        key = COLUMNS[index.column()][0]
        ticker = row.get("ticker", "")

        if role == Qt.ItemDataRole.DisplayRole:
            if key == "volume_display":
                return _fmt_shares(row.get("volume_shares")) or row.get("volume", "")
            val = row.get(key, "")
            return "" if val is None else str(val)

        if role == Qt.ItemDataRole.ForegroundRole:
            ch = row.get("change_num")
            if ch is None:
                return _FLAT
            if ch > 0:
                return _GREEN
            if ch < 0:
                return _RED
            return _FLAT

        if role == Qt.ItemDataRole.BackgroundRole and ticker in self._highlight:
            return self._hi_brush

        if role == Qt.ItemDataRole.UserRole:
            sk = _SORT_KEYS.get(key)
            if not sk:
                return None
            if key == "ticker":
                return ticker
            return row.get(sk)

        return None

    def set_rows(self, rows: list[dict], highlight: set[str]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self._highlight = set(highlight)
        self.endResetModel()

    def ticker_at(self, row: int) -> str:
        if 0 <= row < len(self._rows):
            return self._rows[row].get("ticker", "")
        return ""


class FetchWorker(QThread):
    finished_ok = Signal(list, float, str)
    finished_err = Signal(str)

    def __init__(self, spec: ScannerSpec, mins: MinFilters, parent=None) -> None:
        super().__init__(parent)
        self.spec = spec
        self.mins = mins

    def run(self) -> None:
        client = FinvizClient()
        try:
            rows, elapsed, screener = client.fetch(self.spec, self.mins)
            self.finished_ok.emit(rows, elapsed, screener)
        except Exception as e:
            logger.exception("Fetch failed")
            self.finished_err.emit(str(e))
        finally:
            client.close()


class ScannerWindow(QMainWindow):
    layout_changed = Signal()

    def __init__(
        self,
        spec: ScannerSpec,
        instance_id: int,
        parent=None,
        *,
        geometry: dict | None = None,
        screen_name: str = "",
        poll_seconds: int | None = None,
        always_on_top: bool = False,
    ) -> None:
        super().__init__(parent)
        self.spec = spec
        self.instance_id = instance_id
        self.window_key = f"{spec.id}_{instance_id}"
        self._prev_tickers: set[str] = set()
        self._worker: FetchWorker | None = None
        self._paused = False
        self._rows: list[dict] = []
        self._sort_col = 2  # change %
        self._sort_order = Qt.SortOrder.DescendingOrder
        self._layout_save_timer = QTimer(self)
        self._layout_save_timer.setSingleShot(True)
        self._layout_save_timer.setInterval(400)
        self._layout_save_timer.timeout.connect(self.layout_changed.emit)

        self.setWindowTitle(f"{spec.title} #{instance_id}")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setMinimumSize(520, 360)
        self.resize(780, 520)
        apply_scanner_theme(self)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        controls = QHBoxLayout()
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 600)
        self.interval_spin.setValue(15 if poll_seconds is None else int(poll_seconds))
        self.interval_spin.setSuffix(" s")
        controls.addWidget(QLabel("Poll"))
        controls.addWidget(self.interval_spin)

        self.always_on_top = QCheckBox("Always on top")
        self.always_on_top.toggled.connect(self._toggle_on_top)
        controls.addWidget(self.always_on_top)
        if always_on_top:
            self.always_on_top.blockSignals(True)
            self.always_on_top.setChecked(True)
            self.always_on_top.blockSignals(False)
            flags = self.windowFlags()
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)

        self.apply_btn = QPushButton("Refresh")
        self.apply_btn.clicked.connect(self.refresh_now)
        controls.addWidget(self.apply_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setCheckable(True)
        self.pause_btn.toggled.connect(self._toggle_pause)
        controls.addWidget(self.pause_btn)

        controls.addStretch(1)
        root.addLayout(controls)

        self.model = ScannerTableModel(self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(False)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._copy_ticker)
        root.addWidget(self.table)

        self.status = QLabel("Ready")
        self.status.setStyleSheet(f"color: {TEXT_MUTED};")
        root.addWidget(self.status)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_now)
        self.interval_spin.valueChanged.connect(self._restart_timer)

        if geometry:
            apply_geometry(
                self,
                x=int(geometry.get("x", 100)),
                y=int(geometry.get("y", 100)),
                w=int(geometry.get("w", 780)),
                h=int(geometry.get("h", 520)),
                screen_name=screen_name,
            )
        else:
            geo = get_window_geometry(self.window_key)
            if geo:
                apply_geometry(
                    self,
                    x=geo["x"],
                    y=geo["y"],
                    w=geo["w"],
                    h=geo["h"],
                    screen_name=screen_name,
                )

        self._restart_timer()
        QTimer.singleShot(200, self.refresh_now)

    def _toggle_on_top(self, checked: bool) -> None:
        flags = self.windowFlags()
        if checked:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def _toggle_pause(self, paused: bool) -> None:
        self._paused = paused
        self.pause_btn.setText("Resume" if paused else "Pause")
        if paused:
            self._timer.stop()
            self.status.setText(self.status.text() + "  · paused")
        else:
            self._restart_timer()
            self.refresh_now()

    def _restart_timer(self) -> None:
        if self._paused:
            return
        self._timer.stop()
        self._timer.start(self.interval_spin.value() * 1000)

    def refresh_now(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        if not get_api_key():
            self.status.setText("FINVIZ_API_KEY is missing — enter it in the main window and Save Key")
            return
        self.apply_btn.setEnabled(False)
        self.status.setText("Fetching…")
        self._worker = FetchWorker(self.spec, MinFilters(), self)
        self._worker.finished_ok.connect(self._on_ok)
        self._worker.finished_err.connect(self._on_err)
        self._worker.start()

    def _on_ok(self, rows: list, elapsed: float, screener: str) -> None:
        self.apply_btn.setEnabled(True)
        new_set = {r.get("ticker", "") for r in rows if r.get("ticker")}
        highlight = new_set - self._prev_tickers if self._prev_tickers else set()
        self._prev_tickers = new_set
        self._rows = rows
        self._apply_sort(rows)
        self.model.set_rows(self._rows, highlight)
        self.table.horizontalHeader().setSortIndicator(self._sort_col, self._sort_order)
        now = datetime.now().strftime("%H:%M:%S")
        self.status.setStyleSheet("color: #9ab4c8;")
        self.status.setText(
            f"{len(rows)} rows · updated {now} · {elapsed * 1000:.0f} ms"
        )

    def _on_err(self, message: str) -> None:
        self.apply_btn.setEnabled(True)
        self.status.setStyleSheet("color: #f87171;")
        self.status.setText(f"Error: {message}")

    def _on_header_clicked(self, section: int) -> None:
        if section == self._sort_col:
            if self._sort_order == Qt.SortOrder.AscendingOrder:
                self._sort_order = Qt.SortOrder.DescendingOrder
            else:
                self._sort_order = Qt.SortOrder.AscendingOrder
        else:
            self._sort_col = section
            self._sort_order = Qt.SortOrder.AscendingOrder
        self._apply_sort(self._rows)
        self.model.set_rows(self._rows, self.model._highlight)
        self.table.horizontalHeader().setSortIndicator(self._sort_col, self._sort_order)

    def _apply_sort(self, rows: list[dict]) -> None:
        key = COLUMNS[self._sort_col][0]
        sk = _SORT_KEYS[key]
        reverse = self._sort_order == Qt.SortOrder.DescendingOrder

        def sort_val(r: dict):
            v = r.get(sk)
            if key == "ticker":
                return str(v or "")
            if v is None:
                return float("-inf") if reverse else float("inf")
            return v

        rows.sort(key=sort_val, reverse=reverse)
        self._rows = rows

    def _copy_ticker(self, index: QModelIndex) -> None:
        ticker = self.model.ticker_at(index.row())
        if not ticker:
            return
        QGuiApplication.clipboard().setText(ticker)
        self.status.setText(f"Copied {ticker}")

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        self._layout_save_timer.start()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._layout_save_timer.start()

    def closeEvent(self, event) -> None:
        geo = self.geometry()
        set_window_geometry(self.window_key, geo.x(), geo.y(), geo.width(), geo.height())
        self._timer.stop()
        if self._worker and self._worker.isRunning():
            self._worker.wait(2000)
        super().closeEvent(event)
