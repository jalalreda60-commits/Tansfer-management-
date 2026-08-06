"""
Small coloured "pill" label used to represent OverallStatus values
consistently (Green/Yellow/Red/Grey) across tables and cards.
"""
from __future__ import annotations

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

from app.config import STATUS_COLORS


class StatusBadge(QLabel):
    def __init__(self, status: str, parent=None):
        super().__init__(status, parent)
        self.set_status(status)
        self.setAlignment(Qt.AlignCenter)

    def set_status(self, status: str):
        color = STATUS_COLORS.get(status, "#95a5a6")
        self.setText(status)
        self.setStyleSheet(f"""
            background-color: {color};
            color: white;
            border-radius: 9px;
            padding: 3px 10px;
            font-weight: 600;
            font-size: 11px;
        """)
