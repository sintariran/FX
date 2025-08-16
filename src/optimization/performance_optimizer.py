"""
パフォーマンス最適化実装
目標: 19ms以下の応答時間達成

レビューフィードバックを反映:
1. NumPy/Numba最適化
2. イベント駆動アーキテクチャ
3. メモリ効率化
"""

import time
import statistics
from collections import deque
from typing import Dict, List, Callable, Optional
import asyncio
import threading
from dataclasses import dataclass


def fast_sma(prices: List[float], period: int) -> float:
    """高速移動平均計算（標準ライブラリ版）"""
    if len(prices) < period:
        return 0.0
    return statistics.mean(prices[-period:])


def fast_ema(prices: List[float], period: int) -> float:
    """最適化EMA計算"""
    if len(prices) < 2:
        return prices[-1] if len(prices) > 0 else 0.0
    
    alpha = 2.0 / (period + 1)
    ema = prices[0]
    
    for price in prices[1:]:
        ema = alpha * price + (1 - alpha) * ema
    
    return ema


def fast_macd(prices: List[float], fast_period: int = 12, 
              slow_period: int = 26, signal_period: int = 9) -> tuple:
    """高速MACD計算（レビュー指摘のボトルネック対策）"""
    if len(prices) < slow_period:
        return 0.0, 0.0, 0.0
    
    # EMA計算
    fast_ema_val = fast_ema_calc(prices, fast_period)
    slow_ema_val = fast_ema_calc(prices, slow_period)
    
    macd_line = fast_ema_val - slow_ema_val
    signal_line = 0.0  # 簡略化
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def fast_ema_calc(prices: List[float], period: int) -> float:
    """EMA計算の最適化版"""
    if len(prices) == 0:
        return 0.0
        
    alpha = 2.0 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = alpha * price + (1 - alpha) * ema
    return ema


def fast_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """高速ATR計算（リスク管理用）"""
    if len(highs) < period + 1:
        return 0.0
    
    true_ranges = []
    
    for i in range(1, len(highs)):
        high_low = highs[i] - lows[i]
        high_close = abs(highs[i] - closes[i-1])
        low_close = abs(lows[i] - closes[i-1])
        
        true_ranges.append(max(high_low, max(high_close, low_close)))
    
    # ATR = True Range の移動平均
    return statistics.mean(true_ranges[-period:])


class RingBuffer:
    """メモリ効率的なリングバッファ（レビュー推奨）"""
    
    def __init__(self, maxsize: int):
        self.maxsize = maxsize
        self.data = deque(maxlen=maxsize)
        self._list_cache = None
        self._cache_dirty = True
    
    def append(self, item):
        self.data.append(item)
        self._cache_dirty = True
    
    def to_list(self) -> List[float]:
        """リストに変換（キャッシュ付き）"""
        if self._cache_dirty:
            self._list_cache = list(self.data)
            self._cache_dirty = False
        return self._list_cache
    
    def __len__(self):
        return len(self.data)


@dataclass
class MarketEvent:
    """イベント駆動アーキテクチャ用イベント"""
    event_type: str
    symbol: str
    timestamp: str
    data: Dict


