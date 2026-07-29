"""対象指標・データソースの設定。"""

# Forex Factory カレンダーで拾うイベントを判定するキーワード(タイトルに部分一致、大小文字無視)。
# 一致したら INDICATORS のキーに正規化する。
# 国コード(USD/JPY)も合わせて照合するため、同じ単語(CPIなど)が米/日で重複しても誤爆しない。
FF_TITLE_KEYWORDS = {
    "us_cpi": ["CPI m/m", "CPI y/y"],
    "us_nfp": ["Non-Farm Employment Change", "Nonfarm Payrolls"],
    "us_unemployment": ["Unemployment Rate"],
    "us_fomc": ["Federal Funds Rate"],
    "jp_cpi": ["National CPI", "Tokyo CPI", "Tokyo Core CPI", "National Core CPI"],
    "boj_rate": ["BOJ Policy Rate"],
}

# INDICATORS[key]["country"] は "US"/"JP"。FFの country は "USD"/"JPY"。
FF_COUNTRY_TO_REGION = {"USD": "US", "JPY": "JP"}

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
