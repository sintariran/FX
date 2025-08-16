#!/usr/bin/env python3
"""
通貨ペア適応型バックテスト戦略

EURUSD低取引回数問題の解決:
- 通貨ペア別の動的閾値設定
- ボラティリティ適応型パラメータ
- ATRベースのもみ判定
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional
import csv


class CurrencyAdaptiveStrategy:
    """通貨ペア適応型戦略"""
    
    def __init__(self, pair: str):
        self.pair = pair
        self.prev_candles = []
        self.position_direction = 0
        self.entry_price = None
        self.consecutive_losses = 0
        
        # 通貨ペア別パラメータ設定
        self.params = self._get_currency_params(pair)
        
        print(f"🎯 {pair}用パラメータ設定:")
        for key, value in self.params.items():
            print(f"  {key}: {value}")
    
    def _get_currency_params(self, pair: str) -> Dict[str, float]:
        """通貨ペア別パラメータを取得"""
        
        # 基本ATR分析に基づく適応型設定
        if pair == "USDJPY":
            return {
                "momi_threshold": 0.0008,    # 0.8pips (低ボラティリティ)
                "profit_target": 0.0015,     # 1.5pips
                "stop_loss": 0.0008,         # 0.8pips
                "atr_multiplier": 1.5,       # ATR倍率
                "max_consecutive_losses": 4  # 連敗許容
            }
        elif pair == "EURJPY":
            return {
                "momi_threshold": 0.0012,    # 1.2pips (中ボラティリティ)
                "profit_target": 0.0020,     # 2.0pips  
                "stop_loss": 0.0010,         # 1.0pips
                "atr_multiplier": 1.8,
                "max_consecutive_losses": 4
            }
        elif pair == "EURUSD":
            return {
                "momi_threshold": 0.0025,    # 25pips (高ボラティリティ対応)
                "profit_target": 0.0040,     # 40pips
                "stop_loss": 0.0020,         # 20pips  
                "atr_multiplier": 2.0,
                "max_consecutive_losses": 5  # より多く試行
            }
        elif pair == "GBPJPY":
            return {
                "momi_threshold": 0.0020,    # 2.0pips (高ボラティリティ)
                "profit_target": 0.0035,     # 3.5pips
                "stop_loss": 0.0018,         # 1.8pips
                "atr_multiplier": 2.2,
                "max_consecutive_losses": 5
            }
        else:
            # デフォルト（中ボラティリティ）
            return {
                "momi_threshold": 0.0015,
                "profit_target": 0.0025,
                "stop_loss": 0.0012,
                "atr_multiplier": 1.8,
                "max_consecutive_losses": 4
            }
    
    def calculate_adaptive_atr(self, candles: List[Dict], period: int = 14) -> float:
        """適応型ATR計算"""
        if len(candles) < period + 1:
            return 0.001  # デフォルト値
        
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
        適応型シグナル生成
        
        Returns:
            1: 買い, 2: 売り, 3: 待機, 0: クローズ
        """
        # 最低限のデータが必要
        if index < 15:  # ATR計算に必要
            return 3
        
        # 直近のキャンドルを保存
        self.prev_candles = all_candles[max(0, index-15):index+1]
        
        # 連敗制限チェック（通貨ペア別）
        if self.consecutive_losses >= self.params["max_consecutive_losses"]:
            return 3
        
        # 適応型ATR計算
        current_atr = self.calculate_adaptive_atr(self.prev_candles)
        adaptive_threshold = current_atr * self.params["atr_multiplier"]
        
        # 動的もみ判定
        current_range = candle['high'] - candle['low']
        if current_range < adaptive_threshold:
            return 3  # もみ = 待機
        
        # 1. 改良同逆判定
        dokyaku_signal = self._check_adaptive_dokyaku()
        
        # 2. 改良行帰判定  
        ikikaeri_signal = self._check_adaptive_ikikaeri()
        
        # 3. ボラティリティ調整済み統合判定
        return self._integrate_adaptive_signals(dokyaku_signal, ikikaeri_signal, current_atr)
    
    def _check_adaptive_dokyaku(self) -> int:
        """適応型同逆判定"""
        if len(self.prev_candles) < 3:
            return 3
        
        current = self.prev_candles[-1]
        prev1 = self.prev_candles[-2]
        prev2 = self.prev_candles[-3]
        
        # 前々足からの乖離チェック（通貨ペア別調整）
        deviation_threshold = self.params["momi_threshold"] * 2
        
        # 高値からの乖離
        high_deviation = abs(current['close'] - prev2['high'])
        low_deviation = abs(current['close'] - prev2['low'])
        
        if high_deviation < deviation_threshold:
            return 2  # 売り傾向
        elif low_deviation < deviation_threshold:
            return 1  # 買い傾向
        
        return 3  # 判定不明
    
    def _check_adaptive_ikikaeri(self) -> int:
        """適応型行帰判定"""
        if len(self.prev_candles) < 2:
            return 3
        
        current = self.prev_candles[-1]
        prev = self.prev_candles[-2]
        
        # 平均足方向の計算
        current_ha_direction = 1 if current['close'] > current['open'] else 2
        prev_ha_direction = 1 if prev['close'] > prev['open'] else 2
        
        # 高値安値更新の確認
        higher_high = current['high'] > prev['high']
        higher_low = current['low'] > prev['low']
        
        # 行帰パターン判定（ボラティリティ調整済み）
        if current_ha_direction == prev_ha_direction:
            if higher_high and higher_low:
                return current_ha_direction  # 行行：継続
            else:
                return 3  # 行帰：様子見
        else:
            if higher_high or higher_low:
                return current_ha_direction  # 帰行：転換後進行
            else:
                return 3  # 帰戻：様子見
    
    def _integrate_adaptive_signals(self, dokyaku: int, ikikaeri: int, atr: float) -> int:
        """適応型信号統合"""
        
        # 高ボラティリティ時は慎重に
        volatility_factor = atr / self.params["momi_threshold"]
        
        if volatility_factor > 3.0:  # 非常に高いボラティリティ
            # 両信号一致時のみエントリー
            if dokyaku == ikikaeri and dokyaku in [1, 2]:
                return dokyaku
            return 3
        
        elif volatility_factor > 2.0:  # 高ボラティリティ
            # どちらか一つでも信号があればエントリー
            if dokyaku in [1, 2]:
                return dokyaku
            elif ikikaeri in [1, 2]:
                return ikikaeri
            return 3
        
        else:  # 通常ボラティリティ
            # 従来ロジック
            if dokyaku in [1, 2]:
                return dokyaku
            elif ikikaeri in [1, 2]:
                return ikikaeri
            return 3
    
    def update_performance(self, trade_result: str):
        """パフォーマンス更新"""
        if trade_result == "loss":
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0


