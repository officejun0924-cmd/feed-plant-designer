APP_NAME = "사료플랜트 기계 설계 계산기"
APP_VERSION = "1.1.0"

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

# ── 원재료 DB ─────────────────────────────────────────────────────────────
# specific_gravity: 비중 (t/m³),  friction: 마찰계수,  material_factor: 재료계수 Cf
MATERIAL_DB = {
    "직접 입력":             {"specific_gravity": 0.65, "friction": 0.40, "material_factor": 1.4},
    "옥수수 (Corn)":          {"specific_gravity": 0.72, "friction": 0.35, "material_factor": 1.2},
    "밀 (Wheat)":             {"specific_gravity": 0.78, "friction": 0.32, "material_factor": 1.2},
    "보리 (Barley)":          {"specific_gravity": 0.62, "friction": 0.35, "material_factor": 1.2},
    "쌀 (Rice)":              {"specific_gravity": 0.80, "friction": 0.30, "material_factor": 1.1},
    "대두 (Soybean)":         {"specific_gravity": 0.72, "friction": 0.35, "material_factor": 1.3},
    "대두박 (Soybean Meal)":  {"specific_gravity": 0.59, "friction": 0.42, "material_factor": 1.4},
    "쌀겨 (Rice Bran)":       {"specific_gravity": 0.35, "friction": 0.55, "material_factor": 1.8},
    "밀기울 (Wheat Bran)":    {"specific_gravity": 0.26, "friction": 0.50, "material_factor": 1.8},
    "옥수수글루텐 (Corn Gluten)": {"specific_gravity": 0.55, "friction": 0.45, "material_factor": 1.5},
    "어분 (Fish Meal)":       {"specific_gravity": 0.55, "friction": 0.50, "material_factor": 1.6},
    "배합사료 (Mixed Feed)":  {"specific_gravity": 0.65, "friction": 0.40, "material_factor": 1.4},
    "사료 펠렛 (Feed Pellet)":{"specific_gravity": 0.68, "friction": 0.35, "material_factor": 1.2},
    "분쇄사료 (Ground Feed)": {"specific_gravity": 0.55, "friction": 0.45, "material_factor": 1.5},
    "석회석 (Limestone)":     {"specific_gravity": 1.35, "friction": 0.45, "material_factor": 1.5},
    "소금 (Salt)":            {"specific_gravity": 0.90, "friction": 0.45, "material_factor": 1.6},
    "설탕 (Sugar)":           {"specific_gravity": 0.85, "friction": 0.40, "material_factor": 1.4},
    "MCP/DCP":                {"specific_gravity": 0.90, "friction": 0.48, "material_factor": 1.5},
}

# ── RS/RF 체인 단면 데이터 (KS B 1407) ────────────────────────────────────
# Z1=19 소 스프로켓 기준 정격 동력 표 (kW)
# key: rpm → {chain_designation: max_kW}
RS_POWER_TABLE = {
    50:   {"RS-40": 0.5,  "RS-50": 1.1,  "RS-60": 1.8,  "RS-80": 4.5,
           "RS-100": 8.0,  "RS-120": 13.0, "RS-140": 20.0, "RS-160": 28.0},
    100:  {"RS-40": 0.9,  "RS-50": 1.8,  "RS-60": 3.1,  "RS-80": 7.5,
           "RS-100": 13.5, "RS-120": 22.0, "RS-140": 34.0, "RS-160": 48.0},
    200:  {"RS-40": 1.5,  "RS-50": 3.0,  "RS-60": 5.2,  "RS-80": 13.0,
           "RS-100": 23.0, "RS-120": 38.0, "RS-140": 58.0, "RS-160": 82.0},
    500:  {"RS-40": 3.0,  "RS-50": 6.0,  "RS-60": 10.0, "RS-80": 25.0,
           "RS-100": 45.0, "RS-120": 72.0, "RS-140": 108.0,"RS-160": 152.0},
    1000: {"RS-40": 5.0,  "RS-50": 10.0, "RS-60": 16.0, "RS-80": 40.0,
           "RS-100": 72.0, "RS-120": 115.0,"RS-140": 170.0,"RS-160": 240.0},
    1500: {"RS-40": 6.5,  "RS-50": 12.5, "RS-60": 21.0, "RS-80": 52.0,
           "RS-100": 90.0, "RS-120": 140.0,"RS-140": 200.0,"RS-160": 280.0},
}

# RF 체인: 중부하용 (RS 대비 약 1.4배 정격)
RF_POWER_TABLE = {
    50:   {"RF-40": 0.7,  "RF-50": 1.5,  "RF-60": 2.5,  "RF-80": 6.3,
           "RF-100": 11.0, "RF-120": 18.0, "RF-140": 28.0, "RF-160": 39.0},
    100:  {"RF-40": 1.3,  "RF-50": 2.5,  "RF-60": 4.3,  "RF-80": 10.5,
           "RF-100": 19.0, "RF-120": 31.0, "RF-140": 48.0, "RF-160": 67.0},
    200:  {"RF-40": 2.1,  "RF-50": 4.2,  "RF-60": 7.3,  "RF-80": 18.0,
           "RF-100": 32.0, "RF-120": 53.0, "RF-140": 81.0, "RF-160": 115.0},
    500:  {"RF-40": 4.2,  "RF-50": 8.4,  "RF-60": 14.0, "RF-80": 35.0,
           "RF-100": 63.0, "RF-120": 101.0,"RF-140": 151.0,"RF-160": 213.0},
    1000: {"RF-40": 7.0,  "RF-50": 14.0, "RF-60": 22.0, "RF-80": 56.0,
           "RF-100": 101.0,"RF-120": 161.0,"RF-140": 238.0,"RF-160": 336.0},
    1500: {"RF-40": 9.1,  "RF-50": 17.5, "RF-60": 29.4, "RF-80": 72.8,
           "RF-100": 126.0,"RF-120": 196.0,"RF-140": 280.0,"RF-160": 392.0},
}

# 체인 피치 데이터 (mm)
CHAIN_PITCH = {
    "RS-40": 12.70,  "RS-50": 15.875, "RS-60": 19.05,
    "RS-80": 25.40,  "RS-100": 31.75, "RS-120": 38.10,
    "RS-140": 44.45, "RS-160": 50.80,
    "RF-40": 12.70,  "RF-50": 15.875, "RF-60": 19.05,
    "RF-80": 25.40,  "RF-100": 31.75, "RF-120": 38.10,
    "RF-140": 44.45, "RF-160": 50.80,
}

# 감속기 브랜드 (SEW·FALK = 직결, 체인 미사용)
REDUCER_BRANDS = ["효성", "SEW", "FALK"]
DIRECT_COUPLING_BRANDS = ["SEW", "FALK"]   # 이 브랜드 선택 시 체인 없음

# 베어링 하우징 타입
BEARING_HOUSING_TYPES = ["직접 장착", "UCF (4볼트 플랜지)", "UCP (필로우 블록)", "UCFC (2볼트 원형)"]
