"""
Transfers module (spec section 2): list, search, filter, sort, CRUD,
duplicate, export to Excel, attachments/comments/history, printing.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QLabel, QMessageBox, QHeaderView,
    QAbstractItemView, QMenu,
)

from app.controllers.transfer_controller import TransferController
from app.controllers.preparation_controller import PreparationController
from app.controllers.release_controller import ReleaseController
from app.models.transfer import Transfer
from app.views.dialogs.transfer_dialog import TransferDialog
from app.views.dialogs.entity_detail_dialog import EntityDetailDialog
from app.views.widgets.status_badge import StatusBadge
from app.utils.excel_export import export_rows_to_excel
from app.config import TransferType, Activity


class TransfersView(QWidget):
    data_changed = Signal()

    COLUMNS = ["TRF Number", "Planned Date", "Days Left", "Type", "Activity",
               "Sender", "Receiver", "Technology", "Prep %", "Release %", "Status"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = TransferController()
        self.prep_controller = PreparationController()
        self.release_controller = ReleaseController()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Transfers")
        title.setStyleSheet("font-size: 22px; font-weight: 800;")
        layout.addWidget(title)

        # --- toolbar: search + filters + actions ---
        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search TRF number, technology, location...")
        self.search_edit.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search_edit, 2)

        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types")
        self.type_filter.addItems([t.value for t in TransferType])
        self.type_filter.currentTextChanged.connect(self.refresh)
        toolbar.addWidget(self.type_filter)

        self.activity_filter = QComboBox()
        self.activity_filter.addItem("All Activities")
        self.activity_filter.addItems([a.value for a in Activity])
        self.activity_filter.currentTextChanged.connect(self.refresh)
        toolbar.addWidget(self.activity_filter)

        toolbar.addStretch()

        add_btn = QPushButton("+ New Transfer")
        add_btn.clicked.connect(self._add_transfer)
        toolbar.addWidget(add_btn)

        export_btn = QPushButton("Export to Excel")
        export_btn.setObjectName("SecondaryButton")
        export_btn.clicked.connect(self._export_excel)
        toolbar.addWidget(export_btn)

        print_btn = QPushButton("Print")
        print_btn.setObjectName("SecondaryButton")
        print_btn.clicked.connect(self._print_table)
        toolbar.addWidget(print_btn)

        layout.addLayout(toolbar)

        # --- table ---
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._edit_selected)
        layout.addWidget(self.table)

        self.refresh()

    # ------------------------------------------------------------------
    def refresh(self):
        filters = {
            "transfer_type": None if self.type_filter.currentText() == "All Types"
            else self.type_filter.currentText(),
            "activity": None if self.activity_filter.currentText() == "All Activities"
            else self.activity_filter.currentText(),
        }
        transfers = self.controller.list_transfers(self.search_edit.text().strip(), filters)

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(transfers))
        for row, t in enumerate(transfers):
            prep_pct = self.prep_controller.preparation_progress(t)
            rel_pct = self.release_controller.release_progress(t)
            status = self.release_controller.release_status(t)
            if status not in ("Completed",):
                status = self.prep_controller.preparation_status(t)

            values = [
                t.trf_number, str(t.planned_transfer_date), str(t.days_remaining),
                t.transfer_type, t.activity, t.sender_location, t.receiver_location,
                t.technology, f"{prep_pct}%", f"{rel_pct}%",
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, t.id)
                if col == 2 and t.days_remaining < 0:
                    item.setForeground(Qt.red)
                self.table.setItem(row, col, item)

            badge_container = StatusBadge(status)
            self.table.setCellWidget(row, len(self.COLUMNS) - 1, badge_container)

        self.table.setSortingEnabled(True)

    def _selected_transfer(self) -> Transfer | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        transfer_id = item.data(Qt.UserRole)
        return self.controller.get_transfer(transfer_id)

    # ------------------------------------------------------------------
    def _add_transfer(self):
        dialog = TransferDialog(self.controller, parent=self)
        if dialog.exec():
            self.refresh()
            self.data_changed.emit()

    def _edit_selected(self):
        transfer = self._selected_transfer()
        if not transfer:
            return
        dialog = TransferDialog(self.controller, transfer=transfer, parent=self)
        if dialog.exec():
            self.refresh()
            self.data_changed.emit()

    def _delete_selected(self):
        transfer = self._selected_transfer()
        if not transfer:
            return
        if QMessageBox.question(
            self, "Delete Transfer",
            f"Delete transfer {transfer.trf_number}? This removes all related "
            f"preparation and release data and cannot be undone."
        ) == QMessageBox.Yes:
            self.controller.delete_transfer(transfer.id)
            self.refresh()
            self.data_changed.emit()

    def _duplicate_selected(self):
        transfer = self._selected_transfer()
        if not transfer:
            return
        new_transfer = self.controller.duplicate_transfer(transfer.id)
        QMessageBox.information(self, "Duplicated", f"Created {new_transfer.trf_number}.")
        self.refresh()
        self.data_changed.emit()

    def _show_details(self):
        transfer = self._selected_transfer()
        if not transfer:
            return
        dialog = EntityDetailDialog(self.controller, "transfer", transfer.id, transfer.trf_number, parent=self)
        dialog.exec()
        self.refresh()

    def _show_context_menu(self, pos):
        if self.table.itemAt(pos) is None:
            return
        menu = QMenu(self)
        menu.addAction("Edit", self._edit_selected)
        menu.addAction("Duplicate", self._duplicate_selected)
        menu.addAction("Attachments / Comments / History", self._show_details)
        menu.addSeparator()
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._delete_selected)
        menu.addAction(delete_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    # ------------------------------------------------------------------
    def _export_excel(self):
        headers = self.COLUMNS
        rows = []
        for row in range(self.table.rowCount()):
            values = [self.table.item(row, c).text() if self.table.item(row, c) else ""
                      for c in range(len(self.COLUMNS) - 1)]
            widget = self.table.cellWidget(row, len(self.COLUMNS) - 1)
            values.append(widget.text() if widget else "")
            rows.append(values)
        path = export_rows_to_excel(headers, rows, "Transfers")
        QMessageBox.information(self, "Export Complete", f"Exported to:\n{path}")

    def _print_table(self):
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.Accepted:
            return
        from PySide6.QtGui import QPainter
        painter = QPainter(printer)
        self.table.render(painter)
        painter.end()
