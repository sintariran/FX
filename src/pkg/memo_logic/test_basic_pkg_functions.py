"""
Week 6: 基本PKG関数のTDDテスト
t_wada式のTest-Driven Developmentでメモファイルベースの仕様を検証

メモファイル仕様の検証:
- 20200514_エクセル関数のパッケージ照合.txt
- 20200115_オペレーションロジックまとめ.txt
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any

from .core_pkg_functions import PKGId, TimeFrame, Currency, Period, MarketData
from .basic_pkg_functions import (
    ZFunction, SLFunction, MNFunction, COFunction, 
    SGFunction, ASFunction, SSFunction, IFunction, 
    ROFunction, NLFunction, BasicPKGFunctionFactory
)

class TestPKGIds:
    """テスト用PKG IDの定義"""
    
    @staticmethod
    def create_test_pkg_id(layer: int = 1, sequence: int = 1) -> PKGId:
        return PKGId(
            timeframe=TimeFrame.M15,
            period=Period.COMMON,
            currency=Currency.USDJPY,
            layer=layer,
            sequence=sequence
        )

class TestZFunction:
    """Z関数のTDDテスト"""
    
    def test_z2_basic_subtraction(self):
        """
        テスト: Z(2)基本減算
        メモ仕様: 2入力減算関数
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        z_func = ZFunction(pkg_id, operation_type=2)
        
        # Act
        result = z_func.execute({'inputs': [110.50, 110.00]})
        
        # Assert
        assert result == 0.5
        
    def test_z2_negative_result(self):
        """
        テスト: Z(2)負の結果
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        z_func = ZFunction(pkg_id, operation_type=2)
        
        # Act
        result = z_func.execute({'inputs': [110.00, 110.50]})
        
        # Assert
        assert result == -0.5
        
    def test_z2_insufficient_inputs(self):
        """
        テスト: Z(2)入力不足
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        z_func = ZFunction(pkg_id, operation_type=2)
        
        # Act
        result = z_func.execute({'inputs': [110.50]})
        
        # Assert
        assert result == 0.0  # 入力不足時はデフォルト値
        
    def test_z8_mod_operation(self):
        """
        テスト: Z(8)mod演算
        メモ仕様: 8入力mod演算
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        z_func = ZFunction(pkg_id, operation_type=8)
        
        # Act
        result = z_func.execute({'inputs': [1, 2, 3, 4, 5, 6, 7, 8]})
        
        # Assert
        expected = sum([1, 2, 3, 4, 5, 6, 7, 8]) % 8  # 36 % 8 = 4
        assert result == expected
        
    def test_z8_insufficient_inputs_padding(self):
        """
        テスト: Z(8)入力不足時のパディング
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        z_func = ZFunction(pkg_id, operation_type=8)
        
        # Act
        result = z_func.execute({'inputs': [1, 2, 3]})
        
        # Assert
        expected = sum([1, 2, 3, 0, 0, 0, 0, 0]) % 8  # 6 % 8 = 6
        assert result == expected

