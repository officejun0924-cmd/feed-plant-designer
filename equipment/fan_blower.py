from models.input_models import FanBlowerInput, BearingInput, ShaftInput, ReducerInput, VBeltInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, VBeltSelector


def calculate(inp: FanBlowerInput,
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

    P_kW = motor_calc.calc_fan_power(inp)
    v_ms = inp.flow_rate_m3h / 3600.0
    if inp.static_pressure_pa > 5000:
        notes.append("⚠ 정압 5000 Pa 초과 — 블로어 또는 압축기 사양 검토 권장")
    if inp.fan_efficiency < 0.65:
        notes.append("⚠ 팬 효율 65% 미만 — 임펠러 설계 또는 팬 선정 재검토")

    motor_result = motor_calc.select_standard_motor(P_kW)

    fan_rpm = bearing_inp.shaft_speed_rpm  # 팬 회전수 = 베어링 입력 rpm
    bearing_inp_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=fan_rpm,
        desired_life_hr=bearing_inp.desired_life_hr,
        bearing_type=bearing_inp.bearing_type,
        reliability=bearing_inp.reliability,
    )
    min_bore = motor_result.shaft_dia_mm
    bearing_drive = bearing_calc.select_bearing(bearing_inp_adj, min_bore_mm=min_bore)
    bearing_driven = bearing_calc.select_bearing(bearing_inp_adj, min_bore_mm=min_bore)

    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(fan_rpm, 1)
    shaft_inp_adj = ShaftInput(
        torque_Nm=T_Nm,
        bending_moment_Nm=shaft_inp.bending_moment_Nm,
        material=shaft_inp.material,
        safety_factor=shaft_inp.safety_factor,
        km_factor=shaft_inp.km_factor,
        kt_factor=shaft_inp.kt_factor,
    )
    shaft_result = shaft_designer.design(shaft_inp_adj)

    reducer_inp_adj = ReducerInput(
        input_power_kW=motor_result.selected_motor_kW,
        input_speed_rpm=motor_result.rated_rpm,
        output_speed_rpm=fan_rpm,
        service_factor=reducer_inp.service_factor,
    )
    reducer_result = reducer_sel.select_reducer(reducer_inp_adj)

    vbelt_inp_adj = VBeltInput(
        design_power_kW=motor_result.selected_motor_kW,
        drive_speed_rpm=motor_result.rated_rpm,
        driven_speed_rpm=fan_rpm,
        center_distance_m=vbelt_inp.center_distance_m,
        section=vbelt_inp.section,
    )
    vbelt_result = vbelt_sel.select_vbelt(vbelt_inp_adj)

    return EquipmentResult(
        equipment_type="팬/블로어",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        vbelt=vbelt_result,
        calculation_notes=notes,
    )
