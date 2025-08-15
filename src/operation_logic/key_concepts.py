"""
FXオペレーションロジック - 重要概念のコード化

このモジュールは、メモファイル群から抽出したオペレーションロジックの
核心概念をPythonクラスとして実装するための準備コードを提供します。

主要概念:
1. 同逆判定 (DokyakuJudgment)
2. 行帰判定 (IkikaeriJudgment)
3. もみ・オーバーシュート判定 (MomiOvershootJudgment)
4. 時間足連携 (TimeframeCoordination)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np


class Direction(Enum):
    """方向性を表す列挙型"""
    UP = 1      # 上方向
    DOWN = 2    # 下方向
    NONE = 0    # 方向性なし


class TimeFrame(Enum):
    """時間足を表す列挙型"""
    M1 = "1M"     # 1分足
    M5 = "5M"     # 5分足
    M15 = "15M"   # 15分足
    M30 = "30M"   # 30分足
    H1 = "1H"     # 1時間足
    H4 = "4H"     # 4時間足


class IkikaeriType(Enum):
    """行帰の種類を表す列挙型"""
    IKI_IKI = "行行"    # 継続
    IKI_KAERI = "行帰"  # 一時的戻り
    KAERI_IKI = "帰行"  # 戻りから再進行
    KAERI_MODORI = "帰戻"  # 完全転換


@dataclass
class PriceData:
    """価格データを格納するデータクラス"""
    open: float
    high: float
    low: float
    close: float
    timestamp: pd.Timestamp
    timeframe: TimeFrame


@dataclass
class HeikinAshiData:
    """平均足データを格納するデータクラス"""
    open: float
    high: float
    low: float
    close: float
    direction: Direction
    timestamp: pd.Timestamp
    timeframe: TimeFrame


@dataclass
class IndicatorData:
    """指標データを格納するデータクラス"""
    os_value: float          # Os指標値
    os_direction: Direction  # Os方向
    os_increase: bool        # Os増減
    mac_direction: Direction # Mac方向
    period_t: int           # T周期
    period_s: int           # S周期
    base_line: float        # 基準線
    remaining_distance: float  # 残足


class BaseJudgment(ABC):
    """判定システムの基底クラス"""
    
    def __init__(self, name: str):
        self.name = name
        self.confidence_level = 0.0
        
    @abstractmethod
    def calculate(self, data: Dict) -> Tuple[Direction, float]:
        """
        判定計算を実行
        
        Returns:
            Tuple[Direction, float]: (方向, 信頼度)
        """
        pass


class DokyakuJudgment(BaseJudgment):
    """
    同逆判定システム
    
    前々足乖離による方向判断を実装
    メモファイル: 20200115_オペレーションロジックまとめ.txt より
    """
    
    def __init__(self):
        super().__init__("同逆判定")
        self.win_rates = {
            "mhih_mjih_match": 0.557,      # MHIHとMJIHが揃った場合
            "mmhmh_mmjmh": 0.560,          # 不一致時のMMHMH/MMJMH方向
            "mh_confirm": 0.558            # MH確定方向確認
        }
    
    def calculate(self, data: Dict) -> Tuple[Direction, float]:
        """
        同逆判定の計算実行
        
        Args:
            data: {
                'mhih_direction': Direction,    # 前足平均実勢方向
                'mjih_direction': Direction,    # 今足実勢平均方向
                'mmhmh_direction': Direction,   # 前々足平均平均方向
                'mmjmh_direction': Direction,   # 前々足実勢平均方向
                'mh_confirm_direction': Direction # MH確定方向
            }
        
        Returns:
            Tuple[Direction, float]: 判定方向と信頼度
        """
        mhih = data.get('mhih_direction', Direction.NONE)
        mjih = data.get('mjih_direction', Direction.NONE)
        
        # Step 1: MHIHとMJIHの一致確認
        if mhih == mjih and mhih != Direction.NONE:
            return mhih, self.win_rates["mhih_mjih_match"]
        
        # Step 2: 不一致時のMMHMH/MMJMH確認
        mmhmh = data.get('mmhmh_direction', Direction.NONE)
        mmjmh = data.get('mmjmh_direction', Direction.NONE)
        
        if mmhmh == mmjmh and mmhmh != Direction.NONE:
            return mmhmh, self.win_rates["mmhmh_mmjmh"]
        
        # Step 3: MH確定方向の確認
        mh_confirm = data.get('mh_confirm_direction', Direction.NONE)
        if mh_confirm != Direction.NONE:
            return mh_confirm, self.win_rates["mh_confirm"]
        
        return Direction.NONE, 0.0
    
    def check_exclusion_rule(self, data: Dict) -> bool:
        """
        除外ルールの確認
        転換足でMMHMHとMMJMHが逆向きの場合
        """
        mmhmh = data.get('mmhmh_direction', Direction.NONE)
        mmjmh = data.get('mmjmh_direction', Direction.NONE)
        mh_confirm = data.get('mh_confirm_direction', Direction.NONE)
        is_transition_bar = data.get('is_transition_bar', False)
        
        if is_transition_bar and mmhmh != mmjmh and mh_confirm != mmhmh:
            return True  # 転換しない
        
        return False


class IkikaeriJudgment(BaseJudgment):
    """
    行帰判定システム
    
    前足の動きから今足の方向予測を実装
    メモファイル: 20200330_取引用の行帰の見方.txt より
    """
    
    def __init__(self):
        super().__init__("行帰判定")
        self.ikikaeri_patterns = {
            IkikaeriType.IKI_IKI: {"priority": 1, "confidence": 0.70},
            IkikaeriType.KAERI_IKI: {"priority": 2, "confidence": 0.65},
            IkikaeriType.KAERI_MODORI: {"priority": 3, "confidence": 0.60},
            IkikaeriType.IKI_KAERI: {"priority": 4, "confidence": 0.55}
        }
    
    def calculate(self, data: Dict) -> Tuple[Direction, float]:
        """
        行帰判定の計算実行
        
        Args:
            data: {
                'current_heikin_direction': Direction,
                'previous_heikin_direction': Direction,
                'high_low_update': bool,           # 高値安値更新有無
                'base_line_position': float,       # 基準線位置
                'current_price': float,            # 現在価格
                'timeframe_alignment': Dict        # 時間足の方向揃い
            }
        """
        current_dir = data.get('current_heikin_direction', Direction.NONE)
        previous_dir = data.get('previous_heikin_direction', Direction.NONE)
        high_low_update = data.get('high_low_update', False)
        
        # 行帰パターンの判定
        ikikaeri_type = self._determine_ikikaeri_type(
            current_dir, previous_dir, high_low_update
        )
        
        pattern_info = self.ikikaeri_patterns.get(ikikaeri_type)
        if pattern_info:
            return current_dir, pattern_info["confidence"]
        
        return Direction.NONE, 0.0
    
    def _determine_ikikaeri_type(self, current_dir: Direction, 
                               previous_dir: Direction, 
                               high_low_update: bool) -> IkikaeriType:
        """行帰タイプの判定"""
        if current_dir == previous_dir:
            if high_low_update:
                return IkikaeriType.IKI_IKI
            else:
                return IkikaeriType.IKI_KAERI
        else:
            if high_low_update:
                return IkikaeriType.KAERI_IKI
            else:
                return IkikaeriType.KAERI_MODORI
    
    def calculate_remaining_distance(self, current_price: float, 
                                   target_line: float, 
                                   average_range: float) -> float:
        """残足計算"""
        if average_range == 0:
            return float('inf')
        return abs(current_price - target_line) / average_range


class MomiOvershootJudgment(BaseJudgment):
    """
    もみ・オーバーシュート判定システム
    
    相場状況の判定を実装
    メモファイル: 20200401_もみ検討.txt より
    """
    
    def __init__(self):
        super().__init__("もみ・オーバーシュート判定")
        self.momi_threshold = 3.0  # もみ判定の閾値（pips）
        self.overshoot_threshold = 2.0  # オーバーシュート閾値
    
    def calculate(self, data: Dict) -> Tuple[Direction, float]:
        """
        もみ・オーバーシュート判定の計算実行
        
        Args:
            data: {
                'range_width': float,              # レンジ幅
                'os_remaining': float,             # Os残足
                'current_timeframe_conversion': float,  # 今足換算値
                'breakout_direction': Direction,   # 抜け方向
                'previous_overshoot': Direction    # 前足オーバーシュート方向
            }
        """
        range_width = data.get('range_width', 0.0)
        os_remaining = data.get('os_remaining', 0.0)
        current_conversion = data.get('current_timeframe_conversion', 1.0)
        
        # もみ判定
        if range_width < self.momi_threshold:
            return self._handle_momi_state(data)
        
        # オーバーシュート判定
        if os_remaining / current_conversion >= self.overshoot_threshold:
            return self._handle_overshoot_state(data)
        
        return Direction.NONE, 0.0
    
    def _handle_momi_state(self, data: Dict) -> Tuple[Direction, float]:
        """もみ状態の処理"""
        breakout_direction = data.get('breakout_direction', Direction.NONE)
        if breakout_direction != Direction.NONE:
            return breakout_direction, 0.77  # メモより77%の勝率
        return Direction.NONE, 0.0
    
    def _handle_overshoot_state(self, data: Dict) -> Tuple[Direction, float]:
        """オーバーシュート状態の処理"""
        previous_overshoot = data.get('previous_overshoot', Direction.NONE)
        current_direction = data.get('current_direction', Direction.NONE)
        
        # 逆方向オーバーシュートの確認
        if previous_overshoot != Direction.NONE and previous_overshoot != current_direction:
            # 逆方向に返す可能性が高い
            return previous_overshoot, 0.65
        
        return Direction.NONE, 0.0


class TimeframeCoordination(BaseJudgment):
    """
    時間足連携システム
    
    1M, 5M, 15M, 30M の連携ロジックを実装
    メモファイル: 20200918_オペレーション時間単体及び時間結合のロジック.txt より
    """
    
    def __init__(self):
        super().__init__("時間足連携")
        self.coordination_patterns = {
            ("15M_UP", "5M_UP"): {"zone": "0-T", "strength": "strong"},
            ("15M_UP", "5M_DOWN"): {"zone": "0-T,T-S", "strength": "adjustment"},
            ("15M_DOWN", "5M_UP"): {"zone": "0-T,T-S,T-L", "strength": "preparation"},
            ("15M_DOWN", "5M_DOWN"): {"zone": "T-S,T-M,T-L", "strength": "confirmed"}
        }
    
    def calculate(self, data: Dict) -> Tuple[Direction, float]:
        """
        時間足連携の計算実行
        
        Args:
            data: {
                'timeframe_directions': Dict[TimeFrame, Direction],
                'transition_timings': Dict[TimeFrame, bool],
                'period_alignments': Dict[TimeFrame, bool]
            }
        """
        directions = data.get('timeframe_directions', {})
        transition_timings = data.get('transition_timings', {})
        
        # 基本的な時間足連携パターンの確認
        m15_dir = directions.get(TimeFrame.M15, Direction.NONE)
        m5_dir = directions.get(TimeFrame.M5, Direction.NONE)
        
        pattern_key = (f"15M_{m15_dir.name}", f"5M_{m5_dir.name}")
        pattern_info = self.coordination_patterns.get(pattern_key)
        
        if pattern_info:
            strength = pattern_info["strength"]
            confidence = self._calculate_confidence_by_strength(strength)
            
            # 時間足連携による方向決定
            if strength in ["strong", "confirmed"]:
                return m15_dir, confidence
            else:
                # 調整段階では短い時間足を重視
                return m5_dir, confidence * 0.8
        
        return Direction.NONE, 0.0
    
    def _calculate_confidence_by_strength(self, strength: str) -> float:
        """強度による信頼度計算"""
        strength_map = {
            "strong": 0.85,
            "confirmed": 0.80,
            "adjustment": 0.60,
            "preparation": 0.65
        }
        return strength_map.get(strength, 0.5)
    
    def check_transition_timing(self, timeframe: TimeFrame, 
                              remaining_bars: int) -> bool:
        """転換タイミングの確認"""
        return remaining_bars <= 0
    
    def calculate_internal_inclusion(self, data: Dict) -> Dict[TimeFrame, bool]:
        """内包関係の計算"""
        # 時間足の内包関係を計算
        # 実装詳細は具体的な価格データ構造に依存
        pass


class OperationLogicEngine:
    """
    オペレーションロジックエンジン
    
    各判定システムを統合して最終的な取引判断を行う
    """
    
    def __init__(self):
        self.dokyaku_judgment = DokyakuJudgment()
        self.ikikaeri_judgment = IkikaeriJudgment()
        self.momi_overshoot_judgment = MomiOvershootJudgment()
        self.timeframe_coordination = TimeframeCoordination()
        
        # 重み設定（メモファイルの勝率データより）
        self.weights = {
            'dokyaku': 0.25,
            'ikikaeri': 0.25,
            'momi_overshoot': 0.30,  # 高勝率のため重み大
            'timeframe': 0.20
        }
    
    def make_decision(self, market_data: Dict) -> Dict:
        """
        統合判断の実行
        
        Args:
            market_data: 市場データの辞書
            
        Returns:
            Dict: {
                'direction': Direction,
                'confidence': float,
                'entry_signal': bool,
                'exit_signal': bool,
                'details': Dict  # 各判定の詳細
            }
        """
        # 各判定システムの実行
        dokyaku_result = self.dokyaku_judgment.calculate(
            market_data.get('dokyaku_data', {})
        )
        ikikaeri_result = self.ikikaeri_judgment.calculate(
            market_data.get('ikikaeri_data', {})
        )
        momi_result = self.momi_overshoot_judgment.calculate(
            market_data.get('momi_data', {})
        )
        timeframe_result = self.timeframe_coordination.calculate(
            market_data.get('timeframe_data', {})
        )
        
        # 重み付き統合判断
        final_direction, final_confidence = self._integrate_results(
            dokyaku_result, ikikaeri_result, momi_result, timeframe_result
        )
        
        # エントリー・エグジット信号の生成
        entry_signal = self._generate_entry_signal(final_confidence, market_data)
        exit_signal = self._generate_exit_signal(final_confidence, market_data)
        
        return {
            'direction': final_direction,
            'confidence': final_confidence,
            'entry_signal': entry_signal,
            'exit_signal': exit_signal,
            'details': {
                'dokyaku': dokyaku_result,
                'ikikaeri': ikikaeri_result,
                'momi_overshoot': momi_result,
                'timeframe': timeframe_result
            }
        }
    
    def _integrate_results(self, *results) -> Tuple[Direction, float]:
        """結果の統合計算"""
        directions = []
        confidences = []
        weights = list(self.weights.values())
        
        for result in results:
            direction, confidence = result
            if direction != Direction.NONE:
                directions.append(direction)
                confidences.append(confidence)
            else:
                directions.append(None)
                confidences.append(0.0)
        
        # 重み付き平均の計算
        if not any(directions):
            return Direction.NONE, 0.0
        
        # 最も多い方向を採用（重み考慮）
        up_weight = sum(w * c for w, c, d in zip(weights, confidences, directions) 
                       if d == Direction.UP)
        down_weight = sum(w * c for w, c, d in zip(weights, confidences, directions) 
                         if d == Direction.DOWN)
        
        if up_weight > down_weight:
            final_direction = Direction.UP
            final_confidence = up_weight / sum(weights)
        elif down_weight > up_weight:
            final_direction = Direction.DOWN
            final_confidence = down_weight / sum(weights)
        else:
            final_direction = Direction.NONE
            final_confidence = 0.0
        
        return final_direction, final_confidence
    
    def _generate_entry_signal(self, confidence: float, market_data: Dict) -> bool:
        """エントリー信号の生成"""
        # メモファイルのエントリー条件を実装
        if confidence < 0.6:  # 信頼度閾値
            return False
        
        # 前足平均足の陰陽確認
        heikin_condition = market_data.get('previous_heikin_valid', False)
        
        # 周期の揃い確認
        period_alignment = market_data.get('period_alignment', False)
        
        # オーバーシュート成立確認
        overshoot_valid = market_data.get('overshoot_established', False)
        
        return heikin_condition and period_alignment and overshoot_valid
    
    def _generate_exit_signal(self, confidence: float, market_data: Dict) -> bool:
        """エグジット信号の生成"""
        # メモファイルの決済条件を実装
        minute_alignment = market_data.get('minute_alignment', False)
        opff_alignment = market_data.get('opff_previous_alignment', False)
        
        # 時間足の接続点確認
        connection_point = market_data.get('timeframe_connection_point', False)
        
        return (minute_alignment and opff_alignment) or connection_point


# ユーティリティ関数
def calculate_heikin_ashi(price_data: PriceData, 
                         previous_heikin: Optional[HeikinAshiData] = None) -> HeikinAshiData:
    """平均足の計算"""
    ha_close = (price_data.open + price_data.high + price_data.low + price_data.close) / 4
    
    if previous_heikin:
        ha_open = (previous_heikin.open + previous_heikin.close) / 2
    else:
        ha_open = (price_data.open + price_data.close) / 2
    
    ha_high = max(price_data.high, ha_open, ha_close)
    ha_low = min(price_data.low, ha_open, ha_close)
    
    direction = Direction.UP if ha_close > ha_open else Direction.DOWN
    
    return HeikinAshiData(
        open=ha_open,
        high=ha_high,
        low=ha_low,
        close=ha_close,
        direction=direction,
        timestamp=price_data.timestamp,
        timeframe=price_data.timeframe
    )


def validate_timeframe_data(data: Dict[TimeFrame, List[PriceData]]) -> bool:
    """時間足データの妥当性検証"""
    required_timeframes = [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15, TimeFrame.M30]
    
    for tf in required_timeframes:
        if tf not in data or len(data[tf]) < 2:
            return False
    
    return True


# テスト用のサンプルデータ生成関数
def generate_sample_data() -> Dict:
    """テスト用のサンプルデータ生成"""
    return {
        'dokyaku_data': {
            'mhih_direction': Direction.UP,
            'mjih_direction': Direction.UP,
            'mmhmh_direction': Direction.UP,
            'mmjmh_direction': Direction.DOWN,
            'mh_confirm_direction': Direction.UP,
            'is_transition_bar': False
        },
        'ikikaeri_data': {
            'current_heikin_direction': Direction.UP,
            'previous_heikin_direction': Direction.UP,
            'high_low_update': True,
            'base_line_position': 110.50,
            'current_price': 110.75
        },
        'momi_data': {
            'range_width': 2.5,
            'os_remaining': 3.0,
            'current_timeframe_conversion': 1.0,
            'breakout_direction': Direction.UP,
            'previous_overshoot': Direction.DOWN
        },
        'timeframe_data': {
            'timeframe_directions': {
                TimeFrame.M15: Direction.UP,
                TimeFrame.M5: Direction.UP
            },
            'transition_timings': {
                TimeFrame.M15: False,
                TimeFrame.M5: True
            }
        },
        'previous_heikin_valid': True,
        'period_alignment': True,
        'overshoot_established': True,
        'minute_alignment': False,
        'opff_previous_alignment': False,
        'timeframe_connection_point': False
    }


if __name__ == "__main__":
    # 使用例
    engine = OperationLogicEngine()
    sample_data = generate_sample_data()
    
    result = engine.make_decision(sample_data)
    print(f"判定結果: {result}")