from models.input_models import BucketElevatorInput, BearingInput, ShaftInput, ReducerInput, VBeltInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, VBeltSelector


def calculate(inp: BucketElevatorInput,
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

    P_kW = motor_calc.calc_bucket_elevator_power(inp)
    if inp.belt_speed_mps > 2.5:
        notes.append("⚠ 벨트 속도 2.5 m/s 초과 — 재료 이탈 가능성 확인 필요")

    motor_result = motor_calc.select_standard_motor(P_kW)

    # 구동 드럼 회전수 역산
    drum_circum = 0.4  # 드럼 둘레 m (기본값; 실제는 드럼 직경에서 계산)
    drum_rpm = inp.belt_speed_mps * 60.0 / drum_circum

    bearing_inp_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=drum_rpm,
        desired_life_hr=bearing_inp.desired_life_hr,
        bearing_type=bearing_inp.bearing_type,
        reliability=bearing_inp.reliability,
    )
    min_bore = motor_result.shaft_dia_mm
    bearing_drive = bearing_calc.select_bearing(bearing_inp_adj, min_bore_mm=min_bore)
    bearing_driven = bearing_calc.select_bearing(bearing_inp_adj, min_bore_mm=min_bore)

    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(drum_rpm, 1)
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
        output_speed_rpm=drum_rpm,
        service_factor=reducer_inp.service_factor,
    )
    reducer_result = reducer_sel.select_reducer(reducer_inp_adj)

    vbelt_inp_adj = VBeltInput(
        design_power_kW=motor_result.selected_motor_kW,
        drive_speed_rpm=motor_result.rated_rpm,
        driven_speed_rpm=drum_rpm,
        center_distance_m=vbelt_inp.center_distance_m,
        section=vbelt_inp.section,
    )
    vbelt_result = vbelt_sel.select_vbelt(vbelt_inp_adj)

    return EquipmentResult(
        equipment_type="버킷 엘리베이터",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        vbelt=vbelt_result,
        calculation_notes=notes,
    )
