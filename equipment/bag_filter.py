"""Bag Filter 설계 계산기
핸드북 Chapter 8/9 공식:
  여과포 면적: A = Qa / V
  단위 Bag 면적: A' = π × D × H
  Bag 수량: N = Qa / (V × π × D × H)
  Fan 동력: Pm = (Q [m³/s] × ΔP [Pa]) / (η_fan × η_drive × 1000)
"""
import math
from models.input_models import BagFilterInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS


def calculate(inp: BagFilterInput,
              bearing_inp: BearingInput,
              shaft_inp: ShaftInput,
              reducer_inp: ReducerInput,
              chain_inp: ChainInput) -> EquipmentResult:

    notes = []
    motor_calc   = MotorCalculator()
    bearing_calc = BearingCalculator()
    shaft_des    = ShaftDesigner()
    reducer_sel  = ReducerSelector()
    chain_sel    = ChainSelector()

    # ── 여과포 설계 계산 ──────────────────────────────────
    Qa = inp.air_volume_m3min               # m³/min
    V  = inp.filter_velocity_mmin           # m/min
    D  = inp.bag_diameter_m                 # m
    H  = inp.bag_height_m                   # m

    A_total  = Qa / V                       # 필요 총 여과포 면적 (m²)
    A_unit   = math.pi * D * H             # 단위 Bag 면적 (m²)
    N_bags   = math.ceil(A_total / A_unit)  # Bag 수량 (개, 올림)
    V_actual = Qa / (A_unit * N_bags)       # 실제 여과속도 (m/min)

    # Pulse Valve CV 값 (표9-6: Zone당 여과면적 × 3.5 CV/m²)
    # Zone당 Bag 수 = 15 (일반 기준)
    bags_per_zone = min(15, max(1, N_bags // max(1, round(N_bags / 15))))
    zone_area = A_unit * bags_per_zone
    CV_val = zone_area * 3.5

    notes.append(f"■ 여과포 면적: {A_total:.1f} m²")
    notes.append(f"■ Bag 수량 (Ø{D*1000:.0f}×{H*1000:.0f}H): {N_bags} 개")
    notes.append(f"■ 실제 여과속도: {V_actual:.3f} m/min")
    notes.append(f"■ Pulse Valve CV 참고값: {CV_val:.1f} (Zone당 {bags_per_zone}개 기준)")

    if V_actual > 4.3:
        notes.append("⚠ 여과속도 4.3 m/min 초과 — Bag 수량 증가 권장")
    if V_actual < 1.5:
        notes.append("⚠ 여과속도 1.5 m/min 미만 — Bag 수량 감소 검토 가능")

    # ── Fan 동력 (Bag Filter 시스템 Fan) ───────────────────
    P_kW = motor_calc.calc_bag_filter_fan_power(inp)
    motor_result = motor_calc.select_standard_motor(P_kW)

    # Fan 회전수 추정 (일반적으로 1450 rpm)
    fan_rpm = 1450.0

    b_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=fan_rpm,
        desired_life_hr=bearing_inp.desired_life_hr,
        bearing_type=bearing_inp.bearing_type,
        reliability=bearing_inp.reliability,
    )
    bearing_drive  = bearing_calc.select_bearing(b_adj, min_bore_mm=motor_result.shaft_dia_mm)
    bearing_driven = bearing_calc.select_bearing(b_adj, min_bore_mm=motor_result.shaft_dia_mm)

    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(fan_rpm, 1)
    s_adj = ShaftInput(
        torque_Nm=T_Nm,
        bending_moment_Nm=shaft_inp.bending_moment_Nm,
        material=shaft_inp.material,
        safety_factor=shaft_inp.safety_factor,
        km_factor=shaft_inp.km_factor,
        kt_factor=shaft_inp.kt_factor,
    )
    shaft_result = shaft_des.design(s_adj)

    r_adj = ReducerInput(
        input_power_kW=motor_result.selected_motor_kW,
        input_speed_rpm=motor_result.rated_rpm,
        output_speed_rpm=fan_rpm,
        service_factor=reducer_inp.service_factor,
        brand=reducer_inp.brand,
    )
    reducer_result = reducer_sel.select_reducer(r_adj)

    chain_result = chain_sel.select_chain_with_rpm(
        chain_inp,
        design_power_kW=motor_result.selected_motor_kW,
        reducer_brand=reducer_inp.brand,
        output_rpm=motor_result.rated_rpm / max(reducer_result.ratio, 1),
    )
    if reducer_inp.brand in DIRECT_COUPLING_BRANDS:
        notes.append(f"ℹ {reducer_inp.brand} 감속기 — 직결 구동 (체인 없음)")

    return EquipmentResult(
        equipment_type="백 필터",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
