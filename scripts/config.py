"""対象指標・データソースの設定。"""

# Forex Factory カレンダーで拾うイベントを判定するタイトル(完全一致、大小文字無視)。
# 一致したら INDICATORS のキーに正規化する。
# 部分一致だと「Official Bank Rate」に対する「MPC Official Bank Rate Votes」のような
# 別イベント(投票内訳など)まで誤って拾ってしまうため、完全一致で厳密にマッチさせる。
# 同一指標内で複数タイトルを許容しているのは、Prelim/Revised GDPのように
# 発表時刻が異なる別イベントとして存在するケースのみ
# (同時刻に存在するheadline/core等の重複ペアは意図的に片方だけ採用している)。
FF_TITLE_KEYWORDS = {
    "us_cpi": ["CPI m/m", "CPI y/y"],
    "us_nfp": ["Non-Farm Employment Change", "Nonfarm Payrolls"],
    "us_unemployment": ["Unemployment Rate"],
    "us_fomc": ["Federal Funds Rate"],
    "us_pce": ["Core PCE Price Index m/m"],
    "us_ppi": ["PPI m/m"],
    "us_retail_sales": ["Retail Sales m/m"],
    "us_jobless_claims": ["Unemployment Claims"],
    "us_michigan_sentiment": ["Prelim UoM Consumer Sentiment", "Revised UoM Consumer Sentiment"],
    "us_gdp": ["Advance GDP q/q", "Prelim GDP q/q", "Final GDP q/q"],
    "jp_cpi": ["Tokyo Core CPI y/y", "National CPI ex Fresh Food y/y"],
    "boj_rate": ["BOJ Policy Rate"],
    "ecb_rate": ["Main Refinancing Rate"],
    "boe_rate": ["Official Bank Rate"],
}

# INDICATORS[key]["country"] は "US"/"JP"/"EU"/"UK"。FFの country は "USD"/"JPY"/"EUR"/"GBP"。
FF_COUNTRY_TO_REGION = {"USD": "US", "JPY": "JP", "EUR": "EU", "GBP": "UK"}

# 表示用メタ情報
INDICATORS = {
    "us_cpi": {
        "label": "米CPI(消費者物価指数・前年比)",
        "country": "US",
        "unit": "%",
        "fred_series": "CPIAUCSL",
        "fred_units": "pc1",  # FRED側で前年同月比%を計算させる
    },
    "us_nfp": {
        "label": "米雇用統計(非農業部門雇用者数・前月差)",
        "country": "US",
        "unit": "K",
        "fred_series": "PAYEMS",
        "fred_units": "chg",  # 前月差(単位: 千人)
    },
    "us_unemployment": {
        "label": "米失業率",
        "country": "US",
        "unit": "%",
        "fred_series": "UNRATE",
        "fred_units": "lin",
    },
    "us_fomc": {
        "label": "FOMC政策金利(誘導目標レンジ上限)",
        "country": "US",
        "unit": "%",
        "fred_series": "DFEDTARU",  # 日次
        "fred_units": "lin",
    },
    "us_pce": {
        "label": "米PCEコア物価指数(前月比)",
        "country": "US",
        "unit": "%",
        "fred_series": "PCEPILFE",
        "fred_units": "pch",
    },
    "us_ppi": {
        "label": "米PPI(生産者物価指数・前月比)",
        "country": "US",
        "unit": "%",
        "fred_series": "PPIFIS",
        "fred_units": "pch",
    },
    "us_retail_sales": {
        "label": "米小売売上高(前月比)",
        "country": "US",
        "unit": "%",
        "fred_series": "RSAFS",
        "fred_units": "pch",
    },
    "us_jobless_claims": {
        "label": "米新規失業保険申請件数",
        "country": "US",
        "unit": "K",
        "fred_series": "ICSA",
        "fred_units": "lin",
        "fred_value_scale": 0.001,  # FREDは実数、表示は千件単位
    },
    "us_michigan_sentiment": {
        "label": "米ミシガン大学消費者信頼感指数",
        "country": "US",
        "unit": "",
        "fred_series": "UMCSENT",
        "fred_units": "lin",
    },
    "us_gdp": {
        "label": "米GDP(前期比年率)",
        "country": "US",
        "unit": "%",
        "fred_series": "A191RL1Q225SBEA",
        "fred_units": "lin",
    },
    "jp_cpi": {
        "label": "日CPI(全国消費者物価指数)",
        "country": "JP",
        "unit": "%",
        "estat": True,
    },
    "boj_rate": {
        "label": "日銀政策金利",
        "country": "JP",
        "unit": "%",
        "boj_statement": True,
    },
    "ecb_rate": {
        "label": "ECB政策金利(中銀預金金利)",
        "country": "EU",
        "unit": "%",
        "fred_series": "ECBDFR",
        "fred_units": "lin",
    },
    "boe_rate": {
        "label": "BOE政策金利(SONIA参照)",
        "country": "UK",
        "unit": "%",
        "fred_series": "IUDSOIA",
        "fred_units": "lin",
    },
}

# 市場反応を見るティッカー(yfinance)
MARKET_TICKERS = {
    "usdjpy": "JPY=X",
    "nikkei225": "^N225",
    "sp500": "^GSPC",
    "us10y": "^TNX",
}

# e-Stat: 消費者物価指数(全国・総合)の統計表ID
# 基準年改定でIDが変わることがあるため、失敗時はREADME参照の上で更新すること。
ESTAT_CPI_STATS_DATA_ID = "0004052037"

# BOJ声明PDFのURLパターン(YY=西暦下2桁, MM, DD)
BOJ_STATEMENT_URL_TMPL = "https://www.boj.or.jp/en/mopo/mpmdeci/mpr_20{yy}/k{yy}{mm}{dd}a.pdf"

# 公開JSONは thisweek のみ存在確認済み(next/last weekは404)。
# そのため過去実績は自前でdocs/data/results.jsonに蓄積していく方式にする。
FF_CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
