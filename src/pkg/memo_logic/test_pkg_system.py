"""
Week 6: PKG関数システムテスト
97個のメモファイルから実装したPKG関数システムの統合テスト
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging
import time
import json
from datetime import datetime, timedelta

from .core_pkg_functions import MarketData, PKGId, TimeFrame, Currency, Period
from .pkg_system_integration import PKGSystemIntegration

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class PKGSystemTester:
    """PKG関数システムのテスト実行クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pkg_system = PKGSystemIntegration()
        
    def generate_test_market_data(self, num_bars: int = 200) -> List[MarketData]:
        """テスト用の市場データ生成"""
        base_price = 150.0  # USDJPY基準価格
        current_time = datetime.now()
        
        market_data = []
        
        for i in range(num_bars):
            # ランダムウォーク + トレンド + ボラティリティ
            trend = 0.0001 * i if i < num_bars // 2 else -0.0001 * (i - num_bars // 2)
            noise = np.random.normal(0, 0.01)
            price_change = trend + noise
            
            if i == 0:
                open_price = base_price
            else:
                open_price = market_data[i-1].close
            
            close_price = open_price * (1 + price_change)
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
            
            # 平均足の計算
            if i == 0:
                ha_open = (open_price + close_price) / 2
                ha_close = (open_price + high_price + low_price + close_price) / 4
            else:
                prev_ha = market_data[i-1]
                ha_open = (prev_ha.heikin_ashi_open + prev_ha.heikin_ashi_close) / 2
                ha_close = (open_price + high_price + low_price + close_price) / 4
            
            ha_high = max(high_price, ha_open, ha_close)
            ha_low = min(low_price, ha_open, ha_close)
            
            bar_data = MarketData(
                timestamp=current_time + timedelta(minutes=i),
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=np.random.uniform(1000, 10000),
                heikin_ashi_open=ha_open,
                heikin_ashi_high=ha_high,
                heikin_ashi_low=ha_low,
                heikin_ashi_close=ha_close
            )
            
            market_data.append(bar_data)
        
        return market_data
    
    def generate_multi_timeframe_data(self) -> Dict[str, List[MarketData]]:
        """マルチタイムフレームテストデータの生成"""
        base_data = self.generate_test_market_data(1000)
        
        # 各時間足のデータを生成（簡易実装）
        multi_tf_data = {
            '1M': base_data[-200:],      # 1分足: 直近200本
            '5M': base_data[-200::5],    # 5分足: 5本おき
            '15M': base_data[-200::15],  # 15分足: 15本おき
            '30M': base_data[-200::30],  # 30分足: 30本おき
            '60M': base_data[-200::60],  # 1時間足: 60本おき
            '240M': base_data[-200::240] # 4時間足: 240本おき
        }
        
        return multi_tf_data
    
    async def test_individual_pkg_functions(self) -> Dict[str, any]:
        """個別PKG関数のテスト"""
        self.logger.info("Starting individual PKG function tests...")
        
        test_data = {
            'market_data': self.generate_test_market_data(100),
            'multi_timeframe_data': self.generate_multi_timeframe_data()
        }
        
        results = await self.pkg_system.execute_all_pkg_functions(test_data)
        
        test_summary = {
            'total_functions_tested': len(results),
            'successful_executions': sum(1 for r in results if r.success),
            'failed_executions': sum(1 for r in results if not r.success),
            'signals_generated': sum(1 for r in results if r.success and r.signal is not None),
            'individual_results': []
        }
        
        for result in results:
            function_name = result.signal.signal_type if result.signal else 'unknown'
            test_summary['individual_results'].append({
                'function': function_name,
                'pkg_id': str(result.pkg_id),
                'success': result.success,
                'execution_time_ms': result.execution_time_ms,
                'signal_generated': result.signal is not None,
                'signal_direction': result.signal.direction if result.signal else None,
                'signal_confidence': result.signal.confidence if result.signal else None,
                'error': result.error_message
            })
        
        self.logger.info(f"Individual tests completed: {test_summary['successful_executions']}/{test_summary['total_functions_tested']} successful")
        return test_summary
    
    def test_synchronized_execution(self) -> Dict[str, any]:
        """同期実行テスト（パフォーマンス比較用）"""
        self.logger.info("Starting synchronized execution test...")
        
        test_data = {
            'market_data': self.generate_test_market_data(100),
            'multi_timeframe_data': self.generate_multi_timeframe_data()
        }
        
        start_time = time.perf_counter()
        results = self.pkg_system.execute_synchronized_pkg_functions(test_data)
        total_time = (time.perf_counter() - start_time) * 1000
        
        return {
            'execution_method': 'synchronized',
            'total_execution_time_ms': total_time,
            'successful_executions': sum(1 for r in results if r.success),
            'failed_executions': sum(1 for r in results if not r.success),
            'performance_target_achieved': total_time <= self.pkg_system.performance_targets['total_system']
        }
    
    def test_signal_integration(self) -> Dict[str, any]:
        """信号統合テスト"""
        self.logger.info("Starting signal integration test...")
        
        test_data = {
            'market_data': self.generate_test_market_data(150),
            'multi_timeframe_data': self.generate_multi_timeframe_data()
        }
        
        # 同期実行で結果取得
        execution_results = self.pkg_system.execute_synchronized_pkg_functions(test_data)
        
        # 信号統合
        integration_result = self.pkg_system.integrate_signals(execution_results)
        
        return {
            'integration_test': True,
            'input_signals': len([r for r in execution_results if r.success and r.signal]),
            'final_direction': integration_result['final_direction'],
            'final_confidence': integration_result['confidence'],
            'integration_method': integration_result['integration_method'],
            'consensus_analysis': integration_result.get('consensus_analysis', {}),
            'individual_signals': integration_result.get('individual_signals', [])
        }
    
    def test_performance_targets(self) -> Dict[str, any]:
        """パフォーマンス目標達成テスト"""
        self.logger.info("Starting performance target tests...")
        
        performance_tests = []
        
        # 複数回実行してパフォーマンスを測定
        for test_run in range(5):
            test_data = {
                'market_data': self.generate_test_market_data(200),
                'multi_timeframe_data': self.generate_multi_timeframe_data()
            }
            
            # 同期実行
            sync_results = self.pkg_system.execute_synchronized_pkg_functions(test_data)
            
            performance_tests.append({
                'test_run': test_run + 1,
                'sync_results': {
                    'total_time_ms': sum(r.execution_time_ms for r in sync_results),
                    'individual_times': {
                        r.signal.signal_type if r.signal else 'unknown': r.execution_time_ms 
                        for r in sync_results if r.success
                    }
                }
            })
        
        # パフォーマンス統計
        performance_summary = self.pkg_system.get_performance_summary()
        
        return {
            'performance_target_tests': performance_tests,
            'performance_summary': performance_summary,
            'targets': self.pkg_system.performance_targets
        }
    
    def test_error_handling(self) -> Dict[str, any]:
        """エラーハンドリングテスト"""
        self.logger.info("Starting error handling tests...")
        
        error_tests = []
        
        # 不完全なデータでのテスト
        incomplete_data_tests = [
            {'market_data': []},  # 空のデータ
            {'market_data': self.generate_test_market_data(2)},  # 不十分なデータ
            {'market_data': None},  # Noneデータ
            {}  # 空の辞書
        ]
        
        for i, test_data in enumerate(incomplete_data_tests):
            try:
                results = self.pkg_system.execute_synchronized_pkg_functions(test_data)
                error_tests.append({
                    'test_case': f'incomplete_data_{i}',
                    'success': True,
                    'results_count': len(results),
                    'errors': [r.error_message for r in results if not r.success]
                })
            except Exception as e:
                error_tests.append({
                    'test_case': f'incomplete_data_{i}',
                    'success': False,
                    'exception': str(e)
                })
        
        return {
            'error_handling_tests': error_tests,
            'total_tests': len(error_tests),
            'successful_error_handling': sum(1 for t in error_tests if t['success'])
        }
    
    async def run_comprehensive_test_suite(self) -> Dict[str, any]:
        """包括的テストスイートの実行"""
        self.logger.info("=== Starting comprehensive PKG system test suite ===")
        
        start_time = time.perf_counter()
        
        # 各種テストの実行
        test_results = {}
        
        try:
            # 1. 個別関数テスト
            test_results['individual_functions'] = await self.test_individual_pkg_functions()
            
            # 2. 同期実行テスト
            test_results['synchronized_execution'] = self.test_synchronized_execution()
            
            # 3. 信号統合テスト
            test_results['signal_integration'] = self.test_signal_integration()
            
            # 4. パフォーマンステスト
            test_results['performance_targets'] = self.test_performance_targets()
            
            # 5. エラーハンドリングテスト
            test_results['error_handling'] = self.test_error_handling()
            
        except Exception as e:
            self.logger.error(f"Test suite execution failed: {e}")
            test_results['test_suite_error'] = str(e)
        
        total_test_time = (time.perf_counter() - start_time) * 1000
        
        # 総合評価
        overall_assessment = self._assess_overall_performance(test_results)
        
        test_results['test_suite_summary'] = {
            'total_execution_time_ms': total_test_time,
            'timestamp': datetime.now().isoformat(),
            'overall_assessment': overall_assessment
        }
        
        self.logger.info(f"=== Test suite completed in {total_test_time:.2f}ms ===")
        return test_results
    
    def _assess_overall_performance(self, test_results: Dict[str, any]) -> Dict[str, any]:
        """総合パフォーマンス評価"""
        assessment = {
            'functionality_score': 0.0,
            'performance_score': 0.0,
            'reliability_score': 0.0,
            'overall_score': 0.0,
            'recommendations': []
        }
        
        # 機能性スコア
        if 'individual_functions' in test_results:
            individual_results = test_results['individual_functions']
            success_rate = individual_results['successful_executions'] / individual_results['total_functions_tested']
            signal_rate = individual_results['signals_generated'] / individual_results['total_functions_tested']
            assessment['functionality_score'] = (success_rate * 0.7 + signal_rate * 0.3) * 100
        
        # パフォーマンススコア
        if 'performance_targets' in test_results:
            perf_summary = test_results['performance_targets']['performance_summary']
            if 'summary' in perf_summary:
                target_achieved = perf_summary['summary'].get('total_target_achieved', False)
                assessment['performance_score'] = 100 if target_achieved else 60
        
        # 信頼性スコア
        if 'error_handling' in test_results:
            error_results = test_results['error_handling']
            error_handling_rate = error_results['successful_error_handling'] / error_results['total_tests']
            assessment['reliability_score'] = error_handling_rate * 100
        
        # 総合スコア
        scores = [assessment['functionality_score'], assessment['performance_score'], assessment['reliability_score']]
        assessment['overall_score'] = np.mean([s for s in scores if s > 0])
        
        # 推奨事項
        if assessment['functionality_score'] < 80:
            assessment['recommendations'].append("Individual PKG function implementations need improvement")
        
        if assessment['performance_score'] < 80:
            assessment['recommendations'].append("Performance optimization required to meet target execution times")
        
        if assessment['reliability_score'] < 80:
            assessment['recommendations'].append("Error handling and edge case management needs enhancement")
        
        if assessment['overall_score'] > 85:
            assessment['recommendations'].append("System is ready for production deployment")
        elif assessment['overall_score'] > 70:
            assessment['recommendations'].append("System is suitable for testing environment with monitoring")
        else:
            assessment['recommendations'].append("Significant improvements required before deployment")
        
        return assessment

