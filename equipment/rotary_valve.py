"""Rotary Valve 배출 용량 및 구동 동력 계산기
핸드북 Chapter 11 공식:
  용적: W = π × L × (D² - d²) / 4
  배출량(제2식): Q = 0.7 × W × (1-X) × N × 60 × γ  [Ton/hr]
  구동 모터: 경험식 기반 토크 추정
"""
import math
from models.input_models import RotaryValveInput, BearingInput, ShaftInput, ReducerInput, VBeltInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, VBeltSelector

# 표11-1 Rotor 날개 지름별 최대 회전수 및 배출용량
_ROTOR_DB = {
    200: (94, 0.0045),
    250: (82, 0.0093),
    300: (77, 0.015),
    350: (72, 0.025),
    400: (67, 0.030),
    450: (63, 0.051),
    500: (60, 0.086),
}


def calculate(inp: RotaryValveInput,
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

    D_m = inp.rotor_diameter_mm / 1000.0
    d_m = inp.shaft_diameter_mm / 1000.0

    # ── Rotary Valve 배출 용량 계산 ──────────────────────────
    # 용적 W (m³)
    W_volume = math.pi * inp.rotor_length_m * (D_m ** 2 - d_m ** 2) / 4.0

    # 배출량 제2식: Q = 0.7 × W × (1-X) × N × 60 × γ
    Q_calc = 0.7 * W_volume * (1 - inp.clearance_ratio) * inp.rotation_speed_rpm * 60 * inp.material_density

    # 표11-1에서 가장 가까운 Rotor 직경의 최대 회전수 확인
    D_mm = inp.rotor_diameter_mm
    nearest_d = min(_ROTOR_DB.keys(), key=lambda k: abs(k - D_mm))
    max_rpm_ref, v_per_rev = _ROTOR_DB[nearest_d]

    notes.append(f"■ Rotor 용적 W: {W_volume*1000:.2f} ℓ")
    notes.append(f"■ 계산 배출량 Q: {Q_calc:.2f} Ton/hr")
    notes.append(f"■ 참고 최대 회전수 (Ø{nearest_d}): {max_rpm_ref} rpm")
    notes.append(f"■ 참고 배출용량/rev (Ø{nearest_d}): {v_per_rev*1000:.1f} ℓ/rev")

    if inp.rotation_speed_rpm > 40:
        notes.append("⚠ 회전수 40 rpm 초과 — 원료 안정 공급에 불리, 30 rpm 권장")
    if inp.rotation_speed_rpm > max_rpm_ref:
        notes.append(f"⚠ 회전수 {inp.rotation_speed_rpm} rpm이 최대 허용 {max_rpm_ref} rpm 초과!")

    # ── 구동 모터 ───────────────────────────────────────────
    P_kW = motor_calc.calc_rotary_valve_power(inp)
    motor_result = motor_calc.select_standard_motor(P_kW)

    b_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=inp.rotation_speed_rpm,
        desired_life_hr=bearing_inp.desired_life_hr,
        bearing_type=bearing_inp.bearing_type,
        reliability=bearing_inp.reliability,
    )
    bearing_drive  = bearing_calc.select_bearing(b_adj, min_bore_mm=motor_result.shaft_dia_mm)
    bearing_driven = bearing_calc.select_bearing(b_adj, min_bore_mm=motor_result.shaft_dia_mm)

    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(inp.rotation_speed_rpm, 1)
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
        output_speed_rpm=inp.rotation_speed_rpm,
        service_factor=reducer_inp.service_factor,
    )
    reducer_result = reducer_sel.select_reducer(r_adj)

    vb_adj = VBeltInput(
        design_power_kW=motor_result.selected_motor_kW,
        drive_speed_rpm=motor_result.rated_rpm,
        driven_speed_rpm=inp.rotation_speed_rpm,
        center_distance_m=vbelt_inp.center_distance_m,
        section=vbelt_inp.section,
    )
    vbelt_result = vbelt_sel.select_vbelt(vb_adj)

    return EquipmentResult(
        equipment_type="로터리 밸브",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        vbelt=vbelt_result,
        calculation_notes=notes,
    )
