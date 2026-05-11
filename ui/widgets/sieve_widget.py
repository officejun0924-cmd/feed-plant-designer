from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup
from models.input_models import SieveInput
from app.config import MATERIAL_DB
import equipment.sieve as calc_module


class SieveWidget(BaseEquipmentWidget):

    def build_equipment_specs(self) -> QGroupBox:
        g = QGroupBox("체 (Sieve) 사양")
        l = QFormLayout(g)

        self.i_capacity = InputGroup("목표 처리량",     "ton/hr", 0.1, 500,  50)
        self.i_opening  = InputGroup("체 구멍 크기",    "mm",     0.1, 100,  3.0, 2,
                                      "표14-1: 0.16~100 mm")
        self.i_area     = InputGroup("체 면적",         "m²",     0.5, 50,   4.0, 1)
        self.i_density  = InputGroup("외관상 비중 ρ'",  "t/m³",   0.1, 2.0,  0.65, 2)
        self.i_incline  = InputGroup("경사각 β",        "°",      5,   45,   15, 0,
                                      "일반 10~20°, 분리 중시 5~10°")
        self.i_k        = InputGroup("k — 입도 분포",   "", 0.1, 2.0, 1.0, 2)
        self.i_l        = InputGroup("l — 입자 형상",   "", 0.1, 2.0, 1.0, 2)
        self.i_m        = InputGroup("m — 수분",        "", 0.1, 2.0, 1.0, 2)
        self.i_n        = InputGroup("n — 입자 밀도",   "", 0.1, 2.0, 1.0, 2)
        self.i_o        = InputGroup("o — 부착성",      "", 0.1, 2.0, 1.0, 2)
        self.i_p        = InputGroup("p — 공급 균일도", "", 0.1, 2.0, 1.0, 2)

        for w in [self.i_capacity, self.i_opening, self.i_area, self.i_density,
                  self.i_incline, self.i_k, self.i_l, self.i_m, self.i_n, self.i_o, self.i_p]:
            l.addRow(w)
        return g

    def collect_equipment_input(self):
        return SieveInput(
            capacity_tph=self.i_capacity.value(),
            sieve_opening_mm=self.i_opening.value(),
            sieve_area_m2=self.i_area.value(),
            material_density=self.i_density.value(),
            inclination_deg=self.i_incline.value(),
            k_factor=self.i_k.value(),
            l_factor=self.i_l.value(),
            m_factor=self.i_m.value(),
            n_factor=self.i_n.value(),
            o_factor=self.i_o.value(),
            p_factor=self.i_p.value(),
        )

    def validate_inputs(self, inp) -> list:
        eq, *_ = inp
        errors = []
        if eq.capacity_tph <= 0:
            errors.append("처리량은 0 초과이어야 합니다.")
        if eq.sieve_area_m2 <= 0:
            errors.append("체 면적은 0 초과이어야 합니다.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
