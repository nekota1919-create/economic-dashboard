"""Forex Factory の公開カレンダーJSONを取得し、対象指標にマッチするイベントだけ抽出する。

注意: Forex Factory は公式APIを提供していない。この週次JSON
(https://nfs.faireconomy.media/ff_calendar_thisweek.json) は同社サイトが配信する
公開ファイルで、多くの個人・OSSプロジェクトが個人利用の範囲で参照している実例があるが、
利用規約上グレーゾーンであることを認識した上で、低頻度(1日3回)・個人利用に限定して使う。
将来配信停止/ブロックされる可能性があるため、失敗時は例外を投げず空リストで継続する。
"""
from __future__ import annotations

import datetime as dt
from typing import Any

import net  # noqa: F401  (truststore injection, must import before requests use)
import requests

from config import FF_CALENDAR_URL, FF_COUNTRY_TO_REGION, FF_TITLE_KEYWORDS, INDICATORS

USER_AGENT = "Mozilla/5.0 (personal economic dashboard; contact via GitHub repo)"


def _match_indicator(title: str, ff_country: str) -> str | None:
    region = FF_COUNTRY_TO_REGION.get(ff_country)
    if region is None:
        return None
    title_norm = title.strip().lower()
    for key, keywords in FF_TITLE_KEYWORDS.items():
        if INDICATORS[key]["country"] != region:
            continue
        for kw in keywords:
            if kw.strip().lower() == title_norm:
                return key
    return None


def fetch_raw_events() -> list[dict[str, Any]]:
    try:
        resp = requests.get(FF_CALENDAR_URL, headers={"User-Agent": USER_AGENT}, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: BLE001
        print(f"[fetch_calendar] 取得失敗、空リストで継続: {exc}")
        return []


def fetch_indicator_events() -> list[dict[str, Any]]:
    """対象5指標にマッチするイベントを正規化して返す。"""
    raw = fetch_raw_events()
    events: list[dict[str, Any]] = []
    for item in raw:
        title = item.get("title", "")
        ff_country = item.get("country")
        indicator_key = _match_indicator(title, ff_country)
        if indicator_key is None:
            continue
        try:
            event_dt = dt.datetime.fromisoformat(item["date"])
        except (KeyError, ValueError):
            continue
        events.append(
            {
                "indicator": indicator_key,
                "ff_title": title,
                "country": item.get("country"),
                "impact": item.get("impact"),
                "datetime_utc": event_dt.astimezone(dt.timezone.utc).isoformat(),
                "forecast": item.get("forecast") or None,
                "previous": item.get("previous") or None,
            }
        )
    events.sort(key=lambda e: e["datetime_utc"])
    return events


if __name__ == "__main__":
    import json

    print(json.dumps(fetch_indicator_events(), indent=2, ensure_ascii=False))
