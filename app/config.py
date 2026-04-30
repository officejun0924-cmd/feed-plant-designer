APP_NAME = "사료플랜트 기계 설계 계산기"
APP_VERSION = "1.0.0"

IEC_MOTOR_SERIES = [
    0.18, 0.25, 0.37, 0.55, 0.75, 1.1, 1.5, 2.2,
    3.0, 4.0, 5.5, 7.5, 11.0, 15.0, 18.5, 22.0,
    30.0, 37.0, 45.0, 55.0, 75.0, 90.0, 110.0, 132.0, 160.0, 200.0,
]

KS_PREFERRED_DIAMETERS = [
    20, 22, 25, 28, 30, 32, 35, 38, 40, 42, 45, 48, 50,
    55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 110, 120,
    130, 140, 150, 160, 180, 200,
]

SHAFT_MATERIALS = {
    "S45C":   {"Sy_MPa": 490, "Su_MPa": 690, "Se_MPa": 275},
    "SCM440": {"Sy_MPa": 835, "Su_MPa": 980, "Se_MPa": 412},
    "SNC836": {"Sy_MPa": 980, "Su_MPa": 1130, "Se_MPa": 520},
}

# ISO 281 a1 신뢰도 계수
RELIABILITY_A1 = {
    90: 1.00,
    95: 0.62,
    96: 0.53,
    97: 0.44,
    98: 0.33,
    99: 0.21,
}

# KS B 1400 V벨트 단면 데이터
VBELT_SECTIONS = {
    "A": {"top_width_mm": 13, "height_mm": 8,  "pitch_dia_min_mm": 75,  "power_base_kW": 0.4},
    "B": {"top_width_mm": 17, "height_mm": 11, "pitch_dia_min_mm": 125, "power_base_kW": 0.9},
    "C": {"top_width_mm": 22, "height_mm": 14, "pitch_dia_min_mm": 200, "power_base_kW": 2.2},
    "D": {"top_width_mm": 32, "height_mm": 19, "pitch_dia_min_mm": 355, "power_base_kW": 5.5},
}
