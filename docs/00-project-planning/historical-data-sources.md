# FX取引システム - ヒストリカルデータ取得方法

## 現在利用可能なデータソース

### 1. 📁 既存のローカルデータ（取得データ/フォルダ）

現在プロジェクトには以下のヒストリカルデータが存在：

```
取得データ/
├── Logic_Signal_*.csv  # シグナルデータ（2019年）
├── 各種PKG配置データ（.xlsm, .xlsx）
└── 各時間足フォルダ/
    ├── 1-6122_15/  # 15分足データ
    ├── 1-6127_15/  # 15分足データ
    └── その他/
```

**注意**: これらは過去のシステムで使用されたデータで、現在のシステムには直接使えない可能性があります。

### 2. 🌐 OANDA API（推奨）

すでに実装済みの `src/utils/oanda_client.py` を使用：

#### デモ口座での取得方法

```python
from src.utils.oanda_client import OandaClient, DataCollector

# 1. OANDAデモ口座を開設（無料）
# https://www.oanda.jp/lab-education/openaccount/demo/

# 2. API設定
client = OandaClient()  # .envファイルから設定読み込み

# 3. ヒストリカルデータ取得
collector = DataCollector(client)
collector.collect_and_save_data(
    instruments=["USD_JPY", "EUR_USD", "EUR_JPY"],
    timeframes=["M1", "M5", "M15", "M30", "H1", "H4"],
    days_back=30  # 過去30日分
)
```

#### 取得可能なデータ
- **通貨ペア**: 主要通貨ペアすべて
- **時間足**: M1, M5, M15, M30, H1, H4, D1
- **期間**: 最大5000本のキャンドル（APIの制限）
- **形式**: OHLCV（Open, High, Low, Close, Volume）

### 3. 📊 その他の無料データソース

#### a) Yahoo Finance（yfinance）
```bash
pip install yfinance
```

```python
import yfinance as yf

# USD/JPY日足データ
usdjpy = yf.download("USDJPY=X", start="2020-01-01", end="2024-01-01")
```

**制限**: 分足データは過去7日間のみ

#### b) Alpha Vantage（無料API）
```python
# APIキー取得: https://www.alphavantage.co/support/#api-key
# 制限: 1日500リクエスト、1分5リクエスト

import requests

API_KEY = "your_api_key"
url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol=USD&to_symbol=JPY&interval=1min&apikey={API_KEY}"
```

#### c) Dukascopy（ヒストリカルデータ）
- **URL**: https://www.dukascopy.com/swiss/english/marketwatch/historical/
- **特徴**: ティックデータまで取得可能
- **形式**: CSV/バイナリ

```python
# dukascopy-apiを使用
pip install dukascopy-api

from dukascopy import Dukascopy

dc = Dukascopy()
df = dc.get_dataframe(
    'USDJPY', 
    start='2023-01-01', 
    end='2024-01-01',
    timeframe='m1'
)
```

#### d) MetaTrader 5（MT5）
```python
pip install MetaTrader5

import MetaTrader5 as mt5

# MT5に接続
mt5.initialize()

# ヒストリカルデータ取得
rates = mt5.copy_rates_from_pos("USDJPY", mt5.TIMEFRAME_M1, 0, 1000)
```

**注意**: MT5のインストールと口座開設が必要

### 4. 💰 有料データソース（高品質）

#### プロフェッショナル向け
- **Refinitiv (旧Thomson Reuters)**: 機関投資家向け
- **Bloomberg Terminal**: 月額約$2,000
- **Quandl**: 月額$50～
- **HistData.com**: 無料だが品質に注意

## 推奨する取得方法

### Week 2のバックテスト用

1. **最優先**: OANDA API（デモ口座）
   - すでに実装済み
   - リアルタイムデータと同じソース
   - 無料で十分なデータ量

2. **補完用**: Dukascopy
   - より長期間のデータが必要な場合
   - ティックレベルの詳細データが必要な場合

### 実装例

```python
# data_fetcher.py
import asyncio
from datetime import datetime, timedelta

async def fetch_all_historical_data():
    """全ヒストリカルデータ取得"""
    
    # 1. OANDA APIから取得
    from src.utils.oanda_client import OandaClient, DataCollector
    
    client = OandaClient()
    collector = DataCollector(client, data_dir="./data/historical")
    
    # 各通貨ペア、各時間足でデータ取得
    instruments = ["USD_JPY", "EUR_USD", "EUR_JPY"]
    timeframes = ["M1", "M5", "M15", "M30", "H1", "H4"]
    
    for instrument in instruments:
        for timeframe in timeframes:
            print(f"Fetching {instrument} {timeframe}...")
            
            # 30日分を取得
            df = client.get_historical_data(
                instrument=instrument,
                granularity=timeframe,
                count=5000  # 最大値
            )
            
            # データベースに保存
            from src.utils.database import DatabaseManager
            db = DatabaseManager()
            db.save_price_data(instrument, timeframe, df)
            
            # レート制限対策
            await asyncio.sleep(1)
    
    print("✅ ヒストリカルデータ取得完了")

# 実行
asyncio.run(fetch_all_historical_data())
```

## データ品質チェックリスト

- [ ] 欠損値の確認
- [ ] 異常値（スパイク）の検出
- [ ] 時間の連続性確認
- [ ] スプレッドの妥当性確認
- [ ] ボリュームデータの有無

## まとめ

**Week 2のバックテスト用には、OANDA APIから過去30日分のデータを取得することを推奨します。**

すでに `OandaClient` が実装されているので、追加開発なしですぐにデータ取得可能です。

より長期間のバックテストが必要な場合は、Dukascopyなどの無料ソースを併用してください。