"""Cyclone 설계 계산기
핸드북 Chapter 10 공식:
  1) 입구 단면적:  A = Qa / (Va × 60)  [m²]
     Qa: m³/min, Va: m/sec → A [m²]
  2) 몸통 직경:   D = √(A / (H_ratio × W_ratio))  [m]
     A = H_inlet × W_inlet = (H_ratio×D) × (W_ratio×D) = H_ratio×W_ratio×D²
  3) 압력손실:    ΔP [mmH₂O] = λ × Va² / (2g) × γ_air
                 ΔP [Pa]    = ΔP [mmH₂O] × 9.81
  4) Fan 동력:    P = (Q[m³/s] × ΔP[Pa]) / (η_fan × η_drive × 1000)  [kW]
표10-2 표준 치수 비율 (일반 Cyclone 기준):
  고효율: H/D=0.44, W/D=0.21, Do/D=0.4,  몸통=1.4D, 원추=2.5D
  일반:   H/D=0.50, W/D=0.25, Do/D=0.5,  몸통=2.0D, 원추=2.0D
  고용량: H/D=0.80, W/D=0.35, Do/D=0.75, 몸통=1.7D, 원추=2.0D
"""
import math
from models.input_models import CycloneInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS

# 표10-2 치수 비율  {type: (H/D, W/D, Do/D, body_len/D, cone_len/D)}
_CYCLONE_RATIO = {
    "고효율": (0.44, 0.21, 0.4, 1.4, 2.5),
    "일반":   (0.5,  0.25, 0.5, 2.0, 2.0),
    "고용량": (0.8,  0.35, 0.75, 1.7, 2.0),
}


def calculate(inp: CycloneInput,
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

    Qa    = inp.air_volume_m3min        # m³/min
    Va    = inp.inlet_velocity_msec     # m/sec
    lam   = inp.pressure_loss_coef      # λ
    eta_f = inp.fan_efficiency
    eta_d = inp.drive_efficiency
    Sf    = inp.safety_factor
    g     = 9.8
    gamma_air = 1.2                     # kg/m³ (공기 밀도)

    ratio = _CYCLONE_RATIO.get(inp.cyclone_type, _CYCLONE_RATIO["일반"])
    H_ratio, W_ratio, Do_ratio, body_ratio, cone_ratio = ratio

    # ── 1) 입구 단면적 및 몸통 직경 ─────────────────────────────────────────
    A_inlet = Qa / (Va * 60.0)         # m²
    D_m = math.sqrt(A_inlet / (H_ratio * W_ratio))

    H_in_m  = H_ratio * D_m
    W_in_m  = W_ratio * D_m
    Do_m    = Do_ratio * D_m
    body_m  = body_ratio * D_m
    cone_m  = cone_ratio * D_m
    total_m = body_m + cone_m

    notes.append(f"■ 1) 입구 단면적 및 몸통 직경  [{inp.cyclone_type} 형]")
    notes.append(f"   입구 단면적 A = Qa / (Va × 60)")
    notes.append(f"              = {Qa:.1f} / ({Va:.1f} × 60)")
    notes.append(f"              = {A_inlet:.4f}  m²")
    notes.append(f"   D = √(A / (H/D × W/D)) = √({A_inlet:.4f} / ({H_ratio} × {W_ratio}))")
    notes.append(f"     = {D_m*1000:.0f}  mm")
    notes.append(f"■ 2) 표10-2 치수 비율 적용  [{inp.cyclone_type}]")
    notes.append(f"   유입구: {H_in_m*1000:.0f}(H) × {W_in_m*1000:.0f}(W) mm")
    notes.append(f"   가스 출구 직경 Do = {Do_ratio}D = {Do_m*1000:.0f} mm")
    notes.append(f"   몸통 길이: {body_ratio}D = {body_m*1000:.0f} mm")
    notes.append(f"   원추 길이: {cone_ratio}D = {cone_m*1000:.0f} mm")
    notes.append(f"   전체 높이: {total_m*1000:.0f} mm")

    # ── 3) 압력손실 ──────────────────────────────────────────────────────────
    dP_mmH2O = lam * Va ** 2 / (2 * g) * gamma_air
    dP_Pa    = dP_mmH2O * 9.81

    notes.append("■ 3) 압력손실 ΔP")
    notes.append(f"   ΔP [mmH₂O] = λ × Va² / (2g) × γ_air")
    notes.append(f"              = {lam} × {Va:.1f}² / (2 × {g}) × {gamma_air}")
    notes.append(f"              = {lam} × {Va**2:.2f} / {2*g:.1f} × {gamma_air}")
    notes.append(f"              = {dP_mmH2O:.2f}  mmH₂O")
    notes.append(f"   ΔP [Pa]    = {dP_mmH2O:.2f} × 9.81 = {dP_Pa:.1f}  Pa")

    if Va < 7:
        notes.append("   ⚠ 유입속도 7 m/sec 미만 — 집진 효율 저하 우려")
    if Va > 18:
        notes.append("   ⚠ 유입속도 18 m/sec 초과 — 압력손실 급증")

    # ── 4) Fan 소요 동력 ─────────────────────────────────────────────────────
    Q_m3s = Qa / 60.0
    P_shaft_kW = (Q_m3s * dP_Pa) / (eta_f * eta_d * 1000.0)
    P_req_kW   = P_shaft_kW * Sf

    notes.append("■ 4) Fan 소요 동력")
    notes.append(f"   Q = {Qa:.1f} m³/min = {Q_m3s:.4f}  m³/s")
    notes.append(f"   P = (Q × ΔP) / (η_fan × η_drive × 1000)")
    notes.append(f"     = ({Q_m3s:.4f} × {dP_Pa:.1f}) / ({eta_f} × {eta_d} × 1000)")
    notes.append(f"     = {P_shaft_kW:.3f}  kW")
    notes.append(f"   안전율 적용: {P_shaft_kW:.3f} × {Sf} = {P_req_kW:.3f}  kW")

    # ── 모터 선정 ─────────────────────────────────────────────────────────
    motor_result = motor_calc.select_standard_motor(P_req_kW)

    fan_rpm = 1450.0

    # ── 비틀림 모멘트 ────────────────────────────────────────────────────────
    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(fan_rpm, 1)
    notes.append(f"■ 비틀림 모멘트 T = 9550 × {motor_result.selected_motor_kW} / {fan_rpm:.0f} = {T_Nm:.1f}  N·m")

    # ── 베어링 선정 ──────────────────────────────────────────────────────────
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
        output_speed_rpm=fan_rpm,
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
        equipment_type="사이클론",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
