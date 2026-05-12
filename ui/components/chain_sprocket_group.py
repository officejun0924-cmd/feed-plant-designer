"""체인/스프라켓 입력 + PCD 자동 계산 위젯"""
import math
from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QComboBox, QSpinBox, QLabel,
)
from PyQt6.QtCore import Qt
from app.config import CHAIN_PITCH

CHAIN_TYPES = ["RS", "RF"]

# 호칭 번호 크기 순서 (적정 여부 비교용)
_PITCH_ORDER = [40, 50, 60, 80, 100, 120, 140, 160]

def _desig_index(desig: str) -> int:
    """호칭 번호의 크기 인덱스 반환 (RS-60 → 2). 없으면 -1."""
    try:
        num = int(desig.split("-")[1])
        return _PITCH_ORDER.index(num)
    except (IndexError, ValueError):
        return -1


class ChainSprocketGroup(QWidget):
    """체인 종류 + 호칭 선택 + Z1 + Z2 → 피치 + PCD 자동 표시 + 적정 여부"""

    def __init__(self, default_chain: str = "RS", parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 체인 종류 (RS / RF)
        self._type_combo = QComboBox()
        self._type_combo.addItems(CHAIN_TYPES)
        if default_chain in CHAIN_TYPES:
            self._type_combo.setCurrentText(default_chain)
        self._type_combo.setMinimumWidth(165)
        layout.addRow("  체인 종류", self._type_combo)

        # 체인 호칭 콤보 (사용자 선택)
        self._desig_combo = QComboBox()
        self._desig_combo.setMinimumWidth(165)
        layout.addRow("  체인 호칭", self._desig_combo)

        # 적정 여부 (계산 후 표시)
        self._adequacy_label = QLabel("(계산 후 표시)")
        self._adequacy_label.setObjectName("result_label")
        layout.addRow("  체인 적정 여부", self._adequacy_label)

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

        # 시그널 연결
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        self._desig_combo.currentTextChanged.connect(self._update_pcd)
        self._z1_spin.valueChanged.connect(self._update_pcd)
        self._z2_spin.valueChanged.connect(self._update_pcd)

        # 초기 호칭 목록 로드
        self._on_type_changed(default_chain)

    # ── 내부 메서드 ──────────────────────────────────────────────────────────
    def _on_type_changed(self, chain_type: str):
        """체인 종류 변경 시 호칭 콤보 재구성"""
        self._desig_combo.blockSignals(True)
        current = self._desig_combo.currentText()
        self._desig_combo.clear()
        desigs = [f"{chain_type}-{n}" for n in _PITCH_ORDER]
        self._desig_combo.addItems(desigs)
        # 같은 번호 유지 (종류만 바뀐 경우)
        try:
            num = current.split("-")[1]
            self._desig_combo.setCurrentText(f"{chain_type}-{num}")
        except (IndexError, AttributeError):
            pass
        self._desig_combo.blockSignals(False)
        self._update_pcd()

    def _current_pitch(self) -> float:
        """현재 선택된 호칭의 피치 (mm)"""
        return CHAIN_PITCH.get(self._desig_combo.currentText(), 19.05)

    def _update_pcd(self):
        pitch = self._current_pitch()
        z1 = self._z1_spin.value()
        z2 = self._z2_spin.value()
        pcd1 = pitch / math.sin(math.pi / z1)
        pcd2 = pitch / math.sin(math.pi / z2)
        self._pcd1_label.setText(f"{pcd1:.1f}  mm  (Z={z1})")
        self._pcd2_label.setText(f"{pcd2:.1f}  mm  (Z={z2})")

    def update_designation(self, recommended: str):
        """계산 완료 후 권장 호칭을 받아 적정 여부 판단"""
        user_desig = self._desig_combo.currentText()
        user_idx   = _desig_index(user_desig)
        rec_idx    = _desig_index(recommended)

        if rec_idx < 0:
            # 직결 구동 등 비교 불가
            self._adequacy_label.setText("(해당 없음)")
            return

        if user_idx >= rec_idx:
            self._adequacy_label.setText(
                f"✓ 적정  (선정: {user_desig}  /  최소: {recommended})"
            )
            self._adequacy_label.setStyleSheet("color: #a6e3a1;")  # 초록
        else:
            self._adequacy_label.setText(
                f"⚠ 과소 선정  (선정: {user_desig}  /  최소: {recommended} 필요)"
            )
            self._adequacy_label.setStyleSheet("color: #f38ba8;")  # 빨강

        # PCD도 권장 호칭 피치로 재계산
        pitch = CHAIN_PITCH.get(recommended, self._current_pitch())
        z1 = self._z1_spin.value()
        z2 = self._z2_spin.value()
        pcd1 = pitch / math.sin(math.pi / z1)
        pcd2 = pitch / math.sin(math.pi / z2)
        self._pcd1_label.setText(f"{pcd1:.1f}  mm  (Z={z1})")
        self._pcd2_label.setText(f"{pcd2:.1f}  mm  (Z={z2})")

    # ── 외부 인터페이스 ─────────────────────────────────────────────────────
    def chain_type(self) -> str:
        return self._type_combo.currentText()

    def designation(self) -> str:
        return self._desig_combo.currentText()

    def z1(self) -> int:
        return self._z1_spin.value()

    def z2(self) -> int:
        return self._z2_spin.value()

    def pitch_mm(self) -> float:
        return self._current_pitch()
