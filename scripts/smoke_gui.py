"""Headless-ish smoke: open launcher + scanner, wait for rows, quit."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

load_dotenv(ROOT / ".env")

from finideas.ui.launcher import LauncherWindow


def main() -> int:
    app = QApplication(sys.argv)
    launcher = LauncherWindow()
    launcher.show()
    launcher.open_52w_high()
    win = launcher._windows[0]

    result = {"rows": 0, "status": ""}

    def check() -> None:
        rows = win.model.rowCount()
        status = win.status.text()
        print(f"STATUS={status!r} ROWS={rows}")
        if rows > 0 or status.startswith("Error"):
            result["rows"] = rows
            result["status"] = status
            app.quit()

    # Poll until data or error (max ~20s)
    timer = QTimer()
    timer.timeout.connect(check)
    timer.start(500)
    QTimer.singleShot(20000, app.quit)
    code = app.exec()
    print(f"EXIT={code} FINAL_ROWS={result['rows']} FINAL_STATUS={result['status']!r}")
    return 0 if result["rows"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
