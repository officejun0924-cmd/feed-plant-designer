# CHANGELOG

## [v1.1.0] — 2026-05-01

### 추가 (Added)
2026.05 사료플랜트 기계 설계 핸드북(스캔본) 공식을 기반으로 장비 7종 추가.  
탭 5개 → 12개 확장.

#### 새 장비
| 장비 | 파일 | 핸드북 챕터 | 핵심 공식 |
|---|---|---|---|
| 벨트 컨베이어 | `equipment/belt_conveyor.py` | Ch.1 | P = P₁+P₂+P₃, Pm=P/η |
| 플로우 컨베이어 | `equipment/flow_conveyor.py` | Ch.3 | H[HP] = E×L×Qt/367 |
| 드래그 컨베이어 | `equipment/drag_conveyor.py` | Ch.4 | H[HP] = Qt×F×L×(1.2+0.3N)/(300×E) |
| 백 필터 | `equipment/bag_filter.py` | Ch.8/9 | A=Qa/V, N=Qa/(V·π·D·H) |
| 사이클론 | `equipment/cyclone.py` | Ch.10 | A=Qa/(Va×60), ΔP=λ·Va²/(2g)·γ |
| 로터리 밸브 | `equipment/rotary_valve.py` | Ch.11 | Q=0.7·W·(1-X)·N·60·γ |
| 체 (Sieve) | `equipment/sieve.py` | Ch.14 | Q=(k·l·m·n·o·p)·ρ'·a·q |

#### 새 UI 위젯 (7개)
- `ui/widgets/belt_conveyor_widget.py`
- `ui/widgets/flow_conveyor_widget.py`
- `ui/widgets/drag_conveyor_widget.py`
- `ui/widgets/bag_filter_widget.py`
- `ui/widgets/cyclone_widget.py`
- `ui/widgets/rotary_valve_widget.py`
- `ui/widgets/sieve_widget.py`

### 수정 (Modified)
| 파일 | 변경 내용 |
|---|---|
| `models/input_models.py` | 7개 Input 데이터클래스 추가 (`BeltConveyorInput` ~ `SieveInput`) |
| `core/motor.py` | 7개 동력 계산 메서드 추가 (`calc_belt_conveyor_power` 등) |
| `ui/main_window.py` | import 7개 추가, `_setup_tabs()` 12탭으로 확장, 정보 창 업데이트 |
| `CLAUDE.md` | 12종 장비·공식 표, 새 장비 추가 가이드, 빠른 시작 안내 반영 |

### 특이사항
- 백 필터·사이클론 탭: **모터 = 시스템 Fan 동력** (여과포/치수 설계 결과는 하단 메모 영역에 표시)
- 로터리 밸브: 배출 용량(Ton/hr) 계산 결과 + 표11-1 최대 회전수 경고 자동 표시
- 체(Sieve): 표14-1 기준처리능력 선형 보간, 처리량 충족 여부 자동 판정
- 사이클론 치수: 표10-2 고효율/일반/고용량 비율 적용 → Cyclone 형식 콤보박스 선택으로 자동 계산

---

## [v1.0.0] — 2026-04 (초기 구현)

### 추가 (Added)
#### 장비 5종
- 스크류 컨베이어 (KS B 6852)
- 버킷 엘리베이터
- 믹서/펠레타이저 (Newton 교반 동력수)
- 분쇄기/해머밀 (Bond 분쇄 법칙)
- 팬/블로어

#### 공통 계산 엔진
- 모터 선정: IEC 표준 용량 계열 DB (26종)
- 베어링 수명: ISO 281 L10h, SKF/NSK/FAG DB
- 샤프트 설계: ASME Te 공식
- 감속기 + V벨트: KS B 1400

#### 기타
- PyQt6 다크 테마 UI (5탭, 좌우 분할 레이아웃)
- PDF 보고서 (reportlab)
- Excel 보고서 (openpyxl)
- CLAUDE.md 작성 (Claude Code 연동용 프로젝트 문서)
