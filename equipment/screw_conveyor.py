import math
from models.input_models import ScrewConveyorInput, BearingInput, ShaftInput, ReducerInput, ChainInput
from models.result_models import EquipmentResult
from core.motor import MotorCalculator
from core.bearing import BearingCalculator
from core.shaft import ShaftDesigner
from core.reducer import ReducerSelector, ChainSelector
from app.config import DIRECT_COUPLING_BRANDS


def calculate(inp: ScrewConveyorInput,
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

    # ── 이론 운반 용량 ─────────────────────────────────────────────────────
    # Q_theory = 60 × (π/4) × D² × S × n × ψ × ρ  [t/h]
    D = inp.screw_diameter_m
    S = inp.screw_pitch_m
    n = inp.screw_speed_rpm
    psi = inp.fill_efficiency
    rho = inp.specific_gravity   # t/m³
    Q_theory = 60.0 * (math.pi / 4.0) * D**2 * S * n * psi * rho
    notes.append(f"이론 운반 용량: {Q_theory:.2f} t/h  (D={D}m, S={S}m, n={n:.0f}rpm, ψ={psi:.2f}, ρ={rho} t/m³)")

    if Q_theory > 0 and abs(inp.capacity_tph - Q_theory) / Q_theory > 0.20:
        notes.append(f"⚠ 설계 운반 용량({inp.capacity_tph:.1f} t/h)이 이론값과 20% 이상 차이")

    # ── 소요 동력 (KS B 6852) ─────────────────────────────────────────────
    P_kW = motor_calc.calc_screw_conveyor_power(inp)

    if inp.fill_efficiency > 0.45:
        notes.append(f"⚠ 충만효율 {inp.fill_efficiency:.2f} > 0.45 — 재료 흘러내림 위험 검토 필요")
    if inp.inclination_deg > 20:
        notes.append("⚠ 경사각 20° 초과 — 스크류 직경 확대 검토 권장")

    motor_result = motor_calc.select_standard_motor(P_kW)

    # ── 베어링 선정 ────────────────────────────────────────────────────────
    min_bore = motor_result.shaft_dia_mm
    btype = bearing_inp.bearing_type
    b_inp_adj = BearingInput(
        radial_load_N=bearing_inp.radial_load_N,
        axial_load_N=bearing_inp.axial_load_N,
        shaft_speed_rpm=inp.screw_speed_rpm,
        desired_life_hr=bearing_inp.desired_life_hr,
        bearing_type=btype,
        reliability=bearing_inp.reliability,
    )

    if btype in ("UCF", "UCP", "UCFC"):
        bearing_drive = bearing_calc.select_ucf_bearing(b_inp_adj, btype, min_bore)
        bearing_driven = bearing_calc.select_ucf_bearing(b_inp_adj, btype, min_bore)
    else:
        bearing_drive = bearing_calc.select_bearing(b_inp_adj, min_bore_mm=min_bore)
        bearing_driven = bearing_calc.select_bearing(b_inp_adj, min_bore_mm=min_bore)

    # ── 샤프트 설계 ───────────────────────────────────────────────────────
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

    # ── 감속기 선정 ───────────────────────────────────────────────────────
    reducer_inp_adj = ReducerInput(
        input_power_kW=motor_result.selected_motor_kW,
        input_speed_rpm=motor_result.rated_rpm,
        output_speed_rpm=inp.screw_speed_rpm,
        service_factor=reducer_inp.service_factor,
        brand=reducer_inp.brand,
    )
    reducer_result = reducer_sel.select_reducer(reducer_inp_adj)

    # ── 체인 선정 ─────────────────────────────────────────────────────────
    chain_result = chain_sel.select_chain_with_rpm(
        chain_inp,
        design_power_kW=motor_result.selected_motor_kW,
        reducer_brand=reducer_inp.brand,
        output_rpm=inp.screw_speed_rpm,
    )
    if reducer_inp.brand in DIRECT_COUPLING_BRANDS:
        notes.append(f"ℹ {reducer_inp.brand} 감속기 — 직결 구동 (체인 없음)")

    return EquipmentResult(
        equipment_type="스크류 컨베이어",
        motor=motor_result,
        bearing_drive=bearing_drive,
        bearing_driven=bearing_driven,
        shaft=shaft_result,
        reducer=reducer_result,
        chain=chain_result,
        calculation_notes=notes,
    )
