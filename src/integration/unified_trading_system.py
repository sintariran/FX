"""
統合FX取引システム
Week4: 全コンポーネントの統合

機能:
1. 全システムコンポーネントの統合管理
2. リアルタイム監視ダッシュボード
3. ワンストップ制御インターフェース
4. パフォーマンス監視と自動調整
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sys
import os

# パッケージパス追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from optimization.advanced_event_engine import AdvancedEventEngine, EventPriority
from risk_management.enhanced_risk_manager import EnhancedRiskManager, RiskLimits, Position
from monitoring.error_handler import ErrorHandler, AlertLevel
from trading.websocket_stream import StreamingTradingEngine
# import memos.pkg_functions as pkg  # 将来実装予定


@dataclass
class SystemStatus:
    """システム全体状態"""
    timestamp: str
    uptime_seconds: float
    is_running: bool
    
    # パフォーマンス
    events_per_second: float
    avg_response_time: float
    memory_usage_mb: float
    
    # 取引状況
    active_positions: int
    total_pnl: float
    current_balance: float
    drawdown: float
    
    # リスク状況
    is_trading_halted: bool
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    
    # エラー状況
    is_failsafe_mode: bool
    error_count: int
    recent_alerts: int


@dataclass
class TradingMetrics:
    """取引メトリクス"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    max_profit: float
    max_loss: float
    avg_profit: float
    avg_loss: float
    sharpe_ratio: float
    max_drawdown: float


class SystemMonitor:
    """システム監視クラス"""
    
    def __init__(self):
        self.start_time = time.perf_counter()
        self.status_history = []
        self.metrics_history = []
        self.alert_history = []
        
    def record_status(self, status: SystemStatus):
        """状態記録"""
        self.status_history.append(status)
        
        # 1時間以上古いデータは削除
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.status_history = [
            s for s in self.status_history 
            if datetime.fromisoformat(s.timestamp) > cutoff_time
        ]
    
    def get_uptime(self) -> float:
        """稼働時間取得"""
        return time.perf_counter() - self.start_time
    
    def get_system_health(self) -> str:
        """システム健全性評価"""
        if not self.status_history:
            return "UNKNOWN"
        
        latest = self.status_history[-1]
        
        if latest.is_failsafe_mode or latest.error_count > 10:
            return "CRITICAL"
        elif latest.is_trading_halted or latest.error_count > 5:
            return "WARNING"
        elif latest.avg_response_time > 50:  # 50ms超
            return "DEGRADED"
        else:
            return "HEALTHY"


