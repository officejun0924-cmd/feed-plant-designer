"""Sieve(체) 설계 계산기
핸드북 Chapter 14 경험식:
  1) 기준 처리능력: q [m³/hr/m²] — 표14-1 체 구멍 크기 기준 (선형 보간)
  2) 종합 수정계수: K = k × l × m × n × o × p
  3) 설계 처리 능력: Q = K × ρ' × a × q  [T/hr]
     a: 체 면적(m²), ρ': 외관상 비중(t/m³)
  4) 필요 체 면적:  a_req = Qt / (K × ρ' × q)  [m²]
  5) 진동 모터 동력: P ≈ 0.75 kW/m² × a × Sf / η
"""
from models.input_models import SieveInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS

# 표14-1: 체 구멍 크기(mm) → 기준 처리능력 q (m³/hr/m²)
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
              chain_inp: ChainInput) -> EquipmentResult:

    notes = []
    motor_calc   = MotorCalculator()
    bearing_calc = BearingCalculator()
    shaft_des    = ShaftDesigner()
    reducer_sel  = ReducerSelector()
    chain_sel    = ChainSelector()

    Qt    = inp.capacity_tph
    a     = inp.sieve_area_m2
    rho   = inp.material_density        # t/m³
    eta   = inp.drive_efficiency
    Sf    = inp.safety_factor

    # ── 1) 표14-1 기준 처리능력 조회 ─────────────────────────────────────────
    q_base = _lookup_q(inp.sieve_opening_mm)

    notes.append("■ 1) 표14-1 기준 처리능력 조회")
    notes.append(f"   체 구멍 크기 = {inp.sieve_opening_mm} mm")
    notes.append(f"   기준 처리능력 q = {q_base:.2f}  m³/hr/m²  (선형 보간)")

    # ── 2) 종합 수정계수 ─────────────────────────────────────────────────────
    k = inp.k_factor
    l = inp.l_factor
    m = inp.m_factor
    n = inp.n_factor
    o = inp.o_factor
    p = inp.p_factor
    K_total = k * l * m * n * o * p

    notes.append("■ 2) 종합 수정계수 K = k × l × m × n × o × p")
    notes.append(f"   k(입도)={k:.2f} × l(형상)={l:.2f} × m(수분)={m:.2f}")
    notes.append(f"   × n(밀도)={n:.2f} × o(부착)={o:.2f} × p(공급균일도)={p:.2f}")
    notes.append(f"   K = {K_total:.3f}")

    # ── 3) 설계 처리 능력 ──────────────────────────────────────────────────
    Q_design = K_total * rho * a * q_base

    notes.append("■ 3) 설계 처리 능력 Q")
    notes.append(f"   Q = K × ρ' × a × q")
    notes.append(f"     = {K_total:.3f} × {rho} × {a} × {q_base:.2f}")
    notes.append(f"     = {Q_design:.2f}  T/hr")
    notes.append(f"   목표 처리량 Qt = {Qt:.2f}  T/hr")

    # ── 4) 필요 체 면적 역산 ────────────────────────────────────────────────
    denom = K_total * rho * q_base
    a_req = Qt / denom if denom > 0 else 0.0

    notes.append("■ 4) 필요 체 면적 a_req")
    notes.append(f"   a_req = Qt / (K × ρ' × q) = {Qt:.2f} / ({K_total:.3f} × {rho} × {q_base:.2f})")
    notes.append(f"         = {a_req:.2f}  m²  (설계 체 면적: {a} m²)")

    if Q_design < Qt:
        shortage = Qt / Q_design
        notes.append(f"   ⚠ 처리량 부족! 체 면적 ×{shortage:.2f} 배 확대 또는 2단 병렬 검토")
    else:
        notes.append(f"   ✓ 체 면적 {a} m² — 처리량 여유율 {(Q_design/Qt - 1)*100:.0f}%")

    if inp.inclination_deg < 10 or inp.inclination_deg > 20:
        notes.append(f"   ℹ 경사각 {inp.inclination_deg:.0f}° — 일반 권장 10~20°")

    # ── 5) 진동 모터 동력 ─────────────────────────────────────────────────
    P_kW_base = 0.75 * a / eta
    P_req_kW  = P_kW_base * Sf

    notes.append("■ 5) 진동 모터 동력")
    notes.append(f"   P = 0.75 kW/m² × a / η = 0.75 × {a} / {eta}")
    notes.append(f"     = {P_kW_base:.3f}  kW")
    notes.append(f"   안전율 적용: {P_kW_base:.3f} × {Sf} = {P_req_kW:.3f}  kW")

    # ── 모터 선정 ─────────────────────────────────────────────────────────
    motor_result = motor_calc.select_standard_motor(P_req_kW)

    vib_rpm = 1000.0

    # ── 비틀림 모멘트 ────────────────────────────────────────────────────────
    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(vib_rpm, 1)
    notes.append(f"■ 진동 회전수 = {vib_rpm:.0f} rpm")
    notes.append(f"■ 비틀림 모멘트 T = 9550 × {motor_result.selected_motor_kW} / {vib_rpm:.0f} = {T_Nm:.1f}  N·m")

    # ── 베어링 선정 ──────────────────────────────────────────────────────────
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

    # ── 샤프트 설계 ──────────────────────────────────────────────────────────
    s_adj = ShaftInput(
        torque_Nm=T_Nm,
        bending_moment_Nm=shaft_inp.bending_moment_Nm,
        material=shaft_inp.material,
        safety_factor=shaft_inp.safety_factor,
        km_factor=shaft_inp.km_factor,
        kt_factor=shaft_inp.kt_factor,
    )
    shaft_result = shaft_des.design(s_adj)

    # ── 감속기 선정 ──────────────────────────────────────────────────────────
    r_adj = ReducerInput(
        input_power_kW=motor_result.selected_motor_kW,
        input_speed_rpm=motor_result.rated_rpm,
        output_speed_rpm=vib_rpm,
        service_factor=reducer_inp.service_factor,
        brand=reducer_inp.brand,
    )
    reducer_result = reducer_sel.select_reducer(r_adj)

    # ── 체인 선정 ─────────────────────────────────────────────────────────────
    chain_result = chain_sel.select_chain_with_rpm(
        chain_inp,
        design_power_kW=motor_result.selected_motor_kW,
        reducer_brand=reducer_inp.brand,
        output_rpm=motor_result.rated_rpm / max(reducer_result.ratio, 1),
    )
    if reducer_inp.brand in DIRECT_COUPLING_BRANDS:
        notes.append(f"ℹ {reducer_inp.brand} 감속기 — 직결 구동 (체인 없음)")

    return EquipmentResult(
        equipment_type="체 (Sieve)",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
