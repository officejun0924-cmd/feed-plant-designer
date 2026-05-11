MAIN_STYLE = """
QMainWindow {
    background-color: #1e1e2e;
}

QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Malgun Gothic", "맑은 고딕", sans-serif;
    font-size: 10pt;
}

QTabWidget::pane {
    border: 1px solid #45475a;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #313244;
    color: #cdd6f4;
    padding: 8px 16px;
    margin-right: 2px;
    border-radius: 4px 4px 0 0;
}

QTabBar::tab:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: #45475a;
}

QGroupBox {
    border: 1px solid #45475a;
    border-radius: 6px;
    margin-top: 12px;
    padding: 8px;
    font-weight: bold;
    color: #89b4fa;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 10px;
}

QDoubleSpinBox, QSpinBox, QComboBox, QLineEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
    color: #cdd6f4;
    min-width: 100px;
}

QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus, QLineEdit:focus {
    border: 1px solid #89b4fa;
}

QDoubleSpinBox[error="true"], QSpinBox[error="true"] {
    border: 1px solid #f38ba8;
}

QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: bold;
    font-size: 11pt;
}

QPushButton:hover {
    background-color: #b4d0ff;
}

QPushButton:pressed {
    background-color: #6c9ef8;
}

QPushButton#btn_pdf {
    background-color: #f38ba8;
}

QPushButton#btn_pdf:hover {
    background-color: #f5a0b5;
}

QPushButton#btn_excel {
    background-color: #a6e3a1;
    color: #1e1e2e;
}

QPushButton#btn_excel:hover {
    background-color: #b8f0b3;
}

QScrollArea {
    border: none;
}

QScrollBar:vertical {
    background: #313244;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #585b70;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #89b4fa;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QLabel#result_value {
    color: #a6e3a1;
    font-weight: bold;
    font-size: 10pt;
}

QLabel#result_label {
    color: #a6adc8;
}

QTableWidget {
    background-color: #313244;
    gridline-color: #45475a;
    border: 1px solid #45475a;
    border-radius: 4px;
}

QTableWidget::item {
    padding: 4px 8px;
}

QTableWidget::item:selected {
    background-color: #45475a;
}

QHeaderView::section {
    background-color: #45475a;
    color: #89b4fa;
    padding: 6px;
    border: none;
    font-weight: bold;
}

QTextEdit#notes_area {
    background-color: #2a2a3e;
    border: 1px solid #45475a;
    border-radius: 4px;
    color: #f9e2af;
    font-size: 9pt;
}

QSplitter::handle {
    background-color: #45475a;
    width: 3px;
}

QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
}

QMenuBar::item:selected {
    background-color: #313244;
}

QMenu {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
}

QMenu::item:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
}

QStatusBar {
    background-color: #181825;
    color: #a6adc8;
}

QToolBar {
    background-color: #181825;
    spacing: 4px;
    padding: 4px;
    border-bottom: 1px solid #45475a;
}

/* ── 홈 화면 ── */
QLabel#home_title {
    color: #89b4fa;
    font-size: 22pt;
    font-weight: bold;
}

QLabel#home_subtitle {
    color: #a6adc8;
    font-size: 11pt;
}

QPushButton#home_btn {
    background-color: #313244;
    color: #cdd6f4;
    border: 2px solid #45475a;
    border-radius: 12px;
    padding: 16px 32px;
    font-size: 14pt;
    font-weight: bold;
}

QPushButton#home_btn:hover {
    background-color: #45475a;
    border-color: #89b4fa;
    color: #89b4fa;
}

QPushButton#home_btn:pressed {
    background-color: #89b4fa;
    color: #1e1e2e;
}

/* ── 장비 선택 화면 카드 ── */
QPushButton#equip_card_btn {
    background-color: #25253a;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 10pt;
    font-weight: normal;
    text-align: left;
}

QPushButton#equip_card_btn:hover {
    background-color: #313244;
    border-color: #89b4fa;
    color: #89b4fa;
}

QPushButton#equip_card_btn:pressed {
    background-color: #89b4fa;
    color: #1e1e2e;
}
"""
