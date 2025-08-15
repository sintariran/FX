"""
Week 6: 基本PKG関数実装
メモファイルから抽出した基本的なPKG関数（Z、SL、MN、CO、SG、AS、等）
Excel関数のパッケージ照合メモの内容をベースに実装

メモファイル参照:
- 20200514_エクセル関数のパッケージ照合.txt
- 20200115_オペレーションロジックまとめ.txt
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
import logging
import math
from datetime import datetime, timedelta

from .core_pkg_functions import (
    BasePKGFunction, PKGId, MarketData, OperationSignal,
    TimeFrame, Currency, Period
)

class ZFunction(BasePKGFunction):
    """
    Z関数 - 算術演算PKG関数
    
    メモファイルから抽出:
    - Z(2): 2入力減算関数
    - Z(8): 8入力mod演算
    - type_z: 1,2で構成されるパッケージを素材として、ステート切替時刻を起点とする
    """
    
    def __init__(self, pkg_id: PKGId, operation_type: int = 2):
        super().__init__(pkg_id)
        self.operation_type = operation_type  # 2=減算, 8=mod演算
        
    def execute(self, data: Dict[str, Any]) -> Union[float, int]:
        """Z関数実行"""
        inputs = data.get('inputs', [])
        
        if self.operation_type == 2:
            return self._execute_z2(inputs)
        elif self.operation_type == 8:
            return self._execute_z8(inputs)
        else:
            self.logger.warning(f"Unsupported Z operation type: {self.operation_type}")
            return 0.0
    
    def _execute_z2(self, inputs: List[float]) -> float:
        """
        Z(2) - 2入力減算関数
        メモ: 条件1に引数、条件2に191^0.49999（ROUNDDOWNで使用）
        """
        if len(inputs) < 2:
            self.logger.warning("Z(2) requires at least 2 inputs")
            return 0.0
            
        return float(inputs[0] - inputs[1])
    
    def _execute_z8(self, inputs: List[float]) -> int:
        """
        Z(8) - 8入力mod演算
        メモ: 引数1を条件1に設定、引数2を条件2に設定
        """
        if len(inputs) < 8:
            self.logger.warning(f"Z(8) requires 8 inputs, got {len(inputs)}")
            # 不足分は0で埋める
            inputs.extend([0.0] * (8 - len(inputs)))
        
        # 最初の8入力を使用
        sum_val = sum(inputs[:8])
        return int(sum_val) % 8

class SLFunction(BasePKGFunction):
    """
    SL関数 - SELECT関数（可変入力）
    
    メモファイルから抽出:
    - 範囲指定の行数分用意
    - 出力値は範囲指定の行番号（1〜n）
    - 条件はタイプX2の出力値が3のルートIDを各範囲指定の行数別に指定
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        
    def execute(self, data: Dict[str, Any]) -> Any:
        """SL関数実行"""
        condition = data.get('condition', 0)
        options = data.get('options', [])
        default_value = data.get('default', 0)
        
        if not options:
            return default_value
            
        # 条件が真の場合は第1オプション、偽の場合は第2オプション
        if isinstance(condition, bool):
            index = 0 if condition else 1
        elif isinstance(condition, (int, float)):
            # 数値の場合、0でない値を真とする
            index = 0 if condition != 0 else 1
        else:
            index = 1
            
        if index < len(options):
            return options[index]
        else:
            return default_value

class MNFunction(BasePKGFunction):
    """
    MN関数 - MINUTE関数（時刻処理）
    
    メモファイルから抽出:
    - 対象の時刻を分換算に置き換える関数
    - モード1: 現在時刻から算出
    - モード2: 条件1に記載するパッケージが持っている時刻データから算出
    """
    
    def __init__(self, pkg_id: PKGId, mode: int = 1):
        super().__init__(pkg_id)
        self.mode = mode
        
    def execute(self, data: Dict[str, Any]) -> int:
        """MN関数実行"""
        if self.mode == 1:
            # 現在時刻から分を取得
            current_time = data.get('current_time', datetime.now())
            if isinstance(current_time, pd.Timestamp):
                return current_time.minute
            elif isinstance(current_time, datetime):
                return current_time.minute
            else:
                return datetime.now().minute
                
        elif self.mode == 2:
            # 指定されたパッケージの時刻データから分を取得
            time_data = data.get('time_data')
            if time_data:
                if isinstance(time_data, pd.Timestamp):
                    return time_data.minute
                elif isinstance(time_data, datetime):
                    return time_data.minute
                elif isinstance(time_data, MarketData):
                    return time_data.timestamp.minute
                    
        return 0

