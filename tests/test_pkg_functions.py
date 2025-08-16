"""
PKG関数層のテスト（TDD）

t_wada式TDDアプローチ：
1. RED: 失敗するテストを書く
2. GREEN: テストを通す最小限の実装
3. REFACTOR: コードを改善

メモファイルから抽出した実際のケースをテストケース化
"""

import unittest
from typing import List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPKGFunctions(unittest.TestCase):
    """PKG関数のテストスイート"""
    
    def setUp(self):
        """各テストの前処理"""
        # 後で実装するPKGFunctionFactoryをインポート
        from src.pkg.function_factory import PKGFunctionFactory
        self.factory = PKGFunctionFactory()
    
    # ==========================================
    # Z関数（算術演算）のテスト
    # ==========================================
    
    def test_z2_function_returns_max_of_two_inputs(self):
        """Z(2)関数: 2入力の最大値を返す"""
        # Arrange
        z2_func = self.factory.create_function("Z", arity=2)
        inputs = {"input1": 1, "input2": 2}
        
        # Act
        result = z2_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 2)
    
    def test_z2_function_with_code_inputs(self):
        """Z(2)関数: コード値（1=買い、2=売り、3=待機）の最大値"""
        # Arrange
        z2_func = self.factory.create_function("Z", arity=2)
        inputs = {"input1": 1, "input2": 3}  # 買いと待機
        
        # Act
        result = z2_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 3)  # 待機が優先
    
    def test_z8_function_returns_max_of_eight_inputs(self):
        """Z(8)関数: 8入力の最大値を返す"""
        # Arrange
        z8_func = self.factory.create_function("Z", arity=8)
        inputs = {
            f"input{i}": i for i in range(1, 9)  # 1,2,3,4,5,6,7,8
        }
        
        # Act
        result = z8_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 8)
    
    # ==========================================
    # SL関数（選択論理）のテスト
    # ==========================================
    
    def test_sl_function_selects_based_on_condition(self):
        """SL関数: 条件に基づいて入力を選択"""
        # Arrange
        sl_func = self.factory.create_function("SL", arity=3)
        inputs = {
            "condition": 1,  # 1=true
            "if_true": 100,
            "if_false": 200
        }
        
        # Act
        result = sl_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 100)
    
    def test_sl_function_with_false_condition(self):
        """SL関数: 条件がfalseの場合"""
        # Arrange
        sl_func = self.factory.create_function("SL", arity=3)
        inputs = {
            "condition": 0,  # 0=false
            "if_true": 100,
            "if_false": 200
        }
        
        # Act
        result = sl_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 200)
    
    # ==========================================
    # OR関数（論理和）のテスト
    # ==========================================
    
    def test_or_function_with_any_true(self):
        """OR関数: いずれかがtrueなら1を返す"""
        # Arrange
        or_func = self.factory.create_function("OR", arity=4)
        inputs = {
            "input1": 0,
            "input2": 1,  # true
            "input3": 0,
            "input4": 0
        }
        
        # Act
        result = or_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 1)
    
    def test_or_function_with_all_false(self):
        """OR関数: すべてfalseなら0を返す"""
        # Arrange
        or_func = self.factory.create_function("OR", arity=4)
        inputs = {f"input{i}": 0 for i in range(1, 5)}
        
        # Act
        result = or_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 0)
    
    # ==========================================
    # AND関数（論理積）のテスト
    # ==========================================
    
    def test_and_function_with_all_true(self):
        """AND関数: すべてtrueなら1を返す"""
        # Arrange
        and_func = self.factory.create_function("AND", arity=4)
        inputs = {f"input{i}": 1 for i in range(1, 5)}
        
        # Act
        result = and_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 1)
    
    def test_and_function_with_any_false(self):
        """AND関数: いずれかがfalseなら0を返す"""
        # Arrange
        and_func = self.factory.create_function("AND", arity=4)
        inputs = {
            "input1": 1,
            "input2": 0,  # false
            "input3": 1,
            "input4": 1
        }
        
        # Act
        result = and_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 0)
    
    # ==========================================
    # CO関数（カウント）のテスト
    # ==========================================
    
    def test_co_function_counts_specific_value(self):
        """CO関数: 特定値の出現回数をカウント"""
        # Arrange
        co_func = self.factory.create_function("CO", arity=8, target_value=1)
        inputs = {
            "input1": 1,  # 買い
            "input2": 1,  # 買い
            "input3": 2,  # 売り
            "input4": 3,  # 待機
            "input5": 1,  # 買い
            "input6": 2,  # 売り
            "input7": 1,  # 買い
            "input8": 3   # 待機
        }
        
        # Act
        result = co_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 4)  # 1が4回出現
    
    def test_co_function_with_no_matches(self):
        """CO関数: マッチする値がない場合"""
        # Arrange
        co_func = self.factory.create_function("CO", arity=4, target_value=3)
        inputs = {f"input{i}": 1 for i in range(1, 5)}  # すべて1
        
        # Act
        result = co_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 0)
    
    # ==========================================
    # SG関数（符号）のテスト
    # ==========================================
    
    def test_sg_function_positive_value(self):
        """SG関数: 正の値は1を返す"""
        # Arrange
        sg_func = self.factory.create_function("SG", arity=1)
        inputs = {"input1": 10.5}
        
        # Act
        result = sg_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 1)
    
    def test_sg_function_negative_value(self):
        """SG関数: 負の値は-1を返す"""
        # Arrange
        sg_func = self.factory.create_function("SG", arity=1)
        inputs = {"input1": -5.3}
        
        # Act
        result = sg_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, -1)
    
    def test_sg_function_zero_value(self):
        """SG関数: ゼロは0を返す"""
        # Arrange
        sg_func = self.factory.create_function("SG", arity=1)
        inputs = {"input1": 0}
        
        # Act
        result = sg_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 0)
    
    # ==========================================
    # AS関数（合計）のテスト
    # ==========================================
    
    def test_as_function_sums_all_inputs(self):
        """AS関数: すべての入力値を合計"""
        # Arrange
        as_func = self.factory.create_function("AS", arity=4)
        inputs = {
            "input1": 10,
            "input2": 20,
            "input3": 30,
            "input4": 40
        }
        
        # Act
        result = as_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 100)
    
    def test_as_function_with_negative_values(self):
        """AS関数: 負の値も含む合計"""
        # Arrange
        as_func = self.factory.create_function("AS", arity=4)
        inputs = {
            "input1": 10,
            "input2": -5,
            "input3": 20,
            "input4": -3
        }
        
        # Act
        result = as_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 22)
    
    # ==========================================
    # MN関数（最小値）のテスト
    # ==========================================
    
    def test_mn_function_returns_minimum(self):
        """MN関数: 最小値を返す"""
        # Arrange
        mn_func = self.factory.create_function("MN", arity=4)
        inputs = {
            "input1": 5,
            "input2": 3,
            "input3": 7,
            "input4": 1
        }
        
        # Act
        result = mn_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 1)
    
    # ==========================================
    # 実際のメモケースのテスト
    # ==========================================
    
    def test_memo_case_dokyaku_judgment(self):
        """メモケース: 同逆判定のロジック再現"""
        # 191^2-126: MHIHとMJIHの方向判定
        # Arrange
        z2_func = self.factory.create_function("Z", arity=2)
        
        # MHIHが買い(1)、MJIHも買い(1)の場合
        inputs = {
            "mhih_direction": 1,
            "mjih_direction": 1
        }
        
        # Act
        result = z2_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 1)  # 同方向なので買い
    
    def test_memo_case_ikikaeri_pattern(self):
        """メモケース: 行帰パターンの判定"""
        # 行行パターン: 継続判定
        # Arrange
        and_func = self.factory.create_function("AND", arity=2)
        
        inputs = {
            "current_direction": 1,  # 現在買い
            "previous_direction": 1  # 前も買い
        }
        
        # Act
        result = and_func.evaluate(inputs)
        
        # Assert
        self.assertEqual(result, 1)  # 継続
    
    def test_memo_case_momi_detection(self):
        """メモケース: もみ状態の検出"""
        # レンジ幅が3pips未満の場合
        # Arrange
        sl_func = self.factory.create_function("SL", arity=3)
        
        inputs = {
            "range_width": 2.5,  # 2.5pips
            "threshold": 3.0,    # 3pips閾値
            "comparison": 1      # range < threshold
        }
        
        # Act（SLで条件判定を模擬）
        result = sl_func.evaluate({
            "condition": 1,  # 2.5 < 3.0 = true
            "if_true": 3,    # もみ状態 = 待機(3)
            "if_false": 0    # もみではない
        })
        
        # Assert
        self.assertEqual(result, 3)  # もみ状態なので待機


class TestPKGFunctionIntegration(unittest.TestCase):
    """PKG関数の統合テスト"""
    
    def setUp(self):
        from src.pkg.function_factory import PKGFunctionFactory
        from src.pkg.function_composer import FunctionComposer
        
        self.factory = PKGFunctionFactory()
        self.composer = FunctionComposer(self.factory)
    
    def test_complex_function_composition(self):
        """複雑な関数合成のテスト"""
        # 191^3-1: 複数の判定を統合
        # (Z(2) ∘ AND) ∘ OR
        
        # Arrange
        composition = self.composer.compose([
            ("Z", 2),
            ("AND", 2),
            ("OR", 2)
        ])
        
        inputs = {
            "signal1": 1,
            "signal2": 1,
            "signal3": 0,
            "signal4": 1
        }
        
        # Act
        result = composition.evaluate(inputs)
        
        # Assert
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()