"""Drag Conveyor 통합 계산기
핸드북 Chapter 4 공식:
  계수 N_coef = 1.2 + 0.3 × N_outlet  (배출구 수 보정)
  수평: H = Qt × F × L × N_coef / (300 × E)  [HP]
  경사: H = Qt × N_coef × (F×L + H_vert) / (300 × E)  [HP]
  P [kW] = H [HP] × 0.7457 / η_drive × Sf
  이론 운반량: Qt_theory = 60 × A × V × γ × φ  [T/hr]
  단면적: A = B × H_trough  [m²]
  운반 용적: Qvol = Qt / γ  [m³/hr]
  운반물 1m당 중량: W = 16.7 × Qt / V  [kg/m]
"""
import math
from models.input_models import DragConveyorInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS

# Sprocket PCD (m) — 기본값
_SPROCKET_PCD_M = 0.30


def calculate(inp: DragConveyorInput,
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
    F     = inp.friction_factor_F
    L     = inp.conveyor_length_m
    H_v   = inp.conveyor_height_m
    N_out = inp.num_outlets
    E     = inp.mechanical_efficiency
    V     = inp.chain_speed_mpm          # m/min
    B     = inp.trough_width_m           # 트로프 폭
    H_t   = inp.trough_height_m          # 트로프 높이
    phi   = inp.fill_efficiency
    rho   = inp.specific_gravity          # t/m³
    eta   = inp.drive_efficiency
    Sf    = inp.safety_factor

    # ── 1) 트로프 단면적 및 이론 운반량 ─────────────────────────────────────
    A = B * H_t                           # 트로프 단면적 (m²)
    Qt_theory = 60.0 * A * V * rho * phi  # 이론 운반량 (T/hr)
    Qvol_theory = Qt_theory / rho if rho > 0 else 0.0  # 이론 운반 용적 (m³/hr)
    Qvol_design = Qt / rho if rho > 0 else 0.0          # 설계 운반 용적 (m³/hr)

    notes.append("■ 1) 트로프 단면적 및 이론 운반량")
    notes.append(f"   트로프 폭 B = {B:.2f} m,  트로프 높이 H = {H_t:.2f} m")
    notes.append(f"   단면적 A = B × H = {B:.2f} × {H_t:.2f} = {A:.4f}  m²  ({A*1e6:.0f}  mm²)")
    notes.append(f"   이론 운반량 Qt_theory = 60 × A × V × γ × φ")
    notes.append(f"                        = 60 × {A:.4f} × {V:.1f} × {rho} × {phi}")
    notes.append(f"                        = {Qt_theory:.2f}  T/hr")
    notes.append(f"   이론 운반 용적 Qvol = {Qt_theory:.2f} / {rho} = {Qvol_theory:.2f}  m³/hr")
    notes.append(f"   설계 운반량 Qt = {Qt:.2f}  T/hr  →  설계 운반 용적 = {Qvol_design:.2f}  m³/hr")

    if Qt_theory > 0:
        ratio = Qt / Qt_theory
        if ratio > 1.10:
            notes.append(f"   ⚠ 설계 용량이 이론값 대비 {ratio:.1%} — 트로프 단면 또는 속도 재검토")
        elif ratio < 0.60:
            notes.append(f"   ℹ 여유율 {(1/ratio - 1)*100:.0f}% — 트로프 축소 또는 속도 감속 가능")
        else:
            notes.append(f"   ✓ 이론 용량 {Qt_theory:.2f} T/hr 대비 여유율 {(Qt_theory/Qt - 1)*100:.0f}%")

    # ── 2) 소요 동력 ─────────────────────────────────────────────────────────
    N_coef = 1.2 + 0.3 * N_out

    if H_v > 0:
        H_HP = Qt * N_coef * (F * L + H_v) / (300.0 * E)
        mode_str = "경사"
    else:
        H_HP = Qt * F * L * N_coef / (300.0 * E)
        mode_str = "수평"

    P_kW_base = H_HP * 0.7457 / eta
    P_req_kW  = P_kW_base * Sf

    notes.append(f"■ 2) 소요 동력 계산 (핸드북 Ch.4 — {mode_str})")
    notes.append(f"   배출구 수 N = {N_out}  →  계수 N_coef = 1.2 + 0.3×{N_out} = {N_coef:.2f}")
    if H_v > 0:
        notes.append(f"   H = Qt × N_coef × (F×L + H_vert) / (300 × E)")
        notes.append(f"     = {Qt:.2f} × {N_coef:.2f} × ({F}×{L} + {H_v}) / (300 × {E})")
    else:
        notes.append(f"   H = Qt × F × L × N_coef / (300 × E)")
        notes.append(f"     = {Qt:.2f} × {F} × {L} × {N_coef:.2f} / (300 × {E})")
    notes.append(f"     = {H_HP:.3f}  HP")
    notes.append(f"   P = H × 0.7457 / η = {H_HP:.3f} × 0.7457 / {eta}")
    notes.append(f"     = {P_kW_base:.3f}  kW")
    notes.append(f"   안전율 적용: {P_kW_base:.3f} × {Sf} = {P_req_kW:.3f}  kW")

    # ── 3) 컨베어 운반 속도 및 운반물 1m당 중량 ────────────────────────────
    W_per_m = 16.7 * Qt / max(V, 1)
    notes.append("■ 3) 컨베어 운반 속도 및 운반물 중량")
    notes.append(f"   체인 속도 V = {V:.1f}  m/min")
    notes.append(f"   운반물 1m당 중량 W = 16.7 × Qt / V = 16.7 × {Qt:.2f} / {V:.1f} = {W_per_m:.1f}  kg/m")
    notes.append(f"   마찰계수 F = {F},  기계효율 E = {E}")

    if H_v > L * 0.84:
        notes.append("   ⚠ 경사각 40° 초과 — Drag Conveyor 설계 한계 검토")
    if Qt > 200:
        notes.append("   ⚠ 처리량 200 T/hr 초과 — 체인 선정 재검토 필요")

    # ── 모터 선정 ─────────────────────────────────────────────────────────
    motor_result = motor_calc.select_standard_motor(P_req_kW)

    # Sprocket 회전수
    sprocket_rpm = V / (math.pi * _SPROCKET_PCD_M)
    notes.append(f"   Sprocket PCD = {_SPROCKET_PCD_M*1000:.0f} mm → 회전수 = {sprocket_rpm:.1f} rpm")

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
    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(sprocket_rpm, 1)
    s_adj = ShaftInput(
        torque_Nm=T_Nm,
        bending_moment_Nm=shaft_inp.bending_moment_Nm,
        material=shaft_inp.material,
        safety_factor=shaft_inp.safety_factor,
        km_factor=shaft_inp.km_factor,
        kt_factor=shaft_inp.kt_factor,
    )
    shaft_result = shaft_des.design(s_adj)

    # ── 4) 동력 적정 여부 ────────────────────────────────────────────────────
    notes.append("■ 4) 동력 적정 여부")
    notes.append(f"   필요 동력: {P_req_kW:.3f}  kW")
    notes.append(f"   선정 모터: {motor_result.selected_motor_kW}  kW  ({motor_result.motor_model})")
    if motor_result.selected_motor_kW >= P_req_kW:
        margin = (motor_result.selected_motor_kW / P_req_kW - 1) * 100
        notes.append(f"   ✓ 모터 용량 적정  (여유율 {margin:.0f}%)")
    else:
        notes.append(f"   ⚠ 모터 용량 부족!")

    # ── 5) 축경 적정 여부 ────────────────────────────────────────────────────
    notes.append("■ 5) 축경 적정 여부")
    notes.append(f"   비틀림 모멘트 T = 9550 × {motor_result.selected_motor_kW} / {sprocket_rpm:.1f} = {T_Nm:.1f}  N·m")
    notes.append(f"   계산 최소 축경:  {shaft_result.required_diameter_mm:.1f}  mm")
    notes.append(f"   KS 표준 선정:    {shaft_result.selected_diameter_mm:.0f}  mm")
    notes.append(f"   입력 샤프트 직경: {inp.shaft_diameter_mm:.0f}  mm")
    if inp.shaft_diameter_mm >= shaft_result.required_diameter_mm:
        notes.append(f"   ✓ 축경 적정  (여유 {inp.shaft_diameter_mm - shaft_result.required_diameter_mm:.1f} mm)")
    else:
        notes.append(f"   ⚠ 축경 부족!  최소 {shaft_result.required_diameter_mm:.0f} mm 이상 필요")

    # ── 6) 직접 선정 검증 ────────────────────────────────────────────────────
    if inp.user_motor_kW > 0 or inp.user_bearing_C_kN > 0:
        notes.append("■ 6) 직접 선정 검증")
        if inp.user_motor_kW > 0:
            if inp.user_motor_kW >= P_req_kW:
                notes.append(f"   모터: 지정 {inp.user_motor_kW} kW  ≥  필요 {P_req_kW:.3f} kW  → ✓ 적정")
            else:
                notes.append(f"   모터: 지정 {inp.user_motor_kW} kW  <  필요 {P_req_kW:.3f} kW  → ⚠ 용량 부족!")
        if inp.user_bearing_C_kN > 0:
            C_req_kN = bearing_drive.required_C_N / 1000.0
            if inp.user_bearing_C_kN >= C_req_kN:
                notes.append(f"   베어링: 지정 C = {inp.user_bearing_C_kN} kN  ≥  필요 {C_req_kN:.1f} kN  → ✓ 적정")
            else:
                notes.append(f"   베어링: 지정 C = {inp.user_bearing_C_kN} kN  <  필요 {C_req_kN:.1f} kN  → ⚠ 수명 부족!")

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
        equipment_type="드래그 컨베이어",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        capacity_tph=Qt_theory,
        calculation_notes=notes,
    )
