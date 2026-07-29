"""各fetcherを統合し、docs/data/upcoming.json と docs/data/results.json を生成する。"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
from typing import Any

import net  # noqa: F401

from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

import fetch_boj
import fetch_calendar
import fetch_fred
import fetch_market
import scenario
from config import INDICATORS

DATA_DIR = ROOT / "docs" / "data"
RESULTS_PATH = DATA_DIR / "results.json"
UPCOMING_PATH = DATA_DIR / "upcoming.json"

JST = dt.timezone(dt.timedelta(hours=9))


def _to_jst(iso_utc: str) -> str:
    d = dt.datetime.fromisoformat(iso_utc)
    return d.astimezone(JST).isoformat()


def _load_existing_results() -> list[dict[str, Any]]:
    if not RESULTS_PATH.exists():
        return []
    try:
        return json.loads(RESULTS_PATH.read_text(encoding="utf-8")).get("events", [])
    except (json.JSONDecodeError, OSError):
        return []


def _recent_surprise_history(indicator_key: str, existing_results: list[dict[str, Any]], n: int = 3) -> list[dict[str, Any]]:
    matches = [r for r in existing_results if r.get("indicator") == indicator_key and r.get("beat_forecast") is not None]
    matches.sort(key=lambda r: r["datetime_utc"], reverse=True)
    return [{"beat_forecast": r["beat_forecast"]} for r in matches[:n]]


def _format_value(value_str: str | None, unit: str) -> str | None:
    if value_str is None:
        return None
    try:
        f = float(value_str)
    except ValueError:
        return value_str
    formatted = f"{f:.2f}".rstrip("0").rstrip(".")
    return f"{formatted}{unit}" if unit else formatted


def _fetch_actual_for_event(event: dict[str, Any]) -> dict[str, Any]:
    """過去に発表済みのイベントについて実績値を可能な範囲で取得する。"""
    indicator_key = event["indicator"]
    meta = INDICATORS[indicator_key]
    unit = meta.get("unit", "")

    if "fred_series" in meta:
        data = fetch_fred.fetch_us_indicator(indicator_key)
        if data is None:
            return {"actual_first_release": None, "actual_latest": None, "was_revised": None, "data_note": "FRED取得失敗"}
        return {
            "actual_period": data["period"],
            "actual_first_release": _format_value(data["first_release_value"], unit),
            "actual_first_release_date": data["first_release_date"],
            "actual_latest": _format_value(data["latest_value"], unit),
            "actual_latest_date": data["latest_revision_date"],
            "was_revised": data["was_revised"],
            "data_note": None,
        }

    if meta.get("boj_statement"):
        decision = fetch_boj.fetch_latest_decision()
        if decision is None or decision.get("rate_percent") is None:
            return {
                "actual_first_release": None,
                "actual_latest": None,
                "was_revised": None,
                "data_note": "BOJ声明の自動解析に失敗。手動確認が必要です。",
            }
        rate = f"{decision['rate_percent']}%"
        return {
            "actual_period": decision["meeting_date"],
            "actual_first_release": rate,
            "actual_first_release_date": decision["meeting_date"],
            "actual_latest": rate,
            "actual_latest_date": decision["meeting_date"],
            "was_revised": False,
            "data_note": None,
        }

    if meta.get("estat"):
        return {
            "actual_first_release": None,
            "actual_latest": None,
            "was_revised": None,
            "data_note": "e-Stat未連携のため実績値は未取得(今後対応予定)",
        }

    return {"actual_first_release": None, "actual_latest": None, "was_revised": None, "data_note": "未対応の指標です"}


def build() -> None:
    now = dt.datetime.now(dt.timezone.utc)
    ff_events = fetch_calendar.fetch_indicator_events()
    existing_results = _load_existing_results()
    existing_by_key = {(r["indicator"], r["datetime_utc"]): r for r in existing_results}

    upcoming_out: list[dict[str, Any]] = []
    updated_results: dict[tuple[str, str], dict[str, Any]] = dict(existing_by_key)

    for event in ff_events:
        indicator_key = event["indicator"]
        meta = INDICATORS[indicator_key]
        event_dt = dt.datetime.fromisoformat(event["datetime_utc"])
        is_upcoming = event_dt > now

        base = {
            "indicator": indicator_key,
            "label": meta["label"],
            "country": meta["country"],
            "ff_title": event["ff_title"],
            "impact": event["impact"],
            "datetime_utc": event["datetime_utc"],
            "datetime_jst": _to_jst(event["datetime_utc"]),
            "forecast": event["forecast"],
            "previous": event["previous"],
        }

        if is_upcoming:
            history = _recent_surprise_history(indicator_key, existing_results)
            base["scenario"] = scenario.build_scenario(indicator_key, event["forecast"], event["previous"], history)
            upcoming_out.append(base)
            continue

        # 過去イベント: 実績値・市場反応を付与してresultsに反映
        key = (indicator_key, event["datetime_utc"])
        actual_info = _fetch_actual_for_event(event)
        try:
            market = fetch_market.get_all_reactions(event_dt.date())
        except Exception as exc:  # noqa: BLE001
            print(f"[build_data] market reaction取得失敗 {indicator_key}: {exc}")
            market = {}

        forecast_val = scenario.parse_value(event["forecast"])
        actual_val = scenario.parse_value(actual_info.get("actual_first_release"))
        beat_forecast = None
        if forecast_val is not None and actual_val is not None and abs(actual_val - forecast_val) > 1e-9:
            beat_forecast = actual_val > forecast_val

        record = {**base, **actual_info, "market_reaction": market, "beat_forecast": beat_forecast}
        updated_results[key] = record

    results_list = sorted(updated_results.values(), key=lambda r: r["datetime_utc"], reverse=True)
    upcoming_out.sort(key=lambda r: r["datetime_utc"])

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPCOMING_PATH.write_text(
        json.dumps({"generated_at": now.isoformat(), "events": upcoming_out}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    RESULTS_PATH.write_text(
        json.dumps({"generated_at": now.isoformat(), "events": results_list}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[build_data] upcoming={len(upcoming_out)} results={len(results_list)}")


if __name__ == "__main__":
    build()
