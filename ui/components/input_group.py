from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QDoubleSpinBox, QSpinBox
from PyQt6.QtCore import pyqtSignal, Qt


class InputGroup(QWidget):
    """라벨 + 숫자 입력 + 단위 라벨 묶음 위젯"""
    valueChanged = pyqtSignal(float)

    def __init__(self, label: str, unit: str = "",
                 min_val: float = 0.0, max_val: float = 999999.0,
                 default: float = 0.0, decimals: int = 2,
                 tooltip: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._label = QLabel(label)
        self._label.setMinimumWidth(160)
        self._label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._spinbox = QDoubleSpinBox()
        self._spinbox.setMinimum(min_val)
        self._spinbox.setMaximum(max_val)
        self._spinbox.setValue(default)
        self._spinbox.setDecimals(decimals)
        self._spinbox.setSingleStep(max(0.01, (max_val - min_val) / 1000))
        self._spinbox.setMinimumWidth(110)
        if tooltip:
            self._spinbox.setToolTip(tooltip)
            self._label.setToolTip(tooltip)

        self._unit = QLabel(unit)
        self._unit.setMinimumWidth(55)
        self._unit.setObjectName("result_label")

        layout.addWidget(self._label)
        layout.addWidget(self._spinbox)
        layout.addWidget(self._unit)
        layout.addStretch()

        self._spinbox.valueChanged.connect(lambda v: self.valueChanged.emit(v))

    def value(self) -> float:
        return self._spinbox.value()

    def set_value(self, v: float):
        self._spinbox.setValue(v)

    def set_error(self, msg: str = ""):
        self._spinbox.setProperty("error", "true")
        self._spinbox.style().unpolish(self._spinbox)
        self._spinbox.style().polish(self._spinbox)
        if msg:
            self._spinbox.setToolTip(msg)

    def clear_error(self):
        self._spinbox.setProperty("error", "false")
        self._spinbox.style().unpolish(self._spinbox)
        self._spinbox.style().polish(self._spinbox)


class ComboGroup(QWidget):
    """라벨 + 콤보박스 묶음 위젯"""
    from PyQt6.QtWidgets import QComboBox
    currentTextChanged = pyqtSignal(str)

    def __init__(self, label: str, options: list,
                 default: str = "", parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QComboBox
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        lbl = QLabel(label)
        lbl.setMinimumWidth(160)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._combo = QComboBox()
        self._combo.addItems(options)
        self._combo.setMinimumWidth(165)
        if default and default in options:
            self._combo.setCurrentText(default)

        layout.addWidget(lbl)
        layout.addWidget(self._combo)
        layout.addStretch()

        self._combo.currentTextChanged.connect(self.currentTextChanged)

    def current_text(self) -> str:
        return self._combo.currentText()

    def set_current_text(self, text: str):
        self._combo.setCurrentText(text)
