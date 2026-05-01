"""Drag Conveyor 통합 계산기
핸드북 Chapter 4 공식:
  수평: H = Qt × F × L × (1.2 + 0.3N) / (300 × E)  [HP]
  경사: H = Qt × (1.2 + 0.3N) × (F×L + H) / (300 × E)  [HP]
"""
from models.input_models import DragConveyorInput, BearingInput, ShaftInput, ReducerInput, VBeltInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, VBeltSelector


# 통상 Chain 속도 (m/min) — Drag Conveyor 특성상 느림
_CHAIN_SPEED_MPM = 15.0
# Sprocket PCD (m)
_SPROCKET_PCD_M  = 0.30


def calculate(inp: DragConveyorInput,
              bearing_inp: BearingInput,
              shaft_inp: ShaftInput,
              reducer_inp: ReducerInput,
              vbelt_inp: VBeltInput) -> EquipmentResult:

    notes = []
    motor_calc   = MotorCalculator()
    bearing_calc = BearingCalculator()
    shaft_des    = ShaftDesigner()
    reducer_sel  = ReducerSelector()
    vbelt_sel    = VBeltSelector()

    P_kW = motor_calc.calc_drag_conveyor_power(inp)

    if inp.conveyor_height_m > inp.conveyor_length_m * 0.77:  # ≈ tan(45°)
        notes.append("⚠ 경사각 45° 초과 — Drag Conveyor 설계 한계")
    if inp.capacity_tph > 200:
        notes.append("⚠ 처리량 200 T/hr 초과 — Chain 선정 재검토 필요")

    notes.append(f"ℹ F={inp.friction_factor_F}, N(배출구)={inp.num_outlets}, "
                 f"E={inp.mechanical_efficiency} → {P_kW:.2f} kW")

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
    )
    reducer_result = reducer_sel.select_reducer(r_adj)

    vb_adj = VBeltInput(
        design_power_kW=motor_result.selected_motor_kW,
        drive_speed_rpm=motor_result.rated_rpm,
        driven_speed_rpm=sprocket_rpm,
        center_distance_m=vbelt_inp.center_distance_m,
        section=vbelt_inp.section,
    )
    vbelt_result = vbelt_sel.select_vbelt(vb_adj)

    return EquipmentResult(
        equipment_type="드래그 컨베이어",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        vbelt=vbelt_result,
        calculation_notes=notes,
    )