class UnifiedTradingSystem:
    """統合FX取引システム"""
    
    def __init__(self, initial_balance: float = 1000000):
        print("🏗️ 統合FX取引システム初期化中...")
        
        # コアコンポーネント
        self.event_engine = AdvancedEventEngine(num_workers=6)
        self.risk_manager = EnhancedRiskManager(
            initial_balance=initial_balance,
            limits=RiskLimits(
                max_positions=5,
                max_exposure=500000,
                max_daily_loss=50000,
                max_drawdown=0.05,
                max_risk_per_trade=0.015  # 1.5%
            )
        )
        self.error_handler = ErrorHandler()
        
        # 取引エンジン（オプション）
        self.streaming_engine = None
        
        # 監視・制御
        self.monitor = SystemMonitor()
        self.is_running = False
        self.auto_trading_enabled = False
        
        # 統計
        self.trade_history = []
        self.daily_pnl = {}
        
        # PKGストラテジー統合（将来実装予定）
        self.pkg_strategy = None
        
        # イベントハンドラー登録
        self._setup_event_handlers()
        
        print("✅ 統合システム初期化完了")
    
    def _setup_event_handlers(self):
        """イベントハンドラー設定"""
        
        # 価格更新ハンドラー
        self.event_engine.subscribe("PRICE_UPDATE", self._on_price_update)
        
        # シグナルハンドラー
        self.event_engine.subscribe("SIGNAL_CHECK", self._on_signal_check)
        
        # リスクアラートハンドラー
        self.event_engine.subscribe("RISK_ALERT", self._on_risk_alert)
        
        # システムアラートハンドラー
        self.event_engine.subscribe("SYSTEM_ALERT", self._on_system_alert)
    
    async def start_system(self, enable_auto_trading: bool = False):
        """システム開始"""
        print("🚀 統合FX取引システム開始")
        print("=" * 60)
        
        self.is_running = True
        self.auto_trading_enabled = enable_auto_trading
        
        # イベントエンジン開始
        tasks = await self.event_engine.start()
        
        # ストリーミングエンジン開始（オプション）
        if self.streaming_engine:
            await self.streaming_engine.start()
        
        # 監視タスク開始
        monitor_task = asyncio.create_task(self._monitoring_loop())
        tasks.append(monitor_task)
        
        # ステータス表示タスク
        status_task = asyncio.create_task(self._status_display_loop())
        tasks.append(status_task)
        
        if enable_auto_trading:
            print("🤖 自動取引: 有効")
        else:
            print("👀 自動取引: 無効（監視モードのみ）")
        
        return tasks
    
    async def _on_price_update(self, event):
        """価格更新処理"""
        symbol = event.symbol
        price_data = event.data
        
        try:
            # エラーハンドラーでデータ検証
            is_valid = await self.error_handler.validate_and_process_data(
                price_data, f"PriceUpdate_{symbol}"
            )
            
            if not is_valid:
                return
            
            # 現在価格をリスク管理に反映
            current_prices = {symbol: price_data.get('mid', price_data.get('close', 0))}
            self.risk_manager.update_unrealized_pnl(current_prices)
            
            # PKG戦略でシグナル生成
            signal = await self._generate_pkg_signal(symbol, price_data)
            
            if signal != 0 and self.auto_trading_enabled:
                # シグナルチェックイベント発行
                await self.event_engine.publish_event(
                    "SIGNAL_CHECK",
                    symbol,
                    {
                        'signal': signal,
                        'price_data': price_data,
                        'confidence': 0.8
                    },
                    EventPriority.HIGH
                )
        
        except Exception as e:
            await self.error_handler.handle_exception(e, "PriceUpdateHandler")
    
    async def _on_signal_check(self, event):
        """シグナルチェック処理"""
        symbol = event.symbol
        signal_data = event.data
        
        try:
            signal = signal_data['signal']
            price_data = signal_data['price_data']
            
            # リスク管理チェック
            entry_price = price_data.get('mid', price_data.get('close', 0))
            atr = self._calculate_atr(symbol)  # 簡易ATR計算
            
            risk_check = self.risk_manager.check_entry_allowed(
                symbol, signal, entry_price, atr
            )
            
            if risk_check['allowed']:
                # 取引執行
                await self._execute_trade(symbol, signal, risk_check)
            else:
                # リスクアラート発行
                await self.event_engine.publish_event(
                    "RISK_ALERT",
                    symbol,
                    {
                        'reason': risk_check['reason'],
                        'signal': signal,
                        'rejected_at': datetime.now().isoformat()
                    },
                    EventPriority.CRITICAL
                )
        
        except Exception as e:
            await self.error_handler.handle_exception(e, "SignalCheckHandler")
    
    async def _on_risk_alert(self, event):
        """リスクアラート処理"""
        await self.error_handler.alert_manager.send_alert(
            AlertLevel.WARNING,
            f"リスクアラート: {event.data['reason']}",
            f"RiskManager_{event.symbol}"
        )
    
    async def _on_system_alert(self, event):
        """システムアラート処理"""
        await self.error_handler.alert_manager.send_alert(
            AlertLevel.CRITICAL,
            f"システムアラート: {event.data.get('message', 'Unknown')}",
            "UnifiedSystem"
        )
    
    async def _generate_pkg_signal(self, symbol: str, price_data: Dict) -> int:
        """PKG戦略シグナル生成"""
        try:
            # 簡易的なPKG戦略実装
            close_price = price_data.get('mid', price_data.get('close', 0))
            
            if close_price == 0:
                return 0
            
            # ここで実際のPKG関数を呼び出す
            # 現在は簡易実装
            import random
            
            # 5%の確率でシグナル生成
            if random.random() < 0.05:
                return random.choice([1, 2])  # 買い or 売り
            
            return 0  # 待機
            
        except Exception as e:
            await self.error_handler.handle_exception(e, "PKGSignalGenerator")
            return 0
    
    def _calculate_atr(self, symbol: str) -> float:
        """簡易ATR計算"""
        # 実際の実装では過去データから計算
        # 現在は固定値
        atr_defaults = {
            "USDJPY": 0.30,
            "EURJPY": 0.35,
            "EURUSD": 0.0003,
            "GBPJPY": 0.40
        }
        return atr_defaults.get(symbol, 0.30)
    
    async def _execute_trade(self, symbol: str, signal: int, risk_check: Dict):
        """取引執行"""
        try:
            # ポジション作成
            position = self.risk_manager.add_position(
                symbol=symbol,
                direction=signal,
                size=risk_check['position_size'],
                entry_price=risk_check.get('entry_price', 150.0),
                stop_loss=risk_check.get('stop_loss', 0),
                take_profit=risk_check.get('take_profit', 0)
            )
            
            # 取引記録
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'direction': 'BUY' if signal == 1 else 'SELL',
                'size': position.size,
                'entry_price': position.entry_price,
                'stop_loss': position.stop_loss,
                'take_profit': position.take_profit
            }
            
            self.trade_history.append(trade_record)
            
            print(f"✅ 取引執行: {trade_record['symbol']} {trade_record['direction']} "
                  f"{trade_record['size']:,.0f}通貨 @ {trade_record['entry_price']}")
            
        except Exception as e:
            await self.error_handler.handle_exception(e, "TradeExecution")
    
    async def _monitoring_loop(self):
        """監視ループ"""
        while self.is_running:
            try:
                # システム状態収集
                status = await self._collect_system_status()
                
                # 状態記録
                self.monitor.record_status(status)
                
                # 健全性チェック
                health = self.monitor.get_system_health()
                
                if health in ["CRITICAL", "WARNING"]:
                    await self.event_engine.publish_event(
                        "SYSTEM_ALERT",
                        "SYSTEM",
                        {'message': f'システム健全性: {health}', 'status': asdict(status)},
                        EventPriority.CRITICAL
                    )
                
                await asyncio.sleep(5.0)  # 5秒間隔
                
            except Exception as e:
                await self.error_handler.handle_exception(e, "MonitoringLoop")
                await asyncio.sleep(10.0)
    
    async def _collect_system_status(self) -> SystemStatus:
        """システム状態収集"""
        
        # パフォーマンス統計
        perf_stats = self.event_engine.get_performance_stats()
        
        # リスク管理統計
        risk_stats = self.risk_manager.get_risk_metrics()
        
        # エラーハンドラー統計
        error_stats = self.error_handler.get_system_status()
        
        # メモリ使用量（簡易）
        try:
            import psutil
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        except ImportError:
            memory_mb = 0.0  # psutil利用不可の場合
        
        return SystemStatus(
            timestamp=datetime.now().isoformat(),
            uptime_seconds=self.monitor.get_uptime(),
            is_running=self.is_running,
            
            events_per_second=perf_stats.get('throughput_events_per_second', 0),
            avg_response_time=perf_stats.get('avg_response_time', 0),
            memory_usage_mb=memory_mb,
            
            active_positions=risk_stats['open_positions'],
            total_pnl=risk_stats['current_balance'] - 1000000,  # 初期残高からの差分
            current_balance=risk_stats['current_balance'],
            drawdown=risk_stats['current_drawdown'],
            
            is_trading_halted=risk_stats['is_trading_halted'],
            risk_level=self._evaluate_risk_level(risk_stats),
            
            is_failsafe_mode=error_stats['is_failsafe_mode'],
            error_count=error_stats['health']['error_count'],
            recent_alerts=len(self.error_handler.alert_manager.get_recent_alerts(1))
        )
    
    def _evaluate_risk_level(self, risk_stats: Dict) -> str:
        """リスクレベル評価"""
        if risk_stats['current_drawdown'] > 0.04:  # 4%超
            return "CRITICAL"
        elif risk_stats['current_drawdown'] > 0.02:  # 2%超
            return "HIGH"
        elif risk_stats['consecutive_losses'] > 3:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def _status_display_loop(self):
        """ステータス表示ループ"""
        while self.is_running:
            try:
                await asyncio.sleep(10.0)  # 10秒間隔
                
                if self.monitor.status_history:
                    await self._display_dashboard()
                
            except Exception as e:
                print(f"❌ ダッシュボード表示エラー: {e}")
                await asyncio.sleep(30.0)
    
    async def _display_dashboard(self):
        """ダッシュボード表示"""
        
        if not self.monitor.status_history:
            return
        
        status = self.monitor.status_history[-1]
        health = self.monitor.get_system_health()
        
        # ヘルスアイコン
        health_icons = {
            "HEALTHY": "🟢",
            "DEGRADED": "🟡", 
            "WARNING": "🟠",
            "CRITICAL": "🔴"
        }
        
        # 画面クリア（簡易）
        print("\033[2J\033[H")  # ANSI escape codes
        
        print("=" * 80)
        print(f"🎯 統合FX取引システム ダッシュボード {health_icons.get(health, '⚪')} {health}")
        print("=" * 80)
        
        print(f"📅 時刻: {status.timestamp}")
        print(f"⏱️  稼働時間: {status.uptime_seconds/3600:.1f}時間")
        print(f"🤖 自動取引: {'有効' if self.auto_trading_enabled else '無効'}")
        
        print(f"\n📊 パフォーマンス:")
        print(f"  イベント処理: {status.events_per_second:.0f}イベント/秒")
        print(f"  平均応答時間: {status.avg_response_time:.2f}ms")
        print(f"  メモリ使用量: {status.memory_usage_mb:.1f}MB")
        
        print(f"\n💹 取引状況:")
        print(f"  アクティブポジション: {status.active_positions}")
        print(f"  現在残高: ¥{status.current_balance:,.0f}")
        print(f"  総損益: ¥{status.total_pnl:,.0f}")
        print(f"  ドローダウン: {status.drawdown:.1%}")
        
        print(f"\n🛡️ リスク状況:")
        print(f"  リスクレベル: {status.risk_level}")
        print(f"  取引停止: {'Yes' if status.is_trading_halted else 'No'}")
        
        print(f"\n🚨 システム状況:")
        print(f"  フェイルセーフ: {'Yes' if status.is_failsafe_mode else 'No'}")
        print(f"  エラー数: {status.error_count}")
        print(f"  最近のアラート: {status.recent_alerts}")
        
        print(f"\n📈 取引履歴: {len(self.trade_history)}件")
        
        if self.trade_history:
            print("  最近の取引:")
            for trade in self.trade_history[-3:]:  # 最新3件
                print(f"    {trade['timestamp'][:19]} {trade['symbol']} "
                      f"{trade['direction']} {trade['size']:,.0f}")
    
    def stop_system(self):
        """システム停止"""
        print("\n🛑 統合システム停止中...")
        
        self.is_running = False
        self.event_engine.stop()
        
        if self.streaming_engine:
            asyncio.create_task(self.streaming_engine.stop())
        
        print("✅ 統合システム停止完了")
    
    def get_trading_metrics(self) -> TradingMetrics:
        """取引メトリクス取得"""
        if not self.trade_history:
            return TradingMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        # 実装省略（実際は詳細な計算）
        return TradingMetrics(
            total_trades=len(self.trade_history),
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_pnl=0.0,
            max_profit=0.0,
            max_loss=0.0,
            avg_profit=0.0,
            avg_loss=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0
        )


