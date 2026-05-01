import json
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QMenuBar, QMenu, QToolBar,
    QStatusBar, QFileDialog, QMessageBox,
)
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtCore import Qt

from app.config import APP_NAME, APP_VERSION
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.resize(1100, 780)
        self._last_result = None
        self._setup_ui()

    def _setup_ui(self):
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_tabs()
        self._setup_statusbar()

    def _setup_menubar(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("파일(&F)")
        act_new   = QAction("새 계산(&N)", self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(self._on_new)
        file_menu.addAction(act_new)
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

        act_calc = QAction("▶ 계산", self)
        act_calc.setToolTip("현재 탭 계산 (Ctrl+Enter)")
        act_calc.triggered.connect(self._run_current_tab)
        tb.addAction(act_calc)

        tb.addSeparator()

        act_pdf = QAction("PDF", self)
        act_pdf.triggered.connect(self._on_export_pdf)
        tb.addAction(act_pdf)

        act_excel = QAction("Excel", self)
        act_excel.triggered.connect(self._on_export_excel)
        tb.addAction(act_excel)

    def _setup_tabs(self):
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        self._w_screw        = ScrewConveyorWidget()
        self._w_bucket       = BucketElevatorWidget()
        self._w_mixer        = MixerPelletizerWidget()
        self._w_grinder      = GrinderHammerMillWidget()
        self._w_fan          = FanBlowerWidget()
        self._w_belt         = BeltConveyorWidget()
        self._w_flow         = FlowConveyorWidget()
        self._w_drag         = DragConveyorWidget()
        self._w_bag_filter   = BagFilterWidget()
        self._w_cyclone      = CycloneWidget()
        self._w_rotary_valve = RotaryValveWidget()
        self._w_sieve        = SieveWidget()

        for w, label in [
            (self._w_screw,        "스크류 컨베이어"),
            (self._w_bucket,       "버킷 엘리베이터"),
            (self._w_belt,         "벨트 컨베이어"),
            (self._w_flow,         "플로우 컨베이어"),
            (self._w_drag,         "드래그 컨베이어"),
            (self._w_mixer,        "믹서/펠레타이저"),
            (self._w_grinder,      "분쇄기/해머밀"),
            (self._w_fan,          "팬/블로어"),
            (self._w_bag_filter,   "백 필터"),
            (self._w_cyclone,      "사이클론"),
            (self._w_rotary_valve, "로터리 밸브"),
            (self._w_sieve,        "체 (Sieve)"),
        ]:
            self._tabs.addTab(w, label)
            w.calculation_done.connect(self._on_result)

        self.setCentralWidget(self._tabs)

    def _setup_statusbar(self):
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("준비")

    def _current_widget(self):
        return self._tabs.currentWidget()

    def _run_current_tab(self):
        w = self._current_widget()
        if hasattr(w, "on_calculate"):
            w.on_calculate()

    def _on_result(self, result):
        self._last_result = result
        ts = datetime.now().strftime("%H:%M:%S")
        self._status.showMessage(f"✓ {result.equipment_type} 계산 완료  [{ts}]")

    def _on_new(self):
        pass  # 향후: 입력값 초기화

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
            "<b>혼합/분쇄:</b> 믹서/펠레타이저, 해머밀, 팬/블로어<br><br>"
            "계산 항목: 모터 용량, 베어링 수명 (ISO 281),<br>"
            "샤프트 설계 (ASME), V벨트 선정 (KS B 1400)"
        )
