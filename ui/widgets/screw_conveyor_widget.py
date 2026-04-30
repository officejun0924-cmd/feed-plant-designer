from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import (
    ScrewConveyorInput, BearingInput, ShaftInput, ReducerInput, VBeltInput,
)
import equipment.screw_conveyor as calc_module


class ScrewConveyorWidget(BaseEquipmentWidget):

    def build_input_panel(self):
        # 장비 사양
        g1 = QGroupBox("장비 사양")
        l1 = QFormLayout(g1)
        self.i_capacity    = InputGroup("처리량",        "ton/hr", 0.1, 500, 20)
        self.i_density     = InputGroup("재료 밀도",      "kg/m³",  100, 2000, 600)
        self.i_diameter    = InputGroup("스크류 직경",    "m",      0.1, 1.0,  0.3, 3)
        self.i_pitch       = InputGroup("피치",          "m",      0.05, 1.0, 0.3, 3)
        self.i_speed       = InputGroup("회전수",        "rpm",    10,  200,  50)
        self.i_length      = InputGroup("이송 길이",     "m",      1,   100,  10)
        self.i_inclination = InputGroup("경사각",        "°",      0,   45,   0, 1)
        self.i_mat_factor  = InputGroup("재료 계수 Cf",  "",       0.5, 5.0,  1.4, 2)
        self.i_friction    = InputGroup("마찰계수 f",    "",       0.01, 0.2, 0.05, 3)
        self.i_fill        = InputGroup("충전율",        "",       0.1, 0.6,  0.45, 2)
        self.i_eta         = InputGroup("전동 효율 η",   "",       0.5, 1.0,  0.90, 2)
        self.i_sf_eq       = InputGroup("안전계수",      "",       1.0, 3.0,  1.25, 2)
        for w in [self.i_capacity, self.i_density, self.i_diameter, self.i_pitch,
                  self.i_speed, self.i_length, self.i_inclination, self.i_mat_factor,
                  self.i_friction, self.i_fill, self.i_eta, self.i_sf_eq]:
            l1.addRow(w)
        self._input_layout.addWidget(g1)

        # 베어링 조건
        g2 = QGroupBox("베어링 계산 조건")
        l2 = QFormLayout(g2)
        self.i_b_radial    = InputGroup("반경 하중 Fr",  "N",     100, 500000, 5000)
        self.i_b_axial     = InputGroup("축 하중 Fa",   "N",     0,   200000, 0)
        self.i_b_life      = InputGroup("요구 수명",    "hr",    1000, 100000, 25000)
        self.i_b_type      = ComboGroup("베어링 타입",
                                        ["deep_groove_ball", "spherical_roller", "cylindrical_roller"])
        self.i_b_rel       = ComboGroup("신뢰도",       ["90", "95", "97", "99"], "90")
        for w in [self.i_b_radial, self.i_b_axial, self.i_b_life, self.i_b_type, self.i_b_rel]:
            l2.addRow(w)
        self._input_layout.addWidget(g2)

        # 샤프트
        g3 = QGroupBox("샤프트 설계")
        l3 = QFormLayout(g3)
        self.i_s_bending   = InputGroup("굽힘 모멘트 M", "N·m",  0, 50000, 80)
        self.i_s_material  = ComboGroup("재질", ["S45C", "SCM440", "SNC836"])
        self.i_s_sf        = InputGroup("안전계수",       "",     1.0, 5.0, 2.0, 1)
        self.i_s_km        = InputGroup("굽힘 충격계수 Km","",   1.0, 3.0, 1.5, 1)
        self.i_s_kt        = InputGroup("비틀림 충격계수 Kt","", 1.0, 3.0, 1.0, 1)
        for w in [self.i_s_bending, self.i_s_material, self.i_s_sf, self.i_s_km, self.i_s_kt]:
            l3.addRow(w)
        self._input_layout.addWidget(g3)

        # 감속기/V벨트
        g4 = QGroupBox("감속기 / V벨트")
        l4 = QFormLayout(g4)
        self.i_r_sf        = InputGroup("서비스계수",    "",      1.0, 3.0, 1.5, 1)
        self.i_v_center    = InputGroup("V벨트 중심거리", "m",    0.1, 3.0, 0.5, 2)
        self.i_v_section   = ComboGroup("V벨트 단면",   ["auto", "A", "B", "C", "D"])
        for w in [self.i_r_sf, self.i_v_center, self.i_v_section]:
            l4.addRow(w)
        self._input_layout.addWidget(g4)

    def collect_inputs(self):
        eq = ScrewConveyorInput(
            capacity_tph=self.i_capacity.value(),
            material_density=self.i_density.value(),
            screw_diameter_m=self.i_diameter.value(),
            screw_pitch_m=self.i_pitch.value(),
            screw_speed_rpm=self.i_speed.value(),
            length_m=self.i_length.value(),
            inclination_deg=self.i_inclination.value(),
            material_factor=self.i_mat_factor.value(),
            friction_factor=self.i_friction.value(),
            fill_ratio=self.i_fill.value(),
            drive_efficiency=self.i_eta.value(),
            safety_factor=self.i_sf_eq.value(),
        )
        b = BearingInput(
            radial_load_N=self.i_b_radial.value(),
            axial_load_N=self.i_b_axial.value(),
            shaft_speed_rpm=eq.screw_speed_rpm,
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
        if eq.capacity_tph <= 0:
            errors.append("처리량은 0 초과이어야 합니다.")
        if eq.inclination_deg > 45:
            errors.append("스크류 경사각은 45° 이하로 설정하세요.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, v = inp
        return calc_module.calculate(eq, b, s, r, v)
