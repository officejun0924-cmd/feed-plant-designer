"""계산식 선택 화면 — 핸드북 공식 참조"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget,
    QTextEdit, QPushButton, QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# 공식 이름 → 장비 키 매핑 (main_window EQUIPMENT_MAP 키와 동일해야 함)
FORMULA_TO_EQUIP_KEY = {
    "스크류 컨베이어 (Ch.KS B 6852)":        "screw",
    "버킷 엘리베이터":                        "bucket",
    "벨트 컨베이어 (핸드북 Ch.1 표1-9/1-10)": "belt",
    "플로우 컨베이어 (핸드북 Ch.3)":           "flow",
    "드래그 컨베이어 (핸드북 Ch.4 표4-2)":     "drag",
    "믹서 / 펠레타이저 (Newton 교반)":         "mixer",
    "분쇄기 / 해머밀 (Bond 분쇄 법칙)":        "grinder",
    "팬 / 블로어":                            "fan",
    "백 필터 (핸드북 Ch.8/9)":                "bag_filter",
    "사이클론 (핸드북 Ch.10 표10-2)":          "cyclone",
    "로타리밸브 (핸드북 Ch.11 표11-1)":        "rotary_valve",
    "시브 — 체 (핸드북 Ch.14 표14-1)":         "sieve",
}

FORMULAS = {
    "스크류 컨베이어 (Ch.KS B 6852)": """
■ 운반 용량
  Qt = 47.1 × Φ × (D² - d²) × P × N × γ  [T/hr]
  D = 스크류 외경(m), d = 샤프트 외경(m), P = 피치(m)
  N = 회전수(rpm), Φ = 충만효율, γ = 비중(t/m³)

■ 필요 회전수
  N_req = 4 × Qt / (60 × Φ × π × D² × P × γ)  [rpm]

■ 소요 동력
  H [HP] = (C × Qt × ℓ + Qt × h) / 270 × Sf
  C = 재료 상수, ℓ = 이송 길이(m), h = 수직 높이(m)
  P_kW = H × 0.7457 / η

■ 비틀림 모멘트
  T = 71620 × H / N  [kg·cm]

■ 추력
  F = H × 4500 / V  [kg],  V = P × N  [m/min]
""",

    "버킷 엘리베이터": """
■ 소요 동력
  P = Q × H / (367 × η)  [kW]
  Q = 운반량(T/hr), H = 양정(m), η = 전동효율

■ 이론 운반량
  Qt_theory = 3600 × v × (Vb / s) × γ × φ  [T/hr]
  v = 벨트속도(m/s), Vb = 버킷용적(L), s = 버킷간격(m)
  γ = 비중(t/m³), φ = 충만율

■ 버킷 속도
  v = 버킷 선속 (m/s), 통상 1.0~2.0 m/s

■ Sprocket 회전수
  n = 60 × v / (π × D_sprocket)  [rpm]
""",

    "벨트 컨베이어 (핸드북 Ch.1 표1-9/1-10)": """
■ 무부하 동력
  P1 = 0.06 × f × W × v × (l + l0) / 367  [kW]
  W = 운동부 중량(kg/m), f = 회전저항계수, l0 = 보정항

■ 수평 부하 동력
  P2 = f × Qt × (l + l0) / 367  [kW]

■ 수직 동력
  P3 = ±h × Qt / 367  [kW]  (+경사 상승, -경사 하강)

■ 총 동력
  Pm = (P1 + P2 + P3) / η × Sf

■ 표1-9 (f, l0 선택)
  보통 Roller: f=0.03,  l0=49
  양호 Roller: f=0.022, l0=66
  내림 Conveyor: f=0.012, l0=156

■ 표1-10 Belt 폭별 W (kg/m) — 자동 조회
""",

    "플로우 컨베이어 (핸드북 Ch.3)": """
■ 수평 동력 성분
  H1 = E × L × Qt / 367  [HP]
  E = 핸드북 상수 (사료 ≈ 3.9, 분체 ≈ 5.0~6.0)
  L = 수평 거리(m), Qt = 운반량(T/hr)

■ 수직 동력 성분
  H2 = h × Qt / 367  [HP]
  h = 수직 높이(m)

■ 총 소요 동력
  H_total = H1 + H2  [HP]
  P_kW = H_total × 0.7457 / η × Sf

■ 이론 운반량
  Qt_theory = 60 × A × V × γ × φ  [T/hr]
  A = B × H_trough [m²], V = 체인속도(m/min)

■ 체인: RF S형 롤러 체인 사용 (표준)
""",

    "드래그 컨베이어 (핸드북 Ch.4 표4-2)": """
■ 배출구 보정 계수
  N_coef = 1.2 + 0.3 × N_outlet

■ 수평 동력
  H = Qt × F × L × N_coef / (300 × E)  [HP]
  F = 마찰계수 (표4-2), L = 수평 길이(m)
  E = 기계효율

■ 경사 동력
  H = Qt × N_coef × (F × L + H_vert) / (300 × E)  [HP]

■ 소요 동력
  P_kW = H × 0.7457 / η × Sf

■ 이론 운반량
  Qt_theory = 60 × B × H_trough × V × γ × φ  [T/hr]

■ 운반물 1m당 중량
  W = 16.7 × Qt / V  [kg/m]
""",

    "믹서 / 펠레타이저 (Newton 교반)": """
■ 교반 동력
  P = Np × ρ × n³ × D⁵  [W]
  Np = Newton 파워 넘버 (패들 ≈ 0.3~0.5)
  ρ = 재료 밀도(kg/m³), n = 회전속도(rps)
  D = 패들 직경(m)

