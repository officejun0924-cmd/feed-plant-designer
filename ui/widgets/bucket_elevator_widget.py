from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import BucketElevatorInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from app.config import REDUCER_BRANDS, DIRECT_COUPLING_BRANDS
import equipment.bucket_elevator as calc_module


class BucketElevatorWidget(BaseEquipmentWidget):

    def build_input_panel(self):
        g1 = QGroupBox("장비 사양")
        l1 = QFormLayout(g1)
        self.i_capacity   = InputGroup("처리량",        "ton/hr", 0.1, 500,   20)
        self.i_density    = InputGroup("비중",            "t/m³",   0.1, 3.0,   0.65, 3)
        self.i_height     = InputGroup("양정 (양송 높이)", "m",    1,   100,   15)
        self.i_bkt_vol    = InputGroup("버킷 용량",      "L",     0.5, 100,   5)
        self.i_bkt_space  = InputGroup("버킷 간격",      "m",     0.1, 2.0,   0.5, 2)
        self.i_belt_speed = InputGroup("벨트 속도",      "m/s",   0.5, 5.0,   1.5, 2)
        self.i_eta        = InputGroup("전동 효율 η",    "",      0.5, 1.0,   0.88, 2)
        self.i_sf         = InputGroup("안전계수",       "",      1.0, 3.0,   1.3, 2)
        for w in [self.i_capacity, self.i_density, self.i_height, self.i_bkt_vol,
                  self.i_bkt_space, self.i_belt_speed, self.i_eta, self.i_sf]:
            l1.addRow(w)
        self._input_layout.addWidget(g1)

        g2 = QGroupBox("베어링 계산 조건")
        l2 = QFormLayout(g2)
        self.i_b_radial = InputGroup("반경 하중 Fr", "N",   100, 500000, 8000)
        self.i_b_axial  = InputGroup("축 하중 Fa",  "N",   0,   200000, 0)
        self.i_b_life   = InputGroup("요구 수명",   "hr",  1000, 100000, 30000)
        self.i_b_type   = ComboGroup("베어링 타입",
                                     ["deep_groove_ball", "spherical_roller", "cylindrical_roller"])
        self.i_b_rel    = ComboGroup("신뢰도", ["90", "95", "97", "99"], "90")
        for w in [self.i_b_radial, self.i_b_axial, self.i_b_life, self.i_b_type, self.i_b_rel]:
            l2.addRow(w)
        self._input_layout.addWidget(g2)

        g3 = QGroupBox("샤프트 설계")
        l3 = QFormLayout(g3)
        self.i_s_bending  = InputGroup("굽힘 모멘트 M", "N·m",  0, 50000, 120)
        self.i_s_material = ComboGroup("재질", ["S45C", "SCM440", "SNC836"])
        self.i_s_sf       = InputGroup("안전계수",       "",     1.0, 5.0, 2.0, 1)
        self.i_s_km       = InputGroup("굽힘 충격계수 Km","",   1.0, 3.0, 1.5, 1)
        self.i_s_kt       = InputGroup("비틀림 충격계수 Kt","", 1.0, 3.0, 1.0, 1)
        for w in [self.i_s_bending, self.i_s_material, self.i_s_sf, self.i_s_km, self.i_s_kt]:
            l3.addRow(w)
        self._input_layout.addWidget(g3)

        g_red = QGroupBox("감속기 / 체인")
        l_red = QFormLayout(g_red)
        self.i_r_brand  = ComboGroup("감속기 브랜드",  REDUCER_BRANDS, "효성")
        self.i_r_sf     = InputGroup("서비스계수",    "",     1.0, 3.0, 1.5, 1)
        self.i_c_type   = ComboGroup("체인 종류",     ["RS", "RF"], "RS")
        self.i_c_teeth  = InputGroup("소 스프로켓 잇수", "T", 9, 40,  19, 0)
        self.i_c_center = InputGroup("축간 거리",     "m",   0.1, 5.0, 0.5, 2)
        for w in [self.i_r_brand, self.i_r_sf, self.i_c_type, self.i_c_teeth, self.i_c_center]:
            l_red.addRow(w)
        self._input_layout.addWidget(g_red)
        self.i_r_brand.currentTextChanged.connect(self._on_brand_changed)

    def collect_inputs(self):
        eq = BucketElevatorInput(
            capacity_tph=self.i_capacity.value(),
            specific_gravity=self.i_density.value(),
            lift_height_m=self.i_height.value(),
            bucket_volume_L=self.i_bkt_vol.value(),
            bucket_spacing_m=self.i_bkt_space.value(),
            belt_speed_mps=self.i_belt_speed.value(),
            drive_efficiency=self.i_eta.value(),
            safety_factor=self.i_sf.value(),
        )
        b = BearingInput(
            radial_load_N=self.i_b_radial.value(),
            axial_load_N=self.i_b_axial.value(),
            shaft_speed_rpm=eq.belt_speed_mps * 60.0 / 0.4,
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
        r = ReducerInput(service_factor=self.i_r_sf.value(), brand=self.i_r_brand.current_text())
        c = ChainInput(chain_type=self.i_c_type.current_text(),
                       num_teeth_small=int(self.i_c_teeth.value()),
                       center_distance_m=self.i_c_center.value())
        return eq, b, s, r, c

    def _on_brand_changed(self, brand: str):
        is_direct = brand in DIRECT_COUPLING_BRANDS
        for w in [self.i_c_type, self.i_c_teeth, self.i_c_center]:
            w.setEnabled(not is_direct)

    def validate_inputs(self, inp) -> list:
        eq, b, s, r, c = inp
        errors = []
        if eq.capacity_tph <= 0:
            errors.append("처리량은 0 초과이어야 합니다.")
        if eq.lift_height_m <= 0:
            errors.append("양정은 0 초과이어야 합니다.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
