"""
3ヶ月分データでの15分足バックテスト
本格的な検証実施
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
from datetime import datetime
from backtesting.backtest_engine import BacktestEngine
from backtesting.backtest_15min import MemoBasedStrategy15Min


def run_3months_backtest():
    """3ヶ月分のバックテスト実行"""
    
    print("=" * 70)
    print("🎯 3ヶ月バックテスト（15分足）")
    print("=" * 70)
    print("期間: 2023年10月1日 〜 2024年1月1日（92日間）")
    print("=" * 70)
    
    # テスト対象通貨ペア
    pairs = ["USDJPY", "EURJPY", "EURUSD", "GBPJPY"]
    
    all_results = []
    
    for pair in pairs:
        print(f"\n{'='*60}")
        print(f"📊 {pair} バックテスト開始")
        print(f"{'='*60}")
        
        # 15分足データ読み込み
        m15_file = f"./data/histdata/{pair}_M15_3months.csv"
        
        if not os.path.exists(m15_file):
            print(f"❌ ファイルが見つかりません: {m15_file}")
            continue
        
        # データ読み込み
        m15_data = []
        with open(m15_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['open'] = float(row['open'])
                row['high'] = float(row['high'])
                row['low'] = float(row['low'])
                row['close'] = float(row['close'])
                row['volume'] = float(row['volume'])
                m15_data.append(row)
        
        print(f"📂 データ読み込み完了: {len(m15_data):,}本")
        
        # 期間確認
        start_date = m15_data[0]['timestamp']
        end_date = m15_data[-1]['timestamp']
        print(f"📅 期間: {start_date} 〜 {end_date}")
        
        # ストラテジー初期化（改良版）
        strategy = ImprovedMemoStrategy15Min()
        
        # バックテスト実行
        engine = BacktestEngine(initial_balance=1000000)
        results = engine.run_backtest(m15_data, strategy.generate_signal)
        
        # 結果保存
        results['pair'] = pair
        results['timeframe'] = 'M15'
        results['total_candles'] = len(m15_data)
        results['period_days'] = 92  # 3ヶ月
        all_results.append(results)
        
        # 結果表示
        engine.print_results()
        
        # 詳細統計
        if results['total_trades'] > 0:
            avg_trades_per_day = results['total_trades'] / 92
            win_loss_ratio = results['winning_trades'] / results['losing_trades'] if results['losing_trades'] > 0 else 0
            
            print(f"\n📊 詳細統計:")
            print(f"  1日平均取引数: {avg_trades_per_day:.1f}回")
            print(f"  勝敗比: {win_loss_ratio:.2f}")
            print(f"  期待値: ¥{results['total_pnl'] / results['total_trades']:.0f}/取引")
        
        # JSON保存
        engine.save_results(f"./data/{pair}_M15_3months_results.json")
    
    # 全体サマリー
    print("\n" + "=" * 70)
    print("📈 3ヶ月バックテスト総合結果")
    print("=" * 70)
    
    total_pnl = 0
    total_trades = 0
    total_wins = 0
    
    for result in all_results:
        print(f"\n【{result['pair']}】")
        print(f"  勝率: {result['win_rate']:.1f}%")
        print(f"  総損益: ¥{result['total_pnl']:,.0f}")
        print(f"  リターン: {result['return_pct']:.2f}%")
        print(f"  最大DD: {result['max_drawdown']:.2f}%")
        print(f"  取引数: {result['total_trades']}回")
        
        total_pnl += result['total_pnl']
        total_trades += result['total_trades']
        total_wins += result['winning_trades']
    
    # 総合評価
    print("\n" + "=" * 70)
    print("🎯 総合評価")
    print("=" * 70)
    
    if all_results:
        avg_win_rate = sum(r['win_rate'] for r in all_results) / len(all_results)
        avg_return = sum(r['return_pct'] for r in all_results) / len(all_results)
        overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        print(f"平均勝率: {avg_win_rate:.1f}%")
        print(f"総合勝率: {overall_win_rate:.1f}%")
        print(f"平均リターン: {avg_return:.2f}%")
        print(f"総合損益: ¥{total_pnl:,.0f}")
        print(f"総取引数: {total_trades}回")
        
        # 目標達成判定
        print("\n" + "=" * 70)
        if avg_win_rate >= 55:
            print("✅ 目標勝率55%達成！")
        else:
            print(f"⚠️  勝率改善必要（目標: 55%, 現在: {avg_win_rate:.1f}%）")
            
            print("\n📝 改善提案:")
            print("1. エントリー条件の厳格化")
            print("   - もみ判定の精度向上")
            print("   - 複数時間足での確認")
            print("2. リスク管理の強化")
            print("   - 動的な損切り幅設定")
            print("   - ポジションサイジング")
            print("3. 市場セッション考慮")
            print("   - 東京、ロンドン、NY時間の特性活用")


class ImprovedMemoStrategy15Min(MemoBasedStrategy15Min):
    """改良版15分足ストラテジー"""
    
    def __init__(self):
        super().__init__()
        # 改良パラメータ（現実的に調整）
        self.momi_threshold = 0.0015   # 0.15% (約15pips for USDJPY@150)
        self.profit_target = 0.0025    # 0.25% (約25pips)
        self.stop_loss = 0.0010        # 0.10% (約10pips)
        self.entry_count = 0
        self.consecutive_losses = 0
        
    def generate_signal(self, candle, index, all_candles):
        """改良版シグナル生成"""
        # 最低限のデータが必要
        if index < 10:  # より多くの履歴を要求
            return 3
        
        # 直近のキャンドルを保存
        self.prev_candles = all_candles[max(0, index-10):index+1]
        
        # 連敗中は慎重に
        if self.consecutive_losses >= 3:
            return 3  # 待機
        
        # 1. トレンド確認（追加）
        trend = self._check_trend()
        if trend == 0:
            return 3  # トレンドなしは待機
        
        # 2. もみ判定
        momi_signal = self._check_momi()
        if momi_signal == 3:
            return 3
        
        # 3. 同逆判定
        dokyaku_signal = self._check_dokyaku()
        
        # 4. トレンドと同逆が一致する場合のみエントリー
        if trend == dokyaku_signal and dokyaku_signal != 0:
            # ポジション管理
            if self.position_direction == 0:
                self.position_direction = dokyaku_signal
                self.entry_price = candle['close']
                self.entry_count += 1
                return dokyaku_signal
        
        # 5. 利益確定・損切り
        if self.position_direction != 0 and self.entry_price:
            current_price = candle['close']
            price_change = (current_price - self.entry_price) / self.entry_price
            
            # 方向に応じた損益計算
            if self.position_direction == 1:  # 買い
                if price_change >= self.profit_target or price_change <= -self.stop_loss:
                    self.consecutive_losses = 0 if price_change > 0 else self.consecutive_losses + 1
                    self.position_direction = 0
                    self.entry_price = None
                    return 0
            elif self.position_direction == 2:  # 売り
                if -price_change >= self.profit_target or -price_change <= -self.stop_loss:
                    self.consecutive_losses = 0 if -price_change > 0 else self.consecutive_losses + 1
                    self.position_direction = 0
                    self.entry_price = None
                    return 0
        
        return 3
    
    def _check_trend(self) -> int:
        """トレンド判定（SMA20）"""
        if len(self.prev_candles) < 10:  # 要求データ数を減らす
            return 0
        
        # 10期間単純移動平均
        prices = [c['close'] for c in self.prev_candles[-10:]]
        sma10 = sum(prices) / len(prices)
        
        current_price = self.prev_candles[-1]['close']
        
        # トレンド判定（閾値を緩和）
        if current_price > sma10 * 1.001:  # 0.1%上
            return 1  # 上昇トレンド
        elif current_price < sma10 * 0.999:  # 0.1%下
            return 2  # 下降トレンド
        
        return 0  # トレンドなし
    
    def _check_momi(self) -> int:
        """もみ判定（改良版）"""
        if len(self.prev_candles) < 5:
            return 0
        
        # 直近5本のATR計算（割合ベース）
        atr_sum = 0
        for i in range(1, 6):
            candle = self.prev_candles[-i]
            # 価格に対する変動率として計算
            atr_sum += (candle['high'] - candle['low']) / candle['close']
        
        avg_atr = atr_sum / 5
        
        # ATRが閾値以下ならもみ
        if avg_atr < self.momi_threshold:
            return 3
        
        return 0


if __name__ == "__main__":
    run_3months_backtest()