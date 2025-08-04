# 損益計算システム設定

FXシステムの損益計算に関する設定（08_損益計算v2.xlsmより）

## ディレクトリ設定

| 項目名 | 説明 | パス例 |
|--------|------|--------|
| READ_DIR | 読み込みファイルディレクトリ | C:\Users\keira_dev\AppData\Roaming\MetaQuotes\Terminal\...\MQL4\Files\pkg_log\trade_log_*.csv |
| RESULT_DIR | 損益結果ディレクトリ | C:\Users\keira_dev\AppData\Roaming\MetaQuotes\Terminal\...\MQL4\Files\Profit |
| CHART_DIR | チャート表示結果ディレクトリ | C:\Users\keira_dev\AppData\Roaming\MetaQuotes\Terminal\...\MQL4\Files\Chart |
| HIST_DIR | ヒストリカル読込ディレクトリ | C:\Users\keira_dev\Desktop\保存しておきたい\USDJPY\1 |

## 取引設定

| 項目名 | 説明 | 値 |
|--------|------|-----|
| LOT_RATIO | 1Lot = ○通貨 | 100000 |
| CANCEL_ORDER | 同一時刻の打消しの注文を相殺する | OFF |

## 機能概要

このシステムは以下の機能を提供します：

1. **取引ログの読み込み**
   - MetaTrader 4のFiles/pkg_logディレクトリから取引ログを読み込む
   - ファイル名形式：trade_log_YYYYMMDDHHMI_YYYYMMDDHHMI.csv

2. **損益計算**
   - 1Lot = 100,000通貨として計算
   - 同一時刻の打消し注文の相殺機能（デフォルトOFF）

3. **結果出力**
   - 損益結果をProfitディレクトリに出力
   - チャート表示用データをChartディレクトリに出力

4. **ヒストリカルデータ参照**
   - 保存されたヒストリカルデータを参照して計算精度を向上

## 関連ファイル

- 08_損益計算.xlsm（旧バージョン）
- 損益計算検証用.xlsm
- 最大損失計算.xlsx