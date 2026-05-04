"""Drag Conveyor 통합 계산기
핸드북 Chapter 4 공식:
  계수 N_coef = 1.2 + 0.3 × N_outlet  (배출구 수 보정)
  수평: H = Qt × F × L × N_coef / (300 × E)  [HP]
  경사: H = Qt × N_coef × (F×L + H_vert) / (300 × E)  [HP]
  P [kW] = H [HP] × 0.7457 / η_drive × Sf
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

# 통상 Chain 속도 (m/min) — Drag Conveyor 특성상 느림
_CHAIN_SPEED_MPM = 15.0
# Sprocket PCD (m)
_SPROCKET_PCD_M  = 0.30


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
    eta   = inp.drive_efficiency
    Sf    = inp.safety_factor

    # ── 1) 보정 계수 및 소요 동력 ────────────────────────────────────────────
    N_coef = 1.2 + 0.3 * N_out

    if H_v > 0:
        H_HP = Qt * N_coef * (F * L + H_v) / (300.0 * E)
        mode_str = "경사"
    else:
        H_HP = Qt * F * L * N_coef / (300.0 * E)
        mode_str = "수평"

    P_kW_base = H_HP * 0.7457 / eta
    P_req_kW  = P_kW_base * Sf

    notes.append(f"■ 1) 소요 동력 계산 (핸드북 Ch.4 — {mode_str})")
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

    # ── 2) 운반물 1m당 중량 및 Chain 속도 ───────────────────────────────────
    chain_v = _CHAIN_SPEED_MPM
    W_per_m = 16.7 * Qt / max(chain_v, 1)

    notes.append("■ 2) 운반 특성")
    notes.append(f"   Chain 속도 V = {chain_v} m/min  (Drag Conveyor 표준)")
    notes.append(f"   운반물 1m당 중량 W = 16.7 × Qt / V = 16.7 × {Qt:.2f} / {chain_v}")
    notes.append(f"                      = {W_per_m:.1f}  kg/m")
    notes.append(f"   마찰계수 F = {F},  기계효율 E = {E}")

    if H_v > L * 0.84:   # tan(40°) ≈ 0.84
        notes.append("   ⚠ 경사각 40° 초과 — Drag Conveyor 설계 한계 검토")
    if Qt > 200:
        notes.append("   ⚠ 처리량 200 T/hr 초과 — Chain 선정 재검토 필요")

    # Sprocket 회전수
    sprocket_rpm = chain_v / (math.pi * _SPROCKET_PCD_M)
    notes.append(f"■ Sprocket PCD = {_SPROCKET_PCD_M*1000:.0f} mm → 회전수 = {sprocket_rpm:.1f} rpm")

    # ── 모터 선정 ─────────────────────────────────────────────────────────
    motor_result = motor_calc.select_standard_motor(P_req_kW)

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
        equipment_type="드래그 컨베이어",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
