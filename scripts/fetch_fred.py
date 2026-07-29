"""FRED APIから米指標の実績値と改定履歴(ALFRED)を取得する。

FRED APIキーは無料で取得可能: https://fred.stlouisfed.org/docs/api/api_key.html
環境変数 FRED_API_KEY に設定して使う。

`units` パラメータ(pc1=前年比%, chg=前期差, lin=そのまま)をFRED側に渡すことで
前年比/前月差の計算をFREDに任せる。`output_type=2` + `realtime_start`を過去日にすると、
指定した観測期間(period)について「いつ・どんな値として世に出ていたか」の変遷
(=初値→改定値の履歴)がそのまま返ってくる。
"""
from __future__ import annotations

import os
import re
from typing import Any

import net  # noqa: F401
import requests

from config import INDICATORS

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


def _api_key() -> str:
    key = os.environ.get("FRED_API_KEY")
    if not key:
        raise RuntimeError("環境変数 FRED_API_KEY が未設定です")
    return key


def _get(params: dict[str, Any]) -> list[dict[str, Any]]:
    query = {"api_key": _api_key(), "file_type": "json", **params}
    resp = requests.get(FRED_BASE, params=query, timeout=20)
    resp.raise_for_status()
    obs = resp.json().get("observations", [])
    return [o for o in obs if o.get("value") not in (None, ".")]


def get_recent_observations(series_id: str, units: str = "lin", limit: int = 3) -> list[dict[str, Any]]:
    return _get(
        {
            "series_id": series_id,
            "units": units,
            "sort_order": "desc",
            "limit": limit,
        }
    )


def get_revision_history(series_id: str, period_date: str, units: str = "lin") -> list[dict[str, Any]]:
    """指定期間(YYYY-MM-DD)について、初値〜最新までの改定履歴を古い順で返す。

    output_type=2 のレスポンスは1期間1オブジェクトで、
    キーが "{series_id}_{YYYYMMDD}"(改定が反映された日) → 値、という形式になる。
    """
    query = {
        "api_key": _api_key(),
        "file_type": "json",
        "series_id": series_id,
        "units": units,
        "observation_start": period_date,
        "observation_end": period_date,
        "realtime_start": period_date,
        "realtime_end": "9999-12-31",
        "output_type": 2,
    }
    resp = requests.get(FRED_BASE, params=query, timeout=20)
    resp.raise_for_status()
    raw_obs = resp.json().get("observations", [])
    if not raw_obs:
        return []
    row = raw_obs[0]
    # キー例: "PAYEMS_20260211"(units=lin) / "PAYEMS_CHG_20260211"(units=chg等)
    # 末尾8桁が改定が反映された日付(YYYYMMDD)。
    key_pattern = re.compile(rf"^{re.escape(series_id)}_.*?(\d{{8}})$")
    vintages = []
    for key, value in row.items():
        if key == "date" or value in (None, "."):
            continue
        m = key_pattern.match(key)
        if not m:
            continue
        raw_date = m.group(1)
        iso_date = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
        vintages.append({"realtime_start": iso_date, "value": value})
    vintages.sort(key=lambda v: v["realtime_start"])
    return vintages


def fetch_us_indicator(indicator_key: str) -> dict[str, Any] | None:
    meta = INDICATORS[indicator_key]
    series_id = meta["fred_series"]
    units = meta.get("fred_units", "lin")

    recent = get_recent_observations(series_id, units=units, limit=3)
    if not recent:
        print(f"[fetch_fred] {indicator_key}: 観測値が取得できませんでした")
        return None

    latest = recent[0]
    period = latest["date"]
    revisions = get_revision_history(series_id, period, units=units)
    if revisions:
        first_release = revisions[0]
        latest_revised = revisions[-1]
    else:
        first_release = latest_revised = latest

    return {
        "indicator": indicator_key,
        "series_id": series_id,
        "period": period,
        "first_release_value": first_release["value"],
        "first_release_date": first_release["realtime_start"],
        "latest_value": latest_revised["value"],
        "latest_revision_date": latest_revised["realtime_start"],
        "was_revised": first_release["value"] != latest_revised["value"],
    }


def fetch_all_us_indicators() -> dict[str, Any]:
    result = {}
    for key, meta in INDICATORS.items():
        if "fred_series" not in meta:
            continue
        data = fetch_us_indicator(key)
        if data is not None:
            result[key] = data
    return result


if __name__ == "__main__":
    import json

    print(json.dumps(fetch_all_us_indicators(), indent=2, ensure_ascii=False))
