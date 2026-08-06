#!/usr/bin/env python3
"""
Transfer Management System
---------------------------
Entry point. Initialises the SQLite database (creating tables on first
run) and launches the PySide6 application.

Run with:  python main.py
"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from app.config import APP_NAME, APP_ORG
from app.database import init_db
from app.views.main_window import MainWindow


def main() -> int:
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