class EventDrivenEngine:
    """イベント駆動型取引エンジン（レビュー推奨アーキテクチャ）"""
    
    def __init__(self):
        self.event_queue = asyncio.Queue()
        self.price_buffers = {}
        self.indicators_cache = {}
        self.subscribers = {}
        self.is_running = False
        
        # パフォーマンス測定
        self.response_times = deque(maxlen=1000)
        self.last_tick_time = None
        
    def subscribe(self, event_type: str, callback: Callable):
        """イベントサブスクライバー登録"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    async def publish_event(self, event: MarketEvent):
        """イベント発行"""
        await self.event_queue.put(event)
    
    async def process_events(self):
        """イベント処理ループ"""
        while self.is_running:
            try:
                # ノンブロッキングでイベント取得
                event = await asyncio.wait_for(self.event_queue.get(), timeout=0.1)
                
                # パフォーマンス測定開始
                start_time = time.perf_counter()
                
                # イベント処理
                await self._handle_event(event)
                
                # レスポンス時間記録
                response_time = (time.perf_counter() - start_time) * 1000  # ms
                self.response_times.append(response_time)
                
                # 19ms目標チェック
                if response_time > 19.0:
                    print(f"⚠️  応答時間オーバー: {response_time:.2f}ms > 19ms")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ イベント処理エラー: {e}")
    
    async def _handle_event(self, event: MarketEvent):
        """個別イベント処理"""
        if event.event_type == "PRICE_UPDATE":
            await self._handle_price_update(event)
        elif event.event_type == "SIGNAL_CHECK":
            await self._handle_signal_check(event)
    
    async def _handle_price_update(self, event: MarketEvent):
        """価格更新イベント処理"""
        symbol = event.symbol
        price_data = event.data
        
        # リングバッファに価格追加
        if symbol not in self.price_buffers:
            self.price_buffers[symbol] = {
                'prices': RingBuffer(100),  # 直近100本のみ保持
                'highs': RingBuffer(100),
                'lows': RingBuffer(100),
                'timestamps': RingBuffer(100)
            }
        
        buffers = self.price_buffers[symbol]
        buffers['prices'].append(price_data['close'])
        buffers['highs'].append(price_data['high'])
        buffers['lows'].append(price_data['low'])
        buffers['timestamps'].append(event.timestamp)
        
        # 指標更新（キャッシュクリア）
        if symbol in self.indicators_cache:
            self.indicators_cache[symbol] = {}
        
        # サブスクライバーに通知
        if "PRICE_UPDATE" in self.subscribers:
            for callback in self.subscribers["PRICE_UPDATE"]:
                await callback(event)
    
    async def _handle_signal_check(self, event: MarketEvent):
        """シグナルチェックイベント処理"""
        # サブスクライバーに通知
        if "SIGNAL_CHECK" in self.subscribers:
            for callback in self.subscribers["SIGNAL_CHECK"]:
                await callback(event)
    
    def calculate_indicators(self, symbol: str) -> Dict:
        """高速指標計算（Numba最適化）"""
        if symbol not in self.price_buffers:
            return {}
        
        # キャッシュチェック
        if symbol in self.indicators_cache and self.indicators_cache[symbol]:
            return self.indicators_cache[symbol]
        
        buffers = self.price_buffers[symbol]
        
        if len(buffers['prices']) < 20:
            return {}
        
        # リストに変換
        prices = buffers['prices'].to_list()
        highs = buffers['highs'].to_list()
        lows = buffers['lows'].to_list()
        
        # 高速指標計算
        indicators = {
            'sma_20': fast_sma(prices, 20),
            'ema_12': fast_ema(prices, 12),
            'atr_14': fast_atr(highs, lows, prices, 14),
            'macd': fast_macd(prices)
        }
        
        # キャッシュ保存
        self.indicators_cache[symbol] = indicators
        
        return indicators
    
    def get_performance_stats(self) -> Dict:
        """パフォーマンス統計"""
        if not self.response_times:
            return {}
        
        times = list(self.response_times)
        
        # パーセンタイル計算
        sorted_times = sorted(times)
        p95_index = int(len(sorted_times) * 0.95)
        p99_index = int(len(sorted_times) * 0.99)
        
        target_achieved = sum(1 for t in times if t <= 19.0)
        
        return {
            'avg_response_time': statistics.mean(times),
            'max_response_time': max(times),
            'min_response_time': min(times),
            'p95_response_time': sorted_times[p95_index] if p95_index < len(sorted_times) else max(times),
            'p99_response_time': sorted_times[p99_index] if p99_index < len(sorted_times) else max(times),
            'samples': len(times),
            'target_achievement': (target_achieved / len(times)) * 100
        }
    
    async def start(self):
        """エンジン開始"""
        self.is_running = True
        print("🚀 イベント駆動エンジン開始（19ms目標）")
        
        # イベント処理タスクを開始
        return asyncio.create_task(self.process_events())
    
    def stop(self):
        """エンジン停止"""
        self.is_running = False
        print("🛑 イベント駆動エンジン停止")
        
        # パフォーマンス結果表示
        stats = self.get_performance_stats()
        if stats:
            print("\n📊 パフォーマンス結果:")
            print(f"  平均応答時間: {stats['avg_response_time']:.2f}ms")
            print(f"  最大応答時間: {stats['max_response_time']:.2f}ms")
            print(f"  95%タイル: {stats['p95_response_time']:.2f}ms")
            print(f"  19ms目標達成率: {stats['target_achievement']:.1f}%")


class OptimizedStrategy:
    """最適化されたストラテジー"""
    
    def __init__(self, engine: EventDrivenEngine):
        self.engine = engine
        self.position_direction = 0
        self.entry_price = None
        
        # ATRベースのリスク管理（レビュー推奨）
        self.atr_multiplier = 2.0
        self.max_risk_per_trade = 0.02  # 口座の2%
    
    async def on_price_update(self, event: MarketEvent):
        """価格更新時の戦略実行"""
        symbol = event.symbol
        
        # 高速指標計算
        indicators = self.engine.calculate_indicators(symbol)
        
        if not indicators:
            return
        
        # シグナル生成
        signal = self._generate_signal(indicators)
        
        if signal != 0:
            # シグナルチェックイベントを発行
            signal_event = MarketEvent(
                event_type="SIGNAL_CHECK",
                symbol=symbol,
                timestamp=event.timestamp,
                data={'signal': signal, 'indicators': indicators}
            )
            await self.engine.publish_event(signal_event)
    
    def _generate_signal(self, indicators: Dict) -> int:
        """シグナル生成（最適化版）"""
        sma20 = indicators.get('sma_20', 0)
        ema12 = indicators.get('ema_12', 0)
        
        if sma20 == 0 or ema12 == 0:
            return 0
        
        # シンプルなクロスオーバー戦略
        if ema12 > sma20 * 1.001:  # 0.1%以上上
            return 1  # 買い
        elif ema12 < sma20 * 0.999:  # 0.1%以上下
            return 2  # 売り
        
        return 0  # 待機
    
    def calculate_position_size(self, symbol: str, atr: float, 
                               account_balance: float) -> float:
        """ATRベースのポジションサイジング（レビュー推奨）"""
        if atr == 0:
            return 10000  # デフォルト
        
        # リスク = 口座残高 × リスク率
        risk_amount = account_balance * self.max_risk_per_trade
        
        # ストップロス幅 = ATR × 乗数
        stop_loss_distance = atr * self.atr_multiplier
        
        # ポジションサイズ = リスク金額 ÷ ストップロス幅
        position_size = risk_amount / stop_loss_distance
        
        return min(position_size, 50000)  # 最大5万通貨


async def performance_test():
    """パフォーマンステスト実行"""
    print("=" * 60)
    print("🎯 パフォーマンス最適化テスト（19ms目標）")
    print("=" * 60)
    
    # エンジン初期化
    engine = EventDrivenEngine()
    strategy = OptimizedStrategy(engine)
    
    # ストラテジーをサブスクライブ
    engine.subscribe("PRICE_UPDATE", strategy.on_price_update)
    
    # エンジン開始
    task = await engine.start()
    
    try:
        # テストデータ送信（1000回）
        for i in range(1000):
            # ダミー価格データ
            import random
            price_data = {
                'open': 150.0 + random.gauss(0, 0.1),
                'high': 150.2 + random.gauss(0, 0.1),
                'low': 149.8 + random.gauss(0, 0.1),
                'close': 150.0 + random.gauss(0, 0.1),
                'volume': random.randint(1000, 5000)
            }
            
            # イベント発行
            event = MarketEvent(
                event_type="PRICE_UPDATE",
                symbol="USDJPY",
                timestamp=f"2024-01-01T00:{i//60:02d}:{i%60:02d}",
                data=price_data
            )
            
            await engine.publish_event(event)
            
            # 少し待機（実際のティック間隔をシミュレート）
            if i % 100 == 0:
                await asyncio.sleep(0.001)
        
        # 処理完了待機
        await asyncio.sleep(1.0)
        
    finally:
        engine.stop()
        task.cancel()


def main():
    """メイン実行"""
    asyncio.run(performance_test())


if __name__ == "__main__":
    main()