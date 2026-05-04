"""스크류 컨베이어 통합 계산기
참조 엑셀 준거 공식:
  1) 운반 용량:  Qt = 47.1 × Φ × (D² - d²) × P × N × γ  [T/hr]
  2) 필요 회전수: N_req = 4 × Qt / (60 × Φ × π × D² × P × γ)
  3) 소요 동력:  H[HP] = (C × Qt × ℓ + Qt × h) / 270 × Sf
  4) Torque:    T = 71620 × H / N  [kg·cm]
  5) 추력:      F = H × 4500 / V  [kg]   (V = P × N [m/min])
"""
import math
from models.input_models import ScrewConveyorInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS


def calculate(inp: ScrewConveyorInput,
              bearing_inp: BearingInput,
              shaft_inp: ShaftInput,
              reducer_inp: ReducerInput,
              chain_inp: ChainInput) -> EquipmentResult:

    notes = []
    motor_calc    = MotorCalculator()
    bearing_calc  = BearingCalculator()
    shaft_des     = ShaftDesigner()
    reducer_sel   = ReducerSelector()
    chain_sel     = ChainSelector()

    D   = inp.screw_diameter_m
    d   = inp.shaft_outer_diameter_m
    P   = inp.screw_pitch_m
    N   = inp.screw_speed_rpm
    phi = inp.fill_efficiency
    rho = inp.specific_gravity
    L   = inp.length_m
    C   = inp.material_factor
    Sf  = inp.safety_factor
    eta = inp.drive_efficiency

    # ── 1) 운반 용량 Qt ───────────────────────────────────────────────────
    # Qt = 47.1 × Φ × (D² - d²) × P × N × γ
    Qt_calc = 47.1 * phi * (D**2 - d**2) * P * N * rho

    notes.append("■ 1) 스크류 운반 용량")
    notes.append(f"   Qt = 47.1 × Φ × (D² - d²) × P × N × γ")
    notes.append(f"      = 47.1 × {phi} × ({D}² - {d}²) × {P} × {N} × {rho}")
    notes.append(f"      = {Qt_calc:.2f}  Ton/Hr")

    Qt = inp.capacity_tph   # 설계 운반 용량 (입력값)
    notes.append(f"   설계 운반 용량 Qt = {Qt:.2f}  Ton/Hr")
    if Qt_calc > 0:
        ratio = Qt / Qt_calc
        if ratio > 1.15:
            notes.append(f"   ⚠ 설계 용량이 이론 값 대비 {ratio:.1%} — 스크류 직경·회전수 재검토")
        elif ratio < 0.50:
            notes.append(f"   ℹ 여유율 {(1/ratio - 1)*100:.0f}% — 직경 축소 가능")
        else:
            notes.append(f"   ✓ 이론 용량 {Qt_calc:.2f} T/hr 대비 여유율 {(Qt_calc/Qt - 1)*100:.0f}%")

    # ── 2) 필요 회전수 ────────────────────────────────────────────────────
    # N_req = 4 × Qt / (60 × Φ × π × D² × P × γ)
    denom_N = 60.0 * phi * math.pi * (D**2) * P * rho
    N_req = (4.0 * Qt / denom_N) if denom_N > 0 else N
    notes.append("■ 2) 필요 회전수 N_req")
    notes.append(f"   N = 4 × Qt / (60 × Φ × π × D² × P × γ)")
    notes.append(f"     = 4 × {Qt:.3f} / (60 × {phi} × π × {D}² × {P} × {rho})")
    notes.append(f"     = {N_req:.2f}  r.p.m   (설계 N = {N:.0f} rpm)")

    # ── 3) 소요 동력 H ────────────────────────────────────────────────────
    # H[HP] = (C × Qt × ℓ + Qt × h) / 270 × Sf
    theta  = math.radians(inp.inclination_deg)
    H_vert = L * math.sin(theta)
    h_eff  = max(1.0, H_vert)        # 수평 시 최솟값 1

    H_base_HP = (C * Qt * L + Qt * h_eff) / 270.0
    H_req_HP  = H_base_HP * Sf
    P_req_kW  = H_req_HP * 0.7457 / eta

    notes.append("■ 3) 소요 동력 H")
    notes.append(f"   H = (C × Qt × ℓ + Qt × h) / 270")
    notes.append(f"     = ({C} × {Qt:.2f} × {L} + {Qt:.2f} × {h_eff:.1f}) / 270")
    notes.append(f"     = {H_base_HP:.3f}  HP")
    notes.append(f"   안전율 적용 : {H_base_HP:.3f} × {Sf} = {H_req_HP:.3f}  HP")
    notes.append(f"   → 소요 동력  P = {H_req_HP:.3f} HP × 0.7457 / {eta} = {P_req_kW:.3f}  kW")

    # ── 4) 비틀림 모멘트 T ────────────────────────────────────────────────
    # T = 71620 × H / N  [kg·cm]
    T_kgcm = 71620.0 * H_req_HP / max(N, 1.0)
    notes.append("■ 4) 비틀림 모멘트 T")
    notes.append(f"   T = 71620 × H / N = 71620 × {H_req_HP:.3f} / {N:.0f}")
    notes.append(f"     = {T_kgcm:.2f}  kg·cm")

    # ── 5) 운반 속도 V 및 추력 F ─────────────────────────────────────────
    # V = P × N  [m/min]
    V_mpm = P * N
    # F = H × 4500 / V  [kg]
    F_kg  = H_req_HP * 4500.0 / max(V_mpm, 1.0)
    notes.append("■ 5) 운반 속도 및 추력")
    notes.append(f"   V = P × N = {P} × {N:.0f} = {V_mpm:.2f}  m/min")
    notes.append(f"   F = H × 4500 / V = {H_req_HP:.3f} × 4500 / {V_mpm:.2f}")
    notes.append(f"     = {F_kg:.2f}  kg")

    if inp.fill_efficiency > 0.45:
        notes.append(f"   ⚠ 충만효율 {inp.fill_efficiency:.2f} > 0.45 — 재료 흘러내림 위험 검토")
    if inp.inclination_deg > 20:
        notes.append("   ⚠ 경사각 20° 초과 — 스크류 직경 확대 검토 권장")

    # ── 모터 선정 ────────────────────────────────────────────────────────
    motor_result = motor_calc.select_standard_motor(P_req_kW)

    # ── 베어링 선정 ────────────────────────────────────────────────────────
    btype = bearing_inp.bearing_type
    b_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=N,
        desired_life_hr=bearing_inp.desired_life_hr,
        bearing_type=btype,
        reliability=bearing_inp.reliability,
    )
    if btype in ("UCF", "UCP", "UCFC"):
        bearing_drive  = bearing_calc.select_ucf_bearing(b_adj, btype, motor_result.shaft_dia_mm)
        bearing_driven = bearing_calc.select_ucf_bearing(b_adj, btype, motor_result.shaft_dia_mm)
    else:
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
        output_rpm=N,
    )
    if reducer_inp.brand in DIRECT_COUPLING_BRANDS:
        notes.append(f"ℹ {reducer_inp.brand} 감속기 — 직결 구동 (체인 없음)")

    return EquipmentResult(
        equipment_type="스크류 컨베이어",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
