"""Finviz-inspired dark blue theme for Finviz Scanner Desktop."""

from __future__ import annotations

# Core palette
BG = "#0c1e30"
BG_RAISED = "#12283f"
BG_INPUT = "#16324f"
BG_INPUT_HOVER = "#1a3a5c"
BG_TAB = "#0f2438"
BORDER = "#2a4d6e"
BORDER_SOFT = "#1e3a55"
TEXT = "#d6e4f0"
TEXT_DIM = "#9ab4c8"
TEXT_MUTED = "#6f879c"
ACCENT = "#3b82f6"
ACCENT_HOVER = "#60a5fa"
SUCCESS = "#34d399"
DANGER = "#f87171"

# Active filter (changed from Any) — high-visibility amber
ACTIVE_BG = "#e8a317"
ACTIVE_BG_HOVER = "#f0b429"
ACTIVE_TEXT = "#0b1a28"
ACTIVE_BORDER = "#ffc94a"

# Scanner windows: slightly deeper navy
SCANNER_BG = "#081624"
SCANNER_RAISED = "#0d2034"
SCANNER_INPUT = "#132a42"
SCANNER_ALT_ROW = "#0f2438"
SCANNER_NEW_ROW = "#1a4d3a"

_COMBO_BASE = f"""
QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 22px;
}}
QComboBox:hover {{
    background-color: {BG_INPUT_HOVER};
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_RAISED};
    color: {TEXT};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    selection-color: white;
    outline: 0;
}}
"""

_COMBO_ACTIVE = f"""
QComboBox {{
    background-color: {ACTIVE_BG};
    color: {ACTIVE_TEXT};
    border: 1px solid {ACTIVE_BORDER};
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 22px;
    font-weight: 600;
}}
QComboBox:hover {{
    background-color: {ACTIVE_BG_HOVER};
    border-color: {ACTIVE_BORDER};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_RAISED};
    color: {TEXT};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    selection-color: white;
    outline: 0;
}}
"""

LAUNCHER_QSS = f"""
QMainWindow, QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-size: 12px;
}}
QLabel {{
    color: {TEXT};
    background: transparent;
}}
QLineEdit {{
    background-color: {BG_INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}
QLineEdit::placeholder {{
    color: {TEXT_MUTED};
}}
QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 22px;
}}
QComboBox:hover {{
    background-color: {BG_INPUT_HOVER};
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_RAISED};
    color: {TEXT};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    selection-color: white;
    outline: 0;
}}
QPushButton {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 7px 14px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton:pressed {{
    background-color: #2563eb;
}}
QPushButton:disabled {{
    background-color: {BORDER_SOFT};
    color: {TEXT_MUTED};
}}
QPushButton[secondary="true"] {{
    background-color: {BG_INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
}}
QPushButton[secondary="true"]:hover {{
    background-color: {BG_INPUT_HOVER};
    border-color: {ACCENT};
}}
QListWidget {{
    background-color: {BG_RAISED};
    color: {TEXT};
    border: 1px solid {BORDER_SOFT};
    border-radius: 6px;
    padding: 4px;
    outline: 0;
}}
QListWidget::item {{
    padding: 6px 8px;
    border-radius: 4px;
}}
QListWidget::item:selected {{
    background-color: {ACCENT};
    color: white;
}}
QListWidget::item:hover:!selected {{
    background-color: {BG_INPUT};
}}
QInputDialog {{
    background-color: {BG_RAISED};
    color: {TEXT};
}}
QTabWidget::pane {{
    border: 1px solid {BORDER_SOFT};
    border-radius: 6px;
    background-color: {BG_TAB};
    top: -1px;
}}
QTabBar::tab {{
    background-color: {BG_RAISED};
    color: {TEXT_DIM};
    border: 1px solid {BORDER_SOFT};
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    padding: 7px 14px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {BG_TAB};
    color: {TEXT};
    font-weight: 600;
    border-color: {BORDER};
}}
QTabBar::tab:hover:!selected {{
    color: {TEXT};
    background-color: {BG_INPUT};
}}
QScrollArea {{
    background-color: {BG_TAB};
    border: none;
}}
QScrollBar:vertical {{
    background: {BG_TAB};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QMessageBox {{
    background-color: {BG_RAISED};
    color: {TEXT};
}}
"""

SCANNER_QSS = f"""
QMainWindow, QWidget {{
    background-color: {SCANNER_BG};
    color: {TEXT};
    font-size: 12px;
}}
QLabel {{
    color: {TEXT};
    background: transparent;
}}
QCheckBox {{
    color: {TEXT};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {BORDER};
    border-radius: 3px;
    background: {SCANNER_INPUT};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QPushButton {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 12px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton:disabled {{
    background-color: {BORDER_SOFT};
    color: {TEXT_MUTED};
}}
QPushButton:checked {{
    background-color: #1d4ed8;
}}
QSpinBox {{
    background-color: {SCANNER_INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 3px 6px;
}}
QTableView {{
    background-color: {SCANNER_RAISED};
    alternate-background-color: {SCANNER_ALT_ROW};
    color: {TEXT};
    gridline-color: {BORDER_SOFT};
    border: 1px solid {BORDER_SOFT};
    border-radius: 4px;
    selection-background-color: {ACCENT};
    selection-color: white;
}}
QHeaderView::section {{
    background-color: {SCANNER_INPUT};
    color: {TEXT};
    border: none;
    border-right: 1px solid {BORDER_SOFT};
    border-bottom: 1px solid {BORDER};
    padding: 5px 6px;
    font-weight: 600;
}}
QTableView::item {{
    padding: 2px 4px;
}}
"""


def combo_stylesheet(*, active: bool) -> str:
    return _COMBO_ACTIVE if active else _COMBO_BASE


def apply_launcher_theme(widget) -> None:
    widget.setStyleSheet(LAUNCHER_QSS)


def apply_scanner_theme(widget) -> None:
    widget.setStyleSheet(SCANNER_QSS)
