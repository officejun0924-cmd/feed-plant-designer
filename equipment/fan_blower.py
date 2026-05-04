"""팬/블로어 통합 계산기
참조 공식:
  1) 풍량:       Q [m³/s] = Q [m³/hr] / 3600
  2) 축 동력:    P_shaft = (Q [m³/s] × ΔP [Pa]) / (η_fan × η_drive × 1000)  [kW]
  3) 소요 동력:  P_req = P_shaft × Sf  [kW]
  4) 비틀림 모멘트: T = 9550 × P_motor / N  [N·m]
"""
from models.input_models import FanBlowerInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS


def calculate(inp: FanBlowerInput,
              bearing_inp: BearingInput,
              shaft_inp: ShaftInput,
              reducer_inp: ReducerInput,
              chain_inp: ChainInput) -> EquipmentResult:

    notes = []
    motor_calc    = MotorCalculator()
    bearing_calc  = BearingCalculator()
    shaft_designer = ShaftDesigner()
    reducer_sel   = ReducerSelector()
    chain_sel     = ChainSelector()

    Q_m3h  = inp.flow_rate_m3h          # m³/hr
    Q_m3s  = Q_m3h / 3600.0            # m³/s
    dP     = inp.static_pressure_pa     # Pa
    eta_f  = inp.fan_efficiency
    eta_d  = inp.drive_efficiency
    Sf     = inp.safety_factor
    rho    = inp.air_density             # kg/m³

    # ── 1) 풍량 변환 ────────────────────────────────────────────────────────
    notes.append("■ 1) 풍량")
    notes.append(f"   Q = {Q_m3h:.1f} m³/hr")
    notes.append(f"     = {Q_m3h:.1f} / 3600 = {Q_m3s:.4f}  m³/s")

    # ── 2) 축 동력 (팬 소요 동력) ────────────────────────────────────────────
    P_shaft_kW = (Q_m3s * dP) / (eta_f * eta_d * 1000.0)
    P_req_kW   = P_shaft_kW * Sf

    notes.append("■ 2) 축 동력 P_shaft")
    notes.append(f"   P = (Q [m³/s] × ΔP [Pa]) / (η_fan × η_drive × 1000)")
    notes.append(f"     = ({Q_m3s:.4f} × {dP:.1f}) / ({eta_f} × {eta_d} × 1000)")
    notes.append(f"     = {Q_m3s * dP:.3f} / {eta_f * eta_d * 1000:.1f}")
    notes.append(f"     = {P_shaft_kW:.3f}  kW")
    notes.append(f"   안전율 적용: {P_shaft_kW:.3f} × {Sf} = {P_req_kW:.3f}  kW")

    # ── 3) 공기역학 참고 ──────────────────────────────────────────────────────
    # 동압 ΔP_d = ρ × v² / 2 참고용 (유속 추정 불가 — 덕트 단면 미입력)
    # 전압 = 정압 + 동압 (정압만 입력된 경우)
    notes.append("■ 3) 참고 데이터")
    notes.append(f"   정압 ΔP = {dP:.1f}  Pa  ({dP/9.81:.2f} mmH₂O)")
    notes.append(f"   공기 밀도 ρ = {rho:.3f}  kg/m³")
    notes.append(f"   팬 효율 η_fan = {eta_f:.2f},  전동 효율 η_drive = {eta_d:.2f}")

    if inp.static_pressure_pa > 5000:
        notes.append("   ⚠ 정압 5000 Pa 초과 — 블로어 또는 압축기 사양 검토 권장")
    if inp.fan_efficiency < 0.65:
        notes.append("   ⚠ 팬 효율 65% 미만 — 임펠러 설계 또는 팬 선정 재검토")

    # 팬 rpm은 베어링 입력에서 가져옴
    fan_rpm = bearing_inp.shaft_speed_rpm

    # ── 모터 선정 ─────────────────────────────────────────────────────────
    motor_result = motor_calc.select_standard_motor(P_req_kW)

    # ── 4) 비틀림 모멘트 ─────────────────────────────────────────────────────
    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(fan_rpm, 1)
    notes.append("■ 4) 비틀림 모멘트")
    notes.append(f"   T = 9550 × P_motor / N")
    notes.append(f"     = 9550 × {motor_result.selected_motor_kW} / {fan_rpm:.1f}")
    notes.append(f"     = {T_Nm:.1f}  N·m")

    # ── 베어링 선정 ──────────────────────────────────────────────────────────
    bearing_inp_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=fan_rpm,
        desired_life_hr=bearing_inp.desired_life_hr,
        bearing_type=bearing_inp.bearing_type,
        reliability=bearing_inp.reliability,
    )
    bearing_drive  = bearing_calc.select_bearing(bearing_inp_adj, min_bore_mm=motor_result.shaft_dia_mm)
    bearing_driven = bearing_calc.select_bearing(bearing_inp_adj, min_bore_mm=motor_result.shaft_dia_mm)

    # ── 샤프트 설계 ──────────────────────────────────────────────────────────
    shaft_inp_adj = ShaftInput(
        torque_Nm=T_Nm,
        bending_moment_Nm=shaft_inp.bending_moment_Nm,
        material=shaft_inp.material,
        safety_factor=shaft_inp.safety_factor,
        km_factor=shaft_inp.km_factor,
        kt_factor=shaft_inp.kt_factor,
    )
    shaft_result = shaft_designer.design(shaft_inp_adj)

    # ── 감속기 선정 ──────────────────────────────────────────────────────────
    reducer_inp_adj = ReducerInput(
        input_power_kW=motor_result.selected_motor_kW,
        input_speed_rpm=motor_result.rated_rpm,
        output_speed_rpm=fan_rpm,
        service_factor=reducer_inp.service_factor,
        brand=reducer_inp.brand,
    )
    reducer_result = reducer_sel.select_reducer(reducer_inp_adj)

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
        equipment_type="팬/블로어",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
