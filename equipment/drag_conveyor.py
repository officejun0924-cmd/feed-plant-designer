"""Drag Conveyor 통합 계산기
핸드북 Chapter 4 공식:
  수평: H = Qt × F × L × (1.2 + 0.3N) / (300 × E)  [HP]
  경사: H = Qt × (1.2 + 0.3N) × (F×L + H) / (300 × E)  [HP]
"""
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

    P_kW = motor_calc.calc_drag_conveyor_power(inp)

    if inp.conveyor_height_m > inp.conveyor_length_m * 0.77:  # ≈ tan(45°)
        notes.append("⚠ 경사각 45° 초과 — Drag Conveyor 설계 한계")
    if inp.capacity_tph > 200:
        notes.append("⚠ 처리량 200 T/hr 초과 — Chain 선정 재검토 필요")

    # P.81: 운반물 1m당 중량 W = 16.7 × Qt / V  (참고용)
    chain_v = _CHAIN_SPEED_MPM
    W_per_m = 16.7 * inp.capacity_tph / max(chain_v, 1)
    notes.append(f"■ 핸드북 공식: F={inp.friction_factor_F}, N(배출구)={inp.num_outlets}, "
                 f"E={inp.mechanical_efficiency} → {P_kW:.2f} kW")
    notes.append(f"■ 운반물 1m당 중량 W = {W_per_m:.1f} kg/m  (V={chain_v} m/min 기준)")

    motor_result = motor_calc.select_standard_motor(P_kW)

    import math
    sprocket_rpm = _CHAIN_SPEED_MPM / (math.pi * _SPROCKET_PCD_M)

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

    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(sprocket_rpm, 1)
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
        output_speed_rpm=sprocket_rpm,
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
        equipment_type="드래그 컨베이어",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
