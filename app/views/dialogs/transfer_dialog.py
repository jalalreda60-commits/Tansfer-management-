"""
Dialog used to create a new Transfer or edit an existing one, including
its nested Tools -> Part Numbers structure.
"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QPushButton, QLabel, QTreeWidget, QTreeWidgetItem, QMessageBox,
    QInputDialog, QDialogButtonBox,
)

from app.config import TransferType, Activity, TECHNOLOGIES, LOCATIONS
from app.utils.validators import require_non_empty, require_unique, validate_all


class TransferDialog(QDialog):
    def __init__(self, controller, transfer=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.transfer = transfer
        self.is_edit = transfer is not None
        self.setWindowTitle("Edit Transfer" if self.is_edit else "New Transfer")
        self.setMinimumWidth(560)

        # tools_data: list of dicts {tool_number, part_numbers: [..]}
        self.tools_data: list[dict] = []
        if self.is_edit:
            for tool in transfer.tools:
                self.tools_data.append({
                    "tool_number": tool.tool_number,
                    "part_numbers": [p.part_number for p in tool.part_numbers],
                })

        self._build_ui()
        if self.is_edit:
            self._load_transfer()

    def _build_ui(self):
        root = QVBoxLayout(self)

        form = QFormLayout()
        self.trf_number_edit = QLineEdit()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())

        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value for t in TransferType])

        self.activity_combo = QComboBox()
        self.activity_combo.addItems([a.value for a in Activity])

        self.sender_combo = QComboBox()
        self.sender_combo.setEditable(True)
        self.sender_combo.addItems(LOCATIONS)

        self.receiver_combo = QComboBox()
        self.receiver_combo.setEditable(True)
        self.receiver_combo.addItems(LOCATIONS)

        self.technology_combo = QComboBox()
        self.technology_combo.setEditable(True)
        self.technology_combo.addItems(TECHNOLOGIES)

        form.addRow("TRF Number*:", self.trf_number_edit)
        form.addRow("Planned Transfer Date*:", self.date_edit)
        form.addRow("Transfer Type*:", self.type_combo)
        form.addRow("Activity*:", self.activity_combo)
        form.addRow("Sender Location*:", self.sender_combo)
        form.addRow("Receiver Location*:", self.receiver_combo)
        form.addRow("Technology*:", self.technology_combo)
        root.addLayout(form)

        # --- Tools / Part Numbers editor ---
        root.addWidget(QLabel("Tools & Part Numbers:"))
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Tool / Part Number"])
        self.tree.setMinimumHeight(180)
        root.addWidget(self.tree)

        tools_btns = QHBoxLayout()
        add_tool_btn = QPushButton("+ Add Tool")
        add_tool_btn.setObjectName("SecondaryButton")
        add_tool_btn.clicked.connect(self._add_tool)
        add_pn_btn = QPushButton("+ Add Part Number")
        add_pn_btn.setObjectName("SecondaryButton")
        add_pn_btn.clicked.connect(self._add_part_number)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.setObjectName("DangerButton")
        remove_btn.clicked.connect(self._remove_selected)
        tools_btns.addWidget(add_tool_btn)
        tools_btns.addWidget(add_pn_btn)
        tools_btns.addWidget(remove_btn)
        tools_btns.addStretch()
        root.addLayout(tools_btns)

        self._refresh_tree()

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _load_transfer(self):
        t = self.transfer
        self.trf_number_edit.setText(t.trf_number)
        self.date_edit.setDate(QDate(t.planned_transfer_date.year, t.planned_transfer_date.month,
                                      t.planned_transfer_date.day))
        self.type_combo.setCurrentText(t.transfer_type)
        self.activity_combo.setCurrentText(t.activity)
        self.sender_combo.setCurrentText(t.sender_location)
        self.receiver_combo.setCurrentText(t.receiver_location)
        self.technology_combo.setCurrentText(t.technology)

    def _refresh_tree(self):
        self.tree.clear()
        for tool in self.tools_data:
            tool_item = QTreeWidgetItem([f"🔧 {tool['tool_number']}"])
            tool_item.setData(0, Qt.UserRole, ("tool", tool))
            for pn in tool["part_numbers"]:
                pn_item = QTreeWidgetItem([f"▫ {pn}"])
                pn_item.setData(0, Qt.UserRole, ("part", tool, pn))
                tool_item.addChild(pn_item)
            self.tree.addTopLevelItem(tool_item)
        self.tree.expandAll()

    def _add_tool(self):
        text, ok = QInputDialog.getText(self, "Add Tool", "Tool Number:")
        if ok and text.strip():
            self.tools_data.append({"tool_number": text.strip(), "part_numbers": []})
            self._refresh_tree()

    def _add_part_number(self):
        item = self.tree.currentItem()
        if not item:
            QMessageBox.information(self, "Select a Tool", "Select a tool first to add a part number to it.")
            return
        data = item.data(0, Qt.UserRole)
        tool = data[1] if data else None
        if tool is None:
            return
        text, ok = QInputDialog.getText(self, "Add Part Number", "Part Number:")
        if ok and text.strip():
            tool["part_numbers"].append(text.strip())
            self._refresh_tree()

    def _remove_selected(self):
        item = self.tree.currentItem()
        if not item:
            return
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        if data[0] == "tool":
            self.tools_data.remove(data[1])
        elif data[0] == "part":
            data[1]["part_numbers"].remove(data[2])
        self._refresh_tree()

    def _on_save(self):
        existing_numbers = [t.trf_number for t in self.controller.list_transfers()]
        current = self.transfer.trf_number if self.is_edit else None

        is_valid, message = validate_all(
            require_non_empty(self.trf_number_edit.text(), "TRF Number"),
            require_unique(self.trf_number_edit.text(), existing_numbers, "TRF Number", current=current),
            require_non_empty(self.sender_combo.currentText(), "Sender Location"),
            require_non_empty(self.receiver_combo.currentText(), "Receiver Location"),
            require_non_empty(self.technology_combo.currentText(), "Technology"),
        )
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", message)
            return

        if not self.tools_data:
            QMessageBox.warning(self, "Validation Error", "Add at least one Tool.")
            return

        qdate = self.date_edit.date()
        data = {
            "trf_number": self.trf_number_edit.text().strip(),
            "planned_transfer_date": dt.date(qdate.year(), qdate.month(), qdate.day()),
            "transfer_type": self.type_combo.currentText(),
            "activity": self.activity_combo.currentText(),
            "sender_location": self.sender_combo.currentText().strip(),
            "receiver_location": self.receiver_combo.currentText().strip(),
            "technology": self.technology_combo.currentText().strip(),
        }

        if self.is_edit:
            self.controller.update_transfer(self.transfer.id, data)
            # NOTE: structural tool/part-number edits for existing transfers
            # are managed from the Transfers table's row actions to keep
            # this dialog focused and avoid destructive bulk-diffing.
        else:
            self.controller.create_transfer(data, self.tools_data)

        self.accept()
