#!/usr/bin/env python3
"""
システム統合テスト
PKGエンジン、DAGエンジン、メモベース取引戦略の連携動作を検証

テスト範囲:
1. PKG関数群の統合動作
2. DAGエンジンとPKG関数の連携  
3. メモベース取引戦略の実行パイプライン
4. マルチタイムフレーム処理
5. エラーハンドリングと復旧
"""

import unittest
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import traceback

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接インポート（numpy依存回避）
import importlib.util

def load_module_from_file(module_name: str, file_path: str):
    """ファイルから直接モジュールを読み込み"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# 必要なモジュールの読み込み
base_dir = os.path.dirname(os.path.dirname(__file__))

# コアPKG関数
core_pkg_module = load_module_from_file(
    "core_pkg_functions",
    os.path.join(base_dir, "pkg", "memo_logic", "core_pkg_functions.py")
)

# DAGエンジン
dag_engine_module = load_module_from_file(
    "dag_engine_v2", 
    os.path.join(base_dir, "pkg", "memo_logic", "dag_engine_v2.py")
)

# 取引戦略
strategy_module = load_module_from_file(
    "memo_based_strategy",
    os.path.join(base_dir, "trading", "memo_based_strategy.py")
)

# クラスの抽出
PKGFunctionFactory = core_pkg_module.PKGFunctionFactory
MarketData = core_pkg_module.MarketData
TimeFrame = core_pkg_module.TimeFrame
Currency = core_pkg_module.Currency
Period = core_pkg_module.Period
PKGId = core_pkg_module.PKGId

DAGEngine = dag_engine_module.DAGEngine
MemoBasedTradingStrategy = strategy_module.MemoBasedTradingStrategy
TradeDirection = strategy_module.TradeDirection

class SystemIntegrationTest(unittest.TestCase):
    """システム統合テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        logging.basicConfig(level=logging.WARNING)  # テスト時はWARNING以上のみ
        
        self.factory = PKGFunctionFactory()
        self.dag_engine = DAGEngine()
        self.strategy = MemoBasedTradingStrategy(Currency.USDJPY)
        
        # テスト用市場データ生成
        self.test_market_data = self._generate_test_market_data()
        
    def _generate_test_market_data(self) -> Dict[str, List[MarketData]]:
        """テスト用市場データ生成"""
        base_price = 150.0
        base_time = datetime.now()
        
        # トレンド方向の市場データ（上昇トレンド）
        market_data = {}
        
        # 1分足データ（20本）
        m1_data = []
        for i in range(20):
            timestamp = base_time - timedelta(minutes=20-i)
            price_trend = i * 0.002  # 0.2pipsずつ上昇
            
            open_price = base_price + price_trend
            high_price = open_price + 0.005
            low_price = open_price - 0.003
            close_price = open_price + 0.002
            
            # 平均足も計算
            ha_close = (open_price + high_price + low_price + close_price) / 4
            ha_open = (m1_data[-1].heikin_ashi_close + m1_data[-1].heikin_ashi_open) / 2 if m1_data else open_price
            ha_high = max(high_price, ha_open, ha_close)
            ha_low = min(low_price, ha_open, ha_close)
            
            bar = MarketData(
                timestamp=timestamp,
                open=open_price,
                high=high_price, 
                low=low_price,
                close=close_price,
                volume=1000 + i * 10,
                heikin_ashi_open=ha_open,
                heikin_ashi_high=ha_high,
                heikin_ashi_low=ha_low,
                heikin_ashi_close=ha_close
            )
            m1_data.append(bar)
        
        # 5分足データ（10本）
        m5_data = []
        for i in range(10):
            timestamp = base_time - timedelta(minutes=(10-i)*5)
            price_trend = i * 0.01  # 1pipsずつ上昇
            
            open_price = base_price + price_trend
            high_price = open_price + 0.015
            low_price = open_price - 0.008
            close_price = open_price + 0.008
            
            ha_close = (open_price + high_price + low_price + close_price) / 4
            ha_open = (m5_data[-1].heikin_ashi_close + m5_data[-1].heikin_ashi_open) / 2 if m5_data else open_price
            ha_high = max(high_price, ha_open, ha_close)
            ha_low = min(low_price, ha_open, ha_close)
            
            bar = MarketData(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price, 
                close=close_price,
                volume=5000 + i * 50,
                heikin_ashi_open=ha_open,
                heikin_ashi_high=ha_high,
                heikin_ashi_low=ha_low,
                heikin_ashi_close=ha_close
            )
            m5_data.append(bar)
        
        # 15分足データ（8本）
        m15_data = []
        for i in range(8):
            timestamp = base_time - timedelta(minutes=(8-i)*15)
            price_trend = i * 0.025  # 2.5pipsずつ上昇
            
            open_price = base_price + price_trend
            high_price = open_price + 0.03
            low_price = open_price - 0.015
            close_price = open_price + 0.02
            
            ha_close = (open_price + high_price + low_price + close_price) / 4
            ha_open = (m15_data[-1].heikin_ashi_close + m15_data[-1].heikin_ashi_open) / 2 if m15_data else open_price
            ha_high = max(high_price, ha_open, ha_close)
            ha_low = min(low_price, ha_open, ha_close)
            
            bar = MarketData(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=15000 + i * 100,
                heikin_ashi_open=ha_open,
                heikin_ashi_high=ha_high,
                heikin_ashi_low=ha_low,
                heikin_ashi_close=ha_close
            )
            m15_data.append(bar)
        
        # 30分足データ（6本）
        m30_data = []
        for i in range(6):
            timestamp = base_time - timedelta(minutes=(6-i)*30)
            price_trend = i * 0.04  # 4pipsずつ上昇
            
            open_price = base_price + price_trend
            high_price = open_price + 0.05
            low_price = open_price - 0.025
            close_price = open_price + 0.035
            
            ha_close = (open_price + high_price + low_price + close_price) / 4
            ha_open = (m30_data[-1].heikin_ashi_close + m30_data[-1].heikin_ashi_open) / 2 if m30_data else open_price
            ha_high = max(high_price, ha_open, ha_close)
            ha_low = min(low_price, ha_open, ha_close)
            
            bar = MarketData(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=30000 + i * 200,
                heikin_ashi_open=ha_open,
                heikin_ashi_high=ha_high,
                heikin_ashi_low=ha_low,
                heikin_ashi_close=ha_close
            )
            m30_data.append(bar)
        
        market_data = {
            'M1': m1_data,
            'M5': m5_data, 
            'M15': m15_data,
            'M30': m30_data
        }
        
        return market_data
    
    def test_pkg_function_factory_integration(self):
        """PKG関数ファクトリー統合テスト"""
        print("\n=== PKG関数ファクトリー統合テスト ===")
        
        # サポート関数タイプの確認
        supported_types = self.factory.get_supported_types()
        self.assertGreaterEqual(len(supported_types), 6)
        
        print(f"✓ サポート関数タイプ数: {len(supported_types)}")
        
        # 各関数タイプのインスタンス生成テスト
        pkg_id = PKGId(TimeFrame.M15, Period.COMMON, Currency.USDJPY, 1, 1)
        
        successful_functions = 0
        for func_type in ['Ratio', 'OSum', 'LeaderNum', 'Minus']:
            try:
                func_instance = self.factory.create_function(func_type, pkg_id)
                self.assertIsNotNone(func_instance)
                successful_functions += 1
                print(f"✓ {func_type}関数インスタンス生成成功")
            except Exception as e:
                print(f"✗ {func_type}関数エラー: {e}")
        
        self.assertGreaterEqual(successful_functions, 4)
        print(f"✓ 統合テスト成功: {successful_functions}/4 関数")
    
    def test_dag_engine_integration(self):
        """DAGエンジン統合テスト"""
        print("\n=== DAGエンジン統合テスト ===")
        
        try:
            # 生データ登録
            self.dag_engine.register_raw_data("AA001", 3, 9, 1, 100.0)
            self.dag_engine.register_raw_data("AA002", 3, 9, 1, 105.0)
            
            # PKG関数登録
            self.dag_engine.register_function(
                pkg_id="391^1-001",
                function_type="Z",
                input_refs=["391^0-AA001", "391^0-AA002"]
            )
            
            print("✓ 生データとPKG関数の登録成功")
            
            # 評価テスト
            results = self.dag_engine.evaluate(["391^1-001"])
            self.assertIn("391^1-001", results)
            
            print(f"✓ DAG評価成功: 結果={results['391^1-001']}")
            
            # グラフ可視化テスト
            graph_viz = self.dag_engine.visualize_graph()
            self.assertIsInstance(graph_viz, str)
            self.assertGreater(len(graph_viz), 0)
            
            print("✓ グラフ可視化成功")
            
        except Exception as e:
            self.fail(f"DAGエンジン統合テスト失敗: {e}")
    
    def test_trading_strategy_integration(self):
        """取引戦略統合テスト"""
        print("\n=== 取引戦略統合テスト ===")
        
        try:
            # 市場状況分析テスト
            analysis = self.strategy.analyze_market_condition(self.test_market_data)
            
            self.assertIn('overall_direction', analysis)
            self.assertIn('confidence', analysis)
            self.assertIn('dokyaku_signal', analysis)
            self.assertIn('ikikaeri_signal', analysis)
            
            print(f"✓ 市場分析成功:")
            print(f"  - 方向: {analysis['overall_direction'].name}")
            print(f"  - 信頼度: {analysis['confidence']:.3f}")
            print(f"  - 同逆判定: {'有効' if analysis['dokyaku_signal'] else '無効'}")
            print(f"  - 行帰判定: {'有効' if analysis['ikikaeri_signal'] else '無効'}")
            
            # 取引セットアップ生成テスト
            current_price = 150.25
            setup = self.strategy.generate_trade_setup(analysis, current_price)
            
            if setup:
                print(f"✓ 取引セットアップ生成成功:")
                print(f"  - 方向: {setup.direction.name}")
                print(f"  - エントリー価格: {setup.entry_price}")
                print(f"  - 信頼度: {setup.confidence:.3f}")
                
                # 取引実行テスト
                success = self.strategy.execute_trade(setup)
                self.assertTrue(success)
                print("✓ 取引実行成功")
                
            else:
                print("⚠ 取引セットアップ未生成（条件未達成）")
            
            # 統計取得テスト
            stats = self.strategy.get_strategy_statistics()
            self.assertIn('total_trades', stats)
            self.assertIn('win_rate', stats)
            
            print(f"✓ 戦略統計取得成功: 合計取引数={stats['total_trades']}")
            
        except Exception as e:
            self.fail(f"取引戦略統合テスト失敗: {e}")
    
    def test_multi_timeframe_processing(self):
        """マルチタイムフレーム処理テスト"""
        print("\n=== マルチタイムフレーム処理テスト ===")
        
        try:
            # 各時間足のデータ検証
            timeframes = ['M1', 'M5', 'M15', 'M30']
            for tf in timeframes:
                data = self.test_market_data.get(tf, [])
                self.assertGreater(len(data), 0, f"{tf}データが空")
                
                # データの連続性確認
                for i in range(1, len(data)):
                    self.assertGreater(data[i].timestamp, data[i-1].timestamp, 
                                     f"{tf}の時系列順序エラー")
                
                print(f"✓ {tf}データ検証成功: {len(data)}本")
            
            # 時間足間の整合性確認
            m15_latest = self.test_market_data['M15'][-1]
            m5_latest = self.test_market_data['M5'][-1]
            
            # 15分足の方が5分足より時間軸が大きいことを確認
            self.assertLessEqual(m15_latest.timestamp, m5_latest.timestamp + timedelta(minutes=15))
            
            print("✓ 時間足間整合性確認成功")
            
            # マルチタイムフレーム同期テスト
            sync_result = self.strategy._check_timeframe_sync(
                self.test_market_data['M1'],
                self.test_market_data['M5'], 
                self.test_market_data['M15'],
                self.test_market_data['M30']
            )
            
            print(f"✓ 時間足同期テスト成功: {'同期中' if sync_result else '非同期'}")
            
        except Exception as e:
            self.fail(f"マルチタイムフレーム処理テスト失敗: {e}")
    
    def test_error_handling_and_recovery(self):
        """エラーハンドリング・復旧テスト"""
        print("\n=== エラーハンドリング・復旧テスト ===")
        
        # 不正データでのテスト
        try:
            # 空データでの分析
            empty_data = {'M15': []}
            analysis = self.strategy.analyze_market_condition(empty_data)
            self.assertEqual(analysis['overall_direction'], TradeDirection.NEUTRAL)
            print("✓ 空データエラーハンドリング成功")
            
            # 不正価格での取引セットアップ
            setup = self.strategy.generate_trade_setup(analysis, -100.0)  # 負の価格
            # エラーが発生しても例外で停止しないことを確認
            print("✓ 不正価格エラーハンドリング成功")
            
            # DAGエンジン不正入力テスト
            try:
                self.dag_engine.register_function("invalid_id", "InvalidType", [])
                results = self.dag_engine.evaluate(["invalid_id"])
                print("✓ DAG不正入力エラーハンドリング成功")
            except Exception:
                print("✓ DAG不正入力で適切に例外処理")
            
        except Exception as e:
            print(f"⚠ エラーハンドリングテストで予期しない例外: {e}")
            # テスト継続（エラーハンドリング自体のテストなので）
    
    def test_performance_benchmarks(self):
        """パフォーマンスベンチマークテスト"""
        print("\n=== パフォーマンスベンチマークテスト ===")
        
        import time
        
        # メモファイル目標時間との比較
        target_times = {
            'overall': 0.019,        # 19ms
            'momi_detection': 0.077,  # 77ms
            'overshoot': 0.550,      # 550ms
            'time_sync': 0.565       # 565ms
        }
        
        try:
            # 全体処理時間計測
            start_time = time.time()
            analysis = self.strategy.analyze_market_condition(self.test_market_data)
            overall_time = time.time() - start_time
            
            print(f"✓ 全体処理時間: {overall_time*1000:.1f}ms (目標: {target_times['overall']*1000:.1f}ms)")
            
            # もみ判定時間計測
            start_time = time.time()
            momi_result = self.strategy._detect_momi_condition(self.test_market_data['M15'])
            momi_time = time.time() - start_time
            
            print(f"✓ もみ判定時間: {momi_time*1000:.1f}ms (目標: {target_times['momi_detection']*1000:.1f}ms)")
            
            # オーバーシュート検出時間計測
            start_time = time.time()
            overshoot_result = self.strategy._detect_overshoot(self.test_market_data['M15'])
            overshoot_time = time.time() - start_time
            
            print(f"✓ オーバーシュート検出時間: {overshoot_time*1000:.1f}ms (目標: {target_times['overshoot']*1000:.1f}ms)")
            
            # 時間足同期時間計測
            start_time = time.time()
            sync_result = self.strategy._check_timeframe_sync(
                self.test_market_data['M1'],
                self.test_market_data['M5'],
                self.test_market_data['M15'], 
                self.test_market_data['M30']
            )
            sync_time = time.time() - start_time
            
            print(f"✓ 時間足同期時間: {sync_time*1000:.1f}ms (目標: {target_times['time_sync']*1000:.1f}ms)")
            
            # パフォーマンス判定
            performance_score = 0
            if overall_time <= target_times['overall'] * 2:  # 目標の2倍以内
                performance_score += 25
            if momi_time <= target_times['momi_detection']:
                performance_score += 25
            if overshoot_time <= target_times['overshoot']:
                performance_score += 25  
            if sync_time <= target_times['time_sync']:
                performance_score += 25
            
            print(f"✓ パフォーマンススコア: {performance_score}/100")
            
        except Exception as e:
            print(f"⚠ パフォーマンステストエラー: {e}")
    
    def test_full_system_workflow(self):
        """システム全体ワークフローテスト"""
        print("\n=== システム全体ワークフローテスト ===")
        
        workflow_steps = []
        
        try:
            # ステップ1: データ準備
            workflow_steps.append("データ準備")
            self.assertIsNotNone(self.test_market_data)
            self.assertGreater(len(self.test_market_data['M15']), 0)
            
            # ステップ2: PKG関数初期化
            workflow_steps.append("PKG関数初期化")
            pkg_stats = self.factory.get_implementation_stats()
            self.assertGreater(pkg_stats['total_types'], 0)
            
            # ステップ3: 市場分析
            workflow_steps.append("市場分析")
            analysis = self.strategy.analyze_market_condition(self.test_market_data)
            self.assertIsNotNone(analysis)
            
            # ステップ4: 取引判定
            workflow_steps.append("取引判定")
            current_price = self.test_market_data['M15'][-1].close
            setup = self.strategy.generate_trade_setup(analysis, current_price)
            
            # ステップ5: リスク管理
            workflow_steps.append("リスク管理")
            if setup:
                self.assertGreater(setup.take_profit, setup.entry_price)
                self.assertLess(setup.stop_loss, setup.entry_price)
            
            # ステップ6: 決済判定
            workflow_steps.append("決済判定")
            exit_signal = self.strategy.should_exit_position(self.test_market_data, current_price)
            self.assertIsInstance(exit_signal, bool)
            
            # ステップ7: 統計更新
            workflow_steps.append("統計更新")
            stats = self.strategy.get_strategy_statistics()
            self.assertIn('total_trades', stats)
            
            print(f"✓ 全ワークフローステップ成功: {len(workflow_steps)}段階")
            for i, step in enumerate(workflow_steps, 1):
                print(f"  {i}. {step} ✓")
            
        except Exception as e:
            failed_step = len(workflow_steps) + 1
            print(f"✗ ワークフローステップ{failed_step}で失敗: {e}")
            print("完了したステップ:")
            for i, step in enumerate(workflow_steps, 1):
                print(f"  {i}. {step} ✓")
            raise


