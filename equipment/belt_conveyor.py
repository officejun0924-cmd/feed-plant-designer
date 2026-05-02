"""Belt Conveyor 통합 계산기
핸드북 Chapter 1 공식:
  P = P1 + P2 + P3,  Pm = P / η
"""
import math
from models.input_models import BeltConveyorInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS


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

    P_kW = motor_calc.calc_belt_conveyor_power(inp)

    # 운반 용량 검토 (Qt ≤ 200 T/hr)
    if inp.capacity_tph > 200:
        notes.append("⚠ 운반량 200 Ton/hr 초과 — Belt Conveyor 상한 초과")
    if inp.inclination_deg > 20:
        notes.append("⚠ 경사각 20° 초과 — 재료 미끄러짐 위험, 경사각 재검토 권장")
    if inp.belt_speed_mpm > 180:
        notes.append("⚠ Belt 속도 180 m/min 초과")

    # 운반 용량 역산 표시
    theta = math.radians(inp.inclination_deg)
    B_m = inp.belt_width_mm / 1000.0
    k_val = 0.1488   # 표1-5 Trough 35°, 동안식각 20° 기준
    Qt_check = 60 * k_val * (0.9 * B_m - 0.05) ** 2 * inp.belt_speed_mpm * 0.65
    notes.append(f"ℹ 이론 운반량(Trough35°, φ=0.65): {Qt_check:.1f} Ton/hr")

    motor_result = motor_calc.select_standard_motor(P_kW)

    # Belt 구동 드럼 회전수 추정
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
