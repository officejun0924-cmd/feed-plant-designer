"""기계 선택 화면 — 12종 장비 카드 그리드"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

EQUIPMENT_LIST = [
    ("스크류 컨베이어",   "screw",        "나선형 스크류로 분체·입상물 수평 이송"),
    ("버킷 엘리베이터",  "bucket",       "버킷으로 분체를 수직 상승 이송"),
    ("벨트 컨베이어",    "belt",         "고무 벨트로 원료 수평·경사 이송"),
    ("플로우 컨베이어",  "flow",         "RF체인·플라이트로 분체 수평 이송"),
    ("드래그 컨베이어",  "drag",         "RS/RF체인·비행판으로 원료 이송"),
    ("믹서 / 펄버라이저","mixer",        "패들 믹서·펠레타이저 동력 계산"),
    ("분쇄기 / 해머밀",  "grinder",      "Bond 분쇄 법칙 기반 해머밀 동력"),
    ("팬 / 블로어",      "fan",          "압력 상승·풍량 기반 팬 동력 계산"),
    ("백 필터",          "bag_filter",   "필터 면적·백 수·팬 동력 계산"),
    ("사이클론",         "cyclone",      "표10-2 비율로 사이클론 치수 설계"),
    ("로타리밸브",       "rotary_valve", "회전속도·형상으로 용량 계산"),
    ("시브 (Sieve)",     "sieve",        "표14-1 K계수 기반 체 처리 능력"),
]


class EquipmentSelectScreen(QWidget):
    equipment_selected = pyqtSignal(str)   # equipment key
    back_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 16, 24, 16)

        # ── 헤더 ───────────────────────────────────────────────────────────
        header = QHBoxLayout()
        btn_back = QPushButton("←  홈으로")
        btn_back.setFixedWidth(110)
        btn_back.clicked.connect(self.back_clicked)

        title = QLabel("기계 선택하기")
        f = QFont(); f.setPointSize(16); f.setBold(True)
        title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header.addWidget(btn_back)
        header.addStretch()
        header.addWidget(title)
        header.addStretch()
        header.addSpacing(110)   # btn_back 폭만큼 오른쪽 여백
        layout.addLayout(header)

        # ── 장비 그리드 ─────────────────────────────────────────────────────
        grid = QGridLayout()
        grid.setSpacing(14)

        for idx, (name, key, desc) in enumerate(EQUIPMENT_LIST):
            btn = QPushButton(f"  {name}\n  {desc}")
            btn.setObjectName("equip_card_btn")
            btn.setMinimumSize(210, 78)
            btn.setCheckable(False)
            btn.clicked.connect(lambda _, k=key: self.equipment_selected.emit(k))
            grid.addWidget(btn, idx // 3, idx % 3)

        layout.addLayout(grid)
        layout.addStretch()
