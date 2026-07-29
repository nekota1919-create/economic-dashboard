"""発表前イベント向けの参考シナリオ文をルールベースで生成する(AI不使用)。

あくまで教科書的な一般論をテンプレート化したもので、実際の相場予測ではない。
画面側でも「機械的生成の参考情報」であることを明示する前提。
"""
from __future__ import annotations

import re
from typing import Any

_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")

# 指標ごとに「予想が前回より高い/上振れ」ときの一般的な市場の解釈
# (タカ派=金融引き締め方向・円高/ドル高要因、ハト派=逆、というざっくりした教科書的整理)
MARKET_TEMPLATES: dict[str, dict[str, str]] = {
    "us_cpi": {
        "higher_is": "インフレ加速(タカ派材料)",
        "lower_is": "インフレ鈍化(ハト派材料)",
        "beat": "予想を上回った場合、Fedの利下げ観測が後退しやすく、米金利上昇・ドル高(円安)/株安に振れやすいとされる",
        "miss": "予想を下回った場合、利下げ観測が強まりやすく、米金利低下・ドル安(円高)/株高に振れやすいとされる",
    },
    "us_nfp": {
        "higher_is": "雇用改善(タカ派材料)",
        "lower_is": "雇用鈍化(ハト派材料)",
        "beat": "予想を上回った場合、労働市場の底堅さが意識され、ドル高(円安)/金利上昇に振れやすいとされる",
        "miss": "予想を下回った場合、景気減速懸念からドル安(円高)/金利低下に振れやすいとされる",
    },
    "us_unemployment": {
        "higher_is": "労働市場の悪化(ハト派材料)",
        "lower_is": "労働市場の改善(タカ派材料)",
        "beat": "予想より低い(改善)場合、ドル高(円安)方向に振れやすいとされる",
        "miss": "予想より高い(悪化)場合、ドル安(円高)方向に振れやすいとされる",
    },
    "us_fomc": {
        "higher_is": "利上げ/据置維持(タカ派)",
        "lower_is": "利下げ(ハト派)",
        "beat": "予想よりタカ派な決定の場合、ドル高(円安)/米金利上昇に振れやすいとされる",
        "miss": "予想よりハト派な決定の場合、ドル安(円高)/米金利低下に振れやすいとされる",
    },
    "jp_cpi": {
        "higher_is": "インフレ加速(日銀の利上げ観測を後押し)",
        "lower_is": "インフレ鈍化(利上げ観測後退)",
        "beat": "予想を上回った場合、日銀の早期利上げ観測から円高方向に振れやすいとされる",
        "miss": "予想を下回った場合、利上げ観測が後退し円安方向に振れやすいとされる",
    },
    "boj_rate": {
        "higher_is": "利上げ(タカ派)",
        "lower_is": "利下げ/据置(ハト派)",
        "beat": "予想よりタカ派な決定の場合、円高方向に振れやすいとされる",
        "miss": "予想よりハト派な決定の場合、円安方向に振れやすいとされる",
    },
}


def parse_value(raw: str | None) -> float | None:
    if not raw:
        return None
    m = _NUM_RE.search(raw)
    if not m:
        return None
    return float(m.group())


def trend_label(forecast: float | None, previous: float | None) -> str:
    if forecast is None or previous is None:
        return "前回との比較データなし"
    diff = forecast - previous
    if abs(diff) < 1e-9:
        return "前回から横ばいの予想"
    return "前回より加速の予想" if diff > 0 else "前回より鈍化の予想"


def surprise_history_text(indicator_key: str, past_results: list[dict[str, Any]]) -> str:
    """past_results: [{"beat_forecast": bool}, ...] 直近が先頭。"""
    if not past_results:
        return "直近のサプライズ傾向: データ蓄積中"
    n = len(past_results)
    beats = sum(1 for r in past_results if r.get("beat_forecast"))
    return f"直近{n}回の発表中{beats}回が予想を上回る結果"


def build_scenario(indicator_key: str, forecast_raw: str | None, previous_raw: str | None,
                    past_results: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    template = MARKET_TEMPLATES.get(indicator_key, {})
    forecast_val = parse_value(forecast_raw)
    previous_val = parse_value(previous_raw)

    lines = [
        f"予想: {forecast_raw or '未発表'} / 前回: {previous_raw or '-'}({trend_label(forecast_val, previous_val)})",
    ]
    if template:
        lines.append(f"上振れ({template.get('higher_is', '')}): {template.get('beat', '')}")
        lines.append(f"下振れ({template.get('lower_is', '')}): {template.get('miss', '')}")
    lines.append(surprise_history_text(indicator_key, past_results or []))
    lines.append("※機械的に生成した一般論の参考情報であり、投資助言ではありません。")

    return {
        "forecast_value": forecast_val,
        "previous_value": previous_val,
        "trend_label": trend_label(forecast_val, previous_val),
        "text_lines": lines,
    }


if __name__ == "__main__":
    import json

    print(
        json.dumps(
            build_scenario("us_cpi", "3.2%", "3.0%", [{"beat_forecast": True}, {"beat_forecast": False}]),
            indent=2,
            ensure_ascii=False,
        )
    )
