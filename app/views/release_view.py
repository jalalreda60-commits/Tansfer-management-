"""
Release module (sidebar item 4): tracks the final release checklist for
each transfer and computes Release Progress used on the Dashboard.
"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QDateEdit, QLineEdit,
    QMessageBox, QInputDialog, QTextEdit, QFrame,
)

from app.controllers.transfer_controller import TransferController
from app.controllers.release_controller import ReleaseController
from app.views.widgets.progress_widget import colored_progress_bar
from app.config import SimpleStatus


class ReleaseView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tc = TransferController()
        self.rc = ReleaseController()
        self.current_transfer = None

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 20)
        root.setSpacing(12)

        title = QLabel("Release")
        title.setStyleSheet("font-size: 22px; font-weight: 800;")
        root.addWidget(title)

        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Transfer:"))
        self.transfer_combo = QComboBox()
        self.transfer_combo.setMinimumWidth(280)
        self.transfer_combo.currentIndexChanged.connect(self._on_transfer_selected)
        selector_row.addWidget(self.transfer_combo)
        selector_row.addStretch()
        root.addLayout(selector_row)

        self.status_label = QLabel()
        root.addWidget(self.status_label)

        self.progress_container = QVBoxLayout()
        root.addLayout(self.progress_container)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Release Item", "Status", "Responsible", "Due Date", "Completion Date", "Comments"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

        btn_row = QHBoxLayout()
        add_item_btn = QPushButton("+ Add Custom Item")
        add_item_btn.setObjectName("SecondaryButton")
        add_item_btn.clicked.connect(self._add_item)
        remove_item_btn = QPushButton("Remove Selected Item")
        remove_item_btn.setObjectName("DangerButton")
        remove_item_btn.clicked.connect(self._remove_item)
        btn_row.addWidget(add_item_btn)
        btn_row.addWidget(remove_item_btn)
        btn_row.addStretch()
        self.finalize_btn = QPushButton("✅ Finalize Release")
        self.finalize_btn.clicked.connect(self._finalize_release)
        btn_row.addWidget(self.finalize_btn)
        root.addLayout(btn_row)

        self.reload_transfers()

    def reload_transfers(self):
        self.transfer_combo.blockSignals(True)
        self.transfer_combo.clear()
        for t in self.tc.list_transfers():
            self.transfer_combo.addItem(t.trf_number, t.id)
        self.transfer_combo.blockSignals(False)
        if self.transfer_combo.count():
            self.transfer_combo.setCurrentIndex(0)
            self._on_transfer_selected(0)
        else:
            self.current_transfer = None
            self._refresh()

    def _on_transfer_selected(self, index):
        transfer_id = self.transfer_combo.currentData()
        self.current_transfer = self.tc.get_transfer(transfer_id) if transfer_id else None
        self._refresh()

    def _refresh(self):
        self._clear_layout(self.progress_container)
        if not self.current_transfer:
            self.status_label.setText("No transfers available yet — create one in the Transfers module.")
            self.table.setRowCount(0)
            self.finalize_btn.setEnabled(False)
            return

        checklist = self.rc.get_checklist(self.current_transfer)
        released = checklist.released == "Yes"
        status_txt = "RELEASED ✅" if released else self.rc.release_status(self.current_transfer)
        self.status_label.setText(
            f"Transfer <b>{self.current_transfer.trf_number}</b> — Status: <b>{status_txt}</b>"
            + (f" on {checklist.release_date} by {checklist.released_by}" if released else ""))

        self.progress_container.addWidget(
            colored_progress_bar(checklist.progress_percent,
                                  "Completed" if released else None))

        self.finalize_btn.setEnabled(not released and checklist.progress_percent >= 100)

        self.table.blockSignals(True)
        self.table.setRowCount(len(checklist.items))
        for row, item in enumerate(checklist.items):
            name_item = QTableWidgetItem(item.name)
            name_item.setData(Qt.UserRole, item.id)
            self.table.setItem(row, 0, name_item)

            status_combo = QComboBox()
            status_combo.addItems([s.value for s in SimpleStatus])
            status_combo.setCurrentText(item.status)
            status_combo.currentTextChanged.connect(lambda val, it=item: self._update_item(it, status=val))
            self.table.setCellWidget(row, 1, status_combo)

            resp_edit = QLineEdit(item.responsible or "")
            resp_edit.editingFinished.connect(
                lambda it=item, w=resp_edit: self._update_item(it, responsible=w.text()))
            self.table.setCellWidget(row, 2, resp_edit)

            due_edit = QDateEdit()
            due_edit.setCalendarPopup(True)
            due_edit.setDisplayFormat("yyyy-MM-dd")
            due_edit.setDate(item.due_date or dt.date.today())
            due_edit.dateChanged.connect(lambda val, it=item: self._update_item(it, due_date=val.toPython()))
            self.table.setCellWidget(row, 3, due_edit)

            completion_label = QLabel(str(item.completion_date) if item.completion_date else "-")
            completion_label.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 4, completion_label)

            comment_edit = QLineEdit(item.comments or "")
            comment_edit.editingFinished.connect(
                lambda it=item, w=comment_edit: self._update_item(it, comments=w.text()))
            self.table.setCellWidget(row, 5, comment_edit)
        self.table.blockSignals(False)

    def _update_item(self, item, **fields):
        self.rc.update_item(item, **fields)
        self._refresh()

    def _add_item(self):
        if not self.current_transfer:
            return
        name, ok = QInputDialog.getText(self, "Add Release Item", "Item name:")
        if ok and name.strip():
            checklist = self.rc.get_checklist(self.current_transfer)
            self.rc.add_custom_item(checklist, name.strip())
            self._refresh()

    def _remove_item(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        self.rc.remove_item(item_id)
        self._refresh()

    def _finalize_release(self):
        name, ok = QInputDialog.getText(self, "Finalize Release", "Released by:")
        if ok and name.strip():
            checklist = self.rc.get_checklist(self.current_transfer)
            self.rc.finalize_release(checklist, name.strip())
            QMessageBox.information(self, "Released",
                                     f"Transfer {self.current_transfer.trf_number} marked as released.")
            self._refresh()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
