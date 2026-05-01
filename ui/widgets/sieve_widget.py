from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import SieveInput, BearingInput, ShaftInput, ReducerInput, VBeltInput
import equipment.sieve as calc_module


class SieveWidget(BaseEquipmentWidget):

    def build_input_panel(self):
        g1 = QGroupBox("체 (Sieve) 사양")
        l1 = QFormLayout(g1)
        self.i_capacity = InputGroup("목표 처리량",          "ton/hr", 0.1, 500,  50)
        self.i_opening  = InputGroup("체 구멍 크기",         "mm",     0.1, 100,  3.0, 2,
                                     "표14-1: 0.16~100 mm")
        self.i_area     = InputGroup("체 면적",              "m²",     0.5, 50,   4.0, 1)
        self.i_density  = InputGroup("외관상 비중 ρ'",       "t/m³",   0.1, 2.0,  0.65, 2)
        self.i_incline  = InputGroup("경사각 β",             "°",      5,   45,   15,  0,
                                     "일반 10~20°, 분리 중시 5~10°")
        self._input_layout.addWidget(g1)

        g_factors = QGroupBox("수정계수 (표14-2 기준, 양호 조건 = 1.0)")
        lf = QFormLayout(g_factors)
        self.i_k = InputGroup("k — 입도 분포",    "", 0.1, 2.0, 1.0, 2)
        self.i_l = InputGroup("l — 입자 형상",    "", 0.1, 2.0, 1.0, 2)
        self.i_m = InputGroup("m — 수분",         "", 0.1, 2.0, 1.0, 2)
        self.i_n = InputGroup("n — 입자 밀도",    "", 0.1, 2.0, 1.0, 2)
        self.i_o = InputGroup("o — 부착성",       "", 0.1, 2.0, 1.0, 2)
        self.i_p = InputGroup("p — 공급 균일도",  "", 0.1, 2.0, 1.0, 2)
        for w in [self.i_k, self.i_l, self.i_m, self.i_n, self.i_o, self.i_p]:
            lf.addRow(w)
        self._input_layout.addWidget(g_factors)

        g_drive = QGroupBox("진동 모터 / 구동 조건")
        ld = QFormLayout(g_drive)
        self.i_eta = InputGroup("전동 효율 η", "", 0.5, 1.0, 0.90, 2)
        self.i_sf  = InputGroup("안전계수",    "", 1.0, 3.0, 1.2,  2)
        for w in [self.i_eta, self.i_sf]:
            ld.addRow(w)
        self._input_layout.addWidget(g_drive)

        g2 = QGroupBox("베어링 계산 조건")
        l2 = QFormLayout(g2)
        self.i_b_radial = InputGroup("반경 하중 Fr", "N",   100, 200000, 4000)
        self.i_b_axial  = InputGroup("축 하중 Fa",   "N",   0,   100000, 0)
        self.i_b_life   = InputGroup("요구 수명",    "hr",  1000, 100000, 20000)
        self.i_b_type   = ComboGroup("베어링 타입",
                                     ["deep_groove_ball", "spherical_roller", "cylindrical_roller"])
        self.i_b_rel    = ComboGroup("신뢰도",       ["90", "95", "97", "99"], "90")
        for w in [self.i_b_radial, self.i_b_axial, self.i_b_life, self.i_b_type, self.i_b_rel]:
            l2.addRow(w)
        self._input_layout.addWidget(g2)

        g3 = QGroupBox("샤프트 설계")
        l3 = QFormLayout(g3)
        self.i_s_bend = InputGroup("굽힘 모멘트 M", "N·m", 0, 50000, 60)
        self.i_s_mat  = ComboGroup("재질", ["S45C", "SCM440", "SNC836"])
        self.i_s_sf   = InputGroup("안전계수",       "",   1.0, 5.0, 2.0, 1)
        self.i_s_km   = InputGroup("굽힘 충격계수 Km","",  1.0, 3.0, 2.0, 1,
                                    "진동체: 갑작스러운 충격 → 2.0 권장")
        self.i_s_kt   = InputGroup("비틀림 충격계수 Kt","", 1.0, 3.0, 1.5, 1)
        for w in [self.i_s_bend, self.i_s_mat, self.i_s_sf, self.i_s_km, self.i_s_kt]:
            l3.addRow(w)
        self._input_layout.addWidget(g3)

        g4 = QGroupBox("감속기 / V벨트")
        l4 = QFormLayout(g4)
        self.i_r_sf  = InputGroup("서비스계수",     "",  1.0, 3.0, 1.5, 1)
        self.i_v_cen = InputGroup("V벨트 중심거리", "m", 0.1, 3.0, 0.4, 2)
        self.i_v_sec = ComboGroup("V벨트 단면",    ["auto", "A", "B", "C", "D"])
        for w in [self.i_r_sf, self.i_v_cen, self.i_v_sec]:
            l4.addRow(w)
        self._input_layout.addWidget(g4)

    def collect_inputs(self):
        eq = SieveInput(
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
            drive_efficiency=self.i_eta.value(),
            safety_factor=self.i_sf.value(),
        )
        b = BearingInput(
            radial_load_N=self.i_b_radial.value(),
            axial_load_N=self.i_b_axial.value(),
            shaft_speed_rpm=1000,
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
        if eq.sieve_area_m2 <= 0:
            errors.append("체 면적은 0 초과이어야 합니다.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, v = inp
        return calc_module.calculate(eq, b, s, r, v)
