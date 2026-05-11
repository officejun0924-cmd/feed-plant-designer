from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import RotaryValveInput
from app.config import MATERIAL_DB
import equipment.rotary_valve as calc_module


class RotaryValveWidget(BaseEquipmentWidget):

    def build_equipment_specs(self) -> QGroupBox:
        g = QGroupBox("로터리 밸브 사양")
        l = QFormLayout(g)

        material_keys = list(MATERIAL_DB.keys())
        self.i_material  = ComboGroup("원재료",              material_keys, "직접 입력")
        self.i_rotor_d   = InputGroup("Rotor 날개 직경 D",  "mm",    200, 500, 300, 0,
                                       "표준: 200/250/300/350/400/450/500 mm")
        self.i_rotor_l   = InputGroup("Rotor 유효 길이 L",  "m",     0.1, 2.0, 0.388, 3)
        self.i_rpm       = InputGroup("회전수 N",            "rpm",   10,  100, 33.06, 2,
                                       "통상 25~40 rpm, 최대 40 rpm 권장")
        self.i_density   = InputGroup("분립체 비중 ρ",       "t/m³",  0.1, 2.0, 0.7,  2)
        self.i_pockets   = InputGroup("포켓 개수 npocket",   "개",    4,   12,  6,    0)
        self.i_pocket_a  = InputGroup("포켓 단면적 Apocket", "m²",    0.0, 1.0, 0.0,  6,
                                       "0 입력 시 기하학으로 자동 계산")
        self.i_clearance = InputGroup("공극률 X",            "",      0.05, 0.35, 0.1, 2,
                                       "사료=0.1, 대두=0.25, 옥수수=0.25")
        self.i_vol_eta   = InputGroup("충만 효율 η",         "",      0.5, 1.0, 0.8,  2)

        for w in [self.i_material, self.i_rotor_d, self.i_rotor_l, self.i_rpm,
                  self.i_density, self.i_pockets, self.i_pocket_a,
                  self.i_clearance, self.i_vol_eta]:
            l.addRow(w)

        self.i_material.currentTextChanged.connect(self._on_material_changed)
        return g

    def _on_material_changed(self, name: str):
        data = MATERIAL_DB.get(name, {})
        if data:
            self.i_density.set_value(data.get("specific_gravity", 0.65))

    def collect_equipment_input(self):
        s = self._collect_shaft()
        return RotaryValveInput(
            rotor_diameter_mm=self.i_rotor_d.value(),
            rotor_length_m=self.i_rotor_l.value(),
            shaft_diameter_mm=s.user_diameter_mm if s.user_diameter_mm > 0 else 60.0,
            rotation_speed_rpm=self.i_rpm.value(),
            material_density=self.i_density.value(),
            num_pockets=int(self.i_pockets.value()),
            pocket_area_m2=self.i_pocket_a.value(),
            clearance_ratio=self.i_clearance.value(),
            volumetric_efficiency=self.i_vol_eta.value(),
        )

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
