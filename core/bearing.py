import math
from models.input_models import BearingInput
from models.result_models import BearingResult
from app.config import RELIABILITY_A1


class BearingCalculator:
    """ISO 281:2007 기준 베어링 수명 계산 및 선정"""

    def calc_equivalent_load(self, Fr: float, Fa: float,
                              C0_N: float, bearing_type: str,
                              e: float = 0.26, X: float = 0.56, Y: float = 1.71) -> float:
        """등가 동하중 P 계산
        deep_groove_ball: ISO 표 1 기준 e, X, Y 인자 사용
        spherical_roller:  P = Fr + Y1*Fa 또는 0.67*Fr + Y2*Fa
        cylindrical_roller: P = Fr (순수 반경 하중만)
        """
        if bearing_type == "cylindrical_roller":
            return Fr

        if bearing_type == "spherical_roller":
            e_sph = 0.3
            Y1, Y2 = 1.5, 2.5
            if Fa == 0 or Fr == 0:
                return Fr
            if Fa / Fr <= e_sph:
                return Fr + Y1 * Fa
            else:
                return 0.67 * Fr + Y2 * Fa

        # deep_groove_ball (default)
        if Fr == 0:
            return max(Fa, 0.0)
        if Fa / Fr <= e:
            return Fr
        else:
            return X * Fr + Y * Fa

    def calc_L10_hours(self, C_N: float, P_N: float,
                       n_rpm: float, p: float = 3.0) -> float:
        """기본 정격 수명 L10h [hr]
        L10 [백만 회전] = (C/P)^p
        L10h = L10 * 1e6 / (60 * n)
        """
        if P_N <= 0 or n_rpm <= 0:
            return float("inf")
        L10_mr = (C_N / P_N) ** p
        return L10_mr * 1e6 / (60.0 * n_rpm)

    def calc_required_C(self, P_N: float, L10h_req: float,
                        n_rpm: float, p: float = 3.0) -> float:
        """요구 기본 동정격하중 C_req 역산
        C_req = P * (L10h * 60 * n / 1e6)^(1/p)
        """
        L10_mr = L10h_req * 60.0 * n_rpm / 1e6
        return P_N * (L10_mr ** (1.0 / p))

    def select_bearing(self, inp: BearingInput,
                       min_bore_mm: float = 0.0) -> BearingResult:
        """
        1. 등가하중 P 계산
        2. 요구 C_req 계산
        3. DB에서 bore >= min_bore, C >= C_req 조건 SKF→NSK→FAG 순 최소 외경 선정
        """
        from database.db_loader import DBLoader

        p = 3.0 if "ball" in inp.bearing_type else 10.0 / 3.0

        # a1 신뢰도 계수
        rel = int(inp.reliability)
        a1 = RELIABILITY_A1.get(rel, 1.0)

        # DB 전체 조회
        all_bearings = DBLoader.get_all_bearings()

        # 타입 필터
        type_map = {
            "deep_groove_ball": "deep_groove_ball",
            "spherical_roller": "spherical_roller",
            "cylindrical_roller": "cylindrical_roller",
        }
        btype = type_map.get(inp.bearing_type, "deep_groove_ball")
        candidates = [b for b in all_bearings if b.get("type") == btype]
        if not candidates:
            candidates = all_bearings

        results = []
        for b in candidates:
            C_N = b["C_kN"] * 1000.0
            C0_N = b["C0_kN"] * 1000.0
            e = b.get("e_factor", 0.26)
            X = b.get("X_factor", 0.56)
            Y = b.get("Y_factor", 1.71)

            P_N = self.calc_equivalent_load(
                inp.radial_load_N, inp.axial_load_N, C0_N, btype, e, X, Y
            )
            C_req = self.calc_required_C(P_N, inp.desired_life_hr / a1, inp.shaft_speed_rpm, p)

            bore = b["bore_mm"]
            if bore < min_bore_mm:
                continue
            if C_N >= C_req:
                L10h = self.calc_L10_hours(C_N, P_N, inp.shaft_speed_rpm, p) * a1
                results.append((b, P_N, C_req, C_N, L10h))

        if not results:
            # 조건 미달 → 가장 큰 C 선정
            b = max(candidates, key=lambda x: x["C_kN"])
            C_N = b["C_kN"] * 1000.0
            C0_N = b["C0_kN"] * 1000.0
            e = b.get("e_factor", 0.26)
            X = b.get("X_factor", 0.56)
            Y = b.get("Y_factor", 1.71)
            P_N = self.calc_equivalent_load(
                inp.radial_load_N, inp.axial_load_N, C0_N, btype, e, X, Y
            )
            C_req = self.calc_required_C(P_N, inp.desired_life_hr, inp.shaft_speed_rpm, p)
            L10h = self.calc_L10_hours(C_N, P_N, inp.shaft_speed_rpm, p)
            selected_b, P_N_s, C_req_s, C_N_s, L10h_s = b, P_N, C_req, C_N, L10h
        else:
            # SKF 우선, 같은 제조사 내 최소 외경
            for mfr in ["SKF", "NSK", "FAG"]:
                mfr_res = [r for r in results if r[0].get("manufacturer", "").upper() == mfr]
                if mfr_res:
                    selected = min(mfr_res, key=lambda r: r[0]["outer_dia_mm"])
                    break
            else:
                selected = min(results, key=lambda r: r[0]["outer_dia_mm"])
            selected_b, P_N_s, C_req_s, C_N_s, L10h_s = selected

        return BearingResult(
            equivalent_load_P_N=round(P_N_s, 1),
            required_C_N=round(C_req_s, 0),
            basic_load_rating_C_N=round(C_N_s, 0),
            L10_hr=round(L10h_s, 0),
            bearing_number=selected_b["bearing_number"],
            bearing_type=selected_b.get("type", ""),
            manufacturer=selected_b.get("manufacturer", ""),
            bore_mm=selected_b["bore_mm"],
            outer_dia_mm=selected_b["outer_dia_mm"],
            width_mm=selected_b["width_mm"],
        )

    def select_ucf_bearing(self, inp: BearingInput,
                           housing_type: str = "UCF",
                           min_bore_mm: float = 0.0) -> BearingResult:
        """UCF/UCP/UCFC 하우징 유닛 베어링 선정 (ISO 3228 / KS B 2016).
        UC 삽입 베어링 기반 볼 베어링이므로 p=3.
        housing_type: "UCF" | "UCP" | "UCFC"
        """
        from database.db_loader import DBLoader

        p = 3.0
        rel = int(inp.reliability)
        a1 = RELIABILITY_A1.get(rel, 1.0)

        units = DBLoader.get_ucf_bearing_db()

        # housing_type 코드로 필터 (e.g. "UCF" → "UCF204" 등 포함 여부)
        filtered = [
            u for u in units
            if any(ht.startswith(housing_type) for ht in u.get("housing_types", []))
            and u["bore_mm"] >= min_bore_mm
        ]
        if not filtered:
            filtered = [u for u in units if u["bore_mm"] >= min_bore_mm] or list(units)

        results = []
        for u in filtered:
            C_N = u["C_kN"] * 1000.0
            C0_N = u["C0_kN"] * 1000.0
            P_N = self.calc_equivalent_load(
                inp.radial_load_N, inp.axial_load_N, C0_N, "deep_groove_ball"
            )
            C_req = self.calc_required_C(P_N, inp.desired_life_hr / a1, inp.shaft_speed_rpm, p)
            if C_N >= C_req:
                L10h = self.calc_L10_hours(C_N, P_N, inp.shaft_speed_rpm, p) * a1
                results.append((u, P_N, C_req, C_N, L10h))

        if not results:
            u = max(filtered, key=lambda x: x["C_kN"])
            C_N = u["C_kN"] * 1000.0
            C0_N = u["C0_kN"] * 1000.0
            P_N = self.calc_equivalent_load(inp.radial_load_N, inp.axial_load_N, C0_N, "deep_groove_ball")
            C_req = self.calc_required_C(P_N, inp.desired_life_hr, inp.shaft_speed_rpm, p)
            L10h = self.calc_L10_hours(C_N, P_N, inp.shaft_speed_rpm, p)
            selected_u = u
            P_N_s, C_req_s, C_N_s, L10h_s = P_N, C_req, C_N, L10h
        else:
            best = min(results, key=lambda r: r[0]["outer_dia_mm"])
            selected_u, P_N_s, C_req_s, C_N_s, L10h_s = best

        # 하우징 호칭 생성 (e.g. UCF + 208 → UCF208)
        uc_num = selected_u["designation"].replace("UC", "")   # "204" etc.
        bearing_number = f"{housing_type}{uc_num}"

        return BearingResult(
            equivalent_load_P_N=round(P_N_s, 1),
            required_C_N=round(C_req_s, 0),
            basic_load_rating_C_N=round(C_N_s, 0),
            L10_hr=round(L10h_s, 0),
            bearing_number=bearing_number,
            bearing_type=f"UC insert ({housing_type} housing)",
            manufacturer="NSK/SNR/NTN",
            bore_mm=selected_u["bore_mm"],
            outer_dia_mm=selected_u["outer_dia_mm"],
            width_mm=selected_u["width_mm"],
        )
