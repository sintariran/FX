"""
Week 6: PKG関数ロジック実装 - コアPKG関数
97個のメモファイルから抽出した核心的なトレーディングロジックを
関数型DAGアーキテクチャで実装

メモファイル分析結果:
- 同逆判定（Dokyaku）: 前々足乖離による方向判断、勝率55.7%～56.1%
- 行帰判定（Ikikaeri）: 前足の動きから今足の方向予測
- もみ判定: レンジ相場とブレイクアウト検出
- オーバーシュート判定: 残足による転換予測
- 時間結合: マルチタイムフレーム統合判断
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
import logging
from dataclasses import dataclass
import math

# PKG ID体系の定義
class TimeFrame(Enum):
    """時間足定義"""
    M1 = 1   # 1分足
    M5 = 2   # 5分足
    M15 = 3  # 15分足
    M30 = 4  # 30分足
    H1 = 5   # 1時間足
    H4 = 6   # 4時間足

class Currency(Enum):
    """通貨ペア定義"""
    USDJPY = 1
    EURUSD = 2
    EURJPY = 3

class Period(Enum):
    """周期定義（TSML周期）"""
    COMMON = 9    # 共通（周期なし）
    PERIOD_10 = 10
    PERIOD_15 = 15
    PERIOD_30 = 30
    PERIOD_45 = 45
    PERIOD_60 = 60
    PERIOD_90 = 90
    PERIOD_180 = 180

@dataclass
class PKGId:
    """PKG ID体系: [時間足][周期][通貨]^[階層]-[連番]"""
    timeframe: TimeFrame
    period: Period
    currency: Currency
    layer: int
    sequence: int
    
    def __str__(self) -> str:
        return f"{self.timeframe.value}{self.period.value:02d}{self.currency.value}^{self.layer}-{self.sequence}"
    
    @classmethod
    def parse(cls, pkg_id_str: str) -> 'PKGId':
        """PKG ID文字列をパース"""
        try:
            base, layer_seq = pkg_id_str.split('^')
            layer, sequence = layer_seq.split('-')
            
            timeframe = TimeFrame(int(base[0]))
            period = Period(int(base[1:3]))
            currency = Currency(int(base[3]))
            
            return cls(timeframe, period, currency, int(layer), int(sequence))
        except Exception as e:
            raise ValueError(f"Invalid PKG ID format: {pkg_id_str}") from e

@dataclass
class MarketData:
    """市場データ構造"""
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float
    heikin_ashi_open: Optional[float] = None
    heikin_ashi_high: Optional[float] = None
    heikin_ashi_low: Optional[float] = None
    heikin_ashi_close: Optional[float] = None

@dataclass
class OperationSignal:
    """オペレーション信号"""
    pkg_id: PKGId
    signal_type: str  # 'dokyaku', 'ikikaeri', 'momi', 'overshoot', 'time_combination'
    direction: int    # 1=上, 2=下, 0=中立
    confidence: float  # 信頼度 0.0-1.0
    timestamp: pd.Timestamp
    metadata: Dict = None

class BasePKGFunction:
    """PKG関数の基底クラス"""
    
    def __init__(self, pkg_id: PKGId):
        self.pkg_id = pkg_id
        self.logger = logging.getLogger(f"PKG_{pkg_id}")
        self.cache = {}
        
    def execute(self, data: Dict[str, any]) -> any:
        """PKG関数実行（サブクラスで実装）"""
        raise NotImplementedError("Subclasses must implement execute method")
    
    def validate_input(self, data: Dict[str, any]) -> bool:
        """入力データの検証"""
        return True
    
    def get_cache_key(self, data: Dict[str, any]) -> str:
        """キャッシュキーの生成"""
        return str(hash(str(data)))

class DokyakuFunction(BasePKGFunction):
    """
    同逆判定PKG関数
    
    メモファイルから抽出した同逆判定ロジック:
    - 前々足乖離による方向判断
    - MHIH/MJIH、MMHMH/MMJMHの方向一致性評価
    - 勝率: 55.7%～56.1%
    - 平均足の転換確定と基準線交点のタイミング評価
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        self.performance_stats = {
            'win_rate': 0.557,  # メモより抽出
            'total_signals': 0,
            'correct_signals': 0
        }
    
    def execute(self, data: Dict[str, any]) -> OperationSignal:
        """同逆判定の実行"""
        if not self.validate_input(data):
            return None
            
        market_data = data.get('market_data', [])
        if len(market_data) < 3:
            return None
            
        # 前々足、前足、今足の取得
        current_bar = market_data[-1]
        prev_bar = market_data[-2]
        prev_prev_bar = market_data[-3]
        
        # 同逆判定の核心ロジック
        direction = self._calculate_dokyaku_direction(
            prev_prev_bar, prev_bar, current_bar
        )
        
        confidence = self._calculate_confidence(
            prev_prev_bar, prev_bar, current_bar
        )
        
        signal = OperationSignal(
            pkg_id=self.pkg_id,
            signal_type='dokyaku',
            direction=direction,
            confidence=confidence,
            timestamp=current_bar.timestamp,
            metadata={
                'prev_prev_deviation': self._calculate_deviation(prev_prev_bar),
                'heikin_ashi_consistency': self._check_heikin_ashi_consistency(market_data[-5:]),
                'baseline_cross_timing': self._check_baseline_cross_timing(market_data[-3:])
            }
        )
        
        self._update_performance_stats(signal)
        return signal
    
    def _calculate_dokyaku_direction(self, prev_prev: MarketData, 
                                   prev: MarketData, current: MarketData) -> int:
        """
        同逆方向の計算
        メモ: 前々足乖離による方向判断
        """
        # 前々足の乖離状態を評価
        prev_prev_deviation = self._calculate_deviation(prev_prev)
        
        # 平均足の方向一致性をチェック
        ha_consistency = self._check_heikin_ashi_direction_consistency([prev_prev, prev, current])
        
        # MHIH/MJIH指標の方向評価
        direction_indicators = self._evaluate_direction_indicators([prev_prev, prev, current])
        
        # 統合判断
        if prev_prev_deviation > 0.5 and ha_consistency and direction_indicators > 0:
            return 1  # 上方向
        elif prev_prev_deviation < -0.5 and ha_consistency and direction_indicators < 0:
            return 2  # 下方向
        else:
            return 0  # 中立
    
    def _calculate_deviation(self, bar: MarketData) -> float:
        """乖離の計算"""
        if bar.heikin_ashi_close is None:
            return 0.0
        
        # 実勢価格と平均足の乖離
        deviation = (bar.close - bar.heikin_ashi_close) / bar.heikin_ashi_close
        return deviation
    
    def _check_heikin_ashi_consistency(self, bars: List[MarketData]) -> bool:
        """平均足の方向一致性チェック"""
        if len(bars) < 3:
            return False
            
        directions = []
        for bar in bars:
            if bar.heikin_ashi_open is not None and bar.heikin_ashi_close is not None:
                if bar.heikin_ashi_close > bar.heikin_ashi_open:
                    directions.append(1)  # 陽線
                else:
                    directions.append(-1)  # 陰線
        
        # 方向の一致性を評価（単純化）
        return len(set(directions)) <= 2
    
    def _check_heikin_ashi_direction_consistency(self, bars: List[MarketData]) -> bool:
        """平均足方向の一致性チェック（改良版）"""
        if len(bars) < 2:
            return False
            
        consistent_count = 0
        total_count = len(bars) - 1
        
        for i in range(1, len(bars)):
            prev_direction = 1 if bars[i-1].heikin_ashi_close > bars[i-1].heikin_ashi_open else -1
            curr_direction = 1 if bars[i].heikin_ashi_close > bars[i].heikin_ashi_open else -1
            
            if prev_direction == curr_direction:
                consistent_count += 1
                
        return consistent_count / total_count > 0.6
    
    def _evaluate_direction_indicators(self, bars: List[MarketData]) -> float:
        """方向指標の評価（MHIH/MJIH等）"""
        if len(bars) < 3:
            return 0.0
            
        # 高値・安値の更新パターンを評価
        high_momentum = 0
        low_momentum = 0
        
        for i in range(1, len(bars)):
            if bars[i].high > bars[i-1].high:
                high_momentum += 1
            if bars[i].low < bars[i-1].low:
                low_momentum += 1
                
        return high_momentum - low_momentum
    
    def _check_baseline_cross_timing(self, bars: List[MarketData]) -> bool:
        """基準線交点タイミングのチェック"""
        # 基準線との交点タイミングを簡易実装
        # 実際の実装では移動平均等の基準線を使用
        if len(bars) < 2:
            return False
            
        baseline_crosses = 0
        for i in range(1, len(bars)):
            # 簡易的な基準線として前足終値を使用
            baseline = bars[i-1].close
            if (bars[i-1].close <= baseline <= bars[i].close) or \
               (bars[i-1].close >= baseline >= bars[i].close):
                baseline_crosses += 1
                
        return baseline_crosses > 0
    
    def _calculate_confidence(self, prev_prev: MarketData, 
                            prev: MarketData, current: MarketData) -> float:
        """信頼度の計算"""
        confidence_factors = []
        
        # 乖離の強さ
        deviation_strength = abs(self._calculate_deviation(prev_prev))
        confidence_factors.append(min(deviation_strength * 2, 1.0))
        
        # 平均足の一致性
        ha_consistency = self._check_heikin_ashi_direction_consistency([prev_prev, prev, current])
        confidence_factors.append(0.8 if ha_consistency else 0.3)
        
        # 方向指標の強さ
        direction_strength = abs(self._evaluate_direction_indicators([prev_prev, prev, current]))
        confidence_factors.append(min(direction_strength / 3.0, 1.0))
        
        # 統計的勝率を考慮
        base_confidence = self.performance_stats['win_rate']
        
        return base_confidence * np.mean(confidence_factors)
    
    def _update_performance_stats(self, signal: OperationSignal):
        """パフォーマンス統計の更新"""
        self.performance_stats['total_signals'] += 1
        # 実際の正解判定は後で実装

