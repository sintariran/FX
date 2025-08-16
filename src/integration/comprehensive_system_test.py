"""
Week4 統合システムテスト
全システムコンポーネントの統合検証

レビューフィードバック実装後の総合テスト:
1. パフォーマンス最適化 (0.41ms達成)
2. リスク管理強化 (ATRベース、ドローダウン制限)
3. エラー処理・自動復旧
4. 統合動作確認
"""

import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass
import sys
import os

# パッケージパス追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from optimization.performance_optimizer import EventDrivenEngine, MarketEvent, OptimizedStrategy
from risk_management.enhanced_risk_manager import EnhancedRiskManager, RiskLimits
from monitoring.error_handler import ErrorHandler, AlertLevel


@dataclass
class IntegrationTestResults:
    """統合テスト結果"""
    performance_stats: Dict
    risk_management_stats: Dict
    error_handling_stats: Dict
    overall_success: bool
    execution_time: float
    total_events_processed: int


class ComprehensiveSystemTest:
    """包括的システムテスト"""
    
    def __init__(self):
        # システムコンポーネント初期化
        self.event_engine = EventDrivenEngine()
        self.risk_manager = EnhancedRiskManager(
            initial_balance=1000000,  # 100万円
            limits=RiskLimits(
                max_positions=3,
                max_exposure=500000,
                max_daily_loss=50000,
                max_drawdown=0.05,  # 5%
                max_risk_per_trade=0.02  # 2%
            )
        )
        self.error_handler = ErrorHandler()
        
        # テスト統計
        self.test_start_time = None
        self.events_processed = 0
        self.trades_executed = 0
        self.errors_encountered = 0
        self.performance_violations = 0
        
        # 統合ストラテジー
        self.strategy = IntegratedStrategy(
            self.event_engine,
            self.risk_manager,
            self.error_handler
        )
    
    async def run_comprehensive_test(self, duration_seconds: int = 30) -> IntegrationTestResults:
        """包括的システムテスト実行"""
        print("=" * 80)
        print("🎯 Week4 統合システムテスト開始")
        print("=" * 80)
        
        self.test_start_time = time.perf_counter()
        
        # 1. システム初期化テスト
        print("\n📋 1. システム初期化テスト")
        await self._test_system_initialization()
        
        # 2. パフォーマンステスト
        print("\n⚡ 2. パフォーマンス最適化テスト")
        await self._test_performance_optimization()
        
        # 3. リスク管理テスト
        print("\n🛡️ 3. リスク管理システムテスト")
        await self._test_risk_management()
        
        # 4. エラー処理テスト
        print("\n🚨 4. エラー処理・自動復旧テスト")
        await self._test_error_handling()
        
        # 5. 統合負荷テスト
        print("\n🔥 5. 統合負荷テスト")
        await self._test_integrated_load(duration_seconds)
        
        # 6. 結果集計
        print("\n📊 6. テスト結果集計")
        results = await self._compile_results()
        
        return results
    
    async def _test_system_initialization(self):
        """システム初期化テスト"""
        
        # ストラテジー登録
        self.event_engine.subscribe("PRICE_UPDATE", self.strategy.on_price_update)
        self.event_engine.subscribe("SIGNAL_CHECK", self.strategy.on_signal_check)
        
        # エンジン開始
        task = await self.event_engine.start()
        
        # 初期状態確認
        status = self.error_handler.get_system_status()
        risk_metrics = self.risk_manager.get_risk_metrics()
        
        print(f"  ✅ イベントエンジン: 動作中")
        print(f"  ✅ リスク管理: 残高¥{risk_metrics['current_balance']:,.0f}")
        print(f"  ✅ エラーハンドラー: フェイルセーフ={status['is_failsafe_mode']}")
        
        return True
    
    async def _test_performance_optimization(self):
        """パフォーマンス最適化テスト"""
        
        # 高頻度イベントテスト（1000イベント）
        test_events = 1000
        
        for i in range(test_events):
            import random
            
            # ダミー価格データ
            price_data = {
                'open': 150.0 + random.gauss(0, 0.1),
                'high': 150.2 + random.gauss(0, 0.1),
                'low': 149.8 + random.gauss(0, 0.1),
                'close': 150.0 + random.gauss(0, 0.1),
                'volume': random.randint(1000, 5000)
            }
            
            event = MarketEvent(
                event_type="PRICE_UPDATE",
                symbol="USDJPY",
                timestamp=f"2024-01-01T00:{i//60:02d}:{i%60:02d}",
                data=price_data
            )
            
            await self.event_engine.publish_event(event)
            self.events_processed += 1
        
        # 処理完了待機
        await asyncio.sleep(0.5)
        
        # パフォーマンス統計取得
        perf_stats = self.event_engine.get_performance_stats()
        
        if perf_stats:
            avg_time = perf_stats['avg_response_time']
            max_time = perf_stats['max_response_time']
            target_achievement = perf_stats['target_achievement']
            
            print(f"  📈 平均応答時間: {avg_time:.2f}ms (目標: 19ms)")
            print(f"  📈 最大応答時間: {max_time:.2f}ms")
            print(f"  📈 目標達成率: {target_achievement:.1f}%")
            
            # 19ms目標チェック
            if avg_time <= 19.0:
                print(f"  ✅ パフォーマンス目標達成!")
            else:
                print(f"  ❌ パフォーマンス目標未達成")
                self.performance_violations += 1
    
    async def _test_risk_management(self):
        """リスク管理システムテスト"""
        
        # テスト1: 正常エントリー
        print("    📊 テスト1: 正常エントリーチェック")
        result = self.risk_manager.check_entry_allowed("USDJPY", 1, 150.0, 0.30)
        
        if result['allowed']:
            position = self.risk_manager.add_position(
                symbol="USDJPY",
                direction=1,
                size=result['position_size'],
                entry_price=150.0,
                stop_loss=result['stop_loss'],
                take_profit=result['take_profit']
            )
            print(f"      ✅ ポジション追加: {result['position_size']:,.0f}通貨")
        
        # テスト2: リスク制限テスト
        print("    📊 テスト2: リスク制限テスト")
        
        # 複数ポジション追加（制限テスト）
        for i in range(5):
            result = self.risk_manager.check_entry_allowed(
                f"TEST{i}", 1, 150.0 + i, 0.30
            )
            
            if result['allowed']:
                self.risk_manager.add_position(
                    symbol=f"TEST{i}",
                    direction=1,
                    size=10000,
                    entry_price=150.0 + i
                )
            else:
                print(f"      ⚠️ ポジション{i+1}: {result['reason']}")
        
        # テスト3: 損失シミュレーション
        print("    📊 テスト3: 損失シミュレーション")
        
        initial_balance = self.risk_manager.current_balance
        
        # 損失ポジション追加
        for i in range(3):
            pos = self.risk_manager.add_position("LOSS_TEST", 1, 10000, 150.0)
            pnl = self.risk_manager.close_position(pos, 149.0)  # 1円損失
            print(f"      📉 取引{i+1}: 損失¥{pnl:,.0f}")
        
        final_balance = self.risk_manager.current_balance
        total_loss = initial_balance - final_balance
        
        print(f"      💰 合計損失: ¥{total_loss:,.0f}")
        
        # リスク指標表示
        risk_metrics = self.risk_manager.get_risk_metrics()
        print(f"      📊 現在の指標:")
        print(f"        - 残高: ¥{risk_metrics['current_balance']:,.0f}")
        print(f"        - ドローダウン: {risk_metrics['current_drawdown']:.1%}")
        print(f"        - 連敗数: {risk_metrics['consecutive_losses']}")
        print(f"        - 勝率: {risk_metrics['win_rate']:.1%}")
    
    async def _test_error_handling(self):
        """エラー処理・自動復旧テスト"""
        
        # テスト1: データ検証
        print("    📊 テスト1: データ検証テスト")
        
        # 正常データ
        normal_data = {
            'timestamp': datetime.now().isoformat(),
            'bid': 150.000,
            'ask': 150.003,
            'mid': 150.0015,
            'volume': 1000
        }
        
        is_valid = await self.error_handler.validate_and_process_data(
            normal_data, "TestComponent"
        )
        print(f"      ✅ 正常データ処理: {is_valid}")
        
        # 異常データ
        invalid_data = {
            'timestamp': datetime.now().isoformat(),
            'bid': 150.000,
            'ask': 149.990,  # 逆スプレッド
            'mid': 150.0015
        }
        
        is_valid = await self.error_handler.validate_and_process_data(
            invalid_data, "TestComponent"
        )
        print(f"      ❌ 異常データ処理: {is_valid}")
        
        # テスト2: 例外処理
        print("    📊 テスト2: 例外処理テスト")
        
        try:
            raise ValueError("テスト例外")
        except Exception as e:
            can_continue = await self.error_handler.handle_exception(
                e, "TestComponent", {'test': True}
            )
            print(f"      🔧 例外処理: 継続可能={can_continue}")
            self.errors_encountered += 1
        
        # テスト3: システム状態確認
        status = self.error_handler.get_system_status()
        print(f"    📊 システム状態:")
        print(f"      - フェイルセーフ: {status['is_failsafe_mode']}")
        print(f"      - エラー数: {status['health']['error_count']}")
        print(f"      - 稼働時間: {status['health']['uptime_seconds']:.1f}秒")
    
    async def _test_integrated_load(self, duration_seconds: int):
        """統合負荷テスト"""
        
        print(f"    🔥 {duration_seconds}秒間の統合負荷テスト開始")
        
        start_time = time.perf_counter()
        events_sent = 0
        
        while (time.perf_counter() - start_time) < duration_seconds:
            # 複数シンボルの価格データ送信
            symbols = ["USDJPY", "EURJPY", "EURUSD", "GBPJPY"]
            
            for symbol in symbols:
                import random
                
                price_data = {
                    'open': 150.0 + random.gauss(0, 0.5),
                    'high': 150.5 + random.gauss(0, 0.5),
                    'low': 149.5 + random.gauss(0, 0.5),
                    'close': 150.0 + random.gauss(0, 0.5),
                    'volume': random.randint(1000, 10000)
                }
                
                event = MarketEvent(
                    event_type="PRICE_UPDATE",
                    symbol=symbol,
                    timestamp=datetime.now().isoformat(),
                    data=price_data
                )
                
                await self.event_engine.publish_event(event)
                events_sent += 1
                self.events_processed += 1
            
            # 少し待機
            await asyncio.sleep(0.01)
        
        # 処理完了待機
        await asyncio.sleep(1.0)
        
        print(f"      📊 負荷テスト結果:")
        print(f"        - 送信イベント数: {events_sent:,}")
        print(f"        - 平均送信レート: {events_sent/duration_seconds:.0f}イベント/秒")
        
        # パフォーマンス統計更新
        perf_stats = self.event_engine.get_performance_stats()
        if perf_stats:
            print(f"        - 最終平均応答時間: {perf_stats['avg_response_time']:.2f}ms")
    
    async def _compile_results(self) -> IntegrationTestResults:
        """テスト結果集計"""
        
        execution_time = time.perf_counter() - self.test_start_time
        
        # パフォーマンス統計
        perf_stats = self.event_engine.get_performance_stats()
        
        # リスク管理統計
        risk_stats = self.risk_manager.get_risk_metrics()
        
        # エラーハンドリング統計
        error_stats = self.error_handler.get_system_status()
        
        # 総合成功判定
        overall_success = (
            self.performance_violations == 0 and
            not risk_stats.get('is_trading_halted', False) and
            not error_stats.get('is_failsafe_mode', False)
        )
        
        results = IntegrationTestResults(
            performance_stats=perf_stats or {},
            risk_management_stats=risk_stats,
            error_handling_stats=error_stats,
            overall_success=overall_success,
            execution_time=execution_time,
            total_events_processed=self.events_processed
        )
        
        # 結果表示
        print("\n" + "=" * 80)
        print("📋 統合システムテスト 最終結果")
        print("=" * 80)
        
        print(f"\n⏱️  実行時間: {execution_time:.2f}秒")
        print(f"📊 処理イベント数: {self.events_processed:,}")
        print(f"💹 実行取引数: {self.trades_executed}")
        print(f"❌ エラー発生数: {self.errors_encountered}")
        print(f"⚠️  パフォーマンス違反数: {self.performance_violations}")
        
        if perf_stats:
            print(f"\n🎯 パフォーマンス結果:")
            print(f"  - 平均応答時間: {perf_stats['avg_response_time']:.2f}ms")
            print(f"  - 最大応答時間: {perf_stats['max_response_time']:.2f}ms")
            print(f"  - 目標達成率: {perf_stats['target_achievement']:.1f}%")
        
        print(f"\n🛡️ リスク管理結果:")
        print(f"  - 最終残高: ¥{risk_stats['current_balance']:,.0f}")
        print(f"  - 最大ドローダウン: {risk_stats['max_drawdown_reached']:.1%}")
        print(f"  - 取引停止: {'Yes' if risk_stats['is_trading_halted'] else 'No'}")
        
        print(f"\n🚨 エラー処理結果:")
        print(f"  - フェイルセーフモード: {'Yes' if error_stats['is_failsafe_mode'] else 'No'}")
        print(f"  - 総エラー数: {error_stats['health']['error_count']}")
        
        success_icon = "✅" if overall_success else "❌"
        print(f"\n{success_icon} 総合判定: {'成功' if overall_success else '問題あり'}")
        
        return results


