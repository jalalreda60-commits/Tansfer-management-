"""
Reusable dialog: Attachments + Comments + History tabs, bound to any
(entity_type, entity_id) pair via TransferController's generic helpers.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QListWidget,
    QListWidgetItem, QPushButton, QTextEdit, QFileDialog, QMessageBox, QLabel,
)


class EntityDetailDialog(QDialog):
    def __init__(self, controller, entity_type: str, entity_id: int, title: str, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.setWindowTitle(f"Details — {title}")
        self.setMinimumSize(520, 480)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        tabs.addTab(self._build_attachments_tab(), "📎 Attachments")
        tabs.addTab(self._build_comments_tab(), "💬 Comments")
        tabs.addTab(self._build_history_tab(), "🕒 History")

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    # ------------------------------------------------------------------
    def _build_attachments_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.att_list = QListWidget()
        v.addWidget(self.att_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Attach File")
        add_btn.clicked.connect(self._attach_file)
        del_btn = QPushButton("Remove")
        del_btn.setObjectName("DangerButton")
        del_btn.clicked.connect(self._remove_attachment)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        v.addLayout(btn_row)

        self._reload_attachments()
        return w

    def _reload_attachments(self):
        self.att_list.clear()
        for att in self.controller.list_attachments(self.entity_type, self.entity_id):
            item = QListWidgetItem(f"{att.file_name}  ({att.uploaded_at.strftime('%Y-%m-%d %H:%M')})")
            item.setData(1000, att.id)
            self.att_list.addItem(item)

    def _attach_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select file to attach")
        if path:
            self.controller.add_attachment(self.entity_type, self.entity_id, path)
            self._reload_attachments()

    def _remove_attachment(self):
        item = self.att_list.currentItem()
        if not item:
            return
        att_id = item.data(1000)
        if QMessageBox.question(self, "Remove attachment", "Remove this attachment?") == QMessageBox.Yes:
            self.controller.delete_attachment(att_id)
            self._reload_attachments()

    # ------------------------------------------------------------------
    def _build_comments_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.comment_list = QListWidget()
        v.addWidget(self.comment_list)

        self.comment_input = QTextEdit()
        self.comment_input.setMaximumHeight(70)
        self.comment_input.setPlaceholderText("Write a comment...")
        v.addWidget(self.comment_input)

        add_btn = QPushButton("Add Comment")
        add_btn.clicked.connect(self._add_comment)
        v.addWidget(add_btn)

        self._reload_comments()
        return w

    def _reload_comments(self):
        self.comment_list.clear()
        for c in self.controller.list_comments(self.entity_type, self.entity_id):
            self.comment_list.addItem(
                f"[{c.created_at.strftime('%Y-%m-%d %H:%M')}] {c.author}: {c.text}"
            )

    def _add_comment(self):
        text = self.comment_input.toPlainText().strip()
        if not text:
            return
        self.controller.add_comment(self.entity_type, self.entity_id, text)
        self.comment_input.clear()
        self._reload_comments()

    # ------------------------------------------------------------------
    def _build_history_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.history_list = QListWidget()
        v.addWidget(self.history_list)
        for h in self.controller.list_history(self.entity_type, self.entity_id):
            details = f" — {h.details}" if h.details else ""
            self.history_list.addItem(
                f"[{h.timestamp.strftime('%Y-%m-%d %H:%M')}] {h.action}{details}"
            )
        return w
