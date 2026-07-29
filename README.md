# 経済指標ダッシュボード

米国・日本の重要経済指標(米CPI・米雇用統計・FOMC政策金利、日CPI・日銀金融政策決定会合)について、
①今週の予想とシナリオ、②発表後の予想vs実績(改定込み)と市場反応、を毎日自動更新して表示するダッシュボード。
GitHub Actionsで1日3回データを更新し、GitHub Pagesで公開する。

## 画面

- `docs/index.html` — 今週の予想・参考シナリオ
- `docs/results.html` — 発表済みイベントの実績・改定履歴・市場反応

## データソースと制約

| 用途 | ソース | 備考 |
|---|---|---|
| 発表スケジュール・予想値・前回値 | Forex Factory 公開カレンダーJSON(`nfs.faireconomy.media/ff_calendar_thisweek.json`) | **公式APIではない。** 個人・非商用・低頻度アクセスの範囲で利用している。利用規約上はグレーゾーンであり、将来配信停止/ブロックされる可能性がある。取得失敗時は空リストで継続する設計 |
| 米指標の実績値・改定履歴 | [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html)(無料キー必須) | ALFRED機能で「発表時点の速報値」と「現在の改定値」の両方を取得 |
| 日CPI実績値 | 未実装(今後e-Statまたは代替ソースで対応予定) | 現状は「実績値未取得」の注記のみ表示 |
| 日銀会合の決定内容 | BOJ公式サイトの声明PDFをテキスト解析 | 声明文言が変わるとパースに失敗する可能性があり、その場合は「手動確認が必要」と表示してパイプライン全体は止めない |
| 市場反応 | [yfinance](https://github.com/ranaroussi/yfinance)(非公式) | 発表前営業日終値 vs 当日/翌営業日終値の単純比較(分刻みの反応は見ていない) |

過去実績はForex Factoryの`thisweek.json`(当該週のみ配信)から拾えたタイミングで
`docs/data/results.json`に蓄積していく方式。デプロイ直後は履歴が空で、稼働しながら少しずつ溜まっていく。

## セットアップ

### 1. 必要なAPIキー

- **FRED APIキー**(必須・無料): https://fred.stlouisfed.org/docs/api/api_key.html でメール登録するだけで即発行

### 2. ローカル動作確認

```bash
cd scripts
python -m venv ../.venv
../.venv/Scripts/pip install -r requirements.txt
```

プロジェクトルートに `.env` を作成し、以下を記載(gitにはコミットされない):

```
FRED_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

```bash
python scripts/build_data.py
```

`docs/data/upcoming.json` / `docs/data/results.json` が生成される。
`docs/` を `python -m http.server` 等で配信すればブラウザで確認できる。

> **Windows環境の注意**: セキュリティソフト等のTLSインスペクションにより
> `requests`/`yfinance`の証明書検証が失敗することがある。
> `scripts/net.py` が自動でWindowsの証明書ストアからCA束を生成してキャッシュするため、
> 通常は追加設定不要。

### 3. GitHubリポジトリへのデプロイ

1. GitHubに空リポジトリを作成し、このディレクトリをpush
2. リポジトリの **Settings → Secrets and variables → Actions** で `FRED_API_KEY` を登録
3. **Settings → Pages** で Source を「Deploy from a branch」、Branch を `main` / `docs` に設定
4. **Actions** タブから `Update economic dashboard data` ワークフローを手動実行(Run workflow)して初回データを生成
5. 公開URL(`https://<username>.github.io/<repo>/`)をiPhoneのSafari等で開いてホーム画面に追加すると、アプリのように使える

## 自動更新スケジュール

`.github/workflows/update.yml` が1日3回(JST 06:00 / 13:00 / 23:00)実行され、
データに変化があれば自動でコミット・push・Pages再公開される。

## 免責事項

シナリオ文はルールベースで機械的に生成した一般論であり、投資助言ではない。
Forex Factoryのデータ利用は個人利用の範囲に限定すること。
