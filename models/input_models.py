from dataclasses import dataclass, field
from enum import Enum


class EquipmentType(Enum):
    SCREW_CONVEYOR = "screw_conveyor"
    BUCKET_ELEVATOR = "bucket_elevator"
    MIXER_PELLETIZER = "mixer_pelletizer"
    GRINDER_HAMMERMILL = "grinder_hammer_mill"
    FAN_BLOWER = "fan_blower"


@dataclass
class ScrewConveyorInput:
    capacity_tph: float = 20.0
    material_density: float = 600.0       # kg/m³
    screw_diameter_m: float = 0.3         # m
    screw_pitch_m: float = 0.3            # m
    screw_speed_rpm: float = 50.0         # rpm
    length_m: float = 10.0                # m
    inclination_deg: float = 0.0          # °
    material_factor: float = 1.4          # Cf (사료류 ≈ 1.2~1.8)
    friction_factor: float = 0.05         # f
    fill_ratio: float = 0.45
    drive_efficiency: float = 0.90
    safety_factor: float = 1.25


@dataclass
class BucketElevatorInput:
    capacity_tph: float = 20.0
    material_density: float = 600.0
    lift_height_m: float = 15.0
    bucket_volume_L: float = 5.0
    bucket_spacing_m: float = 0.5
    belt_speed_mps: float = 1.5
    drive_efficiency: float = 0.88
    safety_factor: float = 1.3


@dataclass
class MixerPelletizerInput:
    capacity_tph: float = 5.0
    material_density: float = 500.0
    mixer_diameter_m: float = 0.6
    mixer_length_m: float = 1.5
    paddle_number: int = 12
    shaft_speed_rpm: float = 60.0
    mixing_factor: float = 0.4            # Newton 파워 넘버 Np
    drive_efficiency: float = 0.90
    safety_factor: float = 1.2


@dataclass
class GrinderHammerMillInput:
    capacity_tph: float = 5.0
    material_hardness: float = 12.0       # Bond 작업지수 Wi (kWh/t), 사료 곡물 ≈ 10~15
    feed_size_mm: float = 10.0            # F80 (mm)
    product_size_mm: float = 1.0          # P80 (mm)
    rotor_diameter_m: float = 0.6
    rotor_speed_rpm: float = 3000.0
    drive_efficiency: float = 0.90
    safety_factor: float = 1.35


@dataclass
class FanBlowerInput:
    flow_rate_m3h: float = 5000.0         # m³/hr
    static_pressure_pa: float = 1500.0   # Pa
    air_density: float = 1.2             # kg/m³
    fan_efficiency: float = 0.75
    drive_efficiency: float = 0.95
    safety_factor: float = 1.15


@dataclass
class BearingInput:
    radial_load_N: float = 5000.0
    axial_load_N: float = 0.0
    shaft_speed_rpm: float = 1450.0
    desired_life_hr: float = 25000.0
    bearing_type: str = "deep_groove_ball"   # deep_groove_ball | spherical_roller | cylindrical_roller
    temperature_factor: float = 1.0
    reliability: float = 90.0               # % → ISO 281 a1


@dataclass
class ShaftInput:
    torque_Nm: float = 100.0
    bending_moment_Nm: float = 80.0
    material: str = "S45C"                   # S45C | SCM440 | SNC836
    safety_factor: float = 2.0
    km_factor: float = 1.5                   # 굽힘 충격계수 (점진=1.5, 갑작=2.0)
    kt_factor: float = 1.0                   # 비틀림 충격계수 (점진=1.0, 갑작=1.5)


@dataclass
class ReducerInput:
    input_power_kW: float = 5.5
    input_speed_rpm: float = 1450.0
    output_speed_rpm: float = 50.0
    service_factor: float = 1.5


@dataclass
class VBeltInput:
    design_power_kW: float = 5.5
    drive_speed_rpm: float = 1450.0
    driven_speed_rpm: float = 480.0
    center_distance_m: float = 0.5
    section: str = "auto"                    # auto | A | B | C | D
