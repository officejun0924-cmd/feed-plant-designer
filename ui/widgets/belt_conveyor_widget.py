from PyQt6.QtWidgets import QGroupBox, QFormLayout, QCheckBox
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import BeltConveyorInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from app.config import REDUCER_BRANDS, DIRECT_COUPLING_BRANDS
import equipment.belt_conveyor as calc_module


class BeltConveyorWidget(BaseEquipmentWidget):

    def build_input_panel(self):
        g1 = QGroupBox("장비 사양")
        l1 = QFormLayout(g1)
        self.i_capacity  = InputGroup("처리량",               "ton/hr", 0.1, 500,  80)
        self.i_width     = InputGroup("Belt 폭 B",            "mm",     400, 2200, 600, 0,
                                      "표준: 400/450/500/600/750/900/1000/1050/1200/1400/1600/1800/2000/2200 mm")
        self.i_speed     = InputGroup("Belt 속도 v",          "m/min",  5,   180,  60)
        self.i_length    = InputGroup("수평 길이 l",          "m",      1,   500,  20)
        self.i_incline   = InputGroup("경사각",               "°",      0,   30,   0, 1)
        self.i_density   = InputGroup("재료 겉보기 비중 ρ",   "t/m³",   0.1, 2.0,  0.65, 2)

        # 표1-9: Roller 조건 콤보
        self.i_roller    = ComboGroup("Roller 조건 (표1-9)",
                                      ["양호", "보통", "내림"],
                                      "양호")

        # W 자동조회 여부
        self.chk_auto_W  = QCheckBox("W 자동 (표1-10)")
        self.chk_auto_W.setChecked(True)
        self.chk_auto_W.toggled.connect(self._on_auto_W_toggled)
        self.i_W         = InputGroup("W 수동 입력",           "kg/m",   10,  300,  35.5)
        self.i_W.setEnabled(False)   # 기본 자동

        self.i_eta       = InputGroup("전동 효율 η",           "",       0.5, 1.0,  0.85, 2)
        self.i_sf        = InputGroup("안전계수",              "",       1.0, 3.0,  1.25, 2)

        for w in [self.i_capacity, self.i_width, self.i_speed, self.i_length,
                  self.i_incline, self.i_density, self.i_roller]:
            l1.addRow(w)
        l1.addRow("", self.chk_auto_W)
        l1.addRow(self.i_W)
        l1.addRow(self.i_eta)
        l1.addRow(self.i_sf)
        self._input_layout.addWidget(g1)

        g2 = QGroupBox("베어링 계산 조건")
        l2 = QFormLayout(g2)
        self.i_b_radial = InputGroup("반경 하중 Fr", "N",   100, 500000, 8000)
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
        self.i_s_bend = InputGroup("굽힘 모멘트 M", "N·m", 0, 100000, 150)
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
        self.i_c_center = InputGroup("축간 거리",       "m",    0.1, 5.0, 0.5, 2)
        for w in [self.i_r_brand, self.i_r_sf, self.i_c_type, self.i_c_teeth, self.i_c_center]:
            l4.addRow(w)
        self._input_layout.addWidget(g4)
        self.i_r_brand.currentTextChanged.connect(self._on_brand_changed)

    def _on_brand_changed(self, brand: str):
        is_direct = brand in DIRECT_COUPLING_BRANDS
        for w in [self.i_c_type, self.i_c_teeth, self.i_c_center]:
            w.setEnabled(not is_direct)

    def _on_auto_W_toggled(self, checked: bool):
        self.i_W.setEnabled(not checked)

    def collect_inputs(self):
        eq = BeltConveyorInput(
            capacity_tph=self.i_capacity.value(),
            belt_width_mm=self.i_width.value(),
            belt_speed_mpm=self.i_speed.value(),
            conveyor_length_m=self.i_length.value(),
            inclination_deg=self.i_incline.value(),
            material_density=self.i_density.value(),
            roller_condition=self.i_roller.current_text(),
            auto_W=self.chk_auto_W.isChecked(),
            moving_parts_W=self.i_W.value(),
            drive_efficiency=self.i_eta.value(),
            safety_factor=self.i_sf.value(),
        )
        b = BearingInput(
            radial_load_N=self.i_b_radial.value(),
            axial_load_N=self.i_b_axial.value(),
            shaft_speed_rpm=50,
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
        if eq.capacity_tph <= 0:
            errors.append("처리량은 0 초과이어야 합니다.")
        if eq.inclination_deg > 30:
            errors.append("Belt Conveyor 경사각은 30° 이하로 설정하세요.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
