"""
Reusable KPI card: big value + label + optional accent colour, used all
over the Dashboard.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class KPICard(QFrame):
    def __init__(self, title: str, value: str, accent: str = "#1F4E79",
                 subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(96)
        self.setFrameShape(QFrame.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"font-size: 26px; font-weight: 800; color: {accent}; border:none; background:transparent;"
        )

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #5A6B7B; border:none; background:transparent;"
        )
        self.title_label.setAlignment(Qt.AlignLeft)

        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("font-size: 11px; color: #8A99A8; border:none; background:transparent;")
            layout.addWidget(sub)

        # left accent bar via border
        self.setStyleSheet(self.styleSheet() + f"""
            #Card {{ border-left: 4px solid {accent}; }}
        """)

    def set_value(self, value: str):
        self.value_label.setText(value)