# メイン実行部分
async def main():
    """メインテスト実行"""
    tester = PKGSystemTester()
    
    print("=" * 80)
    print("PKG関数システム Week 6 統合テスト")
    print("97個のメモファイルから抽出したロジックの実装評価")
    print("=" * 80)
    
    # 包括的テストの実行
    test_results = await tester.run_comprehensive_test_suite()
    
    # 結果の表示
    print("\n" + "=" * 50)
    print("テスト結果サマリー")
    print("=" * 50)
    
    if 'test_suite_summary' in test_results:
        summary = test_results['test_suite_summary']
        assessment = summary.get('overall_assessment', {})
        
        print(f"総実行時間: {summary['total_execution_time_ms']:.2f}ms")
        print(f"機能性スコア: {assessment.get('functionality_score', 0):.1f}/100")
        print(f"パフォーマンススコア: {assessment.get('performance_score', 0):.1f}/100")
        print(f"信頼性スコア: {assessment.get('reliability_score', 0):.1f}/100")
        print(f"総合スコア: {assessment.get('overall_score', 0):.1f}/100")
        
        print("\n推奨事項:")
        for recommendation in assessment.get('recommendations', []):
            print(f"- {recommendation}")
    
    # 詳細結果の保存
    output_file = f"pkg_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n詳細結果を保存しました: {output_file}")
    except Exception as e:
        print(f"結果保存エラー: {e}")
    
    print("\n" + "=" * 80)
    print("PKG関数システムテスト完了")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())