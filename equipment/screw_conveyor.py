from models.input_models import ScrewConveyorInput, BearingInput, ShaftInput, ReducerInput, VBeltInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, VBeltSelector


def calculate(inp: ScrewConveyorInput,
              bearing_inp: BearingInput,
              shaft_inp: ShaftInput,
              reducer_inp: ReducerInput,
              vbelt_inp: VBeltInput) -> EquipmentResult:

    notes = []
    motor_calc = MotorCalculator()
    bearing_calc = BearingCalculator()
    shaft_designer = ShaftDesigner()
    reducer_sel = ReducerSelector()
    vbelt_sel = VBeltSelector()

    P_kW = motor_calc.calc_screw_conveyor_power(inp)
    if inp.fill_ratio > 0.45:
        notes.append("⚠ 충전율 0.45 초과 — 재료 흘러내림 위험")
    if inp.inclination_deg > 20:
        notes.append("⚠ 경사각 20° 초과 — 스크류 직경 확대 검토 권장")

    motor_result = motor_calc.select_standard_motor(P_kW)

    # 베어링 하중 자동 추정: 스크류 자중 + 재료 하중
    bearing_inp_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=inp.screw_speed_rpm,
        desired_life_hr=bearing_inp.desired_life_hr,
        bearing_type=bearing_inp.bearing_type,
        reliability=bearing_inp.reliability,
    )
    min_bore = motor_result.shaft_dia_mm
    bearing_drive = bearing_calc.select_bearing(bearing_inp_adj, min_bore_mm=min_bore)
    bearing_driven = bearing_calc.select_bearing(bearing_inp_adj, min_bore_mm=min_bore)

    # 샤프트: 모터 토크 기반 자동 계산
    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(inp.screw_speed_rpm, 1)
    shaft_inp_adj = ShaftInput(
        torque_Nm=T_Nm,
        bending_moment_Nm=shaft_inp.bending_moment_Nm,
        material=shaft_inp.material,
        safety_factor=shaft_inp.safety_factor,
        km_factor=shaft_inp.km_factor,
        kt_factor=shaft_inp.kt_factor,
    )
    shaft_result = shaft_designer.design(shaft_inp_adj)

    # 감속기
    reducer_inp_adj = ReducerInput(
        input_power_kW=motor_result.selected_motor_kW,
        input_speed_rpm=motor_result.rated_rpm,
        output_speed_rpm=inp.screw_speed_rpm,
        service_factor=reducer_inp.service_factor,
    )
    reducer_result = reducer_sel.select_reducer(reducer_inp_adj)

    # V벨트
    vbelt_inp_adj = VBeltInput(
        design_power_kW=motor_result.selected_motor_kW * vbelt_inp.design_power_kW / max(vbelt_inp.design_power_kW, 1),
        drive_speed_rpm=motor_result.rated_rpm,
        driven_speed_rpm=inp.screw_speed_rpm,
        center_distance_m=vbelt_inp.center_distance_m,
        section=vbelt_inp.section,
    )
    vbelt_inp_adj.design_power_kW = motor_result.selected_motor_kW
    vbelt_result = vbelt_sel.select_vbelt(vbelt_inp_adj)

    return EquipmentResult(
        equipment_type="스크류 컨베이어",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        vbelt=vbelt_result,
        calculation_notes=notes,
    )
