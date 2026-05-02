"""Belt Conveyor 통합 계산기
핸드북 Ch.1 표1-9/1-10 공식:
  P = P1+P2+P3,  Pm = P/η
  운반량: Qt = 60×k×(0.9B-0.05)²×v×ρ×γ  (표1-5/1-7)

표1-9 (f, l0): roller_condition 콤보 → 자동조회
표1-10 (W):   belt_width_mm → 자동조회 (auto_W=True)
"""
import math
from models.input_models import BeltConveyorInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS

# 표1-5: Trough 35°, 동안식각별 k값 (대표값)
# 동안식각 10°=0.1023, 20°=0.1488, 30°=0.1849 (Trough 35° 기준)
_K_ANGLE = {10: 0.1023, 20: 0.1488, 30: 0.1849}

# 표1-7: 경사각도별 운반율 γ
_SLOPE_FACTOR = {
    0: 1.00, 2: 1.00, 4: 0.99, 6: 0.98, 8: 0.97,
    10: 0.95, 12: 0.93, 14: 0.91, 16: 0.89, 18: 0.85,
    20: 0.81, 22: 0.76, 24: 0.73, 26: 0.71, 28: 0.64,
    30: 0.59,
}


def _slope_factor(deg: float) -> float:
    """표1-7 경사각도 → 운반율 γ (선형 보간)"""
    angles = sorted(_SLOPE_FACTOR.keys())
    if deg <= angles[0]:
        return _SLOPE_FACTOR[angles[0]]
    if deg >= angles[-1]:
        return _SLOPE_FACTOR[angles[-1]]
    for i in range(len(angles) - 1):
        a0, a1 = angles[i], angles[i + 1]
        if a0 <= deg <= a1:
            t = (deg - a0) / (a1 - a0)
            return _SLOPE_FACTOR[a0] + t * (_SLOPE_FACTOR[a1] - _SLOPE_FACTOR[a0])
    return 1.0


def calculate(inp: BeltConveyorInput,
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

    # ── 표1-9 자동조회 표시 ──────────────────────────────────
    f, l0 = motor_calc._BELT_F_TABLE.get(inp.roller_condition, (0.022, 66.0))
    W = motor_calc.lookup_belt_W(inp.belt_width_mm) if inp.auto_W else inp.moving_parts_W
    notes.append(f"■ 표1-9 → f={f}, l0={l0} m  ({inp.roller_condition} 조건)")
    notes.append(f"■ 표1-10 → W={W} kg/m  (Belt {inp.belt_width_mm:.0f} mm 기준{'·자동' if inp.auto_W else '·수동'})")

    # ── 소요동력 계산 ────────────────────────────────────────
    P_kW = motor_calc.calc_belt_conveyor_power(inp)

    # ── 이론 운반량 검토 (표1-5/1-7, P.25 공식) ──────────────
    # Qt = 60×k×(0.9B-0.05)²×v×ρ×γ
    B_m      = inp.belt_width_mm / 1000.0
    k_val    = _K_ANGLE.get(20, 0.1488)          # Trough 35°, 동안식각 20° 대표값
    gamma_v  = _slope_factor(inp.inclination_deg)
    Qt_theory = (60 * k_val * (0.9 * B_m - 0.05) ** 2
                 * inp.belt_speed_mpm * inp.material_density * gamma_v)
    notes.append(f"■ 이론 운반량 (Trough35°, 동안식각20°): {Qt_theory:.1f} Ton/hr")
    notes.append(f"■ 경사 운반율 γ (표1-7, {inp.inclination_deg:.0f}°): {gamma_v:.2f}")

    if Qt_theory < inp.capacity_tph:
        notes.append(f"⚠ 이론 운반량 부족! Belt 폭 확대 또는 속도 증가 검토 (여유 {Qt_theory/inp.capacity_tph*100:.0f}%)")
    else:
        notes.append(f"✓ 운반량 여유율: {(Qt_theory/inp.capacity_tph - 1)*100:.0f}%")

    if inp.inclination_deg > 20:
        notes.append("⚠ 경사각 20° 초과 — 재료 미끄러짐 위험, 경사각 재검토")
    if inp.belt_speed_mpm > 180:
        notes.append("⚠ Belt 속도 180 m/min 초과")

    motor_result = motor_calc.select_standard_motor(P_kW)

    # Belt 구동 드럼 회전수 추정 (드럼 직경 = belt폭/2 + 100 mm 근사)
    drum_dia_m = max(0.3, inp.belt_width_mm / 2000.0 + 0.1)
    drum_rpm = inp.belt_speed_mpm / (math.pi * drum_dia_m)

    b_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=drum_rpm,
        desired_life_hr=bearing_inp.desired_life_hr,
        bearing_type=bearing_inp.bearing_type,
        reliability=bearing_inp.reliability,
    )
    bearing_drive  = bearing_calc.select_bearing(b_adj, min_bore_mm=motor_result.shaft_dia_mm)
    bearing_driven = bearing_calc.select_bearing(b_adj, min_bore_mm=motor_result.shaft_dia_mm)

    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(drum_rpm, 1)
    s_adj = ShaftInput(
        torque_Nm=T_Nm,
        bending_moment_Nm=shaft_inp.bending_moment_Nm,
        material=shaft_inp.material,
        safety_factor=shaft_inp.safety_factor,
        km_factor=shaft_inp.km_factor,
        kt_factor=shaft_inp.kt_factor,
    )
    shaft_result = shaft_des.design(s_adj)

    r_adj = ReducerInput(
        input_power_kW=motor_result.selected_motor_kW,
        input_speed_rpm=motor_result.rated_rpm,
        output_speed_rpm=drum_rpm,
        service_factor=reducer_inp.service_factor,
        brand=reducer_inp.brand,
    )
    reducer_result = reducer_sel.select_reducer(r_adj)

    chain_result = chain_sel.select_chain_with_rpm(
        chain_inp,
        design_power_kW=motor_result.selected_motor_kW,
        reducer_brand=reducer_inp.brand,
        output_rpm=motor_result.rated_rpm / max(reducer_result.ratio, 1),
    )
    if reducer_inp.brand in DIRECT_COUPLING_BRANDS:
        notes.append(f"ℹ {reducer_inp.brand} 감속기 — 직결 구동 (체인 없음)")

    return EquipmentResult(
        equipment_type="벨트 컨베이어",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
