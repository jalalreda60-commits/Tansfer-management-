"""
DynamicForm: builds a QFormLayout from a declarative field spec and binds
it to an arbitrary object's attributes. This is what lets the many
Preparation sub-modules (PTT, Safety Stock, Raw Material, Pre-check,
Applicator, Counter Part, Training ...) share one implementation instead
of duplicating near-identical form code seven times.

Field spec item: dict with keys
    attr:       object attribute name
    label:      display label
    type:       'text' | 'textarea' | 'combo' | 'date' | 'int' | 'bool'
    options:    list[str] (for 'combo')
    on_change:  optional callable(value) invoked after this field is saved
"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QComboBox, QDateEdit, QSpinBox,
    QTextEdit, QCheckBox, QLabel,
)


class DynamicForm(QWidget):
    saved = Signal()

    def __init__(self, field_specs: list[dict], parent=None):
        super().__init__(parent)
        self.field_specs = field_specs
        self.obj = None
        self._controller_save = None
        self._widgets: dict[str, QWidget] = {}

        self.layout_ = QFormLayout(self)
        self.layout_.setLabelAlignment(Qt.AlignRight)
        self.layout_.setSpacing(10)
        self._build_widgets()

    def _build_widgets(self):
        for spec in self.field_specs:
            widget = self._make_widget(spec)
            self._widgets[spec["attr"]] = widget
            self.layout_.addRow(QLabel(spec["label"] + ":"), widget)

    def _make_widget(self, spec: dict) -> QWidget:
        ftype = spec["type"]
        if ftype == "text":
            w = QLineEdit()
            w.editingFinished.connect(lambda s=spec, w=w: self._commit(s, w.text()))
        elif ftype == "textarea":
            w = QTextEdit()
            w.setMaximumHeight(80)
            w.focusOutEvent = self._wrap_focus_out(w, spec)
        elif ftype == "combo":
            w = QComboBox()
            w.addItems(spec.get("options", []))
            w.currentTextChanged.connect(lambda val, s=spec: self._commit(s, val))
        elif ftype == "date":
            w = QDateEdit()
            w.setCalendarPopup(True)
            w.setDisplayFormat("yyyy-MM-dd")
            w.dateChanged.connect(lambda val, s=spec: self._commit(s, val.toPython()))
        elif ftype == "int":
            w = QSpinBox()
            w.setRange(0, 1_000_000)
            w.valueChanged.connect(lambda val, s=spec: self._commit(s, val))
        elif ftype == "bool":
            w = QCheckBox()
            w.stateChanged.connect(lambda val, s=spec: self._commit(s, bool(val)))
        else:
            w = QLineEdit()
        return w

    def _wrap_focus_out(self, widget: QTextEdit, spec: dict):
        original = QTextEdit.focusOutEvent

        def handler(event):
            self._commit(spec, widget.toPlainText())
            original(widget, event)
        return handler

    def _commit(self, spec: dict, value):
        if self.obj is None:
            return
        setattr(self.obj, spec["attr"], value)
        if self._controller_save:
            self._controller_save(self.obj)
        callback = spec.get("on_change")
        if callback:
            callback(value)
        self.saved.emit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def bind(self, obj, controller_save_fn):
        """Load `obj`'s current values into the widgets; wire future edits
        to call controller_save_fn(obj) to persist immediately."""
        self.obj = obj
        self._controller_save = controller_save_fn
        for spec in self.field_specs:
            widget = self._widgets[spec["attr"]]
            value = getattr(obj, spec["attr"], None)
            self._set_widget_value(widget, spec, value)
        self.setEnabled(True)

    def clear(self, message: str = "Select an item to edit its details."):
        self.obj = None
        self.setEnabled(False)

    def _set_widget_value(self, widget, spec, value):
        widget.blockSignals(True)
        ftype = spec["type"]
        try:
            if ftype == "text":
                widget.setText(value or "")
            elif ftype == "textarea":
                widget.setPlainText(value or "")
            elif ftype == "combo":
                idx = widget.findText(value or "")
                widget.setCurrentIndex(idx if idx >= 0 else 0)
            elif ftype == "date":
                d = value or dt.date.today()
                widget.setDate(d)
            elif ftype == "int":
                widget.setValue(value or 0)
            elif ftype == "bool":
                widget.setChecked(bool(value))
        finally:
            widget.blockSignals(False)
