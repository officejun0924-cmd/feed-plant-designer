from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import GrinderHammerMillInput, BearingInput, ShaftInput, ReducerInput, VBeltInput
import equipment.grinder_hammer_mill as calc_module


class GrinderHammerMillWidget(BaseEquipmentWidget):

    def build_input_panel(self):
        g1 = QGroupBox("장비 사양")
        l1 = QFormLayout(g1)
        self.i_capacity   = InputGroup("처리량",          "ton/hr", 0.1, 200,  5)
        self.i_wi         = InputGroup("Bond 작업지수 Wi", "kWh/t", 1,  50,   12, 1,
                                       "곡류 사료: 10~15, 대두박: 12~18, 석회석: 12~14")
        self.i_feed_size  = InputGroup("공급 입도 F80",   "mm",    1,  200,  10)
        self.i_prod_size  = InputGroup("제품 입도 P80",   "mm",    0.1, 50,   1, 2)
        self.i_rotor_d    = InputGroup("로터 직경",       "m",     0.2, 2.0,  0.6, 2)
        self.i_rotor_rpm  = InputGroup("로터 회전수",     "rpm",   500, 6000, 3000)
        self.i_eta        = InputGroup("전동 효율 η",     "",      0.5, 1.0,  0.90, 2)
        self.i_sf         = InputGroup("안전계수",        "",      1.0, 3.0,  1.35, 2)
        for w in [self.i_capacity, self.i_wi, self.i_feed_size, self.i_prod_size,
                  self.i_rotor_d, self.i_rotor_rpm, self.i_eta, self.i_sf]:
            l1.addRow(w)
        self._input_layout.addWidget(g1)

        g2 = QGroupBox("베어링 계산 조건")
        l2 = QFormLayout(g2)
        self.i_b_radial = InputGroup("반경 하중 Fr", "N",  100, 500000, 10000)
        self.i_b_axial  = InputGroup("축 하중 Fa",  "N",  0,   200000, 0)
        self.i_b_life   = InputGroup("요구 수명",   "hr", 1000, 100000, 20000)
        self.i_b_type   = ComboGroup("베어링 타입",
                                     ["deep_groove_ball", "spherical_roller", "cylindrical_roller"])
        self.i_b_rel    = ComboGroup("신뢰도", ["90", "95", "97", "99"], "90")
        for w in [self.i_b_radial, self.i_b_axial, self.i_b_life, self.i_b_type, self.i_b_rel]:
            l2.addRow(w)
        self._input_layout.addWidget(g2)

        g3 = QGroupBox("샤프트 설계")
        l3 = QFormLayout(g3)
        self.i_s_bending  = InputGroup("굽힘 모멘트 M", "N·m", 0, 100000, 50)
        self.i_s_material = ComboGroup("재질", ["SCM440", "S45C", "SNC836"])
        self.i_s_sf       = InputGroup("안전계수",       "",    1.0, 5.0, 2.5, 1)
        self.i_s_km       = InputGroup("굽힘 충격계수 Km","",  1.5, 3.0, 2.0, 1)
        self.i_s_kt       = InputGroup("비틀림 충격계수 Kt","",1.0, 3.0, 1.5, 1)
        for w in [self.i_s_bending, self.i_s_material, self.i_s_sf, self.i_s_km, self.i_s_kt]:
            l3.addRow(w)
        self._input_layout.addWidget(g3)

        g4 = QGroupBox("감속기 / V벨트")
        l4 = QFormLayout(g4)
        self.i_r_sf      = InputGroup("서비스계수",    "", 1.0, 3.0, 1.75, 1)
        self.i_v_center  = InputGroup("V벨트 중심거리", "m", 0.1, 3.0, 0.6, 2)
        self.i_v_section = ComboGroup("V벨트 단면", ["auto", "B", "C", "D", "A"])
        for w in [self.i_r_sf, self.i_v_center, self.i_v_section]:
            l4.addRow(w)
        self._input_layout.addWidget(g4)

    def collect_inputs(self):
        eq = GrinderHammerMillInput(
            capacity_tph=self.i_capacity.value(),
            material_hardness=self.i_wi.value(),
            feed_size_mm=self.i_feed_size.value(),
            product_size_mm=self.i_prod_size.value(),
            rotor_diameter_m=self.i_rotor_d.value(),
            rotor_speed_rpm=self.i_rotor_rpm.value(),
            drive_efficiency=self.i_eta.value(),
            safety_factor=self.i_sf.value(),
        )
        b = BearingInput(
            radial_load_N=self.i_b_radial.value(),
            axial_load_N=self.i_b_axial.value(),
            shaft_speed_rpm=eq.rotor_speed_rpm,
            desired_life_hr=self.i_b_life.value(),
            bearing_type=self.i_b_type.current_text(),
            reliability=float(self.i_b_rel.current_text()),
        )
        s = ShaftInput(
            torque_Nm=0,
            bending_moment_Nm=self.i_s_bending.value(),
            material=self.i_s_material.current_text(),
            safety_factor=self.i_s_sf.value(),
            km_factor=self.i_s_km.value(),
            kt_factor=self.i_s_kt.value(),
        )
        r = ReducerInput(service_factor=self.i_r_sf.value())
        v = VBeltInput(center_distance_m=self.i_v_center.value(),
                       section=self.i_v_section.current_text())
        return eq, b, s, r, v

    def validate_inputs(self, inp) -> list:
        eq, b, s, r, v = inp
        errors = []
        if eq.product_size_mm >= eq.feed_size_mm:
            errors.append("제품 입도(P80)는 공급 입도(F80)보다 작아야 합니다.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, v = inp
        return calc_module.calculate(eq, b, s, r, v)
