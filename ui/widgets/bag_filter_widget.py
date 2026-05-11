from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup
from models.input_models import BagFilterInput
import equipment.bag_filter as calc_module


class BagFilterWidget(BaseEquipmentWidget):

    def build_equipment_specs(self) -> QGroupBox:
        g = QGroupBox("백필터 설계 조건")
        l = QFormLayout(g)

        self.i_air_vol  = InputGroup("처리 풍량 Qa",      "m³/min", 10,   5000, 380)
        self.i_filt_vel = InputGroup("여과속도 V",         "m/min",  0.5,  5.0,  1.8, 2,
                                      "충격분출식: 1.5~4.3 m/min")
        self.i_bag_d    = InputGroup("여과포 직경 D",      "m",      0.05, 0.30, 0.15, 3)
        self.i_bag_h    = InputGroup("여과포 높이 H",      "m",      1.0,  6.0,  2.5, 1)
        self.i_dp       = InputGroup("시스템 압력손실 ΔP", "Pa",     100,  5000, 1500, 0)
        self.i_fan_eta  = InputGroup("Fan 효율 η_fan",    "",       0.5,  1.0,  0.75, 2)

        for w in [self.i_air_vol, self.i_filt_vel, self.i_bag_d, self.i_bag_h,
                  self.i_dp, self.i_fan_eta]:
            l.addRow(w)
        return g

    def collect_equipment_input(self):
        return BagFilterInput(
            air_volume_m3min=self.i_air_vol.value(),
            filter_velocity_mmin=self.i_filt_vel.value(),
            bag_diameter_m=self.i_bag_d.value(),
            bag_height_m=self.i_bag_h.value(),
            static_pressure_pa=self.i_dp.value(),
            fan_efficiency=self.i_fan_eta.value(),
        )

    def validate_inputs(self, inp) -> list:
        eq, *_ = inp
        errors = []
        if eq.air_volume_m3min <= 0:
            errors.append("처리 풍량은 0 초과이어야 합니다.")
        if eq.filter_velocity_mmin <= 0:
            errors.append("여과속도는 0 초과이어야 합니다.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
