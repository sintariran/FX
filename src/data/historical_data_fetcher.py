"""
ヒストリカルデータ取得ツール
OANDAが使えない場合の代替方法
"""

from datetime import datetime, timedelta
import time
import os
from typing import Dict, List, Optional
import csv
import json
import random


class AlternativeDataFetcher:
    """代替データ取得クラス"""
    
    def __init__(self, data_dir: str = "./data/historical"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def fetch_from_dukascopy(self, symbol: str = "USDJPY", 
                           start_date: str = "2024-01-01",
                           end_date: str = "2024-02-01",
                           timeframe: str = "M1") -> List[Dict]:
        """
        Dukascopyから無料でヒストリカルデータ取得
        
        pip install dukascopy-api
        """
        try:
            from dukascopy import Dukascopy
            
            dc = Dukascopy()
            df = dc.get_dataframe(
                symbol, 
                start=start_date, 
                end=end_date,
                timeframe=timeframe.lower()
            )
            
            print(f"✅ Dukascopyから{symbol} {timeframe}データ取得: {len(df)}行")
            return df.to_dict('records')
            
        except ImportError:
            print("❌ dukascopy-apiがインストールされていません")
            print("   pip install dukascopy-api")
            return []
    
    def fetch_from_yfinance(self, symbol: str = "USDJPY=X",
                          period: str = "1mo") -> List[Dict]:
        """
        Yahoo Financeから取得（日足のみ推奨）
        
        pip install yfinance
        """
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            
            # カラム名を統一
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high', 
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            print(f"✅ Yahoo Financeから{symbol}データ取得: {len(df)}行")
            return df[['open', 'high', 'low', 'close', 'volume']].to_dict('records')
            
        except ImportError:
            print("❌ yfinanceがインストールされていません")
            print("   pip install yfinance")
            return []
    
    def fetch_from_alpha_vantage(self, from_symbol: str = "USD",
                                to_symbol: str = "JPY",
                                interval: str = "1min",
                                api_key: str = None) -> List[Dict]:
        """
        Alpha Vantageから取得（無料、制限あり）
        
        APIキー取得: https://www.alphavantage.co/support/#api-key
        """
        if not api_key:
            print("❌ Alpha Vantage APIキーが必要です")
            print("   取得先: https://www.alphavantage.co/support/#api-key")
            return []
        
        try:
            import urllib.request
            import urllib.parse
            
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "FX_INTRADAY",
                "from_symbol": from_symbol,
                "to_symbol": to_symbol,
                "interval": interval,
                "apikey": api_key
            }
            
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
            
            with urllib.request.urlopen(full_url) as response:
                data = json.loads(response.read())
            
            if "Error Message" in data:
                print(f"❌ エラー: {data['Error Message']}")
                return []
            
            # データ整形
            time_series_key = f"Time Series FX ({interval})"
            if time_series_key in data:
                result = []
                for timestamp, values in data[time_series_key].items():
                    result.append({
                        'timestamp': timestamp,
                        'open': float(values.get('1. open', 0)),
                        'high': float(values.get('2. high', 0)),
                        'low': float(values.get('3. low', 0)),
                        'close': float(values.get('4. close', 0))
                    })
                
                result.sort(key=lambda x: x['timestamp'])
                print(f"✅ Alpha Vantageから{from_symbol}/{to_symbol}データ取得: {len(result)}行")
                return result
            
        except Exception as e:
            print(f"❌ Alpha Vantageエラー: {e}")
        
        return []
    
    def generate_synthetic_data(self, 
                               start_date: str = "2024-01-01",
                               end_date: str = "2024-02-01",
                               timeframe: str = "M1",
                               base_price: float = 150.0) -> List[Dict]:
        """
        テスト用の合成データ生成
        実際の価格変動をシミュレート
        """
        # 時間足に応じた分数
        freq_map = {
            "M1": 1,
            "M5": 5,
            "M15": 15,
            "M30": 30,
            "H1": 60,
            "H4": 240,
            "D1": 1440
        }
        
        minutes = freq_map.get(timeframe, 1)
        
        # 日付範囲生成
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        dates = []
        current = start_dt
        while current <= end_dt:
            dates.append(current)
            current += timedelta(minutes=minutes)
        
        # ランダムウォークでリアルな価格変動をシミュレート
        random.seed(42)
        n = len(dates)
        
        # トレンド成分
        trend_step = random.gauss(0, 0.02) / n
        
        # 価格生成
        result = []
        current_price = base_price
        
        for i, date in enumerate(dates):
            # ランダム成分（ボラティリティ）
            volatility = 0.001  # 0.1%のボラティリティ
            random_change = random.gauss(0, volatility)
            
            # 周期成分（日中パターン）
            hour = date.hour
            import math
            daily_pattern = math.sin(hour * math.pi / 12) * 0.002
            
            # 価格計算
            current_price += trend_step + random_change + daily_pattern
            
            # OHLC生成
            daily_range = abs(random.gauss(0, 0.001 * base_price))
            
            high = current_price + daily_range * random.random()
            low = current_price - daily_range * random.random()
            open_price = result[-1]['close'] if result else base_price
            
            result.append({
                'timestamp': date.isoformat(),
                'open': open_price,
                'high': high,
                'low': low,
                'close': current_price,
                'volume': random.randint(1000, 10000)
            })
        
        print(f"✅ 合成データ生成: {len(result)}行 ({timeframe})")
        return result
    
    def save_to_csv(self, data: List[Dict], filename: str):
        """CSVファイルに保存"""
        if not data:
            print(f"❌ データが空です: {filename}")
            return
            
        filepath = os.path.join(self.data_dir, filename)
        
        # CSVに書き込み
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        print(f"💾 保存完了: {filepath}")
    
    def load_from_csv(self, filename: str) -> List[Dict]:
        """CSVファイルから読み込み"""
        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            print(f"📂 読み込み完了: {filepath} ({len(data)}行)")
            return data
        else:
            print(f"❌ ファイルが存在しません: {filepath}")
            return []


