"""
Week 6: 専門PKG関数実装
乖離判断、レンジ判定、予知計算等のメモから抽出した専門的なロジック
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging
import math

from .core_pkg_functions import (
    BasePKGFunction, PKGId, MarketData, OperationSignal,
    TimeFrame, Currency, Period
)

class KairiFunction(BasePKGFunction):
    """
    乖離判断PKG関数
    
    メモファイルから抽出した乖離判断ロジック:
    - 前足平均乖離なし/前足実勢乖離なし/今足実勢乖離なし
    - 内包乖離成立/前足平均足乖離/前足実勢乖離/今足実勢乖離
    - 乖離方向に対しての前足T周期増減/前足S周期増減
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        self.kairi_threshold = 0.001  # 乖離閾値（0.1%）
        
    def execute(self, data: Dict[str, any]) -> OperationSignal:
        """乖離判断の実行"""
        if not self.validate_input(data):
            return None
            
        market_data = data.get('market_data', [])
        if len(market_data) < 5:
            return None
            
        # 乖離状態の分析
        kairi_analysis = self._analyze_kairi_conditions(market_data)
        direction = self._calculate_kairi_direction(market_data, kairi_analysis)
        confidence = self._calculate_kairi_confidence(market_data, kairi_analysis)
        
        signal = OperationSignal(
            pkg_id=self.pkg_id,
            signal_type='kairi',
            direction=direction,
            confidence=confidence,
            timestamp=market_data[-1].timestamp,
            metadata={
                'kairi_analysis': kairi_analysis,
                'deviation_types': kairi_analysis.get('deviation_types', {}),
                'period_changes': kairi_analysis.get('period_changes', {})
            }
        )
        
        return signal
    
    def _analyze_kairi_conditions(self, market_data: List[MarketData]) -> Dict:
        """
        乖離条件の分析
        メモ: 前足平均乖離なし/前足実勢乖離なし/今足実勢乖離なし
        """
        if len(market_data) < 3:
            return {'kairi_detected': False}
            
        current_bar = market_data[-1]
        prev_bar = market_data[-2]
        
        # 各種乖離の計算
        deviation_types = {
            'prev_heikin_ashi_deviation': self._calculate_heikin_ashi_deviation(prev_bar),
            'prev_real_deviation': self._calculate_real_price_deviation(prev_bar, market_data),
            'current_real_deviation': self._calculate_real_price_deviation(current_bar, market_data),
            'containment_deviation': self._calculate_containment_deviation(market_data)
        }
        
        # 周期増減の分析
        period_changes = self._analyze_period_changes(market_data)
        
        # 乖離成立条件の評価
        kairi_conditions = self._evaluate_kairi_conditions(deviation_types, period_changes)
        
        return {
            'kairi_detected': kairi_conditions['established'],
            'deviation_types': deviation_types,
            'period_changes': period_changes,
            'kairi_conditions': kairi_conditions,
            'deviation_strength': self._calculate_deviation_strength(deviation_types),
            'trend_consistency': self._check_trend_consistency(market_data)
        }
    
    def _calculate_heikin_ashi_deviation(self, bar: MarketData) -> float:
        """平均足乖離の計算"""
        if bar.heikin_ashi_close is None or bar.heikin_ashi_open is None:
            return 0.0
            
        # 平均足の実体と終値の乖離
        ha_body_center = (bar.heikin_ashi_open + bar.heikin_ashi_close) / 2
        deviation = (bar.close - ha_body_center) / ha_body_center if ha_body_center > 0 else 0.0
        
        return deviation
    
    def _calculate_real_price_deviation(self, bar: MarketData, 
                                      market_data: List[MarketData]) -> float:
        """実勢価格乖離の計算"""
        # 直近の移動平均からの乖離
        if len(market_data) >= 10:
            recent_closes = [b.close for b in market_data[-10:]]
            ma_10 = np.mean(recent_closes)
            deviation = (bar.close - ma_10) / ma_10 if ma_10 > 0 else 0.0
        else:
            deviation = 0.0
            
        return deviation
    
    def _calculate_containment_deviation(self, market_data: List[MarketData]) -> float:
        """
        内包乖離の計算
        メモ: 内包乖離成立
        """
        if len(market_data) < 5:
            return 0.0
            
        # 時間足の内包関係における乖離
        current_tf_data = market_data[-5:]  # 現在時間足の直近5足
        
        # より大きな時間足の推定値を計算
        longer_tf_close = np.mean([bar.close for bar in current_tf_data])
        current_close = current_tf_data[-1].close
        
        # 内包乖離
        containment_deviation = (current_close - longer_tf_close) / longer_tf_close if longer_tf_close > 0 else 0.0
        
        return containment_deviation
    
    def _analyze_period_changes(self, market_data: List[MarketData]) -> Dict:
        """
        周期増減の分析
        メモ: 乖離方向に対しての前足T周期増減/前足S周期増減
        """
        if len(market_data) < 15:
            return {'t_period_change': 0, 's_period_change': 0}
            
        # T周期（中期）とS周期（短期）の計算
        t_period = 10  # T周期
        s_period = 5   # S周期
        
        # 前足における各周期の変化
        prev_t_values = [bar.close for bar in market_data[-t_period-1:-1]]
        curr_t_values = [bar.close for bar in market_data[-t_period:]]
        
        prev_s_values = [bar.close for bar in market_data[-s_period-1:-1]]
        curr_s_values = [bar.close for bar in market_data[-s_period:]]
        
        # 各周期の増減計算
        prev_t_avg = np.mean(prev_t_values)
        curr_t_avg = np.mean(curr_t_values)
        t_change = (curr_t_avg - prev_t_avg) / prev_t_avg if prev_t_avg > 0 else 0.0
        
        prev_s_avg = np.mean(prev_s_values)
        curr_s_avg = np.mean(curr_s_values)
        s_change = (curr_s_avg - prev_s_avg) / prev_s_avg if prev_s_avg > 0 else 0.0
        
        return {
            't_period_change': t_change,
            's_period_change': s_change,
            't_period_direction': 1 if t_change > 0 else -1 if t_change < 0 else 0,
            's_period_direction': 1 if s_change > 0 else -1 if s_change < 0 else 0
        }
    
    def _evaluate_kairi_conditions(self, deviation_types: Dict, 
                                 period_changes: Dict) -> Dict:
        """乖離成立条件の評価"""
        conditions = {
            'prev_ha_no_deviation': abs(deviation_types['prev_heikin_ashi_deviation']) < self.kairi_threshold,
            'prev_real_no_deviation': abs(deviation_types['prev_real_deviation']) < self.kairi_threshold,
            'current_real_no_deviation': abs(deviation_types['current_real_deviation']) < self.kairi_threshold,
            'containment_deviation_exists': abs(deviation_types['containment_deviation']) > self.kairi_threshold
        }
        
        # 基本条件: 乖離なし状態
        basic_condition = (conditions['prev_ha_no_deviation'] and 
                          conditions['prev_real_no_deviation'] and 
                          conditions['current_real_no_deviation'])
        
        # イレギュラー条件: 乖離あり状態
        irregular_condition = conditions['containment_deviation_exists']
        
        # 周期条件: 周期の方向一致
        period_alignment = (period_changes['t_period_direction'] == period_changes['s_period_direction'] and
                          period_changes['t_period_direction'] != 0)
        
        # 統合判定
        established = basic_condition or (irregular_condition and period_alignment)
        
        return {
            'established': established,
            'basic_condition': basic_condition,
            'irregular_condition': irregular_condition,
            'period_alignment': period_alignment,
            'conditions_detail': conditions
        }
    
    def _calculate_deviation_strength(self, deviation_types: Dict) -> float:
        """乖離強度の計算"""
        deviations = [abs(v) for v in deviation_types.values()]
        return np.mean(deviations) if deviations else 0.0
    
    def _check_trend_consistency(self, market_data: List[MarketData]) -> float:
        """トレンド一貫性のチェック"""
        if len(market_data) < 5:
            return 0.0
            
        # 直近5足のトレンド方向の一貫性
        directions = []
        for i in range(1, min(6, len(market_data))):
            if market_data[-i].close > market_data[-i-1].close:
                directions.append(1)
            else:
                directions.append(-1)
        
        # 一貫性スコア
        if not directions:
            return 0.0
            
        most_common_direction = max(set(directions), key=directions.count)
        consistency = directions.count(most_common_direction) / len(directions)
        
        return consistency
    
    def _calculate_kairi_direction(self, market_data: List[MarketData], 
                                 kairi_analysis: Dict) -> int:
        """乖離方向の計算"""
        if not kairi_analysis['kairi_detected']:
            return 0
            
        # 主要な乖離方向を特定
        deviation_types = kairi_analysis['deviation_types']
        period_changes = kairi_analysis['period_changes']
        
        # 内包乖離が主要な場合
        if abs(deviation_types['containment_deviation']) > self.kairi_threshold:
            return 1 if deviation_types['containment_deviation'] > 0 else 2
        
        # 周期変化による方向判定
        if period_changes['t_period_direction'] == period_changes['s_period_direction']:
            return 1 if period_changes['t_period_direction'] > 0 else 2
        
        # デフォルト: 最新の価格トレンド
        if len(market_data) >= 2:
            if market_data[-1].close > market_data[-2].close:
                return 1
            else:
                return 2
                
        return 0
    
    def _calculate_kairi_confidence(self, market_data: List[MarketData], 
                                  kairi_analysis: Dict) -> float:
        """乖離判定の信頼度計算"""
        if not kairi_analysis['kairi_detected']:
            return 0.1
            
        confidence_factors = []
        
        # 乖離強度
        deviation_strength = kairi_analysis['deviation_strength']
        strength_factor = min(1.0, deviation_strength * 100)  # 0.01 = 1% で最大
        confidence_factors.append(strength_factor)
        
        # トレンド一貫性
        trend_consistency = kairi_analysis['trend_consistency']
        confidence_factors.append(trend_consistency)
        
        # 条件成立の明確さ
        kairi_conditions = kairi_analysis['kairi_conditions']
        if kairi_conditions['basic_condition']:
            confidence_factors.append(0.8)  # 基本条件は高信頼度
        elif kairi_conditions['irregular_condition'] and kairi_conditions['period_alignment']:
            confidence_factors.append(0.7)  # イレギュラーでも周期一致なら中信頼度
        else:
            confidence_factors.append(0.4)  # その他は低信頼度
        
        # 周期変化の一致性
        period_changes = kairi_analysis['period_changes']
        if period_changes['t_period_direction'] == period_changes['s_period_direction'] and period_changes['t_period_direction'] != 0:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.5)
        
        return np.mean(confidence_factors)

