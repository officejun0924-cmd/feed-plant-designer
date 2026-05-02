# 사료플랜트 기계 설계 계산 프로그램

## 프로젝트 개요
사료플랜트 장비 12종의 모터·베어링·샤프트·V벨트를 KS/ISO 공식으로 계산하고 선정하는 PyQt6 데스크탑 앱.
2026.05 사료플랜트 기계 설계 핸드북(스캔본) 공식을 코드로 구현.

---

## 빠른 시작 (다른 컴퓨터에서 처음 클론할 때)

```bash
git clone https://github.com/officejun0924-cmd/feed-plant-designer
cd feed-plant-designer
py -m pip install -r requirements.txt   # Windows
# python3 -m pip install -r requirements.txt  # Mac/Linux
py main.py
```

> **주의 (Windows)**: `python`, `pip` 대신 `py`를 사용해야 합니다.
> Python 3.10 이상 권장. Python 3.14에서 정상 동작 확인.

---

## 이미 클론된 컴퓨터에서 최신 코드 받기

```bash
cd feed-plant-designer
git pull
py main.py
```

---

## Claude Code로 이어서 작업할 때

```bash
cd feed-plant-designer
claude   # Claude Code 실행 → CLAUDE.md 자동 인식으로 맥락 파악
```

---

## 디렉토리 구조

```
main.py                          # 진입점
app/                             # 전역 설정
  config.py                      # 앱 이름, 버전, IEC 모터 시리즈
  styles.py                      # PyQt6 다크 테마
core/                            # 순수 계산 엔진 (UI 의존 없음)
  motor.py                       # 장비 12종 동력 계산 + IEC 모터 선정
  bearing.py                     # ISO 281 L10 수명 + 베어링 선정
  shaft.py                       # ASME 샤프트 설계
  reducer.py                     # 감속기 + KS B 1400 V벨트 선정
equipment/                       # 장비별 통합 계산기 (core 조합)
  screw_conveyor.py
  bucket_elevator.py
  mixer_pelletizer.py
  grinder_hammer_mill.py
  fan_blower.py
  belt_conveyor.py               # ★ 2026.05 추가 (표1-9/1-10 자동조회)
  flow_conveyor.py               # ★ 2026.05 추가
  drag_conveyor.py               # ★ 2026.05 추가
  bag_filter.py                  # ★ 2026.05 추가
  cyclone.py                     # ★ 2026.05 추가
  rotary_valve.py                # ★ 2026.05 추가
  sieve.py                       # ★ 2026.05 추가 (표14-1 선형보간)
database/                        # JSON DB
  motors.json                    # IEC 모터 26종
  bearings_skf.json              # SKF 베어링 28종
  bearings_nsk.json              # NSK 베어링 17종
  bearings_fag.json              # FAG 베어링 22종
  vbelts.json                    # V벨트 규격
  reducers.json                  # 감속기 규격
models/                          # 입력/결과 dataclass
  input_models.py                # 12개 장비 Input + BearingInput/ShaftInput/…
  result_models.py               # EquipmentResult, MotorResult, …
ui/                              # PyQt6 UI
  main_window.py                 # 12탭 메인 윈도우 + PDF/Excel 내보내기
  base_widget.py                 # 공통 레이아웃 (입력 패널 | 결과 패널)
  components/
    input_group.py               # InputGroup, ComboGroup 위젯
    result_card.py               # 결과 카드, 베어링 테이블
  widgets/                       # 장비별 위젯 (12개)
reports/
  pdf_generator.py               # reportlab PDF 출력
  excel_generator.py             # openpyxl Excel 출력
```

---

## 지원 장비 12종 및 핵심 설계 공식

### 컨베이어류
| 장비 | 공식 출처 | 핵심 공식 |
|---|---|---|
| 스크류 컨베이어 | KS B 6852 | P = (Q·L·Cf·f + Q·H) / (367·η) |
| 버킷 엘리베이터 | — | P = Q·H / (367·η) |
| 벨트 컨베이어 | 핸드북 Ch.1 표1-9/1-10 | P = P₁+P₂+P₃, W·f 자동조회 |
| 플로우 컨베이어 | 핸드북 Ch.3 표3-7 | H[HP] = E×L×Qt / 367 |
| 드래그 컨베이어 | 핸드북 Ch.4 표4-2 | H[HP] = Qt×F×L×(1.2+0.3N) / (300×E) |

### 분리·집진류
| 장비 | 공식 출처 | 핵심 공식 |
|---|---|---|
| 백 필터 | 핸드북 Ch.8/9 | A = Qa/V, N = Qa/(V·π·D·H) |
| 사이클론 | 핸드북 Ch.10 표10-2 | A = Qa/(Va·60), 치수비율 자동계산 |
| 로터리 밸브 | 핸드북 Ch.11 표11-1 | Q = 0.7·W·(1-X)·N·60·γ |
| 체 (Sieve) | 핸드북 Ch.14 표14-1 | Q = (k·l·m·n·o·p)·ρ'·a·q |

### 혼합·분쇄·공조류
| 장비 | 공식 출처 | 핵심 공식 |
|---|---|---|
| 믹서/펠레타이저 | Newton 교반 | P = Np·ρ·n³·D⁵ |
| 분쇄기/해머밀 | Bond 분쇄 법칙 | W = Wi·(10/√P80 − 10/√F80) |
| 팬/블로어 | — | P = Q·ΔP / (η_fan·η·1000) |

### 공통 계산 항목 (전 장비)
- **베어링**: ISO 281 — L10h = (C/P)^p × 10⁶ / (60n)
- **샤프트**: ASME — Te = √[(Km·M)²+(Kt·T)²], d = (16Te/π·Ss)^(1/3)
- **V벨트**: KS B 1400 — 단면 자동 선정, 벨트 길이·개수 계산

---

## 의존 패키지

```
PyQt6 >= 6.6.0
numpy >= 1.26.0
scipy >= 1.12.0
reportlab >= 4.1.0
openpyxl >= 3.1.2
```

---

## 새 장비 추가 방법 (개발 가이드)

1. `models/input_models.py` — `@dataclass class NewEquipInput` 추가
2. `core/motor.py` — `calc_new_equip_power()` 메서드 추가
3. `equipment/new_equip.py` — `calculate()` 함수 작성 (기존 파일 참고)
4. `ui/widgets/new_equip_widget.py` — `BaseEquipmentWidget` 상속 위젯 작성
5. `ui/main_window.py` — import + `_setup_tabs()`에 탭 추가

---

## 개발 현황

- [x] 12개 장비 계산 엔진
- [x] IEC 모터 DB (26종), SKF/NSK/FAG 베어링 DB (각 17~28종)
- [x] PyQt6 다크 테마 UI (12탭)
- [x] PDF / Excel 보고서 출력
- [x] 2026.05 핸드북 기반 장비 7종 추가
- [x] Belt Conveyor 표1-9/1-10 자동조회, 운반량 정확 공식 적용
- [ ] 계산 결과 JSON 저장/불러오기
- [ ] 추가 장비 (냉각기, 스팀믹서, 펠렛밀 등)
- [ ] 단위 환산 도구
