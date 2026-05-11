from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import BucketElevatorInput
from app.config import MATERIAL_DB
import equipment.bucket_elevator as calc_module


class BucketElevatorWidget(BaseEquipmentWidget):

    def build_equipment_specs(self) -> QGroupBox:
        g = QGroupBox("장비 사양 — 버킷 엘리베이터")
        l = QFormLayout(g)

        material_keys = list(MATERIAL_DB.keys())
        self.i_material   = ComboGroup("원재료",          material_keys, "직접 입력")
        self.i_capacity   = InputGroup("처리량",          "ton/hr", 0.1, 500,   20)
        self.i_density    = InputGroup("비중 γ",          "t/m³",   0.1, 3.0,   0.65, 3)
        self.i_height     = InputGroup("양정 (양송 높이)","m",      1,   100,   15)
        self.i_bkt_vol    = InputGroup("버킷 용량",       "L",      0.5, 100,   5)
        self.i_bkt_space  = InputGroup("버킷 간격",       "m",      0.1, 2.0,   0.5, 2)
        self.i_belt_speed = InputGroup("벨트 속도",       "m/s",    0.5, 5.0,   1.5, 2)

        for w in [self.i_material, self.i_capacity, self.i_density, self.i_height,
                  self.i_bkt_vol, self.i_bkt_space, self.i_belt_speed]:
            l.addRow(w)

        self.i_material.currentTextChanged.connect(self._on_material_changed)
        return g

    def _on_material_changed(self, name: str):
        data = MATERIAL_DB.get(name, {})
        if data:
            self.i_density.set_value(data.get("specific_gravity", 0.65))

    def collect_equipment_input(self):
        return BucketElevatorInput(
            capacity_tph=self.i_capacity.value(),
            specific_gravity=self.i_density.value(),
            lift_height_m=self.i_height.value(),
            bucket_volume_L=self.i_bkt_vol.value(),
            bucket_spacing_m=self.i_bkt_space.value(),
            belt_speed_mps=self.i_belt_speed.value(),
        )

    def validate_inputs(self, inp) -> list:
        eq, *_ = inp
        errors = []
        if eq.capacity_tph <= 0:
            errors.append("처리량은 0 초과이어야 합니다.")
        if eq.lift_height_m <= 0:
            errors.append("양정은 0 초과이어야 합니다.")
        return errors

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
