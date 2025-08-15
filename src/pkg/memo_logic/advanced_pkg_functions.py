"""
Week 6: 高度なPKG関数実装
もみ判定、オーバーシュート判定、時間結合等の複雑なロジック
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging

from .core_pkg_functions import (
    BasePKGFunction, PKGId, MarketData, OperationSignal,
    TimeFrame, Currency, Period
)

class MomiFunction(BasePKGFunction):
    """
    もみ判定PKG関数
    
    メモファイルから抽出したもみ判定ロジック:
    - レンジ幅3pips未満でもみ判定
    - 残足による抜けタイミング評価
    - 内包関係による時間足別もみ状態管理
    - 軸周期による判定基準の動的変更
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        self.momi_threshold = 3.0  # pips
        self.range_analysis_periods = [10, 15, 30, 45, 60, 90, 180]
        
    def execute(self, data: Dict[str, any]) -> OperationSignal:
        """もみ判定の実行"""
        if not self.validate_input(data):
            return None
            
        market_data = data.get('market_data', [])
        if len(market_data) < 10:
            return None
            
        # もみ状態の判定
        momi_state = self._determine_momi_state(market_data)
        direction = self._calculate_momi_direction(market_data, momi_state)
        confidence = self._calculate_momi_confidence(market_data, momi_state)
        
        signal = OperationSignal(
            pkg_id=self.pkg_id,
            signal_type='momi',
            direction=direction,
            confidence=confidence,
            timestamp=market_data[-1].timestamp,
            metadata={
                'momi_state': momi_state,
                'range_width': self._calculate_range_width(market_data),
                'breakout_probability': self._calculate_breakout_probability(market_data),
                'axis_period': self._determine_axis_period(market_data)
            }
        )
        
        return signal
    
    def _determine_momi_state(self, market_data: List[MarketData]) -> Dict:
        """
        もみ状態の判定
        メモ: レンジ幅、軸周期による判定
        """
        recent_data = market_data[-20:]  # 直近20足を分析
        
        # レンジ幅の計算
        range_width = self._calculate_range_width(recent_data)
        
        # 軸周期の決定
        axis_period = self._determine_axis_period(recent_data)
        
        # レンジ状態の詳細分析
        range_analysis = self._analyze_range_structure(recent_data)
        
        # もみ判定
        is_momi = range_width < self.momi_threshold and range_analysis['stability'] > 0.7
        
        return {
            'is_momi': is_momi,
            'range_width': range_width,
            'axis_period': axis_period,
            'range_analysis': range_analysis,
            'remaining_bars': self._calculate_remaining_bars(recent_data),
            'breakout_direction': self._predict_breakout_direction(recent_data)
        }
    
    def _calculate_range_width(self, market_data: List[MarketData]) -> float:
        """レンジ幅の計算（pips単位）"""
        if not market_data:
            return 0.0
            
        highs = [bar.high for bar in market_data]
        lows = [bar.low for bar in market_data]
        
        range_high = max(highs)
        range_low = min(lows)
        
        # USDJPY基準でpips計算（簡易実装）
        return (range_high - range_low) * 100
    
    def _determine_axis_period(self, market_data: List[MarketData]) -> int:
        """
        軸周期の決定
        メモ: 価格がどの線の間にいるかでレンジが決まる
        """
        current_price = market_data[-1].close
        
        # 各周期の移動平均を計算
        period_mas = {}
        for period in self.range_analysis_periods:
            if len(market_data) >= period:
                prices = [bar.close for bar in market_data[-period:]]
                period_mas[period] = np.mean(prices)
        
        # 価格が最も近い移動平均の周期を軸周期とする
        if not period_mas:
            return 10  # デフォルト
            
        min_distance = float('inf')
        axis_period = 10
        
        for period, ma_value in period_mas.items():
            distance = abs(current_price - ma_value)
            if distance < min_distance:
                min_distance = distance
                axis_period = period
                
        return axis_period
    
    def _analyze_range_structure(self, market_data: List[MarketData]) -> Dict:
        """
        レンジ構造の分析
        メモ: 上下の周期の線よりも長い線が180と上下の線との間にいる場合
        """
        if len(market_data) < 5:
            return {'stability': 0.0, 'trend_strength': 0.0}
            
        # 価格の安定性を評価
        closes = [bar.close for bar in market_data]
        price_std = np.std(closes)
        price_mean = np.mean(closes)
        stability = 1.0 - min(1.0, price_std / price_mean) if price_mean > 0 else 0.0
        
        # トレンド強度を評価
        trend_strength = self._calculate_trend_strength(market_data)
        
        # 周期線の配置分析
        line_arrangement = self._analyze_line_arrangement(market_data)
        
        return {
            'stability': stability,
            'trend_strength': trend_strength,
            'line_arrangement': line_arrangement,
            'consolidation_time': len(market_data)
        }
    
    def _calculate_trend_strength(self, market_data: List[MarketData]) -> float:
        """トレンド強度の計算"""
        if len(market_data) < 2:
            return 0.0
            
        closes = [bar.close for bar in market_data]
        
        # 線形回帰の傾きでトレンド強度を評価
        x = np.arange(len(closes))
        slope, _ = np.polyfit(x, closes, 1)
        
        # 正規化（価格に対する相対的な傾き）
        return abs(slope) / np.mean(closes) if np.mean(closes) > 0 else 0.0
    
    def _analyze_line_arrangement(self, market_data: List[MarketData]) -> Dict:
        """
        周期線の配置分析
        メモ: 180に対して上下の線がどのように配置されているか
        """
        if len(market_data) < 180:
            return {'arrangement': 'insufficient_data'}
            
        current_price = market_data[-1].close
        
        # 各周期の移動平均を計算
        ma_180 = np.mean([bar.close for bar in market_data[-180:]])
        ma_90 = np.mean([bar.close for bar in market_data[-90:]]) if len(market_data) >= 90 else ma_180
        ma_30 = np.mean([bar.close for bar in market_data[-30:]]) if len(market_data) >= 30 else ma_180
        ma_10 = np.mean([bar.close for bar in market_data[-10:]]) if len(market_data) >= 10 else ma_180
        
        # 価格と各移動平均の位置関係を分析
        relative_positions = {
            'price_vs_ma180': 1 if current_price > ma_180 else -1,
            'ma90_vs_ma180': 1 if ma_90 > ma_180 else -1,
            'ma30_vs_ma180': 1 if ma_30 > ma_180 else -1,
            'ma10_vs_ma180': 1 if ma_10 > ma_180 else -1
        }
        
        # レンジ判定のロジック
        if abs(current_price - ma_180) < abs(current_price - ma_30):
            range_type = "180-30_range"
        elif abs(current_price - ma_30) < abs(current_price - ma_10):
            range_type = "30-10_range"
        else:
            range_type = "no_range"
            
        return {
            'arrangement': range_type,
            'relative_positions': relative_positions,
            'ma_values': {'ma_180': ma_180, 'ma_90': ma_90, 'ma_30': ma_30, 'ma_10': ma_10}
        }
    
    def _calculate_remaining_bars(self, market_data: List[MarketData]) -> int:
        """
        残足の計算
        メモ: 残足でもみ評価するため、抜けタイミングは評価できる
        """
        if len(market_data) < 5:
            return 0
            
        # 平均足の転換までの推定残足
        recent_bars = market_data[-5:]
        ha_direction_changes = 0
        
        for i in range(1, len(recent_bars)):
            prev_ha_dir = 1 if recent_bars[i-1].heikin_ashi_close > recent_bars[i-1].heikin_ashi_open else -1
            curr_ha_dir = 1 if recent_bars[i].heikin_ashi_close > recent_bars[i].heikin_ashi_open else -1
            
            if prev_ha_dir != curr_ha_dir:
                ha_direction_changes += 1
        
        # 転換頻度から残足を推定
        if ha_direction_changes > 2:
            return 1  # 頻繁な転換 = 近い転換
        elif ha_direction_changes > 0:
            return 3  # 中程度
        else:
            return 5  # 安定 = 遠い転換
    
    def _predict_breakout_direction(self, market_data: List[MarketData]) -> int:
        """ブレイクアウト方向の予測"""
        if len(market_data) < 10:
            return 0
            
        # ボリューム分析（簡易実装）
        recent_volumes = [bar.volume for bar in market_data[-10:]]
        volume_trend = np.polyfit(range(len(recent_volumes)), recent_volumes, 1)[0]
        
        # 価格の位置分析
        recent_closes = [bar.close for bar in market_data[-10:]]
        range_high = max([bar.high for bar in market_data[-20:]])
        range_low = min([bar.low for bar in market_data[-20:]])
        
        current_position = (recent_closes[-1] - range_low) / (range_high - range_low)
        
        # 予測ロジック
        if current_position > 0.7 and volume_trend > 0:
            return 1  # 上ブレイク
        elif current_position < 0.3 and volume_trend > 0:
            return 2  # 下ブレイク
        else:
            return 0  # 中立
    
    def _calculate_breakout_probability(self, market_data: List[MarketData]) -> float:
        """ブレイクアウト確率の計算"""
        if len(market_data) < 20:
            return 0.0
            
        # 統計的分析
        consolidation_time = self._get_consolidation_duration(market_data)
        volume_buildup = self._analyze_volume_buildup(market_data)
        pressure_points = self._analyze_pressure_points(market_data)
        
        # 確率計算
        time_factor = min(1.0, consolidation_time / 50.0)  # 長期もみは高確率
        volume_factor = min(1.0, volume_buildup)
        pressure_factor = pressure_points
        
        return np.mean([time_factor, volume_factor, pressure_factor])
    
    def _get_consolidation_duration(self, market_data: List[MarketData]) -> int:
        """もみ合い期間の算出"""
        # 簡易実装: 直近の大きな価格変動からの期間
        threshold = self.momi_threshold * 2
        
        for i in range(len(market_data) - 1, 0, -1):
            price_change = abs(market_data[i].close - market_data[i-1].close) * 100
            if price_change > threshold:
                return len(market_data) - i
                
        return len(market_data)
    
    def _analyze_volume_buildup(self, market_data: List[MarketData]) -> float:
        """ボリューム蓄積の分析"""
        if len(market_data) < 10:
            return 0.0
            
        recent_volumes = [bar.volume for bar in market_data[-10:]]
        baseline_volumes = [bar.volume for bar in market_data[-20:-10]] if len(market_data) >= 20 else recent_volumes
        
        recent_avg = np.mean(recent_volumes)
        baseline_avg = np.mean(baseline_volumes)
        
        return min(1.0, recent_avg / baseline_avg) if baseline_avg > 0 else 0.0
    
    def _analyze_pressure_points(self, market_data: List[MarketData]) -> float:
        """圧力ポイントの分析"""
        if len(market_data) < 5:
            return 0.0
            
        # サポート・レジスタンスレベルでの反発回数
        recent_data = market_data[-20:]
        highs = [bar.high for bar in recent_data]
        lows = [bar.low for bar in recent_data]
        
        resistance_level = max(highs)
        support_level = min(lows)
        
        # 各レベルでのタッチ回数
        resistance_touches = sum(1 for bar in recent_data if abs(bar.high - resistance_level) < 0.001)
        support_touches = sum(1 for bar in recent_data if abs(bar.low - support_level) < 0.001)
        
        # 圧力の強さを評価
        pressure_strength = (resistance_touches + support_touches) / len(recent_data)
        return min(1.0, pressure_strength * 2)
    
    def _calculate_momi_direction(self, market_data: List[MarketData], 
                                momi_state: Dict) -> int:
        """もみ状態での方向判定"""
        if not momi_state['is_momi']:
            return 0  # もみ状態でない場合は中立
            
        # ブレイクアウト方向の予測
        breakout_direction = momi_state['breakout_direction']
        
        # 残足が少ない場合はブレイクアウト方向を採用
        if momi_state['remaining_bars'] <= 2:
            return breakout_direction
            
        # レンジ内での振動方向
        current_price = market_data[-1].close
        range_analysis = momi_state['range_analysis']
        ma_values = range_analysis['line_arrangement']['ma_values']
        
        if current_price > ma_values['ma_30']:
            return 2  # レンジ上部 → 下方向期待
        elif current_price < ma_values['ma_30']:
            return 1  # レンジ下部 → 上方向期待
        else:
            return 0  # 中央 → 中立
    
    def _calculate_momi_confidence(self, market_data: List[MarketData], 
                                 momi_state: Dict) -> float:
        """もみ判定の信頼度計算"""
        if not momi_state['is_momi']:
            return 0.1  # もみでない場合は低信頼度
            
        confidence_factors = []
        
        # レンジの安定性
        stability = momi_state['range_analysis']['stability']
        confidence_factors.append(stability)
        
        # もみ合い期間の長さ（長いほど高信頼度）
        consolidation_time = momi_state['range_analysis']['consolidation_time']
        time_factor = min(1.0, consolidation_time / 30.0)
        confidence_factors.append(time_factor)
        
        # ブレイクアウト確率
        breakout_prob = momi_state.get('breakout_probability', 0.5)
        confidence_factors.append(breakout_prob)
        
        # 軸周期の信頼性
        axis_period = momi_state['axis_period']
        period_factor = min(1.0, axis_period / 60.0)  # 長い周期ほど信頼性が高い
        confidence_factors.append(period_factor)
        
        return np.mean(confidence_factors)

