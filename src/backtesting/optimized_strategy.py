#!/usr/bin/env python3
"""
最適化戦略実装

デバッグ結果に基づく改善:
1. ATR閾値の大幅削減
2. 同逆・行帰判定ロジックの強化
3. 通貨ペア別細かい調整
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional


class OptimizedStrategy:
    """最適化戦略"""
    
    def __init__(self, pair: str):
        self.pair = pair
        self.prev_candles = []
        self.position_direction = 0
        self.entry_price = None
        self.consecutive_losses = 0
        
        # 最適化パラメータ
        self.params = self._get_optimized_params(pair)
        
        print(f"🎯 {pair}最適化パラメータ:")
        for key, value in self.params.items():
            print(f"  {key}: {value}")
    
    def _get_optimized_params(self, pair: str) -> Dict[str, float]:
        """最適化パラメータを取得"""
        
        if pair == "USDJPY":
            return {
                "momi_threshold": 0.0008,
                "atr_multiplier": 0.5,      # 大幅削減: 1.5→0.5
                "profit_target": 0.0012,
                "stop_loss": 0.0006,
                "max_consecutive_losses": 3,
                "signal_sensitivity": 0.6   # 判定感度向上
            }
        elif pair == "EURJPY":
            return {
                "momi_threshold": 0.0012,
                "atr_multiplier": 0.6,      # 大幅削減: 1.8→0.6
                "profit_target": 0.0018,
                "stop_loss": 0.0009,
                "max_consecutive_losses": 3,
                "signal_sensitivity": 0.6
            }
        elif pair == "EURUSD":
            return {
                "momi_threshold": 0.0025,
                "atr_multiplier": 1.5,      # 適度削減: 2.0→1.5
                "profit_target": 0.004,
                "stop_loss": 0.002,
                "max_consecutive_losses": 4,
                "signal_sensitivity": 0.7   # やや厳格
            }
        elif pair == "GBPJPY":
            return {
                "momi_threshold": 0.002,
                "atr_multiplier": 0.8,      # 大幅削減: 2.2→0.8
                "profit_target": 0.003,
                "stop_loss": 0.0015,
                "max_consecutive_losses": 3,
                "signal_sensitivity": 0.5   # 最も積極的
            }
        else:
            return {
                "momi_threshold": 0.0015,
                "atr_multiplier": 1.0,
                "profit_target": 0.0025,
                "stop_loss": 0.0012,
                "max_consecutive_losses": 3,
                "signal_sensitivity": 0.6
            }
    
    def calculate_adaptive_atr(self, candles: List[Dict], period: int = 14) -> float:
        """ATR計算（最適化版）"""
        if len(candles) < period + 1:
            return 0.001
        
        true_ranges = []
        for i in range(1, min(len(candles), period + 1)):
            high = candles[i]['high']
            low = candles[i]['low']
            prev_close = candles[i-1]['close']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        return sum(true_ranges) / len(true_ranges) if true_ranges else 0.001
    
    def generate_signal(self, candle: Dict, index: int, all_candles: List[Dict]) -> int:
        """
        最適化シグナル生成
        
        Returns:
            1: 買い, 2: 売り, 3: 待機, 0: クローズ
        """
        if index < 15:
            return 3
        
        self.prev_candles = all_candles[max(0, index-15):index+1]
        
        # 連敗制限チェック（緩和）
        if self.consecutive_losses >= self.params["max_consecutive_losses"]:
            return 3
        
        # 最適化ATR計算
        current_atr = self.calculate_adaptive_atr(self.prev_candles)
        adaptive_threshold = current_atr * self.params["atr_multiplier"]
        
        # もみ判定（大幅緩和）
        current_range = candle['high'] - candle['low']
        if current_range < adaptive_threshold:
            return 3
        
        # 強化された同逆判定
        dokyaku_signal = self._enhanced_dokyaku_judgment()
        
        # 強化された行帰判定
        ikikaeri_signal = self._enhanced_ikikaeri_judgment()
        
        # 総合判定（感度調整）
        return self._integrated_judgment(dokyaku_signal, ikikaeri_signal)
    
    def _enhanced_dokyaku_judgment(self) -> int:
        """強化同逆判定"""
        if len(self.prev_candles) < 3:
            return 3
        
        current = self.prev_candles[-1]
        prev1 = self.prev_candles[-2]
        prev2 = self.prev_candles[-3]
        
        # 価格動向の分析
        current_trend = 1 if current['close'] > current['open'] else 2
        prev_trend = 1 if prev1['close'] > prev1['open'] else 2
        
        # 高値安値の関係分析
        higher_high = current['high'] > prev1['high']
        higher_low = current['low'] > prev1['low']
        lower_high = current['high'] < prev1['high']
        lower_low = current['low'] < prev1['low']
        
        # ボラティリティ考慮の乖離判定
        price_center = (current['high'] + current['low']) / 2
        prev2_center = (prev2['high'] + prev2['low']) / 2
        deviation = abs(price_center - prev2_center)
        
        # 通貨ペア別閾値調整
        if self.pair in ["USDJPY", "EURJPY", "GBPJPY"]:
            deviation_threshold = 0.5  # 円ペア用
        else:
            deviation_threshold = 0.002  # その他通貨ペア用
        
        # 判定ロジック（感度向上）
        sensitivity = self.params["signal_sensitivity"]
        
        if current_trend == prev_trend:  # トレンド継続
            if (higher_high and higher_low) or (lower_high and lower_low):
                return current_trend if deviation > deviation_threshold * sensitivity else 3
        else:  # トレンド転換
            if deviation > deviation_threshold * (1 - sensitivity):
                return current_trend
        
        return 3
    
    def _enhanced_ikikaeri_judgment(self) -> int:
        """強化行帰判定"""
        if len(self.prev_candles) < 2:
            return 3
        
        current = self.prev_candles[-1]
        prev = self.prev_candles[-2]
        
        # 平均足方向計算
        current_ha_close = (current['open'] + current['high'] + current['low'] + current['close']) / 4
        prev_ha_close = (prev['open'] + prev['high'] + prev['low'] + prev['close']) / 4
        
        if len(self.prev_candles) >= 3:
            prev2 = self.prev_candles[-3]
            prev_ha_open = (prev2['open'] + prev2['close']) / 2
        else:
            prev_ha_open = (prev['open'] + prev['close']) / 2
        
        current_ha_open = (prev_ha_open + prev_ha_close) / 2
        
        current_ha_direction = 1 if current_ha_close > current_ha_open else 2
        prev_ha_direction = 1 if prev_ha_close > prev_ha_open else 2
        
        # 高値安値更新パターン
        higher_high = current['high'] > prev['high']
        higher_low = current['low'] > prev['low']
        
        # 行帰パターン判定（感度調整）
        sensitivity = self.params["signal_sensitivity"]
        
        if current_ha_direction == prev_ha_direction:
            if higher_high and higher_low:
                return current_ha_direction  # 行行：継続
            elif sensitivity < 0.7:  # 積極的モード
                return current_ha_direction  # 行帰も許容
        else:
            if higher_high or higher_low:
                if sensitivity < 0.6:  # 非常に積極的
                    return current_ha_direction  # 帰行
        
        return 3
    
    def _integrated_judgment(self, dokyaku: int, ikikaeri: int) -> int:
        """統合判定（最適化版）"""
        
        # 両信号が一致した場合
        if dokyaku == ikikaeri and dokyaku in [1, 2]:
            return dokyaku
        
        # どちらか一方でも有効な信号がある場合（積極化）
        sensitivity = self.params["signal_sensitivity"]
        
        if sensitivity <= 0.6:  # 積極モード
            if dokyaku in [1, 2]:
                return dokyaku
            elif ikikaeri in [1, 2]:
                return ikikaeri
        
        elif sensitivity <= 0.7:  # 標準モード
            # より強い信号を優先
            if dokyaku in [1, 2] and ikikaeri == 3:
                return dokyaku
            elif ikikaeri in [1, 2] and dokyaku == 3:
                return ikikaeri
        
        # 保守的モード：両方一致時のみ
        return 3
    
    def update_performance(self, trade_result: str):
        """パフォーマンス更新"""
        if trade_result == "loss":
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0


def run_optimized_backtest():
    """最適化バックテスト実行"""
    
    print("=" * 80)
    print("🚀 最適化戦略バックテスト実行")
    print("=" * 80)
    print("改善点:")
    print("1. ATR閾値50-70%削減")
    print("2. 同逆・行帰判定強化")
    print("3. 通貨ペア別感度調整")
    print("=" * 80)
    
    # パラメータテスト
    pairs = ["USDJPY", "EURJPY", "EURUSD", "GBPJPY"]
    
    for pair in pairs:
        print(f"\n🔧 {pair} 最適化パラメータテスト")
        strategy = OptimizedStrategy(pair)
        
        # シグナル生成テスト（サンプル）
        print(f"  ✅ 戦略初期化完了")
        print(f"  📊 ATR倍率: {strategy.params['atr_multiplier']}")
        print(f"  🎯 感度設定: {strategy.params['signal_sensitivity']}")


if __name__ == "__main__":
    run_optimized_backtest()