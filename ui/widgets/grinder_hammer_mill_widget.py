from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup
from models.input_models import GrinderHammerMillInput
import equipment.grinder_hammer_mill as calc_module


class GrinderHammerMillWidget(BaseEquipmentWidget):

    def build_equipment_specs(self) -> QGroupBox:
        g = QGroupBox("장비 사양 — 분쇄기 / 해머밀")
        l = QFormLayout(g)

        self.i_capacity  = InputGroup("처리량",           "ton/hr", 0.1, 200,  5)
        self.i_wi        = InputGroup("Bond 작업지수 Wi", "kWh/t",  1,   50,   12, 1,
                                       "곡류 사료: 10~15, 대두박: 12~18, 석회석: 12~14")
        self.i_feed_size = InputGroup("공급 입도 F80",    "mm",     1,   200,  10)
        self.i_prod_size = InputGroup("제품 입도 P80",    "mm",     0.1, 50,   1, 2)
        self.i_rotor_d   = InputGroup("로터 직경",        "m",      0.2, 2.0,  0.6, 2)
        self.i_rotor_rpm = InputGroup("로터 회전수",      "rpm",    500, 6000, 3000)

        for w in [self.i_capacity, self.i_wi, self.i_feed_size, self.i_prod_size,
                  self.i_rotor_d, self.i_rotor_rpm]:
            l.addRow(w)
        return g

    def collect_equipment_input(self):
        return GrinderHammerMillInput(
            capacity_tph=self.i_capacity.value(),
            material_hardness=self.i_wi.value(),
            feed_size_mm=self.i_feed_size.value(),
            product_size_mm=self.i_prod_size.value(),
            rotor_diameter_m=self.i_rotor_d.value(),
            rotor_speed_rpm=self.i_rotor_rpm.value(),
        )

    def validate_inputs(self, inp) -> list:
        eq, *_ = inp
        errors = []
        if eq.product_size_mm >= eq.feed_size_mm:
            errors.append("제품 입도(P80)는 공급 입도(F80)보다 작아야 합니다.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
