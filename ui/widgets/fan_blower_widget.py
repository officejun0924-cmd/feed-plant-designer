from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup
from models.input_models import FanBlowerInput
import equipment.fan_blower as calc_module


class FanBlowerWidget(BaseEquipmentWidget):

    def build_equipment_specs(self) -> QGroupBox:
        g = QGroupBox("장비 사양 — 팬 / 블로어")
        l = QFormLayout(g)

        self.i_flow    = InputGroup("풍량",          "m³/hr",  100, 200000, 5000)
        self.i_pressure= InputGroup("정압 ΔP",       "Pa",     100, 30000,  1500)
        self.i_density = InputGroup("공기 밀도",     "kg/m³",  0.8, 2.0,    1.2, 3)
        self.i_fan_eta = InputGroup("팬 효율 η_fan", "",       0.4, 0.95,   0.75, 2)
        self.i_fan_rpm = InputGroup("팬 회전수",     "rpm",    100, 5000,   1450)

        for w in [self.i_flow, self.i_pressure, self.i_density, self.i_fan_eta, self.i_fan_rpm]:
            l.addRow(w)
        return g

    def collect_equipment_input(self):
        return FanBlowerInput(
            flow_rate_m3h=self.i_flow.value(),
            static_pressure_pa=self.i_pressure.value(),
            air_density=self.i_density.value(),
            fan_efficiency=self.i_fan_eta.value(),
        )

    def validate_inputs(self, inp) -> list:
        eq, *_ = inp
        errors = []
        if eq.flow_rate_m3h <= 0:
            errors.append("풍량은 0 초과이어야 합니다.")
        if eq.static_pressure_pa <= 0:
            errors.append("정압은 0 초과이어야 합니다.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