class IkikaerikFunction(BasePKGFunction):
    """
    行帰判定PKG関数
    
    メモファイルから抽出した行帰判定ロジック:
    - 行行：継続、行帰：一時的戻り、帰行：戻りから再進行、帰戻：完全転換
    - 平均足転換点と基準線による判定
    - 内包関係による時間足統合
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        
    def execute(self, data: Dict[str, any]) -> OperationSignal:
        """行帰判定の実行"""
        if not self.validate_input(data):
            return None
            
        market_data = data.get('market_data', [])
        if len(market_data) < 5:
            return None
            
        # 行帰パターンの判定
        ikikaeri_pattern = self._determine_ikikaeri_pattern(market_data)
        direction = self._calculate_ikikaeri_direction(market_data, ikikaeri_pattern)
        confidence = self._calculate_ikikaeri_confidence(market_data, ikikaeri_pattern)
        
        signal = OperationSignal(
            pkg_id=self.pkg_id,
            signal_type='ikikaeri',
            direction=direction,
            confidence=confidence,
            timestamp=market_data[-1].timestamp,
            metadata={
                'pattern': ikikaeri_pattern,
                'trend_continuation': self._check_trend_continuation(market_data),
                'reversal_strength': self._calculate_reversal_strength(market_data)
            }
        )
        
        return signal
    
    def _determine_ikikaeri_pattern(self, market_data: List[MarketData]) -> str:
        """
        行帰パターンの判定
        - 行行：継続
        - 行帰：一時的戻り
        - 帰行：戻りから再進行
        - 帰戻：完全転換
        """
        if len(market_data) < 4:
            return 'unknown'
            
        # 最近4足の高値・安値更新パターンを分析
        recent_bars = market_data[-4:]
        
        # 高値・安値の更新状況を評価
        high_updates = []
        low_updates = []
        
        for i in range(1, len(recent_bars)):
            high_updates.append(recent_bars[i].high > recent_bars[i-1].high)
            low_updates.append(recent_bars[i].low < recent_bars[i-1].low)
        
        # パターン判定
        if all(high_updates):
            return 'gyou_gyou'  # 行行（継続上昇）
        elif all(low_updates):
            return 'gyou_gyou'  # 行行（継続下降）
        elif high_updates[0] and not high_updates[-1]:
            return 'gyou_kaeri'  # 行帰（上昇から戻り）
        elif low_updates[0] and not low_updates[-1]:
            return 'gyou_kaeri'  # 行帰（下降から戻り）
        elif not high_updates[0] and high_updates[-1]:
            return 'kaeri_gyou'  # 帰行（戻りから再上昇）
        elif not low_updates[0] and low_updates[-1]:
            return 'kaeri_gyou'  # 帰行（戻りから再下降）
        else:
            return 'kaeri_modori'  # 帰戻（完全転換）
    
    def _calculate_ikikaeri_direction(self, market_data: List[MarketData], 
                                    pattern: str) -> int:
        """行帰パターンに基づく方向判定"""
        current_bar = market_data[-1]
        prev_bar = market_data[-2]
        
        # 平均足の方向
        ha_direction = 1 if current_bar.heikin_ashi_close > current_bar.heikin_ashi_open else -1
        
        # パターン別の方向判定
        if pattern == 'gyou_gyou':
            # 継続パターン - 平均足方向に従う
            return 1 if ha_direction > 0 else 2
        elif pattern == 'gyou_kaeri':
            # 一時的戻り - 逆方向を示唆
            return 2 if ha_direction > 0 else 1
        elif pattern == 'kaeri_gyou':
            # 戻りから再進行 - 平均足方向に従う
            return 1 if ha_direction > 0 else 2
        elif pattern == 'kaeri_modori':
            # 完全転換 - 逆方向
            return 2 if ha_direction > 0 else 1
        else:
            return 0  # 中立
    
    def _calculate_ikikaeri_confidence(self, market_data: List[MarketData], 
                                     pattern: str) -> float:
        """行帰判定の信頼度計算"""
        confidence_factors = []
        
        # パターンの明確さ
        pattern_clarity = {
            'gyou_gyou': 0.8,
            'gyou_kaeri': 0.7,
            'kaeri_gyou': 0.75,
            'kaeri_modori': 0.6,
            'unknown': 0.3
        }
        confidence_factors.append(pattern_clarity.get(pattern, 0.3))
        
        # 平均足の一貫性
        ha_consistency = self._check_heikin_ashi_direction_consistency(market_data[-5:])
        confidence_factors.append(0.8 if ha_consistency else 0.4)
        
        # ボラティリティ考慮
        volatility = self._calculate_volatility(market_data[-10:])
        vol_factor = max(0.3, min(1.0, 1.0 - volatility))
        confidence_factors.append(vol_factor)
        
        return np.mean(confidence_factors)
    
    def _check_trend_continuation(self, market_data: List[MarketData]) -> bool:
        """トレンド継続性のチェック"""
        if len(market_data) < 10:
            return False
            
        # 過去10足のトレンド方向を評価
        closes = [bar.close for bar in market_data[-10:]]
        trend_up = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
        
        return trend_up > 6 or trend_up < 4  # 明確なトレンドがある場合
    
    def _calculate_reversal_strength(self, market_data: List[MarketData]) -> float:
        """反転強度の計算"""
        if len(market_data) < 5:
            return 0.0
            
        recent_bars = market_data[-5:]
        price_changes = []
        
        for i in range(1, len(recent_bars)):
            change = (recent_bars[i].close - recent_bars[i-1].close) / recent_bars[i-1].close
            price_changes.append(change)
        
        # 反転の強度を変化率の標準偏差で評価
        return np.std(price_changes) if price_changes else 0.0
    
    def _check_heikin_ashi_direction_consistency(self, bars: List[MarketData]) -> bool:
        """平均足方向の一致性チェック（再利用）"""
        if len(bars) < 2:
            return False
            
        consistent_count = 0
        total_count = len(bars) - 1
        
        for i in range(1, len(bars)):
            if bars[i-1].heikin_ashi_close is None or bars[i].heikin_ashi_close is None:
                continue
                
            prev_direction = 1 if bars[i-1].heikin_ashi_close > bars[i-1].heikin_ashi_open else -1
            curr_direction = 1 if bars[i].heikin_ashi_close > bars[i].heikin_ashi_open else -1
            
            if prev_direction == curr_direction:
                consistent_count += 1
                
        return consistent_count / total_count > 0.6 if total_count > 0 else False
    
    def _calculate_volatility(self, bars: List[MarketData]) -> float:
        """ボラティリティ計算"""
        if len(bars) < 2:
            return 0.0
            
        returns = []
        for i in range(1, len(bars)):
            ret = (bars[i].close - bars[i-1].close) / bars[i-1].close
            returns.append(ret)
            
        return np.std(returns) if returns else 0.0

# 他のPKG関数は次のファイルで実装します