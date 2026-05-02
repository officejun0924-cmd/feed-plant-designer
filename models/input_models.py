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
    specific_gravity: float = 0.65        # 비중 (t/m³)
    material_name: str = "직접 입력"      # 원재료 이름 (MATERIAL_DB 키)
    screw_diameter_m: float = 0.3         # m
    screw_pitch_m: float = 0.3            # m
    screw_speed_rpm: float = 50.0         # rpm
    length_m: float = 10.0                # m
    inclination_deg: float = 0.0          # °
    material_factor: float = 1.4          # Cf (사료류 ≈ 1.2~1.8)
    friction_factor: float = 0.05         # f
    fill_efficiency: float = 0.45         # 충만효율 ψ
    drive_efficiency: float = 0.90
    safety_factor: float = 1.25


@dataclass
class BucketElevatorInput:
    capacity_tph: float = 20.0
    specific_gravity: float = 0.65        # 비중 (t/m³)
    material_name: str = "직접 입력"
    lift_height_m: float = 15.0
    bucket_volume_L: float = 5.0
    bucket_spacing_m: float = 0.5
    belt_speed_mps: float = 1.5
    drive_efficiency: float = 0.88
    safety_factor: float = 1.3


@dataclass
class MixerPelletizerInput:
    capacity_tph: float = 5.0
    specific_gravity: float = 0.5         # 비중 (t/m³)
    material_name: str = "직접 입력"
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
    brand: str = "효성"                   # 효성 | SEW | FALK


@dataclass
class VBeltInput:
    design_power_kW: float = 5.5
    drive_speed_rpm: float = 1450.0
    driven_speed_rpm: float = 480.0
    center_distance_m: float = 0.5
    section: str = "auto"                    # auto | A | B | C | D


@dataclass
class ChainInput:
    """RS/RF 체인 선정 입력 (KS B 1407)"""
    chain_type: str = "RS"                   # "RS" | "RF"
    num_teeth_small: int = 19                # 소 스프로켓 잇수 Z1
    center_distance_m: float = 0.5           # 축간 거리 (m)


# ── 추가 장비 (2026.05 핸드북 기반) ──────────────────────────────────────

@dataclass
class BeltConveyorInput:
    """Belt Conveyor 소요동력 — 핸드북 4장 공식"""
    capacity_tph: float = 80.0              # 운반량 Qt (Ton/hr)
    belt_width_mm: float = 600.0            # Belt 폭 B (mm)
    belt_speed_mpm: float = 60.0            # Belt 속도 v (m/min)
    conveyor_length_m: float = 20.0         # 수평 길이 l (m)
    inclination_deg: float = 0.0            # 경사각 (°)
    roller_friction_f: float = 0.022        # Roller 회전 마찰계수 f (표1-9)
    moving_parts_W: float = 35.5            # 운반물 이외 운동부 중량 W (kg/m, 표1-10)
    correction_length_l0: float = 66.0      # 기장의 보정길이 l0 (m, 표1-9)
    drive_efficiency: float = 0.85
    safety_factor: float = 1.25


@dataclass
class FlowConveyorInput:
    """Flow Conveyor 소요동력 — 핸드북 3장(Chapter 3) 공식
    H [HP] = E × L × Qt / 367
    """
    capacity_tph: float = 80.0              # 운반량 Qt (Ton/hr)
    conveyor_length_m: float = 15.0         # Conveyor 길이 L (m)
    inclination_deg: float = 0.0            # 경사각 (°)  0=수평
    height_m: float = 0.0                   # 수직 높이 H (m, 경사 시 입력)
    chain_speed_mpm: float = 28.0           # Chain 속도 V (m/min)
    specific_gravity: float = 0.7            # 비중 γ (t/m³)
    fill_efficiency: float = 0.65           # 충만효율 φ
    E_constant: float = 3.9                 # 핸드북 표3-7 상수 (사료류 ≈3.9)
    drive_efficiency: float = 0.85
    safety_factor: float = 1.2


@dataclass
class DragConveyorInput:
    """Drag Conveyor 소요동력 — 핸드북 4장 공식
    수평: H = Qt × F × L × (1.2 + 0.3N) / (300 × E)
    경사: H = Qt × (1.2 + 0.3N) × (F×L + H) / (300 × E)
    """
    capacity_tph: float = 50.0              # 운반량 Qt (Ton/hr)
    conveyor_length_m: float = 10.0         # 수평 길이 L (m)
    conveyor_height_m: float = 0.0          # 수직 높이 H (m)
    num_outlets: int = 1                    # 배출구 수 N
    friction_factor_F: float = 0.55         # 마찰계수 F (표4-2)
    mechanical_efficiency: float = 0.85     # 기계효율 E
    drive_efficiency: float = 0.90
    safety_factor: float = 1.25


