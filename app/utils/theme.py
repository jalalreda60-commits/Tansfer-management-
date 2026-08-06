"""
Theming: a professional "blue industrial" palette, with light & dark QSS
variants generated from the same token set so they stay visually consistent.
"""
from __future__ import annotations

# Shared brand tokens
PRIMARY = "#1F4E79"        # deep industrial blue
PRIMARY_LIGHT = "#2E6DA4"
ACCENT = "#3D8BFD"
SUCCESS = "#2ecc71"
WARNING = "#f1c40f"
DANGER = "#e74c3c"
GREY = "#95a5a6"

LIGHT_TOKENS = {
    "bg": "#F4F6F9",
    "surface": "#FFFFFF",
    "border": "#D9E1E8",
    "text": "#1B2733",
    "text_muted": "#5A6B7B",
    "sidebar_bg": PRIMARY,
    "sidebar_text": "#EAF1F8",
    "sidebar_active": PRIMARY_LIGHT,
    "table_alt": "#F0F4F8",
}

DARK_TOKENS = {
    "bg": "#121A24",
    "surface": "#1B2733",
    "border": "#2B3B4A",
    "text": "#E7EEF5",
    "text_muted": "#9FB0C0",
    "sidebar_bg": "#0E1620",
    "sidebar_text": "#DCE8F5",
    "sidebar_active": PRIMARY,
    "table_alt": "#202D3A",
}


def build_qss(tokens: dict) -> str:
    return f"""
    QWidget {{
        background-color: {tokens['bg']};
        color: {tokens['text']};
        font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
        font-size: 13px;
    }}

    QMainWindow {{
        background-color: {tokens['bg']};
    }}

    /* --- Sidebar --- */
    #Sidebar {{
        background-color: {tokens['sidebar_bg']};
        border: none;
    }}
    #Sidebar QPushButton {{
        color: {tokens['sidebar_text']};
        background-color: transparent;
        border: none;
        text-align: left;
        padding: 12px 18px;
        font-size: 14px;
        font-weight: 500;
        border-radius: 6px;
        margin: 2px 8px;
    }}
    #Sidebar QPushButton:hover {{
        background-color: rgba(255,255,255,0.08);
    }}
    #Sidebar QPushButton:checked {{
        background-color: {tokens['sidebar_active']};
        color: white;
        font-weight: 600;
    }}
    #SidebarTitle {{
        color: white;
        font-size: 16px;
        font-weight: 700;
        padding: 18px 16px 8px 16px;
    }}

    /* --- Cards / surfaces --- */
    #Card, QFrame#Card {{
        background-color: {tokens['surface']};
        border: 1px solid {tokens['border']};
        border-radius: 10px;
    }}

    #TopBar {{
        background-color: {tokens['surface']};
        border-bottom: 1px solid {tokens['border']};
    }}

    /* --- Tables --- */
    QTableWidget, QTableView {{
        background-color: {tokens['surface']};
        alternate-background-color: {tokens['table_alt']};
        gridline-color: {tokens['border']};
        border: 1px solid {tokens['border']};
        border-radius: 8px;
        selection-background-color: {ACCENT};
        selection-color: white;
    }}
    QHeaderView::section {{
        background-color: {PRIMARY};
        color: white;
        padding: 6px;
        border: none;
        font-weight: 600;
    }}

    /* --- Inputs --- */
    QLineEdit, QComboBox, QDateEdit, QSpinBox, QTextEdit, QPlainTextEdit {{
        background-color: {tokens['surface']};
        border: 1px solid {tokens['border']};
        border-radius: 6px;
        padding: 5px 8px;
        color: {tokens['text']};
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{
        border: 1px solid {ACCENT};
    }}

    /* --- Buttons --- */
    QPushButton {{
        background-color: {PRIMARY};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 7px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {PRIMARY_LIGHT};
    }}
    QPushButton:disabled {{
        background-color: {tokens['border']};
        color: {tokens['text_muted']};
    }}
    QPushButton#SecondaryButton {{
        background-color: transparent;
        border: 1px solid {tokens['border']};
        color: {tokens['text']};
    }}
    QPushButton#DangerButton {{
        background-color: {DANGER};
    }}

    /* --- Tabs --- */
    QTabWidget::pane {{
        border: 1px solid {tokens['border']};
        border-radius: 8px;
        top: -1px;
    }}
    QTabBar::tab {{
        background: {tokens['bg']};
        border: 1px solid {tokens['border']};
        padding: 8px 14px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }}
    QTabBar::tab:selected {{
        background: {PRIMARY};
        color: white;
        font-weight: 600;
    }}

    /* --- Progress bars --- */
    QProgressBar {{
        border: 1px solid {tokens['border']};
        border-radius: 6px;
        text-align: center;
        background-color: {tokens['table_alt']};
        height: 16px;
    }}
    QProgressBar::chunk {{
        background-color: {ACCENT};
        border-radius: 6px;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
    }}
    QScrollBar::handle:vertical {{
        background: {tokens['border']};
        border-radius: 5px;
    }}
    """


LIGHT_QSS = build_qss(LIGHT_TOKENS)
DARK_QSS = build_qss(DARK_TOKENS)


def get_stylesheet(dark: bool = False) -> str:
    return DARK_QSS if dark else LIGHT_QSS
