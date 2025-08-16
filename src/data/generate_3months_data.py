"""
3ヶ月分のヒストリカルデータ生成
実際の市場データに近い特性を持つ合成データ
"""

import csv
import random
import math
from datetime import datetime, timedelta
import os


class ThreeMonthsDataGenerator:
    """3ヶ月分のリアリスティックなFXデータ生成"""
    
    def __init__(self, data_dir: str = "./data/histdata"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # 市場セッション時間（日本時間）
        self.tokyo_open = 9
        self.tokyo_close = 15
        self.london_open = 16
        self.london_close = 1  # 翌日1時
        self.ny_open = 22
        self.ny_close = 6  # 翌日6時
        
    def generate_3months_data(self, 
                             pair: str = "USDJPY",
                             start_date: str = "2023-10-01",
                             end_date: str = "2024-01-01") -> str:
        """3ヶ月分の1分足データ生成"""
        
        print(f"🔄 {pair} 3ヶ月分データ生成中...")
        
        # 基準価格とボラティリティ設定
        base_configs = {
            "USDJPY": {
                "base_price": 149.50,
                "volatility": 0.0008,  # 0.08%
                "trend": 0.5,  # 上昇トレンド
                "spread": 0.003  # 0.3pips
            },
            "EURJPY": {
                "base_price": 161.00,
                "volatility": 0.0010,
                "trend": -0.3,
                "spread": 0.005
            },
            "EURUSD": {
                "base_price": 1.0650,
                "volatility": 0.0007,
                "trend": 0.2,
                "spread": 0.00003
            },
            "GBPJPY": {
                "base_price": 185.00,
                "volatility": 0.0012,
                "trend": 0.8,
                "spread": 0.008
            }
        }
        
        config = base_configs.get(pair, base_configs["USDJPY"])
        
        # データ生成
        data = []
        current_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        current_price = config["base_price"]
        
        # ランダムシード（再現性のため）
        random.seed(42 + hash(pair))
        
        minute_count = 0
        
        while current_dt < end_dt:
            # 週末スキップ（土曜6時〜月曜6時）
            if current_dt.weekday() == 5 and current_dt.hour >= 6:  # 土曜午前6時以降
                current_dt = current_dt + timedelta(days=2)
                current_dt = current_dt.replace(hour=6, minute=0, second=0)
                continue
            elif current_dt.weekday() == 6:  # 日曜
                current_dt = current_dt + timedelta(days=1)
                current_dt = current_dt.replace(hour=6, minute=0, second=0)
                continue
            
            # 市場セッションによるボラティリティ調整
            hour = current_dt.hour
            session_multiplier = self._get_session_volatility(hour)
            
            # 価格変動計算
            # トレンド成分
            trend_component = config["trend"] / (250 * 24 * 60)  # 年間トレンドを分単位に
            
            # ランダム成分
            random_component = random.gauss(0, config["volatility"] * session_multiplier)
            
            # 日中パターン（アジア時間は比較的静か）
            intraday_pattern = math.sin((hour - 6) * math.pi / 12) * 0.0001
            
            # 価格更新
            current_price = current_price * (1 + trend_component + random_component + intraday_pattern)
            
            # OHLC生成（1分足）
            high = current_price * (1 + abs(random.gauss(0, config["volatility"] * 0.3)))
            low = current_price * (1 - abs(random.gauss(0, config["volatility"] * 0.3)))
            close = random.uniform(low, high)
            
            # ボリューム（市場セッションに応じて）
            base_volume = 1000 * session_multiplier
            volume = int(base_volume * (1 + random.random()))
            
            data.append({
                'timestamp': current_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'open': current_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
            
            # 次の価格の開始値
            current_price = close
            
            # 時間を進める
            current_dt += timedelta(minutes=1)
            minute_count += 1
            
            # 進捗表示
            if minute_count % 10000 == 0:
                print(f"  {minute_count:,}分足生成済み...")
        
        # CSV保存
        filename = f"{pair}_M1_3months.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        print(f"✅ {pair} データ生成完了: {len(data):,}本")
        print(f"💾 保存先: {filepath}")
        
        return filepath
    
    def _get_session_volatility(self, hour: int) -> float:
        """市場セッションに基づくボラティリティ係数"""
        # 東京時間（9-15時）
        if 9 <= hour <= 15:
            return 1.0
        # ロンドン時間（16-25時）
        elif 16 <= hour <= 23:
            return 1.5
        elif 0 <= hour <= 1:
            return 1.5
        # NY時間（22-6時）
        elif 22 <= hour <= 23:
            return 2.0  # ロンドン・NYオーバーラップ
        elif 0 <= hour <= 6:
            return 1.3
        # その他（早朝など）
        else:
            return 0.5
    
    def generate_all_pairs(self):
        """主要通貨ペアすべて生成"""
        pairs = ["USDJPY", "EURJPY", "EURUSD", "GBPJPY"]
        
        print("=" * 60)
        print("📊 3ヶ月分ヒストリカルデータ生成")
        print("=" * 60)
        print(f"期間: 2023-10-01 〜 2024-01-01")
        print(f"通貨ペア: {', '.join(pairs)}")
        print("=" * 60)
        
        generated_files = []
        
        for pair in pairs:
            filepath = self.generate_3months_data(
                pair=pair,
                start_date="2023-10-01",
                end_date="2024-01-01"
            )
            generated_files.append(filepath)
        
        print("\n" + "=" * 60)
        print("✅ 全データ生成完了")
        print("=" * 60)
        
        for filepath in generated_files:
            # ファイルサイズ確認
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  {os.path.basename(filepath)}: {size_mb:.1f} MB")
        
        return generated_files


def convert_to_15min_optimized(m1_filepath: str) -> str:
    """1分足から15分足への効率的な変換"""
    
    print(f"📊 15分足変換中: {os.path.basename(m1_filepath)}")
    
    m15_data = []
    current_candle = None
    candle_minutes = []
    
    with open(m1_filepath, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # 数値変換
            row['open'] = float(row['open'])
            row['high'] = float(row['high'])
            row['low'] = float(row['low'])
            row['close'] = float(row['close'])
            row['volume'] = float(row['volume'])
            
            # 時刻確認
            dt = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            
            # 15分の境界確認
            if dt.minute % 15 == 0:
                # 前のキャンドルを保存
                if current_candle and len(candle_minutes) > 0:
                    # 集計
                    current_candle['high'] = max(m['high'] for m in candle_minutes)
                    current_candle['low'] = min(m['low'] for m in candle_minutes)
                    current_candle['close'] = candle_minutes[-1]['close']
                    current_candle['volume'] = sum(m['volume'] for m in candle_minutes)
                    m15_data.append(current_candle)
                
                # 新しいキャンドル開始
                current_candle = {
                    'timestamp': row['timestamp'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                }
                candle_minutes = [row]
            else:
                # 既存キャンドルに追加
                candle_minutes.append(row)
    
    # 最後のキャンドル
    if current_candle and candle_minutes:
        current_candle['high'] = max(m['high'] for m in candle_minutes)
        current_candle['low'] = min(m['low'] for m in candle_minutes)
        current_candle['close'] = candle_minutes[-1]['close']
        current_candle['volume'] = sum(m['volume'] for m in candle_minutes)
        m15_data.append(current_candle)
    
    # 15分足データ保存
    m15_filepath = m1_filepath.replace('_M1_', '_M15_')
    
    with open(m15_filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=m15_data[0].keys())
        writer.writeheader()
        writer.writerows(m15_data)
    
    print(f"✅ 15分足変換完了: {len(m15_data):,}本")
    
    return m15_filepath


def main():
    """メイン実行"""
    generator = ThreeMonthsDataGenerator()
    
    # 3ヶ月分のデータ生成
    m1_files = generator.generate_all_pairs()
    
    # 15分足に変換
    print("\n" + "=" * 60)
    print("📊 15分足データ変換")
    print("=" * 60)
    
    m15_files = []
    for m1_file in m1_files:
        m15_file = convert_to_15min_optimized(m1_file)
        m15_files.append(m15_file)
    
    print("\n" + "=" * 60)
    print("✅ 準備完了")
    print("=" * 60)
    print("生成データ:")
    print("  - 期間: 3ヶ月（2023年10月〜2024年1月）")
    print("  - 1分足: 約130,000本/通貨ペア")
    print("  - 15分足: 約8,600本/通貨ペア")
    print("\n次のステップ:")
    print("  python3 src/backtesting/run_3months_backtest.py")


if __name__ == "__main__":
    main()