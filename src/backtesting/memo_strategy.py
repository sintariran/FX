"""
メモベースストラテジー実装
実際のPKGシステムと連携したバックテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional
from pkg.function_factory import PKGFunctionFactory


class MemoBasedStrategy:
    """メモベースの取引戦略"""
    
    def __init__(self):
        self.factory = PKGFunctionFactory()
        
        # 状態管理
        self.prev_candles = []
        self.position_direction = 0
        self.entry_price = None
        
    def generate_signal(self, candle: Dict, index: int, 
                       all_candles: List[Dict]) -> int:
        """
        メモロジックに基づくシグナル生成
        
        Returns:
            1: 買い, 2: 売り, 3: 待機, 0: クローズ
        """
        # 最低限のデータが必要
        if index < 3:
            return 3
        
        # 直近のキャンドルを保存
        self.prev_candles = all_candles[max(0, index-3):index+1]
        
        # 1. もみ判定
        momi_signal = self._check_momi()
        if momi_signal == 3:
            return 3  # もみなら待機
        
        # 2. 同逆判定
        dokyaku_signal = self._check_dokyaku()
        
        # 3. 行帰判定
        ikikaeri_signal = self._check_ikikaeri()
        
        # 4. オーバーシュート判定
        overshoot_signal = self._check_overshoot()
        
        # 5. 統合判定（Z関数で優先順位決定）
        z_func = self.factory.create_function("Z", arity=4)
        final_signal = z_func.evaluate({
            "input1": momi_signal,
            "input2": dokyaku_signal,
            "input3": ikikaeri_signal,
            "input4": overshoot_signal
        })
        
        # ポジション管理
        if final_signal in [1, 2]:
            # 逆方向のポジションがあればクローズ
            if self.position_direction != 0 and self.position_direction != final_signal:
                self.position_direction = final_signal
                self.entry_price = candle['close']
                return final_signal  # 新規ポジション
            elif self.position_direction == 0:
                self.position_direction = final_signal
                self.entry_price = candle['close']
                return final_signal
        
        # 利益確定条件チェック
        if self.position_direction != 0:
            if self._check_exit_condition():
                self.position_direction = 0
                return 0  # クローズ
        
        return 3  # デフォルトは待機
    
    def _check_momi(self) -> int:
        """もみ判定"""
        if len(self.prev_candles) < 2:
            return 0
        
        # レンジ幅計算
        high = max(c['high'] for c in self.prev_candles[-2:])
        low = min(c['low'] for c in self.prev_candles[-2:])
        range_width = high - low
        
        # 3pips未満ならもみ
        if range_width < 0.03:
            return 3  # 待機
        return 0
    
    def _check_dokyaku(self) -> int:
        """同逆判定"""
        if len(self.prev_candles) < 2:
            return 0
        
        prev = self.prev_candles[-2]
        current = self.prev_candles[-1]
        
        # 平均足の方向判定
        prev_ha = (prev['open'] + prev['high'] + prev['low'] + prev['close']) / 4
        current_ha = (current['open'] + current['high'] + current['low'] + current['close']) / 4
        
        if current_ha > prev_ha * 1.001:  # 0.1%上昇
            return 1  # 買い
        elif current_ha < prev_ha * 0.999:  # 0.1%下落
            return 2  # 売り
        return 0
    
    def _check_ikikaeri(self) -> int:
        """行帰判定"""
        if len(self.prev_candles) < 3:
            return 0
        
        prev2 = self.prev_candles[-3]
        prev1 = self.prev_candles[-2]
        current = self.prev_candles[-1]
        
        # 行行パターン（上昇トレンド）
        if (current['high'] > prev1['high'] and 
            current['low'] > prev1['low'] and
            prev1['high'] > prev2['high']):
            return 1  # 買い継続
        
        # 帰帰パターン（下降トレンド）
        if (current['low'] < prev1['low'] and 
            current['high'] < prev1['high'] and
            prev1['low'] < prev2['low']):
            return 2  # 売り継続
        
        return 0
    
    def _check_overshoot(self) -> int:
        """オーバーシュート判定"""
        if len(self.prev_candles) < 2:
            return 0
        
        prev = self.prev_candles[-2]
        current = self.prev_candles[-1]
        
        # 急激な価格変動を検出
        price_change = abs(current['close'] - prev['close'])
        avg_range = (prev['high'] - prev['low'])
        
        if avg_range > 0 and price_change > avg_range * 2:
            # オーバーシュートなので逆張り
            if current['close'] > prev['close']:
                return 2  # 売り
            else:
                return 1  # 買い
        
        return 0
    
    def _check_exit_condition(self) -> bool:
        """利益確定条件"""
        if len(self.prev_candles) < 2 or self.entry_price is None:
            return False
        
        current = self.prev_candles[-1]
        entry_price = self.entry_price
        
        # 利益確定幅（10pips）
        profit_target = 0.10
        
        if self.position_direction == 1:  # 買いポジション
            if current['close'] >= entry_price + profit_target:
                return True
        elif self.position_direction == 2:  # 売りポジション
            if current['close'] <= entry_price - profit_target:
                return True
        
        # ストップロス（5pips）
        stop_loss = 0.05
        if self.position_direction == 1:
            if current['close'] <= entry_price - stop_loss:
                return True
        elif self.position_direction == 2:
            if current['close'] >= entry_price + stop_loss:
                return True
        
        return False


def run_memo_backtest():
    """メモベースバックテスト実行"""
    import csv
    from backtesting.backtest_engine import BacktestEngine
    
    # データ読み込み
    data_file = "./data/historical/USDJPY_M5_synthetic.csv"
    
    with open(data_file, 'r') as f:
        reader = csv.DictReader(f)
        price_data = list(reader)
    
    # float変換
    for candle in price_data:
        for key in ['open', 'high', 'low', 'close', 'volume']:
            candle[key] = float(candle[key])
    
    print(f"📂 データ読み込み: {len(price_data)}本")
    
    # ストラテジー初期化
    strategy = MemoBasedStrategy()
    
    # バックテスト実行
    engine = BacktestEngine(initial_balance=1000000)
    results = engine.run_backtest(price_data, strategy.generate_signal)
    
    # 結果表示
    engine.print_results()
    
    # 結果保存
    engine.save_results("./data/memo_backtest_results.json")
    
    print("\n🎯 メモベースストラテジーのバックテスト完了")
    
    # パフォーマンス分析
    if results['total_trades'] > 0:
        print("\n📈 追加分析:")
        avg_win = (results['total_pnl'] / results['winning_trades'] 
                  if results['winning_trades'] > 0 else 0)
        avg_loss = (results['total_pnl'] / results['losing_trades'] 
                   if results['losing_trades'] > 0 else 0)
        
        print(f"  平均利益: ¥{avg_win:,.0f}")
        print(f"  平均損失: ¥{abs(avg_loss):,.0f}")
        
        if results['win_rate'] >= 55:
            print("  ✅ 目標勝率55%達成！")
        else:
            print(f"  ⚠️  勝率改善必要（目標: 55%, 現在: {results['win_rate']:.1f}%）")


if __name__ == "__main__":
    run_memo_backtest()