class TestSLFunction:
    """SL関数のTDDテスト"""
    
    def test_sl_basic_true_condition(self):
        """
        テスト: SL基本動作（真条件）
        メモ仕様: SELECT関数（可変入力）
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        sl_func = SLFunction(pkg_id)
        
        # Act
        result = sl_func.execute({
            'condition': True,
            'options': ['買い', '売り'],
            'default': '待機'
        })
        
        # Assert
        assert result == '買い'
        
    def test_sl_basic_false_condition(self):
        """
        テスト: SL基本動作（偽条件）
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        sl_func = SLFunction(pkg_id)
        
        # Act
        result = sl_func.execute({
            'condition': False,
            'options': ['買い', '売り'],
            'default': '待機'
        })
        
        # Assert
        assert result == '売り'
        
    def test_sl_numeric_condition_nonzero(self):
        """
        テスト: SL数値条件（非ゼロ）
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        sl_func = SLFunction(pkg_id)
        
        # Act
        result = sl_func.execute({
            'condition': 1.5,
            'options': [1, -1],
            'default': 0
        })
        
        # Assert
        assert result == 1
        
    def test_sl_numeric_condition_zero(self):
        """
        テスト: SL数値条件（ゼロ）
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        sl_func = SLFunction(pkg_id)
        
        # Act
        result = sl_func.execute({
            'condition': 0,
            'options': [1, -1],
            'default': 0
        })
        
        # Assert
        assert result == -1
        
    def test_sl_insufficient_options(self):
        """
        テスト: SLオプション不足
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        sl_func = SLFunction(pkg_id)
        
        # Act
        result = sl_func.execute({
            'condition': False,
            'options': ['買い'],  # 1つしかない
            'default': '待機'
        })
        
        # Assert
        assert result == '待機'  # デフォルト値が返される

class TestMNFunction:
    """MN関数のTDDテスト"""
    
    def test_mn_mode1_current_time(self):
        """
        テスト: MN モード1（現在時刻）
        メモ仕様: 現在時刻から算出
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        mn_func = MNFunction(pkg_id, mode=1)
        test_time = datetime(2024, 1, 15, 14, 35, 20)
        
        # Act
        result = mn_func.execute({'current_time': test_time})
        
        # Assert
        assert result == 35
        
    def test_mn_mode2_package_time(self):
        """
        テスト: MN モード2（パッケージ時刻）
        メモ仕様: 条件1に記載するパッケージが持っている時刻データから算出
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        mn_func = MNFunction(pkg_id, mode=2)
        test_time = pd.Timestamp('2024-01-15 14:42:30')
        
        # Act
        result = mn_func.execute({'time_data': test_time})
        
        # Assert
        assert result == 42
        
    def test_mn_mode2_market_data(self):
        """
        テスト: MN モード2（MarketData）
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        mn_func = MNFunction(pkg_id, mode=2)
        market_data = MarketData(
            timestamp=pd.Timestamp('2024-01-15 09:27:45'),
            open=110.0, high=110.5, low=109.8, close=110.2, volume=1000
        )
        
        # Act
        result = mn_func.execute({'time_data': market_data})
        
        # Assert
        assert result == 27