async def demo_unified_system():
    """統合システムデモ"""
    
    # システム初期化
    system = UnifiedTradingSystem(initial_balance=1000000)
    
    try:
        # システム開始（監視モード）
        tasks = await system.start_system(enable_auto_trading=False)
        
        # ダミーイベント送信
        print("\n🔄 ダミーイベント送信開始...")
        
        symbols = ["USDJPY", "EURJPY", "EURUSD"]
        
        for i in range(100):  # 100個のイベント
            import random
            
            symbol = random.choice(symbols)
            
            # 価格データ
            await system.event_engine.publish_event(
                "PRICE_UPDATE",
                symbol,
                {
                    'bid': 150.0 + random.gauss(0, 0.1),
                    'ask': 150.003 + random.gauss(0, 0.1),
                    'mid': 150.0015 + random.gauss(0, 0.1),
                    'volume': random.randint(1000, 5000)
                },
                EventPriority.NORMAL
            )
            
            await asyncio.sleep(0.1)
        
        # 少し待機してダッシュボード確認
        print("\n📊 30秒間ダッシュボード監視...")
        await asyncio.sleep(30)
        
    finally:
        system.stop_system()
        
        # タスクキャンセル
        for task in tasks:
            if not task.cancelled():
                task.cancel()


if __name__ == "__main__":
    asyncio.run(demo_unified_system())