# 사료플랜트 기계 설계 계산 프로그램

## 프로젝트 개요
사료플랜트 장비(스크류 컨베이어, 버킷 엘리베이터, 믹서/펠레타이저, 해머밀, 팬/블로어)의
모터·베어링·샤프트·V벨트를 KS/ISO 공식으로 계산하고 선정하는 PyQt6 데스크탑 앱.

## 실행 방법
```bash
git clone https://github.com/officejun0924-cmd/feed-plant-designer
cd feed-plant-designer
pip install -r requirements.txt
python main.py
```

## 디렉토리 구조
```
main.py              # 진입점
app/                 # 전역 설정 (config.py, styles.py)
core/                # 순수 계산 엔진
  motor.py           # 장비별 동력 계산 + IEC 모터 선정
  bearing.py         # ISO 281 L10 수명 + 베어링 선정
  shaft.py           # ASME 샤프트 설계
  reducer.py         # 감속기 + KS B 1400 V벨트 선정
equipment/           # 장비별 통합 계산기 (core 조합)
database/            # JSON DB (모터, 베어링 SKF/NSK/FAG, V벨트, 감속기)
models/              # 입력/결과 dataclass
ui/                  # PyQt6 UI (main_window, base_widget, 장비별 위젯)
reports/             # PDF (reportlab), Excel (openpyxl) 보고서
```

## 핵심 설계 공식
- **모터**: KS B 6852 (스크류), Q·H/367η (버킷), Newton Np (믹서), Bond Wi (해머밀), Q·ΔP/η (팬)
- **베어링**: ISO 281 — L10h = (C/P)^p × 10⁶ / (60n)
- **샤프트**: ASME — Te = √[(Km·M)²+(Kt·T)²], d = (16Te/π·Ss)^(1/3)
- **V벨트**: KS B 1400 — 단면 자동 선정, 벨트 길이·개수 계산

## 의존 패키지
- PyQt6, numpy, reportlab, openpyxl

## 개발 현황
- [x] 5개 장비 계산 엔진
- [x] IEC 모터 DB (26종), SKF/NSK/FAG 베어링 DB (각 17~28종)
- [x] PyQt6 다크 테마 UI
- [x] PDF / Excel 보고서 출력
- [ ] 계산 결과 JSON 저장/불러오기
- [ ] 추가 장비 (냉각기, 스팀믹서 등)
