"""체인/스프라켓 입력 + PCD 자동 계산 위젯"""
import math
from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QComboBox, QSpinBox, QLabel,
)
from PyQt6.QtCore import Qt
from app.config import CHAIN_PITCH, DIRECT_COUPLING_BRANDS

CHAIN_TYPES = ["RS", "RF"]


class ChainSprocketGroup(QWidget):
    """체인 종류 + Z1 + Z2 → 피치 + PCD 자동 표시"""

    def __init__(self, default_chain: str = "RS", parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 체인 종류
        self._type_combo = QComboBox()
        self._type_combo.addItems(CHAIN_TYPES)
        if default_chain in CHAIN_TYPES:
            self._type_combo.setCurrentText(default_chain)
        self._type_combo.setMinimumWidth(165)
        layout.addRow("  체인 종류", self._type_combo)

        # 체인 호칭 (자동 선정 결과 표시용)
        self._desig_label = QLabel("(계산 후 표시)")
        self._desig_label.setObjectName("result_label")
        layout.addRow("  체인 호칭", self._desig_label)

        # 소 스프로켓 Z1
        self._z1_spin = QSpinBox()
        self._z1_spin.setRange(9, 100)
        self._z1_spin.setValue(19)
        self._z1_spin.setMinimumWidth(110)
        layout.addRow("  소 스프로켓 잇수 Z1", self._z1_spin)

        # 대 스프로켓 Z2
        self._z2_spin = QSpinBox()
        self._z2_spin.setRange(9, 200)
        self._z2_spin.setValue(38)
        self._z2_spin.setMinimumWidth(110)
        layout.addRow("  대 스프로켓 잇수 Z2", self._z2_spin)

        # PCD 표시
        self._pcd1_label = QLabel("—  mm")
        self._pcd2_label = QLabel("—  mm")
        self._pcd1_label.setObjectName("result_label")
        self._pcd2_label.setObjectName("result_label")
        layout.addRow("  소 스프로켓 PCD", self._pcd1_label)
        layout.addRow("  대 스프로켓 PCD", self._pcd2_label)

        self._z1_spin.valueChanged.connect(self._update_pcd)
        self._z2_spin.valueChanged.connect(self._update_pcd)
        self._type_combo.currentTextChanged.connect(self._update_pcd)
        self._update_pcd()

    def _get_pitch(self) -> float:
        """현재 체인 종류 기준 대표 피치 (RS-60 or RF-60 기본값) mm"""
        ctype = self._type_combo.currentText()
        key = f"{ctype}-60"
        return CHAIN_PITCH.get(key, 19.05)

    def _update_pcd(self):
        pitch = self._get_pitch()
        z1 = self._z1_spin.value()
        z2 = self._z2_spin.value()
        pcd1 = pitch / math.sin(math.pi / z1)
        pcd2 = pitch / math.sin(math.pi / z2)
        self._pcd1_label.setText(f"{pcd1:.1f}  mm  (Z={z1})")
        self._pcd2_label.setText(f"{pcd2:.1f}  mm  (Z={z2})")

    def update_designation(self, designation: str):
        """계산 완료 후 체인 호칭 업데이트 + PCD 재계산"""
        self._desig_label.setText(designation)
        pitch = CHAIN_PITCH.get(designation, self._get_pitch())
        z1 = self._z1_spin.value()
        z2 = self._z2_spin.value()
        pcd1 = pitch / math.sin(math.pi / z1)
        pcd2 = pitch / math.sin(math.pi / z2)
        self._pcd1_label.setText(f"{pcd1:.1f}  mm  (Z={z1})")
        self._pcd2_label.setText(f"{pcd2:.1f}  mm  (Z={z2})")

    def set_enabled(self, enabled: bool):
        super().setEnabled(enabled)

    # ── 외부 인터페이스 ─────────────────────────────────────────────────────
    def chain_type(self) -> str:
        return self._type_combo.currentText()

    def z1(self) -> int:
        return self._z1_spin.value()

    def z2(self) -> int:
        return self._z2_spin.value()

    def pitch_mm(self) -> float:
        return self._get_pitch()
