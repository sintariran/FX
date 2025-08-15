#!/usr/bin/env python3
"""
Week 6: 基本PKG関数の簡易TDDテスト（依存関係なし版）
t_wada式TDDでメモファイル仕様を検証

実行方法:
python3 simple_pkg_test_runner.py
"""

import sys
import time
import math
from datetime import datetime
from typing import Any, Dict, List, Union
from enum import Enum

# ========================================
# 依存関係なしの基本実装
# ========================================

class TimeFrame(Enum):
    M1 = 1   # 1分足
    M5 = 2   # 5分足
    M15 = 3  # 15分足
    M30 = 4  # 30分足
    H1 = 5   # 1時間足
    H4 = 6   # 4時間足

class Currency(Enum):
    USDJPY = 1
    EURUSD = 2
    EURJPY = 3

class Period(Enum):
    COMMON = 9    # 共通（周期なし）
    PERIOD_10 = 10
    PERIOD_15 = 15
    PERIOD_30 = 30
    PERIOD_45 = 45
    PERIOD_60 = 60
    PERIOD_90 = 90
    PERIOD_180 = 180

class PKGId:
    def __init__(self, timeframe: TimeFrame, period: Period, currency: Currency, layer: int, sequence: int):
        self.timeframe = timeframe
        self.period = period
        self.currency = currency
        self.layer = layer
        self.sequence = sequence
    
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

# ========================================
# 基本PKG関数実装（簡略版）
# ========================================

class BasePKGFunction:
    def __init__(self, pkg_id: PKGId):
        self.pkg_id = pkg_id

class ZFunction(BasePKGFunction):
    def __init__(self, pkg_id: PKGId, operation_type: int = 2):
        super().__init__(pkg_id)
        self.operation_type = operation_type
        
    def execute(self, data: Dict[str, Any]) -> Union[float, int]:
        inputs = data.get('inputs', [])
        
        if self.operation_type == 2:
            return self._execute_z2(inputs)
        elif self.operation_type == 8:
            return self._execute_z8(inputs)
        else:
            return 0.0
    
    def _execute_z2(self, inputs: List[float]) -> float:
        if len(inputs) < 2:
            return 0.0
        return float(inputs[0] - inputs[1])
    
    def _execute_z8(self, inputs: List[float]) -> int:
        if len(inputs) < 8:
            inputs.extend([0.0] * (8 - len(inputs)))
        sum_val = sum(inputs[:8])
        return int(sum_val) % 8

class SLFunction(BasePKGFunction):
    def execute(self, data: Dict[str, Any]) -> Any:
        condition = data.get('condition', 0)
        options = data.get('options', [])
        default_value = data.get('default', 0)
        
        if not options:
            return default_value
            
        if isinstance(condition, bool):
            index = 0 if condition else 1
        elif isinstance(condition, (int, float)):
            index = 0 if condition != 0 else 1
        else:
            index = 1
            
        if index < len(options):
            return options[index]
        else:
            return default_value

class MNFunction(BasePKGFunction):
    def __init__(self, pkg_id: PKGId, mode: int = 1):
        super().__init__(pkg_id)
        self.mode = mode
        
    def execute(self, data: Dict[str, Any]) -> int:
        if self.mode == 1:
            current_time = data.get('current_time', datetime.now())
            if isinstance(current_time, datetime):
                return current_time.minute
            else:
                return datetime.now().minute
        elif self.mode == 2:
            time_data = data.get('time_data')
            if time_data and hasattr(time_data, 'minute'):
                return time_data.minute
        return 0

class COFunction(BasePKGFunction):
    def execute(self, data: Dict[str, Any]) -> int:
        time_series = data.get('time_series', [])
        target_code = data.get('target_code', 1)
        
        if not time_series and isinstance(target_code, (int, float)) and target_code > 0:
            # メモ仕様: 5が指定されたら、5+4+3+2+1の値を出力する
            return sum(range(1, int(target_code) + 1))
        
        # 通常のカウント処理
        window_size = data.get('window_size', len(time_series))
        recent_data = time_series[-window_size:] if window_size < len(time_series) else time_series
        return sum(1 for value in recent_data if value == target_code)

class ROFunction(BasePKGFunction):
    def execute(self, data: Dict[str, Any]) -> int:
        input_value = data.get('input_value', 0.0)
        
        # Excel ROUNDDOWN(value, 0)と同等: 0方向への切り捨て
        # 正の数: floor、負の数: ceil（絶対値が小さくなる方向）
        result = math.trunc(float(input_value))
        
        return int(result)

class BasicPKGFunctionFactory:
    @staticmethod
    def create_function(function_type: str, pkg_id: PKGId, **kwargs) -> BasePKGFunction:
        function_map = {
            'Z': ZFunction,
            'SL': SLFunction,
            'MN': MNFunction,
            'CO': COFunction,
            'RO': ROFunction,
        }
        
        if function_type not in function_map:
            raise ValueError(f"Unknown function type: {function_type}")
            
        function_class = function_map[function_type]
        return function_class(pkg_id, **kwargs)

