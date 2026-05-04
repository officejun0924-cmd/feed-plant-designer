"""버킷 엘리베이터 통합 계산기
참조 공식:
  1) 이론 운반량: Qt_theory = (Vb / a) × v × ρ × 3.6  [T/hr]
     Vb = 버킷 용량 (ℓ → m³), a = 버킷 간격 (m), v = Belt 속도 (m/s)
  2) 소요 동력:   P = (Q × H) / (367 × η) × Sf  [kW]
  3) 비틀림 모멘트: T = 9550 × P / N  [N·m]
"""
import math
from models.input_models import BucketElevatorInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS


def calculate(inp: BucketElevatorInput,
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

    Qt     = inp.capacity_tph
    H      = inp.lift_height_m
    Vb_m3  = inp.bucket_volume_L / 1000.0   # ℓ → m³
    a      = inp.bucket_spacing_m
    v      = inp.belt_speed_mps
    rho    = inp.specific_gravity            # t/m³
    eta    = inp.drive_efficiency
    Sf     = inp.safety_factor

    # ── 1) 이론 운반량 ───────────────────────────────────────────────────────
    Qt_theory = (Vb_m3 / a) * v * rho * 3600.0   # T/hr

    notes.append("■ 1) 이론 운반량 Qt_theory")
    notes.append(f"   Qt = (Vb / a) × v × ρ × 3600")
    notes.append(f"      = ({Vb_m3*1000:.1f}L / {a}) × {v} × {rho} × 3600")
    notes.append(f"      = {Qt_theory:.2f}  T/hr")
    notes.append(f"   설계 운반량 Qt = {Qt:.2f}  T/hr")

    if Qt_theory > 0:
        ratio = Qt / Qt_theory
        if ratio > 1.10:
            notes.append(f"   ⚠ 설계 용량이 이론값 대비 {ratio:.1%} — 버킷 용량·속도 재검토")
        elif ratio < 0.60:
            notes.append(f"   ℹ 여유율 {(1/ratio - 1)*100:.0f}% — 버킷 간격 축소 또는 속도 감소 가능")
        else:
            notes.append(f"   ✓ 이론 용량 {Qt_theory:.2f} T/hr 대비 여유율 {(Qt_theory/Qt - 1)*100:.0f}%")

    # ── 2) 소요 동력 ─────────────────────────────────────────────────────────
    P_base_kW = (Qt * H) / (367.0 * eta)
    P_req_kW  = P_base_kW * Sf

    notes.append("■ 2) 소요 동력 P")
    notes.append(f"   P = (Q × H) / (367 × η)")
    notes.append(f"     = ({Qt:.2f} × {H}) / (367 × {eta})")
    notes.append(f"     = {P_base_kW:.3f}  kW")
    notes.append(f"   안전율 적용: {P_base_kW:.3f} × {Sf} = {P_req_kW:.3f}  kW")

    if inp.belt_speed_mps > 2.5:
        notes.append("   ⚠ 벨트 속도 2.5 m/s 초과 — 재료 이탈 가능성 확인 필요")

    # 구동 드럼 회전수 역산 (드럼 둘레 ≈ belt폭/2 + 100 mm 근사, 최소 400mm)
    drum_dia_m = max(0.4, inp.bucket_volume_L / 10.0 / 1000.0 + 0.3)
    drum_circum = math.pi * drum_dia_m
    drum_rpm = v * 60.0 / drum_circum

    # ── 3) 비틀림 모멘트 ─────────────────────────────────────────────────────
    notes.append("■ 3) 모터 선정 후 비틀림 모멘트")

    motor_result = motor_calc.select_standard_motor(P_req_kW)

    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(drum_rpm, 1)
    notes.append(f"   T = 9550 × P_motor / N_drum")
    notes.append(f"     = 9550 × {motor_result.selected_motor_kW} / {drum_rpm:.1f}")
    notes.append(f"     = {T_Nm:.1f}  N·m")
    notes.append(f"   드럼 직경 (추정) = {drum_dia_m*1000:.0f} mm,  드럼 회전수 = {drum_rpm:.1f} rpm")

    # ── 베어링 선정 ──────────────────────────────────────────────────────────
    bearing_inp_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=drum_rpm,
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
        output_speed_rpm=drum_rpm,
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
        equipment_type="버킷 엘리베이터",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
