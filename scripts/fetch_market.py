"""yfinanceで指標発表前後の市場反応(前日終値 vs 当日/翌営業日終値)を取得する。"""
from __future__ import annotations

import datetime as dt
from typing import Any

import net  # noqa: F401
import yfinance as yf

from config import MARKET_TICKERS


def _history(ticker: str, around: dt.date, window_days: int = 10):
    start = around - dt.timedelta(days=window_days)
    end = around + dt.timedelta(days=window_days)
    df = yf.Ticker(ticker).history(start=start.isoformat(), end=end.isoformat(), interval="1d")
    df = df[["Close"]].copy()
    df.index = df.index.tz_localize(None) if df.index.tz is not None else df.index
    df["date"] = df.index.date
    return df


def get_reaction(ticker: str, event_date: dt.date) -> dict[str, Any] | None:
    df = _history(ticker, event_date)
    if df.empty:
        return None

    before = df[df["date"] < event_date]
    on_or_after = df[df["date"] >= event_date]

    if before.empty or on_or_after.empty:
        return None

    prev_row = before.iloc[-1]
    post_row = on_or_after.iloc[0]

    prev_close = float(prev_row["Close"])
    post_close = float(post_row["Close"])
    change_pct = (post_close - prev_close) / prev_close * 100 if prev_close else None

    return {
        "ticker": ticker,
        "prev_date": prev_row["date"].isoformat(),
        "prev_close": round(prev_close, 4),
        "post_date": post_row["date"].isoformat(),
        "post_close": round(post_close, 4),
        "change_pct": round(change_pct, 3) if change_pct is not None else None,
    }


def get_all_reactions(event_date: dt.date) -> dict[str, Any]:
    result = {}
    for key, ticker in MARKET_TICKERS.items():
        try:
            reaction = get_reaction(ticker, event_date)
        except Exception as exc:  # noqa: BLE001
            print(f"[fetch_market] {ticker} 取得失敗: {exc}")
            reaction = None
        if reaction is not None:
            result[key] = reaction
    return result


if __name__ == "__main__":
    import json

    today = dt.date.today()
    print(json.dumps(get_all_reactions(today - dt.timedelta(days=5)), indent=2, ensure_ascii=False))