class IntegratedStrategy:
    """統合ストラテジー（全システム連携）"""
    
    def __init__(self, engine, risk_manager, error_handler):
        self.engine = engine
        self.risk_manager = risk_manager
        self.error_handler = error_handler
        self.signals_generated = 0
        self.trades_attempted = 0
        
    async def on_price_update(self, event: MarketEvent):
        """価格更新時の処理"""
        symbol = event.symbol
        
        try:
            # 指標計算（パフォーマンス最適化済み）
            indicators = self.engine.calculate_indicators(symbol)
            
            if not indicators:
                return
            
            # シグナル生成
            signal = self._generate_signal(indicators)
            
            if signal != 0:
                self.signals_generated += 1
                
                # シグナルチェックイベント発行
                signal_event = MarketEvent(
                    event_type="SIGNAL_CHECK",
                    symbol=symbol,
                    timestamp=event.timestamp,
                    data={'signal': signal, 'indicators': indicators}
                )
                await self.engine.publish_event(signal_event)
        
        except Exception as e:
            # エラーハンドラーに委譲
            await self.error_handler.handle_exception(e, "IntegratedStrategy")
    
    async def on_signal_check(self, event: MarketEvent):
        """シグナルチェック時の処理"""
        symbol = event.symbol
        signal = event.data['signal']
        indicators = event.data['indicators']
        
        try:
            # リスク管理チェック
            atr = indicators.get('atr_14', 0.30)
            entry_price = 150.0  # ダミー価格
            
            risk_check = self.risk_manager.check_entry_allowed(
                symbol, signal, entry_price, atr
            )
            
            if risk_check['allowed']:
                # 仮想取引実行
                position = self.risk_manager.add_position(
                    symbol=symbol,
                    direction=signal,
                    size=risk_check['position_size'],
                    entry_price=entry_price,
                    stop_loss=risk_check['stop_loss'],
                    take_profit=risk_check['take_profit']
                )
                
                self.trades_attempted += 1
                
                # 即座にクローズ（テスト用）
                import random
                exit_price = entry_price * (1 + random.gauss(0, 0.01))
                self.risk_manager.close_position(position, exit_price)
        
        except Exception as e:
            await self.error_handler.handle_exception(e, "IntegratedStrategy")
    
    def _generate_signal(self, indicators: Dict) -> int:
        """シンプルなシグナル生成"""
        sma20 = indicators.get('sma_20', 0)
        ema12 = indicators.get('ema_12', 0)
        
        if sma20 == 0 or ema12 == 0:
            return 0
        
        # EMAとSMAのクロス
        if ema12 > sma20 * 1.002:  # 0.2%以上上
            return 1  # 買い
        elif ema12 < sma20 * 0.998:  # 0.2%以上下
            return 2  # 売り
        
        return 0


async def main():
    """統合システムテスト実行"""
    
    test_system = ComprehensiveSystemTest()
    
    try:
        # 30秒間の包括テスト実行
        results = await test_system.run_comprehensive_test(duration_seconds=30)
        
        # 結果に基づく推奨事項
        print("\n" + "=" * 80)
        print("💡 推奨事項・次のステップ")
        print("=" * 80)
        
        if results.overall_success:
            print("✅ 全システムが正常に動作しています")
            print("✅ Week4のパフォーマンス最適化目標を達成")
            print("✅ Week5の本番環境デプロイ準備に進める状態です")
        else:
            print("⚠️ いくつかの改善点が見つかりました:")
            
            if results.performance_stats.get('avg_response_time', 0) > 19:
                print("   - パフォーマンス最適化の追加調整が必要")
            
            if results.risk_management_stats.get('is_trading_halted'):
                print("   - リスク管理設定の見直しが必要")
            
            if results.error_handling_stats.get('is_failsafe_mode'):
                print("   - エラー処理ロジックの調整が必要")
        
        return results
        
    finally:
        # システム停止
        test_system.event_engine.stop()


if __name__ == "__main__":
    asyncio.run(main())