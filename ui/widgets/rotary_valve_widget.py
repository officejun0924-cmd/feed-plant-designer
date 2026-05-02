from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import RotaryValveInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from app.config import REDUCER_BRANDS, DIRECT_COUPLING_BRANDS
import equipment.rotary_valve as calc_module


class RotaryValveWidget(BaseEquipmentWidget):

    def build_input_panel(self):
        g1 = QGroupBox("로터리 밸브 사양")
        l1 = QFormLayout(g1)
        self.i_rotor_d  = InputGroup("Rotor 날개 직경 D", "mm",    200, 500, 300, 0,
                                     "표준: 200/250/300/350/400/450/500 mm")
        self.i_rotor_l  = InputGroup("Rotor 날개 길이 L", "m",     0.1, 1.0, 0.3, 2)
        self.i_shaft_d  = InputGroup("Shaft 직경 d",      "mm",    30,  150, 60,  0)
        self.i_rpm      = InputGroup("회전수 N",           "rpm",   10,  100, 30,  0,
                                     "통상 25~40 rpm, 최대 40 rpm 권장")
        self.i_density  = InputGroup("분립체 비중 γ",      "t/m³",  0.1, 2.0, 0.65, 2)
        self.i_clearance= InputGroup("공극률 X (표11-2)",  "",      0.05, 0.35, 0.1, 2,
                                     "사료=0.1, 대두=0.25, 옥수수=0.25")
        self.i_vol_eta  = InputGroup("용적 효율 η",        "",      0.5, 1.0, 0.85, 2)
        self.i_eta      = InputGroup("전동 효율",          "",      0.5, 1.0, 0.90, 2)
        self.i_sf       = InputGroup("안전계수",           "",      1.0, 3.0, 1.2,  2)
        for w in [self.i_rotor_d, self.i_rotor_l, self.i_shaft_d, self.i_rpm,
                  self.i_density, self.i_clearance, self.i_vol_eta, self.i_eta, self.i_sf]:
            l1.addRow(w)
        self._input_layout.addWidget(g1)

        g2 = QGroupBox("베어링 계산 조건")
        l2 = QFormLayout(g2)
        self.i_b_radial = InputGroup("반경 하중 Fr", "N",   100, 200000, 3000)
        self.i_b_axial  = InputGroup("축 하중 Fa",   "N",   0,   100000, 500)
        self.i_b_life   = InputGroup("요구 수명",    "hr",  1000, 100000, 25000)
        self.i_b_type   = ComboGroup("베어링 타입",
                                     ["deep_groove_ball", "spherical_roller", "cylindrical_roller"])
        self.i_b_rel    = ComboGroup("신뢰도",       ["90", "95", "97", "99"], "90")
        for w in [self.i_b_radial, self.i_b_axial, self.i_b_life, self.i_b_type, self.i_b_rel]:
            l2.addRow(w)
        self._input_layout.addWidget(g2)

        g3 = QGroupBox("샤프트 설계")
        l3 = QFormLayout(g3)
        self.i_s_bend = InputGroup("굽힘 모멘트 M", "N·m", 0, 50000, 50)
        self.i_s_mat  = ComboGroup("재질", ["S45C", "SCM440", "SNC836"])
        self.i_s_sf   = InputGroup("안전계수",       "",   1.0, 5.0, 2.0, 1)
        self.i_s_km   = InputGroup("굽힘 충격계수 Km","",  1.0, 3.0, 1.5, 1)
        self.i_s_kt   = InputGroup("비틀림 충격계수 Kt","", 1.0, 3.0, 1.0, 1)
        for w in [self.i_s_bend, self.i_s_mat, self.i_s_sf, self.i_s_km, self.i_s_kt]:
            l3.addRow(w)
        self._input_layout.addWidget(g3)

        g4 = QGroupBox("감속기 / 체인")
        l4 = QFormLayout(g4)
        self.i_r_brand  = ComboGroup("감속기 브랜드",   REDUCER_BRANDS, "효성")
        self.i_r_sf     = InputGroup("서비스계수",      "",     1.0, 3.0, 1.5, 1)
        self.i_c_type   = ComboGroup("체인 종류",       ["RS", "RF"], "RS")
        self.i_c_teeth  = InputGroup("소 스프로켓 잇수","T",    9, 40, 19, 0)
        self.i_c_center = InputGroup("축간 거리",       "m",    0.1, 5.0, 0.4, 2)
        for w in [self.i_r_brand, self.i_r_sf, self.i_c_type, self.i_c_teeth, self.i_c_center]:
            l4.addRow(w)
        self._input_layout.addWidget(g4)
        self.i_r_brand.currentTextChanged.connect(self._on_brand_changed)

    def _on_brand_changed(self, brand: str):
        is_direct = brand in DIRECT_COUPLING_BRANDS
        for w in [self.i_c_type, self.i_c_teeth, self.i_c_center]:
            w.setEnabled(not is_direct)

    def collect_inputs(self):
        eq = RotaryValveInput(
            rotor_diameter_mm=self.i_rotor_d.value(),
            rotor_length_m=self.i_rotor_l.value(),
            shaft_diameter_mm=self.i_shaft_d.value(),
            rotation_speed_rpm=self.i_rpm.value(),
            material_density=self.i_density.value(),
            clearance_ratio=self.i_clearance.value(),
            volumetric_efficiency=self.i_vol_eta.value(),
            drive_efficiency=self.i_eta.value(),
            safety_factor=self.i_sf.value(),
        )
        b = BearingInput(
            radial_load_N=self.i_b_radial.value(),
            axial_load_N=self.i_b_axial.value(),
            shaft_speed_rpm=eq.rotation_speed_rpm,
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
        r = ReducerInput(service_factor=self.i_r_sf.value(), brand=self.i_r_brand.current_text())
        c = ChainInput(chain_type=self.i_c_type.current_text(),
                       num_teeth_small=int(self.i_c_teeth.value()),
                       center_distance_m=self.i_c_center.value())
        return eq, b, s, r, c

    def validate_inputs(self, inp) -> list:
        eq, *_ = inp
        errors = []
        if eq.rotor_diameter_mm < 200 or eq.rotor_diameter_mm > 500:
            errors.append("Rotor 직경은 200~500 mm 범위이어야 합니다.")
        if eq.rotation_speed_rpm > 100:
            errors.append("회전수는 100 rpm 이하로 설정하세요.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
