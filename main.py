"""Finviz Scanner Desktop entry point."""

from __future__ import annotations

import logging
import sys

from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication

from finideas.settings import app_dir, migrate_env_key_if_needed
from finideas.ui.launcher import LauncherWindow


def main() -> int:
    root = app_dir()
    load_dotenv(root / ".env")
    migrate_env_key_if_needed()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    app = QApplication(sys.argv)
    app.setApplicationName("Finviz Scanner Desktop")
    app.setOrganizationName("Finviz Scanner Desktop")
    # Scanner windows alone should not keep the process alive after launcher closes
    app.setQuitOnLastWindowClosed(True)

    win = LauncherWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
