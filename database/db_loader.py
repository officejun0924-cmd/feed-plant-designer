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
