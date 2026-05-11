from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import CycloneInput
import equipment.cyclone as calc_module


class CycloneWidget(BaseEquipmentWidget):

    def build_equipment_specs(self) -> QGroupBox:
        g = QGroupBox("사이클론 설계 조건")
        l = QFormLayout(g)

        self.i_air_vol = InputGroup("처리 풍량 Qa",    "m³/min", 10,   5000, 380)
        self.i_inlet_v = InputGroup("유입 풍속 Va",     "m/sec",  7,    18,   18, 1,
                                     "최적 15~18 m/sec")
        self.i_lambda  = InputGroup("압력손실계수 λ",  "",       5,    25,   12, 0,
                                     "일반 Cyclone ≈ 12, 고효율 ≈ 8")
        self.i_type    = ComboGroup("Cyclone 형식",    ["일반", "고효율", "고용량"])
        self.i_fan_eta = InputGroup("Fan 효율 η_fan", "",       0.5,  1.0,  0.72, 2)

        for w in [self.i_air_vol, self.i_inlet_v, self.i_lambda, self.i_type, self.i_fan_eta]:
            l.addRow(w)
        return g

    def collect_equipment_input(self):
        return CycloneInput(
            air_volume_m3min=self.i_air_vol.value(),
            inlet_velocity_msec=self.i_inlet_v.value(),
            pressure_loss_coef=self.i_lambda.value(),
            cyclone_type=self.i_type.current_text(),
            fan_efficiency=self.i_fan_eta.value(),
        )

    def validate_inputs(self, inp) -> list:
        eq, *_ = inp
        errors = []
        if eq.air_volume_m3min <= 0:
            errors.append("처리 풍량은 0 초과이어야 합니다.")
        if eq.inlet_velocity_msec < 7:
            errors.append("유입 풍속은 7 m/sec 이상이어야 합니다.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
