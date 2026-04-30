from dataclasses import dataclass, field


@dataclass
class MotorResult:
    required_power_kW: float = 0.0
    selected_motor_kW: float = 0.0
    motor_model: str = ""
    iec_frame: str = ""
    rated_rpm: int = 0
    rated_current_A: float = 0.0
    rated_torque_Nm: float = 0.0
    efficiency_pct: float = 0.0
    shaft_dia_mm: float = 0.0


@dataclass
class BearingResult:
    equivalent_load_P_N: float = 0.0
    required_C_N: float = 0.0
    basic_load_rating_C_N: float = 0.0
    L10_hr: float = 0.0
    bearing_number: str = ""
    bearing_type: str = ""
    manufacturer: str = ""
    bore_mm: float = 0.0
    outer_dia_mm: float = 0.0
    width_mm: float = 0.0


@dataclass
class ShaftResult:
    required_diameter_mm: float = 0.0
    selected_diameter_mm: float = 0.0
    von_mises_stress_MPa: float = 0.0
    allowable_stress_MPa: float = 0.0
    safety_factor_actual: float = 0.0
    material: str = ""


@dataclass
class ReducerResult:
    ratio: float = 0.0
    model: str = ""
    input_torque_Nm: float = 0.0
    output_torque_Nm: float = 0.0
    efficiency_pct: float = 0.0
    frame_size: str = ""


@dataclass
class VBeltResult:
    section: str = ""
    belt_length_mm: float = 0.0
    belt_length_designation: str = ""
    number_of_belts: int = 0
    drive_pulley_dia_mm: float = 0.0
    driven_pulley_dia_mm: float = 0.0
    actual_ratio: float = 0.0
    contact_angle_deg: float = 0.0


@dataclass
class EquipmentResult:
    equipment_type: str = ""
    motor: MotorResult = field(default_factory=MotorResult)
    bearing_drive: BearingResult = field(default_factory=BearingResult)
    bearing_driven: BearingResult = field(default_factory=BearingResult)
    shaft: ShaftResult = field(default_factory=ShaftResult)
    reducer: ReducerResult = field(default_factory=ReducerResult)
    vbelt: VBeltResult = field(default_factory=VBeltResult)
    calculation_notes: list = field(default_factory=list)
