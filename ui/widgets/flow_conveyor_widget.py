from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import FlowConveyorInput
import equipment.flow_conveyor as calc_module
from app.config import MATERIAL_DB


class FlowConveyorWidget(BaseEquipmentWidget):
    default_chain_type = "RF"

    def build_equipment_specs(self) -> QGroupBox:
        g = QGroupBox("장비 사양 — 플로우 컨베이어")
        l = QFormLayout(g)

        material_keys = list(MATERIAL_DB.keys())
        self.i_material = ComboGroup("원재료",             material_keys, "직접 입력")
        self.i_capacity = InputGroup("설계 운반량 Qt",     "ton/hr", 0.1,  500,  80)
        self.i_length   = InputGroup("Conveyor 길이 L",    "m",      1,    200,  15)
        self.i_incline  = InputGroup("경사각",             "°",      0,    90,   0, 1)
        self.i_height   = InputGroup("수직 높이 (경사 시)","m",      0,    50,   0)
        self.i_chain_v  = InputGroup("Chain 속도 V",       "m/min",  5,    50,   28)
        self.i_trough_w = InputGroup("트로프 폭 B",        "m",      0.1,  2.0,  0.50, 2)
        self.i_trough_h = InputGroup("트로프 높이 H",      "m",      0.05, 1.0,  0.25, 2)
        self.i_fill     = InputGroup("충만효율 φ",         "",       0.3,  0.9,  0.65, 2)
        self.i_density  = InputGroup("재료 비중 γ",        "t/m³",   0.1,  3.0,  0.7,  2)
        self.i_E        = InputGroup("상수 E (표3-7)",     "",       1.0,  10.0, 3.9,  1)

        for w in [self.i_material, self.i_capacity, self.i_length, self.i_incline,
                  self.i_height, self.i_chain_v, self.i_trough_w, self.i_trough_h,
                  self.i_fill, self.i_density, self.i_E]:
            l.addRow(w)

        self.i_material.currentTextChanged.connect(self._on_material_changed)
        return g

    def _on_material_changed(self, name: str):
        data = MATERIAL_DB.get(name, {})
        if data:
            self.i_density.set_value(data.get("specific_gravity", 0.65))

    def collect_equipment_input(self):
        s = self._collect_shaft()
        return FlowConveyorInput(
            capacity_tph=self.i_capacity.value(),
            conveyor_length_m=self.i_length.value(),
            inclination_deg=self.i_incline.value(),
            height_m=self.i_height.value(),
            chain_speed_mpm=self.i_chain_v.value(),
            trough_width_m=self.i_trough_w.value(),
            trough_height_m=self.i_trough_h.value(),
            fill_efficiency=self.i_fill.value(),
            specific_gravity=self.i_density.value(),
            E_constant=self.i_E.value(),
            shaft_diameter_mm=s.user_diameter_mm,
        )

    def validate_inputs(self, inp) -> list:
        eq, *_ = inp
        errors = []
        if eq.capacity_tph <= 0:
            errors.append("처리량은 0 초과이어야 합니다.")
        if eq.trough_width_m <= 0 or eq.trough_height_m <= 0:
            errors.append("트로프 폭/높이는 0 초과이어야 합니다.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
