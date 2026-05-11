from PyQt6.QtWidgets import QGroupBox, QFormLayout, QCheckBox
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import BeltConveyorInput
from app.config import MATERIAL_DB
import equipment.belt_conveyor as calc_module


class BeltConveyorWidget(BaseEquipmentWidget):

    def build_equipment_specs(self) -> QGroupBox:
        g = QGroupBox("장비 사양 — 벨트 컨베이어")
        l = QFormLayout(g)

        material_keys = list(MATERIAL_DB.keys())
        self.i_material = ComboGroup("원재료",              material_keys, "직접 입력")
        self.i_capacity = InputGroup("처리량",              "ton/hr", 0.1, 500,  80)
        self.i_density  = InputGroup("재료 겉보기 비중 ρ", "t/m³",   0.1, 2.0,  0.65, 2)
        self.i_width    = InputGroup("Belt 폭 B",           "mm",     400, 2200, 600, 0,
                                      "표준: 400/500/600/750/900/1000/1200/1400/1600 mm")
        self.i_speed    = InputGroup("Belt 속도 v",         "m/min",  5,   180,  60)
        self.i_length   = InputGroup("수평 길이 l",         "m",      1,   500,  20)
        self.i_incline  = InputGroup("경사각",              "°",      0,   30,   0, 1)
        self.i_roller   = ComboGroup("Roller 조건 (표1-9)", ["양호", "보통", "내림"], "양호")

        self.chk_auto_W = QCheckBox("W 자동 (표1-10)")
        self.chk_auto_W.setChecked(True)
        self.chk_auto_W.toggled.connect(self._on_auto_W_toggled)
        self.i_W = InputGroup("W 수동 입력", "kg/m", 10, 300, 35.5)
        self.i_W.setEnabled(False)

        for w in [self.i_material, self.i_capacity, self.i_density, self.i_width,
                  self.i_speed, self.i_length, self.i_incline, self.i_roller]:
            l.addRow(w)
        l.addRow("", self.chk_auto_W)
        l.addRow(self.i_W)

        self.i_material.currentTextChanged.connect(self._on_material_changed)
        return g

    def _on_material_changed(self, name: str):
        data = MATERIAL_DB.get(name, {})
        if data:
            self.i_density.set_value(data.get("specific_gravity", 0.65))

    def _on_auto_W_toggled(self, checked: bool):
        self.i_W.setEnabled(not checked)

    def collect_equipment_input(self):
        return BeltConveyorInput(
            capacity_tph=self.i_capacity.value(),
            belt_width_mm=self.i_width.value(),
            belt_speed_mpm=self.i_speed.value(),
            conveyor_length_m=self.i_length.value(),
            inclination_deg=self.i_incline.value(),
            material_density=self.i_density.value(),
            roller_condition=self.i_roller.current_text(),
            auto_W=self.chk_auto_W.isChecked(),
            moving_parts_W=self.i_W.value(),
        )

    def validate_inputs(self, inp) -> list:
        eq, *_ = inp
        errors = []
        if eq.capacity_tph <= 0:
            errors.append("처리량은 0 초과이어야 합니다.")
        if eq.inclination_deg > 30:
            errors.append("Belt Conveyor 경사각은 30° 이하로 설정하세요.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
