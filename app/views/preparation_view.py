"""
Preparation module (spec sections 3.1 -> 3.7).

Layout: Transfer selector on top, a Tools/Part-Numbers tree on the left,
and a tabbed panel on the right. Transfer-level tabs (PTT Approval, E2E
Follow-up) are always active once a transfer is chosen; Tool-level tabs
(Safety Stock, Training) activate on tool selection; Part-Number-level
tabs (Raw Material, Pre-check, Applicator/Counter Part) activate on part
selection.
"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QTreeWidget,
    QTreeWidgetItem, QTabWidget, QSplitter, QGroupBox, QPushButton,
    QTableWidget, QTableWidgetItem, QInputDialog, QMessageBox, QDateEdit,
    QHeaderView, QCheckBox, QScrollArea, QFrame,
)

from app.controllers.transfer_controller import TransferController
from app.controllers.preparation_controller import PreparationController
from app.views.widgets.dynamic_form import DynamicForm
from app.views.widgets.progress_widget import colored_progress_bar
from app.views.widgets.status_badge import StatusBadge
from app.config import (
    SimpleStatus, OEMStatus, NAOngoingDone, NAOngoingReceived, PrecheckFeedback,
    MeetingStatus, YesNo, PCNStatus, TrainingStatus, Urgency, Activity,
)


class PreparationView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tc = TransferController()
        self.pc = PreparationController()
        self.current_transfer = None
        self.current_tool = None
        self.current_part = None

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 20)
        root.setSpacing(12)

        title = QLabel("Preparation")
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

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)

        # --- Left: tree ---
        tree_container = QFrame()
        tree_container.setObjectName("Card")
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.addWidget(QLabel("<b>Tools & Part Numbers</b>"))
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemSelectionChanged.connect(self._on_tree_selection)
        tree_layout.addWidget(self.tree)
        splitter.addWidget(tree_container)

        # --- Right: tabs ---
        self.tabs = QTabWidget()
        splitter.addWidget(self.tabs)
        splitter.setSizes([260, 760])

        self._build_ptt_tab()
        self._build_safety_stock_tab()
        self._build_raw_material_tab()
        self._build_pre_check_tab()
        self._build_e2e_tab()
        self._build_applicator_tab()
        self._build_training_tab()

        self.reload_transfers()

    # ==================================================================
    # Transfer / tree navigation
    # ==================================================================
    def reload_transfers(self):
        self.transfer_combo.blockSignals(True)
        self.transfer_combo.clear()
        for t in self.tc.list_transfers():
            self.transfer_combo.addItem(f"{t.trf_number}  ({t.activity})", t.id)
        self.transfer_combo.blockSignals(False)
        if self.transfer_combo.count():
            self.transfer_combo.setCurrentIndex(0)
            self._on_transfer_selected(0)
        else:
            self.current_transfer = None
            self._refresh_all_tabs()

    def _on_transfer_selected(self, index):
        transfer_id = self.transfer_combo.currentData()
        self.current_transfer = self.tc.get_transfer(transfer_id) if transfer_id else None
        self.current_tool = None
        self.current_part = None
        self._reload_tree()
        self._refresh_all_tabs()

    def _reload_tree(self):
        self.tree.clear()
        if not self.current_transfer:
            return
        for tool in self.current_transfer.tools:
            tool_item = QTreeWidgetItem([f"🔧 {tool.tool_number}"])
            tool_item.setData(0, Qt.UserRole, ("tool", tool.id))
            for pn in tool.part_numbers:
                pn_item = QTreeWidgetItem([f"▫ {pn.part_number}"])
                pn_item.setData(0, Qt.UserRole, ("part", pn.id))
                tool_item.addChild(pn_item)
            self.tree.addTopLevelItem(tool_item)
        self.tree.expandAll()
        if self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(0))

    def _on_tree_selection(self):
        items = self.tree.selectedItems()
        if not items:
            self.current_tool, self.current_part = None, None
        else:
            kind, obj_id = items[0].data(0, Qt.UserRole)
            if kind == "tool":
                self.current_tool = self.tc.session.get(type(self.current_transfer.tools[0]), obj_id)
                self.current_part = None
            else:
                from app.models.transfer import PartNumber, Tool
                part = self.tc.session.get(PartNumber, obj_id)
                self.current_part = part
                self.current_tool = part.tool if part else None
        self._refresh_tool_part_tabs()

    def _refresh_all_tabs(self):
        self._refresh_ptt_tab()
        self._refresh_e2e_tab()
        self._refresh_tool_part_tabs()

    def _refresh_tool_part_tabs(self):
        self._refresh_safety_stock_tab()
        self._refresh_training_tab()
        self._refresh_raw_material_tab()
        self._refresh_pre_check_tab()
        self._refresh_applicator_tab()

    # ==================================================================
    # 3.1 PTT Approval
    # ==================================================================
    def _build_ptt_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)

        self.ptt_status_label = QLabel()
        v.addWidget(self.ptt_status_label)

        v.addWidget(QLabel("<b>Step 1 — Internal Approval</b>"))
        internal_fields = [
            {"attr": "internal_status", "label": "Status", "type": "combo",
             "options": [s.value for s in SimpleStatus]},
            {"attr": "internal_responsible", "label": "Responsible", "type": "text"},
            {"attr": "internal_due_date", "label": "Due Date", "type": "date"},
            {"attr": "internal_approval_date", "label": "Approval Date", "type": "date"},
            {"attr": "internal_comments", "label": "Comments", "type": "textarea"},
        ]
        self.ptt_internal_form = DynamicForm(internal_fields)
        self.ptt_internal_form.saved.connect(self._refresh_ptt_tab)
        v.addWidget(self.ptt_internal_form)

        v.addWidget(QLabel("<b>Step 2 — OEM Approval</b> (one or multiple OEMs)"))
        self.oem_table = QTableWidget(0, 5)
        self.oem_table.setHorizontalHeaderLabels(["OEM Name", "Status", "Due Date", "Approval Date", "Comments"])
        self.oem_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        v.addWidget(self.oem_table)

        oem_btns = QHBoxLayout()
        add_oem_btn = QPushButton("+ Add OEM")
        add_oem_btn.clicked.connect(self._add_oem)
        remove_oem_btn = QPushButton("Remove Selected OEM")
        remove_oem_btn.setObjectName("DangerButton")
        remove_oem_btn.clicked.connect(self._remove_oem)
        oem_btns.addWidget(add_oem_btn)
        oem_btns.addWidget(remove_oem_btn)
        oem_btns.addStretch()
        v.addLayout(oem_btns)

        self.tabs.addTab(w, "3.1 PTT Approval")

    def _refresh_ptt_tab(self):
        if not self.current_transfer:
            self.ptt_status_label.setText("Select a transfer.")
            self.ptt_internal_form.clear()
            self.oem_table.setRowCount(0)
            return
        ptt = self.pc.get_ptt(self.current_transfer)
        self.ptt_status_label.setText(
            f"Overall PTT Status: <b>{ptt.overall_status}</b>  —  Progress: {ptt.progress_percent}%")
        self.ptt_internal_form.bind(ptt, self.pc.save)

        self.oem_table.setRowCount(len(ptt.oem_approvals))
        for row, oem in enumerate(ptt.oem_approvals):
            self.oem_table.setItem(row, 0, QTableWidgetItem(oem.oem_name))
            self.oem_table.item(row, 0).setData(Qt.UserRole, oem.id)

            status_combo = QComboBox()
            status_combo.addItems([s.value for s in OEMStatus])
            status_combo.setCurrentText(oem.status)
            status_combo.currentTextChanged.connect(
                lambda val, o=oem: self._update_oem(o, status=val))
            self.oem_table.setCellWidget(row, 1, status_combo)

            due_edit = QDateEdit()
            due_edit.setCalendarPopup(True)
            due_edit.setDisplayFormat("yyyy-MM-dd")
            due_edit.setDate(oem.due_date or dt.date.today())
            due_edit.dateChanged.connect(lambda val, o=oem: self._update_oem(o, due_date=val.toPython()))
            self.oem_table.setCellWidget(row, 2, due_edit)

            appr_edit = QDateEdit()
            appr_edit.setCalendarPopup(True)
            appr_edit.setDisplayFormat("yyyy-MM-dd")
            appr_edit.setDate(oem.approval_date or dt.date.today())
            appr_edit.dateChanged.connect(lambda val, o=oem: self._update_oem(o, approval_date=val.toPython()))
            self.oem_table.setCellWidget(row, 3, appr_edit)

            comment_item = QTableWidgetItem(oem.comments or "")
            self.oem_table.setItem(row, 4, comment_item)
        self.oem_table.itemChanged.connect(self._on_oem_comment_changed)

    def _on_oem_comment_changed(self, item):
        if item.column() != 4:
            return
        oem_id = self.oem_table.item(item.row(), 0).data(Qt.UserRole)
        from app.models.ptt_approval import OEMApproval
        oem = self.tc.session.get(OEMApproval, oem_id)
        if oem:
            self._update_oem(oem, comments=item.text())

    def _update_oem(self, oem, **fields):
        for k, v in fields.items():
            setattr(oem, k, v)
        self.pc.save(oem)
        self.ptt_status_label.setText(
            f"Overall PTT Status: <b>{self.current_transfer.ptt_approval.overall_status}</b>  —  "
            f"Progress: {self.current_transfer.ptt_approval.progress_percent}%")

    def _add_oem(self):
        if not self.current_transfer:
            return
        name, ok = QInputDialog.getText(self, "Add OEM", "OEM Name:")
        if ok and name.strip():
            ptt = self.pc.get_ptt(self.current_transfer)
            self.pc.add_oem(ptt, name.strip())
            self._refresh_ptt_tab()

    def _remove_oem(self):
        row = self.oem_table.currentRow()
        if row < 0:
            return
        oem_id = self.oem_table.item(row, 0).data(Qt.UserRole)
        self.pc.remove_oem(oem_id)
        self._refresh_ptt_tab()

    # ==================================================================
    # 3.2 Safety Stock (per Tool)
    # ==================================================================
    def _build_safety_stock_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.ss_label = QLabel()
        v.addWidget(self.ss_label)

        self.ss_required_checkbox = QCheckBox("Safety Stock Required")
        self.ss_required_checkbox.stateChanged.connect(self._on_ss_required_changed)
        v.addWidget(self.ss_required_checkbox)

        fields = [
            {"attr": "start_calendar_week", "label": "Start Calendar Week (YYYY-Wnn)", "type": "text"},
            {"attr": "number_of_weeks", "label": "Number of Weeks", "type": "int"},
            {"attr": "required_quantity", "label": "Required Quantity", "type": "int"},
            {"attr": "current_built_quantity", "label": "Current Built Quantity", "type": "int"},
        ]
        self.ss_form = DynamicForm(fields)
        self.ss_form.saved.connect(self._refresh_safety_stock_tab)
        v.addWidget(self.ss_form)

        self.ss_finish_cw_label = QLabel()
        v.addWidget(self.ss_finish_cw_label)

        self.ss_progress_container = QVBoxLayout()
        v.addLayout(self.ss_progress_container)
        v.addStretch()

        self.tabs.addTab(w, "3.2 Safety Stock")

    def _refresh_safety_stock_tab(self):
        if not self.current_tool:
            self.ss_label.setText("Select a Tool in the tree to manage its Safety Stock.")
            self.ss_form.clear()
            self.ss_required_checkbox.setEnabled(False)
            self._clear_layout(self.ss_progress_container)
            return
        self.ss_required_checkbox.setEnabled(True)
        ss = self.pc.get_safety_stock(self.current_tool)
        self.ss_label.setText(f"Tool: <b>{self.current_tool.tool_number}</b>")

        self.ss_required_checkbox.blockSignals(True)
        self.ss_required_checkbox.setChecked(ss.required)
        self.ss_required_checkbox.blockSignals(False)

        self.ss_form.bind(ss, self._save_safety_stock)
        self.ss_form.setEnabled(ss.required)

        finish_cw = self.pc.compute_finish_cw(ss)
        self.ss_finish_cw_label.setText(f"Finish Calendar Week: <b>{finish_cw or '-'}</b>")

        self._clear_layout(self.ss_progress_container)
        self.ss_progress_container.addWidget(colored_progress_bar(ss.progress_percent, ss.status))

    def _save_safety_stock(self, ss):
        ss.finish_calendar_week = self.pc.compute_finish_cw(ss)
        self.pc.save(ss)

    def _on_ss_required_changed(self, state):
        if not self.current_tool:
            return
        ss = self.pc.get_safety_stock(self.current_tool)
        ss.required = bool(state)
        self.pc.save(ss)
        self._refresh_safety_stock_tab()

    # ==================================================================
    # 3.3 Raw Material Follow-up (per Part Number)
    # ==================================================================
    def _build_raw_material_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.rm_label = QLabel()
        v.addWidget(self.rm_label)

        fields = [
            {"attr": "subgroup", "label": "Subgroup", "type": "combo",
             "options": [s.value for s in NAOngoingDone]},
            {"attr": "setup", "label": "Setup", "type": "combo",
             "options": [s.value for s in NAOngoingDone]},
            {"attr": "rm_order", "label": "RM Order", "type": "combo",
             "options": [s.value for s in NAOngoingDone]},
            {"attr": "rm_availability", "label": "RM Availability", "type": "combo",
             "options": [s.value for s in NAOngoingDone]},
            {"attr": "due_date", "label": "Due Date", "type": "date"},
            {"attr": "comment", "label": "Comment", "type": "textarea"},
        ]
        self.rm_form = DynamicForm(fields)
        self.rm_form.saved.connect(self._refresh_raw_material_tab)
        v.addWidget(self.rm_form)
        v.addStretch()
        self.tabs.addTab(w, "3.3 Raw Material")

    def _refresh_raw_material_tab(self):
        if not self.current_part:
            self.rm_label.setText("Select a Part Number in the tree to manage Raw Material follow-up.")
            self.rm_form.clear()
            return
        rm = self.pc.get_raw_material(self.current_part)
        self.rm_label.setText(
            f"Part Number: <b>{self.current_part.part_number}</b> — "
            f"Overall Status: <b>{rm.overall_status}</b> ({rm.progress_percent}%)")
        self.rm_form.bind(rm, self.pc.save)

    # ==================================================================
    # 3.4 Pre-check (per Part Number)
    # ==================================================================
    def _build_pre_check_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.pre_label = QLabel()
        v.addWidget(self.pre_label)

        fields = [
            {"attr": "pe_responsible", "label": "PE Responsible", "type": "text"},
            {"attr": "samples_before", "label": "Samples Before", "type": "combo",
             "options": [s.value for s in NAOngoingReceived]},
            {"attr": "pe_requirement", "label": "PE Requirement", "type": "combo",
             "options": [s.value for s in NAOngoingReceived]},
            {"attr": "measurement_report", "label": "Measurement Report", "type": "combo",
             "options": [s.value for s in NAOngoingReceived]},
            {"attr": "feedback", "label": "Pre-check Feedback", "type": "combo",
             "options": [s.value for s in PrecheckFeedback]},
            {"attr": "due_date", "label": "Due Date", "type": "date"},
            {"attr": "actions", "label": "Actions", "type": "textarea"},
            {"attr": "comments", "label": "Comments", "type": "textarea"},
        ]
        self.pre_form = DynamicForm(fields)
        self.pre_form.saved.connect(self._refresh_pre_check_tab)
        v.addWidget(self.pre_form)
        v.addStretch()
        self.tabs.addTab(w, "3.4 Pre-check")

    def _refresh_pre_check_tab(self):
        if not self.current_part:
            self.pre_label.setText("Select a Part Number in the tree to manage Pre-check.")
            self.pre_form.clear()
            return
        pre = self.pc.get_pre_check(self.current_part)
        self.pre_label.setText(
            f"Part Number: <b>{self.current_part.part_number}</b> — "
            f"Overall Status: <b>{pre.overall_status}</b>")
        self.pre_form.bind(pre, self.pc.save)

    # ==================================================================
    # 3.5 E2E Follow-up (per Transfer, 3 mandatory meetings)
    # ==================================================================
    def _build_e2e_tab(self):
        w = QWidget()
        outer = QVBoxLayout(w)
        self.e2e_label = QLabel()
        outer.addWidget(self.e2e_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)
        inner = QWidget()
        scroll.setWidget(inner)
        v = QVBoxLayout(inner)

        kickoff_box = QGroupBox("Kick-off Call")
        kb = QVBoxLayout(kickoff_box)
        self.kickoff_form = DynamicForm([
            {"attr": "kickoff_calendar_week", "label": "Planned Calendar Week", "type": "text"},
            {"attr": "kickoff_status", "label": "Status", "type": "combo",
             "options": [s.value for s in MeetingStatus]},
        ])
        self.kickoff_form.saved.connect(self._refresh_e2e_tab)
        kb.addWidget(self.kickoff_form)
        v.addWidget(kickoff_box)

        pcn_box = QGroupBox("PCN & PPAP Call")
        pb = QVBoxLayout(pcn_box)
        self.pcn_form = DynamicForm([
            {"attr": "pcn_ppap_calendar_week", "label": "Planned Calendar Week", "type": "text"},
            {"attr": "pcn_ppap_status", "label": "Status", "type": "combo",
             "options": [s.value for s in MeetingStatus]},
            {"attr": "pcn_decision", "label": "PCN Decision", "type": "combo",
             "options": [s.value for s in YesNo]},
            {"attr": "pcn_status", "label": "PCN Status", "type": "combo",
             "options": [s.value for s in PCNStatus]},
            {"attr": "pcn_action_list", "label": "Action List (one per line)", "type": "textarea"},
        ])
        self.pcn_form.saved.connect(self._refresh_e2e_tab)
        pb.addWidget(self.pcn_form)
        v.addWidget(pcn_box)

        sop_box = QGroupBox("SOP Readiness Call")
        sb = QVBoxLayout(sop_box)
        self.sop_form = DynamicForm([
            {"attr": "sop_calendar_week", "label": "Planned Calendar Week", "type": "text"},
            {"attr": "sop_status", "label": "Status", "type": "combo",
             "options": [s.value for s in MeetingStatus]},
            {"attr": "sop_link_to_e2e_file", "label": "Link to E2E File", "type": "text"},
            {"attr": "sop_comments", "label": "Comments", "type": "textarea"},
            {"attr": "sop_open_actions", "label": "Open Actions (one per line)", "type": "textarea"},
        ])
        self.sop_form.saved.connect(self._refresh_e2e_tab)
        sb.addWidget(self.sop_form)
        v.addWidget(sop_box)
        v.addStretch()

        self.tabs.addTab(w, "3.5 E2E Follow-up")

    def _refresh_e2e_tab(self):
        if not self.current_transfer:
            self.e2e_label.setText("Select a transfer.")
            for f in (self.kickoff_form, self.pcn_form, self.sop_form):
                f.clear()
            return
        e2e = self.pc.get_e2e(self.current_transfer)
        self.e2e_label.setText(
            f"Overall E2E Status: <b>{e2e.overall_status}</b> — Progress: {e2e.progress_percent}%")
        self.kickoff_form.bind(e2e, self.pc.save)
        self.pcn_form.bind(e2e, self.pc.save)
        self.sop_form.bind(e2e, self.pc.save)

    # ==================================================================
    # 3.6 Applicator / Counter Part (per Part Number, conditional)
    # ==================================================================
    def _build_applicator_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.app_label = QLabel()
        v.addWidget(self.app_label)

        self.applicator_fields = [
            {"attr": "pe", "label": "PE", "type": "text"},
            {"attr": "urgency", "label": "Urgency", "type": "combo",
             "options": [u.value for u in Urgency]},
            {"attr": "applicator_required", "label": "Applicator Required", "type": "combo",
             "options": [y.value for y in YesNo]},
            {"attr": "applicator", "label": "Applicator", "type": "text"},
            {"attr": "crimping_specification", "label": "Crimping Specification", "type": "text"},
            {"attr": "terminal", "label": "Terminal", "type": "text"},
            {"attr": "wire_section", "label": "Wire Section", "type": "text"},
            {"attr": "number_of_parts", "label": "Number of Parts", "type": "int"},
            {"attr": "required_approvals", "label": "Required Approvals", "type": "text"},
            {"attr": "applicator_available_location", "label": "Applicator Available Location", "type": "text"},
            {"attr": "crimping_request", "label": "Crimping Request", "type": "text"},
            {"attr": "comments", "label": "Comments", "type": "textarea"},
        ]
        self.applicator_form = DynamicForm(self.applicator_fields)
        self.applicator_form.saved.connect(self._refresh_applicator_tab)
        v.addWidget(self.applicator_form)

        self.counter_part_fields = [
            {"attr": "pe", "label": "PE", "type": "text"},
            {"attr": "counter_part", "label": "Counter Part", "type": "text"},
            {"attr": "terminal", "label": "Terminal", "type": "text"},
            {"attr": "crimping", "label": "Crimping", "type": "text"},
            {"attr": "terminal_request", "label": "Terminal Request", "type": "text"},
            {"attr": "status", "label": "Status", "type": "combo",
             "options": [s.value for s in SimpleStatus]},
            {"attr": "comments", "label": "Comments", "type": "textarea"},
        ]
        self.counter_part_form = DynamicForm(self.counter_part_fields)
        self.counter_part_form.saved.connect(self._refresh_applicator_tab)
        v.addWidget(self.counter_part_form)
        v.addStretch()

        self.tabs.addTab(w, "3.6 Applicator / Counter Part")

    def _refresh_applicator_tab(self):
        if not self.current_transfer or not self.current_part:
            self.app_label.setText("Select a Part Number in the tree.")
            self.applicator_form.clear()
            self.counter_part_form.clear()
            self.applicator_form.hide()
            self.counter_part_form.hide()
            return

        if self.pc.uses_applicator(self.current_transfer):
            self.app_label.setText(
                f"Activity = Stamping → <b>Applicator</b> section for {self.current_part.part_number}")
            applicator = self.pc.get_applicator(self.current_part)
            self.applicator_form.bind(applicator, self.pc.save)
            self.applicator_form.show()
            self.counter_part_form.clear()
            self.counter_part_form.hide()
        else:
            self.app_label.setText(
                f"Activity = Molding → <b>Counter Part</b> section for {self.current_part.part_number}")
            counter_part = self.pc.get_counter_part(self.current_part)
            self.counter_part_form.bind(counter_part, self.pc.save)
            self.counter_part_form.show()
            self.applicator_form.clear()
            self.applicator_form.hide()

    # ==================================================================
    # 3.7 Training (per Tool)
    # ==================================================================
    def _build_training_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.tr_label = QLabel()
        v.addWidget(self.tr_label)

        self.tr_required_checkbox = QCheckBox("Training Required")
        self.tr_required_checkbox.stateChanged.connect(self._on_training_required_changed)
        v.addWidget(self.tr_required_checkbox)

        fields = [
            {"attr": "planned_calendar_week", "label": "Planned Calendar Week", "type": "text"},
            {"attr": "duration", "label": "Duration", "type": "text"},
            {"attr": "invitation_sent", "label": "Invitation Sent", "type": "bool"},
            {"attr": "status", "label": "Status", "type": "combo",
             "options": [s.value for s in TrainingStatus]},
            {"attr": "comments", "label": "Comments", "type": "textarea"},
        ]
        self.training_form = DynamicForm(fields)
        self.training_form.saved.connect(self._refresh_training_tab)
        v.addWidget(self.training_form)
        v.addStretch()

        self.tabs.addTab(w, "3.7 Training")

    def _refresh_training_tab(self):
        if not self.current_tool:
            self.tr_label.setText("Select a Tool in the tree to manage Training.")
            self.training_form.clear()
            self.tr_required_checkbox.setEnabled(False)
            return
        self.tr_required_checkbox.setEnabled(True)
        training = self.pc.get_training(self.current_tool)
        self.tr_label.setText(
            f"Tool: <b>{self.current_tool.tool_number}</b> — Status: <b>{training.overall_status}</b>")

        self.tr_required_checkbox.blockSignals(True)
        self.tr_required_checkbox.setChecked(training.required)
        self.tr_required_checkbox.blockSignals(False)

        self.training_form.bind(training, self.pc.save)
        self.training_form.setEnabled(training.required)

    def _on_training_required_changed(self, state):
        if not self.current_tool:
            return
        training = self.pc.get_training(self.current_tool)
        training.required = bool(state)
        self.pc.save(training)
        self._refresh_training_tab()

    # ==================================================================
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
