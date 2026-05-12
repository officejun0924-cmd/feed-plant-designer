"""베어링 브랜드 → 번호 연계 선택 위젯"""
from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QComboBox, QLabel,
)
from PyQt6.QtCore import Qt
from database.db_loader import DBLoader

BEARING_BRANDS = ["SKF", "NSK", "FAG", "UCF", "UCP", "UCFC"]


class BearingSelectGroup(QWidget):
    """브랜드 콤보 → 번호 콤보 연계 + 사양 표시"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 브랜드
        self._brand_combo = QComboBox()
        self._brand_combo.addItems(BEARING_BRANDS)
        self._brand_combo.setMinimumWidth(165)
        layout.addRow("  베어링 브랜드", self._brand_combo)

        # 번호 (브랜드 연계)
        self._number_combo = QComboBox()
        self._number_combo.setMinimumWidth(165)
        layout.addRow("  베어링 번호", self._number_combo)

        # 베어링 스펙 표시 (읽기전용)
        self._spec_label = QLabel("—")
        self._spec_label.setObjectName("result_label")
        self._spec_label.setWordWrap(True)
        layout.addRow("  사양", self._spec_label)

        # 초기 번호 목록 로드
        self._load_numbers("SKF")

        self._brand_combo.currentTextChanged.connect(self._load_numbers)
        self._number_combo.currentTextChanged.connect(self._update_spec)

    def _load_numbers(self, brand: str):
        self._number_combo.blockSignals(True)
        self._number_combo.clear()
        nums = DBLoader.get_bearing_numbers_by_brand(brand)
        if nums:
            self._number_combo.addItems(nums)
        else:
            self._number_combo.addItem("(DB 없음)")
        self._number_combo.blockSignals(False)
        self._update_spec(self._number_combo.currentText())

    def _update_spec(self, number: str):
        brand = self._brand_combo.currentText()
        data = DBLoader.get_bearing_by_number(brand, number)
        if data:
            bore  = data.get("bore_mm", "—")
            outer = data.get("outer_dia_mm", "—")
            width = data.get("width_mm", "—")
            C     = data.get("C_kN", "—")
            self._spec_label.setText(
                f"내경 {bore}mm / 외경 {outer}mm / 폭 {width}mm  |  C = {C} kN"
            )
        else:
            self._spec_label.setText("—")

    # ── 외부 인터페이스 ─────────────────────────────────────────────────────
    def brand(self) -> str:
        return self._brand_combo.currentText()

    def number(self) -> str:
        return self._number_combo.currentText()

    def desired_life_hr(self) -> float:
        """고정 25,000 hr (UI 입력 제거됨)"""
        return 25000.0

    def bearing_data(self) -> dict:
        return DBLoader.get_bearing_by_number(self.brand(), self.number())