def run_adaptive_backtest_sample():
    """適応型バックテストのサンプル実行"""
    
    print("=" * 80)
    print("🚀 通貨ペア適応型バックテスト実行")
    print("=" * 80)
    
    pairs = ["USDJPY", "EURJPY", "EURUSD", "GBPJPY"]
    
    for pair in pairs:
        print(f"\n{'='*60}")
        print(f"📊 {pair} 適応型戦略テスト")
        print(f"{'='*60}")
        
        # 戦略初期化
        strategy = CurrencyAdaptiveStrategy(pair)
        
        # データ読み込みテスト
        data_file = f"./data/histdata/{pair}_M15_3months.csv"
        if not os.path.exists(data_file):
            print(f"❌ データファイルなし: {data_file}")
            continue
        
        # 最初の100足でシグナルテスト
        test_data = []
        with open(data_file, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 100:
                    break
                test_data.append({
                    'timestamp': row['timestamp'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close'])
                })
        
        # シグナル生成テスト
        signals = []
        for i in range(20, min(100, len(test_data))):
            signal = strategy.generate_signal(test_data[i], i, test_data)
            if signal in [1, 2]:  # エントリーシグナル
                signals.append((test_data[i]['timestamp'], 'BUY' if signal == 1 else 'SELL'))
        
        print(f"✅ シグナル生成数: {len(signals)}")
        print(f"   最初の5つ: {signals[:5]}")
        
        # ATR分析
        if len(test_data) > 20:
            atr = strategy.calculate_adaptive_atr(test_data[5:20])
            threshold = atr * strategy.params["atr_multiplier"]
            print(f"📈 ATR: {atr:.6f}, 適応閾値: {threshold:.6f}")


if __name__ == "__main__":
    run_adaptive_backtest_sample()