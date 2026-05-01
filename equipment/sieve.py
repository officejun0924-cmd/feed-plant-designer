"""Sieve(체) 설계 계산기
핸드북 Chapter 14 경험식:
  Q = (k·l·m·n·o·p) × ρ' × a × q
  q: 진동체 1 m² 당 기준처리능력 (표14-1)
  진동 모터: P ≈ 0.75 kW/m² × 체 면적 (실무 기준)
"""
from models.input_models import SieveInput, BearingInput, ShaftInput, ReducerInput, VBeltInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, VBeltSelector

# 표14-1: 체 구멍 크기 → 기준 처리능력 q (m³/hr/m²)
_Q_TABLE = [
    (0.16, 1.9), (0.2, 2.2), (0.3, 2.5), (0.4, 2.8), (0.6, 3.2),
    (0.8, 3.7), (1.17, 4.4), (2.0, 5.5), (3.15, 7.0), (5.0, 11.0),
    (8.0, 17.0), (10.0, 19.0), (16.0, 25.5), (20.0, 28.0), (25.0, 31.0),
    (31.5, 34.0), (40.0, 38.0), (50.0, 42.0), (80.0, 56.0), (100.0, 63.0),
]


def _lookup_q(opening_mm: float) -> float:
    """체 구멍 크기에 따른 기준처리능력 q (m³/hr/m²) — 선형 보간"""
    if opening_mm <= _Q_TABLE[0][0]:
        return _Q_TABLE[0][1]
    if opening_mm >= _Q_TABLE[-1][0]:
        return _Q_TABLE[-1][1]
    for i in range(len(_Q_TABLE) - 1):
        x0, y0 = _Q_TABLE[i]
        x1, y1 = _Q_TABLE[i + 1]
        if x0 <= opening_mm <= x1:
            t = (opening_mm - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return 5.0


def calculate(inp: SieveInput,
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

    # ── Sieve 처리 능력 계산 ─────────────────────────────────
    q_base = _lookup_q(inp.sieve_opening_mm)   # m³/hr/m²

    # 종합 수정계수
    K_total = (inp.k_factor * inp.l_factor * inp.m_factor *
               inp.n_factor * inp.o_factor * inp.p_factor)

    # 설계 처리량 (Ton/hr)
    Q_design = K_total * inp.material_density * inp.sieve_area_m2 * q_base

    notes.append(f"■ 체 구멍 {inp.sieve_opening_mm} mm → q = {q_base:.1f} m³/hr/m²")
    notes.append(f"■ 종합 수정계수 K = {K_total:.3f}")
    notes.append(f"■ 설계 처리 능력: {Q_design:.1f} Ton/hr")
    notes.append(f"■ 목표 처리량: {inp.capacity_tph} Ton/hr")

    if Q_design < inp.capacity_tph:
        shortage = inp.capacity_tph / Q_design
        notes.append(f"⚠ 처리량 부족! 체 면적 ×{shortage:.2f} 배 확대 또는 2단 병렬 검토")
    else:
        notes.append(f"✓ 체 면적 {inp.sieve_area_m2} m² — 처리량 여유율 "
                     f"{(Q_design / inp.capacity_tph - 1) * 100:.0f}%")

    # 경사각 검토
    if inp.inclination_deg < 10 or inp.inclination_deg > 20:
        notes.append(f"ℹ 경사각 {inp.inclination_deg}° — 일반 권장 10~20°")

    # ── 진동 모터 동력 ─────────────────────────────────────
    P_kW = motor_calc.calc_sieve_power(inp)
    motor_result = motor_calc.select_standard_motor(P_kW)

    # 진동체 진동수 (통상 900~1500 rpm)
    vib_rpm = 1000.0

    b_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=vib_rpm,
        desired_life_hr=bearing_inp.desired_life_hr,
        bearing_type=bearing_inp.bearing_type,
        reliability=bearing_inp.reliability,
    )
    bearing_drive  = bearing_calc.select_bearing(b_adj, min_bore_mm=motor_result.shaft_dia_mm)
    bearing_driven = bearing_calc.select_bearing(b_adj, min_bore_mm=motor_result.shaft_dia_mm)

    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(vib_rpm, 1)
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
        output_speed_rpm=vib_rpm,
        service_factor=reducer_inp.service_factor,
    )
    reducer_result = reducer_sel.select_reducer(r_adj)

    vb_adj = VBeltInput(
        design_power_kW=motor_result.selected_motor_kW,
        drive_speed_rpm=motor_result.rated_rpm,
        driven_speed_rpm=vib_rpm,
        center_distance_m=vbelt_inp.center_distance_m,
        section=vbelt_inp.section,
    )
    vbelt_result = vbelt_sel.select_vbelt(vb_adj)

    return EquipmentResult(
        equipment_type="체 (Sieve)",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        vbelt=vbelt_result,
        calculation_notes=notes,
    )
