"""분쇄기/해머밀 통합 계산기
참조 공식 (Bond 분쇄 법칙):
  1) 단위 분쇄 에너지: W = Wi × (10/√P80 - 10/√F80)  [kWh/t]
     F80, P80: μm 단위, Wi: Bond 작업지수 (kWh/t)
  2) 소요 동력:       P = W × Qt / η_drive × Sf  [kW]
  3) 비틀림 모멘트:   T = 9550 × P_motor / N_rotor  [N·m]
  4) 로터 팁 속도:    v_tip = π × D × N / 60  [m/s]
"""
import math
from models.input_models import GrinderHammerMillInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS


def calculate(inp: GrinderHammerMillInput,
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

    Wi      = inp.material_hardness         # Bond 작업지수 (kWh/t)
    F80_mm  = inp.feed_size_mm              # 공급 입도 F80 (mm)
    P80_mm  = inp.product_size_mm           # 제품 입도 P80 (mm)
    F80_um  = F80_mm * 1000.0              # mm → μm
    P80_um  = P80_mm * 1000.0              # mm → μm
    Qt      = inp.capacity_tph
    eta     = inp.drive_efficiency
    Sf      = inp.safety_factor
    N_rotor = inp.rotor_speed_rpm
    D_rotor = inp.rotor_diameter_m

    # ── 1) Bond 단위 분쇄 에너지 ────────────────────────────────────────────
    term_p = 10.0 / math.sqrt(P80_um)
    term_f = 10.0 / math.sqrt(F80_um)
    W = Wi * (term_p - term_f)
    W = max(W, 0.0)

    notes.append("■ 1) Bond 분쇄 법칙 — 단위 분쇄 에너지 W")
    notes.append(f"   W = Wi × (10/√P80 - 10/√F80)")
    notes.append(f"     = {Wi} × (10/√{P80_um:.0f} - 10/√{F80_um:.0f})")
    notes.append(f"     = {Wi} × ({term_p:.5f} - {term_f:.5f})")
    notes.append(f"     = {W:.4f}  kWh/t")
    notes.append(f"   F80 = {F80_mm} mm ({F80_um:.0f} μm),  P80 = {P80_mm} mm ({P80_um:.0f} μm)")

    if W <= 0:
        notes.append("   ⚠ W ≤ 0 — 제품 입도가 공급 입도보다 크거나 같음, 입력 확인 필요")

    # ── 2) 소요 동력 ─────────────────────────────────────────────────────────
    P_base_kW = W * Qt / eta
    P_req_kW  = P_base_kW * Sf

    notes.append("■ 2) 소요 동력 P")
    notes.append(f"   P = W × Qt / η")
    notes.append(f"     = {W:.4f} × {Qt:.2f} / {eta}")
    notes.append(f"     = {P_base_kW:.3f}  kW")
    notes.append(f"   안전율 적용: {P_base_kW:.3f} × {Sf} = {P_req_kW:.3f}  kW")

    # ── 3) 로터 팁 속도 ──────────────────────────────────────────────────────
    v_tip = math.pi * D_rotor * N_rotor / 60.0
    notes.append("■ 3) 로터 사양")
    notes.append(f"   로터 직경 D = {D_rotor*1000:.0f} mm,  회전수 N = {N_rotor:.0f} rpm")
    notes.append(f"   팁 속도 v_tip = π × D × N / 60 = {v_tip:.1f}  m/s")
    if v_tip < 50:
        notes.append("   ℹ 팁 속도 50 m/s 미만 — 분쇄 효율 낮을 수 있음 (일반 해머밀: 50~100 m/s)")
    elif v_tip > 120:
        notes.append("   ⚠ 팁 속도 120 m/s 초과 — 해머·라이너 마모 가속 가능")

    if N_rotor > 3600:
        notes.append("   ⚠ 로터 속도 3600 rpm 초과 — 동적 균형 및 베어링 발열 주의")

    # ── 모터 선정 ─────────────────────────────────────────────────────────
    motor_result = motor_calc.select_standard_motor(P_req_kW)

    # ── 4) 비틀림 모멘트 ─────────────────────────────────────────────────────
    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(N_rotor, 1)
    notes.append("■ 4) 비틀림 모멘트")
    notes.append(f"   T = 9550 × P_motor / N")
    notes.append(f"     = 9550 × {motor_result.selected_motor_kW} / {N_rotor:.0f}")
    notes.append(f"     = {T_Nm:.1f}  N·m")

    if abs(motor_result.rated_rpm - N_rotor) / max(N_rotor, 1) < 0.05:
        notes.append("   ℹ 모터와 로터 속도가 유사 — 직결 구동 검토 가능")

    # ── 베어링 선정 ──────────────────────────────────────────────────────────
    bearing_inp_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=N_rotor,
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
        output_speed_rpm=N_rotor,
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
        equipment_type="분쇄기/해머밀",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
