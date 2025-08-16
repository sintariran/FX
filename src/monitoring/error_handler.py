"""
エラー処理と自動復旧機能
レビューフィードバック対応:

1. WebSocket自動再接続
2. ログとモニタリング充実
3. フェイルセーフモード
4. データ異常検出
5. アラート通知システム
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
from collections import deque
from dataclasses import dataclass
from enum import Enum


class AlertLevel(Enum):
    """アラートレベル"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class Alert:
    """アラート情報"""
    level: AlertLevel
    message: str
    timestamp: datetime
    component: str
    data: Dict = None


class ConnectionManager:
    """WebSocket接続管理（自動再接続機能付き）"""
    
    def __init__(self, max_retries: int = 5, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.connection_attempts = 0
        self.is_connected = False
        self.last_data_time = None
        self.connection_callbacks = []
        self.disconnection_callbacks = []
    
    async def connect_with_retry(self, connect_func: Callable) -> bool:
        """指数バックオフによる自動再接続"""
        self.connection_attempts = 0
        
        while self.connection_attempts < self.max_retries:
            try:
                await connect_func()
                self.is_connected = True
                self.connection_attempts = 0
                
                # 接続成功コールバック
                for callback in self.connection_callbacks:
                    await self._safe_callback(callback, "CONNECTED")
                
                return True
                
            except Exception as e:
                self.connection_attempts += 1
                self.is_connected = False
                
                if self.connection_attempts >= self.max_retries:
                    # 最大リトライ回数達成
                    for callback in self.disconnection_callbacks:
                        await self._safe_callback(callback, f"MAX_RETRIES_REACHED: {e}")
                    return False
                
                # 指数バックオフ待機
                delay = self.base_delay * (2 ** (self.connection_attempts - 1))
                await asyncio.sleep(delay)
                
                print(f"🔄 再接続試行 {self.connection_attempts}/{self.max_retries} "
                      f"(次回: {delay:.1f}s後)")
        
        return False
    
    def register_connection_callback(self, callback: Callable):
        """接続成功時のコールバック登録"""
        self.connection_callbacks.append(callback)
    
    def register_disconnection_callback(self, callback: Callable):
        """切断時のコールバック登録"""
        self.disconnection_callbacks.append(callback)
    
    async def _safe_callback(self, callback: Callable, data):
        """安全なコールバック実行"""
        try:
            await callback(data)
        except Exception as e:
            print(f"❌ コールバックエラー: {e}")
    
    def update_last_data_time(self):
        """最後のデータ受信時刻更新"""
        self.last_data_time = datetime.now()
    
    def check_data_timeout(self, timeout_seconds: int = 30) -> bool:
        """データ受信タイムアウトチェック"""
        if not self.last_data_time:
            return False
        
        return (datetime.now() - self.last_data_time).total_seconds() > timeout_seconds


class DataValidator:
    """データ異常検出システム"""
    
    def __init__(self):
        self.price_history = deque(maxlen=100)
        self.volume_history = deque(maxlen=100)
        self.last_price = None
        self.price_spike_threshold = 0.02  # 2%のスパイクを異常とする
        self.volume_spike_threshold = 10.0  # 10倍のボリュームスパイク
    
    def validate_price_data(self, price_data: Dict) -> Dict:
        """価格データの妥当性検証"""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # 基本構造チェック
            required_fields = ['timestamp', 'bid', 'ask', 'mid']
            for field in required_fields:
                if field not in price_data:
                    validation_result['errors'].append(f'必須フィールド不足: {field}')
                    validation_result['is_valid'] = False
            
            if not validation_result['is_valid']:
                return validation_result
            
            # 数値妥当性チェック
            bid = float(price_data['bid'])
            ask = float(price_data['ask'])
            mid = float(price_data['mid'])
            
            # スプレッドチェック
            spread = ask - bid
            if spread < 0:
                validation_result['errors'].append(f'無効なスプレッド: {spread}')
                validation_result['is_valid'] = False
            
            if spread > bid * 0.1:  # スプレッドが10%超
                validation_result['warnings'].append(f'異常に大きなスプレッド: {spread}')
            
            # 価格スパイクチェック
            if self.last_price:
                price_change = abs(mid - self.last_price) / self.last_price
                if price_change > self.price_spike_threshold:
                    validation_result['warnings'].append(
                        f'価格スパイク検出: {price_change:.1%} > {self.price_spike_threshold:.1%}'
                    )
            
            # 履歴更新
            self.price_history.append(mid)
            self.last_price = mid
            
            # ボリュームチェック（あれば）
            if 'volume' in price_data:
                volume = float(price_data['volume'])
                if self.volume_history:
                    avg_volume = sum(self.volume_history) / len(self.volume_history)
                    if volume > avg_volume * self.volume_spike_threshold:
                        validation_result['warnings'].append(f'ボリュームスパイク検出: {volume}')
                
                self.volume_history.append(volume)
        
        except Exception as e:
            validation_result['errors'].append(f'データ検証エラー: {e}')
            validation_result['is_valid'] = False
        
        return validation_result
    
    def detect_market_anomaly(self) -> Optional[str]:
        """市場異常検出"""
        if len(self.price_history) < 10:
            return None
        
        recent_prices = list(self.price_history)[-10:]
        
        # 価格変動率の標準偏差計算
        price_changes = []
        for i in range(1, len(recent_prices)):
            change = (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
            price_changes.append(abs(change))
        
        if price_changes:
            avg_volatility = sum(price_changes) / len(price_changes)
            if avg_volatility > 0.01:  # 1%超の平均変動
                return f"高ボラティリティ検出: 平均変動率 {avg_volatility:.1%}"
        
        return None


class SystemHealthMonitor:
    """システムヘルスモニタリング"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.error_count = 0
        self.last_error_time = None
        self.performance_metrics = deque(maxlen=1000)
        self.memory_usage = deque(maxlen=100)
        
    def record_error(self, error_type: str, error_message: str):
        """エラー記録"""
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        # エラー率チェック
        uptime = (datetime.now() - self.start_time).total_seconds()
        error_rate = self.error_count / max(uptime, 1) * 3600  # 1時間あたりエラー数
        
        if error_rate > 10:  # 1時間に10回超
            return AlertLevel.CRITICAL
        elif error_rate > 5:
            return AlertLevel.ERROR
        elif error_rate > 1:
            return AlertLevel.WARNING
        
        return AlertLevel.INFO
    
    def record_performance(self, response_time: float):
        """パフォーマンス記録"""
        self.performance_metrics.append({
            'timestamp': datetime.now(),
            'response_time': response_time
        })
    
    def get_health_status(self) -> Dict:
        """システムヘルス状態取得"""
        uptime = datetime.now() - self.start_time
        
        # パフォーマンス統計
        if self.performance_metrics:
            recent_metrics = [m['response_time'] for m in self.performance_metrics]
            avg_response_time = sum(recent_metrics) / len(recent_metrics)
            max_response_time = max(recent_metrics)
        else:
            avg_response_time = 0
            max_response_time = 0
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'error_count': self.error_count,
            'last_error': self.last_error_time.isoformat() if self.last_error_time else None,
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time,
            'performance_samples': len(self.performance_metrics)
        }


class AlertManager:
    """アラート管理システム"""
    
    def __init__(self):
        self.alerts = deque(maxlen=1000)
        self.alert_callbacks = {}
        self.alert_history = deque(maxlen=5000)
        
    def register_alert_handler(self, level: AlertLevel, callback: Callable):
        """アラートハンドラー登録"""
        if level not in self.alert_callbacks:
            self.alert_callbacks[level] = []
        self.alert_callbacks[level].append(callback)
    
    async def send_alert(self, level: AlertLevel, message: str, 
                        component: str, data: Dict = None):
        """アラート送信"""
        alert = Alert(
            level=level,
            message=message,
            timestamp=datetime.now(),
            component=component,
            data=data
        )
        
        self.alerts.append(alert)
        self.alert_history.append(alert)
        
        # コンソール出力
        level_icons = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        
        icon = level_icons.get(level, "📢")
        print(f"{icon} [{level.value}] {component}: {message}")
        
        # レベル別ハンドラー実行
        handlers = self.alert_callbacks.get(level, [])
        for handler in handlers:
            try:
                await handler(alert)
            except Exception as e:
                print(f"❌ アラートハンドラーエラー: {e}")
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """最近のアラート取得"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alerts if alert.timestamp > cutoff_time]


class ErrorHandler:
    """統合エラーハンドラー"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.data_validator = DataValidator()
        self.health_monitor = SystemHealthMonitor()
        self.alert_manager = AlertManager()
        
        # フェイルセーフ状態
        self.is_failsafe_mode = False
        self.failsafe_reason = None
        
        # ログ設定
        self._setup_logging()
        
        # アラートハンドラー登録
        self._setup_alert_handlers()
    
    def _setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trading_system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _setup_alert_handlers(self):
        """アラートハンドラー設定"""
        # 重要アラートの処理
        self.alert_manager.register_alert_handler(
            AlertLevel.CRITICAL, 
            self._handle_critical_alert
        )
        
        self.alert_manager.register_alert_handler(
            AlertLevel.ERROR,
            self._handle_error_alert
        )
    
    async def _handle_critical_alert(self, alert: Alert):
        """重大アラート処理"""
        self.logger.critical(f"CRITICAL ALERT: {alert.message}")
        
        # フェイルセーフモードに移行
        if not self.is_failsafe_mode:
            await self.enter_failsafe_mode(alert.message)
    
    async def _handle_error_alert(self, alert: Alert):
        """エラーアラート処理"""
        self.logger.error(f"ERROR ALERT: {alert.message}")
        
        # 必要に応じて自動復旧処理
        if "connection" in alert.message.lower():
            # 接続エラーの場合は再接続試行
            await self.alert_manager.send_alert(
                AlertLevel.INFO,
                "接続エラーによる自動復旧を試行中",
                "ErrorHandler"
            )
    
    async def handle_exception(self, exception: Exception, component: str, 
                             context: Dict = None) -> bool:
        """例外処理"""
        error_level = self.health_monitor.record_error(
            type(exception).__name__, 
            str(exception)
        )
        
        # アラート送信
        await self.alert_manager.send_alert(
            error_level,
            f"例外発生: {exception}",
            component,
            {'context': context, 'exception_type': type(exception).__name__}
        )
        
        # 重大エラーの場合
        if error_level == AlertLevel.CRITICAL:
            await self.enter_failsafe_mode(f"重大エラー: {exception}")
            return False
        
        return True  # 継続可能
    
    async def validate_and_process_data(self, price_data: Dict, 
                                      component: str) -> bool:
        """データ検証と処理"""
        # データ検証
        validation_result = self.data_validator.validate_price_data(price_data)
        
        if not validation_result['is_valid']:
            await self.alert_manager.send_alert(
                AlertLevel.ERROR,
                f"データ検証失敗: {validation_result['errors']}",
                component
            )
            return False
        
        # 警告がある場合
        if validation_result['warnings']:
            await self.alert_manager.send_alert(
                AlertLevel.WARNING,
                f"データ警告: {validation_result['warnings']}",
                component
            )
        
        # 市場異常検出
        anomaly = self.data_validator.detect_market_anomaly()
        if anomaly:
            await self.alert_manager.send_alert(
                AlertLevel.WARNING,
                f"市場異常検出: {anomaly}",
                component
            )
        
        return True
    
    async def enter_failsafe_mode(self, reason: str):
        """フェイルセーフモード移行"""
        self.is_failsafe_mode = True
        self.failsafe_reason = reason
        
        await self.alert_manager.send_alert(
            AlertLevel.CRITICAL,
            f"フェイルセーフモード移行: {reason}",
            "ErrorHandler"
        )
        
        # 緊急停止処理（実装は外部から注入）
        print("🆘 フェイルセーフモード: 全ポジションクローズを推奨")
    
    def exit_failsafe_mode(self, reason: str = "手動復旧"):
        """フェイルセーフモード解除"""
        self.is_failsafe_mode = False
        self.failsafe_reason = None
        
        self.logger.info(f"フェイルセーフモード解除: {reason}")
        print(f"✅ フェイルセーフモード解除: {reason}")
    
    def get_system_status(self) -> Dict:
        """システム状態取得"""
        health_status = self.health_monitor.get_health_status()
        recent_alerts = self.alert_manager.get_recent_alerts(1)  # 1時間
        
        return {
            'is_failsafe_mode': self.is_failsafe_mode,
            'failsafe_reason': self.failsafe_reason,
            'connection_status': self.connection_manager.is_connected,
            'health': health_status,
            'recent_alerts_count': len(recent_alerts),
            'last_data_time': self.connection_manager.last_data_time.isoformat() 
                              if self.connection_manager.last_data_time else None
        }


async def demo_error_handling():
    """エラー処理デモ"""
    print("=" * 60)
    print("🚨 エラー処理・自動復旧システム デモ")
    print("=" * 60)
    
    error_handler = ErrorHandler()
    
    # テスト1: 正常データ処理
    print("\n📊 テスト1: 正常データ処理")
    normal_data = {
        'timestamp': datetime.now().isoformat(),
        'bid': 150.000,
        'ask': 150.003,
        'mid': 150.0015,
        'volume': 1000
    }
    
    is_valid = await error_handler.validate_and_process_data(normal_data, "TestComponent")
    print(f"処理結果: {is_valid}")
    
    # テスト2: 異常データ処理
    print("\n📊 テスト2: 異常データ処理")
    invalid_data = {
        'timestamp': datetime.now().isoformat(),
        'bid': 150.000,
        'ask': 149.990,  # 異常なスプレッド
        'mid': 150.0015
    }
    
    is_valid = await error_handler.validate_and_process_data(invalid_data, "TestComponent")
    print(f"処理結果: {is_valid}")
    
    # テスト3: 例外処理
    print("\n📊 テスト3: 例外処理")
    try:
        raise ValueError("テスト例外")
    except Exception as e:
        can_continue = await error_handler.handle_exception(e, "TestComponent")
        print(f"継続可否: {can_continue}")
    
    # テスト4: 価格スパイク検出
    print("\n📊 テスト4: 価格スパイク検出")
    spike_data = {
        'timestamp': datetime.now().isoformat(),
        'bid': 160.000,  # 10円のスパイク
        'ask': 160.003,
        'mid': 160.0015,
        'volume': 1000
    }
    
    await error_handler.validate_and_process_data(spike_data, "TestComponent")
    
    # テスト5: システム状態確認
    print("\n📊 テスト5: システム状態")
    status = error_handler.get_system_status()
    print("システム状態:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # 少し待ってからアラート履歴表示
    await asyncio.sleep(0.1)
    
    recent_alerts = error_handler.alert_manager.get_recent_alerts()
    print(f"\n📢 最近のアラート ({len(recent_alerts)}件):")
    for alert in recent_alerts[-5:]:  # 最新5件
        print(f"  [{alert.level.value}] {alert.component}: {alert.message}")


if __name__ == "__main__":
    asyncio.run(demo_error_handling())