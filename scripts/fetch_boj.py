"""日銀金融政策決定会合の結果(政策金利)をBOJ公式サイトの声明PDFから取得する。

公式インデックスページ(HTML)から声明PDFのリンク一覧を取得し、
直近の「a」枝番(=メインの声明)PDFをテキスト抽出して政策金利を正規表現で抜き出す。
声明の文言が変わる等でパースに失敗した場合はNoneを返し、呼び出し側で
「手動確認待ち」として扱う(パイプライン全体は止めない)。
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Any

import net  # noqa: F401
import requests
from pypdf import PdfReader
import io

INDEX_URL_TMPL = "https://www.boj.or.jp/en/mopo/mpmdeci/state_{year}/index.htm"
LINK_PATTERN = re.compile(r'mpr_(\d{4})/k(\d{6})([a-z])\.pdf')
RATE_PATTERNS = [
    re.compile(r"remain at around\s*([\d.]+)\s*percent", re.IGNORECASE),
    re.compile(r"call rate.{0,80}?([\d.]+)\s*percent", re.IGNORECASE | re.DOTALL),
]
USER_AGENT = "Mozilla/5.0 (personal economic dashboard; contact via GitHub repo)"


def _list_statements(year: int) -> list[dict[str, str]]:
    url = INDEX_URL_TMPL.format(year=year)
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"[fetch_boj] {year}年インデックス取得失敗: {exc}")
        return []
    statements = []
    for m in LINK_PATTERN.finditer(resp.text):
        yyyy, yymmdd, suffix = m.groups()
        if suffix != "a":
            continue  # 主要声明のみ(b/c/dは付属資料)
        date_str = f"20{yymmdd[0:2]}-{yymmdd[2:4]}-{yymmdd[4:6]}"
        statements.append(
            {
                "date": date_str,
                "url": f"https://www.boj.or.jp/en/mopo/mpmdeci/mpr_{yyyy}/k{yymmdd}a.pdf",
            }
        )
    statements.sort(key=lambda s: s["date"])
    return statements


def list_recent_statements(lookback_years: int = 1) -> list[dict[str, str]]:
    this_year = dt.date.today().year
    all_statements: list[dict[str, str]] = []
    for year in range(this_year - lookback_years, this_year + 1):
        all_statements.extend(_list_statements(year))
    all_statements.sort(key=lambda s: s["date"])
    return all_statements


def _extract_rate_from_pdf(pdf_bytes: bytes) -> str | None:
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = reader.pages[0].extract_text() or ""
        text = re.sub(r"\s+", " ", text)  # 改行/連続空白を1個に正規化
    except Exception as exc:  # noqa: BLE001
        print(f"[fetch_boj] PDFテキスト抽出失敗: {exc}")
        return None
    for pattern in RATE_PATTERNS:
        m = pattern.search(text)
        if m:
            return m.group(1)
    return None


def fetch_decision(statement: dict[str, str]) -> dict[str, Any] | None:
    try:
        resp = requests.get(statement["url"], headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"[fetch_boj] PDF取得失敗 {statement['url']}: {exc}")
        return None
    rate = _extract_rate_from_pdf(resp.content)
    if rate is None:
        print(f"[fetch_boj] 金利抽出失敗、手動確認が必要: {statement['url']}")
        return {
            "meeting_date": statement["date"],
            "rate_percent": None,
            "source_url": statement["url"],
            "needs_manual_review": True,
        }
    return {
        "meeting_date": statement["date"],
        "rate_percent": rate,
        "source_url": statement["url"],
        "needs_manual_review": False,
    }


def fetch_latest_decision() -> dict[str, Any] | None:
    statements = list_recent_statements()
    if not statements:
        return None
    return fetch_decision(statements[-1])


if __name__ == "__main__":
    import json

    print(json.dumps(fetch_latest_decision(), indent=2, ensure_ascii=False))
