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

import math
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
import logging
from dataclasses import dataclass
from datetime import datetime

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
        return f"{self.timeframe.value}{self.period.value}{self.currency.value}^{self.layer}-{self.sequence}"
    
    @classmethod
    def parse(cls, pkg_id_str: str) -> 'PKGId':
        """PKG ID文字列をパース"""
        try:
            base, layer_seq = pkg_id_str.split('^')
            layer, sequence = layer_seq.split('-')
            
            timeframe = TimeFrame(int(base[0]))
            period = Period(int(base[1]))  # 周期は1桁
            currency = Currency(int(base[2]))  # 通貨は3桁目
            
            return cls(timeframe, period, currency, int(layer), int(sequence))
        except Exception as e:
            raise ValueError(f"Invalid PKG ID format: {pkg_id_str}") from e

@dataclass
class MarketData:
    """市場データ構造"""
    timestamp: datetime
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
    timestamp: datetime
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
        
        return base_confidence * (sum(confidence_factors) / len(confidence_factors))
    
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
        
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
    
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
        if not price_changes:
            return 0.0
        mean_change = sum(price_changes) / len(price_changes)
        variance = sum((x - mean_change) ** 2 for x in price_changes) / len(price_changes)
        return math.sqrt(variance)
    
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
            
        if not returns:
            return 0.0
        mean_return = sum(returns) / len(returns)
        variance = sum((x - mean_return) ** 2 for x in returns) / len(returns)
        return math.sqrt(variance)

# === 優先度高PKG関数実装 ===
# 分析結果に基づく実装可能な関数群

class RatioFunction(BasePKGFunction):
    """
    比率計算関数（Ratio）
    
    使用例: CA111 = Ratio(CA111_CA118_CA125_CA132)
    複数の入力値から比率を計算
    Z(2)関数を使用した実装
    使用頻度: 4回
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        self.function_type = "Ratio"
    
    def execute(self, data: Dict[str, any]) -> float:
        """比率計算の実行"""
        if not self.validate_input(data):
            return 0.0
        
        inputs = data.get('inputs', [])
        if len(inputs) < 2:
            self.logger.warning(f"Ratio関数には2個以上の入力が必要: {len(inputs)}個")
            return 0.0
        
        try:
            # 基本パターン: 最初の値を分子、残りの合計を分母とする比率
            numerator = float(inputs[0]) if inputs[0] is not None else 0.0
            denominator = sum(float(x) if x is not None else 0.0 for x in inputs[1:])
            
            if abs(denominator) < 1e-10:  # ゼロ除算回避
                return 0.0
                
            ratio = numerator / denominator
            
            self.logger.debug(f"Ratio計算: {numerator} / {denominator} = {ratio}")
            return ratio
            
        except Exception as e:
            self.logger.error(f"Ratio計算エラー: {e}")
            return 0.0
    
    def validate_input(self, data: Dict[str, any]) -> bool:
        """入力検証"""
        return 'inputs' in data and len(data['inputs']) >= 2


class OSumFunction(BasePKGFunction):
    """
    合計関数（OSum）
    
    使用例: CA139 = OSum(SU067_SU068)
    複数の入力値を合計
    CO関数の拡張実装
    使用頻度: 13回（最重要）
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        self.function_type = "OSum"
    
    def execute(self, data: Dict[str, any]) -> float:
        """合計計算の実行"""
        if not self.validate_input(data):
            return 0.0
        
        inputs = data.get('inputs', [])
        if not inputs:
            return 0.0
        
        try:
            # 全入力値の合計
            total = sum(float(x) if x is not None else 0.0 for x in inputs)
            
            self.logger.debug(f"OSum計算: {inputs} = {total}")
            return total
            
        except Exception as e:
            self.logger.error(f"OSum計算エラー: {e}")
            return 0.0
    
    def validate_input(self, data: Dict[str, any]) -> bool:
        """入力検証"""
        return 'inputs' in data


