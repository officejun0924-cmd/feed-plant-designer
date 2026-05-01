from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import FlowConveyorInput, BearingInput, ShaftInput, ReducerInput, VBeltInput
import equipment.flow_conveyor as calc_module


class FlowConveyorWidget(BaseEquipmentWidget):

    def build_input_panel(self):
        g1 = QGroupBox("장비 사양")
        l1 = QFormLayout(g1)
        self.i_capacity  = InputGroup("처리량",              "ton/hr", 0.1,  500,  80)
        self.i_length    = InputGroup("Conveyor 길이",       "m",      1,    200,  15)
        self.i_incline   = InputGroup("경사각",              "°",      0,    90,   0, 1)
        self.i_height    = InputGroup("수직 높이 (경사 시)", "m",      0,    50,   0)
        self.i_chain_v   = InputGroup("Chain 속도",          "m/min",  5,    50,   28)
        self.i_density   = InputGroup("재료 비중 γ",         "t/m³",   0.1,  3.0,  0.7, 2)
        self.i_fill      = InputGroup("충만효율 φ",          "",       0.3,  0.9,  0.65, 2)
        self.i_E         = InputGroup("상수 E (표3-7)",      "",       1.0,  10.0, 3.9, 1)
        self.i_eta       = InputGroup("전동 효율 η",         "",       0.5,  1.0,  0.85, 2)
        self.i_sf        = InputGroup("안전계수",            "",       1.0,  3.0,  1.2, 2)
        for w in [self.i_capacity, self.i_length, self.i_incline, self.i_height,
                  self.i_chain_v, self.i_density, self.i_fill, self.i_E, self.i_eta, self.i_sf]:
            l1.addRow(w)
        self._input_layout.addWidget(g1)

        g2 = QGroupBox("베어링 계산 조건")
        l2 = QFormLayout(g2)
        self.i_b_radial = InputGroup("반경 하중 Fr", "N",   100, 500000, 6000)
        self.i_b_axial  = InputGroup("축 하중 Fa",   "N",   0,   200000, 0)
        self.i_b_life   = InputGroup("요구 수명",    "hr",  1000, 100000, 25000)
        self.i_b_type   = ComboGroup("베어링 타입",
                                     ["deep_groove_ball", "spherical_roller", "cylindrical_roller"])
        self.i_b_rel    = ComboGroup("신뢰도",       ["90", "95", "97", "99"], "90")
        for w in [self.i_b_radial, self.i_b_axial, self.i_b_life, self.i_b_type, self.i_b_rel]:
            l2.addRow(w)
        self._input_layout.addWidget(g2)

        g3 = QGroupBox("샤프트 설계")
        l3 = QFormLayout(g3)
        self.i_s_bend = InputGroup("굽힘 모멘트 M", "N·m", 0, 100000, 100)
        self.i_s_mat  = ComboGroup("재질", ["S45C", "SCM440", "SNC836"])
        self.i_s_sf   = InputGroup("안전계수",       "",   1.0, 5.0, 2.0, 1)
        self.i_s_km   = InputGroup("굽힘 충격계수 Km","",  1.0, 3.0, 1.5, 1)
        self.i_s_kt   = InputGroup("비틀림 충격계수 Kt","", 1.0, 3.0, 1.0, 1)
        for w in [self.i_s_bend, self.i_s_mat, self.i_s_sf, self.i_s_km, self.i_s_kt]:
            l3.addRow(w)
        self._input_layout.addWidget(g3)

        g4 = QGroupBox("감속기 / V벨트")
        l4 = QFormLayout(g4)
        self.i_r_sf  = InputGroup("서비스계수",     "",  1.0, 3.0, 1.5, 1)
        self.i_v_cen = InputGroup("V벨트 중심거리", "m", 0.1, 3.0, 0.5, 2)
        self.i_v_sec = ComboGroup("V벨트 단면",    ["auto", "A", "B", "C", "D"])
        for w in [self.i_r_sf, self.i_v_cen, self.i_v_sec]:
            l4.addRow(w)
        self._input_layout.addWidget(g4)

    def collect_inputs(self):
        eq = FlowConveyorInput(
            capacity_tph=self.i_capacity.value(),
            conveyor_length_m=self.i_length.value(),
            inclination_deg=self.i_incline.value(),
            height_m=self.i_height.value(),
            chain_speed_mpm=self.i_chain_v.value(),
            material_density=self.i_density.value(),
            fill_ratio=self.i_fill.value(),
            E_constant=self.i_E.value(),
            drive_efficiency=self.i_eta.value(),
            safety_factor=self.i_sf.value(),
        )
        b = BearingInput(
            radial_load_N=self.i_b_radial.value(),
            axial_load_N=self.i_b_axial.value(),
            shaft_speed_rpm=23,
            desired_life_hr=self.i_b_life.value(),
            bearing_type=self.i_b_type.current_text(),
            reliability=float(self.i_b_rel.current_text()),
        )
        s = ShaftInput(
            torque_Nm=0,
            bending_moment_Nm=self.i_s_bend.value(),
            material=self.i_s_mat.current_text(),
            safety_factor=self.i_s_sf.value(),
            km_factor=self.i_s_km.value(),
            kt_factor=self.i_s_kt.value(),
        )
        r = ReducerInput(service_factor=self.i_r_sf.value())
        v = VBeltInput(center_distance_m=self.i_v_cen.value(),
                       section=self.i_v_sec.current_text())
        return eq, b, s, r, v

    def validate_inputs(self, inp) -> list:
        eq, *_ = inp
        errors = []
        if eq.capacity_tph <= 0:
            errors.append("처리량은 0 초과이어야 합니다.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, v = inp
        return calc_module.calculate(eq, b, s, r, v)
