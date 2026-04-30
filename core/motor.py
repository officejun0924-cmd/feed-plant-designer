import math
from models.input_models import (
    ScrewConveyorInput, BucketElevatorInput, MixerPelletizerInput,
    GrinderHammerMillInput, FanBlowerInput,
)
from models.result_models import MotorResult
from app.config import IEC_MOTOR_SERIES


class MotorCalculator:

    def calc_screw_conveyor_power(self, inp: ScrewConveyorInput) -> float:
        """KS B 6852 / CEMA 공식
        P_total = P_horizontal + P_vertical
        P_h = (Q * L_h * f_m * f) / (367 * eta)
        P_v = (Q * H) / (367 * eta)
        """
        theta = math.radians(inp.inclination_deg)
        L_h = inp.length_m * math.cos(theta)
        H = inp.length_m * math.sin(theta)
        eta = inp.drive_efficiency

        P_h = (inp.capacity_tph * L_h * inp.material_factor * inp.friction_factor) / (367.0 * eta)
        P_v = (inp.capacity_tph * H) / (367.0 * eta) if H > 0 else 0.0
        return (P_h + P_v) * inp.safety_factor

    def calc_bucket_elevator_power(self, inp: BucketElevatorInput) -> float:
        """P [kW] = (Q * H) / (367 * eta)"""
        P = (inp.capacity_tph * inp.lift_height_m) / (367.0 * inp.drive_efficiency)
        return P * inp.safety_factor

    def calc_mixer_power(self, inp: MixerPelletizerInput) -> float:
        """Newton 교반 동력 수: P = Np * rho * n^3 * D^5  [W → kW]"""
        n_rps = inp.shaft_speed_rpm / 60.0
        P_W = inp.mixing_factor * inp.material_density * (n_rps ** 3) * (inp.mixer_diameter_m ** 5)
        P_kW = P_W / (1000.0 * inp.drive_efficiency)
        return P_kW * inp.safety_factor

    def calc_hammermill_power(self, inp: GrinderHammerMillInput) -> float:
        """Bond 분쇄 법칙: W = Wi * (10/√P80 - 10/√F80) [kWh/t]
        F80, P80: mm → μm 변환
        """
        F80_um = inp.feed_size_mm * 1000.0
        P80_um = inp.product_size_mm * 1000.0
        W = inp.material_hardness * (10.0 / math.sqrt(P80_um) - 10.0 / math.sqrt(F80_um))
        W = max(W, 0.0)
        P_kW = W * inp.capacity_tph / 3.6  # kWh/t * t/hr / 3.6 = kW... 실제: W[kWh/t]*Q[t/h] = kW directly? no
        # W [kWh/t] * Q [t/h] = kWh/h = kW (1 kWh/h = 1 kW) → direct
        P_kW = W * inp.capacity_tph / inp.drive_efficiency
        return P_kW * inp.safety_factor

    def calc_fan_power(self, inp: FanBlowerInput) -> float:
        """P_shaft [kW] = (Q [m³/s] * ΔP [Pa]) / (eta_fan * eta_drive * 1000)"""
        Q_m3s = inp.flow_rate_m3h / 3600.0
        P = (Q_m3s * inp.static_pressure_pa) / (inp.fan_efficiency * inp.drive_efficiency * 1000.0)
        return P * inp.safety_factor

    def select_standard_motor(self, required_kW: float) -> MotorResult:
        """IEC 표준 용량 계열에서 필요 동력 이상 최소 용량 선정 후 DB 조회"""
        from database.db_loader import DBLoader
        motors = DBLoader.get_motor_db()

        candidates = [m for m in motors if m["rated_kW"] >= required_kW]
        if not candidates:
            candidates = [max(motors, key=lambda m: m["rated_kW"])]
        selected = min(candidates, key=lambda m: m["rated_kW"])

        return MotorResult(
            required_power_kW=round(required_kW, 3),
            selected_motor_kW=selected["rated_kW"],
            motor_model=selected["model"],
            iec_frame=selected["frame"],
            rated_rpm=selected["rated_rpm"],
            rated_current_A=selected["current_A_400V"],
            rated_torque_Nm=selected["torque_Nm"],
            efficiency_pct=selected["efficiency_pct"],
            shaft_dia_mm=selected["shaft_dia_mm"],
        )
