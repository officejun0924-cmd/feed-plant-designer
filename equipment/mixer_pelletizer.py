"""믹서/펠레타이저 통합 계산기
참조 공식 (Newton 교반 동력 수):
  1) 교반 동력: P = Np × ρ × n³ × D⁵  [W]
     Np: 파워 넘버 (mixing_factor), ρ: kg/m³, n: rps, D: m
  2) 소요 동력: P_kW = P[W] / (1000 × η_drive) × Sf
  3) 비틀림 모멘트: T = 9550 × P_motor / N  [N·m]
"""
from models.input_models import MixerPelletizerInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS


def calculate(inp: MixerPelletizerInput,
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

    Np      = inp.mixing_factor             # Newton 파워 넘버
    rho_t   = inp.specific_gravity          # t/m³
    rho_kg  = rho_t * 1000.0               # kg/m³
    N_rpm   = inp.shaft_speed_rpm
    n_rps   = N_rpm / 60.0                 # rev/s
    D       = inp.mixer_diameter_m          # m
    eta     = inp.drive_efficiency
    Sf      = inp.safety_factor

    # ── 1) 교반 동력 (Newton 교반 동력 수) ──────────────────────────────────
    P_W  = Np * rho_kg * (n_rps ** 3) * (D ** 5)
    P_kW_base = P_W / (1000.0 * eta)
    P_req_kW  = P_kW_base * Sf

    notes.append("■ 1) 교반 동력 P (Newton 교반 동력 수)")
    notes.append(f"   P = Np × ρ × n³ × D⁵")
    notes.append(f"     = {Np} × {rho_kg:.0f} × ({n_rps:.4f})³ × ({D})⁵")
    notes.append(f"     = {Np} × {rho_kg:.0f} × {n_rps**3:.6f} × {D**5:.6f}")
    notes.append(f"     = {P_W:.2f}  W")
    notes.append(f"   P_shaft = P / (1000 × η) = {P_W:.2f} / (1000 × {eta})")
    notes.append(f"           = {P_kW_base:.3f}  kW")
    notes.append(f"   안전율 적용: {P_kW_base:.3f} × {Sf} = {P_req_kW:.3f}  kW")

    if inp.mixing_factor > 1.0:
        notes.append("   ⚠ 파워 넘버 Np > 1.0 — 고점도 재료 또는 고부하 패들 조건")

    # ── 2) 이론 용량 확인 ──────────────────────────────────────────────────
    import math
    V_mixer = math.pi / 4.0 * D ** 2 * inp.mixer_length_m  # 믹서 내부 체적 (m³)
    Qt_theory = V_mixer * rho_t * 3600.0 / (60.0 / N_rpm)  # 단순 참고값
    notes.append("■ 2) 믹서 사양 참고")
    notes.append(f"   믹서 직경 D = {D} m,  길이 L = {inp.mixer_length_m} m")
    notes.append(f"   내부 체적 V = π/4 × D² × L = {V_mixer:.3f}  m³")
    notes.append(f"   패들 수 = {inp.paddle_number}개,  회전수 N = {N_rpm:.1f} rpm")
    notes.append(f"   설계 처리량 Qt = {inp.capacity_tph:.2f}  T/hr")

    # ── 모터 선정 ─────────────────────────────────────────────────────────
    motor_result = motor_calc.select_standard_motor(P_req_kW)

    # ── 3) 비틀림 모멘트 ─────────────────────────────────────────────────────
    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(N_rpm, 1)
    notes.append("■ 3) 비틀림 모멘트")
    notes.append(f"   T = 9550 × P_motor / N")
    notes.append(f"     = 9550 × {motor_result.selected_motor_kW} / {N_rpm:.1f}")
    notes.append(f"     = {T_Nm:.1f}  N·m")

    # ── 베어링 선정 ──────────────────────────────────────────────────────────
    bearing_inp_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=N_rpm,
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
        output_speed_rpm=N_rpm,
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
        equipment_type="믹서/펠레타이저",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