class COFunction(BasePKGFunction):
    """
    CO関数 - COUNT関数（時間窓での特定コードカウント）
    
    メモファイルから抽出:
    - type_co (count): 素材として指定した数字を基に値を計算する
    - 5が指定されたら、5+4+3+2+1の値を出力する
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        
    def execute(self, data: Dict[str, Any]) -> int:
        """CO関数実行"""
        time_series = data.get('time_series', [])
        target_code = data.get('target_code', 1)
        window_size = data.get('window_size', len(time_series))
        
        if not time_series:
            return 0
            
        # 指定されたサイズの時間窓で計算
        if window_size <= 0:
            return 0
            
        # メモの仕様: 指定された数字を基に連続値の和を計算
        if isinstance(target_code, (int, float)) and target_code > 0:
            # 5が指定されたら5+4+3+2+1を計算
            return sum(range(1, int(target_code) + 1))
        
        # 通常のカウント処理
        recent_data = time_series[-window_size:] if window_size < len(time_series) else time_series
        return sum(1 for value in recent_data if value == target_code)

class SGFunction(BasePKGFunction):
    """
    SG関数 - SUM_GROUP関数（グループ内積算）
    
    メモファイルから抽出:
    - 素材1で指定されたパッケージで区間の切替りを1,2で指定
    - 素材2で積算対象の数字を指定
    - 素材1と素材2のパッケージに基づいて、区間毎の値の和算をする
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        
    def execute(self, data: Dict[str, Any]) -> float:
        """SG関数実行"""
        section_indicators = data.get('section_indicators', [])  # 区間切替指標（1,2のリスト）
        values_to_sum = data.get('values_to_sum', [])  # 積算対象の値
        
        if not section_indicators or not values_to_sum:
            return 0.0
            
        # データ長を合わせる
        min_length = min(len(section_indicators), len(values_to_sum))
        section_indicators = section_indicators[:min_length]
        values_to_sum = values_to_sum[:min_length]
        
        # 区間毎の合計を計算
        current_sum = 0.0
        section_sums = []
        
        for i in range(len(section_indicators)):
            current_sum += values_to_sum[i]
            
            # 区間の切替り（1→2 または 2→1）を検出
            if i > 0 and section_indicators[i] != section_indicators[i-1]:
                section_sums.append(current_sum - values_to_sum[i])  # 前の区間の合計
                current_sum = values_to_sum[i]  # 新しい区間の開始
        
        # 最後の区間の合計を追加
        section_sums.append(current_sum)
        
        # 最新の区間の合計を返す
        return section_sums[-1] if section_sums else 0.0

class ASFunction(BasePKGFunction):
    """
    AS関数 - AVERAGE_SECTION（区間平均計算）
    
    メモファイルから抽出:
    - 素材1に平均したい区間用のPKGを指定
    - 素材2に平均したい数値(価格)のPKGを指定
    - 出力に1を指定した場合は現区間の平均を出し、2を指定した場合は1つ前区間の平均を出す
    """
    
    def __init__(self, pkg_id: PKGId, output_mode: int = 1):
        super().__init__(pkg_id)
        self.output_mode = output_mode  # 1=現区間, 2=前区間
        
    def execute(self, data: Dict[str, Any]) -> float:
        """AS関数実行"""
        section_indicators = data.get('section_indicators', [])  # 区間指標
        price_values = data.get('price_values', [])  # 価格データ
        
        if not section_indicators or not price_values:
            return 0.0
            
        # データ長を合わせる
        min_length = min(len(section_indicators), len(price_values))
        section_indicators = section_indicators[:min_length]
        price_values = price_values[:min_length]
        
        # 区間毎の平均を計算
        sections = []
        current_section = []
        
        for i in range(len(section_indicators)):
            current_section.append(price_values[i])
            
            # 区間の切替りを検出
            if i > 0 and section_indicators[i] != section_indicators[i-1]:
                if len(current_section) > 1:  # 前の区間のデータ（最後の要素を除く）
                    sections.append(current_section[:-1])
                current_section = [price_values[i]]  # 新しい区間の開始
        
        # 最後の区間を追加
        if current_section:
            sections.append(current_section)
        
        if not sections:
            return 0.0
            
        if self.output_mode == 1:
            # 現区間の平均
            current_section_data = sections[-1]
            return np.mean(current_section_data) if current_section_data else 0.0
        elif self.output_mode == 2:
            # 前区間の平均
            if len(sections) >= 2:
                previous_section_data = sections[-2]
                return np.mean(previous_section_data) if previous_section_data else 0.0
            else:
                return 0.0
        
        return 0.0

