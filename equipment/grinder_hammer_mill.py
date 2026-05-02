from models.input_models import GrinderHammerMillInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS


def calculate(inp: GrinderHammerMillInput,
              bearing_inp: BearingInput,
              shaft_inp: ShaftInput,
              reducer_inp: ReducerInput,
              chain_inp: ChainInput) -> EquipmentResult:

    notes = []
    motor_calc = MotorCalculator()
    bearing_calc = BearingCalculator()
    shaft_designer = ShaftDesigner()
    reducer_sel = ReducerSelector()
    chain_sel = ChainSelector()

    P_kW = motor_calc.calc_hammermill_power(inp)
    notes.append(f"ℹ Bond 분쇄 법칙: Wi={inp.material_hardness} kWh/t, F80={inp.feed_size_mm}mm → P80={inp.product_size_mm}mm")
    if inp.rotor_speed_rpm > 3600:
        notes.append("⚠ 로터 속도 3600 rpm 초과 — 동적 균형 및 베어링 발열 주의")

    motor_result = motor_calc.select_standard_motor(P_kW)

    bearing_inp_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=inp.rotor_speed_rpm,
        desired_life_hr=bearing_inp.desired_life_hr,
        bearing_type=bearing_inp.bearing_type,
        reliability=bearing_inp.reliability,
    )
    min_bore = motor_result.shaft_dia_mm
    bearing_drive = bearing_calc.select_bearing(bearing_inp_adj, min_bore_mm=min_bore)
    bearing_driven = bearing_calc.select_bearing(bearing_inp_adj, min_bore_mm=min_bore)

    T_Nm = 9550.0 * motor_result.selected_motor_kW / max(inp.rotor_speed_rpm, 1)
    shaft_inp_adj = ShaftInput(
        torque_Nm=T_Nm,
        bending_moment_Nm=shaft_inp.bending_moment_Nm,
        material=shaft_inp.material,
        safety_factor=shaft_inp.safety_factor,
        km_factor=shaft_inp.km_factor,
        kt_factor=shaft_inp.kt_factor,
    )
    shaft_result = shaft_designer.design(shaft_inp_adj)

    # 해머밀은 직결 또는 체인만 (감속기 없음이 일반적이지만 DB에서 가장 가까운 선정)
    reducer_inp_adj = ReducerInput(
        input_power_kW=motor_result.selected_motor_kW,
        input_speed_rpm=motor_result.rated_rpm,
        output_speed_rpm=inp.rotor_speed_rpm,
        service_factor=reducer_inp.service_factor,
        brand=reducer_inp.brand,
    )
    if abs(motor_result.rated_rpm - inp.rotor_speed_rpm) / max(inp.rotor_speed_rpm, 1) < 0.05:
        notes.append("ℹ 모터와 로터 속도가 유사 — 직결 구동 검토 가능")
    reducer_result = reducer_sel.select_reducer(reducer_inp_adj)

    chain_result = chain_sel.select_chain_with_rpm(
        chain_inp,
        design_power_kW=motor_result.selected_motor_kW,
        reducer_brand=reducer_inp.brand,
        output_rpm=motor_result.rated_rpm / max(reducer_result.ratio, 1),
    )
    if reducer_inp.brand in DIRECT_COUPLING_BRANDS:
        notes.append(f"ℹ {reducer_inp.brand} 감속기 — 직결 구동 (체인 없음)")

    return EquipmentResult(
        equipment_type="분쇄기/해머밀",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