class LeaderNumFunction(BasePKGFunction):
    """
    3通貨ペア強弱判定関数（LeaderNum）
    
    使用例: SA014 = LeaderNum(USDJPY_strength, EURJPY_strength, EURUSD_strength, threshold=45)
    USDJPY/EURJPY/EURUSDの3通貨ペア間の相対強弱を判定
    
    物理的連動理由:
    - 三角裁定関係: USDJPY × EURUSD = EURJPY
    - 共通通貨JPY: USDJPYとEURJPYの連動性
    - クロス通貨関係: EURUSDが他2ペアに与える影響
    
    メモファイルの通貨間相対価値理論に基づく実装
    使用頻度: 11回
    """
    
    # 3通貨ペアマッピング（PKGシステム対応）
    CURRENCY_PAIR_MAP = {
        1: "USDJPY",  # USD/JPY
        2: "EURJPY",  # EUR/JPY  
        3: "EURUSD"   # EUR/USD
    }
    
    # 通貨別強弱を計算するための係数
    CURRENCY_COEFFICIENTS = {
        "USD": {"USDJPY": 1, "EURJPY": 0, "EURUSD": -1},   # USD強い = USDJPY上昇, EURUSD下降
        "EUR": {"USDJPY": 0, "EURJPY": 1, "EURUSD": 1},    # EUR強い = EURJPY上昇, EURUSD上昇
        "JPY": {"USDJPY": -1, "EURJPY": -1, "EURUSD": 0}   # JPY強い = USD/JPY下降, EUR/JPY下降
    }
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        self.function_type = "LeaderNum"
    
    def execute(self, data: Dict[str, any]) -> int:
        """3通貨ペア動きのリーダー判定の実行"""
        if not self.validate_input(data):
            return 0
        
        inputs = data.get('inputs', [])
        threshold = data.get('threshold', 0.0)
        
        # 3通貨ペアの価格が必要
        if len(inputs) < 3:
            self.logger.warning(f"3通貨ペア動きのリーダー判定には3個の入力が必要: {len(inputs)}個")
            return 0
        
        try:
            # 現在価格の取得
            usdjpy_price = float(inputs[0]) if inputs[0] is not None else 0.0
            eurjpy_price = float(inputs[1]) if inputs[1] is not None else 0.0
            eurusd_price = float(inputs[2]) if inputs[2] is not None else 0.0
            
            if usdjpy_price <= 0 or eurjpy_price <= 0 or eurusd_price <= 0:
                return 0
            
            # 三角裁定理論値の計算
            # 理論的に成立すべき関係: USDJPY × EURUSD = EURJPY
            theoretical_eurjpy = usdjpy_price * eurusd_price
            
            # 各通貨ペアの三角裁定からの乖離度を計算
            usdjpy_deviation = abs((eurjpy_price / eurusd_price) - usdjpy_price) / usdjpy_price
            eurjpy_deviation = abs(theoretical_eurjpy - eurjpy_price) / eurjpy_price  
            eurusd_deviation = abs((eurjpy_price / usdjpy_price) - eurusd_price) / eurusd_price
            
            # 乖離度が最大の通貨ペアがリーダー
            deviations = {
                1: ("USDJPY", usdjpy_deviation),
                2: ("EURJPY", eurjpy_deviation),
                3: ("EURUSD", eurusd_deviation)
            }
            
            # 最大乖離度を持つ通貨ペアを特定
            max_deviation = 0.0
            leader_pair = 0
            
            for pair_num, (pair_name, deviation) in deviations.items():
                if deviation > max_deviation and deviation > threshold:
                    max_deviation = deviation
                    leader_pair = pair_num
            
            if leader_pair > 0:
                leader_name = deviations[leader_pair][0]
                self.logger.debug(f"動きのリーダー判定: {leader_name}がリーダー (乖離度={max_deviation:.4f}, 閾値={threshold})")
                self.logger.debug(f"理論EURJPY={theoretical_eurjpy:.4f}, 実際EURJPY={eurjpy_price:.4f}")
                return leader_pair
            else:
                self.logger.debug(f"動きのリーダー判定: 閾値{threshold}を超える乖離なし")
                return 0
                
        except Exception as e:
            self.logger.error(f"動きのリーダー判定エラー: {e}")
            return 0
    
    def get_triangular_arbitrage_analysis(self, data: Dict[str, any]) -> Dict[str, float]:
        """三角裁定分析を返す（デバッグ用）"""
        inputs = data.get('inputs', [])
        if len(inputs) < 3:
            return {}
        
        try:
            usdjpy_price = float(inputs[0]) if inputs[0] is not None else 0.0
            eurjpy_price = float(inputs[1]) if inputs[1] is not None else 0.0
            eurusd_price = float(inputs[2]) if inputs[2] is not None else 0.0
            
            if usdjpy_price <= 0 or eurjpy_price <= 0 or eurusd_price <= 0:
                return {}
            
            # 三角裁定理論値
            theoretical_eurjpy = usdjpy_price * eurusd_price
            theoretical_usdjpy = eurjpy_price / eurusd_price
            theoretical_eurusd = eurjpy_price / usdjpy_price
            
            # 各ペアの乖離度
            usdjpy_deviation = abs(theoretical_usdjpy - usdjpy_price) / usdjpy_price
            eurjpy_deviation = abs(theoretical_eurjpy - eurjpy_price) / eurjpy_price  
            eurusd_deviation = abs(theoretical_eurusd - eurusd_price) / eurusd_price
            
            return {
                "USDJPY_actual": usdjpy_price,
                "EURJPY_actual": eurjpy_price,
                "EURUSD_actual": eurusd_price,
                "EURJPY_theoretical": theoretical_eurjpy,
                "USDJPY_theoretical": theoretical_usdjpy,
                "EURUSD_theoretical": theoretical_eurusd,
                "USDJPY_deviation": usdjpy_deviation,
                "EURJPY_deviation": eurjpy_deviation,
                "EURUSD_deviation": eurusd_deviation,
                "max_deviation": max(usdjpy_deviation, eurjpy_deviation, eurusd_deviation),
                "arbitrage_opportunity": abs(theoretical_eurjpy - eurjpy_price)  # 裁定機会の大きさ
            }
            
        except Exception:
            return {}
    
    def validate_input(self, data: Dict[str, any]) -> bool:
        """入力検証"""
        return 'inputs' in data and len(data['inputs']) >= 3


