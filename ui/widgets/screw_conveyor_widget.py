from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import (
    ScrewConveyorInput, BearingInput, ShaftInput, ReducerInput, ChainInput,
)
from app.config import MATERIAL_DB, REDUCER_BRANDS, DIRECT_COUPLING_BRANDS
import equipment.screw_conveyor as calc_module


class ScrewConveyorWidget(BaseEquipmentWidget):

    def build_input_panel(self):
        # ── 장비 사양 ──────────────────────────────────────────────────────
        g1 = QGroupBox("장비 사양")
        l1 = QFormLayout(g1)

        material_keys = list(MATERIAL_DB.keys())
        self.i_material      = ComboGroup("원재료",            material_keys, "직접 입력")
        self.i_specific_grav = InputGroup("비중 γ",           "t/m³",  0.1, 3.0,  0.65, 3)
        self.i_friction      = InputGroup("마찰계수 f",        "",      0.01, 0.9, 0.40, 3)
        self.i_mat_factor    = InputGroup("재료 상수 C",       "",      0.5, 5.0,  1.2,  2,
                                          "사료류 ≈ 1.2, 분체류 ≈ 1.5~4.0")
        self.i_capacity      = InputGroup("운반 용량 Qt",      "ton/hr", 0.1, 500, 20)
        self.i_diameter      = InputGroup("스크류 외경 D",     "m",     0.1, 1.0,  0.3, 3)
        self.i_shaft_d       = InputGroup("샤프트 외경 d",     "m",     0.02, 0.5, 0.089, 3,
                                          "스크류 축 외경 — 예: D×0.3 ≈ 0.09m")
        self.i_pitch         = InputGroup("피치 P",            "m",     0.05, 1.0, 0.3, 3)
        self.i_speed         = InputGroup("회전수 N",          "rpm",   10, 500,   100)
        self.i_length        = InputGroup("이송 길이 ℓ",       "m",     1, 100,    6)
        self.i_inclination   = InputGroup("경사각",            "°",     0,  45,    0, 1)
        self.i_fill          = InputGroup("충만효율 Φ",        "",      0.1, 1.0,  0.45, 2)
        self.i_eta           = InputGroup("전동 효율 η",       "",      0.5, 1.0,  0.90, 2)
        self.i_sf_eq         = InputGroup("안전계수 Sf",       "",      1.0, 3.0,  1.1,  2)

        for w in [self.i_material, self.i_specific_grav, self.i_friction, self.i_mat_factor,
                  self.i_capacity, self.i_diameter, self.i_shaft_d, self.i_pitch,
                  self.i_speed, self.i_length, self.i_inclination,
                  self.i_fill, self.i_eta, self.i_sf_eq]:
            l1.addRow(w)
        self._input_layout.addWidget(g1)

        # 원재료 변경 → 자동 입력
        self.i_material.currentTextChanged.connect(self._on_material_changed)

        # ── 베어링 계산 조건 ───────────────────────────────────────────────
        g2 = QGroupBox("베어링 계산 조건")
        l2 = QFormLayout(g2)
        self.i_b_radial = InputGroup("반경 하중 Fr",  "N",   100, 500000, 5000)
        self.i_b_axial  = InputGroup("축 하중 Fa",   "N",   0,   200000, 0)
        self.i_b_life   = InputGroup("요구 수명",    "hr",  1000, 100000, 25000)
        self.i_b_type   = ComboGroup("베어링 타입",
                                     ["deep_groove_ball", "UCF", "UCP", "UCFC",
                                      "spherical_roller", "cylindrical_roller"])
        self.i_b_rel    = ComboGroup("신뢰도",       ["90", "95", "97", "99"], "90")
        for w in [self.i_b_radial, self.i_b_axial, self.i_b_life, self.i_b_type, self.i_b_rel]:
            l2.addRow(w)
        self._input_layout.addWidget(g2)

        # ── 샤프트 설계 ───────────────────────────────────────────────────
        g3 = QGroupBox("샤프트 설계")
        l3 = QFormLayout(g3)
        self.i_s_bending  = InputGroup("굽힘 모멘트 M", "N·m", 0, 50000, 80)
        self.i_s_material = ComboGroup("재질", ["S45C", "SCM440", "SNC836"])
        self.i_s_sf       = InputGroup("안전계수",       "",    1.0, 5.0, 2.0, 1)
        self.i_s_km       = InputGroup("굽힘 충격계수 Km","",  1.0, 3.0, 1.5, 1)
        self.i_s_kt       = InputGroup("비틀림 충격계수 Kt","",1.0, 3.0, 1.0, 1)
        for w in [self.i_s_bending, self.i_s_material, self.i_s_sf, self.i_s_km, self.i_s_kt]:
            l3.addRow(w)
        self._input_layout.addWidget(g3)

        # ── 감속기 / 체인 ─────────────────────────────────────────────────
        g4 = QGroupBox("감속기 / 체인")
        l4 = QFormLayout(g4)
        self.i_r_brand  = ComboGroup("감속기 브랜드",  REDUCER_BRANDS, "효성")
        self.i_r_sf     = InputGroup("서비스계수",    "",     1.0, 3.0, 1.5, 1)
        self.i_c_type   = ComboGroup("체인 종류",     ["RS", "RF"], "RS")
        self.i_c_teeth  = InputGroup("소 스프로켓 잇수", "T", 9, 40,  19, 0)
        self.i_c_center = InputGroup("축간 거리",     "m",   0.1, 5.0, 0.5, 2)
        for w in [self.i_r_brand, self.i_r_sf, self.i_c_type, self.i_c_teeth, self.i_c_center]:
            l4.addRow(w)
        self._input_layout.addWidget(g4)

        # 브랜드 변경 → 체인 위젯 활성/비활성
        self.i_r_brand.currentTextChanged.connect(self._on_brand_changed)

    def _on_material_changed(self, name: str):
        """원재료 선택 시 비중·마찰계수·재료계수 자동 입력"""
        data = MATERIAL_DB.get(name, {})
        if data:
            self.i_specific_grav.set_value(data.get("specific_gravity", 0.65))
            self.i_friction.set_value(data.get("friction", 0.40))
            self.i_mat_factor.set_value(data.get("material_factor", 1.4))

    def _on_brand_changed(self, brand: str):
        """SEW/FALK 직결 브랜드 선택 시 체인 위젯 비활성화"""
        is_direct = brand in DIRECT_COUPLING_BRANDS
        for w in [self.i_c_type, self.i_c_teeth, self.i_c_center]:
            w.setEnabled(not is_direct)

    def collect_inputs(self):
        eq = ScrewConveyorInput(
            capacity_tph=self.i_capacity.value(),
            specific_gravity=self.i_specific_grav.value(),
            material_name=self.i_material.current_text(),
            screw_diameter_m=self.i_diameter.value(),
            shaft_outer_diameter_m=self.i_shaft_d.value(),
            screw_pitch_m=self.i_pitch.value(),
            screw_speed_rpm=self.i_speed.value(),
            length_m=self.i_length.value(),
            inclination_deg=self.i_inclination.value(),
            material_factor=self.i_mat_factor.value(),
            friction_factor=self.i_friction.value(),
            fill_efficiency=self.i_fill.value(),
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
        r = ReducerInput(
            service_factor=self.i_r_sf.value(),
            brand=self.i_r_brand.current_text(),
        )
        c = ChainInput(
            chain_type=self.i_c_type.current_text(),
            num_teeth_small=int(self.i_c_teeth.value()),
            center_distance_m=self.i_c_center.value(),
        )
        return eq, b, s, r, c

    def validate_inputs(self, inp) -> list:
        eq, b, s, r, c = inp
        errors = []
        if eq.capacity_tph <= 0:
            errors.append("운반 용량은 0 초과이어야 합니다.")
        if eq.inclination_deg > 45:
            errors.append("스크류 경사각은 45° 이하로 설정하세요.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
