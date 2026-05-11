import json
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QMenuBar, QMenu, QToolBar,
    QStatusBar, QFileDialog, QMessageBox,
)
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtCore import Qt

from app.config import APP_NAME, APP_VERSION
from ui.home_screen import HomeScreen
from ui.equipment_select_screen import EquipmentSelectScreen
from ui.formula_screen import FormulaScreen

from ui.widgets.screw_conveyor_widget import ScrewConveyorWidget
from ui.widgets.bucket_elevator_widget import BucketElevatorWidget
from ui.widgets.mixer_pelletizer_widget import MixerPelletizerWidget
from ui.widgets.grinder_hammer_mill_widget import GrinderHammerMillWidget
from ui.widgets.fan_blower_widget import FanBlowerWidget
from ui.widgets.belt_conveyor_widget import BeltConveyorWidget
from ui.widgets.flow_conveyor_widget import FlowConveyorWidget
from ui.widgets.drag_conveyor_widget import DragConveyorWidget
from ui.widgets.bag_filter_widget import BagFilterWidget
from ui.widgets.cyclone_widget import CycloneWidget
from ui.widgets.rotary_valve_widget import RotaryValveWidget
from ui.widgets.sieve_widget import SieveWidget

# ── 장비 키 → (위젯 클래스, 탭 라벨) ──────────────────────────────────────
EQUIPMENT_MAP = {
    "screw":        (ScrewConveyorWidget,      "스크류 컨베이어"),
    "bucket":       (BucketElevatorWidget,     "버킷 엘리베이터"),
    "belt":         (BeltConveyorWidget,       "벨트 컨베이어"),
    "flow":         (FlowConveyorWidget,       "플로우 컨베이어"),
    "drag":         (DragConveyorWidget,       "드래그 컨베이어"),
    "mixer":        (MixerPelletizerWidget,    "믹서/펄버라이저"),
    "grinder":      (GrinderHammerMillWidget,  "분쇄기/해머밀"),
    "fan":          (FanBlowerWidget,          "팬/블로어"),
    "bag_filter":   (BagFilterWidget,          "백 필터"),
    "cyclone":      (CycloneWidget,            "사이클론"),
    "rotary_valve": (RotaryValveWidget,        "로터리밸브"),
    "sieve":        (SieveWidget,              "시브 (Sieve)"),
}

