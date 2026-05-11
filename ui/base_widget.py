import math
from PyQt6.QtWidgets import (
    QWidget, QSplitter, QScrollArea, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QGroupBox, QFormLayout, QLabel,
    QComboBox, QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRunnable, QThreadPool, QObject, pyqtSlot
from PyQt6.QtGui import QKeySequence, QShortcut, QFont

from ui.components.result_card import ResultCard, BearingResultTable
from ui.components.input_group import InputGroup, ComboGroup
from ui.components.bearing_select_group import BearingSelectGroup
from ui.components.chain_sprocket_group import ChainSprocketGroup
from models.input_models import BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from app.config import REDUCER_BRANDS, DIRECT_COUPLING_BRANDS


class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)


class CalculationWorker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            import traceback
            self.signals.error.emit(traceback.format_exc())


class BaseEquipmentWidget(QWidget):
    """모든 장비 위젯의 공통 베이스 클래스

    서브클래스 구현 의무:
      - build_equipment_specs(self) → 장비 사양 GroupBox 반환
      - collect_equipment_input(self) → 장비별 Input 데이터클래스 반환
      - run_calculation(self, inp) → EquipmentResult 반환

    선택적 오버라이드:
      - default_chain_type: str  (기본 "RS", 플로우는 "RF")
      - validate_inputs(self, inp) → list[str]
    """
    calculation_done = pyqtSignal(object)
    default_chain_type: str = "RS"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread_pool = QThreadPool.globalInstance()
        self._setup_ui()

    # ── UI 구축 ────────────────────────────────────────────────────────────
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 왼쪽: 입력 패널
        input_scroll = QScrollArea()
        input_scroll.setWidgetResizable(True)
        input_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        input_container = QWidget()
        self._input_layout = QVBoxLayout(input_container)
        self._input_layout.setSpacing(10)
        self._input_layout.setContentsMargins(4, 4, 4, 4)

        self.build_input_panel()

        self._btn_calc = QPushButton("▶  계산 실행")
        self._btn_calc.setMinimumHeight(40)
        self._btn_calc.clicked.connect(self.on_calculate)
        self._input_layout.addWidget(self._btn_calc)
        self._input_layout.addStretch()

        input_scroll.setWidget(input_container)
        splitter.addWidget(input_scroll)

        # 오른쪽: 결과 패널
        result_scroll = QScrollArea()
        result_scroll.setWidgetResizable(True)
        result_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        result_container = QWidget()
        self._result_layout = QVBoxLayout(result_container)
        self._result_layout.setSpacing(10)
        self._result_layout.setContentsMargins(4, 4, 4, 4)

        self._card_motor   = ResultCard("모터 선정 결과")
        self._card_shaft   = ResultCard("샤프트 설계 결과")
        self._card_reducer = ResultCard("감속기 선정 결과")
        self._card_chain   = ResultCard("체인 / 스프라켓 결과")
        self._bearing_table = BearingResultTable()
        self._notes = QTextEdit()
        self._notes.setObjectName("notes_area")
        self._notes.setReadOnly(True)
        self._notes.setMinimumHeight(160)
        self._notes.setPlaceholderText("계산 노트 및 경고")

        for w in [self._card_motor, self._bearing_table, self._card_shaft,
                  self._card_reducer, self._card_chain, self._notes]:
            self._result_layout.addWidget(w)
        self._result_layout.addStretch()

        result_scroll.setWidget(result_container)
        splitter.addWidget(result_scroll)
        splitter.setSizes([430, 560])

        main_layout.addWidget(splitter)

        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.on_calculate)

    def build_input_panel(self):
        """장비 사양 + 공통 그룹(베어링·샤프트·감속기·체인) 순서로 추가"""
        # 1) 장비 사양 (서브클래스 구현)
        g_equip = self.build_equipment_specs()
        if g_equip:
            self._input_layout.addWidget(g_equip)

        # 2) 베어링 선택
        self._g_bearing = QGroupBox("베어링 선택")
        l_b = QVBoxLayout(self._g_bearing)
        self._bearing_select = BearingSelectGroup()
        l_b.addWidget(self._bearing_select)
        self._input_layout.addWidget(self._g_bearing)

        # 3) 샤프트
        self._g_shaft = QGroupBox("샤프트")
        l_s = QFormLayout(self._g_shaft)
        self._i_shaft_d   = InputGroup("축 직경",  "mm",  10, 500, 60, 0,
                                        "검증에 사용 (0 = 자동 계산만)")
        self._i_shaft_mat = ComboGroup("재질", ["S45C", "SCM440", "SNC836"])
        l_s.addRow(self._i_shaft_d)
        l_s.addRow(self._i_shaft_mat)
        self._input_layout.addWidget(self._g_shaft)

        # 4) 감속기
        self._g_reducer = QGroupBox("감속기")
        l_r = QFormLayout(self._g_reducer)
        self._i_r_brand   = ComboGroup("브랜드",  REDUCER_BRANDS, "효성")
        self._i_r_ratio   = InputGroup("감속비",  "",  1, 200, 20, 1,
                                        "0 입력 시 자동 선정")
        self._i_r_kw      = InputGroup("모터 kW", "kW", 0, 500, 0, 2,
                                        "0 입력 시 자동 선정")
        l_r.addRow(self._i_r_brand)
        l_r.addRow(self._i_r_ratio)
        l_r.addRow(self._i_r_kw)
        self._input_layout.addWidget(self._g_reducer)

        # 5) 체인 / 스프라켓
        self._g_chain = QGroupBox("체인 / 스프라켓")
        l_c = QVBoxLayout(self._g_chain)
        self._chain_group = ChainSprocketGroup(self.default_chain_type)
        l_c.addWidget(self._chain_group)
        self._input_layout.addWidget(self._g_chain)

        # 브랜드 변경 → 체인 그룹 활성/비활성
        self._i_r_brand.currentTextChanged.connect(self._on_brand_changed)

    def _on_brand_changed(self, brand: str):
        is_direct = brand in DIRECT_COUPLING_BRANDS
        self._g_chain.setEnabled(not is_direct)

    # ── 서브클래스 구현 의무 ───────────────────────────────────────────────
    def build_equipment_specs(self) -> QGroupBox:
        """장비 사양 GroupBox 반환 (서브클래스 구현)"""
        raise NotImplementedError

    def collect_equipment_input(self):
        """장비별 입력 데이터 반환 (서브클래스 구현)"""
        raise NotImplementedError

    def run_calculation(self, inp) -> EquipmentResult:
        raise NotImplementedError

    def validate_inputs(self, inp) -> list:
        return []

    # ── 공통 collect helpers ────────────────────────────────────────────────
    def _collect_bearing(self) -> BearingInput:
        return BearingInput(
            shaft_speed_rpm=1450.0,     # 계산 모듈에서 sprocket_rpm으로 덮어씀
            desired_life_hr=self._bearing_select.desired_life_hr(),
            bearing_brand=self._bearing_select.brand(),
            bearing_number=self._bearing_select.number(),
        )

    def _collect_shaft(self) -> ShaftInput:
        return ShaftInput(
            torque_Nm=0.0,              # 계산 모듈에서 덮어씀
            bending_moment_Nm=80.0,     # 기본값
            material=self._i_shaft_mat.current_text(),
            safety_factor=2.0,
            km_factor=1.5,
            kt_factor=1.0,
            user_diameter_mm=self._i_shaft_d.value(),
        )

    def _collect_reducer(self) -> ReducerInput:
        return ReducerInput(
            service_factor=1.5,
            brand=self._i_r_brand.current_text(),
            user_ratio=self._i_r_ratio.value(),
        )

    def _collect_chain(self) -> ChainInput:
        return ChainInput(
            chain_type=self._chain_group.chain_type(),
            num_teeth_small=self._chain_group.z1(),
            num_teeth_large=self._chain_group.z2(),
            center_distance_m=0.5,
        )

    def collect_inputs(self):
        eq = self.collect_equipment_input()
        b  = self._collect_bearing()
        s  = self._collect_shaft()
        r  = self._collect_reducer()
        c  = self._collect_chain()
        return eq, b, s, r, c

    # ── 계산 실행 ──────────────────────────────────────────────────────────
    def on_calculate(self):
        try:
            inp = self.collect_inputs()
        except Exception as e:
            self._notes.setPlainText(f"입력 수집 오류: {e}")
            return

        errors = self.validate_inputs(inp)
        if errors:
            self._notes.setPlainText("\n".join(errors))
            return

        self._btn_calc.setEnabled(False)
        self._btn_calc.setText("⏳ 계산 중...")

        worker = CalculationWorker(self.run_calculation, inp)
        worker.signals.finished.connect(self._on_done)
        worker.signals.error.connect(self._on_error)
        self._thread_pool.start(worker)

    @pyqtSlot(object)
    def _on_done(self, result: EquipmentResult):
        self._btn_calc.setEnabled(True)
        self._btn_calc.setText("▶  계산 실행")
        self.update_results(result)
        self.calculation_done.emit(result)

    @pyqtSlot(str)
    def _on_error(self, msg: str):
        self._btn_calc.setEnabled(True)
        self._btn_calc.setText("▶  계산 실행")
        self._notes.setPlainText(f"계산 오류:\n{msg}")

    # ── 결과 표시 ──────────────────────────────────────────────────────────
    def update_results(self, r: EquipmentResult):
        m = r.motor
        self._card_motor.clear_rows()
        self._card_motor.set_row("필요 동력",       f"{m.required_power_kW:.3f}", "kW")
        self._card_motor.set_row("선정 모터",        f"{m.selected_motor_kW}", "kW")
        self._card_motor.set_row("모터 모델",        m.motor_model)
        self._card_motor.set_row("IEC 프레임",       m.iec_frame)
        self._card_motor.set_row("정격 회전수",      f"{m.rated_rpm}", "rpm")
        self._card_motor.set_row("정격 전류 (400V)", f"{m.rated_current_A}", "A")
        self._card_motor.set_row("정격 토크",        f"{m.rated_torque_Nm}", "N·m")
        self._card_motor.set_row("효율",             f"{m.efficiency_pct}", "%")
        self._card_motor.set_row("샤프트 직경",      f"{m.shaft_dia_mm}", "mm")

        self._bearing_table.update(r.bearing_drive, r.bearing_driven)

        s = r.shaft
        self._card_shaft.clear_rows()
        self._card_shaft.set_row("계산 최소 직경", f"{s.required_diameter_mm:.2f}", "mm")
        self._card_shaft.set_row("KS 선정 직경",   f"{s.selected_diameter_mm:.0f}", "mm")
        self._card_shaft.set_row("Von Mises 응력", f"{s.von_mises_stress_MPa:.2f}", "MPa")
        self._card_shaft.set_row("허용 응력",       f"{s.allowable_stress_MPa:.2f}", "MPa")
        self._card_shaft.set_row("실제 안전계수",   f"{s.safety_factor_actual:.2f}")
        self._card_shaft.set_row("재질",            s.material)

        rd = r.reducer
        self._card_reducer.clear_rows()
        self._card_reducer.set_row("모델",    rd.model)
        self._card_reducer.set_row("감속비",  f"{rd.ratio:.2f}")
        self._card_reducer.set_row("입력 토크", f"{rd.input_torque_Nm:.1f}", "N·m")
        self._card_reducer.set_row("출력 토크", f"{rd.output_torque_Nm:.1f}", "N·m")
        self._card_reducer.set_row("효율",     f"{rd.efficiency_pct}", "%")

        ch = r.chain
        self._card_chain.clear_rows()
        if ch.chain_designation == "직결":
            self._card_chain.set_row("구동 방식", "직결 구동 (체인 없음)")
        elif ch.chain_designation:
            self._card_chain.set_row("체인 호칭",   ch.chain_designation)
            self._card_chain.set_row("피치",         f"{ch.chain_pitch_mm:.3f}", "mm")
            pcd1 = ch.sprocket_dia_drive_mm
            pcd2 = ch.sprocket_dia_driven_mm
            self._card_chain.set_row("소 스프로켓",
                f"Z={ch.drive_sprocket_teeth}  PCD={pcd1:.1f} mm")
            self._card_chain.set_row("대 스프로켓",
                f"Z={ch.driven_sprocket_teeth}  PCD={pcd2:.1f} mm")
            self._card_chain.set_row("감속비",       f"{ch.actual_ratio:.3f}")
            self._card_chain.set_row("체인 속도",    f"{ch.chain_speed_mpm:.1f}", "m/min")
            self._card_chain.set_row("링크 수",      f"{ch.chain_length_links}", "링크")
            # 체인 호칭을 ChainSprocketGroup에도 업데이트
            if hasattr(self, "_chain_group"):
                self._chain_group.update_designation(ch.chain_designation)
        else:
            self._card_chain.set_row("체인", "—")

        notes = r.calculation_notes
        self._notes.setPlainText("\n".join(notes) if notes else "✓ 계산 완료 — 경고 없음")
