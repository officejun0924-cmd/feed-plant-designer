from PyQt6.QtWidgets import QGroupBox, QFormLayout
from ui.base_widget import BaseEquipmentWidget
from ui.components.input_group import InputGroup, ComboGroup
from models.input_models import MixerPelletizerInput
from app.config import MATERIAL_DB
import equipment.mixer_pelletizer as calc_module


class MixerPelletizerWidget(BaseEquipmentWidget):

    def build_equipment_specs(self) -> QGroupBox:
        g = QGroupBox("장비 사양 — 믹서 / 펄버라이저")
        l = QFormLayout(g)

        material_keys = list(MATERIAL_DB.keys())
        self.i_material = ComboGroup("원재료",         material_keys, "직접 입력")
        self.i_capacity = InputGroup("처리량",         "ton/hr", 0.1, 200,  5)
        self.i_density  = InputGroup("비중 γ",         "t/m³",   0.1, 3.0,  0.65, 3)
        self.i_diameter = InputGroup("믹서 직경",      "m",      0.2, 3.0,  0.6, 2)
        self.i_length   = InputGroup("믹서 길이",      "m",      0.3, 10.0, 1.5, 2)
        self.i_paddles  = InputGroup("패들 수",        "개",     2,   100,  12, 0)
        self.i_speed    = InputGroup("샤프트 회전수",  "rpm",    10,  500,  60)
        self.i_np       = InputGroup("파워 넘버 Np",   "",       0.1, 5.0,  0.4, 2,
                                      "Newton 교반 동력 수 (패들믹서 ≈ 0.3~1.2)")

        for w in [self.i_material, self.i_capacity, self.i_density, self.i_diameter,
                  self.i_length, self.i_paddles, self.i_speed, self.i_np]:
            l.addRow(w)

        self.i_material.currentTextChanged.connect(self._on_material_changed)
        return g

    def _on_material_changed(self, name: str):
        data = MATERIAL_DB.get(name, {})
        if data:
            self.i_density.set_value(data.get("specific_gravity", 0.65))

    def collect_equipment_input(self):
        return MixerPelletizerInput(
            capacity_tph=self.i_capacity.value(),
            specific_gravity=self.i_density.value(),
            mixer_diameter_m=self.i_diameter.value(),
            mixer_length_m=self.i_length.value(),
            paddle_number=int(self.i_paddles.value()),
            shaft_speed_rpm=self.i_speed.value(),
            mixing_factor=self.i_np.value(),
        )

    def validate_inputs(self, inp) -> list:
        return []

    def run_calculation(self, inp):
        eq, b, s, r, c = inp
        return calc_module.calculate(eq, b, s, r, c)