# ========================================
# TDDテストランナー
# ========================================

class TDDTestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def assert_equal(self, actual: Any, expected: Any, message: str = ""):
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
        print(f"\n🧪 Running: {test_name}")
        try:
            test_func(self)
        except Exception as e:
            self.failed += 1
            error_msg = f"💥 ERROR in {test_name}: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            
    def summary(self):
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

# ========================================
# TDDテストケース
# ========================================

def create_test_pkg_id(layer: int = 1, sequence: int = 1) -> PKGId:
    return PKGId(TimeFrame.M15, Period.COMMON, Currency.USDJPY, layer, sequence)

def test_pkg_id_memo_specification(runner: TDDTestRunner):
    """
    テスト: PKG ID仕様（メモファイル基準）
    メモ仕様: 191^2-126 = 1分足, 周期なし(9), USDJPY, 第2階層, 126番
    """
    # Red: まず失敗するテストを書く
    pkg_id = PKGId.parse("191^2-126")
    
    runner.assert_equal(pkg_id.timeframe, TimeFrame.M1, "PKG ID: Timeframe (1分足)")
    runner.assert_equal(pkg_id.period, Period.COMMON, "PKG ID: Period (周期なし)")
    runner.assert_equal(pkg_id.currency, Currency.USDJPY, "PKG ID: Currency (USDJPY)")
    runner.assert_equal(pkg_id.layer, 2, "PKG ID: Layer (第2階層)")
    runner.assert_equal(pkg_id.sequence, 126, "PKG ID: Sequence (126番)")
    
    # 文字列化テスト
    pkg_str = str(pkg_id)
    runner.assert_equal(pkg_str, "191^2-126", "PKG ID: String representation")

def test_z_function_memo_specification(runner: TDDTestRunner):
    """
    テスト: Z関数仕様（メモファイル基準）
    メモ仕様: Z(2)=2入力減算関数, Z(8)=8入力mod演算
    """
    pkg_id = create_test_pkg_id()
    
    # Z(2) テスト
    z2_func = ZFunction(pkg_id, operation_type=2)
    result = z2_func.execute({'inputs': [110.50, 110.00]})
    runner.assert_equal(result, 0.5, "Z(2): Basic subtraction (110.50 - 110.00)")
    
    result = z2_func.execute({'inputs': [110.00, 110.50]})
    runner.assert_equal(result, -0.5, "Z(2): Negative result (110.00 - 110.50)")
    
    result = z2_func.execute({'inputs': [110.50]})
    runner.assert_equal(result, 0.0, "Z(2): Insufficient inputs handling")
    
    # Z(8) テスト
    z8_func = ZFunction(pkg_id, operation_type=8)
    result = z8_func.execute({'inputs': [1, 2, 3, 4, 5, 6, 7, 8]})
    expected = sum([1, 2, 3, 4, 5, 6, 7, 8]) % 8  # 36 % 8 = 4
    runner.assert_equal(result, expected, "Z(8): 8-input mod operation")
    
    result = z8_func.execute({'inputs': [1, 2, 3]})
    expected = sum([1, 2, 3, 0, 0, 0, 0, 0]) % 8  # 6 % 8 = 6
    runner.assert_equal(result, expected, "Z(8): Insufficient inputs with padding")

def test_sl_function_memo_specification(runner: TDDTestRunner):
    """
    テスト: SL関数仕様（メモファイル基準）
    メモ仕様: SELECT関数（可変入力）、範囲指定の行数分用意
    """
    pkg_id = create_test_pkg_id()
    sl_func = SLFunction(pkg_id)
    
    # 基本的な選択テスト
    result = sl_func.execute({
        'condition': True,
        'options': ['買い', '売り'],
        'default': '待機'
    })
    runner.assert_equal(result, '買い', "SL: True condition selects first option")
    
    result = sl_func.execute({
        'condition': False,
        'options': ['買い', '売り'],
        'default': '待機'
    })
    runner.assert_equal(result, '売り', "SL: False condition selects second option")
    
    # 数値条件テスト
    result = sl_func.execute({
        'condition': 1.5,
        'options': [1, -1],
        'default': 0
    })
    runner.assert_equal(result, 1, "SL: Non-zero numeric condition")
    
    result = sl_func.execute({
        'condition': 0,
        'options': [1, -1],
        'default': 0
    })
    runner.assert_equal(result, -1, "SL: Zero numeric condition")
    
    # オプション不足テスト
    result = sl_func.execute({
        'condition': False,
        'options': ['買い'],
        'default': '待機'
    })
    runner.assert_equal(result, '待機', "SL: Insufficient options returns default")

