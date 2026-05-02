"""Flow Conveyor 통합 계산기
핸드북 Chapter 3 공식:
  H [HP] = E × L × Qt / 367  (경사 포함 시 수직분 별도 가산)
  Qt [Ton/hr] = 60 × A × V × γ × φ
"""
import math
from models.input_models import FlowConveyorInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS


def calculate(inp: FlowConveyorInput,
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

    P_kW = motor_calc.calc_flow_conveyor_power(inp)

    # 경고 체크
    if inp.inclination_deg > 45:
        notes.append("⚠ 경사각 45° 초과 — 수직 Flow Conveyor 설계 재검토")
    if inp.chain_speed_mpm > 30:
        notes.append("⚠ Chain 속도 30 m/min 초과 — 소음·마모 증가 우려")

    # 이론 운반량 검토 (A = 0.11025 m² 기준 예시)
    # A ≈ width(m) × height(m) × φ
    notes.append(f"ℹ 소요동력 계산: E={inp.E_constant}, L={inp.conveyor_length_m}m, "
                 f"Qt={inp.capacity_tph} T/hr → {P_kW:.2f} kW")

    motor_result = motor_calc.select_standard_motor(P_kW)

    # Sprocket 회전수 추정 (PCD 350mm 기준)
    pcd_m = 0.35
    sprocket_rpm = inp.chain_speed_mpm / (math.pi * pcd_m)

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
        equipment_type="플로우 컨베이어",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
