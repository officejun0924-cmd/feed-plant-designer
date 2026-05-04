"""Flow Conveyor 통합 계산기
핸드북 Chapter 3 공식:
  H [HP] = E × L × Qt / 367           (수평 성분)
  H_vert = h × Qt / 367               (수직 성분)
  H_total = H_horiz + H_vert  [HP]
  P [kW] = H_total × 0.7457 / η_drive × Sf
이론 운반량: Qt_theory = 60 × A × V × γ × φ  [T/hr]
  A: 단면적(m²), V: Chain 속도(m/min), γ: 비중(t/m³), φ: 충만효율
"""
import math
from models.input_models import FlowConveyorInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS


def calculate(inp: FlowConveyorInput,
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
    L     = inp.conveyor_length_m
    E     = inp.E_constant
    V     = inp.chain_speed_mpm         # m/min
    rho   = inp.specific_gravity        # t/m³
    phi   = inp.fill_efficiency
    eta   = inp.drive_efficiency
    Sf    = inp.safety_factor

    # ── 경사 계산 ─────────────────────────────────────────────────────────────
    theta  = math.radians(inp.inclination_deg)
    l_h    = L * math.cos(theta)        # 수평 거리 (m)
    h_vert = L * math.sin(theta) + inp.height_m   # 총 수직 높이 (m)

    # ── 1) 소요 동력 계산 ─────────────────────────────────────────────────────
    H_horiz = E * l_h * Qt / 367.0
    H_vert  = h_vert * Qt / 367.0
    H_total = H_horiz + H_vert
    P_kW_base = H_total * 0.7457 / eta
    P_req_kW  = P_kW_base * Sf

    notes.append("■ 1) 소요 동력 계산 (핸드북 Ch.3)")
    notes.append(f"   수평 성분 H1 = E × L × Qt / 367")
    notes.append(f"              = {E} × {l_h:.2f} × {Qt:.2f} / 367")
    notes.append(f"              = {H_horiz:.3f}  HP")
    notes.append(f"   수직 성분 H2 = h × Qt / 367")
    notes.append(f"              = {h_vert:.2f} × {Qt:.2f} / 367")
    notes.append(f"              = {H_vert:.3f}  HP")
    notes.append(f"   H_total = H1 + H2 = {H_horiz:.3f} + {H_vert:.3f} = {H_total:.3f}  HP")
    notes.append(f"   P = H_total × 0.7457 / η = {H_total:.3f} × 0.7457 / {eta}")
    notes.append(f"     = {P_kW_base:.3f}  kW")
    notes.append(f"   안전율 적용: {P_kW_base:.3f} × {Sf} = {P_req_kW:.3f}  kW")
    notes.append(f"   [E={E}: 사료류 ≈ 3.9, 분체류 ≈ 5.0~6.0]")

    # ── 2) 이론 운반량 ──────────────────────────────────────────────────────
    # Qt_theory = 60 × A × V × γ × φ
    # A 역산: Qt = 60 × A × V × γ × φ → A = Qt / (60 × V × γ × φ)
    denom = 60.0 * V * rho * phi
    A_req = Qt / denom if denom > 0 else 0.0

    notes.append("■ 2) 이론 운반량 및 단면적")
    notes.append(f"   Qt = 60 × A × V × γ × φ")
    notes.append(f"   필요 단면적 A = Qt / (60 × V × γ × φ)")
    notes.append(f"                = {Qt:.2f} / (60 × {V:.1f} × {rho} × {phi})")
    notes.append(f"                = {A_req:.4f}  m²  ({A_req*1e6:.0f}  mm²)")
    notes.append(f"   Chain 속도 V = {V:.1f}  m/min,  충만효율 φ = {phi:.2f}")
    notes.append(f"   경사각 {inp.inclination_deg:.1f}° → 수평 {l_h:.2f} m,  수직 {h_vert:.2f} m")

    if inp.inclination_deg > 45:
        notes.append("   ⚠ 경사각 45° 초과 — 수직 Flow Conveyor 설계 재검토")
    if V > 30:
        notes.append("   ⚠ Chain 속도 30 m/min 초과 — 소음·마모 증가 우려")

    # ── 모터 선정 ─────────────────────────────────────────────────────────
    motor_result = motor_calc.select_standard_motor(P_req_kW)

    # Sprocket 회전수 추정 (PCD 350mm 기준)
    pcd_m = 0.35
    sprocket_rpm = V / (math.pi * pcd_m)

    notes.append(f"■ Sprocket 추정 PCD = {pcd_m*1000:.0f} mm → 회전수 = {sprocket_rpm:.1f} rpm")

    # ── 비틀림 모멘트 ────────────────────────────────────────────────────────
    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(sprocket_rpm, 1)
    notes.append(f"■ 비틀림 모멘트 T = 9550 × {motor_result.selected_motor_kW} / {sprocket_rpm:.1f} = {T_Nm:.1f}  N·m")

    # ── 베어링 선정 ──────────────────────────────────────────────────────────
    b_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=sprocket_rpm,
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
        output_speed_rpm=sprocket_rpm,
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
        equipment_type="플로우 컨베이어",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
