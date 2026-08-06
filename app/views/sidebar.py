"""
Collapsible left sidebar listing the four main modules.
Emits `navigate(str)` when the user picks a module.
"""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QButtonGroup

from app.config import SIDEBAR_MODULES

ICONS = {
    "Dashboard": "📊",
    "Transfers": "🔄",
    "Preparation": "🛠",
    "Release": "🚀",
}


class Sidebar(QWidget):
    navigate = Signal(str)

    EXPANDED_WIDTH = 220
    COLLAPSED_WIDTH = 64

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self._expanded = True
        self.setFixedWidth(self.EXPANDED_WIDTH)

        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(0)

        self.title_label = QLabel("Transfer Mgmt")
        self.title_label.setObjectName("SidebarTitle")
        self.layout_.addWidget(self.title_label)

        self.toggle_btn = QPushButton("⮜  Collapse")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle)
        self.layout_.addWidget(self.toggle_btn)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.buttons: dict[str, QPushButton] = {}

        for module in SIDEBAR_MODULES:
            btn = QPushButton(f"{ICONS.get(module, '')}   {module}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, m=module: self.navigate.emit(m))
            self.button_group.addButton(btn)
            self.buttons[module] = btn
            self.layout_.addWidget(btn)

        self.layout_.addStretch()
        self.buttons[SIDEBAR_MODULES[0]].setChecked(True)

    def toggle(self):
        self._expanded = not self._expanded
        self.setFixedWidth(self.EXPANDED_WIDTH if self._expanded else self.COLLAPSED_WIDTH)
        self.title_label.setVisible(self._expanded)
        self.toggle_btn.setText("⮜  Collapse" if self._expanded else "⮞")
        for module, btn in self.buttons.items():
            btn.setText(f"{ICONS.get(module, '')}   {module}" if self._expanded else ICONS.get(module, ""))

    def set_active(self, module: str):
        if module in self.buttons:
            self.buttons[module].setChecked(True)
