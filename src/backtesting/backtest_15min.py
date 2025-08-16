"""
15分足ベースのバックテスト実装
メモファイルに基づく正しい時間足での検証
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List
import csv
from datetime import datetime
from backtesting.backtest_engine import BacktestEngine
from backtesting.memo_strategy import MemoBasedStrategy


def convert_to_15min(m1_data: List[Dict]) -> List[Dict]:
    """1分足データを15分足に変換"""
    if not m1_data:
        return []
    
    m15_data = []
    current_candle = None
    candle_count = 0
    
    for minute in m1_data:
        # タイムスタンプから15分区切りを計算
        dt = datetime.fromisoformat(minute['timestamp'].replace(' ', 'T'))
        minute_of_hour = dt.minute
        
        # 15分の開始（0, 15, 30, 45）
        is_new_candle = minute_of_hour % 15 == 0
        
        if is_new_candle or current_candle is None:
            # 前のキャンドルを保存
            if current_candle and candle_count == 15:
                m15_data.append(current_candle)
            
            # 新しいキャンドル開始
            current_candle = {
                'timestamp': minute['timestamp'],
                'open': minute['open'],
                'high': minute['high'],
                'low': minute['low'],
                'close': minute['close'],
                'volume': minute['volume']
            }
            candle_count = 1
        else:
            # 既存キャンドルを更新
            if current_candle:
                current_candle['high'] = max(current_candle['high'], minute['high'])
                current_candle['low'] = min(current_candle['low'], minute['low'])
                current_candle['close'] = minute['close']
                current_candle['volume'] += minute['volume']
                candle_count += 1
    
    # 最後のキャンドル
    if current_candle and candle_count > 0:
        m15_data.append(current_candle)
    
    return m15_data


def run_15min_backtest():
    """15分足でのバックテスト実行"""
    
    print("=" * 70)
    print("🎯 15分足ベースバックテスト（メモファイル準拠）")
    print("=" * 70)
    
    # 1分足データ読み込み
    data_dir = "./data/histdata"
    pairs = ["USDJPY", "EURJPY", "EURUSD"]
    
    all_results = []
    
    for pair in pairs:
        print(f"\n{'='*60}")
        print(f"📊 {pair} 15分足バックテスト")
        print(f"{'='*60}")
        
        # 1分足データ読み込み
        m1_file = f"{data_dir}/{pair}_M1.csv"
        
        if not os.path.exists(m1_file):
            print(f"❌ データファイルが見つかりません: {m1_file}")
            continue
        
        # CSV読み込み
        with open(m1_file, 'r') as f:
            reader = csv.DictReader(f)
            m1_data = []
            for row in reader:
                row['open'] = float(row['open'])
                row['high'] = float(row['high'])
                row['low'] = float(row['low'])
                row['close'] = float(row['close'])
                row['volume'] = float(row.get('volume', 0))
                m1_data.append(row)
        
        print(f"📂 1分足データ: {len(m1_data)}本")
        
        # 15分足に変換
        m15_data = convert_to_15min(m1_data)
        print(f"📊 15分足データ: {len(m15_data)}本")
        
        # より長期間のテスト（30日分以上を推奨）
        # 現在は7日間のデータなので約672本（7日×24時間×4本/時間）
        
        # ストラテジー初期化
        strategy = MemoBasedStrategy15Min()
        
        # バックテスト実行
        engine = BacktestEngine(initial_balance=1000000)
        results = engine.run_backtest(m15_data, strategy.generate_signal)
        
        # 結果保存
        results['pair'] = pair
        results['timeframe'] = 'M15'
        results['period_days'] = len(m15_data) / (4 * 24)  # 15分足の本数から日数計算
        all_results.append(results)
        
        # 結果表示
        engine.print_results()
        
        # 詳細保存
        engine.save_results(f"./data/{pair}_M15_backtest_results.json")
    
    # サマリー表示
    print("\n" + "=" * 70)
    print("📈 15分足バックテストサマリー")
    print("=" * 70)
    
    for result in all_results:
        print(f"\n{result['pair']}:")
        print(f"  時間足: {result['timeframe']}")
        print(f"  期間: {result['period_days']:.1f}日")
        print(f"  勝率: {result['win_rate']:.1f}%")
        print(f"  総損益: ¥{result['total_pnl']:,.0f}")
        print(f"  リターン: {result['return_pct']:.2f}%")
        print(f"  最大DD: {result['max_drawdown']:.2f}%")
        print(f"  取引回数: {result['total_trades']}回")
        
        # 1日あたりの取引回数
        if result['period_days'] > 0:
            trades_per_day = result['total_trades'] / result['period_days']
            print(f"  1日あたり: {trades_per_day:.1f}回")
    
    # 目標達成チェック
    if all_results:
        avg_win_rate = sum(r['win_rate'] for r in all_results) / len(all_results)
        print("\n" + "=" * 70)
        print("🎯 目標達成状況")
        print("=" * 70)
        print(f"平均勝率: {avg_win_rate:.1f}%")
        
        if avg_win_rate >= 55:
            print("✅ 目標勝率55%達成！")
        else:
            print(f"⚠️  勝率改善必要（目標: 55%, 現在: {avg_win_rate:.1f}%）")
            print("\n改善ポイント:")
            print("  1. メモファイルの15分足ロジック精査")
            print("  2. 同逆判定の閾値調整")
            print("  3. エントリー条件の厳格化")
            print("  4. 利確・損切り幅の最適化")


class MemoBasedStrategy15Min(MemoBasedStrategy):
    """15分足用に調整したメモベースストラテジー"""
    
    def __init__(self):
        super().__init__()
        # 15分足用のパラメータ
        self.momi_threshold = 0.10  # 10pips（15分足用に拡大）
        self.profit_target = 0.30   # 30pips
        self.stop_loss = 0.15       # 15pips
    
    def _check_momi(self) -> int:
        """もみ判定（15分足用）"""
        if len(self.prev_candles) < 2:
            return 0
        
        # 15分足では3本分（45分）のレンジを見る
        high = max(c['high'] for c in self.prev_candles[-3:] if c)
        low = min(c['low'] for c in self.prev_candles[-3:] if c)
        range_width = high - low
        
        # 15分足では10pips未満をもみとする
        if range_width < self.momi_threshold:
            return 3  # 待機
        return 0
    
    def _check_dokyaku(self) -> int:
        """同逆判定（15分足用）"""
        if len(self.prev_candles) < 3:
            return 0
        
        # 15分足では前3本を評価
        prev3 = self.prev_candles[-4] if len(self.prev_candles) > 3 else self.prev_candles[0]
        prev2 = self.prev_candles[-3]
        prev1 = self.prev_candles[-2]
        current = self.prev_candles[-1]
        
        # 平均足方向の判定
        ha_prev = (prev1['open'] + prev1['high'] + prev1['low'] + prev1['close']) / 4
        ha_current = (current['open'] + current['high'] + current['low'] + current['close']) / 4
        
        # 15分足では0.05%の変化を基準
        if ha_current > ha_prev * 1.0005:
            return 1  # 買い
        elif ha_current < ha_prev * 0.9995:
            return 2  # 売り
        return 0
    
    def _check_exit_condition(self) -> bool:
        """利益確定条件（15分足用）"""
        if len(self.prev_candles) < 2 or self.entry_price is None:
            return False
        
        current = self.prev_candles[-1]
        entry_price = self.entry_price
        
        if self.position_direction == 1:  # 買いポジション
            # 利確: 30pips
            if current['close'] >= entry_price + self.profit_target:
                return True
            # 損切り: 15pips
            if current['close'] <= entry_price - self.stop_loss:
                return True
        elif self.position_direction == 2:  # 売りポジション
            if current['close'] <= entry_price - self.profit_target:
                return True
            if current['close'] >= entry_price + self.stop_loss:
                return True
        
        return False


if __name__ == "__main__":
    run_15min_backtest()