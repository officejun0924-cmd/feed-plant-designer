from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import ScrewConveyorInput
from app.config import MATERIAL_DB
import equipment.screw_conveyor as calc_module


class ScrewConveyorWidget(BaseEquipmentWidget):

    def build_equipment_specs(self) -> QGroupBox:
        g = QGroupBox("장비 사양 — 스크류 컨베이어")
        l = QFormLayout(g)

        material_keys = list(MATERIAL_DB.keys())
        self.i_material   = ComboGroup("원재료",         material_keys, "직접 입력")
        self.i_sg         = InputGroup("비중 γ",         "t/m³",  0.1, 3.0,  0.65, 3)
        self.i_mat_factor = InputGroup("재료 상수 C",    "",      0.5, 5.0,  1.2,  2,
                                        "사료류 ≈ 1.2, 분체류 ≈ 1.5~4.0")
        self.i_capacity   = InputGroup("운반 용량 Qt",   "ton/hr",0.1, 500,  20)
        self.i_diameter   = InputGroup("스크류 외경 D",  "m",     0.1, 1.0,  0.3,  3)
        self.i_shaft_od   = InputGroup("샤프트 외경 d",  "m",     0.02,0.5,  0.089,3,
                                        "D×0.3 정도 기준")
        self.i_pitch      = InputGroup("피치 P",         "m",     0.05,1.0,  0.3,  3)
        self.i_speed      = InputGroup("회전수 N",       "rpm",   10,  500,  100)
        self.i_length     = InputGroup("이송 길이 ℓ",    "m",     1,   100,  6)
        self.i_incline    = InputGroup("경사각",         "°",     0,   45,   0, 1)
        self.i_fill       = InputGroup("충만효율 Φ",     "",      0.1, 1.0,  0.45, 2)

        for w in [self.i_material, self.i_sg, self.i_mat_factor, self.i_capacity,
                  self.i_diameter, self.i_shaft_od, self.i_pitch, self.i_speed,
                  self.i_length, self.i_incline, self.i_fill]:
            l.addRow(w)

        self.i_material.currentTextChanged.connect(self._on_material_changed)
        return g

    def _on_material_changed(self, name: str):
        data = MATERIAL_DB.get(name, {})
        if data:
            self.i_sg.set_value(data.get("specific_gravity", 0.65))
            self.i_mat_factor.set_value(data.get("material_factor", 1.4))

    def collect_equipment_input(self):
        return ScrewConveyorInput(
            capacity_tph=self.i_capacity.value(),
            specific_gravity=self.i_sg.value(),
            material_name=self.i_material.current_text(),
            screw_diameter_m=self.i_diameter.value(),
            shaft_outer_diameter_m=self.i_shaft_od.value(),
            screw_pitch_m=self.i_pitch.value(),
            screw_speed_rpm=self.i_speed.value(),
            length_m=self.i_length.value(),
            inclination_deg=self.i_incline.value(),
            material_factor=self.i_mat_factor.value(),
            fill_efficiency=self.i_fill.value(),
        )

    def validate_inputs(self, inp) -> list:
        eq, *_ = inp
        errors = []
        if eq.capacity_tph <= 0:
            errors.append("운반 용량은 0 초과이어야 합니다.")
        if eq.inclination_deg > 45:
            errors.append("스크류 경사각은 45° 이하로 설정하세요.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