class OvershootFunction(BasePKGFunction):
    """
    オーバーシュート判定PKG関数
    
    メモファイルから抽出したオーバーシュート判定ロジック:
    - 前足Os残足が今足換算で2以上でオーバーシュート
    - 実行時間目標: 550.6ms
    - 転換方向と逆方向のオーバーシュート成立確認
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        self.overshoot_threshold = 2.0
        
    def execute(self, data: Dict[str, any]) -> OperationSignal:
        """オーバーシュート判定の実行"""
        if not self.validate_input(data):
            return None
            
        market_data = data.get('market_data', [])
        if len(market_data) < 5:
            return None
            
        # オーバーシュート状態の分析
        overshoot_analysis = self._analyze_overshoot_conditions(market_data)
        direction = self._calculate_overshoot_direction(market_data, overshoot_analysis)
        confidence = self._calculate_overshoot_confidence(market_data, overshoot_analysis)
        
        signal = OperationSignal(
            pkg_id=self.pkg_id,
            signal_type='overshoot',
            direction=direction,
            confidence=confidence,
            timestamp=market_data[-1].timestamp,
            metadata={
                'overshoot_analysis': overshoot_analysis,
                'remaining_bars_current': overshoot_analysis.get('current_remaining_bars', 0),
                'remaining_bars_previous': overshoot_analysis.get('previous_remaining_bars', 0)
            }
        )
        
        return signal
    
    def _analyze_overshoot_conditions(self, market_data: List[MarketData]) -> Dict:
        """
        オーバーシュート条件の分析
        メモ: 前足Os残足が今足換算で2以上
        """
        if len(market_data) < 3:
            return {'overshoot_detected': False}
            
        current_bar = market_data[-1]
        previous_bar = market_data[-2]
        
        # Os残足の計算
        current_remaining = self._calculate_os_remaining_bars(market_data, -1)
        previous_remaining = self._calculate_os_remaining_bars(market_data, -2)
        
        # 今足換算での前足残足
        previous_remaining_current_basis = self._convert_to_current_timeframe(
            previous_remaining, previous_bar, current_bar
        )
        
        # オーバーシュート判定
        overshoot_detected = previous_remaining_current_basis >= self.overshoot_threshold
        
        # 転換方向の分析
        trend_direction = self._analyze_trend_direction(market_data)
        
        # 逆方向オーバーシュートの確認
        reverse_overshoot = self._check_reverse_direction_overshoot(
            market_data, trend_direction
        )
        
        return {
            'overshoot_detected': overshoot_detected,
            'current_remaining_bars': current_remaining,
            'previous_remaining_bars': previous_remaining,
            'previous_remaining_current_basis': previous_remaining_current_basis,
            'trend_direction': trend_direction,
            'reverse_overshoot': reverse_overshoot,
            'overshoot_strength': previous_remaining_current_basis / self.overshoot_threshold if self.overshoot_threshold > 0 else 0
        }
    
    def _calculate_os_remaining_bars(self, market_data: List[MarketData], 
                                   bar_index: int) -> float:
        """
        Os残足の計算
        oscillatorベースの残足計算（簡易実装）
        """
        if abs(bar_index) > len(market_data):
            return 0.0
            
        target_bar = market_data[bar_index]
        
        # 移動平均からの乖離を基にした残足計算
        if len(market_data) >= 14:
            recent_closes = [bar.close for bar in market_data[bar_index-13:bar_index+1]]
            ma_14 = np.mean(recent_closes)
            
            # RSIライクな計算
            price_changes = []
            for i in range(1, len(recent_closes)):
                change = recent_closes[i] - recent_closes[i-1]
                price_changes.append(change)
            
            gains = [change for change in price_changes if change > 0]
            losses = [-change for change in price_changes if change < 0]
            
            avg_gain = np.mean(gains) if gains else 0
            avg_loss = np.mean(losses) if losses else 0
            
            if avg_loss == 0:
                rs = 100
            else:
                rs = avg_gain / avg_loss
                
            rsi = 100 - (100 / (1 + rs))
            
            # RSIから残足を推定
            if rsi > 70:
                return (100 - rsi) / 10  # 買われすぎ → 下落残足
            elif rsi < 30:
                return rsi / 10  # 売られすぎ → 上昇残足
            else:
                return 5.0  # 中立
        
        return 3.0  # デフォルト
    
    def _convert_to_current_timeframe(self, remaining_bars: float, 
                                    previous_bar: MarketData, 
                                    current_bar: MarketData) -> float:
        """
        前足の残足を今足換算に変換
        時間軸の違いを考慮した変換
        """
        # 時間差による調整係数を計算
        time_diff = (current_bar.timestamp - previous_bar.timestamp).total_seconds()
        
        # 標準的な時間足の秒数
        timeframe_seconds = {
            1: 60,      # 1分
            5: 300,     # 5分
            15: 900,    # 15分
            30: 1800,   # 30分
            60: 3600,   # 1時間
            240: 14400  # 4時間
        }
        
        # 現在の時間足を推定
        current_timeframe_seconds = 60  # デフォルト1分
        for tf_minutes, tf_seconds in timeframe_seconds.items():
            if abs(time_diff - tf_seconds) < 30:  # 30秒の誤差許容
                current_timeframe_seconds = tf_seconds
                break
        
        # 変換係数の計算
        conversion_factor = time_diff / current_timeframe_seconds if current_timeframe_seconds > 0 else 1.0
        
        return remaining_bars * conversion_factor
    
    def _analyze_trend_direction(self, market_data: List[MarketData]) -> int:
        """トレンド方向の分析"""
        if len(market_data) < 5:
            return 0
            
        # 短期・中期移動平均による方向判定
        short_period = min(5, len(market_data))
        medium_period = min(10, len(market_data))
        
        short_ma = np.mean([bar.close for bar in market_data[-short_period:]])
        medium_ma = np.mean([bar.close for bar in market_data[-medium_period:]])
        
        if short_ma > medium_ma:
            return 1  # 上昇トレンド
        elif short_ma < medium_ma:
            return -1  # 下降トレンド
        else:
            return 0  # 横ばい
    
    def _check_reverse_direction_overshoot(self, market_data: List[MarketData], 
                                         trend_direction: int) -> bool:
        """
        転換方向と逆方向のオーバーシュート確認
        メモ: 転換方向と逆方向に今足オーバーシュートが成立していないか
        """
        if len(market_data) < 3:
            return False
            
        current_remaining = self._calculate_os_remaining_bars(market_data, -1)
        
        # 現在のオーバーシュート方向を判定
        current_price = market_data[-1].close
        ma_10 = np.mean([bar.close for bar in market_data[-10:]]) if len(market_data) >= 10 else current_price
        
        if current_price > ma_10:
            current_overshoot_direction = 1  # 上方向オーバーシュート
        else:
            current_overshoot_direction = -1  # 下方向オーバーシュート
        
        # トレンド方向と逆方向かチェック
        is_reverse = (trend_direction > 0 and current_overshoot_direction < 0) or \
                    (trend_direction < 0 and current_overshoot_direction > 0)
        
        # オーバーシュート成立かつ逆方向の場合
        return is_reverse and current_remaining >= self.overshoot_threshold
    
    def _calculate_overshoot_direction(self, market_data: List[MarketData], 
                                     overshoot_analysis: Dict) -> int:
        """オーバーシュート方向の計算"""
        if not overshoot_analysis['overshoot_detected']:
            return 0
            
        # 逆方向オーバーシュートの場合は反転シグナル
        if overshoot_analysis['reverse_overshoot']:
            trend_direction = overshoot_analysis['trend_direction']
            return 1 if trend_direction < 0 else 2 if trend_direction > 0 else 0
        
        # 通常のオーバーシュート → 戻り方向
        current_price = market_data[-1].close
        ma_10 = np.mean([bar.close for bar in market_data[-10:]]) if len(market_data) >= 10 else current_price
        
        if current_price > ma_10:
            return 2  # 上オーバーシュート → 下方向
        else:
            return 1  # 下オーバーシュート → 上方向
    
    def _calculate_overshoot_confidence(self, market_data: List[MarketData], 
                                      overshoot_analysis: Dict) -> float:
        """オーバーシュート判定の信頼度計算"""
        if not overshoot_analysis['overshoot_detected']:
            return 0.1
            
        confidence_factors = []
        
        # オーバーシュートの強度
        overshoot_strength = overshoot_analysis['overshoot_strength']
        strength_factor = min(1.0, overshoot_strength / 2.0)  # 2倍以上で最大信頼度
        confidence_factors.append(strength_factor)
        
        # 逆方向オーバーシュートの場合は高信頼度
        if overshoot_analysis['reverse_overshoot']:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.6)
        
        # トレンドの明確さ
        trend_direction = overshoot_analysis['trend_direction']
        trend_clarity = abs(trend_direction)  # -1, 0, 1 → 0, 0, 1
        confidence_factors.append(trend_clarity)
        
        # ボラティリティ考慮
        volatility = self._calculate_volatility(market_data[-10:])
        vol_factor = max(0.3, min(1.0, 1.0 - volatility * 5))  # 高ボラティリティは信頼度下げる
        confidence_factors.append(vol_factor)
        
        return np.mean(confidence_factors)
    
    def _calculate_volatility(self, bars: List[MarketData]) -> float:
        """ボラティリティ計算（再利用）"""
        if len(bars) < 2:
            return 0.0
            
        returns = []
        for i in range(1, len(bars)):
            ret = (bars[i].close - bars[i-1].close) / bars[i-1].close
            returns.append(ret)
            
        return np.std(returns) if returns else 0.0

class TimeKetsugouFunction(BasePKGFunction):
    """
    時間結合PKG関数
    
    メモファイルから抽出した時間結合ロジック:
    - マルチタイムフレーム統合判断
    - 内包関係による統合判断
    - 実行時間目標: 564.9ms
    - 6つの時間足(1M, 5M, 15M, 30M, 1H, 4H)の並列処理
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        self.timeframes = [1, 5, 15, 30, 60, 240]  # 分単位
        
    def execute(self, data: Dict[str, any]) -> OperationSignal:
        """時間結合の実行"""
        if not self.validate_input(data):
            return None
            
        # マルチタイムフレームデータの取得
        multi_tf_data = data.get('multi_timeframe_data', {})
        if not multi_tf_data:
            return None
            
        # 各時間足での分析
        tf_analysis = self._analyze_all_timeframes(multi_tf_data)
        
        # 統合判断
        integration_result = self._integrate_timeframe_signals(tf_analysis)
        
        direction = integration_result['direction']
        confidence = integration_result['confidence']
        
        signal = OperationSignal(
            pkg_id=self.pkg_id,
            signal_type='time_combination',
            direction=direction,
            confidence=confidence,
            timestamp=pd.Timestamp.now(),
            metadata={
                'timeframe_analysis': tf_analysis,
                'integration_result': integration_result,
                'dominant_timeframe': integration_result.get('dominant_timeframe'),
                'consensus_strength': integration_result.get('consensus_strength', 0.0)
            }
        )
        
        return signal
    
    def _analyze_all_timeframes(self, multi_tf_data: Dict) -> Dict:
        """全時間足の分析"""
        tf_analysis = {}
        
        for tf in self.timeframes:
            tf_key = f"{tf}M"
            if tf_key not in multi_tf_data:
                continue
                
            market_data = multi_tf_data[tf_key]
            if not market_data or len(market_data) < 5:
                continue
                
            analysis = {
                'timeframe': tf,
                'trend_direction': self._analyze_trend_direction(market_data),
                'trend_strength': self._calculate_trend_strength(market_data),
                'momentum': self._calculate_momentum(market_data),
                'volatility': self._calculate_volatility(market_data),
                'support_resistance': self._analyze_support_resistance(market_data),
                'heikin_ashi_signal': self._analyze_heikin_ashi_signal(market_data),
                'remaining_bars': self._estimate_remaining_bars(market_data)
            }
            
            tf_analysis[tf] = analysis
            
        return tf_analysis
    
    def _analyze_trend_direction(self, market_data: List[MarketData]) -> int:
        """トレンド方向の分析（改良版）"""
        if len(market_data) < 10:
            return 0
            
        # 複数期間の移動平均による判定
        short_ma = np.mean([bar.close for bar in market_data[-5:]])
        medium_ma = np.mean([bar.close for bar in market_data[-10:]])
        long_ma = np.mean([bar.close for bar in market_data[-20:]]) if len(market_data) >= 20 else medium_ma
        
        # 平均足の方向も考慮
        ha_direction = 0
        if market_data[-1].heikin_ashi_close and market_data[-1].heikin_ashi_open:
            ha_direction = 1 if market_data[-1].heikin_ashi_close > market_data[-1].heikin_ashi_open else -1
        
        # 統合判定
        ma_score = 0
        if short_ma > medium_ma > long_ma:
            ma_score = 2  # 強い上昇
        elif short_ma > medium_ma:
            ma_score = 1  # 弱い上昇
        elif short_ma < medium_ma < long_ma:
            ma_score = -2  # 強い下降
        elif short_ma < medium_ma:
            ma_score = -1  # 弱い下降
        
        # 平均足方向との統合
        if ma_score > 0 and ha_direction > 0:
            return 1  # 上昇
        elif ma_score < 0 and ha_direction < 0:
            return 2  # 下降
        else:
            return 0  # 中立
    
    def _calculate_trend_strength(self, market_data: List[MarketData]) -> float:
        """トレンド強度の計算（改良版）"""
        if len(market_data) < 10:
            return 0.0
            
        closes = [bar.close for bar in market_data[-20:]] if len(market_data) >= 20 else [bar.close for bar in market_data]
        
        # 線形回帰によるトレンド強度
        x = np.arange(len(closes))
        slope, intercept = np.polyfit(x, closes, 1)
        
        # R二乗値でトレンドの強さを評価
        predicted = slope * x + intercept
        r_squared = 1 - (np.sum((closes - predicted) ** 2) / np.sum((closes - np.mean(closes)) ** 2))
        
        return max(0.0, r_squared)
    
    def _calculate_momentum(self, market_data: List[MarketData]) -> float:
        """モメンタムの計算"""
        if len(market_data) < 10:
            return 0.0
            
        # ROC (Rate of Change) による計算
        current_price = market_data[-1].close
        past_price = market_data[-10].close
        
        momentum = (current_price - past_price) / past_price if past_price > 0 else 0.0
        
        return momentum
    
    def _analyze_support_resistance(self, market_data: List[MarketData]) -> Dict:
        """サポート・レジスタンス分析"""
        if len(market_data) < 20:
            return {'support': 0, 'resistance': 0, 'current_position': 0.5}
            
        recent_data = market_data[-20:]
        highs = [bar.high for bar in recent_data]
        lows = [bar.low for bar in recent_data]
        
        resistance = max(highs)
        support = min(lows)
        current_price = market_data[-1].close
        
        # 現在価格の相対位置
        if resistance > support:
            current_position = (current_price - support) / (resistance - support)
        else:
            current_position = 0.5
            
        return {
            'support': support,
            'resistance': resistance,
            'current_position': current_position
        }
    
    def _analyze_heikin_ashi_signal(self, market_data: List[MarketData]) -> Dict:
        """平均足シグナルの分析"""
        if len(market_data) < 3:
            return {'signal': 0, 'consistency': 0.0}
            
        # 最近3足の平均足方向
        recent_bars = market_data[-3:]
        ha_directions = []
        
        for bar in recent_bars:
            if bar.heikin_ashi_close and bar.heikin_ashi_open:
                direction = 1 if bar.heikin_ashi_close > bar.heikin_ashi_open else -1
                ha_directions.append(direction)
        
        if not ha_directions:
            return {'signal': 0, 'consistency': 0.0}
            
        # 一貫性の計算
        consistency = len([d for d in ha_directions if d == ha_directions[0]]) / len(ha_directions)
        
        # 主要シグナル
        signal = ha_directions[-1] if consistency > 0.6 else 0
        
        return {
            'signal': signal,
            'consistency': consistency
        }
    
    def _estimate_remaining_bars(self, market_data: List[MarketData]) -> int:
        """残足の推定"""
        if len(market_data) < 5:
            return 5
            
        # ボラティリティベースの推定
        volatility = self._calculate_volatility(market_data[-10:])
        
        # 高ボラティリティ = 早い転換
        if volatility > 0.02:
            return 2
        elif volatility > 0.01:
            return 4
        else:
            return 6
    
    def _integrate_timeframe_signals(self, tf_analysis: Dict) -> Dict:
        """時間足シグナルの統合"""
        if not tf_analysis:
            return {'direction': 0, 'confidence': 0.0}
            
        # 各時間足の重み（長期ほど重い）
        timeframe_weights = {
            1: 0.1,    # 1分
            5: 0.15,   # 5分
            15: 0.2,   # 15分
            30: 0.25,  # 30分
            60: 0.15,  # 1時間
            240: 0.15  # 4時間
        }
        
        weighted_signals = []
        consensus_count = {'up': 0, 'down': 0, 'neutral': 0}
        
        for tf, analysis in tf_analysis.items():
            weight = timeframe_weights.get(tf, 0.1)
            direction = analysis['trend_direction']
            strength = analysis['trend_strength']
            
            # 重み付きシグナル
            weighted_signal = direction * strength * weight
            weighted_signals.append(weighted_signal)
            
            # コンセンサス計算
            if direction == 1:
                consensus_count['up'] += weight
            elif direction == 2:
                consensus_count['down'] += weight
            else:
                consensus_count['neutral'] += weight
        
        # 統合方向の決定
        total_signal = sum(weighted_signals)
        total_weight = sum(timeframe_weights[tf] for tf in tf_analysis.keys())
        
        if total_weight > 0:
            normalized_signal = total_signal / total_weight
        else:
            normalized_signal = 0
            
        # 最終方向判定
        if normalized_signal > 0.3:
            final_direction = 1  # 上
        elif normalized_signal < -0.3:
            final_direction = 2  # 下
        else:
            final_direction = 0  # 中立
        
        # コンセンサス強度
        max_consensus = max(consensus_count.values())
        consensus_strength = max_consensus / total_weight if total_weight > 0 else 0
        
        # 支配的時間足の特定
        dominant_tf = None
        max_weighted_contribution = 0
        
        for tf, analysis in tf_analysis.items():
            weight = timeframe_weights.get(tf, 0.1)
            contribution = abs(analysis['trend_direction'] * analysis['trend_strength'] * weight)
            
            if contribution > max_weighted_contribution:
                max_weighted_contribution = contribution
                dominant_tf = tf
        
        # 信頼度計算
        confidence_factors = [
            consensus_strength,  # コンセンサスの強さ
            abs(normalized_signal),  # シグナルの強さ
            len(tf_analysis) / len(self.timeframes)  # データ利用可能性
        ]
        
        confidence = np.mean(confidence_factors)
        
        return {
            'direction': final_direction,
            'confidence': confidence,
            'normalized_signal': normalized_signal,
            'consensus_strength': consensus_strength,
            'dominant_timeframe': dominant_tf,
            'consensus_count': consensus_count
        }
    
    def _calculate_volatility(self, bars: List[MarketData]) -> float:
        """ボラティリティ計算（再利用）"""
        if len(bars) < 2:
            return 0.0
            
        returns = []
        for i in range(1, len(bars)):
            ret = (bars[i].close - bars[i-1].close) / bars[i-1].close
            returns.append(ret)
            
        return np.std(returns) if returns else 0.0