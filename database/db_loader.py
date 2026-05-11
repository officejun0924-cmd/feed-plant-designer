import json
from functools import lru_cache
from pathlib import Path

DB_DIR = Path(__file__).parent


class DBLoader:
    _cache: dict = {}

    @classmethod
    def _load(cls, fname: str) -> dict:
        if fname not in cls._cache:
            path = DB_DIR / fname
            with open(path, encoding="utf-8") as f:
                cls._cache[fname] = json.load(f)
        return cls._cache[fname]

    @classmethod
    def get_motor_db(cls) -> list:
        return cls._load("motors_iec.json")["motors"]

    @classmethod
    def get_bearing_db(cls, manufacturer: str) -> list:
        fname = f"bearings_{manufacturer.lower()}.json"
        data = cls._load(fname)["bearings"]
        for b in data:
            b["manufacturer"] = manufacturer.upper()
        return data

    @classmethod
    def get_all_bearings(cls) -> list:
        result = []
        for mfr in ["skf", "nsk", "fag"]:
            try:
                data = cls._load(f"bearings_{mfr}.json")["bearings"]
                for b in data:
                    b["manufacturer"] = mfr.upper()
                result.extend(data)
            except Exception:
                pass
        return result

    @classmethod
    def get_vbelt_db(cls) -> dict:
        return cls._load("vbelt_ks.json")["sections"]

    @classmethod
    def get_reducer_db(cls) -> list:
        return cls._load("reducer_catalog.json")["reducers"]

    @classmethod
    def get_ucf_bearing_db(cls) -> list:
        """UC 계열 삽입 베어링 + 하우징 유닛 (UCF/UCP/UCFC)"""
        return cls._load("bearings_ucf.json")["units"]

    @classmethod
    def get_reducer_by_brand(cls, brand: str) -> list:
        """브랜드별 감속기 DB 반환. 효성/SEW/FALK 지원"""
        fname_map = {
            "효성": "reducers_hyosung.json",
            "SEW":  "reducers_sew.json",
            "FALK": "reducers_falk.json",
        }
        fname = fname_map.get(brand, "reducer_catalog.json")
        data = cls._load(fname)
        return data.get("reducers", [])

    @classmethod
    def get_bearing_numbers_by_brand(cls, brand: str) -> list:
        """브랜드/타입별 베어링 번호 목록 반환"""
        if brand in ("UCF", "UCP", "UCFC"):
            units = cls.get_ucf_bearing_db()
            result = []
            for u in units:
                for ht in u.get("housing_types", []):
                    if ht.startswith(brand):
                        result.append(ht)
            return result
        else:
            fname_map = {"SKF": "bearings_skf.json", "NSK": "bearings_nsk.json", "FAG": "bearings_fag.json"}
            fname = fname_map.get(brand.upper())
            if not fname:
                return []
            bearings = cls._load(fname).get("bearings", [])
            return [b["bearing_number"] for b in bearings]

    @classmethod
    def get_bearing_by_number(cls, brand: str, number: str) -> dict:
        """브랜드+번호로 베어링 데이터 반환"""
        if brand in ("UCF", "UCP", "UCFC"):
            units = cls.get_ucf_bearing_db()
            for u in units:
                if number in u.get("housing_types", []):
                    return {
                        "bearing_number": number,
                        "type": "insert_ball",
                        "bore_mm": u["bore_mm"],
                        "outer_dia_mm": u["outer_dia_mm"],
                        "width_mm": u["width_mm"],
                        "C_kN": u["C_kN"],
                        "C0_kN": u["C0_kN"],
                        "manufacturer": "NSK/SNR",
                        "speed_limit_grease_rpm": u.get("speed_limit_rpm", 5000),
                    }
        else:
            fname_map = {"SKF": "bearings_skf.json", "NSK": "bearings_nsk.json", "FAG": "bearings_fag.json"}
            fname = fname_map.get(brand.upper())
            if fname:
                for b in cls._load(fname).get("bearings", []):
                    if b["bearing_number"] == number:
                        b["manufacturer"] = brand.upper()
                        return b
        return {}