def main():
    """メイン実行"""
    fetcher = AlternativeDataFetcher()
    
    print("=" * 60)
    print("🔍 利用可能なデータソースをチェック中...")
    print("=" * 60)
    
    # 1. Dukascopyを試す
    print("\n1. Dukascopy（推奨）:")
    data_duka = fetcher.fetch_from_dukascopy(
        symbol="USDJPY",
        start_date="2024-01-01",
        end_date="2024-01-07",
        timeframe="M1"
    )
    
    if data_duka:
        fetcher.save_to_csv(data_duka, "USDJPY_M1_dukascopy.csv")
    
    # 2. Yahoo Financeを試す
    print("\n2. Yahoo Finance（日足のみ）:")
    data_yf = fetcher.fetch_from_yfinance("USDJPY=X", period="1mo")
    
    if data_yf:
        fetcher.save_to_csv(data_yf, "USDJPY_D1_yahoo.csv")
    
    # 3. 合成データ生成（テスト用）
    print("\n3. 合成データ（テスト用）:")
    for timeframe in ["M1", "M5", "M15", "M30"]:
        data_synthetic = fetcher.generate_synthetic_data(
            start_date="2024-01-01",
            end_date="2024-01-02",  # テスト用に短期間
            timeframe=timeframe,
            base_price=150.0
        )
        fetcher.save_to_csv(data_synthetic, f"USDJPY_{timeframe}_synthetic.csv")
    
    print("\n" + "=" * 60)
    print("✅ データ取得完了！")
    print("   保存先: ./data/historical/")
    print("\n推奨事項:")
    print("1. まずは合成データでシステムテスト")
    print("2. Dukascopyから実データ取得")
    print("3. バックテスト実施")


if __name__ == "__main__":
    main()