class SSFunction(BasePKGFunction):
    """
    SS関数 - SPECIFIED_SHUKI（指定周期関数）
    
    メモファイルから抽出:
    - 周期特定（設定ファイル上で指定したトリガーが成立したタイミングで最終成立周期を保持して、常時出力する）
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        self.last_established_period = 0
        self.trigger_conditions = []
        
    def execute(self, data: Dict[str, Any]) -> int:
        """SS関数実行"""
        trigger_signals = data.get('trigger_signals', [])
        period_candidates = data.get('period_candidates', [10, 15, 30, 45, 60, 90, 180])
        current_period_data = data.get('current_period_data', {})
        
        # トリガー成立の確認
        trigger_established = self._check_trigger_establishment(trigger_signals, current_period_data)
        
        if trigger_established:
            # 最適な周期を特定
            optimal_period = self._determine_optimal_period(
                period_candidates, current_period_data
            )
            self.last_established_period = optimal_period
            
        return self.last_established_period
    
    def _check_trigger_establishment(self, trigger_signals: List, current_data: Dict) -> bool:
        """トリガー成立の確認"""
        if not trigger_signals:
            return False
            
        # 複数のトリガー条件をチェック
        established_triggers = 0
        for signal in trigger_signals:
            if isinstance(signal, dict):
                # 複合条件の場合
                if signal.get('value', 0) > signal.get('threshold', 0):
                    established_triggers += 1
            elif signal:
                # 単純なブール値の場合
                established_triggers += 1
                
        # 過半数のトリガーが成立した場合
        return established_triggers > len(trigger_signals) / 2
    
    def _determine_optimal_period(self, candidates: List[int], data: Dict) -> int:
        """最適周期の決定"""
        if not candidates:
            return 10  # デフォルト
            
        # 現在の市場状況に基づいて最適周期を選択
        volatility = data.get('volatility', 0.5)
        trend_strength = data.get('trend_strength', 0.5)
        
        # ボラティリティが高い場合は短い周期、低い場合は長い周期
        if volatility > 0.7:
            # 高ボラティリティ → 短期周期
            return min(candidates)
        elif volatility < 0.3:
            # 低ボラティリティ → 長期周期
            return max(candidates)
        else:
            # 中程度 → 中間周期
            sorted_candidates = sorted(candidates)
            mid_index = len(sorted_candidates) // 2
            return sorted_candidates[mid_index]

class IFunction(BasePKGFunction):
    """
    I関数 - IDEAL関数（理想値計算）
    
    メモファイルから抽出:
    - 素材として指定された上下の区間において、最小値と最大値を算出し、それぞれの足で方向を出す
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """I関数実行"""
        price_data = data.get('price_data', [])
        upper_range = data.get('upper_range', [])
        lower_range = data.get('lower_range', [])
        
        if not price_data:
            return {'direction': 0, 'ideal_high': 0, 'ideal_low': 0}
            
        # 上下区間の設定
        if not upper_range and not lower_range:
            # 価格データから自動的に区間を設定
            highs = [bar.high if hasattr(bar, 'high') else bar for bar in price_data]
            lows = [bar.low if hasattr(bar, 'low') else bar for bar in price_data]
            
            upper_range = highs
            lower_range = lows
        
        # 理想的な高値・安値の計算
        ideal_high = max(upper_range) if upper_range else 0
        ideal_low = min(lower_range) if lower_range else 0
        
        # 現在価格の取得
        current_price = price_data[-1]
        if hasattr(current_price, 'close'):
            current_price = current_price.close
        
        # 方向判定
        range_middle = (ideal_high + ideal_low) / 2 if ideal_high != ideal_low else ideal_high
        
        if current_price > range_middle:
            direction = 1  # 上方向
        elif current_price < range_middle:
            direction = 2  # 下方向
        else:
            direction = 0  # 中立
            
        return {
            'direction': direction,
            'ideal_high': ideal_high,
            'ideal_low': ideal_low,
            'range_middle': range_middle,
            'current_position': (current_price - ideal_low) / (ideal_high - ideal_low) if ideal_high != ideal_low else 0.5
        }

