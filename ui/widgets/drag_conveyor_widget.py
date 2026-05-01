from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import DragConveyorInput, BearingInput, ShaftInput, ReducerInput, VBeltInput
import equipment.drag_conveyor as calc_module


class DragConveyorWidget(BaseEquipmentWidget):

    def build_input_panel(self):
        g1 = QGroupBox("장비 사양")
        l1 = QFormLayout(g1)
        self.i_capacity = InputGroup("처리량",           "ton/hr", 0.1, 500,  50)
        self.i_length   = InputGroup("수평 길이 L",      "m",      1,   200,  10)
        self.i_height   = InputGroup("수직 높이 H",      "m",      0,   50,   0)
        self.i_outlets  = InputGroup("배출구 수 N",      "개",     1,   10,   1, 0)
        self.i_F        = InputGroup("마찰계수 F (표4-2)","",      0.3, 1.0,  0.55, 2)
        self.i_E_mech   = InputGroup("기계효율 E",       "",       0.5, 1.0,  0.85, 2)
        self.i_eta      = InputGroup("전동 효율 η",      "",       0.5, 1.0,  0.90, 2)
        self.i_sf       = InputGroup("안전계수",         "",       1.0, 3.0,  1.25, 2)
        for w in [self.i_capacity, self.i_length, self.i_height,
                  self.i_outlets, self.i_F, self.i_E_mech, self.i_eta, self.i_sf]:
            l1.addRow(w)
        self._input_layout.addWidget(g1)

        g2 = QGroupBox("베어링 계산 조건")
        l2 = QFormLayout(g2)
        self.i_b_radial = InputGroup("반경 하중 Fr", "N",   100, 500000, 5000)
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
        self.i_s_bend = InputGroup("굽힘 모멘트 M", "N·m", 0, 100000, 80)
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
        eq = DragConveyorInput(
            capacity_tph=self.i_capacity.value(),
            conveyor_length_m=self.i_length.value(),
            conveyor_height_m=self.i_height.value(),
            num_outlets=int(self.i_outlets.value()),
            friction_factor_F=self.i_F.value(),
            mechanical_efficiency=self.i_E_mech.value(),
            drive_efficiency=self.i_eta.value(),
            safety_factor=self.i_sf.value(),
        )
        b = BearingInput(
            radial_load_N=self.i_b_radial.value(),
            axial_load_N=self.i_b_axial.value(),
            shaft_speed_rpm=16,
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