class DualDirectionFunction(BasePKGFunction):
    """
    双方向判定関数（DualDirection）
    
    使用例: BA061（使用頻度1回）
    上下両方向の判定を行う
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        self.function_type = "DualDirection"
    
    def execute(self, data: Dict[str, any]) -> Dict[str, float]:
        """双方向判定の実行"""
        if not self.validate_input(data):
            return {'up': 0.0, 'down': 0.0}
        
        inputs = data.get('inputs', [])
        if not inputs:
            return {'up': 0.0, 'down': 0.0}
        
        try:
            # 簡単な双方向判定: 値が正なら上、負なら下
            value = float(inputs[0]) if inputs[0] is not None else 0.0
            
            result = {
                'up': max(0.0, value),    # 正の値なら上方向
                'down': max(0.0, -value)  # 負の値なら下方向
            }
            
            self.logger.debug(f"DualDirection判定: {value} → {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"DualDirection計算エラー: {e}")
            return {'up': 0.0, 'down': 0.0}
    
    def validate_input(self, data: Dict[str, any]) -> bool:
        """入力検証"""
        return 'inputs' in data


class AbsIchiFunction(BasePKGFunction):
    """
    絶対値距離関数（AbsIchi）
    
    使用例: AA051（使用頻度1回、閾値0.25）
    入力値と基準値の絶対値距離を計算
    使用頻度: 1回
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        self.function_type = "AbsIchi"
    
    def execute(self, data: Dict[str, any]) -> float:
        """絶対値距離計算の実行"""
        if not self.validate_input(data):
            return 0.0
        
        inputs = data.get('inputs', [])
        reference = data.get('reference', 0.0)  # 基準値
        
        if not inputs:
            return 0.0
        
        try:
            # 最初の入力値と基準値の絶対値距離
            value = float(inputs[0]) if inputs[0] is not None else 0.0
            distance = abs(value - reference)
            
            self.logger.debug(f"AbsIchi計算: |{value} - {reference}| = {distance}")
            return distance
            
        except Exception as e:
            self.logger.error(f"AbsIchi計算エラー: {e}")
            return 0.0
    
    def validate_input(self, data: Dict[str, any]) -> bool:
        """入力検証"""
        return 'inputs' in data


class MinusFunction(BasePKGFunction):
    """
    減算関数（Minus）
    
    使用例: SV003（使用頻度2回）
    2つの入力値の差を計算
    Z(2)関数ベースの実装
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        self.function_type = "Minus"
    
    def execute(self, data: Dict[str, any]) -> float:
        """減算の実行"""
        if not self.validate_input(data):
            return 0.0
        
        inputs = data.get('inputs', [])
        if len(inputs) < 2:
            self.logger.warning(f"Minus関数には2個の入力が必要: {len(inputs)}個")
            return 0.0
        
        try:
            # 第1引数から第2引数を減算
            value1 = float(inputs[0]) if inputs[0] is not None else 0.0
            value2 = float(inputs[1]) if inputs[1] is not None else 0.0
            
            result = value1 - value2
            
            self.logger.debug(f"Minus計算: {value1} - {value2} = {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Minus計算エラー: {e}")
            return 0.0
    
    def validate_input(self, data: Dict[str, any]) -> bool:
        """入力検証"""
        return 'inputs' in data and len(data['inputs']) >= 2


# PKG関数ファクトリー
class PKGFunctionFactory:
    """PKG関数のファクトリークラス"""
    
    FUNCTION_TYPES = {
        'Ratio': RatioFunction,
        'OSum': OSumFunction,
        'LeaderNum': LeaderNumFunction,
        'DualDirection': DualDirectionFunction,
        'AbsIchi': AbsIchiFunction,
        'Minus': MinusFunction,
        'Dokyaku': DokyakuFunction,
        'Ikikaeri': IkikaerikFunction
    }
    
    @classmethod
    def create_function(cls, function_type: str, pkg_id: PKGId) -> BasePKGFunction:
        """PKG関数のインスタンスを生成"""
        if function_type not in cls.FUNCTION_TYPES:
            raise ValueError(f"未サポートの関数タイプ: {function_type}")
        
        function_class = cls.FUNCTION_TYPES[function_type]
        return function_class(pkg_id)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """サポートされている関数タイプの一覧を返す"""
        return list(cls.FUNCTION_TYPES.keys())
    
    @classmethod
    def get_implementation_stats(cls) -> Dict[str, int]:
        """実装統計を返す"""
        return {
            'total_types': len(cls.FUNCTION_TYPES),
            'high_priority_implemented': 6,  # Ratio, OSum, LeaderNum, DualDirection, AbsIchi, Minus
            'memo_based_implemented': 2,     # Dokyaku, Ikikaeri
            'coverage_percentage': 81.4      # 分析結果より
        }