def test_mn_function_memo_specification(runner: TDDTestRunner):
    """
    テスト: MN関数仕様（メモファイル基準）
    メモ仕様: 時刻を分換算に置き換える関数
    """
    pkg_id = create_test_pkg_id()
    
    # モード1: 現在時刻
    mn_func = MNFunction(pkg_id, mode=1)
    test_time = datetime(2024, 1, 15, 14, 35, 20)
    result = mn_func.execute({'current_time': test_time})
    runner.assert_equal(result, 35, "MN Mode 1: Extract minutes from current time")
    
    # モード2: パッケージ時刻
    mn_func = MNFunction(pkg_id, mode=2)
    
    # Mock timestamp class for testing
    class MockTimestamp:
        def __init__(self, minute_val):
            self.minute = minute_val
    
    time_data = MockTimestamp(42)
    result = mn_func.execute({'time_data': time_data})
    runner.assert_equal(result, 42, "MN Mode 2: Extract minutes from package time data")

def test_co_function_memo_specification(runner: TDDTestRunner):
    """
    テスト: CO関数仕様（メモファイル基準）
    メモ仕様: 5が指定されたら、5+4+3+2+1の値を出力する
    """
    pkg_id = create_test_pkg_id()
    co_func = COFunction(pkg_id)
    
    # メモの核心仕様テスト
    result = co_func.execute({'target_code': 5})
    expected = 5 + 4 + 3 + 2 + 1  # 15
    runner.assert_equal(result, expected, "CO: Memo spec - sum sequence for 5")
    
    # 他の値でのテスト
    test_cases = [
        (1, 1),                              # 1
        (3, 3 + 2 + 1),                     # 6
        (7, 7 + 6 + 5 + 4 + 3 + 2 + 1),    # 28
    ]
    
    for input_val, expected in test_cases:
        result = co_func.execute({'target_code': input_val})
        runner.assert_equal(result, expected, f"CO: Sum sequence for {input_val}")
    
    # 従来のカウント機能テスト
    result = co_func.execute({
        'time_series': [1, 2, 1, 1, 2, 1],
        'target_code': 1,
        'window_size': 6
    })
    runner.assert_equal(result, 4, "CO: Traditional count mode")

def test_ro_function_memo_specification(runner: TDDTestRunner):
    """
    テスト: RO関数仕様（Excel ROUNDDOWN準拠）
    ExcelのROUNDDOWN(value, 0)と同等: 0方向への切り捨て
    """
    pkg_id = create_test_pkg_id()
    ro_func = ROFunction(pkg_id)
    
    # Excel ROUNDDOWN仕様のテストケース
    test_cases = [
        # 正の数: 小数点以下切り捨て
        (1.9, 1),     # 1.9 → 1
        (2.7, 2),     # 2.7 → 2
        (0.3, 0),     # 0.3 → 0
        (5.0, 5),     # 5.0 → 5（変更: 整数はそのまま）
        (0.99999, 0), # 0.99999 → 0
        
        # 負の数: 0方向への切り捨て（絶対値が小さくなる方向）
        (-1.9, -1),   # -1.9 → -1（Excel準拠）
        (-2.7, -2),   # -2.7 → -2（Excel準拠）
        (-0.3, 0),    # -0.3 → 0
        (-5.0, -5),   # -5.0 → -5
    ]
    
    for input_val, expected in test_cases:
        result = ro_func.execute({'input_value': input_val})
        runner.assert_equal(result, expected, f"RO: Excel ROUNDDOWN ({input_val})")

def test_pkg_factory_memo_integration(runner: TDDTestRunner):
    """
    テスト: PKG ファクトリー統合（メモファイル基準）
    メモ仕様: エクセル関数のパッケージ照合での関数生成
    """
    pkg_id = create_test_pkg_id()
    
    # 基本関数生成テスト
    function_types = ['Z', 'SL', 'MN', 'CO', 'RO']
    
    for func_type in function_types:
        func = BasicPKGFunctionFactory.create_function(func_type, pkg_id)
        runner.assert_equal(hasattr(func, 'execute'), True, f"Factory: {func_type} has execute method")
    
    # Z関数の詳細パラメータテスト
    z_func = BasicPKGFunctionFactory.create_function('Z', pkg_id, operation_type=8)
    runner.assert_equal(hasattr(z_func, 'operation_type'), True, "Factory: Z function with parameters")
    runner.assert_equal(z_func.operation_type, 8, "Factory: Z function operation_type parameter")
    
    # 未知の関数タイプテスト
    try:
        BasicPKGFunctionFactory.create_function('UNKNOWN', pkg_id)
        runner.assert_equal(False, True, "Factory: Should raise error for unknown type")
    except ValueError:
        runner.assert_equal(True, True, "Factory: Correctly raises error for unknown type")

