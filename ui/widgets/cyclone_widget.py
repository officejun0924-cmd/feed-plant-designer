from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import CycloneInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from app.config import REDUCER_BRANDS, DIRECT_COUPLING_BRANDS
import equipment.cyclone as calc_module


class CycloneWidget(BaseEquipmentWidget):

    def build_input_panel(self):
        g1 = QGroupBox("사이클론 설계 조건")
        l1 = QFormLayout(g1)
        self.i_air_vol  = InputGroup("처리 풍량 Qa",      "m³/min", 10,   5000, 380)
        self.i_inlet_v  = InputGroup("유입 풍속 Va",       "m/sec",  7,    18,   18, 1,
                                     "최적 15~18 m/sec")
        self.i_lambda   = InputGroup("압력손실계수 λ",     "",       5,    25,   12, 0,
                                     "일반 Cyclone ≈ 12, 고효율 ≈ 8")
        self.i_type     = ComboGroup("Cyclone 형식",      ["일반", "고효율", "고용량"])
        self.i_fan_eta  = InputGroup("Fan 효율 η_fan",    "",       0.5,  1.0,  0.72, 2)
        self.i_eta      = InputGroup("전동 효율 η",        "",       0.5,  1.0,  0.95, 2)
        self.i_sf       = InputGroup("안전계수",           "",       1.0,  3.0,  1.15, 2)
        for w in [self.i_air_vol, self.i_inlet_v, self.i_lambda,
                  self.i_type, self.i_fan_eta, self.i_eta, self.i_sf]:
            l1.addRow(w)
        self._input_layout.addWidget(g1)

        g2 = QGroupBox("베어링 계산 조건 (Fan 구동)")
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

        g4 = QGroupBox("감속기 / 체인")
        l4 = QFormLayout(g4)
        self.i_r_brand  = ComboGroup("감속기 브랜드",   REDUCER_BRANDS, "효성")
        self.i_r_sf     = InputGroup("서비스계수",      "",     1.0, 3.0, 1.2, 1)
        self.i_c_type   = ComboGroup("체인 종류",       ["RS", "RF"], "RS")
        self.i_c_teeth  = InputGroup("소 스프로켓 잇수","T",    9, 40, 19, 0)
        self.i_c_center = InputGroup("축간 거리",       "m",    0.1, 5.0, 0.5, 2)
        for w in [self.i_r_brand, self.i_r_sf, self.i_c_type, self.i_c_teeth, self.i_c_center]:
            l4.addRow(w)
        self._input_layout.addWidget(g4)
        self.i_r_brand.currentTextChanged.connect(self._on_brand_changed)

    def _on_brand_changed(self, brand: str):
        is_direct = brand in DIRECT_COUPLING_BRANDS
        for w in [self.i_c_type, self.i_c_teeth, self.i_c_center]:
            w.setEnabled(not is_direct)

    def collect_inputs(self):
        eq = CycloneInput(
            air_volume_m3min=self.i_air_vol.value(),
            inlet_velocity_msec=self.i_inlet_v.value(),
            pressure_loss_coef=self.i_lambda.value(),
            cyclone_type=self.i_type.current_text(),
            fan_efficiency=self.i_fan_eta.value(),
            drive_efficiency=self.i_eta.value(),
            safety_factor=self.i_sf.value(),
        )
        b = BearingInput(
            radial_load_N=self.i_b_radial.value(),
            axial_load_N=self.i_b_axial.value(),
            shaft_speed_rpm=1450,
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
        if eq.air_volume_m3min <= 0:
            errors.append("처리 풍량은 0 초과이어야 합니다.")
        if eq.inlet_velocity_msec < 7:
            errors.append("유입 풍속은 7 m/sec 이상이어야 합니다.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
