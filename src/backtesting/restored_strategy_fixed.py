"""
復元版高パフォーマンス戦略（修正版）
連続損失後の復帰ロジック追加
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List
from pkg.function_factory import PKGFunctionFactory


class RestoredHighPerformanceStrategyFixed:
    """復元版高パフォーマンス戦略（連続損失バグ修正版）"""
    
    def __init__(self, pair: str = "USDJPY"):
        self.factory = PKGFunctionFactory()
        self.pair = pair
        
        # 状態管理
        self.prev_candles = []
        self.position_direction = 0
        self.entry_price = None
        self.consecutive_losses = 0
        self.pause_trading_count = 0  # 取引休止カウンター
        
        # 通貨ペアごとの正しいパラメータ（元の成功版）
        if pair == "USDJPY":
            self.momi_threshold = 0.30  # 30pips（15分足では大きめ）
            self.profit_target = 0.50   # 50pips
            self.stop_loss = 0.25       # 25pips
            self.dokyaku_threshold = 0.002  # 0.2%
        elif pair == "EURJPY":
            self.momi_threshold = 0.40  # 40pips
            self.profit_target = 0.60   # 60pips
            self.stop_loss = 0.30       # 30pips
            self.dokyaku_threshold = 0.0025  # 0.25%
        elif pair == "EURUSD":
            self.momi_threshold = 0.0030  # 30pips（EURUSDのスケール）
            self.profit_target = 0.0050   # 50pips
            self.stop_loss = 0.0025       # 25pips
            self.dokyaku_threshold = 0.002  # 0.2%
        else:  # GBPJPY
            self.momi_threshold = 0.50  # 50pips（ボラティリティ高）
            self.profit_target = 0.80   # 80pips
            self.stop_loss = 0.40       # 40pips
            self.dokyaku_threshold = 0.003  # 0.3%
    
    def generate_signal(self, candle: Dict, index: int, 
                       all_candles: List[Dict]) -> int:
        """
        高パフォーマンス版シグナル生成（修正版）
        
        Returns:
            1: 買い, 2: 売り, 3: 待機, 0: クローズ
        """
        # 最低限のデータが必要（15分足では10本）
        if index < 10:
            return 3
        
        # 直近のキャンドルを保存
        self.prev_candles = all_candles[max(0, index-10):index+1]
        
        # 連続損失後の休止期間管理
        if self.pause_trading_count > 0:
            self.pause_trading_count -= 1
            # 休止期間中でも強いシグナルがあれば取引再開
            strong_signal = self._check_strong_recovery_signal()
            if strong_signal != 0:
                self.pause_trading_count = 0  # 休止解除
                self.consecutive_losses = 0   # リセット
                # 新規エントリー
                self.position_direction = strong_signal
                self.entry_price = candle['close']
                return strong_signal
            return 3  # 通常は待機継続
        
        # 1. もみ判定（厳格）
        momi_signal = self._check_momi_strict()
        if momi_signal == 3:
            return 3  # もみなら絶対待機
        
        # 2. 同逆判定（メイン判定）
        dokyaku_signal = self._check_dokyaku_enhanced()
        
        # 3. 行帰判定（補助）
        ikikaeri_signal = self._check_ikikaeri_pattern()
        
        # 4. 統合判定（シンプル）
        if dokyaku_signal != 0 and ikikaeri_signal != 0:
            # 両方一致したら強いシグナル
            if dokyaku_signal == ikikaeri_signal:
                final_signal = dokyaku_signal
            else:
                return 3  # 不一致なら待機
        elif dokyaku_signal != 0:
            final_signal = dokyaku_signal
        else:
            return 3  # シグナルなければ待機
        
        # ポジション管理
        if final_signal in [1, 2]:
            # 逆方向のポジションがあればクローズ後エントリー
            if self.position_direction != 0 and self.position_direction != final_signal:
                self.position_direction = final_signal
                self.entry_price = candle['close']
                return final_signal
            elif self.position_direction == 0:
                # 連続損失チェック（修正版）
                if self.consecutive_losses >= 5:
                    # 5連敗後は1日休止
                    self.pause_trading_count = 96  # 96本（24時間）休止
                    return 3
                self.position_direction = final_signal
                self.entry_price = candle['close']
                return final_signal
        
        # 利益確定・損切り
        if self.position_direction != 0:
            if self._check_exit_strict():
                prev_direction = self.position_direction
                self.position_direction = 0
                return 0
        
        return 3  # デフォルトは待機
    
    def _check_strong_recovery_signal(self) -> int:
        """強い回復シグナルの検出（休止期間中の再開用）"""
        if len(self.prev_candles) < 5:
            return 0
        
        # 過去5本で明確なトレンド形成
        closes = [c['close'] for c in self.prev_candles[-5:]]
        
        # 5本連続上昇
        if all(closes[i] > closes[i-1] for i in range(1, 5)):
            change_rate = (closes[-1] - closes[0]) / closes[0]
            if change_rate > 0.005:  # 0.5%以上の上昇
                return 1  # 強い買いシグナル
        
        # 5本連続下降
        if all(closes[i] < closes[i-1] for i in range(1, 5)):
            change_rate = (closes[0] - closes[-1]) / closes[0]
            if change_rate > 0.005:  # 0.5%以上の下降
                return 2  # 強い売りシグナル
        
        return 0
    
    def _check_momi_strict(self) -> int:
        """厳格なもみ判定（15分足用）"""
        if len(self.prev_candles) < 5:
            return 0
        
        # 過去5本（75分）のレンジ幅
        high = max(c['high'] for c in self.prev_candles[-5:])
        low = min(c['low'] for c in self.prev_candles[-5:])
        range_width = high - low
        
        # 閾値未満なら確実にもみ
        if range_width < self.momi_threshold:
            return 3  # 待機
        return 0
    
    def _check_dokyaku_enhanced(self) -> int:
        """強化版同逆判定"""
        if len(self.prev_candles) < 5:
            return 0
        
        # 平均足ベースの方向判定
        prev3 = self.prev_candles[-4]
        prev2 = self.prev_candles[-3]
        prev1 = self.prev_candles[-2]
        current = self.prev_candles[-1]
        
        # 平均足計算
        ha_prev2 = (prev2['open'] + prev2['high'] + prev2['low'] + prev2['close']) / 4
        ha_prev1 = (prev1['open'] + prev1['high'] + prev1['low'] + prev1['close']) / 4
        ha_current = (current['open'] + current['high'] + current['low'] + current['close']) / 4
        
        # トレンド判定（閾値使用）
        if (ha_current > ha_prev1 * (1 + self.dokyaku_threshold) and 
            ha_prev1 > ha_prev2 * (1 + self.dokyaku_threshold)):
            return 1  # 上昇トレンド
        elif (ha_current < ha_prev1 * (1 - self.dokyaku_threshold) and 
              ha_prev1 < ha_prev2 * (1 - self.dokyaku_threshold)):
            return 2  # 下降トレンド
        
        return 0
    
    def _check_ikikaeri_pattern(self) -> int:
        """行帰パターン判定"""
        if len(self.prev_candles) < 3:
            return 0
        
        prev2 = self.prev_candles[-3]
        prev1 = self.prev_candles[-2]
        current = self.prev_candles[-1]
        
        # 行行パターン（継続）
        if prev1['close'] > prev1['open'] and current['close'] > current['open']:
            if current['close'] > prev1['high']:
                return 1  # 強い上昇継続
        elif prev1['close'] < prev1['open'] and current['close'] < current['open']:
            if current['close'] < prev1['low']:
                return 2  # 強い下降継続
        
        # 行帰パターン（反転の可能性）
        if prev1['close'] > prev1['open'] and current['close'] < current['open']:
            if current['close'] < prev1['open']:
                return 2  # 下降転換
        elif prev1['close'] < prev1['open'] and current['close'] > current['open']:
            if current['close'] > prev1['open']:
                return 1  # 上昇転換
        
        return 0
    
    def _check_exit_strict(self) -> bool:
        """厳格な利益確定・損切り"""
        if len(self.prev_candles) < 2 or self.entry_price is None:
            return False
        
        current = self.prev_candles[-1]
        entry_price = self.entry_price
        
        if self.position_direction == 1:  # 買いポジション
            # 利確
            if current['close'] >= entry_price + self.profit_target:
                self.consecutive_losses = 0  # 勝利でリセット
                return True
            # 損切り
            if current['close'] <= entry_price - self.stop_loss:
                self.consecutive_losses += 1
                return True
        elif self.position_direction == 2:  # 売りポジション
            # 利確
            if current['close'] <= entry_price - self.profit_target:
                self.consecutive_losses = 0
                return True
            # 損切り
            if current['close'] >= entry_price + self.stop_loss:
                self.consecutive_losses += 1
                return True
        
        return False