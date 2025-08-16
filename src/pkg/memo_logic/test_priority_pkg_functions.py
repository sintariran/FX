#!/usr/bin/env python3
"""
優先度高PKG関数のTDDテスト
t_wada式TDDに従った実装検証
"""

import unittest
import logging
import sys
import os

# パスを追加して相対インポートを可能にする
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core_pkg_functions import (
    PKGId, TimeFrame, Currency, Period,
    RatioFunction, OSumFunction, LeaderNumFunction,
    DualDirectionFunction, AbsIchiFunction, MinusFunction,
    PKGFunctionFactory
)

class TestPriorityPKGFunctions(unittest.TestCase):
    """優先度高PKG関数のテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        logging.basicConfig(level=logging.WARNING)
        self.pkg_id = PKGId(
            timeframe=TimeFrame.M15,
            period=Period.COMMON,
            currency=Currency.USDJPY,
            layer=1,
            sequence=1
        )
    
    def test_ratio_function_basic(self):
        """Ratio関数の基本テスト"""
        ratio_func = RatioFunction(self.pkg_id)
        
        # 正常ケース: 分子/分母の計算
        data = {'inputs': [10.0, 5.0, 3.0, 2.0]}  # 10 / (5+3+2) = 1.0
        result = ratio_func.execute(data)
        self.assertEqual(result, 1.0)
        
        # ゼロ除算回避テスト
        data = {'inputs': [10.0, 0.0, 0.0]}
        result = ratio_func.execute(data)
        self.assertEqual(result, 0.0)
        
        # 入力不足テスト
        data = {'inputs': [10.0]}
        result = ratio_func.execute(data)
        self.assertEqual(result, 0.0)
        
        # None値処理テスト
        data = {'inputs': [10.0, None, 5.0, None]}
        result = ratio_func.execute(data)
        self.assertEqual(result, 2.0)  # 10 / 5 = 2.0
    
    def test_osum_function_basic(self):
        """OSum関数の基本テスト"""
        osum_func = OSumFunction(self.pkg_id)
        
        # 正常ケース: 合計計算
        data = {'inputs': [1.0, 2.0, 3.0, 4.0]}
        result = osum_func.execute(data)
        self.assertEqual(result, 10.0)
        
        # 空入力テスト
        data = {'inputs': []}
        result = osum_func.execute(data)
        self.assertEqual(result, 0.0)
        
        # None値処理テスト
        data = {'inputs': [1.0, None, 3.0, None, 5.0]}
        result = osum_func.execute(data)
        self.assertEqual(result, 9.0)
        
        # 単一値テスト
        data = {'inputs': [42.0]}
        result = osum_func.execute(data)
        self.assertEqual(result, 42.0)
    
    def test_leader_num_function_basic(self):
        """LeaderNum関数（通貨強弱判定）の基本テスト"""
        leader_func = LeaderNumFunction(self.pkg_id)
        
        # 正常ケース: 通貨強弱判定（最大値を持つ通貨を特定）
        data = {'inputs': [45.2, 52.8, 48.1, 43.5], 'threshold': 45.0}
        result = leader_func.execute(data)
        self.assertEqual(result, 2)  # inputs[1]=52.8が最強通貨（JPY）
        
        # 閾値を超える通貨がない場合
        data = {'inputs': [30.0, 35.0, 40.0], 'threshold': 100.0}
        result = leader_func.execute(data)
        self.assertEqual(result, 0)
        
        # USD最強の場合
        data = {'inputs': [85.0, 45.0, 60.0], 'threshold': 50.0}
        result = leader_func.execute(data)
        self.assertEqual(result, 1)  # USD（inputs[0]）が最強
        
        # EUR最強の場合
        data = {'inputs': [55.0, 48.0, 75.0], 'threshold': 50.0}
        result = leader_func.execute(data)
        self.assertEqual(result, 3)  # EUR（inputs[2]）が最強
        
        # None値処理テスト
        data = {'inputs': [None, 46.0, 60.0, None], 'threshold': 45.0}
        result = leader_func.execute(data)
        self.assertEqual(result, 3)  # inputs[2]=60.0が最強
        
        # 通貨強弱ランキングテスト
        ranking = leader_func.get_currency_strength_ranking(data)
        self.assertEqual(len(ranking), 2)  # None以外の2通貨
        self.assertEqual(ranking[0][0], 3)  # 最強はCurrency3
        self.assertEqual(ranking[0][1], 60.0)  # 値60.0
        self.assertEqual(ranking[1][0], 2)  # 次点はCurrency2
    
    def test_dual_direction_function_basic(self):
        """DualDirection関数の基本テスト"""
        dual_func = DualDirectionFunction(self.pkg_id)
        
        # 正の値テスト
        data = {'inputs': [25.0]}
        result = dual_func.execute(data)
        expected = {'up': 25.0, 'down': 0.0}
        self.assertEqual(result, expected)
        
        # 負の値テスト
        data = {'inputs': [-15.0]}
        result = dual_func.execute(data)
        expected = {'up': 0.0, 'down': 15.0}
        self.assertEqual(result, expected)
        
        # ゼロ値テスト
        data = {'inputs': [0.0]}
        result = dual_func.execute(data)
        expected = {'up': 0.0, 'down': 0.0}
        self.assertEqual(result, expected)
        
        # None値処理テスト
        data = {'inputs': [None]}
        result = dual_func.execute(data)
        expected = {'up': 0.0, 'down': 0.0}
        self.assertEqual(result, expected)
    
    def test_abs_ichi_function_basic(self):
        """AbsIchi関数の基本テスト"""
        abs_func = AbsIchiFunction(self.pkg_id)
        
        # 正常ケース: 絶対値距離計算
        data = {'inputs': [15.0], 'reference': 10.0}
        result = abs_func.execute(data)
        self.assertEqual(result, 5.0)
        
        # 負の差テスト
        data = {'inputs': [5.0], 'reference': 10.0}
        result = abs_func.execute(data)
        self.assertEqual(result, 5.0)
        
        # デフォルト基準値テスト（reference=0.0）
        data = {'inputs': [7.5]}
        result = abs_func.execute(data)
        self.assertEqual(result, 7.5)
        
        # None値処理テスト
        data = {'inputs': [None], 'reference': 5.0}
        result = abs_func.execute(data)
        self.assertEqual(result, 5.0)
    
    def test_minus_function_basic(self):
        """Minus関数の基本テスト"""
        minus_func = MinusFunction(self.pkg_id)
        
        # 正常ケース: 減算
        data = {'inputs': [20.0, 8.0]}
        result = minus_func.execute(data)
        self.assertEqual(result, 12.0)
        
        # 負の結果テスト
        data = {'inputs': [5.0, 15.0]}
        result = minus_func.execute(data)
        self.assertEqual(result, -10.0)
        
        # 入力不足テスト
        data = {'inputs': [10.0]}
        result = minus_func.execute(data)
        self.assertEqual(result, 0.0)
        
        # None値処理テスト
        data = {'inputs': [None, 5.0]}
        result = minus_func.execute(data)
        self.assertEqual(result, -5.0)  # 0.0 - 5.0 = -5.0
    
    def test_pkg_function_factory(self):
        """PKGFunctionFactoryのテスト"""
        factory = PKGFunctionFactory()
        
        # サポート関数タイプの確認
        supported_types = factory.get_supported_types()
        expected_types = ['Ratio', 'OSum', 'LeaderNum', 'DualDirection', 'AbsIchi', 'Minus', 'Dokyaku', 'Ikikaeri']
        for func_type in expected_types:
            self.assertIn(func_type, supported_types)
        
        # 関数インスタンス生成テスト
        ratio_instance = factory.create_function('Ratio', self.pkg_id)
        self.assertIsInstance(ratio_instance, RatioFunction)
        self.assertEqual(ratio_instance.function_type, 'Ratio')
        
        osum_instance = factory.create_function('OSum', self.pkg_id)
        self.assertIsInstance(osum_instance, OSumFunction)
        
        # 未サポート関数タイプのテスト
        with self.assertRaises(ValueError):
            factory.create_function('UnsupportedFunction', self.pkg_id)
        
        # 実装統計の確認
        stats = factory.get_implementation_stats()
        self.assertEqual(stats['high_priority_implemented'], 6)
        self.assertEqual(stats['memo_based_implemented'], 2)
        self.assertEqual(stats['coverage_percentage'], 81.4)
    
    def test_pkg_id_parsing(self):
        """PKG IDパースのテスト"""
        # 正常なPKG ID
        pkg_id_str = "391^1-123"
        parsed_id = PKGId.parse(pkg_id_str)
        
        self.assertEqual(parsed_id.timeframe, TimeFrame.M15)  # 3
        self.assertEqual(parsed_id.period, Period.COMMON)     # 9
        self.assertEqual(parsed_id.currency, Currency.USDJPY) # 1
        self.assertEqual(parsed_id.layer, 1)
        self.assertEqual(parsed_id.sequence, 123)
        
        # 文字列変換テスト
        self.assertEqual(str(parsed_id), pkg_id_str)
        
        # 無効なフォーマットテスト
        with self.assertRaises(ValueError):
            PKGId.parse("invalid_format")
    
    def test_performance_scenarios(self):
        """実用的なパフォーマンステスト"""
        
        # シナリオ1: CA111の比率計算（実際の使用例）
        ratio_func = RatioFunction(self.pkg_id)
        ca_data = {'inputs': [100.5, 98.2, 101.3, 99.7]}  # CA111_CA118_CA125_CA132相当
        ratio = ratio_func.execute(ca_data)
        expected_ratio = 100.5 / (98.2 + 101.3 + 99.7)  # ≈ 0.3357
        self.assertAlmostEqual(ratio, expected_ratio, places=4)
        
        # シナリオ2: SA014の通貨強弱判定（実際の使用例）
        leader_func = LeaderNumFunction(self.pkg_id)
        sa_data = {'inputs': [42.3, 50.8], 'threshold': 45}  # USD vs JPY強弱比較
        leader = leader_func.execute(sa_data)
        self.assertEqual(leader, 2)  # JPY（inputs[1]）が強い
        
        # シナリオ3: CA139の合計（実際の使用例）
        osum_func = OSumFunction(self.pkg_id)
        ca139_data = {'inputs': [12.3, 8.7]}  # SU067_SU068相当
        total = osum_func.execute(ca139_data)
        self.assertEqual(total, 21.0)
    
    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        ratio_func = RatioFunction(self.pkg_id)
        
        # 不正な入力データ
        invalid_data = {'invalid_key': [1, 2, 3]}
        result = ratio_func.execute(invalid_data)
        self.assertEqual(result, 0.0)
        
        # 数値変換エラー
        invalid_numeric = {'inputs': ['not_a_number', 5.0]}
        result = ratio_func.execute(invalid_numeric)
        # エラー処理により0.0が返される
        self.assertEqual(result, 0.0)


class TestIntegrationScenarios(unittest.TestCase):
    """実際の使用シナリオに基づく統合テスト"""
    
    def setUp(self):
        """統合テストセットアップ"""
        logging.basicConfig(level=logging.WARNING)
        self.factory = PKGFunctionFactory()
    
    def test_multi_timeframe_calculation(self):
        """マルチタイムフレーム計算シナリオ"""
        
        # 1分足のPKG関数
        m1_pkg_id = PKGId(TimeFrame.M1, Period.COMMON, Currency.USDJPY, 1, 1)
        m1_ratio = self.factory.create_function('Ratio', m1_pkg_id)
        
        # 15分足のPKG関数
        m15_pkg_id = PKGId(TimeFrame.M15, Period.COMMON, Currency.USDJPY, 1, 1)
        m15_osum = self.factory.create_function('OSum', m15_pkg_id)
        
        # データ処理
        m1_data = {'inputs': [105.2, 103.1, 104.8]}
        m1_result = m1_ratio.execute(m1_data)
        
        m15_data = {'inputs': [m1_result, 25.3, 18.7]}
        m15_result = m15_osum.execute(m15_data)
        
        # 結果検証
        expected_m1 = 105.2 / (103.1 + 104.8)  # ≈ 0.5062
        expected_m15 = expected_m1 + 25.3 + 18.7  # ≈ 44.5062
        
        self.assertAlmostEqual(m15_result, expected_m15, places=4)
    
    def test_hierarchical_pkg_processing(self):
        """階層的PKG処理シナリオ"""
        
        # Layer 1: 基本計算
        layer1_pkg = PKGId(TimeFrame.M15, Period.COMMON, Currency.USDJPY, 1, 1)
        base_calc = self.factory.create_function('Minus', layer1_pkg)
        
        # Layer 2: 通貨強弱統合処理
        layer2_pkg = PKGId(TimeFrame.M15, Period.COMMON, Currency.USDJPY, 2, 1)
        integration = self.factory.create_function('LeaderNum', layer2_pkg)
        
        # 階層処理
        layer1_data = {'inputs': [110.5, 108.2]}
        layer1_result = base_calc.execute(layer1_data)  # 2.3
        
        # 通貨強弱判定: USD(2.3), JPY(1.8), EUR(3.5), GBP(0.9)の比較
        layer2_data = {'inputs': [layer1_result, 1.8, 3.5, 0.9], 'threshold': 2.0}
        layer2_result = integration.execute(layer2_data)
        
        # EUR(3.5)が最強なので、通貨番号3を返す
        self.assertEqual(layer2_result, 3)


if __name__ == '__main__':
    print("=" * 60)
    print("優先度高PKG関数 TDDテスト実行")
    print("=" * 60)
    
    # テスト実行
    unittest.main(verbosity=2)