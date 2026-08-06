"""
Thin factory functions that build ready-to-embed QChartView widgets from
plain Python data (dict / list-of-tuples). Keeps view code declarative.
"""
from __future__ import annotations

from PySide6.QtCharts import (
    QChart, QChartView, QPieSeries, QBarSeries, QBarSet,
    QLineSeries, QValueAxis, QBarCategoryAxis,
)
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt

PALETTE = ["#1F4E79", "#3D8BFD", "#2ecc71", "#f1c40f", "#e74c3c",
           "#9b59b6", "#1abc9c", "#e67e22", "#34495e", "#7f8c8d"]


def _base_chart(title: str) -> QChart:
    chart = QChart()
    chart.setTitle(title)
    chart.setAnimationOptions(QChart.SeriesAnimations)
    chart.legend().setVisible(True)
    chart.legend().setAlignment(Qt.AlignBottom)
    chart.setBackgroundVisible(False)
    title_font = QFont()
    title_font.setBold(True)
    title_font.setPointSize(11)
    chart.setTitleFont(title_font)
    return chart


def make_pie_chart(data: dict, title: str = "") -> QChartView:
    series = QPieSeries()
    for i, (label, value) in enumerate(data.items()):
        if value <= 0:
            continue
        slice_ = series.append(f"{label} ({value})", value)
        slice_.setBrush(QColor(PALETTE[i % len(PALETTE)]))
        slice_.setLabelVisible(False)
    chart = _base_chart(title)
    chart.addSeries(series)
    view = QChartView(chart)
    view.setRenderHint(QPainter.Antialiasing)
    view.setMinimumHeight(240)
    return view


def make_bar_chart(data: dict, title: str = "", y_title: str = "") -> QChartView:
    bar_set = QBarSet("Count")
    bar_set.setColor(QColor("#1F4E79"))
    categories = list(data.keys())
    for cat in categories:
        bar_set.append(data[cat])

    series = QBarSeries()
    series.append(bar_set)

    chart = _base_chart(title)
    chart.addSeries(series)
    chart.legend().setVisible(False)

    axis_x = QBarCategoryAxis()
    axis_x.append(categories)
    chart.addAxis(axis_x, Qt.AlignBottom)
    series.attachAxis(axis_x)

    axis_y = QValueAxis()
    max_val = max(data.values()) if data else 1
    axis_y.setRange(0, max(max_val * 1.2, 1))
    axis_y.setTitleText(y_title)
    chart.addAxis(axis_y, Qt.AlignLeft)
    series.attachAxis(axis_y)

    view = QChartView(chart)
    view.setRenderHint(QPainter.Antialiasing)
    view.setMinimumHeight(240)
    return view


def make_horizontal_progress_bar_chart(pairs: list[tuple[str, float]], title: str = "") -> QChartView:
    """Used for 'Progress by Transfer' - one bar per transfer, 0-100 scale."""
    bar_set = QBarSet("Progress %")
    bar_set.setColor(QColor("#3D8BFD"))
    categories = [p[0] for p in pairs]
    for _, val in pairs:
        bar_set.append(val)

    series = QBarSeries()
    series.append(bar_set)

    chart = _base_chart(title)
    chart.addSeries(series)
    chart.legend().setVisible(False)

    axis_x = QBarCategoryAxis()
    axis_x.append(categories)
    chart.addAxis(axis_x, Qt.AlignBottom)
    series.attachAxis(axis_x)

    axis_y = QValueAxis()
    axis_y.setRange(0, 100)
    axis_y.setTitleText("%")
    chart.addAxis(axis_y, Qt.AlignLeft)
    series.attachAxis(axis_y)

    view = QChartView(chart)
    view.setRenderHint(QPainter.Antialiasing)
    view.setMinimumHeight(260)
    return view


def make_line_chart(pairs: list[tuple[str, float]], title: str = "", y_title: str = "") -> QChartView:
    series = QLineSeries()
    series.setColor(QColor("#1F4E79"))
    categories = [p[0] for p in pairs]
    for i, (_, val) in enumerate(pairs):
        series.append(i, val)

    chart = _base_chart(title)
    chart.addSeries(series)
    chart.legend().setVisible(False)

    axis_x = QBarCategoryAxis()
    axis_x.append(categories)
    chart.addAxis(axis_x, Qt.AlignBottom)
    series.attachAxis(axis_x)

    axis_y = QValueAxis()
    max_val = max((v for _, v in pairs), default=1)
    axis_y.setRange(0, max(max_val * 1.2, 1))
    axis_y.setTitleText(y_title)
    chart.addAxis(axis_y, Qt.AlignLeft)
    series.attachAxis(axis_y)

    view = QChartView(chart)
    view.setRenderHint(QPainter.Antialiasing)
    view.setMinimumHeight(240)
    return view
