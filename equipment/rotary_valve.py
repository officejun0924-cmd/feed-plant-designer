"""Rotary Valve (로타리 피더) 통합 계산기
참조 엑셀 준거 공식:
  1) 1회전당 이송 체적:  Vrev = Apocket × L × npocket  [m³/rev]
  2) 체적 용량:         Qvol = Vrev × N × 60 × η       [m³/h]
  3) 질량 용량:         Qt   = ρ × Qvol                 [T/H]
  ※ Apocket = 0이면 로터 기하학에서 자동 계산
     Apocket = π/4 × (D² - d²) / npocket × (1 - X)
"""
import math
from models.input_models import RotaryValveInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS

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
              chain_inp: ChainInput) -> EquipmentResult:

    notes = []
    motor_calc   = MotorCalculator()
    bearing_calc = BearingCalculator()
    shaft_des    = ShaftDesigner()
    reducer_sel  = ReducerSelector()
    chain_sel    = ChainSelector()

    D_m = inp.rotor_diameter_mm / 1000.0
    d_m = inp.shaft_diameter_mm / 1000.0
    L   = inp.rotor_length_m
    N   = inp.rotation_speed_rpm
    rho = inp.material_density
    np_ = inp.num_pockets
    eta = inp.volumetric_efficiency
    X   = inp.clearance_ratio

    # ── 1) 포켓 단면적 Apocket ───────────────────────────────────────────
    if inp.pocket_area_m2 > 0:
        A_pocket = inp.pocket_area_m2
        notes.append(f"■ 포켓 단면적 Apocket (입력값) = {A_pocket:.6f}  m²"
                     f"  ({A_pocket * 1e6:.1f}  mm²)")
    else:
        A_total  = math.pi / 4.0 * (D_m**2 - d_m**2)
        A_pocket = A_total / np_ * (1.0 - X)
        notes.append("■ 포켓 단면적 자동 계산 (기하학)")
        notes.append(f"   A_total = π/4 × (D² - d²) = {A_total:.6f}  m²")
        notes.append(f"   Apocket = A_total / npocket × (1-X)")
        notes.append(f"           = {A_total:.6f} / {np_} × (1 - {X})")
        notes.append(f"           = {A_pocket:.6f}  m²  ({A_pocket*1e6:.0f}  mm²)")

    # ── 2) 1회전당 이송 체적 ──────────────────────────────────────────────
    V_pocket = A_pocket * L
    Vrev     = V_pocket * np_

    notes.append("■ 1) 1회전당 이송 체적")
    notes.append(f"   Vpocket = Apocket × L = {A_pocket:.6f} × {L}")
    notes.append(f"           = {V_pocket:.6f}  m³/pocket  ({V_pocket*1000:.4f}  ℓ/pocket)")
    notes.append(f"   Vrev = Vpocket × npocket = {V_pocket:.6f} × {np_}")
    notes.append(f"        = {Vrev:.6f}  m³/rev")

    # ── 3) 체적·질량 용량 ─────────────────────────────────────────────────
    Qvol = Vrev * N * 60.0 * eta
    Qt   = rho  * Qvol

    notes.append("■ 2) 체적 용량 Qvol")
    notes.append(f"   Qvol = Vrev × N × 60 × η")
    notes.append(f"        = {Vrev:.6f} × {N:.4f} × 60 × {eta}")
    notes.append(f"        = {Qvol:.3f}  m³/h")
    notes.append("■ 3) 질량 용량 Qt")
    notes.append(f"   Qt = ρ × Qvol = {rho} × {Qvol:.3f}")
    notes.append(f"      = {Qt:.3f}  T/H")

    # 참고 DB 최대 회전수 확인
    D_mm = inp.rotor_diameter_mm
    nearest_d = min(_ROTOR_DB.keys(), key=lambda k: abs(k - D_mm))
    max_rpm_ref, v_per_rev = _ROTOR_DB[nearest_d]
    notes.append(f"■ 참고 최대 회전수 (Ø{nearest_d}): {max_rpm_ref} rpm")
    notes.append(f"■ 참고 배출용량/rev (Ø{nearest_d}): {v_per_rev*1000:.1f}  ℓ/rev")
    if N > 40:
        notes.append("   ⚠ 회전수 40 rpm 초과 — 원료 안정 공급에 불리, 30 rpm 권장")
    if N > max_rpm_ref:
        notes.append(f"   ⚠ 회전수 {N:.1f} rpm이 최대 허용 {max_rpm_ref} rpm 초과!")

    # ── 모터 선정 ────────────────────────────────────────────────────────
    P_kW = motor_calc.calc_rotary_valve_power(inp)
    motor_result = motor_calc.select_standard_motor(P_kW)

    # ── 베어링 선정 ────────────────────────────────────────────────────────
    b_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=N,
        desired_life_hr=bearing_inp.desired_life_hr,
        bearing_type=bearing_inp.bearing_type,
        reliability=bearing_inp.reliability,
    )
    bearing_drive  = bearing_calc.select_bearing(b_adj, min_bore_mm=motor_result.shaft_dia_mm)
    bearing_driven = bearing_calc.select_bearing(b_adj, min_bore_mm=motor_result.shaft_dia_mm)

    # ── 샤프트 설계 ───────────────────────────────────────────────────────
    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(N, 1)
    s_adj = ShaftInput(
        torque_Nm=T_Nm,
        bending_moment_Nm=shaft_inp.bending_moment_Nm,
        material=shaft_inp.material,
        safety_factor=shaft_inp.safety_factor,
        km_factor=shaft_inp.km_factor,
        kt_factor=shaft_inp.kt_factor,
    )
    shaft_result = shaft_des.design(s_adj)

    # ── 감속기 선정 ───────────────────────────────────────────────────────
    r_adj = ReducerInput(
        input_power_kW=motor_result.selected_motor_kW,
        input_speed_rpm=motor_result.rated_rpm,
        output_speed_rpm=N,
        service_factor=reducer_inp.service_factor,
        brand=reducer_inp.brand,
    )
    reducer_result = reducer_sel.select_reducer(r_adj)

    # ── 체인 선정 ─────────────────────────────────────────────────────────
    chain_result = chain_sel.select_chain_with_rpm(
        chain_inp,
        design_power_kW=motor_result.selected_motor_kW,
        reducer_brand=reducer_inp.brand,
        output_rpm=motor_result.rated_rpm / max(reducer_result.ratio, 1),
    )
    if reducer_inp.brand in DIRECT_COUPLING_BRANDS:
        notes.append(f"ℹ {reducer_inp.brand} 감속기 — 직결 구동 (체인 없음)")

    return EquipmentResult(
        equipment_type="로터리 밸브 (로타리 피더)",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
