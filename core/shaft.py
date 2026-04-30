import math
from models.input_models import ShaftInput
from models.result_models import ShaftResult
from app.config import SHAFT_MATERIALS, KS_PREFERRED_DIAMETERS


class ShaftDesigner:
    """ASME 코드 기준 샤프트 설계"""

    def calc_equivalent_torque(self, T: float, M: float,
                               Km: float = 1.5, Kt: float = 1.0) -> float:
        """ASME 상당 토크: Te = √[(Km·M)² + (Kt·T)²]"""
        return math.sqrt((Km * M) ** 2 + (Kt * T) ** 2)

    def calc_shaft_diameter(self, Te: float, Ss_allow_MPa: float) -> float:
        """상당 토크로부터 샤프트 직경 [mm]
        d³ = 16·Te / (π·Ss_allow)
        Ss_allow in MPa, Te in N·m → d in m → convert to mm
        """
        Ss_Pa = Ss_allow_MPa * 1e6
        d_m = (16.0 * Te / (math.pi * Ss_Pa)) ** (1.0 / 3.0)
        return d_m * 1000.0

    def select_standard_diameter(self, d_calc_mm: float) -> float:
        """KS 우선수(R40) 계열 표준 직경 선정"""
        for d in KS_PREFERRED_DIAMETERS:
            if d >= d_calc_mm:
                return float(d)
        return float(KS_PREFERRED_DIAMETERS[-1])

    def calc_von_mises_stress(self, T: float, M: float, d_mm: float) -> float:
        """Von Mises 복합응력 [MPa]
        σ_b = 32·M / (π·d³)
        τ   = 16·T / (π·d³)
        σ_v = √(σ_b² + 3·τ²)
        """
        d_m = d_mm / 1000.0
        d3 = d_m ** 3
        sigma_b = 32.0 * M / (math.pi * d3)
        tau = 16.0 * T / (math.pi * d3)
        sigma_v = math.sqrt(sigma_b ** 2 + 3.0 * tau ** 2)
        return sigma_v / 1e6  # Pa → MPa

    def design(self, inp: ShaftInput) -> ShaftResult:
        mat = SHAFT_MATERIALS.get(inp.material, SHAFT_MATERIALS["S45C"])
        Sy = mat["Sy_MPa"]

        # 허용 전단응력: Ss_allow = Sy / (2 * SF)
        Ss_allow = Sy / (2.0 * inp.safety_factor)
        allow_stress = Sy / inp.safety_factor

        Te = self.calc_equivalent_torque(inp.torque_Nm, inp.bending_moment_Nm,
                                         inp.km_factor, inp.kt_factor)
        d_calc = self.calc_shaft_diameter(Te, Ss_allow)
        d_std = self.select_standard_diameter(d_calc)

        sigma_v = self.calc_von_mises_stress(inp.torque_Nm, inp.bending_moment_Nm, d_std)
        sf_actual = Sy / sigma_v if sigma_v > 0 else 999.0

        return ShaftResult(
            required_diameter_mm=round(d_calc, 2),
            selected_diameter_mm=d_std,
            von_mises_stress_MPa=round(sigma_v, 2),
            allowable_stress_MPa=round(allow_stress, 2),
            safety_factor_actual=round(sf_actual, 2),
            material=inp.material,
        )
