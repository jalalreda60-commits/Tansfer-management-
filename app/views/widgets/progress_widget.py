"""
QProgressBar pre-styled with the app's status colour based on percentage
and/or an explicit OverallStatus string.
"""
from __future__ import annotations

from PySide6.QtWidgets import QProgressBar

from app.config import STATUS_COLORS, OverallStatus


def colored_progress_bar(percent: float, status: str | None = None) -> QProgressBar:
    bar = QProgressBar()
    bar.setRange(0, 100)
    bar.setValue(int(round(percent)))
    bar.setTextVisible(True)
    bar.setFormat(f"{percent:.0f}%")

    if status is None:
        if percent >= 100:
            status = OverallStatus.COMPLETED.value
        elif percent <= 0:
            status = OverallStatus.NOT_STARTED.value
        else:
            status = OverallStatus.ONGOING.value

    color = STATUS_COLORS.get(status, "#3D8BFD")
    bar.setStyleSheet(f"""
        QProgressBar {{
            border: 1px solid #D9E1E8;
            border-radius: 6px;
            text-align: center;
            background-color: #F0F4F8;
            height: 16px;
        }}
        QProgressBar::chunk {{
            background-color: {color};
            border-radius: 6px;
        }}
    """)
    return bar
