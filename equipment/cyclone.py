"""Cyclone 설계 계산기
핸드북 Chapter 10 공식:
  입구 단면적: A = Qa / (Va × 60)
  압력손실:   ΔP [mmH₂O] = λ × Va² / (2g) × γ_air
  ΔP [Pa]   = ΔP_mmH₂O × 9.81
  Fan 동력:   Pm = (Q [m³/s] × ΔP [Pa]) / (η_fan × η_drive × 1000)
표10-2 표준 치수 비율 (일반 Cyclone 기준 3열):
  몸통직경 D, 유입구 높이 0.5D, 유입구 폭 0.25D,
  가스출구 직경 0.5D, 몸통길이 2.0D, 원추길이 2.0D
"""
import math
from models.input_models import CycloneInput, BearingInput, ShaftInput, ReducerInput, VBeltInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, VBeltSelector

# 표10-2 치수 비율 딕셔너리  {type: (H/D, W/D, Do/D, body_len/D, cone_len/D)}
_CYCLONE_RATIO = {
    "고효율": (0.44, 0.21, 0.4, 1.4, 2.5),
    "일반":   (0.5,  0.25, 0.5, 2.0, 2.0),
    "고용량": (0.8,  0.35, 0.75, 1.7, 2.0),
}


def calculate(inp: CycloneInput,
              bearing_inp: BearingInput,
              shaft_inp: ShaftInput,
              reducer_inp: ReducerInput,
              vbelt_inp: VBeltInput) -> EquipmentResult:

    notes = []
    motor_calc   = MotorCalculator()
    bearing_calc = BearingCalculator()
    shaft_des    = ShaftDesigner()
    reducer_sel  = ReducerSelector()
    vbelt_sel    = VBeltSelector()

    # ── Cyclone 설계 치수 계산 ───────────────────────────────
    Qa = inp.air_volume_m3min          # m³/min
    Va = inp.inlet_velocity_msec       # m/sec

    A_inlet = Qa / (Va * 60.0)        # 입구 단면적 (m²)

    ratio = _CYCLONE_RATIO.get(inp.cyclone_type, _CYCLONE_RATIO["일반"])
    H_ratio, W_ratio, Do_ratio, body_ratio, cone_ratio = ratio

    # 입구 높이 H = H_ratio × D,  폭 W = W_ratio × D
    # A_inlet = H × W = H_ratio × W_ratio × D²  → D = sqrt(A_inlet / (H_ratio × W_ratio))
    D_m = math.sqrt(A_inlet / (H_ratio * W_ratio))

    H_in_m = H_ratio * D_m             # 유입구 높이 (m)
    W_in_m = W_ratio * D_m             # 유입구 폭 (m)
    Do_m   = Do_ratio * D_m            # 가스 출구 직경 (m)
    body_m = body_ratio * D_m          # 몸통 길이 (m)
    cone_m = cone_ratio * D_m          # 원추 길이 (m)
    total_m = body_m + cone_m          # 전체 높이 (m)

    # 압력손실
    g = 9.8
    gamma_air = 1.2   # kg/m³
    dP_mmH2O = inp.pressure_loss_coef * Va ** 2 / (2 * g) * gamma_air
    dP_Pa = dP_mmH2O * 9.81

    notes.append(f"■ Cyclone 몸통 직경 D: {D_m*1000:.0f} mm")
    notes.append(f"■ 유입구: {H_in_m*1000:.0f}(H) × {W_in_m*1000:.0f}(W) mm")
    notes.append(f"■ 가스 출구 직경 Do: {Do_m*1000:.0f} mm")
    notes.append(f"■ 전체 높이: {total_m*1000:.0f} mm (몸통 {body_m*1000:.0f} + 원추 {cone_m*1000:.0f})")
    notes.append(f"■ 압력손실: {dP_mmH2O:.1f} mmH₂O  ({dP_Pa:.0f} Pa)")
    notes.append(f"■ 입구 단면적: {A_inlet:.4f} m²")

    if Va < 7:
        notes.append("⚠ 유입속도 7 m/sec 미만 — 집진 효율 저하 우려")
    if Va > 18:
        notes.append("⚠ 유입속도 18 m/sec 초과 — 압력손실 급증")

    # ── Fan 동력 (Cyclone 시스템 Fan) ───────────────────────
    P_kW = motor_calc.calc_cyclone_fan_power(inp)
    motor_result = motor_calc.select_standard_motor(P_kW)

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
    )
    reducer_result = reducer_sel.select_reducer(r_adj)

    vb_adj = VBeltInput(
        design_power_kW=motor_result.selected_motor_kW,
        drive_speed_rpm=motor_result.rated_rpm,
        driven_speed_rpm=fan_rpm,
        center_distance_m=vbelt_inp.center_distance_m,
        section=vbelt_inp.section,
    )
    vbelt_result = vbelt_sel.select_vbelt(vb_adj)

    return EquipmentResult(
        equipment_type="사이클론",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        vbelt=vbelt_result,
        calculation_notes=notes,
    )
