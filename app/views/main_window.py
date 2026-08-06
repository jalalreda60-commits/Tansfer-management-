"""
Application shell: sidebar + top bar + stacked module views.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QLabel, QPushButton, QFrame,
)

from app.config import APP_NAME
from app.utils.theme import get_stylesheet
from app.controllers.notification_controller import NotificationController

from app.views.sidebar import Sidebar
from app.views.dashboard_view import DashboardView
from app.views.transfers_view import TransfersView
from app.views.preparation_view import PreparationView
from app.views.release_view import ReleaseView
from app.views.dialogs.notification_center_dialog import NotificationCenterDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1440, 900)
        self.dark_mode = False

        self.notification_controller = NotificationController()

        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.navigate.connect(self._on_navigate)
        outer.addWidget(self.sidebar)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        outer.addLayout(right)

        # --- Top bar ---
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(56)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)

        self.page_title = QLabel("Dashboard")
        self.page_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        top_layout.addWidget(self.page_title)
        top_layout.addStretch()

        self.notif_btn = QPushButton("🔔 Notifications")
        self.notif_btn.setObjectName("SecondaryButton")
        self.notif_btn.clicked.connect(self._open_notifications)
        top_layout.addWidget(self.notif_btn)

        self.theme_btn = QPushButton("🌙 Dark Mode")
        self.theme_btn.setObjectName("SecondaryButton")
        self.theme_btn.clicked.connect(self._toggle_theme)
        top_layout.addWidget(self.theme_btn)

        right.addWidget(top_bar)

        # --- Stacked module views ---
        self.stack = QStackedWidget()
        right.addWidget(self.stack)

        self.dashboard_view = DashboardView()
        self.transfers_view = TransfersView()
        self.preparation_view = PreparationView()
        self.release_view = ReleaseView()

        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.transfers_view)
        self.stack.addWidget(self.preparation_view)
        self.stack.addWidget(self.release_view)

        # Keep dependent views in sync when Transfers module changes data.
        self.transfers_view.data_changed.connect(self._on_data_changed)

        self.setStyleSheet(get_stylesheet(dark=False))

        # Background scan for overdue activities (auto notifications).
        self.notif_timer = QTimer(self)
        self.notif_timer.timeout.connect(self._scan_notifications)
        self.notif_timer.start(60_000)  # every minute
        self._scan_notifications()

        self.statusBar().showMessage("Ready — all changes are saved automatically.")

    # ------------------------------------------------------------------
    def _on_navigate(self, module: str):
        index_map = {"Dashboard": 0, "Transfers": 1, "Preparation": 2, "Release": 3}
        self.stack.setCurrentIndex(index_map[module])
        self.page_title.setText(module)
        if module == "Dashboard":
            self.dashboard_view.refresh()
        elif module == "Preparation":
            self.preparation_view.reload_transfers()
        elif module == "Release":
            self.release_view.reload_transfers()

    def _on_data_changed(self):
        """Transfers CRUD happened -> keep every other module's dropdowns fresh."""
        self.preparation_view.reload_transfers()
        self.release_view.reload_transfers()
        self.dashboard_view.refresh()

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.setStyleSheet(get_stylesheet(dark=self.dark_mode))
        self.theme_btn.setText("☀️ Light Mode" if self.dark_mode else "🌙 Dark Mode")

    def _open_notifications(self):
        dialog = NotificationCenterDialog(self.notification_controller, parent=self)
        dialog.exec()
        self._update_notif_badge()

    def _scan_notifications(self):
        created = self.notification_controller.scan_and_generate()
        self._update_notif_badge()
        if created:
            self.statusBar().showMessage(f"{created} new notification(s) generated.", 5000)

    def _update_notif_badge(self):
        unread = len(self.notification_controller.list_unread())
        self.notif_btn.setText(f"🔔 Notifications ({unread})" if unread else "🔔 Notifications")