# 화면 인덱스
PAGE_HOME    = 0
PAGE_EQUIP   = 1
PAGE_FORMULA = 2
PAGE_CALC    = 3   # 장비 계산 화면 (단일 교체)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.resize(1200, 820)
        self._last_result = None
        self._current_widget = None
        self._setup_ui()

    def _setup_ui(self):
        self._setup_menubar()
        self._setup_toolbar()

        # ── QStackedWidget ─────────────────────────────────────────────────
        self._stack = QStackedWidget()

        # 0. 홈 화면
        self._home = HomeScreen()
        self._home.machine_select_clicked.connect(self._show_equip_select)
        self._home.formula_select_clicked.connect(self._show_formula)
        self._stack.addWidget(self._home)             # idx 0

        # 1. 장비 선택 화면
        self._equip_select = EquipmentSelectScreen()
        self._equip_select.equipment_selected.connect(self._open_equipment)
        self._equip_select.back_clicked.connect(self._show_home)
        self._stack.addWidget(self._equip_select)     # idx 1

        # 2. 계산식 선택 화면
        self._formula = FormulaScreen()
        self._formula.back_clicked.connect(self._show_home)
        self._stack.addWidget(self._formula)          # idx 2

        # 3. 장비 계산 화면 (플레이스홀더 — 실제 위젯은 동적 교체)
        from PyQt6.QtWidgets import QWidget
        self._calc_placeholder = QWidget()
        self._stack.addWidget(self._calc_placeholder) # idx 3

        self.setCentralWidget(self._stack)
        self._setup_statusbar()
        self._show_home()

    def _setup_menubar(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("파일(&F)")
        act_home  = QAction("홈으로(&H)", self)
        act_home.setShortcut(QKeySequence("Ctrl+Home"))
        act_home.triggered.connect(self._show_home)
        file_menu.addAction(act_home)
        file_menu.addSeparator()
        act_exit  = QAction("종료(&Q)", self)
        act_exit.setShortcut(QKeySequence("Alt+F4"))
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        report_menu = mb.addMenu("보고서(&R)")
        act_pdf   = QAction("PDF 내보내기(&P)", self)
        act_pdf.setShortcut(QKeySequence("Ctrl+P"))
        act_pdf.triggered.connect(self._on_export_pdf)
        report_menu.addAction(act_pdf)
        act_excel = QAction("Excel 내보내기(&E)", self)
        act_excel.setShortcut(QKeySequence("Ctrl+E"))
        act_excel.triggered.connect(self._on_export_excel)
        report_menu.addAction(act_excel)

        help_menu = mb.addMenu("도움말(&H)")
        act_about = QAction("프로그램 정보(&A)", self)
        act_about.triggered.connect(self._on_about)
        help_menu.addAction(act_about)

    def _setup_toolbar(self):
        tb = QToolBar("주 도구모음")
        tb.setMovable(False)
        self.addToolBar(tb)

        act_home = QAction("🏠 홈", self)
        act_home.setToolTip("홈 화면으로")
        act_home.triggered.connect(self._show_home)
        tb.addAction(act_home)

        tb.addSeparator()

        act_calc = QAction("▶ 계산", self)
        act_calc.setToolTip("현재 장비 계산 실행 (Ctrl+Enter)")
        act_calc.triggered.connect(self._run_current_calc)
        tb.addAction(act_calc)

        tb.addSeparator()

        act_pdf = QAction("PDF", self)
        act_pdf.triggered.connect(self._on_export_pdf)
        tb.addAction(act_pdf)

        act_excel = QAction("Excel", self)
        act_excel.triggered.connect(self._on_export_excel)
        tb.addAction(act_excel)

    def _setup_statusbar(self):
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("홈 화면 — 기계 또는 계산식을 선택하세요")

    # ── 화면 전환 ──────────────────────────────────────────────────────────
    def _show_home(self):
        self._stack.setCurrentIndex(PAGE_HOME)
        self._status.showMessage("홈 화면 — 기계 또는 계산식을 선택하세요")

    def _show_equip_select(self):
        self._stack.setCurrentIndex(PAGE_EQUIP)
        self._status.showMessage("계산할 기계를 선택하세요")

    def _show_formula(self):
        self._stack.setCurrentIndex(PAGE_FORMULA)
        self._status.showMessage("핸드북 계산식 참조")

    def _open_equipment(self, key: str):
        cls, label = EQUIPMENT_MAP.get(key, (None, ""))
        if cls is None:
            return

        # 기존 위젯 교체
        if self._current_widget:
            old = self._stack.widget(PAGE_CALC)
            self._stack.removeWidget(old)
            old.deleteLater()

        widget = cls()
        widget.calculation_done.connect(self._on_result)
        self._stack.insertWidget(PAGE_CALC, widget)
        self._current_widget = widget
        self._stack.setCurrentIndex(PAGE_CALC)
        self.setWindowTitle(f"{APP_NAME}  —  {label}")
        self._status.showMessage(f"[{label}]  입력값을 설정하고 계산 실행 (Ctrl+Enter)")

    def _run_current_calc(self):
        if self._current_widget and hasattr(self._current_widget, "on_calculate"):
            self._current_widget.on_calculate()

    def _on_result(self, result):
        self._last_result = result
        ts = datetime.now().strftime("%H:%M:%S")
        self._status.showMessage(f"✓ {result.equipment_type} 계산 완료  [{ts}]")

    # ── 보고서 ─────────────────────────────────────────────────────────────
    def _on_export_pdf(self):
        if not self._last_result:
            QMessageBox.information(self, "안내", "먼저 계산을 실행하세요.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "PDF 저장", f"설계계산서_{datetime.now():%Y%m%d_%H%M}.pdf",
            "PDF 파일 (*.pdf)"
        )
        if path:
            try:
                from reports.pdf_generator import generate_pdf
                generate_pdf(self._last_result, path)
                QMessageBox.information(self, "완료", f"PDF 저장 완료:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "오류", str(e))

    def _on_export_excel(self):
        if not self._last_result:
            QMessageBox.information(self, "안내", "먼저 계산을 실행하세요.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Excel 저장", f"설계계산서_{datetime.now():%Y%m%d_%H%M}.xlsx",
            "Excel 파일 (*.xlsx)"
        )
        if path:
            try:
                from reports.excel_generator import generate_excel
                generate_excel(self._last_result, path)
                QMessageBox.information(self, "완료", f"Excel 저장 완료:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "오류", str(e))

    def _on_about(self):
        QMessageBox.about(
            self, f"{APP_NAME}",
            f"<b>{APP_NAME}</b><br>"
            f"버전: {APP_VERSION}<br><br>"
            "KS/ISO 기준 설계 공식 + SKF·NSK·FAG DB<br><br>"
            "<b>컨베이어:</b> 스크류·벨트·플로우·드래그 컨베이어, 버킷 엘리베이터<br>"
            "<b>분리/집진:</b> 백 필터, 사이클론, 체(Sieve), 로터리 밸브<br>"
            "<b>혼합/분쇄:</b> 믹서/펄버라이저, 해머밀, 팬/블로어<br><br>"
            "계산 항목: 모터 용량, 베어링 수명 (ISO 281),<br>"
            "샤프트 설계 (ASME), 체인/스프라켓 선정 (KS B 1407)"
        )
