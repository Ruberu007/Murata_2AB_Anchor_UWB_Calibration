"""A quiet navy/teal instrument-panel theme, drawn entirely with Qt."""
from PySide6.QtGui import QFont, QFontDatabase
from pathlib import Path
import os

STYLE = '''
QWidget { font-family: "Segoe UI"; font-size: 12px; color: #21344b; }
QMainWindow, QWidget#workspace { background: #f0f4f8; }
QWidget#sidebar { background: #12263d; }
QLabel#brand { color: #ffffff; font-size: 21px; font-weight: 700; }
QLabel#brandSub { color: #69ddd0; font-size: 11px; }
QLabel#sidebarNote { color: #b2c3d6; font-size: 11px; }
QListWidget#navigation { background: transparent; border: none; color: #c5d4e2; outline: none; }
QListWidget#navigation::item { padding: 12px 8px; margin: 2px 0; border-radius: 6px; }
QListWidget#navigation::item:selected { background: #24465d; color: #78eee0; }
QListWidget#navigation::item:hover { background: #1b384e; }
QLabel#pageTitle { font-size: 21px; font-weight: 700; color: #142c44; }
QLabel#pageSubtitle { color: #587087; font-size: 11px; }
QLabel#badge { background: #ddf3ee; color: #126b60; border-radius: 5px; padding: 5px 10px; font-weight: 600; }
QPushButton { background: #ffffff; border: 1px solid #c7d4df; border-radius: 5px; padding: 6px 12px; font-weight: 600; }
QPushButton:hover { background: #e6f5f2; border-color: #159b8d; }
QPushButton:pressed { background: #d0eae5; }
QPushButton[primary="true"] { background: #087f79; color: white; border-color: #087f79; }
QPushButton[primary="true"]:hover { background: #086b66; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: white; border: 1px solid #cbd7e2; border-radius: 4px; padding: 4px; selection-background-color: #087f79; }
QLineEdit:focus, QComboBox:focus { border-color: #087f79; }
QTextEdit, QTextBrowser, QTableView { background: white; border: 1px solid #d5e0e9; border-radius: 5px; selection-background-color: #ddf3ee; selection-color: #143c43; }
QHeaderView::section { background: #e9eff5; color: #34516a; padding: 6px; border: none; border-bottom: 1px solid #cbd7e2; font-weight: 600; }
QTableView { alternate-background-color: #f6f9fc; gridline-color: #e4ecf2; }
QTabWidget::pane { background: white; border: 1px solid #d5e0e9; border-radius: 5px; }
QTabBar::tab { background: #e9eff5; color: #526b81; padding: 6px 10px; border: none; margin-right: 2px; }
QTabBar::tab:selected { background: #ffffff; color: #087f79; font-weight: 600; border-bottom: 2px solid #087f79; }
QLabel#plotGuide { background: #eff7fa; border-left: 3px solid #159b8d; padding: 6px 10px; color: #34566b; font-size: 11px; }
QStatusBar { background: #e5edf4; color: #3b5a71; font-size: 11px; }
QDockWidget::title { background: #e0eef2; padding: 8px; font-weight: 600; }
QCheckBox { spacing: 6px; }
QToolTip { background: #12263d; color: white; border: none; padding: 6px; }
'''


def apply_theme(window):
    # Native Windows font, also available when rendering an offscreen preview.
    font = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / 'segoeui.ttf'
    if font.is_file():
        QFontDatabase.addApplicationFont(str(font))
    window.setFont(QFont('Segoe UI', 9))
    window.setStyleSheet(STYLE)