class TestCOFunction:
    """CO関数のTDDテスト"""
    
    def test_co_memo_specification_sum_sequence(self):
        """
        テスト: COメモ仕様（連続和）
        メモ仕様: 5が指定されたら、5+4+3+2+1の値を出力する
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        co_func = COFunction(pkg_id)
        
        # Act
        result = co_func.execute({'target_code': 5})
        
        # Assert
        expected = 5 + 4 + 3 + 2 + 1  # 15
        assert result == expected
        
    def test_co_memo_specification_different_numbers(self):
        """
        テスト: COメモ仕様（異なる数値）
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        co_func = COFunction(pkg_id)
        
        test_cases = [
            (3, 3 + 2 + 1),  # 6
            (1, 1),          # 1
            (7, 7 + 6 + 5 + 4 + 3 + 2 + 1)  # 28
        ]
        
        for input_val, expected in test_cases:
            # Act
            result = co_func.execute({'target_code': input_val})
            
            # Assert
            assert result == expected, f"Input {input_val} should return {expected}, got {result}"
    
    def test_co_traditional_count_mode(self):
        """
        テスト: CO従来カウントモード
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        co_func = COFunction(pkg_id)
        
        # Act
        result = co_func.execute({
            'time_series': [1, 2, 1, 1, 2, 1],
            'target_code': 1,
            'window_size': 6
        })
        
        # Assert
        assert result == 4  # 1が4回出現

class TestSGFunction:
    """SG関数のTDDテスト"""
    
    def test_sg_basic_section_sum(self):
        """
        テスト: SG基本区間合計
        メモ仕様: 区間毎の値の和算をする
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        sg_func = SGFunction(pkg_id)
        
        # Act
        result = sg_func.execute({
            'section_indicators': [1, 1, 1, 2, 2, 2, 1, 1],
            'values_to_sum': [10, 20, 30, 15, 25, 35, 5, 15]
        })
        
        # Assert
        # 最後の区間は [1, 1] で値は [5, 15]
        expected = 5 + 15  # 20
        assert result == expected
        
    def test_sg_section_transition(self):
        """
        テスト: SG区間切替り
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        sg_func = SGFunction(pkg_id)
        
        # Act
        result = sg_func.execute({
            'section_indicators': [1, 1, 2, 2, 1],
            'values_to_sum': [10, 20, 15, 25, 5]
        })
        
        # Assert
        # 最後の区間は [1] で値は [5]
        expected = 5
        assert result == expected

class TestASFunction:
    """AS関数のTDDテスト"""
    
    def test_as_current_section_average(self):
        """
        テスト: AS現区間平均
        メモ仕様: 出力に1を指定した場合は現区間の平均を出す
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        as_func = ASFunction(pkg_id, output_mode=1)
        
        # Act
        result = as_func.execute({
            'section_indicators': [1, 1, 1, 2, 2, 2],
            'price_values': [110.0, 110.5, 111.0, 109.5, 110.0, 110.5]
        })
        
        # Assert
        # 現区間（最後の区間）は [2, 2, 2] で価格は [109.5, 110.0, 110.5]
        expected = (109.5 + 110.0 + 110.5) / 3  # 110.0
        assert abs(result - expected) < 0.001
        
    def test_as_previous_section_average(self):
        """
        テスト: AS前区間平均
        メモ仕様: 出力に2を指定した場合は1つ前区間の平均を出す
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        as_func = ASFunction(pkg_id, output_mode=2)
        
        # Act
        result = as_func.execute({
            'section_indicators': [1, 1, 1, 2, 2, 2],
            'price_values': [110.0, 110.5, 111.0, 109.5, 110.0, 110.5]
        })
        
        # Assert
        # 前区間は [1, 1, 1] で価格は [110.0, 110.5, 111.0]
        expected = (110.0 + 110.5 + 111.0) / 3  # 110.5
        assert abs(result - expected) < 0.001

class TestROFunction:
    """RO関数のTDDテスト"""
    
    def test_ro_positive_rounddown(self):
        """
        テスト: RO正の値のROUNDDOWN
        メモ仕様: 材料から0.49999を引いて四捨五入処理
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        ro_func = ROFunction(pkg_id)
        
        # Act & Assert
        test_cases = [
            (1.9, 1),    # 1.9 - 0.49999 = 1.40001 → floor = 1
            (2.7, 2),    # 2.7 - 0.49999 = 2.20001 → floor = 2
            (0.3, 0),    # 0.3 - 0.49999 = -0.19999 → ceil = 0
            (5.0, 4),    # 5.0 - 0.49999 = 4.50001 → floor = 4
        ]
        
        for input_val, expected in test_cases:
            result = ro_func.execute({'input_value': input_val})
            assert result == expected, f"Input {input_val} should return {expected}, got {result}"

class TestIFunction:
    """I関数のTDDテスト"""
    
    def test_i_ideal_value_calculation(self):
        """
        テスト: I関数理想値計算
        メモ仕様: 最小値と最大値を算出し、それぞれの足で方向を出す
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        i_func = IFunction(pkg_id)
        
        # Act
        result = i_func.execute({
            'upper_range': [111.0, 111.5, 112.0, 111.2],
            'lower_range': [109.0, 109.5, 108.8, 109.3],
            'price_data': [110.5]  # 現在価格
        })
        
        # Assert
        assert result['ideal_high'] == 112.0
        assert result['ideal_low'] == 108.8
        assert result['range_middle'] == (112.0 + 108.8) / 2  # 110.4
        assert result['direction'] == 1  # 110.5 > 110.4 なので上方向

class TestBasicPKGFunctionFactory:
    """PKG関数ファクトリーのTDDテスト"""
    
    def test_factory_creates_z_function(self):
        """
        テスト: ファクトリーでZ関数生成
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        
        # Act
        z_func = BasicPKGFunctionFactory.create_function('Z', pkg_id, operation_type=2)
        
        # Assert
        assert isinstance(z_func, ZFunction)
        assert z_func.operation_type == 2
        
    def test_factory_creates_all_function_types(self):
        """
        テスト: ファクトリーで全関数タイプ生成
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        expected_types = ['Z', 'SL', 'MN', 'CO', 'SG', 'AS', 'SS', 'I', 'RO', 'NL']
        
        # Act & Assert
        for func_type in expected_types:
            func = BasicPKGFunctionFactory.create_function(func_type, pkg_id)
            assert func is not None
            assert hasattr(func, 'execute')
            
    def test_factory_unknown_function_type(self):
        """
        テスト: ファクトリー未知関数タイプ
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Unknown function type"):
            BasicPKGFunctionFactory.create_function('UNKNOWN', pkg_id)

