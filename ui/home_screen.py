"""홈 화면 — 기계 선택하기 / 계산식 선택하기"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class HomeScreen(QWidget):
    machine_select_clicked = pyqtSignal()
    formula_select_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── 가운데 카드 컨테이너 ─────────────────────────────────────────────
        card = QWidget()
        card.setObjectName("home_card")
        card.setFixedWidth(680)
        layout = QVBoxLayout(card)
        layout.setSpacing(32)
        layout.setContentsMargins(48, 56, 48, 56)

        # 제목
        title = QLabel("사료플랜트 기계 설계 계산 프로그램")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont()
        f.setPointSize(20)
        f.setBold(True)
        title.setFont(f)
        title.setObjectName("home_title")

        # 부제
        sub = QLabel("KS / ISO 기준  ·  핸드북 공식  ·  DB 자동 선정")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setObjectName("home_subtitle")

        # 버튼
        btn_row = QHBoxLayout()
        btn_row.setSpacing(24)

        self.btn_machine = QPushButton("⚙   기계 선택하기")
        self.btn_machine.setObjectName("home_btn")
        self.btn_machine.setMinimumSize(240, 90)
        self.btn_machine.clicked.connect(self.machine_select_clicked)

        self.btn_formula = QPushButton("📐   계산식 선택하기")
        self.btn_formula.setObjectName("home_btn")
        self.btn_formula.setMinimumSize(240, 90)
        self.btn_formula.clicked.connect(self.formula_select_clicked)

        btn_row.addStretch()
        btn_row.addWidget(self.btn_machine)
        btn_row.addWidget(self.btn_formula)
        btn_row.addStretch()

        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addLayout(btn_row)

        outer.addStretch(2)
        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        outer.addStretch(3)
