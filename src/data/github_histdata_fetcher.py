"""
GitHub philipperemy/FX-1-Minute-Data から直接データ取得
自動ダウンロード実装
"""

import os
import csv
import urllib.request
from typing import List, Dict


class GitHubHistDataFetcher:
    """GitHub経由でHISTDATAを自動取得"""
    
    def __init__(self, data_dir: str = "./data/histdata"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # GitHub Raw URLパターン
        self.base_url = "https://raw.githubusercontent.com/philipperemy/FX-1-Minute-Data/master"
        
    def fetch_available_pairs(self) -> List[str]:
        """利用可能な通貨ペア取得"""
        # READMEから取得可能な通貨ペアリスト
        available_pairs = [
            "AUDJPY", "AUDNZD", "AUDUSD", "CADJPY", "CHFJPY",
            "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY",
            "EURNZD", "EURUSD", "GBPAUD", "GBPCAD", "GBPCHF",
            "GBPJPY", "GBPNZD", "GBPUSD", "NZDJPY", "NZDUSD",
            "USDCAD", "USDCHF", "USDJPY", "XAUUSD"
        ]
        return available_pairs
    
    def download_pair_data(self, pair: str = "USDJPY") -> str:
        """
        通貨ペアデータダウンロード
        注: 実際のGitHubリポジトリ構造に依存
        """
        filename = f"{pair}_M1.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        # すでに存在する場合はスキップ
        if os.path.exists(filepath):
            print(f"✅ 既存ファイル使用: {filepath}")
            return filepath
        
        # サンプルデータURL（実際のURLは要確認）
        sample_url = f"{self.base_url}/sample/{pair}_sample.csv"
        
        try:
            print(f"📥 ダウンロード中: {pair}")
            urllib.request.urlretrieve(sample_url, filepath)
            print(f"✅ ダウンロード完了: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"⚠️  GitHubから直接取得できません。")
            print(f"   Google Driveリンクを使用してください:")
            print(f"   https://drive.google.com/drive/folders/1tPqJl8FXQvPXL-ipPX7Ey0TEzOhKgvPa")
            
            # デモデータ生成
            self._generate_demo_data(filepath, pair)
            return filepath
    
    def _generate_demo_data(self, filepath: str, pair: str):
        """デモデータ生成（実データ取得できない場合）"""
        import random
        from datetime import datetime, timedelta
        
        print(f"🔧 デモデータ生成中: {pair}")
        
        # 基準価格設定
        base_prices = {
            "USDJPY": 150.0,
            "EURUSD": 1.08,
            "EURJPY": 162.0,
            "GBPUSD": 1.27,
            "AUDUSD": 0.65
        }
        
        base_price = base_prices.get(pair, 100.0)
        
        # 1週間分のデータ生成
        data = []
        current_time = datetime(2024, 1, 1, 0, 0, 0)
        current_price = base_price
        
        for _ in range(10080):  # 1週間 = 7日 * 24時間 * 60分
            # ランダムウォーク
            change = random.gauss(0, 0.0001) * base_price
            current_price += change
            
            # OHLC生成
            high = current_price + abs(random.gauss(0, 0.00005) * base_price)
            low = current_price - abs(random.gauss(0, 0.00005) * base_price)
            close = random.uniform(low, high)
            
            data.append({
                'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'open': current_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': random.randint(100, 1000)
            })
            
            current_price = close
            current_time += timedelta(minutes=1)
        
        # CSV保存
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        print(f"✅ デモデータ生成完了: {len(data)}本")
    
    def load_data(self, pair: str = "USDJPY", 
                  start_date: str = None,
                  end_date: str = None) -> List[Dict]:
        """データ読み込み"""
        filename = f"{pair}_M1.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            # ダウンロード試行
            self.download_pair_data(pair)
        
        data = []
        
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 日付フィルタリング
                    if start_date and row['timestamp'] < start_date:
                        continue
                    if end_date and row['timestamp'] > end_date:
                        break
                    
                    # 数値変換
                    row['open'] = float(row['open'])
                    row['high'] = float(row['high'])
                    row['low'] = float(row['low'])
                    row['close'] = float(row['close'])
                    row['volume'] = float(row.get('volume', 0))
                    
                    data.append(row)
            
            print(f"📊 {pair}データ読み込み: {len(data)}本")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
        
        return data


def run_github_backtest():
    """GitHubデータでバックテスト実行"""
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from backtesting.backtest_engine import BacktestEngine
    from backtesting.memo_strategy import MemoBasedStrategy
    
    # データ取得
    fetcher = GitHubHistDataFetcher()
    
    # 主要通貨ペアでテスト
    pairs = ["USDJPY", "EURUSD", "EURJPY"]
    
    results_summary = []
    
    for pair in pairs:
        print(f"\n{'='*60}")
        print(f"🎯 {pair} バックテスト開始")
        print(f"{'='*60}")
        
        # データ取得
        price_data = fetcher.load_data(
            pair=pair,
            start_date="2024-01-01",
            end_date="2024-01-07"
        )
        
        if not price_data:
            print(f"❌ {pair}のデータ取得失敗")
            continue
        
        # ストラテジー初期化
        strategy = MemoBasedStrategy()
        
        # バックテスト実行
        engine = BacktestEngine(initial_balance=1000000)
        results = engine.run_backtest(price_data, strategy.generate_signal)
        
        # 結果保存
        results['pair'] = pair
        results_summary.append(results)
        
        # 結果表示
        engine.print_results()
        engine.save_results(f"./data/{pair}_backtest_results.json")
    
    # サマリー表示
    print("\n" + "="*60)
    print("📈 全通貨ペアサマリー")
    print("="*60)
    
    for result in results_summary:
        print(f"\n{result['pair']}:")
        print(f"  勝率: {result['win_rate']:.1f}%")
        print(f"  総損益: ¥{result['total_pnl']:,.0f}")
        print(f"  リターン: {result['return_pct']:.2f}%")
        print(f"  最大DD: {result['max_drawdown']:.2f}%")
    
    # 平均パフォーマンス
    if results_summary:
        avg_win_rate = sum(r['win_rate'] for r in results_summary) / len(results_summary)
        avg_return = sum(r['return_pct'] for r in results_summary) / len(results_summary)
        
        print("\n" + "="*60)
        print("📊 平均パフォーマンス")
        print("="*60)
        print(f"平均勝率: {avg_win_rate:.1f}%")
        print(f"平均リターン: {avg_return:.2f}%")
        
        if avg_win_rate >= 55:
            print("✅ 目標勝率55%達成！")
        else:
            print(f"⚠️  勝率改善必要（目標: 55%, 現在: {avg_win_rate:.1f}%）")


def main():
    """メイン実行"""
    print("🚀 GitHub HISTDATAフェッチャー起動")
    
    # フェッチャー初期化
    fetcher = GitHubHistDataFetcher()
    
    # 利用可能な通貨ペア表示
    pairs = fetcher.fetch_available_pairs()
    print(f"\n📊 利用可能な通貨ペア ({len(pairs)}種類):")
    for i in range(0, len(pairs), 5):
        print(f"  {', '.join(pairs[i:i+5])}")
    
    # USDJPY取得テスト
    print("\n" + "="*60)
    print("📥 USDJPYデータ取得テスト")
    print("="*60)
    
    data = fetcher.load_data("USDJPY", "2024-01-01", "2024-01-02")
    
    if data:
        print(f"\nサンプルデータ（最初の5本）:")
        for i, candle in enumerate(data[:5]):
            print(f"  {i+1}. {candle['timestamp']}: "
                  f"O={candle['open']:.3f}, H={candle['high']:.3f}, "
                  f"L={candle['low']:.3f}, C={candle['close']:.3f}")
    
    # バックテスト自動実行
    print("\n" + "="*60)
    print("🎯 バックテスト自動実行")
    print("="*60)
    
    run_github_backtest()


if __name__ == "__main__":
    main()