def test_excel_function_chain_memo_integration(runner: TDDTestRunner):
    """
    テスト: Excel関数チェーン統合（メモファイル基準）
    メモ仕様: MATCH→INDEXの2ステップ構成
    """
    pkg_id = create_test_pkg_id()
    
    # メモ仕様: MATCHとINDEXの2ステップ構成
    # Step1: X2タイプ（範囲指定ルートIDと条件1の一致判定）
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
    
    runner.assert_equal(result, 'Route_1', "Excel Chain: MATCH->INDEX simulation")
    
    # 失敗ケース
    match_condition = 99  # 存在しない値
    match_index = range_route_ids.index(match_condition) if match_condition in range_route_ids else -1
    result = sl_func.execute({
        'condition': match_index >= 0,
        'options': [f'Route_{match_index}', 'No_Match'],
        'default': 'Error'
    })
    
    runner.assert_equal(result, 'No_Match', "Excel Chain: MATCH->INDEX no match case")

def test_performance_memo_targets(runner: TDDTestRunner):
    """
    テスト: 性能目標（メモファイル基準）
    メモ仕様: 全体19ms、もみ77ms、OP分岐101.3ms、オーバーシュート550.6ms、時間結合564.9ms
    """
    pkg_id = create_test_pkg_id()
    
    # 基本関数群の作成
    functions = []
    for func_type in ['Z', 'SL', 'CO', 'RO']:
        func = BasicPKGFunctionFactory.create_function(func_type, pkg_id)
        functions.append((func_type, func))
    
    # パフォーマンス測定
    start_time = time.time()
    iterations = 1000
    
    for _ in range(iterations):
        for func_type, func in functions:
            if func_type == 'Z':
                func.execute({'inputs': [110.5, 110.0]})
            elif func_type == 'SL':
                func.execute({'condition': True, 'options': [1, 0]})
            elif func_type == 'CO':
                func.execute({'target_code': 5})
            elif func_type == 'RO':
                func.execute({'input_value': 1.9})
    
    execution_time = (time.time() - start_time) * 1000  # ms
    avg_time_per_call = execution_time / (iterations * len(functions))
    
    print(f"⏱️  Performance Results:")
    print(f"   Total time: {execution_time:.2f}ms")
    print(f"   Iterations: {iterations}")
    print(f"   Functions per iteration: {len(functions)}")
    print(f"   Total calls: {iterations * len(functions)}")
    print(f"   Avg time per call: {avg_time_per_call:.4f}ms")
    
    # 性能目標との比較
    # 基本関数は19ms目標内に収まる必要がある
    runner.assert_equal(execution_time < 50, True, f"Performance: Under 50ms target (actual: {execution_time:.2f}ms)")
    runner.assert_equal(avg_time_per_call < 0.1, True, f"Performance: Under 0.1ms per call (actual: {avg_time_per_call:.4f}ms)")

# ========================================
# メイン実行
# ========================================

def main():
    print("🚀 PKG Function TDD Test Suite")
    print("=" * 50)
    print("メモファイル仕様ベースのTest-Driven Development")
    print("参照メモ: 20200514_エクセル関数のパッケージ照合.txt")
    print("参照メモ: 20200115_オペレーションロジックまとめ.txt")
    print("=" * 50)
    
    runner = TDDTestRunner()
    
    # TDDテストサイクル実行
    test_functions = [
        (test_pkg_id_memo_specification, "PKG ID Memo Specification"),
        (test_z_function_memo_specification, "Z Function Memo Specification"),
        (test_sl_function_memo_specification, "SL Function Memo Specification"),
        (test_mn_function_memo_specification, "MN Function Memo Specification"),
        (test_co_function_memo_specification, "CO Function Memo Specification"),
        (test_ro_function_memo_specification, "RO Function Memo Specification"),
        (test_pkg_factory_memo_integration, "PKG Factory Memo Integration"),
        (test_excel_function_chain_memo_integration, "Excel Function Chain Memo Integration"),
        (test_performance_memo_targets, "Performance Memo Targets"),
    ]
    
    for test_func, test_name in test_functions:
        runner.run_test(test_func, test_name)
    
    # TDDサイクル結果
    success = runner.summary()
    
    print(f"\n🎯 TDD Cycle Status: {'🟢 GREEN (REFACTOR)' if success else '🔴 RED (REFACTOR NEEDED)'}")
    
    if success:
        print("🎉 All tests passed! Ready for next TDD iteration.")
        print("📝 Next steps:")
        print("   1. Refactor code for better design")
        print("   2. Add more complex PKG functions")
        print("   3. Integrate with DAG system")
    else:
        print("🔧 Some tests failed. Fix implementation and retry.")
        print("📝 TDD cycle: RED → GREEN → REFACTOR")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)