@dataclass
class BagFilterInput:
    """Bag Filter 설계 계산 — 핸드북 8장/9장 공식
    여과포 면적: A = Qa / V
    Bag 수량:  N = Qa / (V × π × D × H)
    Fan 동력:  Pm = (Q [m³/s] × ΔP [Pa]) / (η_fan × η_drive × 1000)
    """
    air_volume_m3min: float = 380.0         # 처리 풍량 Qa (m³/min)
    filter_velocity_mmin: float = 1.8       # 여과속도 V (m/min) — 충격식 1.5~4.3
    bag_diameter_m: float = 0.15            # 여과포 직경 D (m)
    bag_height_m: float = 2.5              # 여과포 높이 H (m)
    static_pressure_pa: float = 1500.0     # 백필터 압력손실 ΔP (Pa)
    fan_efficiency: float = 0.75
    drive_efficiency: float = 0.95
    safety_factor: float = 1.15


@dataclass
class CycloneInput:
    """Cyclone 설계 계산 — 핸드북 10장 공식
    입구 단면적: A = Qa / (Va × 60)
    압력손실:   ΔP = λ × Va² / (2g) × γ [mmH₂O]
    Fan 동력:   Pm = (Q [m³/s] × ΔP [Pa]) / (η_fan × η_drive × 1000)
    """
    air_volume_m3min: float = 380.0         # 처리 풍량 Qa (m³/min)
    inlet_velocity_msec: float = 18.0       # 유입 풍속 Va (m/sec) — 최적 15~18
    pressure_loss_coef: float = 12.0        # 압력손실계수 λ (일반 Cyclone ≈ 12)
    air_density: float = 1.2e-3             # 비중 γ (t/m³) → 1.2 kg/m³ = 1.2e-3 t/m³
    cyclone_type: str = "일반"              # 고효율 | 일반 | 고용량
    fan_efficiency: float = 0.72
    drive_efficiency: float = 0.95
    safety_factor: float = 1.15


@dataclass
class RotaryValveInput:
    """Rotary Valve 배출 용량 계산 — 핸드북 11장 공식
    Q = 60 × η × V × N × γ
    V = 0.7 × W × (1-X) × N × 60 × γ  (제2식)
    """
    rotor_diameter_mm: float = 300.0        # Rotor 날개 지름 D (mm)
    rotor_length_m: float = 0.3             # Rotor 날개 길이 L (m)
    shaft_diameter_mm: float = 60.0         # Shaft 직경 d (mm)
    rotation_speed_rpm: float = 30.0        # 회전수 N (rpm) — 통상 25~40
    material_density: float = 0.65          # 분립체 비중 γ (t/m³)
    clearance_ratio: float = 0.1            # 공극률 X (사료=0.1)
    volumetric_efficiency: float = 0.85     # 용적 효율 η
    drive_efficiency: float = 0.90
    safety_factor: float = 1.2


@dataclass
class SieveInput:
    """Sieve(체) 설계 계산 — 핸드북 14장 경험식
    Q = (k·l·m·n·o·p) × ρ' × a × q
    진동 모터 동력 ≈ sieve_area × 0.75 kW/m²
    """
    capacity_tph: float = 50.0              # 목표 처리량 Qt (Ton/hr)
    sieve_opening_mm: float = 3.0           # 체 구멍 크기 (mm)
    sieve_area_m2: float = 4.0             # 체 면적 a (m²)
    material_density: float = 0.65          # 외관상 비중 ρ' (t/m³)
    inclination_deg: float = 15.0           # 경사각 β (°) — 일반 10~20
    # 수정계수 (기본값: 조건 양호)
    k_factor: float = 1.0                   # 입도 수정계수
    l_factor: float = 1.0                   # 입자 형상 수정계수
    m_factor: float = 1.0                   # 수분 수정계수
    n_factor: float = 1.0                   # 입자 밀도 수정계수
    o_factor: float = 1.0                   # 부착성 수정계수
    p_factor: float = 1.0                   # 공급 균일도 수정계수
    drive_efficiency: float = 0.90
    safety_factor: float = 1.2
