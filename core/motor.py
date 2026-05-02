import math
from models.input_models import (
    ScrewConveyorInput, BucketElevatorInput, MixerPelletizerInput,
    GrinderHammerMillInput, FanBlowerInput,
    BeltConveyorInput, FlowConveyorInput, DragConveyorInput,
    BagFilterInput, CycloneInput, RotaryValveInput, SieveInput,
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
        rho_kgm3 = inp.specific_gravity * 1000.0   # t/m³ → kg/m³
        P_W = inp.mixing_factor * rho_kgm3 * (n_rps ** 3) * (inp.mixer_diameter_m ** 5)
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

    # ── 추가 장비 계산 (2026.05 핸드북 기반) ─────────────────────────────

    # 표 1-9: (f, l0) — Roller 조건별
    _BELT_F_TABLE = {
        "보통": (0.03,  49.0),
        "양호": (0.022, 66.0),
        "내림": (0.012, 156.0),
    }

    # 표 1-10: Belt 폭(mm) → W(kg/m) 운동부 중량
    _BELT_W_TABLE = {
        400: 22.4, 450: 28.0, 500: 30.0, 600: 35.5,
        750: 53.0, 900: 63.0, 1000: 69.0, 1050: 80.0,
        1200: 90.0, 1400: 112.0, 1600: 125.0,
        1800: 150.0, 2000: 160.0, 2200: 200.0,
    }

    @classmethod
    def lookup_belt_W(cls, belt_width_mm: float) -> float:
        """표1-10: Belt 폭 → W (kg/m) — 가장 가까운 규격으로 올림 선택"""
        widths = sorted(cls._BELT_W_TABLE.keys())
        for w in widths:
            if belt_width_mm <= w:
                return cls._BELT_W_TABLE[w]
        return cls._BELT_W_TABLE[widths[-1]]

    def calc_belt_conveyor_power(self, inp: BeltConveyorInput) -> float:
        """핸드북 Ch.1 표1-9/1-10: P = P1+P2+P3,  Pm = P/η
        P1 = 0.06 × f × W × v × (l+l0) / 367   [무부하 동력, kW]
        P2 = f × Qt × (l+l0) / 367              [수평부하 동력, kW]
        P3 = ±h × Qt / 367                       [수직부하 동력, kW]
        f, l0: 표1-9 roller_condition 기준 자동조회
        W:     표1-10 belt_width_mm 기준 자동조회 (auto_W=True)
        """
        # 표1-9 자동조회
        f, l0 = self._BELT_F_TABLE.get(inp.roller_condition, (0.022, 66.0))

        # 표1-10 자동조회
        W = self.lookup_belt_W(inp.belt_width_mm) if inp.auto_W else inp.moving_parts_W

        theta = math.radians(inp.inclination_deg)
        l_h = inp.conveyor_length_m * math.cos(theta)   # 수평 거리 (m)
        h   = inp.conveyor_length_m * math.sin(theta)   # 수직 높이 (m)
        eff_len = l_h + l0

        P1 = 0.06 * f * W * inp.belt_speed_mpm * eff_len / 367.0
        P2 = f * inp.capacity_tph * eff_len / 367.0
        P3 = h * inp.capacity_tph / 367.0
        P  = P1 + P2 + P3
        Pm = P / inp.drive_efficiency
        return Pm * inp.safety_factor

    def calc_flow_conveyor_power(self, inp: FlowConveyorInput) -> float:
        """핸드북 3장: H [HP] = E × L × Qt / 367
        경사 포함: L → 수평거리 L, H_height 추가
        """
        theta = math.radians(inp.inclination_deg)
        l_h = inp.conveyor_length_m * math.cos(theta)
        h   = inp.conveyor_length_m * math.sin(theta) + inp.height_m

        H_HP = (inp.E_constant * l_h * inp.capacity_tph / 367.0
                + h * inp.capacity_tph / 367.0)
        # 1 HP = 0.7457 kW
        P_kW = H_HP * 0.7457 / inp.drive_efficiency
        return P_kW * inp.safety_factor

    def calc_drag_conveyor_power(self, inp: DragConveyorInput) -> float:
        """핸드북 4장:
        수평: H = Qt × F × L × (1.2 + 0.3N) / (300 × E)
        경사: H = Qt × (1.2 + 0.3N) × (F×L + H) / (300 × E)  [HP]
        """
        N_coef = 1.2 + 0.3 * inp.num_outlets
        L = inp.conveyor_length_m
        H_h = inp.conveyor_height_m
        E = inp.mechanical_efficiency
        F = inp.friction_factor_F
        Qt = inp.capacity_tph

        if H_h > 0:
            H_HP = Qt * N_coef * (F * L + H_h) / (300.0 * E)
        else:
            H_HP = Qt * F * L * N_coef / (300.0 * E)

        P_kW = H_HP * 0.7457 / inp.drive_efficiency
        return P_kW * inp.safety_factor

    def calc_bag_filter_fan_power(self, inp: BagFilterInput) -> float:
        """Bag Filter 시스템 Fan 동력 계산 (기존 Fan 공식 활용)
        Pm = (Q [m³/s] × ΔP [Pa]) / (η_fan × η_drive × 1000)
        """
        Q_m3s = inp.air_volume_m3min / 60.0
        P = (Q_m3s * inp.static_pressure_pa) / (inp.fan_efficiency * inp.drive_efficiency * 1000.0)
        return P * inp.safety_factor

    def calc_cyclone_fan_power(self, inp: CycloneInput) -> float:
        """Cyclone 시스템 Fan 동력 계산
        ΔP [mmH2O] = λ × Va² / (2g) × γ × 10³
        ΔP [Pa]    = ΔP [mmH2O] × 9.81
        """
        g = 9.8
        gamma_kgm3 = 1.2  # 공기 밀도 kg/m³
        dP_mmH2O = inp.pressure_loss_coef * (inp.inlet_velocity_msec ** 2) / (2 * g) * gamma_kgm3
        dP_Pa = dP_mmH2O * 9.81
        Q_m3s = inp.air_volume_m3min / 60.0
        P = (Q_m3s * dP_Pa) / (inp.fan_efficiency * inp.drive_efficiency * 1000.0)
        return P * inp.safety_factor

    def calc_rotary_valve_power(self, inp: RotaryValveInput) -> float:
        """Rotary Valve 구동 동력 — 경험식 근사
        로터 직경·길이·회전수 기반 토크 추정 후 모터 동력 산출
        T ≈ 0.05 × D² × L × γ × N [N·m] (실무 경험식)
        P = T × N_rps × 2π / 1000  [kW]
        """
        D_m = inp.rotor_diameter_mm / 1000.0
        gamma_kgm3 = inp.material_density * 1000.0  # t/m³ → kg/m³
        # 토크 근사: 재료 저항 + 공기 누설 저항
        T_Nm = 0.06 * (D_m ** 2) * inp.rotor_length_m * gamma_kgm3 * inp.rotation_speed_rpm / 10.0
        T_Nm = max(T_Nm, 2.0)  # 최소 토크
        n_rps = inp.rotation_speed_rpm / 60.0
        P_kW = T_Nm * n_rps * 2 * math.pi / (1000.0 * inp.drive_efficiency)
        return max(P_kW * inp.safety_factor, 0.37)  # 최소 0.37 kW

    def calc_sieve_power(self, inp: SieveInput) -> float:
        """Sieve(체) 진동 모터 동력 — 실무 경험식
        P ≈ 0.75 kW/m² × 체 면적 (사료용 진동체 기준)
        """
        P_kW = 0.75 * inp.sieve_area_m2 / inp.drive_efficiency
        return P_kW * inp.safety_factor

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
