"""
メモファイルの実際のケースをテスト（TDD）

メモファイルから抽出した具体的な取引ロジックを
テストケースとして実装し、正確性を検証
"""

import unittest
from typing import Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pkg.function_factory import PKGFunctionFactory
from src.pkg.function_composer import FunctionComposer


class TestMemoRealCases(unittest.TestCase):
    """メモファイルの実際のケースをテスト"""
    
    def setUp(self):
        self.factory = PKGFunctionFactory()
        self.composer = FunctionComposer(self.factory)
    
    def test_memo_20200115_dokyaku_case(self):
        """
        メモ: 20200115_オペレーションロジックまとめ.txt
        同逆判定の実際のケース
        
        MHIHとMJIHが揃った場合: 55.7%の勝率
        """
        # Arrange
        mhih_direction = 1  # 前足平均実勢: 買い方向
        mjih_direction = 1  # 今足実勢平均: 買い方向
        
        # 同方向の場合、そのまま方向を採用
        and_func = self.factory.create_function("AND", arity=2)
        
        # Act
        result = and_func.evaluate({
            "input1": mhih_direction,
            "input2": mjih_direction
        })
        
        # Assert
        self.assertEqual(result, 1)  # 両方買いなので買い判定
        # 実際の勝率55.7%はバックテストで検証
    
    def test_memo_20200330_ikikaeri_pattern(self):
        """
        メモ: 20200330_取引用の行帰の見方.txt
        行帰パターンの判定
        
        行行: 大きな流れで同方向継続
        """
        # Arrange - 行行パターンのシミュレート
        current_high = 150.50
        current_low = 150.30
        prev_high = 150.40
        prev_low = 150.20
        
        # 高値更新かつ安値更新 = 行行
        higher_high = 1 if current_high > prev_high else 0
        higher_low = 1 if current_low > prev_low else 0
        
        and_func = self.factory.create_function("AND", arity=2)
        
        # Act
        result = and_func.evaluate({
            "input1": higher_high,
            "input2": higher_low
        })
        
        # Assert
        self.assertEqual(result, 1)  # 行行パターン成立
    
    def test_memo_20200401_momi_detection(self):
        """
        メモ: 20200401_もみ検討.txt
        もみ状態の検出ロジック
        
        レンジ幅が3pips未満の場合はもみ状態
        """
        # Arrange
        range_high = 150.50
        range_low = 150.25
        range_width = range_high - range_low  # 0.25 = 25pips
        
        # 3pips = 0.03
        threshold = 0.03
        
        # range_width < threshold なら もみ状態(3:待機)
        sl_func = self.factory.create_function("SL", arity=3)
        
        # Act
        is_momi = 1 if range_width < threshold else 0
        result = sl_func.evaluate({
            "condition": is_momi,
            "if_true": 3,   # もみなら待機
            "if_false": 0   # もみでないなら判定継続
        })
        
        # Assert
        self.assertEqual(result, 0)  # 25pips > 3pipsなのでもみではない
    
    def test_memo_20200401_momi_true_case(self):
        """もみ状態が成立するケース"""
        # Arrange
        range_high = 150.020
        range_low = 150.005
        range_width = range_high - range_low  # 0.015 = 1.5pips
        
        threshold = 0.03  # 3pips
        
        sl_func = self.factory.create_function("SL", arity=3)
        
        # Act
        is_momi = 1 if range_width < threshold else 0
        result = sl_func.evaluate({
            "condition": is_momi,
            "if_true": 3,   # もみなら待機
            "if_false": 0   # もみでないなら判定継続
        })
        
        # Assert
        self.assertEqual(result, 3)  # 1.5pips < 3pipsなのでもみ状態→待機
    
    def test_memo_overshoot_detection(self):
        """
        オーバーシュート判定
        前足Os残足が今足換算で2以上
        """
        # Arrange
        os_remaining = 2.5  # Os残足
        current_conversion = 1.0  # 今足換算
        threshold = 2.0
        
        # オーバーシュート判定
        sg_func = self.factory.create_function("SG", arity=1)
        
        # Act
        overshoot_value = os_remaining / current_conversion - threshold
        result = sg_func.evaluate({"input1": overshoot_value})
        
        # Assert
        self.assertEqual(result, 1)  # 2.5 > 2.0 なのでオーバーシュート
    
    def test_memo_timeframe_coordination(self):
        """
        時間足連携
        15分足と5分足の方向が揃った場合の判定
        """
        # Arrange
        m15_direction = 1  # 15分足: 買い
        m5_direction = 1   # 5分足: 買い
        m1_direction = 2   # 1分足: 売り（逆行）
        
        # 上位時間足優先ロジック
        z_func = self.factory.create_function("Z", arity=2)
        and_func = self.factory.create_function("AND", arity=2)
        
        # Act
        # 15分と5分が揃っているか確認
        alignment = and_func.evaluate({
            "input1": m15_direction,
            "input2": m5_direction
        })
        
        # 揃っていれば上位時間足の方向を採用
        sl_func = self.factory.create_function("SL", arity=3)
        result = sl_func.evaluate({
            "condition": alignment,
            "if_true": m15_direction,
            "if_false": 3  # 揃っていなければ待機
        })
        
        # Assert
        self.assertEqual(result, 1)  # 15分と5分が揃っているので買い
    
    def test_memo_entry_conditions_all_met(self):
        """
        エントリー条件がすべて満たされるケース
        
        1. 前足平均足の陰陽確認
        2. 転換判断の評価足方向合致
        3. 周期の揃い成立
        4. オーバーシュート成立確認
        """
        # Arrange
        conditions = {
            "heikin_ashi_ok": 1,      # 平均足条件OK
            "direction_match": 1,      # 方向一致
            "period_alignment": 1,     # 周期揃い
            "overshoot_established": 1 # オーバーシュート成立
        }
        
        and_func = self.factory.create_function("AND", arity=4)
        
        # Act
        result = and_func.evaluate(conditions)
        
        # Assert
        self.assertEqual(result, 1)  # すべて満たすのでエントリー可能
    
    def test_memo_exit_condition_profit_taking(self):
        """
        利益確定条件
        1分の揃いと前足以前のOPFF揃い
        """
        # Arrange
        minute_alignment = 1     # 1分足揃い
        opff_alignment = 1       # OPFF揃い
        
        and_func = self.factory.create_function("AND", arity=2)
        
        # Act
        result = and_func.evaluate({
            "input1": minute_alignment,
            "input2": opff_alignment
        })
        
        # Assert
        self.assertEqual(result, 1)  # 利益確定条件成立
    
    def test_memo_hedge_condition(self):
        """
        ヘッジ条件の判定
        今足の周期揃い成立 & 平均足方向条件
        """
        # Arrange
        period_alignment = 1     # 周期揃い
        heikin_direction = 1     # 平均足買い方向
        main_position = 2        # メインポジション売り
        
        # ヘッジは逆方向なので
        is_hedge_needed = 1 if heikin_direction != main_position else 0
        
        and_func = self.factory.create_function("AND", arity=2)
        
        # Act
        result = and_func.evaluate({
            "input1": period_alignment,
            "input2": is_hedge_needed
        })
        
        # Assert
        self.assertEqual(result, 1)  # ヘッジ条件成立
    
    def test_memo_multiple_signals_priority(self):
        """
        複数シグナルの優先順位
        待機(3) > 売り(2) > 買い(1)
        """
        # Arrange
        signal1 = 1  # 買いシグナル
        signal2 = 3  # 待機シグナル
        signal3 = 2  # 売りシグナル
        signal4 = 1  # 買いシグナル
        
        z_func = self.factory.create_function("Z", arity=4)
        
        # Act
        result = z_func.evaluate({
            "input1": signal1,
            "input2": signal2,
            "input3": signal3,
            "input4": signal4
        })
        
        # Assert
        self.assertEqual(result, 3)  # 待機が最優先


class TestComplexMemoLogic(unittest.TestCase):
    """複雑なメモロジックの統合テスト"""
    
    def setUp(self):
        self.factory = PKGFunctionFactory()
        self.composer = FunctionComposer(self.factory)
    
    def test_complete_trading_decision_flow(self):
        """
        完全な取引判断フロー
        同逆判定 → 行帰判定 → もみ判定 → 最終判断
        """
        # このテストは実際の統合ロジック実装後に詳細化
        # 現時点では基本的な合成のみテスト
        
        # Arrange - 3段階の判定を合成
        composition = self.composer.compose([
            ("AND", 2),  # 同逆判定
            ("SL", 3),   # 条件分岐
            ("Z", 2)     # 最終統合
        ])
        
        inputs = {
            "dokyaku_signal": 1,
            "ikikaeri_signal": 1,
            "momi_signal": 0,
            "condition": 1,
            "if_true": 1,
            "if_false": 3
        }
        
        # Act
        result = composition.evaluate(inputs)
        
        # Assert
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()