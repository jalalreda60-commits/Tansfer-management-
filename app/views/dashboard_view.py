"""
Dashboard: complete overview of all transfers — KPI cards, charts, and
recent-activity / due-date / delayed-task tables, per spec section 1.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QScrollArea,
    QTableWidget, QTableWidgetItem, QFrame, QSizePolicy,
)

from app.controllers.dashboard_controller import DashboardController
from app.views.widgets.kpi_card import KPICard
from app.views.widgets.charts import (
    make_pie_chart, make_bar_chart, make_horizontal_progress_bar_chart, make_line_chart,
)


class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = DashboardController()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        self.layout_ = QVBoxLayout(content)
        self.layout_.setContentsMargins(20, 16, 20, 20)
        self.layout_.setSpacing(18)

        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 22px; font-weight: 800;")
        self.layout_.addWidget(title)

        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(14)
        self.layout_.addLayout(self.kpi_grid)

        self.charts_grid = QGridLayout()
        self.charts_grid.setSpacing(14)
        self.layout_.addLayout(self.charts_grid)

        tables_label = QLabel("Activity Overview")
        tables_label.setStyleSheet("font-size: 16px; font-weight: 700; margin-top: 8px;")
        self.layout_.addWidget(tables_label)

        self.tables_row = QHBoxLayout()
        self.tables_row.setSpacing(14)
        self.layout_.addLayout(self.tables_row)

        self.refresh()

    # ------------------------------------------------------------------
    def refresh(self):
        self._clear_layout(self.kpi_grid)
        self._clear_layout(self.charts_grid)
        self._clear_layout(self.tables_row)

        kpis = self.controller.kpis()
        cards = [
            KPICard("Total Transfers", str(kpis["total_transfers"]), "#1F4E79"),
            KPICard("Preparation Progress", f"{kpis['preparation_progress']}%", "#3D8BFD"),
            KPICard("Release Progress", f"{kpis['release_progress']}%", "#2ecc71"),
            KPICard("Delayed Activities", str(kpis["delayed_activities"]), "#e74c3c"),
            KPICard("Upcoming Transfers (14d)", str(kpis["upcoming_transfers"]), "#f1c40f"),
            KPICard("Open Actions", str(kpis["open_actions"]), "#9b59b6"),
            KPICard("Completed Transfers", str(kpis["completed_transfers"]), "#1abc9c"),
        ]
        for i, card in enumerate(cards):
            self.kpi_grid.addWidget(card, i // 4, i % 4)

        # --- Charts ---
        progress_by_transfer = self.controller.progress_by_transfer()
        phase = self.controller.progress_by_phase()
        weekly = self.controller.weekly_progress()
        by_tech = self.controller.by_technology()
        type_dist = self.controller.by_transfer_type()

        self.charts_grid.addWidget(
            make_horizontal_progress_bar_chart(progress_by_transfer, "Progress by Transfer"), 0, 0, 1, 2)
        self.charts_grid.addWidget(make_bar_chart(phase, "Progress by Phase", "%"), 0, 2)
        self.charts_grid.addWidget(make_line_chart(weekly, "Weekly Activity", "Actions"), 1, 0)
        self.charts_grid.addWidget(make_pie_chart(by_tech, "Transfers by Technology"), 1, 1)
        self.charts_grid.addWidget(make_pie_chart(type_dist, "Transfer Type Distribution"), 1, 2)

        # --- Tables ---
        self.tables_row.addWidget(self._recent_activities_table())
        self.tables_row.addWidget(self._upcoming_due_dates_table())
        self.tables_row.addWidget(self._delayed_tasks_table())

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

    def _table_container(self, title: str, table: QTableWidget) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Card")
        v = QVBoxLayout(frame)
        label = QLabel(title)
        label.setStyleSheet("font-weight: 700; font-size: 13px;")
        v.addWidget(label)
        v.addWidget(table)
        return frame

    def _recent_activities_table(self) -> QFrame:
        rows = self.controller.recent_activities()
        table = QTableWidget(len(rows), 3)
        table.setHorizontalHeaderLabels(["Time", "Action", "Details"])
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        for r, h in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(h.timestamp.strftime("%Y-%m-%d %H:%M")))
            table.setItem(r, 1, QTableWidgetItem(h.action))
            table.setItem(r, 2, QTableWidgetItem(h.details or ""))
        return self._table_container("Recent Activities", table)

    def _upcoming_due_dates_table(self) -> QFrame:
        transfers = self.controller.upcoming_due_dates()
        table = QTableWidget(len(transfers), 3)
        table.setHorizontalHeaderLabels(["TRF Number", "Planned Date", "Days Left"])
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        for r, t in enumerate(transfers):
            table.setItem(r, 0, QTableWidgetItem(t.trf_number))
            table.setItem(r, 1, QTableWidgetItem(str(t.planned_transfer_date)))
            table.setItem(r, 2, QTableWidgetItem(str(t.days_remaining)))
        return self._table_container("Upcoming Due Dates", table)

    def _delayed_tasks_table(self) -> QFrame:
        rows = self.controller.delayed_tasks()
        table = QTableWidget(len(rows), 3)
        table.setHorizontalHeaderLabels(["TRF Number", "Phase", "Status"])
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        for r, (trf, phase, status) in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(trf))
            table.setItem(r, 1, QTableWidgetItem(phase))
            table.setItem(r, 2, QTableWidgetItem(status))
        return self._table_container("Delayed Tasks", table)
