import math
from models.input_models import ReducerInput, VBeltInput
from models.result_models import ReducerResult, VBeltResult
from app.config import VBELT_SECTIONS


class ReducerSelector:
    """감속기 선정 (KS B 6386)"""

    def select_reducer(self, inp: ReducerInput) -> ReducerResult:
        from database.db_loader import DBLoader
        reducers = DBLoader.get_reducer_db()

        ratio = inp.input_speed_rpm / inp.output_speed_rpm
        design_power = inp.input_power_kW * inp.service_factor

        in_torque = 9550.0 * inp.input_power_kW / inp.input_speed_rpm
        candidates = [
            r for r in reducers
            if abs(r["ratio"] - ratio) / ratio <= 0.15        # ±15% 허용
            and r["rated_power_kW"] >= design_power
        ]

        if not candidates:
            candidates = reducers
        selected = min(candidates, key=lambda r: (abs(r["ratio"] - ratio), r["rated_power_kW"]))

        eff = selected.get("efficiency_pct", 96.0)
        out_torque = in_torque * selected["ratio"] * (eff / 100.0)

        return ReducerResult(
            ratio=round(selected["ratio"], 2),
            model=selected["model"],
            input_torque_Nm=round(in_torque, 1),
            output_torque_Nm=round(out_torque, 1),
            efficiency_pct=eff,
            frame_size=selected.get("frame_size", ""),
        )


class VBeltSelector:
    """V벨트 선정 (KS B 1400)"""

    SECTION_RPM_TABLE = {
        "A": (0.4,  5000),
        "B": (0.9,  4500),
        "C": (2.2,  4000),
        "D": (5.5,  3200),
    }

    def select_section_auto(self, design_power_kW: float, drive_rpm: float) -> str:
        """동력-회전수 기반 단면 자동 선정"""
        if design_power_kW < 2.0 and drive_rpm > 1000:
            return "A"
        elif design_power_kW < 7.5:
            return "B"
        elif design_power_kW < 22.0:
            return "C"
        else:
            return "D"

    def calc_pulley_diameters(self, section: str, drive_rpm: float, driven_rpm: float):
        """피치 직경 계산 (최소 직경 이상, 표준 계열 선정)"""
        min_d = VBELT_SECTIONS[section]["pitch_dia_min_mm"]
        standard_d = [63, 71, 80, 90, 100, 112, 125, 140, 160, 180,
                      200, 224, 250, 280, 315, 355, 400, 450, 500, 560, 630]
        d1 = next((d for d in standard_d if d >= min_d), min_d)
        ratio = drive_rpm / driven_rpm
        d2_calc = d1 * ratio
        d2 = min(standard_d, key=lambda d: abs(d - d2_calc))
        return float(d1), float(d2)

    def calc_belt_length(self, d1: float, d2: float, C: float) -> float:
        """피치 길이 L = 2C + π(d1+d2)/2 + (d2-d1)²/(4C)"""
        return 2.0 * C + math.pi * (d1 + d2) / 2.0 + (d2 - d1) ** 2 / (4.0 * C)

    def select_standard_length(self, section: str, L_calc_mm: float) -> tuple:
        """KS 표준 호칭 길이 선정"""
        from database.db_loader import DBLoader
        vbelt_db = DBLoader.get_vbelt_db()
        lengths = vbelt_db.get(section, {}).get("standard_lengths_mm", [])
        if not lengths:
            std_L = round(L_calc_mm / 50) * 50
            return std_L, str(int(std_L))
        std_L = min(lengths, key=lambda l: abs(l - L_calc_mm) if l >= L_calc_mm else float("inf"))
        # 호칭: KS 기준 벨트 번호 (mm / 25.4 * 인치 표기 또는 mm 직접)
        designation = f"{section}{int(std_L)}"
        return float(std_L), designation

    def calc_contact_angle(self, d1: float, d2: float, C: float) -> float:
        """소 풀리 접촉각 [°] θ = 180 - 57.3*(d2-d1)/C"""
        return 180.0 - 57.3 * (d2 - d1) / C

    def calc_correction_factors(self, section: str, d1: float,
                                contact_deg: float, std_L_mm: float) -> tuple:
        """Kθ (접촉각 보정), KL (길이 보정) - KS B 1400 표 근사식"""
        # 접촉각 보정 Kθ
        if contact_deg >= 180:
            K_theta = 1.0
        elif contact_deg >= 120:
            K_theta = 1.0 - 0.5123 * (1.0 - contact_deg / 180.0) ** 0.5
        else:
            K_theta = 0.5 + 0.5 * math.sin(math.radians(contact_deg / 2.0))

        # 길이 보정 KL (B단면 기준 1250mm 기준장)
        base_lengths = {"A": 900, "B": 1250, "C": 2000, "D": 3550}
        L_base = base_lengths.get(section, 1250)
        K_L = (std_L_mm / L_base) ** 0.09
        return K_theta, K_L

    def calc_power_per_belt(self, section: str, d1: float, drive_rpm: float) -> float:
        """단일 벨트 전달 동력 [kW] - KS B 1400 표 근사식"""
        v = math.pi * d1 / 1000.0 * drive_rpm / 60.0  # m/s
        base = VBELT_SECTIONS[section]["power_base_kW"]
        return base * (v / 10.0) ** 0.8 * (d1 / 150.0) ** 0.2

    def select_vbelt(self, inp: VBeltInput) -> VBeltResult:
        section = inp.section if inp.section != "auto" else \
            self.select_section_auto(inp.design_power_kW, inp.drive_speed_rpm)

        d1, d2 = self.calc_pulley_diameters(section, inp.drive_speed_rpm, inp.driven_speed_rpm)
        C_mm = inp.center_distance_m * 1000.0
        L_calc = self.calc_belt_length(d1, d2, C_mm)
        std_L, designation = self.select_standard_length(section, L_calc)
        theta = self.calc_contact_angle(d1, d2, C_mm)
        K_theta, K_L = self.calc_correction_factors(section, d1, theta, std_L)
        P_per_belt = self.calc_power_per_belt(section, d1, inp.drive_speed_rpm)

        effective_power = P_per_belt * K_theta * K_L
        if effective_power <= 0:
            effective_power = 0.1
        n_belts = math.ceil(inp.design_power_kW / effective_power)
        actual_ratio = d2 / d1

        return VBeltResult(
            section=section,
            belt_length_mm=std_L,
            belt_length_designation=designation,
            number_of_belts=n_belts,
            drive_pulley_dia_mm=d1,
            driven_pulley_dia_mm=d2,
            actual_ratio=round(actual_ratio, 3),
            contact_angle_deg=round(theta, 1),
        )
