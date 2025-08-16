#!/usr/bin/env python3
"""
Week 6: 基本PKG関数の簡易テスト実行
依存関係なしでt_wada式TDDを実践

使用方法:
python3 simple_test_pkg_functions.py
"""

import sys
import traceback
import time
from datetime import datetime
from typing import Any, Dict, List

# Mock pandas.Timestamp for testing
class MockTimestamp:
    def __init__(self, timestamp_str):
        # Simple timestamp parsing
        if isinstance(timestamp_str, str):
            if 'T' in timestamp_str:
                date_part, time_part = timestamp_str.split('T')
            else:
                parts = timestamp_str.split(' ')
                if len(parts) == 2:
                    date_part, time_part = parts
                else:
                    date_part = timestamp_str
                    time_part = "00:00:00"
            
            year, month, day = map(int, date_part.split('-'))
            hour, minute, second = map(int, time_part.split(':'))
            self._datetime = datetime(year, month, day, hour, minute, second)
        else:
            self._datetime = timestamp_str
    
    @property
    def minute(self):
        return self._datetime.minute

# Use mock instead of pandas
pd = type('MockPandas', (), {'Timestamp': MockTimestamp})()

# 相対インポートの調整
try:
    from .core_pkg_functions import PKGId, TimeFrame, Currency, Period, MarketData
    from .basic_pkg_functions import (
        ZFunction, SLFunction, MNFunction, COFunction, 
        SGFunction, ASFunction, SSFunction, IFunction, 
        ROFunction, NLFunction, BasicPKGFunctionFactory
    )
except ImportError:
    # 直接実行の場合
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from core_pkg_functions import PKGId, TimeFrame, Currency, Period, MarketData
    from basic_pkg_functions import (
        ZFunction, SLFunction, MNFunction, COFunction, 
        SGFunction, ASFunction, SSFunction, IFunction, 
        ROFunction, NLFunction, BasicPKGFunctionFactory
    )