# 統合テスト
class TestPKGFunctionIntegration:
    """PKG関数統合テスト"""
    
    def test_excel_function_chain_match_index(self):
        """
        テスト: Excel関数チェーン（MATCH→INDEX）
        メモ仕様: MATCHとINDEXの2ステップ構成
        """
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        
        # Step1: X2タイプ（範囲指定ルートIDと条件1の一致判定）
        # 簡易実装: 条件が一致する場合のインデックスを返す
        match_condition = 2
        range_route_ids = [1, 2, 3, 2, 1]
        match_index = range_route_ids.index(match_condition) if match_condition in range_route_ids else -1
        
        # Step2: SLタイプ（一致判定結果に基づく出力値選定）
        sl_func = SLFunction(pkg_id)
        result = sl_func.execute({
            'condition': match_index >= 0,
            'options': [f'Route_{match_index}', 'No_Match'],
            'default': 'Error'
        })
        
        # Assert
        assert result == 'Route_1'  # インデックス1で見つかった
        
    def test_pkg_id_parsing_memo_format(self):
        """
        テスト: PKG ID解析（メモ形式）
        メモ仕様: [時間足][周期][通貨]^[階層]-[連番]
        例: 191^2-126 = 1分足, 周期なし, USDJPY, 第2階層, 126番
        """
        # Arrange & Act
        pkg_id = PKGId.parse("191^2-126")
        
        # Assert
        assert pkg_id.timeframe == TimeFrame.M1  # 1分足
        assert pkg_id.period == Period.COMMON    # 周期なし (9→COMMON)
        assert pkg_id.currency == Currency.USDJPY  # USDJPY
        assert pkg_id.layer == 2
        assert pkg_id.sequence == 126
        
    def test_memo_performance_target_simulation(self):
        """
        テスト: メモ性能目標シミュレーション
        メモ仕様: 全体19ms、もみ77ms、OP分岐101.3ms、オーバーシュート550.6ms、時間結合564.9ms
        """
        import time
        
        # Arrange
        pkg_id = TestPKGIds.create_test_pkg_id()
        functions = []
        
        # 複数の基本関数を作成
        for func_type in ['Z', 'SL', 'CO', 'AS']:
            func = BasicPKGFunctionFactory.create_function(func_type, pkg_id)
            functions.append(func)
        
        # Act - 性能測定
        start_time = time.time()
        
        for _ in range(100):  # 100回実行
            for func in functions:
                if isinstance(func, ZFunction):
                    func.execute({'inputs': [110.5, 110.0]})
                elif isinstance(func, SLFunction):
                    func.execute({'condition': True, 'options': [1, 0]})
                elif isinstance(func, COFunction):
                    func.execute({'target_code': 5})
                elif isinstance(func, ASFunction):
                    func.execute({
                        'section_indicators': [1, 1, 2, 2],
                        'price_values': [110.0, 110.5, 111.0, 110.8]
                    })
        
        execution_time = (time.time() - start_time) * 1000  # ms
        
        # Assert - 性能目標確認（緩い条件）
        assert execution_time < 100, f"Execution time {execution_time}ms should be under 100ms"

if __name__ == "__main__":
    # pytest実行例
    pytest.main([__file__, "-v", "--tb=short"])