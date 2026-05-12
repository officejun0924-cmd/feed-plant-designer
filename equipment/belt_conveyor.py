"""Belt Conveyor 통합 계산기
핸드북 Ch.1 표1-9/1-10 공식:
  P1 = 0.06 × f × W × v × (l + l0) / 367   [무부하 동력, kW]
  P2 = f × Qt × (l + l0) / 367              [수평부하 동력, kW]
  P3 = ±h × Qt / 367                         [수직부하 동력, kW]
  P  = P1 + P2 + P3,  Pm = P / η
표1-9 (f, l0): roller_condition 콤보 → 자동조회
표1-10 (W):   belt_width_mm → 자동조회 (auto_W=True)
이론 운반량: Qt = 60 × k × (0.9B - 0.05)² × v × ρ × γ  (표1-5/1-7)
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

    Qt    = inp.capacity_tph
    B_mm  = inp.belt_width_mm
    v     = inp.belt_speed_mpm          # m/min
    L     = inp.conveyor_length_m
    eta   = inp.drive_efficiency
    Sf    = inp.safety_factor
    rho   = inp.material_density

    # ── 표1-9 자동조회 ────────────────────────────────────────────────────────
    f, l0 = motor_calc._BELT_F_TABLE.get(inp.roller_condition, (0.022, 66.0))
    W = motor_calc.lookup_belt_W(B_mm) if inp.auto_W else inp.moving_parts_W

    notes.append("■ 표1-9 Roller 조건 조회")
    notes.append(f"   조건: {inp.roller_condition} → f = {f},  l0 = {l0} m")
    notes.append("■ 표1-10 Belt 운동부 중량 W 조회")
    notes.append(f"   Belt {B_mm:.0f} mm → W = {W} kg/m{'  (자동조회)' if inp.auto_W else '  (수동입력)'}")

    # ── 경사 계산 ─────────────────────────────────────────────────────────────
    theta  = math.radians(inp.inclination_deg)
    l_h    = L * math.cos(theta)        # 수평 거리 (m)
    h_vert = L * math.sin(theta)        # 수직 높이 (m)
    eff_len = l_h + l0

    notes.append(f"   경사각 {inp.inclination_deg:.1f}° → 수평거리 l_h = {l_h:.2f} m,  수직 h = {h_vert:.2f} m")
    notes.append(f"   유효 길이 (l_h + l0) = {l_h:.2f} + {l0} = {eff_len:.2f} m")

    # ── 1) 소요 동력 P1, P2, P3 ──────────────────────────────────────────────
    P1 = 0.06 * f * W * v * eff_len / 367.0
    P2 = f * Qt * eff_len / 367.0
    P3 = h_vert * Qt / 367.0
    P  = P1 + P2 + P3
    Pm = P / eta
    P_req_kW = Pm * Sf

    notes.append("■ 1) 소요 동력 계산")
    notes.append(f"   P1 = 0.06 × f × W × v × (l+l0) / 367")
    notes.append(f"      = 0.06 × {f} × {W} × {v:.1f} × {eff_len:.2f} / 367")
    notes.append(f"      = {P1:.3f}  kW  (무부하 동력)")
    notes.append(f"   P2 = f × Qt × (l+l0) / 367")
    notes.append(f"      = {f} × {Qt:.2f} × {eff_len:.2f} / 367")
    notes.append(f"      = {P2:.3f}  kW  (수평부하 동력)")
    notes.append(f"   P3 = h × Qt / 367 = {h_vert:.2f} × {Qt:.2f} / 367")
    notes.append(f"      = {P3:.3f}  kW  (수직부하 동력)")
    notes.append(f"   P  = P1 + P2 + P3 = {P1:.3f} + {P2:.3f} + {P3:.3f} = {P:.3f}  kW")
    notes.append(f"   Pm = P / η = {P:.3f} / {eta} = {Pm:.3f}  kW")
    notes.append(f"   안전율 적용: {Pm:.3f} × {Sf} = {P_req_kW:.3f}  kW")

    # ── 2) 이론 운반량 검토 (표1-5/1-7) ────────────────────────────────────
    B_m      = B_mm / 1000.0
    k_val    = _K_ANGLE.get(20, 0.1488)     # Trough 35°, 동안식각 20° 대표값
    gamma_v  = _slope_factor(inp.inclination_deg)
    Qt_theory = 60.0 * k_val * (0.9 * B_m - 0.05) ** 2 * v * rho * gamma_v

    notes.append("■ 2) 이론 운반량 (표1-5/1-7)")
    notes.append(f"   Qt = 60 × k × (0.9B - 0.05)² × v × ρ × γ")
    notes.append(f"      = 60 × {k_val} × (0.9×{B_m} - 0.05)² × {v:.1f} × {rho} × {gamma_v:.2f}")
    notes.append(f"      = {Qt_theory:.1f}  T/hr  (Trough 35°, 동안식각 20° 기준)")
    notes.append(f"   경사 운반율 γ (표1-7, {inp.inclination_deg:.0f}°) = {gamma_v:.2f}")
    notes.append(f"   설계 운반량 Qt = {Qt:.2f}  T/hr")

    if Qt_theory < Qt:
        notes.append(f"   ⚠ 이론 운반량 부족! 여유율 {Qt_theory/Qt*100:.0f}% — Belt 폭 확대 또는 속도 증가 검토")
    else:
        notes.append(f"   ✓ 이론 운반량 여유율: {(Qt_theory/Qt - 1)*100:.0f}%")

    if inp.inclination_deg > 20:
        notes.append("   ⚠ 경사각 20° 초과 — 재료 미끄러짐 위험, 경사각 재검토")
    if v > 180:
        notes.append("   ⚠ Belt 속도 180 m/min 초과")

    # ── 모터 선정 ─────────────────────────────────────────────────────────
    motor_result = motor_calc.select_standard_motor(P_req_kW)

    # Belt 구동 드럼 회전수 추정
    drum_dia_m = max(0.3, B_mm / 2000.0 + 0.1)
    drum_rpm   = v / (math.pi * drum_dia_m)

    notes.append(f"■ 구동 드럼 추정 직경: {drum_dia_m*1000:.0f} mm → 드럼 회전수: {drum_rpm:.1f} rpm")

    # ── 베어링 선정 ──────────────────────────────────────────────────────────
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

    # ── 샤프트 설계 ──────────────────────────────────────────────────────────
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

    # ── 감속기 선정 ──────────────────────────────────────────────────────────
    r_adj = ReducerInput(
        input_power_kW=motor_result.selected_motor_kW,
        input_speed_rpm=motor_result.rated_rpm,
        output_speed_rpm=drum_rpm,
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
        equipment_type="벨트 컨베이어",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        capacity_tph=Qt_theory,
        calculation_notes=notes,
    )
