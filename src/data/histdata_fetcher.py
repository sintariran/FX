"""
HISTDATA.com からの無料ヒストリカルデータ取得
FXDDクオリティの高品質データ（2000年〜現在）
"""

import os
import csv
import zipfile
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional


class HistDataFetcher:
    """HISTDATA.comから高品質データ取得"""
    
    def __init__(self, data_dir: str = "./data/histdata"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.base_url = "http://www.histdata.com/download-free-forex-historical-data/"
        
    def download_tick_data(self, symbol: str = "USDJPY", 
                          year: int = 2023, 
                          month: int = 1) -> str:
        """
        ティックデータダウンロード（最高品質）
        
        注意: HTTPSではなくHTTP
        手動ダウンロードが必要な場合があります
        """
        # ダウンロードURL構築
        month_str = f"{month:02d}"
        filename = f"{symbol}_ASCII_{year}{month_str}.zip"
        
        # ダウンロード先
        zip_path = os.path.join(self.data_dir, filename)
        
        print(f"📥 ダウンロード手順:")
        print(f"1. ブラウザで以下にアクセス:")
        print(f"   http://www.histdata.com/download-free-forex-data/?/ascii/tick-data-quotes/{symbol.lower()}/{year}/{month}")
        print(f"2. ZIPファイルをダウンロード")
        print(f"3. {self.data_dir} に配置")
        
        return zip_path
    
    def parse_tick_data(self, zip_path: str) -> List[Dict]:
        """
        ティックデータ解析
        フォーマット: DateTime,Bid,Ask,Volume
        """
        if not os.path.exists(zip_path):
            print(f"❌ ファイルが見つかりません: {zip_path}")
            return []
        
        data = []
        
        try:
            # ZIP解凍
            with zipfile.ZipFile(zip_path, 'r') as z:
                # CSVファイル特定
                csv_files = [f for f in z.namelist() if f.endswith('.csv')]
                
                if not csv_files:
                    print("❌ CSVファイルが見つかりません")
                    return []
                
                # CSV読み込み
                with z.open(csv_files[0]) as f:
                    reader = csv.reader(f.read().decode('utf-8').splitlines())
                    
                    for row in reader:
                        if len(row) >= 3:
                            # フォーマット: 20230101 000000,150.123,150.125
                            timestamp_str = row[0]
                            bid = float(row[1])
                            ask = float(row[2])
                            
                            # タイムスタンプ変換
                            dt = datetime.strptime(timestamp_str, "%Y%m%d %H%M%S")
                            
                            data.append({
                                'timestamp': dt.isoformat(),
                                'bid': bid,
                                'ask': ask,
                                'spread': ask - bid
                            })
            
            print(f"✅ {len(data)}ティック読み込み完了")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
        
        return data
    
    def aggregate_to_ohlc(self, tick_data: List[Dict], 
                         timeframe_minutes: int = 1) -> List[Dict]:
        """
        ティックデータをOHLCに集約
        """
        if not tick_data:
            return []
        
        ohlc_data = []
        current_candle = None
        
        for tick in tick_data:
            timestamp = datetime.fromisoformat(tick['timestamp'])
            minute_floor = timestamp.replace(second=0, microsecond=0)
            
            mid_price = (tick['bid'] + tick['ask']) / 2
            
            if current_candle is None or current_candle['timestamp'] != minute_floor:
                # 新しいキャンドル
                if current_candle:
                    ohlc_data.append(current_candle)
                
                current_candle = {
                    'timestamp': minute_floor.isoformat(),
                    'open': mid_price,
                    'high': mid_price,
                    'low': mid_price,
                    'close': mid_price,
                    'volume': 1,
                    'tick_count': 1
                }
            else:
                # 既存キャンドル更新
                current_candle['high'] = max(current_candle['high'], mid_price)
                current_candle['low'] = min(current_candle['low'], mid_price)
                current_candle['close'] = mid_price
                current_candle['tick_count'] += 1
        
        # 最後のキャンドル追加
        if current_candle:
            ohlc_data.append(current_candle)
        
        print(f"✅ {len(ohlc_data)}本のOHLCキャンドル生成")
        return ohlc_data
    
    def save_ohlc(self, ohlc_data: List[Dict], filename: str):
        """OHLC保存"""
        filepath = os.path.join(self.data_dir, filename)
        
        if not ohlc_data:
            print("❌ データが空です")
            return
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=ohlc_data[0].keys())
            writer.writeheader()
            writer.writerows(ohlc_data)
        
        print(f"💾 保存完了: {filepath}")


def fetch_github_histdata():
    """
    GitHub経由でHISTDATAを取得（philipperemy/FX-1-Minute-Data）
    1分足データ（2000-2024）
    """
    print("=" * 60)
    print("📊 GitHub HISTDATA取得")
    print("=" * 60)
    print("\n手動ダウンロード手順:")
    print("1. 以下のURLにアクセス:")
    print("   https://github.com/philipperemy/FX-1-Minute-Data")
    print("\n2. READMEにあるGoogle Driveリンクから:")
    print("   - USDJPY_M1.csv")
    print("   - EURJPY_M1.csv")
    print("   - EURUSD_M1.csv")
    print("   をダウンロード")
    print("\n3. ./data/histdata/ に配置")
    print("\n4. データフォーマット:")
    print("   Timestamp,Open,High,Low,Close,Volume")
    print("\n5. 期間: 2000年〜2024年")
    print("   サイズ: 約3GB（全通貨ペア）")
    print("=" * 60)


def main():
    """メイン実行"""
    fetcher = HistDataFetcher()
    
    # オプション1: HISTDATA.com公式
    print("\n📌 オプション1: HISTDATA.com公式サイト")
    print("高品質ティックデータ（無料）")
    zip_path = fetcher.download_tick_data("USDJPY", 2023, 1)
    
    # もしダウンロード済みなら解析
    if os.path.exists(zip_path):
        tick_data = fetcher.parse_tick_data(zip_path)
        if tick_data:
            ohlc_data = fetcher.aggregate_to_ohlc(tick_data)
            fetcher.save_ohlc(ohlc_data, "USDJPY_M1_histdata.csv")
    
    # オプション2: GitHub経由
    print("\n📌 オプション2: GitHub経由（推奨）")
    fetch_github_histdata()
    
    # オプション3: Dukascopy（プログラマティック）
    print("\n📌 オプション3: Dukascopy API（自動化可能）")
    print("pip install dukascopy-api")
    print("詳細は historical_data_fetcher.py 参照")


if __name__ == "__main__":
    main()