■ 소요 동력
  P_req = P / η × Sf
""",

    "분쇄기 / 해머밀 (Bond 분쇄 법칙)": """
■ Bond 분쇄 법칙
  W = Wi × (10/√P80 - 10/√F80)  [kWh/t]
  Wi = Bond 작업지수 (곡물 ≈ 10~15 kWh/t)
  P80 = 제품 80% 통과 입경(μm)
  F80 = 공급 80% 통과 입경(μm)

■ 소요 동력
  P_req = W × Qt / η × Sf  [kW]

■ 로터 팁 속도
  v_tip = π × D_rotor × n / 60  [m/s]  (권장 60~120 m/s)
""",

    "팬 / 블로어": """
■ 공기 동력
  P_air = Q × ΔP / 1000  [kW]
  Q = 풍량(m³/s), ΔP = 정압 상승(Pa)

■ 축 동력
  P_shaft = P_air / η_fan  [kW]

■ 소요 동력
  P_req = P_shaft / η_drive × Sf  [kW]

■ 비속도
  ns = n × √Q / ΔP^(3/4)
""",

    "백 필터 (핸드북 Ch.8/9)": """
■ 필터 면적
  A = Qa / V_filter  [m²]
  Qa = 처리 풍량(m³/min), V_filter = 여과 속도(m/min)

■ 필요 백 수
  N_bags = A / (π × D_bag × L_bag)  [개]

■ 팬 동력
  P_fan = Qa × ΔP / (60,000 × η)  [kW]

■ 권장 여과속도
  건식: 1.0~2.0 m/min, 습식: 0.5~1.0 m/min
""",

    "사이클론 (핸드북 Ch.10 표10-2)": """
■ 처리 면적
  A_inlet = Qa / (Va × 60)  [m²]
  Qa = 풍량(m³/hr), Va = 입구 속도(m/s)

■ 표10-2 치수 비율
  D = 사이클론 직경, H = 총 높이 = 4D
  입구: a = D/2, b = D/4
  출구관: De = D/2, H_e = D/2

■ 압력 손실
  ΔP = ξ × ρ × v_inlet² / 2  [Pa]
  ξ ≈ 8 (표준 사이클론)
""",

    "로타리밸브 (핸드북 Ch.11 표11-1)": """
■ 이론 처리 용량
  Q = 0.7 × W × (1 - X) × N × 60 × γ  [T/hr]
  W = 셀 용적(L), X = 충만손실계수 (≈0.15)
  N = 회전수(rpm), γ = 비중(t/m³)

■ 소요 동력
  H [HP] = K × D³ × L × N / 1000
  K = 형상계수 (표11-1), D = 로터 직경(m), L = 로터 길이(m)

■ 차압 고려
  P_seal = ΔP × A_inlet × v_leakage  [추가 동력]
""",

    "시브 — 체 (핸드북 Ch.14 표14-1)": """
■ 기본 처리 능력
  Q_basic = k × l × m × n × o × p × ρ' × a × q  [T/hr]
  표14-1: k=기준용량계수, l=보정계수 (입경비)
  m=비중계수, n=습도계수, o=효율계수
  p=경사계수, ρ' = 비중, a = 체 면적(m²)
  q = 해당 채 번호 처리량

■ 필요 체 면적
  A_req = Qt / Q_unit  [m²]
  Qt = 설계 처리량(T/hr)
""",
}


class FormulaScreen(QWidget):
    back_clicked = pyqtSignal()
    equipment_selected = pyqtSignal(str)   # 장비 키 (EQUIPMENT_MAP 키)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 12, 16, 12)

        # 헤더
        header = QHBoxLayout()
        btn_back = QPushButton("←  홈으로")
        btn_back.setFixedWidth(110)
        btn_back.clicked.connect(self.back_clicked)

        title = QLabel("계산식 선택하기")
        f = QFont(); f.setPointSize(16); f.setBold(True)
        title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._btn_go = QPushButton("▶  이 장비 계산하러 가기")
        self._btn_go.setFixedWidth(220)
        self._btn_go.clicked.connect(self._go_to_equipment)

        header.addWidget(btn_back)
        header.addStretch()
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._btn_go)
        layout.addLayout(header)

        # 스플리터: 왼쪽 목록 / 오른쪽 공식
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._list = QListWidget()
        self._list.addItems(list(FORMULAS.keys()))
        self._list.setMaximumWidth(280)
        self._list.currentTextChanged.connect(self._show_formula)
        self._list.doubleClicked.connect(self._go_to_equipment)  # 더블클릭도 지원

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setObjectName("notes_area")
        f2 = QFont("Consolas", 11)
        self._text.setFont(f2)

        splitter.addWidget(self._list)
        splitter.addWidget(self._text)
        splitter.setSizes([280, 700])

        layout.addWidget(splitter)

        # 첫 항목 선택
        if self._list.count():
            self._list.setCurrentRow(0)

    def _show_formula(self, text: str):
        content = FORMULAS.get(text, "")
        self._text.setPlainText(content.strip())
        # 해당 장비가 있으면 버튼 활성화
        key = FORMULA_TO_EQUIP_KEY.get(text, "")
        self._btn_go.setEnabled(bool(key))

    def _go_to_equipment(self):
        current_text = self._list.currentItem()
        if current_text is None:
            return
        key = FORMULA_TO_EQUIP_KEY.get(current_text.text(), "")
        if key:
            self.equipment_selected.emit(key)
