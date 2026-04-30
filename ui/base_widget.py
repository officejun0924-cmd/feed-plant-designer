from PyQt6.QtWidgets import (
    QWidget, QSplitter, QScrollArea, QVBoxLayout, QPushButton,
    QTextEdit, QSizePolicy, QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRunnable, QThreadPool, QObject, QMetaObject, Q_ARG, pyqtSlot
from PyQt6.QtGui import QKeySequence, QShortcut

from ui.components.result_card import ResultCard, BearingResultTable
from models.result_models import EquipmentResult


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
    calculation_done = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread_pool = QThreadPool.globalInstance()
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 왼쪽 입력 패널
        input_scroll = QScrollArea()
        input_scroll.setWidgetResizable(True)
        input_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        input_container = QWidget()
        self._input_layout = QVBoxLayout(input_container)
        self._input_layout.setSpacing(10)
        self._input_layout.setContentsMargins(4, 4, 4, 4)

        self.build_input_panel()

        # 계산 버튼
        self._btn_calc = QPushButton("▶  계산 실행")
        self._btn_calc.setMinimumHeight(40)
        self._btn_calc.clicked.connect(self.on_calculate)
        self._input_layout.addWidget(self._btn_calc)
        self._input_layout.addStretch()

        input_scroll.setWidget(input_container)
        splitter.addWidget(input_scroll)

        # 오른쪽 결과 패널
        result_scroll = QScrollArea()
        result_scroll.setWidgetResizable(True)
        result_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        result_container = QWidget()
        self._result_layout = QVBoxLayout(result_container)
        self._result_layout.setSpacing(10)
        self._result_layout.setContentsMargins(4, 4, 4, 4)

        self._card_motor = ResultCard("모터 선정 결과")
        self._card_shaft = ResultCard("샤프트 설계 결과")
        self._card_reducer = ResultCard("감속기 선정 결과")
        self._card_vbelt = ResultCard("V벨트 선정 결과")
        self._bearing_table = BearingResultTable()
        self._notes = QTextEdit()
        self._notes.setObjectName("notes_area")
        self._notes.setReadOnly(True)
        self._notes.setMaximumHeight(120)
        self._notes.setPlaceholderText("계산 경고 및 메모")

        for w in [self._card_motor, self._bearing_table,
                  self._card_shaft, self._card_reducer,
                  self._card_vbelt, self._notes]:
            self._result_layout.addWidget(w)
        self._result_layout.addStretch()

        result_scroll.setWidget(result_container)
        splitter.addWidget(result_scroll)
        splitter.setSizes([420, 560])

        main_layout.addWidget(splitter)

        # Ctrl+Enter 단축키
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.on_calculate)

    def build_input_panel(self):
        """서브클래스에서 구현: self._input_layout 에 GroupBox 추가"""
        raise NotImplementedError

    def collect_inputs(self):
        """서브클래스에서 구현: 입력값 수집 → dataclass 반환"""
        raise NotImplementedError

    def run_calculation(self, inp) -> EquipmentResult:
        """서브클래스에서 구현: 계산 실행"""
        raise NotImplementedError

    def validate_inputs(self, inp) -> list:
        return []

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

    def update_results(self, r: EquipmentResult):
        m = r.motor
        self._card_motor.set_row("필요 동력", f"{m.required_power_kW:.3f}", "kW")
        self._card_motor.set_row("선정 모터 용량", f"{m.selected_motor_kW}", "kW")
        self._card_motor.set_row("모터 모델", m.motor_model)
        self._card_motor.set_row("IEC 프레임", m.iec_frame)
        self._card_motor.set_row("정격 회전수", f"{m.rated_rpm}", "rpm")
        self._card_motor.set_row("정격 전류 (400V)", f"{m.rated_current_A}", "A")
        self._card_motor.set_row("정격 토크", f"{m.rated_torque_Nm}", "N·m")
        self._card_motor.set_row("효율", f"{m.efficiency_pct}", "%")
        self._card_motor.set_row("샤프트 직경", f"{m.shaft_dia_mm}", "mm")

        self._bearing_table.update(r.bearing_drive, r.bearing_driven)

        s = r.shaft
        self._card_shaft.set_row("계산 직경", f"{s.required_diameter_mm:.2f}", "mm")
        self._card_shaft.set_row("선정 직경 (KS)", f"{s.selected_diameter_mm:.0f}", "mm")
        self._card_shaft.set_row("Von Mises 응력", f"{s.von_mises_stress_MPa:.2f}", "MPa")
        self._card_shaft.set_row("허용 응력", f"{s.allowable_stress_MPa:.2f}", "MPa")
        self._card_shaft.set_row("실제 안전계수", f"{s.safety_factor_actual:.2f}")
        self._card_shaft.set_row("재질", s.material)

        rd = r.reducer
        self._card_reducer.set_row("감속비", f"{rd.ratio:.2f}")
        self._card_reducer.set_row("모델", rd.model)
        self._card_reducer.set_row("입력 토크", f"{rd.input_torque_Nm:.1f}", "N·m")
        self._card_reducer.set_row("출력 토크", f"{rd.output_torque_Nm:.1f}", "N·m")
        self._card_reducer.set_row("효율", f"{rd.efficiency_pct}", "%")

        vb = r.vbelt
        self._card_vbelt.set_row("벨트 단면", vb.section)
        self._card_vbelt.set_row("벨트 호칭", vb.belt_length_designation)
        self._card_vbelt.set_row("벨트 길이", f"{vb.belt_length_mm:.0f}", "mm")
        self._card_vbelt.set_row("벨트 수량", f"{vb.number_of_belts}", "개")
        self._card_vbelt.set_row("구동 풀리 직경", f"{vb.drive_pulley_dia_mm:.0f}", "mm")
        self._card_vbelt.set_row("피동 풀리 직경", f"{vb.driven_pulley_dia_mm:.0f}", "mm")
        self._card_vbelt.set_row("실제 감속비", f"{vb.actual_ratio:.3f}")
        self._card_vbelt.set_row("접촉각", f"{vb.contact_angle_deg:.1f}", "°")

        notes = r.calculation_notes
        self._notes.setPlainText("\n".join(notes) if notes else "✓ 계산 완료 — 경고 없음")