class SimpleTestRunner:
    """簡易テストランナー"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def assert_equal(self, actual: Any, expected: Any, message: str = ""):
        """等価性アサーション"""
        try:
            if actual == expected:
                self.passed += 1
                print(f"✅ PASS: {message}")
                return True
            else:
                self.failed += 1
                error_msg = f"❌ FAIL: {message} - Expected: {expected}, Got: {actual}"
                print(error_msg)
                self.errors.append(error_msg)
                return False
        except Exception as e:
            self.failed += 1
            error_msg = f"💥 ERROR: {message} - {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False
            
    def assert_almost_equal(self, actual: float, expected: float, tolerance: float = 0.001, message: str = ""):
        """近似等価性アサーション"""
        try:
            if abs(actual - expected) < tolerance:
                self.passed += 1
                print(f"✅ PASS: {message}")
                return True
            else:
                self.failed += 1
                error_msg = f"❌ FAIL: {message} - Expected: {expected}, Got: {actual} (tolerance: {tolerance})"
                print(error_msg)
                self.errors.append(error_msg)
                return False
        except Exception as e:
            self.failed += 1
            error_msg = f"💥 ERROR: {message} - {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False
            
    def run_test(self, test_func, test_name: str):
        """個別テスト実行"""
        print(f"\n🧪 Running: {test_name}")
        try:
            test_func()
        except Exception as e:
            self.failed += 1
            error_msg = f"💥 ERROR in {test_name}: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            traceback.print_exc()
            
    def summary(self):
        """テスト結果サマリー"""
        total = self.passed + self.failed
        print(f"\n" + "="*50)
        print(f"📊 Test Summary:")
        print(f"   Total: {total}")
        print(f"   Passed: {self.passed} ✅")
        print(f"   Failed: {self.failed} ❌")
        print(f"   Success Rate: {(self.passed/total*100) if total > 0 else 0:.1f}%")
        
        if self.errors:
            print(f"\n🔍 Error Details:")
            for error in self.errors:
                print(f"   {error}")
                
        return self.failed == 0

def create_test_pkg_id(layer: int = 1, sequence: int = 1) -> PKGId:
    """テスト用PKG ID作成"""
    return PKGId(
        timeframe=TimeFrame.M15,
        period=Period.COMMON,
        currency=Currency.USDJPY,
        layer=layer,
        sequence=sequence
    )

def test_pkg_id_parsing_and_format(runner: SimpleTestRunner):
    """PKG ID解析とフォーマットのテスト"""
    
    # メモ仕様: 191^2-126 = 1分足, 周期なし, USDJPY, 第2階層, 126番
    pkg_id = PKGId.parse("191^2-126")
    
    runner.assert_equal(pkg_id.timeframe, TimeFrame.M1, "Timeframe parsing")
    runner.assert_equal(pkg_id.period, Period.COMMON, "Period parsing")
    runner.assert_equal(pkg_id.currency, Currency.USDJPY, "Currency parsing")
    runner.assert_equal(pkg_id.layer, 2, "Layer parsing")
    runner.assert_equal(pkg_id.sequence, 126, "Sequence parsing")
    
    # 文字列化テスト
    pkg_str = str(pkg_id)
    runner.assert_equal(pkg_str, "191^2-126", "PKG ID string representation")

def test_z_function_basic_operations(runner: SimpleTestRunner):
    """Z関数基本操作のテスト"""
    
    pkg_id = create_test_pkg_id()
    
    # Z(2) 減算テスト
    z2_func = ZFunction(pkg_id, operation_type=2)
    result = z2_func.execute({'inputs': [110.50, 110.00]})
    runner.assert_equal(result, 0.5, "Z(2) basic subtraction")
    
    # Z(2) 負の結果テスト
    result = z2_func.execute({'inputs': [110.00, 110.50]})
    runner.assert_equal(result, -0.5, "Z(2) negative result")
    
    # Z(2) 入力不足テスト
    result = z2_func.execute({'inputs': [110.50]})
    runner.assert_equal(result, 0.0, "Z(2) insufficient inputs")
    
    # Z(8) mod演算テスト
    z8_func = ZFunction(pkg_id, operation_type=8)
    result = z8_func.execute({'inputs': [1, 2, 3, 4, 5, 6, 7, 8]})
    expected = sum([1, 2, 3, 4, 5, 6, 7, 8]) % 8  # 36 % 8 = 4
    runner.assert_equal(result, expected, "Z(8) mod operation")

def test_sl_function_selection_logic(runner: SimpleTestRunner):
    """SL関数選択ロジックのテスト"""
    
    pkg_id = create_test_pkg_id()
    sl_func = SLFunction(pkg_id)
    
    # 真条件テスト
    result = sl_func.execute({
        'condition': True,
        'options': ['買い', '売り'],
        'default': '待機'
    })
    runner.assert_equal(result, '買い', "SL true condition")
    
    # 偽条件テスト
    result = sl_func.execute({
        'condition': False,
        'options': ['買い', '売り'],
        'default': '待機'
    })
    runner.assert_equal(result, '売り', "SL false condition")
    
    # 数値条件テスト（非ゼロ）
    result = sl_func.execute({
        'condition': 1.5,
        'options': [1, -1],
        'default': 0
    })
    runner.assert_equal(result, 1, "SL numeric condition (non-zero)")
    
    # 数値条件テスト（ゼロ）
    result = sl_func.execute({
        'condition': 0,
        'options': [1, -1],
        'default': 0
    })
    runner.assert_equal(result, -1, "SL numeric condition (zero)")

def test_mn_function_time_processing(runner: SimpleTestRunner):
    """MN関数時刻処理のテスト"""
    
    pkg_id = create_test_pkg_id()
    
    # モード1: 現在時刻
    mn_func = MNFunction(pkg_id, mode=1)
    test_time = datetime(2024, 1, 15, 14, 35, 20)
    result = mn_func.execute({'current_time': test_time})
    runner.assert_equal(result, 35, "MN mode 1 (current time)")
    
    # モード2: パッケージ時刻
    mn_func = MNFunction(pkg_id, mode=2)
    test_time = pd.Timestamp('2024-01-15 14:42:30')
    result = mn_func.execute({'time_data': test_time})
    runner.assert_equal(result, 42, "MN mode 2 (package time)")

def test_co_function_memo_specification(runner: SimpleTestRunner):
    """CO関数メモ仕様のテスト"""
    
    pkg_id = create_test_pkg_id()
    co_func = COFunction(pkg_id)
    
    # メモ仕様: 5が指定されたら、5+4+3+2+1の値を出力する
    result = co_func.execute({'target_code': 5})
    expected = 5 + 4 + 3 + 2 + 1  # 15
    runner.assert_equal(result, expected, "CO memo spec: sum sequence (5)")
    
    # 他の数値でもテスト
    test_cases = [
        (3, 3 + 2 + 1),  # 6
        (1, 1),          # 1
        (7, 7 + 6 + 5 + 4 + 3 + 2 + 1)  # 28
    ]
    
    for input_val, expected in test_cases:
        result = co_func.execute({'target_code': input_val})
        runner.assert_equal(result, expected, f"CO memo spec: sum sequence ({input_val})")

def test_sg_function_section_grouping(runner: SimpleTestRunner):
    """SG関数区間グループ化のテスト"""
    
    pkg_id = create_test_pkg_id()
    sg_func = SGFunction(pkg_id)
    
    # 基本区間合計テスト
    result = sg_func.execute({
        'section_indicators': [1, 1, 1, 2, 2, 2, 1, 1],
        'values_to_sum': [10, 20, 30, 15, 25, 35, 5, 15]
    })
    # 最後の区間は [1, 1] で値は [5, 15]
    expected = 5 + 15  # 20
    runner.assert_equal(result, expected, "SG section grouping basic")

def test_as_function_section_average(runner: SimpleTestRunner):
    """AS関数区間平均のテスト"""
    
    pkg_id = create_test_pkg_id()
    
    # 現区間平均
    as_func = ASFunction(pkg_id, output_mode=1)
    result = as_func.execute({
        'section_indicators': [1, 1, 1, 2, 2, 2],
        'price_values': [110.0, 110.5, 111.0, 109.5, 110.0, 110.5]
    })
    # 現区間（最後の区間）は [2, 2, 2] で価格は [109.5, 110.0, 110.5]
    expected = (109.5 + 110.0 + 110.5) / 3  # 110.0
    runner.assert_almost_equal(result, expected, message="AS current section average")
    
    # 前区間平均
    as_func = ASFunction(pkg_id, output_mode=2)
    result = as_func.execute({
        'section_indicators': [1, 1, 1, 2, 2, 2],
        'price_values': [110.0, 110.5, 111.0, 109.5, 110.0, 110.5]
    })
    # 前区間は [1, 1, 1] で価格は [110.0, 110.5, 111.0]
    expected = (110.0 + 110.5 + 111.0) / 3  # 110.5
    runner.assert_almost_equal(result, expected, message="AS previous section average")

def test_ro_function_rounddown(runner: SimpleTestRunner):
    """RO関数ROUNDDOWNのテスト"""
    
    pkg_id = create_test_pkg_id()
    ro_func = ROFunction(pkg_id)
    
    # メモ仕様: 材料から0.49999を引いて四捨五入処理
    test_cases = [
        (1.9, 1),    # 1.9 - 0.49999 = 1.40001 → floor = 1
        (2.7, 2),    # 2.7 - 0.49999 = 2.20001 → floor = 2
        (0.3, 0),    # 0.3 - 0.49999 = -0.19999 → ceil = 0
        (5.0, 4),    # 5.0 - 0.49999 = 4.50001 → floor = 4
    ]
    
    for input_val, expected in test_cases:
        result = ro_func.execute({'input_value': input_val})
        runner.assert_equal(result, expected, f"RO rounddown ({input_val})")

def test_i_function_ideal_calculation(runner: SimpleTestRunner):
    """I関数理想値計算のテスト"""
    
    pkg_id = create_test_pkg_id()
    i_func = IFunction(pkg_id)
    
    result = i_func.execute({
        'upper_range': [111.0, 111.5, 112.0, 111.2],
        'lower_range': [109.0, 109.5, 108.8, 109.3],
        'price_data': [110.5]  # 現在価格
    })
    
    runner.assert_equal(result['ideal_high'], 112.0, "I function ideal high")
    runner.assert_equal(result['ideal_low'], 108.8, "I function ideal low")
    runner.assert_almost_equal(result['range_middle'], (112.0 + 108.8) / 2, message="I function range middle")
    runner.assert_equal(result['direction'], 1, "I function direction (above middle)")

def test_pkg_function_factory(runner: SimpleTestRunner):
    """PKG関数ファクトリーのテスト"""
    
    pkg_id = create_test_pkg_id()
    
    # Z関数生成テスト
    z_func = BasicPKGFunctionFactory.create_function('Z', pkg_id, operation_type=2)
    runner.assert_equal(type(z_func).__name__, 'ZFunction', "Factory creates Z function")
    runner.assert_equal(z_func.operation_type, 2, "Factory Z function operation type")
    
    # 全関数タイプ生成テスト
    function_types = ['Z', 'SL', 'MN', 'CO', 'SG', 'AS', 'SS', 'I', 'RO', 'NL']
    for func_type in function_types:
        func = BasicPKGFunctionFactory.create_function(func_type, pkg_id)
        runner.assert_equal(hasattr(func, 'execute'), True, f"Factory creates {func_type} with execute method")

def test_excel_function_chain_integration(runner: SimpleTestRunner):
    """Excel関数チェーン統合テスト"""
    
    pkg_id = create_test_pkg_id()
    
    # メモ仕様: MATCHとINDEXの2ステップ構成をSLで模擬
    match_condition = 2
    range_route_ids = [1, 2, 3, 2, 1]
    
    # Step1: 一致判定
    match_index = range_route_ids.index(match_condition) if match_condition in range_route_ids else -1
    
    # Step2: SL関数で結果選択
    sl_func = SLFunction(pkg_id)
    result = sl_func.execute({
        'condition': match_index >= 0,
        'options': [f'Route_{match_index}', 'No_Match'],
        'default': 'Error'
    })
    
    runner.assert_equal(result, 'Route_1', "Excel function chain MATCH->INDEX simulation")

def test_performance_simulation(runner: SimpleTestRunner):
    """性能シミュレーションテスト"""
    
    pkg_id = create_test_pkg_id()
    
    # 複数の基本関数を作成
    functions = []
    for func_type in ['Z', 'SL', 'CO', 'AS']:
        func = BasicPKGFunctionFactory.create_function(func_type, pkg_id)
        functions.append((func_type, func))
    
    # 性能測定
    start_time = time.time()
    
    iterations = 100
    for _ in range(iterations):
        for func_type, func in functions:
            if func_type == 'Z':
                func.execute({'inputs': [110.5, 110.0]})
            elif func_type == 'SL':
                func.execute({'condition': True, 'options': [1, 0]})
            elif func_type == 'CO':
                func.execute({'target_code': 5})
            elif func_type == 'AS':
                func.execute({
                    'section_indicators': [1, 1, 2, 2],
                    'price_values': [110.0, 110.5, 111.0, 110.8]
                })
    
    execution_time = (time.time() - start_time) * 1000  # ms
    avg_time_per_call = execution_time / (iterations * len(functions))
    
    print(f"⏱️  Performance Results:")
    print(f"   Total time: {execution_time:.2f}ms")
    print(f"   Iterations: {iterations}")
    print(f"   Functions: {len(functions)}")
    print(f"   Avg time per call: {avg_time_per_call:.4f}ms")
    
    # メモ性能目標との比較（緩い条件）
    runner.assert_equal(execution_time < 100, True, f"Performance under 100ms (actual: {execution_time:.2f}ms)")

def main():
    """メイン実行関数"""
    
    print("🚀 Starting PKG Function TDD Tests")
    print("=" * 50)
    
    runner = SimpleTestRunner()
    
    # テスト実行
    test_functions = [
        (test_pkg_id_parsing_and_format, "PKG ID Parsing and Format"),
        (test_z_function_basic_operations, "Z Function Basic Operations"),
        (test_sl_function_selection_logic, "SL Function Selection Logic"),
        (test_mn_function_time_processing, "MN Function Time Processing"),
        (test_co_function_memo_specification, "CO Function Memo Specification"),
        (test_sg_function_section_grouping, "SG Function Section Grouping"),
        (test_as_function_section_average, "AS Function Section Average"),
        (test_ro_function_rounddown, "RO Function ROUNDDOWN"),
        (test_i_function_ideal_calculation, "I Function Ideal Calculation"),
        (test_pkg_function_factory, "PKG Function Factory"),
        (test_excel_function_chain_integration, "Excel Function Chain Integration"),
        (test_performance_simulation, "Performance Simulation"),
    ]
    
    for test_func, test_name in test_functions:
        runner.run_test(lambda: test_func(runner), test_name)
    
    # 結果サマリー
    success = runner.summary()
    
    print(f"\n🎯 TDD Cycle Status: {'✅ GREEN' if success else '❌ RED'}")
    
    if success:
        print("🎉 All tests passed! Ready for next iteration.")
    else:
        print("🔧 Some tests failed. Refactor and try again.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)