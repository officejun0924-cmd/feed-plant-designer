from PyQt6.QtWidgets import (
    QGroupBox, QFormLayout, QLabel, QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class ResultCard(QGroupBox):
    """계산 결과 카드 (GroupBox + FormLayout)"""

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self._layout = QFormLayout(self)
        self._layout.setSpacing(8)
        self._layout.setContentsMargins(12, 16, 12, 12)
        self._rows: dict = {}

    def set_row(self, label: str, value: str, unit: str = ""):
        display = f"{value}  {unit}".strip() if unit else value
        if label in self._rows:
            self._rows[label].setText(display)
        else:
            lbl = QLabel(label)
            lbl.setObjectName("result_label")
            val = QLabel(display)
            val.setObjectName("result_value")
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._layout.addRow(lbl, val)
            self._rows[label] = val

    def clear_rows(self):
        while self._layout.rowCount() > 0:
            self._layout.removeRow(0)
        self._rows.clear()


class BearingResultTable(QGroupBox):
    """구동측/피동측 베어링 선정 결과 테이블"""
    HEADERS = ["항목", "구동측", "피동측"]
    ROWS = [
        ("베어링 번호", "bearing_number"),
        ("제조사", "manufacturer"),
        ("타입", "bearing_type"),
        ("내경 (mm)", "bore_mm"),
        ("외경 (mm)", "outer_dia_mm"),
        ("폭 (mm)", "width_mm"),
        ("등가하중 P (N)", "equivalent_load_P_N"),
        ("요구 C (N)", "required_C_N"),
        ("기본동정격하중 C (N)", "basic_load_rating_C_N"),
        ("L10 수명 (hr)", "L10_hr"),
    ]

    def __init__(self, parent=None):
        super().__init__("베어링 선정 결과", parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 8)

        self._table = QTableWidget(len(self.ROWS), 3)
        self._table.setHorizontalHeaderLabels(self.HEADERS)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setMinimumHeight(len(self.ROWS) * 30 + 32)  # 행 높이 보장
        self.setMinimumHeight(len(self.ROWS) * 30 + 72)

        for i, (label, _) in enumerate(self.ROWS):
            item = QTableWidgetItem(label)
            item.setForeground(QColor("#a6adc8"))
            self._table.setItem(i, 0, item)

        layout.addWidget(self._table)

    def update(self, drive, driven):
        from models.result_models import BearingResult
        for i, (_, attr) in enumerate(self.ROWS):
            for col, result in [(1, drive), (2, driven)]:
                val = getattr(result, attr, "-")
                if isinstance(val, float):
                    text = f"{val:,.1f}" if val > 100 else f"{val:.2f}"
                else:
                    text = str(val)
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(i, col, item)
