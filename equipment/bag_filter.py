"""Bag Filter 설계 계산기
핸드북 Chapter 8/9 공식:
  1) 필요 여과포 면적: A = Qa / V  [m²]
     Qa: 풍량(m³/min), V: 여과속도(m/min)
  2) 단위 Bag 면적:  A' = π × D × H  [m²]
  3) Bag 수량:       N = ceil(A / A')  [개]
  4) 실제 여과속도:  V_act = Qa / (A' × N)  [m/min]
  5) Fan 동력:       P = (Q[m³/s] × ΔP[Pa]) / (η_fan × η_drive × 1000)  [kW]
"""
import math
from models.input_models import BagFilterInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS


def calculate(inp: BagFilterInput,
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

    Qa  = inp.air_volume_m3min          # m³/min
    V   = inp.filter_velocity_mmin      # m/min
    D   = inp.bag_diameter_m            # m
    H   = inp.bag_height_m              # m
    dP  = inp.static_pressure_pa        # Pa
    eta_f = inp.fan_efficiency
    eta_d = inp.drive_efficiency
    Sf  = inp.safety_factor

    # ── 1) 여과포 설계 ──────────────────────────────────────────────────────
    A_total  = Qa / V                       # 필요 총 여과포 면적 (m²)
    A_unit   = math.pi * D * H             # 단위 Bag 면적 (m²)
    N_bags   = math.ceil(A_total / A_unit)  # Bag 수량 (올림)
    V_actual = Qa / (A_unit * N_bags)       # 실제 여과속도 (m/min)

    notes.append("■ 1) 여과포 면적 계산")
    notes.append(f"   필요 여과포 면적 A = Qa / V")
    notes.append(f"                     = {Qa:.1f} / {V:.2f}")
    notes.append(f"                     = {A_total:.2f}  m²")
    notes.append("■ 2) 단위 Bag 면적")
    notes.append(f"   A' = π × D × H = π × {D} × {H}")
    notes.append(f"      = {A_unit:.3f}  m²  (Ø{D*1000:.0f}mm × H{H*1000:.0f}mm)")
    notes.append("■ 3) Bag 수량")
    notes.append(f"   N = ceil(A / A') = ceil({A_total:.2f} / {A_unit:.3f})")
    notes.append(f"     = {N_bags}  개")
    notes.append("■ 4) 실제 여과속도")
    notes.append(f"   V_act = Qa / (A' × N) = {Qa:.1f} / ({A_unit:.3f} × {N_bags})")
    notes.append(f"         = {V_actual:.3f}  m/min  (설계 V = {V:.2f} m/min)")

    if V_actual > 4.3:
        notes.append("   ⚠ 여과속도 4.3 m/min 초과 — Bag 수량 증가 권장")
    elif V_actual < 1.5:
        notes.append("   ℹ 여과속도 1.5 m/min 미만 — Bag 수량 감소 검토 가능")
    else:
        notes.append(f"   ✓ 여과속도 정상 범위 (1.5~4.3 m/min)")

    # Pulse Valve 참고
    bags_per_zone = min(15, max(1, N_bags // max(1, round(N_bags / 15))))
    zone_area = A_unit * bags_per_zone
    CV_val = zone_area * 3.5
    notes.append(f"   Pulse Valve CV 참고값: {CV_val:.1f}  (Zone당 {bags_per_zone}개 기준)")

    # ── 5) Fan 동력 ──────────────────────────────────────────────────────────
    Q_m3s = Qa / 60.0
    P_shaft_kW = (Q_m3s * dP) / (eta_f * eta_d * 1000.0)
    P_req_kW   = P_shaft_kW * Sf

    notes.append("■ 5) Fan 소요 동력")
    notes.append(f"   Q = {Qa:.1f} m³/min = {Q_m3s:.4f}  m³/s")
    notes.append(f"   P = (Q × ΔP) / (η_fan × η_drive × 1000)")
    notes.append(f"     = ({Q_m3s:.4f} × {dP:.1f}) / ({eta_f} × {eta_d} × 1000)")
    notes.append(f"     = {P_shaft_kW:.3f}  kW")
    notes.append(f"   안전율 적용: {P_shaft_kW:.3f} × {Sf} = {P_req_kW:.3f}  kW")
    notes.append(f"   압력손실 ΔP = {dP:.1f} Pa  ({dP/9.81:.1f} mmH₂O)")

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
        equipment_type="백 필터",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