class ROFunction(BasePKGFunction):
    """
    RO関数 - ROUNDDOWN関数
    
    メモファイルから抽出:
    - 2ステップ構成
    - ステップ1: Z(2)で材料から0.49999を引く
    - ステップ2: 四捨五入処理
    """
    
    def __init__(self, pkg_id: PKGId):
        super().__init__(pkg_id)
        
    def execute(self, data: Dict[str, Any]) -> int:
        """RO関数実行"""
        input_value = data.get('input_value', 0.0)
        
        # ステップ1: 0.49999を引く（Z(2)相当）
        adjusted_value = float(input_value) - 0.49999
        
        # ステップ2: 四捨五入処理（実際にはROUNDDOWN）
        result = math.floor(adjusted_value) if adjusted_value >= 0 else math.ceil(adjusted_value)
        
        return int(result)

class NLFunction(BasePKGFunction):
    """
    NL関数 - LINEAR_LINE（線形補間）
    
    メモファイルから抽出:
    - 隣接線の価格（基準線との予知評価用）
    - 隣接線の周期（周期特定用）
    - モード: 1=直近の上価格, 2=直近の下価格, 3=直近の上周期, 4=直近の下周期
    """
    
    def __init__(self, pkg_id: PKGId, mode: int = 1):
        super().__init__(pkg_id)
        self.mode = mode
        
    def execute(self, data: Dict[str, Any]) -> Union[float, int]:
        """NL関数実行"""
        price_data = data.get('price_data', [])
        period_data = data.get('period_data', [])
        baseline = data.get('baseline', 0.0)
        
        if self.mode == 1:
            # 直近の上価格
            return self._get_nearest_upper_price(price_data, baseline)
        elif self.mode == 2:
            # 直近の下価格
            return self._get_nearest_lower_price(price_data, baseline)
        elif self.mode == 3:
            # 直近の上周期
            return self._get_nearest_upper_period(period_data, baseline)
        elif self.mode == 4:
            # 直近の下周期
            return self._get_nearest_lower_period(period_data, baseline)
        else:
            return 0.0
    
    def _get_nearest_upper_price(self, price_data: List, baseline: float) -> float:
        """基準線より上の最も近い価格"""
        upper_prices = [price for price in price_data if price > baseline]
        return min(upper_prices) if upper_prices else baseline
    
    def _get_nearest_lower_price(self, price_data: List, baseline: float) -> float:
        """基準線より下の最も近い価格"""
        lower_prices = [price for price in price_data if price < baseline]
        return max(lower_prices) if lower_prices else baseline
    
    def _get_nearest_upper_period(self, period_data: List, baseline: float) -> int:
        """基準値より上の最も近い周期"""
        upper_periods = [period for period in period_data if period > baseline]
        return min(upper_periods) if upper_periods else int(baseline)
    
    def _get_nearest_lower_period(self, period_data: List, baseline: float) -> int:
        """基準値より下の最も近い周期"""
        lower_periods = [period for period in period_data if period < baseline]
        return max(lower_periods) if lower_periods else int(baseline)

# PKG関数ファクトリー
class BasicPKGFunctionFactory:
    """基本PKG関数のファクトリークラス"""
    
    @staticmethod
    def create_function(function_type: str, pkg_id: PKGId, **kwargs) -> BasePKGFunction:
        """PKG関数の生成"""
        function_map = {
            'Z': ZFunction,
            'SL': SLFunction,
            'MN': MNFunction,
            'CO': COFunction,
            'SG': SGFunction,
            'AS': ASFunction,
            'SS': SSFunction,
            'I': IFunction,
            'RO': ROFunction,
            'NL': NLFunction
        }
        
        if function_type not in function_map:
            raise ValueError(f"Unknown function type: {function_type}")
            
        function_class = function_map[function_type]
        return function_class(pkg_id, **kwargs)

# 使用例とテスト用のサンプルデータ
if __name__ == "__main__":
    # テスト用PKG ID
    test_pkg_id = PKGId(
        timeframe=TimeFrame.M15,
        period=Period.COMMON,
        currency=Currency.USDJPY,
        layer=1,
        sequence=1
    )
    
    # Z(2)関数のテスト
    z_func = ZFunction(test_pkg_id, operation_type=2)
    z_result = z_func.execute({'inputs': [110.50, 110.00]})
    print(f"Z(2) result: {z_result}")  # 0.5
    
    # SL関数のテスト
    sl_func = SLFunction(test_pkg_id)
    sl_result = sl_func.execute({
        'condition': True,
        'options': ['買い', '売り'],
        'default': '待機'
    })
    print(f"SL result: {sl_result}")  # '買い'
    
    # CO関数のテスト
    co_func = COFunction(test_pkg_id)
    co_result = co_func.execute({'target_code': 5})
    print(f"CO result: {co_result}")  # 15 (5+4+3+2+1)