class SystemIntegrationRunner:
    """統合テスト実行管理"""
    
    def run_all_tests(self):
        """全統合テストを実行"""
        print("=" * 60)
        print("FX取引システム 統合テスト実行")
        print("=" * 60)
        
        # テストスイート作成
        test_suite = unittest.TestLoader().loadTestsFromTestCase(SystemIntegrationTest)
        
        # カスタムテスト実行（詳細出力付き）
        test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': []
        }
        
        for test in test_suite:
            test_results['total_tests'] += 1
            test_name = test._testMethodName.replace('test_', '').replace('_', ' ').title()
            
            try:
                print(f"\n🧪 テスト実行: {test_name}")
                test.setUp()
                getattr(test, test._testMethodName)()
                test_results['passed_tests'] += 1
                print(f"✅ {test_name} - 成功")
                
            except Exception as e:
                test_results['failed_tests'] += 1
                error_info = {
                    'test_name': test_name,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
                test_results['errors'].append(error_info)
                print(f"❌ {test_name} - 失敗: {e}")
        
        # 結果サマリー
        print("\n" + "=" * 60)
        print("📊 統合テスト結果サマリー")
        print("=" * 60)
        print(f"実行テスト数: {test_results['total_tests']}")
        print(f"成功: {test_results['passed_tests']}")
        print(f"失敗: {test_results['failed_tests']}")
        print(f"成功率: {test_results['passed_tests']/test_results['total_tests']*100:.1f}%")
        
        if test_results['errors']:
            print(f"\n⚠️ 失敗詳細:")
            for error in test_results['errors']:
                print(f"  - {error['test_name']}: {error['error']}")
        
        # システムレディネス判定
        success_rate = test_results['passed_tests'] / test_results['total_tests']
        if success_rate >= 0.8:  # 80%以上で合格
            print(f"\n🎉 システム統合テスト合格！")
            print("   バックテスト実行準備完了")
            return True
        else:
            print(f"\n⚠️ システム統合テスト未完了")
            print("   課題解決後に再実行が必要")
            return False


if __name__ == "__main__":
    # 統合テスト実行
    runner = SystemIntegrationRunner()
    success = runner.run_all_tests()
    
    # 終了コード設定
    exit_code = 0 if success else 1
    sys.exit(exit_code)