class RangeFunction(BasePKGFunction):
    """
    レンジ判定PKG関数
    
    メモファイルから抽出したレンジ判定ロジック:
    - 軸周期を決める → それよりも短い線が全て片側に抜けているか確認
    - 価格が軸周期の線と反対側にどの周期の線がいるか
    - レンジ: 180-90、90-30、30-10等の動的判定
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        self.periods = [10, 30, 90, 180]  # 主要周期
        
    def execute(self, data: Dict[str, any]) -> OperationSignal:
        """レンジ判定の実行"""
        if not self.validate_input(data):
            return None
            
        market_data = data.get('market_data', [])
        if len(market_data) < 180:  # 最長周期分のデータが必要
            return None
            
        # レンジ分析
        range_analysis = self._analyze_range_structure(market_data)
        direction = self._calculate_range_direction(market_data, range_analysis)
        confidence = self._calculate_range_confidence(market_data, range_analysis)
        
        signal = OperationSignal(
            pkg_id=self.pkg_id,
            signal_type='range',
            direction=direction,
            confidence=confidence,
            timestamp=market_data[-1].timestamp,
            metadata={
                'range_analysis': range_analysis,
                'axis_period': range_analysis.get('axis_period'),
                'range_type': range_analysis.get('range_type'),
                'breakout_potential': range_analysis.get('breakout_potential', 0.0)
            }
        )
        
        return signal
    
    def _analyze_range_structure(self, market_data: List[MarketData]) -> Dict:
        """
        レンジ構造の分析
        メモ: 軸周期を決める → それよりも短い線が全て片側に抜けているか確認
        """
        current_price = market_data[-1].close
        
        # 各周期の移動平均を計算
        period_mas = {}
        for period in self.periods:
            if len(market_data) >= period:
                closes = [bar.close for bar in market_data[-period:]]
                period_mas[period] = np.mean(closes)
        
        # 軸周期の決定
        axis_period = self._determine_axis_period(current_price, period_mas)
        
        # 価格と各移動平均の位置関係
        price_positions = self._analyze_price_positions(current_price, period_mas)
        
        # レンジタイプの判定
        range_type = self._determine_range_type(current_price, period_mas, axis_period)
        
        # レンジ幅の計算
        range_width = self._calculate_range_width(market_data, range_type)
        
        # ブレイクアウト可能性
        breakout_potential = self._calculate_breakout_potential(market_data, range_type)
        
        return {
            'axis_period': axis_period,
            'period_mas': period_mas,
            'price_positions': price_positions,
            'range_type': range_type,
            'range_width': range_width,
            'breakout_potential': breakout_potential,
            'is_in_range': range_type != 'no_range'
        }
    
    def _determine_axis_period(self, current_price: float, period_mas: Dict) -> int:
        """
        軸周期の決定
        メモ: 価格に最も近い移動平均の周期を軸とする
        """
        if not period_mas:
            return 180  # デフォルト
            
        min_distance = float('inf')
        axis_period = 180
        
        for period, ma_value in period_mas.items():
            distance = abs(current_price - ma_value)
            if distance < min_distance:
                min_distance = distance
                axis_period = period
                
        return axis_period
    
    def _analyze_price_positions(self, current_price: float, period_mas: Dict) -> Dict:
        """価格と各移動平均の位置関係分析"""
        positions = {}
        
        for period, ma_value in period_mas.items():
            if current_price > ma_value:
                positions[period] = 'above'
            elif current_price < ma_value:
                positions[period] = 'below'
            else:
                positions[period] = 'on'
                
        return positions
    
    def _determine_range_type(self, current_price: float, period_mas: Dict, 
                            axis_period: int) -> str:
        """
        レンジタイプの判定
        メモ: 180に対して上にいる場合の分岐ロジック
        """
        if not period_mas or 180 not in period_mas:
            return 'no_range'
            
        ma_180 = period_mas[180]
        
        # 180に対する価格位置
        if current_price > ma_180:
            return self._analyze_upper_range(current_price, period_mas)
        else:
            return self._analyze_lower_range(current_price, period_mas)
    
    def _analyze_upper_range(self, current_price: float, period_mas: Dict) -> str:
        """
        180より上の価格の場合のレンジ分析
        メモファイルの上側分析ロジック
        """
        ma_180 = period_mas.get(180, current_price)
        ma_90 = period_mas.get(90, current_price)
        ma_30 = period_mas.get(30, current_price)
        ma_10 = period_mas.get(10, current_price)
        
        # 180-90の間にいる場合
        if ma_90 <= current_price <= ma_180 or ma_180 <= current_price <= ma_90:
            return '180-90_range'
            
        # 90が180の上の場合
        if ma_90 > ma_180:
            # 90-30の間にいる場合
            if ma_30 <= current_price <= ma_90 or ma_90 <= current_price <= ma_30:
                return '90-30_range'
            # 30が180の上の場合
            elif ma_30 > ma_180:
                # 30-10の間にいる場合
                if ma_10 <= current_price <= ma_30 or ma_30 <= current_price <= ma_10:
                    return '30-10_range'
                else:
                    return 'no_range'
            # 30が180の下の場合
            else:
                # 90-10の間にいる場合
                if ma_10 <= current_price <= ma_90 or ma_90 <= current_price <= ma_10:
                    return '90-10_range'
                else:
                    return 'no_range'
        # 90が180の下の場合
        else:
            # 180-30の間にいる場合
            if ma_30 <= current_price <= ma_180 or ma_180 <= current_price <= ma_30:
                return '180-30_range'
            else:
                return self._analyze_complex_range(current_price, ma_180, ma_30, ma_10)
    
    def _analyze_lower_range(self, current_price: float, period_mas: Dict) -> str:
        """180より下の価格の場合のレンジ分析"""
        # 下側のロジックは上側の鏡像
        ma_180 = period_mas.get(180, current_price)
        ma_90 = period_mas.get(90, current_price)
        ma_30 = period_mas.get(30, current_price)
        ma_10 = period_mas.get(10, current_price)
        
        # 基本的には上側と同じロジックを下向きに適用
        if ma_90 >= current_price >= ma_180 or ma_180 >= current_price >= ma_90:
            return '180-90_range'
        elif ma_30 >= current_price >= ma_90 or ma_90 >= current_price >= ma_30:
            return '90-30_range'
        elif ma_10 >= current_price >= ma_30 or ma_30 >= current_price >= ma_10:
            return '30-10_range'
        else:
            return 'no_range'
    
    def _analyze_complex_range(self, current_price: float, ma_180: float, 
                             ma_30: float, ma_10: float) -> str:
        """複雑なレンジ状況の分析"""
        # 30が180の上の場合
        if ma_30 > ma_180:
            if ma_10 <= current_price <= ma_30 or ma_30 <= current_price <= ma_10:
                return '30-10_range'
            else:
                return 'no_range'
        # 30が180の下の場合
        else:
            if ma_10 <= current_price <= ma_180 or ma_180 <= current_price <= ma_10:
                return '10-180_range'
            else:
                return 'no_range'
    
    def _calculate_range_width(self, market_data: List[MarketData], 
                             range_type: str) -> float:
        """レンジ幅の計算"""
        if range_type == 'no_range':
            return 0.0
            
        # 直近20足のレンジ幅
        recent_data = market_data[-20:] if len(market_data) >= 20 else market_data
        highs = [bar.high for bar in recent_data]
        lows = [bar.low for bar in recent_data]
        
        range_width = (max(highs) - min(lows)) * 100  # pips換算
        return range_width
    
    def _calculate_breakout_potential(self, market_data: List[MarketData], 
                                    range_type: str) -> float:
        """ブレイクアウト可能性の計算"""
        if range_type == 'no_range':
            return 0.0
            
        # ボリューム分析
        recent_volumes = [bar.volume for bar in market_data[-10:]] if len(market_data) >= 10 else []
        baseline_volumes = [bar.volume for bar in market_data[-20:-10]] if len(market_data) >= 20 else recent_volumes
        
        if not recent_volumes or not baseline_volumes:
            return 0.0
            
        volume_ratio = np.mean(recent_volumes) / np.mean(baseline_volumes)
        
        # ボラティリティ分析
        volatility = self._calculate_volatility(market_data[-20:])
        
        # 統合スコア
        breakout_score = min(1.0, (volume_ratio - 1.0) + volatility * 10)
        return max(0.0, breakout_score)
    
    def _calculate_range_direction(self, market_data: List[MarketData], 
                                 range_analysis: Dict) -> int:
        """レンジ方向の計算"""
        if not range_analysis['is_in_range']:
            return 0
            
        current_price = market_data[-1].close
        range_type = range_analysis['range_type']
        period_mas = range_analysis['period_mas']
        
        # レンジタイプに基づく方向判定
        if '180-90' in range_type:
            center = (period_mas.get(180, current_price) + period_mas.get(90, current_price)) / 2
        elif '90-30' in range_type:
            center = (period_mas.get(90, current_price) + period_mas.get(30, current_price)) / 2
        elif '30-10' in range_type:
            center = (period_mas.get(30, current_price) + period_mas.get(10, current_price)) / 2
        else:
            center = period_mas.get(180, current_price)
        
        # レンジ中心からの位置で方向判定
        if current_price > center:
            return 2  # レンジ上部 → 下方向期待
        else:
            return 1  # レンジ下部 → 上方向期待
    
    def _calculate_range_confidence(self, market_data: List[MarketData], 
                                  range_analysis: Dict) -> float:
        """レンジ判定の信頼度計算"""
        if not range_analysis['is_in_range']:
            return 0.1
            
        confidence_factors = []
        
        # レンジの明確さ
        range_width = range_analysis['range_width']
        if range_width > 5:  # 5pips以上
            confidence_factors.append(0.8)
        elif range_width > 2:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.4)
        
        # ブレイクアウト可能性（低いほど安定したレンジ）
        breakout_potential = range_analysis['breakout_potential']
        stability_factor = max(0.3, 1.0 - breakout_potential)
        confidence_factors.append(stability_factor)
        
        # 移動平均の配置の明確さ
        period_mas = range_analysis['period_mas']
        if len(period_mas) >= 3:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.5)
        
        # 時間要素（レンジが長期間続いているか）
        consolidation_time = self._estimate_consolidation_time(market_data)
        time_factor = min(1.0, consolidation_time / 30.0)  # 30足以上で最大
        confidence_factors.append(time_factor)
        
        return np.mean(confidence_factors)
    
    def _estimate_consolidation_time(self, market_data: List[MarketData]) -> int:
        """もみ合い期間の推定"""
        if len(market_data) < 10:
            return len(market_data)
            
        # 大きな価格変動を探して、それ以降の期間を返す
        threshold = 0.005  # 0.5%の変動
        
        for i in range(len(market_data) - 1, 0, -1):
            price_change = abs(market_data[i].close - market_data[i-1].close) / market_data[i-1].close
            if price_change > threshold:
                return len(market_data) - i
                
        return len(market_data)
    
    def _calculate_volatility(self, bars: List[MarketData]) -> float:
        """ボラティリティ計算（再利用）"""
        if len(bars) < 2:
            return 0.0
            
        returns = []
        for i in range(1, len(bars)):
            ret = (bars[i].close - bars[i-1].close) / bars[i-1].close
            returns.append(ret)
            
        return np.std(returns) if returns else 0.0

class YochiFunction(BasePKGFunction):
    """
    予知計算PKG関数
    
    メモファイルから抽出した予知計算ロジック:
    - 今＞先、今予知＞今 ⇒ 上
    - 今＞先、今予知＜今、今予知＞先、先予知＞先 ⇒ 上（多段）
    - 今＞先、今予知＜今、今予知＞先、先予知＜先 ⇒ 下（伸びる）
    - 今＞先、今予知＜今、今予知＜先 ⇒ 下（内包予知）
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        
    def execute(self, data: Dict[str, any]) -> OperationSignal:
        """予知計算の実行"""
        if not self.validate_input(data):
            return None
            
        market_data = data.get('market_data', [])
        if len(market_data) < 5:
            return None
            
        # 予知計算
        yochi_analysis = self._calculate_yochi_patterns(market_data)
        direction = self._determine_yochi_direction(yochi_analysis)
        confidence = self._calculate_yochi_confidence(market_data, yochi_analysis)
        
        signal = OperationSignal(
            pkg_id=self.pkg_id,
            signal_type='yochi',
            direction=direction,
            confidence=confidence,
            timestamp=market_data[-1].timestamp,
            metadata={
                'yochi_analysis': yochi_analysis,
                'pattern_type': yochi_analysis.get('pattern_type'),
                'prediction_strength': yochi_analysis.get('prediction_strength', 0.0)
            }
        )
        
        return signal
    
    def _calculate_yochi_patterns(self, market_data: List[MarketData]) -> Dict:
        """
        予知パターンの計算
        メモ: 今＞先、今予知＞今等の条件分岐
        """
        if len(market_data) < 3:
            return {'pattern_type': 'insufficient_data'}
            
        current_bar = market_data[-1]  # 今
        prev_bar = market_data[-2]     # 先
        
        # 予知価格の計算
        current_yochi = self._calculate_yochi_price(market_data, -1)  # 今予知
        prev_yochi = self._calculate_yochi_price(market_data, -2)     # 先予知
        
        current_price = current_bar.close  # 今
        prev_price = prev_bar.close        # 先
        
        # パターン判定のための条件
        conditions = {
            'current_vs_prev': current_price > prev_price,  # 今＞先
            'current_yochi_vs_current': current_yochi > current_price,  # 今予知＞今
            'current_yochi_vs_prev': current_yochi > prev_price,        # 今予知＞先
            'prev_yochi_vs_prev': prev_yochi > prev_price               # 先予知＞先
        }
        
        # パターン分類
        pattern_type = self._classify_yochi_pattern(conditions)
        
        # 予測強度の計算
        prediction_strength = self._calculate_prediction_strength(
            current_price, prev_price, current_yochi, prev_yochi
        )
        
        return {
            'pattern_type': pattern_type,
            'conditions': conditions,
            'current_price': current_price,
            'prev_price': prev_price,
            'current_yochi': current_yochi,
            'prev_yochi': prev_yochi,
            'prediction_strength': prediction_strength
        }
    
    def _calculate_yochi_price(self, market_data: List[MarketData], 
                             bar_index: int) -> float:
        """
        予知価格の計算
        平均足とオシレーターを組み合わせた予測価格
        """
        if abs(bar_index) > len(market_data):
            return 0.0
            
        target_bar = market_data[bar_index]
        
        # 平均足ベースの予知価格
        if target_bar.heikin_ashi_close and target_bar.heikin_ashi_open:
            ha_momentum = target_bar.heikin_ashi_close - target_bar.heikin_ashi_open
            ha_yochi = target_bar.heikin_ashi_close + ha_momentum * 0.5
        else:
            ha_yochi = target_bar.close
        
        # 移動平均ベースの予知価格
        if len(market_data) >= abs(bar_index) + 5:
            recent_closes = [bar.close for bar in market_data[bar_index-4:bar_index+1]]
            ma_trend = (recent_closes[-1] - recent_closes[0]) / len(recent_closes)
            ma_yochi = target_bar.close + ma_trend
        else:
            ma_yochi = target_bar.close
        
        # オシレーターベースの予知価格
        os_yochi = self._calculate_oscillator_yochi(market_data, bar_index)
        
        # 統合予知価格
        yochi_price = (ha_yochi * 0.4 + ma_yochi * 0.3 + os_yochi * 0.3)
        
        return yochi_price
    
    def _calculate_oscillator_yochi(self, market_data: List[MarketData], 
                                  bar_index: int) -> float:
        """オシレーターベースの予知価格計算"""
        if abs(bar_index) > len(market_data) or len(market_data) < 14:
            return market_data[bar_index].close
            
        # RSIライクな計算で方向性を判定
        end_idx = len(market_data) + bar_index if bar_index < 0 else bar_index + 1
        start_idx = max(0, end_idx - 14)
        
        recent_closes = [bar.close for bar in market_data[start_idx:end_idx]]
        
        if len(recent_closes) < 2:
            return market_data[bar_index].close
            
        price_changes = []
        for i in range(1, len(recent_closes)):
            change = recent_closes[i] - recent_closes[i-1]
            price_changes.append(change)
        
        gains = [change for change in price_changes if change > 0]
        losses = [-change for change in price_changes if change < 0]
        
        avg_gain = np.mean(gains) if gains else 0
        avg_loss = np.mean(losses) if losses else 0
        
        # 次の動きの予測
        if avg_gain > avg_loss:
            momentum = avg_gain * 0.5
        else:
            momentum = -avg_loss * 0.5
            
        return market_data[bar_index].close + momentum
    
    def _classify_yochi_pattern(self, conditions: Dict) -> str:
        """
        予知パターンの分類
        メモファイルの条件分岐ロジック
        """
        c_vs_p = conditions['current_vs_prev']         # 今＞先
        cy_vs_c = conditions['current_yochi_vs_current'] # 今予知＞今
        cy_vs_p = conditions['current_yochi_vs_prev']   # 今予知＞先
        py_vs_p = conditions['prev_yochi_vs_prev']      # 先予知＞先
        
        if c_vs_p:  # 今＞先
            if cy_vs_c:  # 今予知＞今
                return 'up_simple'  # ⇒ 上
            elif not cy_vs_c:  # 今予知＜今
                if cy_vs_p:  # 今予知＞先
                    if py_vs_p:  # 先予知＞先
                        return 'up_multi_stage'  # ⇒ 上（多段）
                    else:  # 先予知＜先
                        return 'down_extend'  # ⇒ 下（伸びる）
                else:  # 今予知＜先
                    return 'down_containment'  # ⇒ 下（内包予知）
        else:  # 今＜先（鏡像パターン）
            if not cy_vs_c:  # 今予知＜今
                return 'down_simple'  # ⇒ 下
            elif cy_vs_c:  # 今予知＞今
                if not cy_vs_p:  # 今予知＜先
                    if not py_vs_p:  # 先予知＜先
                        return 'down_multi_stage'  # ⇒ 下（多段）
                    else:  # 先予知＞先
                        return 'up_extend'  # ⇒ 上（伸びる）
                else:  # 今予知＞先
                    return 'up_containment'  # ⇒ 上（内包予知）
        
        return 'neutral'
    
    def _calculate_prediction_strength(self, current_price: float, prev_price: float,
                                     current_yochi: float, prev_yochi: float) -> float:
        """予測強度の計算"""
        # 価格変化の大きさ
        price_change = abs(current_price - prev_price) / prev_price if prev_price > 0 else 0
        
        # 予知価格の乖離の大きさ
        current_yochi_deviation = abs(current_yochi - current_price) / current_price if current_price > 0 else 0
        prev_yochi_deviation = abs(prev_yochi - prev_price) / prev_price if prev_price > 0 else 0
        
        # 予測の一貫性
        yochi_consistency = 1.0 - abs((current_yochi - current_price) - (prev_yochi - prev_price)) / current_price if current_price > 0 else 0
        
        # 統合強度
        strength_factors = [
            min(1.0, price_change * 100),  # 価格変化（100倍でスケーリング）
            min(1.0, current_yochi_deviation * 50),  # 予知乖離
            max(0.0, yochi_consistency)  # 一貫性
        ]
        
        return np.mean(strength_factors)
    
    def _determine_yochi_direction(self, yochi_analysis: Dict) -> int:
        """予知方向の決定"""
        pattern_type = yochi_analysis.get('pattern_type', 'neutral')
        
        direction_map = {
            'up_simple': 1,
            'up_multi_stage': 1,
            'up_extend': 1,
            'up_containment': 1,
            'down_simple': 2,
            'down_multi_stage': 2,
            'down_extend': 2,
            'down_containment': 2,
            'neutral': 0,
            'insufficient_data': 0
        }
        
        return direction_map.get(pattern_type, 0)
    
    def _calculate_yochi_confidence(self, market_data: List[MarketData], 
                                  yochi_analysis: Dict) -> float:
        """予知計算の信頼度"""
        pattern_type = yochi_analysis.get('pattern_type', 'neutral')
        
        if pattern_type in ['insufficient_data', 'neutral']:
            return 0.1
            
        confidence_factors = []
        
        # パターンタイプ別の基本信頼度
        pattern_confidence = {
            'up_simple': 0.8,
            'down_simple': 0.8,
            'up_multi_stage': 0.7,
            'down_multi_stage': 0.7,
            'up_extend': 0.6,
            'down_extend': 0.6,
            'up_containment': 0.5,
            'down_containment': 0.5
        }
        
        base_confidence = pattern_confidence.get(pattern_type, 0.3)
        confidence_factors.append(base_confidence)
        
        # 予測強度
        prediction_strength = yochi_analysis.get('prediction_strength', 0.0)
        confidence_factors.append(prediction_strength)
        
        # 市場状況の安定性
        volatility = self._calculate_volatility(market_data[-10:])
        stability_factor = max(0.3, 1.0 - volatility * 5)
        confidence_factors.append(stability_factor)
        
        # データの十分性
        data_sufficiency = min(1.0, len(market_data) / 20.0)
        confidence_factors.append(data_sufficiency)
        
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