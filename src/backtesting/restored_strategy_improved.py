"""
復元版高パフォーマンス戦略（改良版）
前足・前々足のもみ判定を含む正しい実装
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List
from pkg.function_factory import PKGFunctionFactory


class RestoredHighPerformanceStrategyImproved:
    """復元版高パフォーマンス戦略（もみ判定改良版）"""
    
    def __init__(self, pair: str = "USDJPY"):
        self.factory = PKGFunctionFactory()
        self.pair = pair
        
        # 状態管理
        self.prev_candles = []
        self.position_direction = 0
        self.entry_price = None
        self.consecutive_losses = 0
        self.pause_trading_count = 0
        
        # 前足もみ状態の記憶
        self.prev_momi_states = []  # 過去のもみ判定結果を保存
        
        # 通貨ペアごとのパラメータ
        if pair == "USDJPY":
            self.momi_threshold = 0.30  # 30pips
            self.profit_target = 0.50   # 50pips
            self.stop_loss = 0.25       # 25pips
            self.dokyaku_threshold = 0.002  # 0.2%
        elif pair == "EURJPY":
            self.momi_threshold = 0.40  # 40pips
            self.profit_target = 0.60   # 60pips
            self.stop_loss = 0.30       # 30pips
            self.dokyaku_threshold = 0.0025  # 0.25%
        elif pair == "EURUSD":
            self.momi_threshold = 0.0030  # 30pips
            self.profit_target = 0.0050   # 50pips
            self.stop_loss = 0.0025       # 25pips
            self.dokyaku_threshold = 0.002  # 0.2%
        else:  # GBPJPY
            self.momi_threshold = 0.50  # 50pips
            self.profit_target = 0.80   # 80pips
            self.stop_loss = 0.40       # 40pips
            self.dokyaku_threshold = 0.003  # 0.3%
    
    def generate_signal(self, candle: Dict, index: int, 
                       all_candles: List[Dict]) -> int:
        """
        改良版シグナル生成（前足もみ判定込み）
        
        Returns:
            1: 買い, 2: 売り, 3: 待機, 0: クローズ
        """
        # 最低限のデータが必要
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
                self.pause_trading_count = 0
                self.consecutive_losses = 0
                self.position_direction = strong_signal
                self.entry_price = candle['close']
                return strong_signal
            return 3
        
        # 1. 包括的もみ判定（現在足、前足、前々足）
        momi_signal = self._check_momi_comprehensive()
        if momi_signal == 3:
            # もみ状態を記録
            self.prev_momi_states.append(True)
            if len(self.prev_momi_states) > 10:
                self.prev_momi_states.pop(0)
            return 3  # もみなら待機
        else:
            self.prev_momi_states.append(False)
            if len(self.prev_momi_states) > 10:
                self.prev_momi_states.pop(0)
        
        # 2. もみ後のブレイクアウト判定
        breakout_signal = self._check_momi_breakout()
        
        # 3. 同逆判定
        dokyaku_signal = self._check_dokyaku_enhanced()
        
        # 4. 行帰判定
        ikikaeri_signal = self._check_ikikaeri_pattern()
        
        # 5. 統合判定
        final_signal = 0
        
        # もみブレイクアウトが最優先
        if breakout_signal != 0:
            final_signal = breakout_signal
        # 同逆と行帰の一致
        elif dokyaku_signal != 0 and ikikaeri_signal != 0:
            if dokyaku_signal == ikikaeri_signal:
                final_signal = dokyaku_signal
        # 同逆のみ（弱いシグナル）
        elif dokyaku_signal != 0:
            # 連続もみ後なら見送り
            if len(self.prev_momi_states) >= 3 and all(self.prev_momi_states[-3:]):
                return 3
            final_signal = dokyaku_signal
        
        # ポジション管理
        if final_signal in [1, 2]:
            # 逆方向のポジションがあればクローズ後エントリー
            if self.position_direction != 0 and self.position_direction != final_signal:
                self.position_direction = final_signal
                self.entry_price = candle['close']
                return final_signal
            elif self.position_direction == 0:
                # 連続損失チェック
                if self.consecutive_losses >= 5:
                    self.pause_trading_count = 96  # 1日休止
                    return 3
                self.position_direction = final_signal
                self.entry_price = candle['close']
                return final_signal
        
        # 利益確定・損切り
        if self.position_direction != 0:
            if self._check_exit_strict():
                self.position_direction = 0
                return 0
        
        return 3
    
    def _check_momi_comprehensive(self) -> int:
        """包括的もみ判定（現在足、前足、前々足）"""
        if len(self.prev_candles) < 3:
            return 0
        
        # 現在足のレンジ
        current = self.prev_candles[-1]
        current_range = current['high'] - current['low']
        
        # 前足のレンジ
        prev1 = self.prev_candles[-2]
        prev1_range = prev1['high'] - prev1['low']
        
        # 前々足のレンジ
        prev2 = self.prev_candles[-3]
        prev2_range = prev2['high'] - prev2['low']
        
        # 3本合計のレンジ
        total_high = max(current['high'], prev1['high'], prev2['high'])
        total_low = min(current['low'], prev1['low'], prev2['low'])
        total_range = total_high - total_low
        
        # もみ判定条件（メモロジック準拠・15分足適正版）
        # 1. 現在足が小さい
        if current_range < self.momi_threshold * 0.3:  # 15分足の通常判定
            return 3
        
        # 2. 前足と前々足が両方小さい（連続もみ）
        if prev1_range < self.momi_threshold * 0.5 and prev2_range < self.momi_threshold * 0.5:
            return 3
        
        # 3. 3本全体でレンジが狭い
        if total_range < self.momi_threshold:  # 標準判定
            return 3
        
        # 4. 価格の往復（もみの典型パターン）
        if len(self.prev_candles) >= 5:
            closes = [c['close'] for c in self.prev_candles[-5:]]
            max_close = max(closes)
            min_close = min(closes)
            
            # 終値が狭いレンジで往復
            if (max_close - min_close) < self.momi_threshold * 0.8:
                # かつ上下動がある（単調ではない）
                up_moves = sum(1 for i in range(1, 5) if closes[i] > closes[i-1])
                down_moves = sum(1 for i in range(1, 5) if closes[i] < closes[i-1])
                if up_moves >= 2 and down_moves >= 2:
                    return 3
        
        return 0
    
    def _check_momi_breakout(self) -> int:
        """もみブレイクアウト判定"""
        if len(self.prev_momi_states) < 3:
            return 0
        
        # 直前3本がもみ状態だった
        if all(self.prev_momi_states[-3:]):
            current = self.prev_candles[-1]
            prev1 = self.prev_candles[-2]
            
            # ブレイクアウト判定
            # 上方ブレイク
            if current['close'] > prev1['high'] + self.momi_threshold * 0.3:
                return 1
            # 下方ブレイク
            if current['close'] < prev1['low'] - self.momi_threshold * 0.3:
                return 2
        
        return 0
    
    def _check_strong_recovery_signal(self) -> int:
        """強い回復シグナル（休止期間中の再開用）"""
        if len(self.prev_candles) < 5:
            return 0
        
        closes = [c['close'] for c in self.prev_candles[-5:]]
        
        # 5本連続上昇
        if all(closes[i] > closes[i-1] for i in range(1, 5)):
            change_rate = (closes[-1] - closes[0]) / closes[0]
            if change_rate > 0.005:  # 0.5%以上
                return 1
        
        # 5本連続下降
        if all(closes[i] < closes[i-1] for i in range(1, 5)):
            change_rate = (closes[0] - closes[-1]) / closes[0]
            if change_rate > 0.005:
                return 2
        
        return 0
    
    def _check_dokyaku_enhanced(self) -> int:
        """強化版同逆判定"""
        if len(self.prev_candles) < 5:
            return 0
        
        prev3 = self.prev_candles[-4]
        prev2 = self.prev_candles[-3]
        prev1 = self.prev_candles[-2]
        current = self.prev_candles[-1]
        
        # 平均足計算
        ha_prev2 = (prev2['open'] + prev2['high'] + prev2['low'] + prev2['close']) / 4
        ha_prev1 = (prev1['open'] + prev1['high'] + prev1['low'] + prev1['close']) / 4
        ha_current = (current['open'] + current['high'] + current['low'] + current['close']) / 4
        
        # トレンド判定
        if (ha_current > ha_prev1 * (1 + self.dokyaku_threshold) and 
            ha_prev1 > ha_prev2 * (1 + self.dokyaku_threshold)):
            return 1
        elif (ha_current < ha_prev1 * (1 - self.dokyaku_threshold) and 
              ha_prev1 < ha_prev2 * (1 - self.dokyaku_threshold)):
            return 2
        
        return 0
    
    def _check_ikikaeri_pattern(self) -> int:
        """行帰パターン判定"""
        if len(self.prev_candles) < 3:
            return 0
        
        prev2 = self.prev_candles[-3]
        prev1 = self.prev_candles[-2]
        current = self.prev_candles[-1]
        
        # 行行パターン
        if prev1['close'] > prev1['open'] and current['close'] > current['open']:
            if current['close'] > prev1['high']:
                return 1
        elif prev1['close'] < prev1['open'] and current['close'] < current['open']:
            if current['close'] < prev1['low']:
                return 2
        
        # 行帰パターン
        if prev1['close'] > prev1['open'] and current['close'] < current['open']:
            if current['close'] < prev1['open']:
                return 2
        elif prev1['close'] < prev1['open'] and current['close'] > current['open']:
            if current['close'] > prev1['open']:
                return 1
        
        return 0
    
    def _check_exit_strict(self) -> bool:
        """厳格な利益確定・損切り"""
        if len(self.prev_candles) < 2 or self.entry_price is None:
            return False
        
        current = self.prev_candles[-1]
        entry_price = self.entry_price
        
        if self.position_direction == 1:  # 買い
            if current['close'] >= entry_price + self.profit_target:
                self.consecutive_losses = 0
                return True
            if current['close'] <= entry_price - self.stop_loss:
                self.consecutive_losses += 1
                return True
        elif self.position_direction == 2:  # 売り
            if current['close'] <= entry_price - self.profit_target:
                self.consecutive_losses = 0
                return True
            if current['close'] >= entry_price + self.stop_loss:
                self.consecutive_losses += 1
                return True
        
        return False