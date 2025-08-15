"""
高度なイベント駆動アーキテクチャ
Week4 最適化: さらなるパフォーマンス向上

新機能:
1. イベントバッチ処理
2. 優先度キュー
3. メモリプール
4. 並行処理ワーカー
5. サーキットブレーカー
"""

import asyncio
import time
import heapq
from collections import deque, defaultdict
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum, IntEnum
import threading
import queue
import statistics
from datetime import datetime, timedelta


class EventPriority(IntEnum):
    """イベント優先度"""
    CRITICAL = 1    # 取引実行、リスクアラート
    HIGH = 2        # 取引シグナル
    NORMAL = 3      # 価格更新
    LOW = 4         # ログ、統計


class CircuitState(Enum):
    """サーキットブレーカー状態"""
    CLOSED = "CLOSED"      # 正常動作
    OPEN = "OPEN"          # 遮断中
    HALF_OPEN = "HALF_OPEN"  # 試験復旧


@dataclass
class PriorityEvent:
    """優先度付きイベント"""
    priority: EventPriority
    timestamp: float
    event_type: str
    symbol: str
    data: Dict
    
    def __lt__(self, other):
        # 優先度が高い（数値が小さい）ほど先に処理
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.timestamp < other.timestamp


@dataclass
class EventBatch:
    """イベントバッチ"""
    events: List[PriorityEvent] = field(default_factory=list)
    created_at: float = field(default_factory=time.perf_counter)
    max_size: int = 50
    max_age_ms: float = 10.0  # 10ms
    
    def can_add(self) -> bool:
        """バッチに追加可能か"""
        if len(self.events) >= self.max_size:
            return False
        
        age_ms = (time.perf_counter() - self.created_at) * 1000
        return age_ms < self.max_age_ms
    
    def add(self, event: PriorityEvent) -> bool:
        """イベント追加"""
        if not self.can_add():
            return False
        
        self.events.append(event)
        return True


class MemoryPool:
    """メモリプール（オブジェクト再利用）"""
    
    def __init__(self):
        self.price_data_pool = queue.Queue()
        self.event_pool = queue.Queue()
        self.batch_pool = queue.Queue()
        
        # プールを事前に満たす
        self._pre_fill_pools()
    
    def _pre_fill_pools(self):
        """プール事前充填"""
        # 価格データオブジェクト
        for _ in range(1000):
            self.price_data_pool.put({})
        
        # バッチオブジェクト
        for _ in range(100):
            self.batch_pool.put(EventBatch())
    
    def get_price_data(self) -> Dict:
        """価格データオブジェクト取得"""
        try:
            data = self.price_data_pool.get_nowait()
            data.clear()  # クリア
            return data
        except queue.Empty:
            return {}  # プール空の場合は新規作成
    
    def return_price_data(self, data: Dict):
        """価格データオブジェクト返却"""
        if self.price_data_pool.qsize() < 1000:
            self.price_data_pool.put(data)
    
    def get_batch(self) -> EventBatch:
        """バッチオブジェクト取得"""
        try:
            batch = self.batch_pool.get_nowait()
            batch.events.clear()
            batch.created_at = time.perf_counter()
            return batch
        except queue.Empty:
            return EventBatch()
    
    def return_batch(self, batch: EventBatch):
        """バッチオブジェクト返却"""
        if self.batch_pool.qsize() < 100:
            self.batch_pool.put(batch)


class CircuitBreaker:
    """サーキットブレーカー（障害時の保護）"""
    
    def __init__(self, failure_threshold: int = 5, 
                 recovery_timeout: float = 30.0,
                 success_threshold: int = 3):
        
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        
        self.total_calls = 0
        self.total_failures = 0
    
    async def call(self, func: Callable, *args, **kwargs):
        """サーキットブレーカー経由での関数呼び出し"""
        self.total_calls += 1
        
        if self.state == CircuitState.OPEN:
            # 復旧試験時間チェック
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            # 関数実行
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # 成功時の処理
            self._on_success()
            return result
            
        except Exception as e:
            # 失敗時の処理
            self._on_failure()
            raise e
    
    def _on_success(self):
        """成功時の処理"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)
    
    def _on_failure(self):
        """失敗時の処理"""
        self.failure_count += 1
        self.total_failures += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def get_stats(self) -> Dict:
        """統計情報取得"""
        return {
            'state': self.state.value,
            'total_calls': self.total_calls,
            'total_failures': self.total_failures,
            'failure_rate': self.total_failures / max(self.total_calls, 1),
            'current_failure_count': self.failure_count
        }


class EventWorker:
    """イベント処理ワーカー"""
    
    def __init__(self, worker_id: int, circuit_breaker: CircuitBreaker):
        self.worker_id = worker_id
        self.circuit_breaker = circuit_breaker
        self.is_running = False
        self.events_processed = 0
        self.processing_times = deque(maxlen=1000)
        self.subscribers = defaultdict(list)
    
    def subscribe(self, event_type: str, callback: Callable):
        """イベントサブスクライバー登録"""
        self.subscribers[event_type].append(callback)
    
    async def process_batch(self, batch: EventBatch) -> Dict:
        """バッチ処理"""
        start_time = time.perf_counter()
        
        results = {
            'processed': 0,
            'errors': 0,
            'duration_ms': 0
        }
        
        try:
            # イベントを優先度順にソート
            batch.events.sort()
            
            for event in batch.events:
                try:
                    # サーキットブレーカー経由で処理
                    await self.circuit_breaker.call(
                        self._process_single_event, event
                    )
                    results['processed'] += 1
                    self.events_processed += 1
                    
                except Exception as e:
                    results['errors'] += 1
                    print(f"❌ ワーカー{self.worker_id}: イベント処理エラー {e}")
            
            # 処理時間記録
            duration_ms = (time.perf_counter() - start_time) * 1000
            results['duration_ms'] = duration_ms
            self.processing_times.append(duration_ms)
            
        except Exception as e:
            print(f"❌ ワーカー{self.worker_id}: バッチ処理エラー {e}")
            results['errors'] += len(batch.events)
        
        return results
    
    async def _process_single_event(self, event: PriorityEvent):
        """単一イベント処理"""
        handlers = self.subscribers.get(event.event_type, [])
        
        for handler in handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
    
    def get_stats(self) -> Dict:
        """ワーカー統計"""
        if self.processing_times:
            avg_time = statistics.mean(self.processing_times)
            max_time = max(self.processing_times)
        else:
            avg_time = max_time = 0
        
        return {
            'worker_id': self.worker_id,
            'events_processed': self.events_processed,
            'avg_processing_time': avg_time,
            'max_processing_time': max_time,
            'circuit_breaker': self.circuit_breaker.get_stats()
        }


class AdvancedEventEngine:
    """高度なイベント駆動エンジン"""
    
    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        
        # イベントキュー（優先度付き）
        self.priority_queue = []
        self.queue_lock = asyncio.Lock()
        
        # バッチ処理
        self.current_batch = None
        self.batch_queue = asyncio.Queue()
        
        # ワーカープール
        self.workers = []
        self.worker_tasks = []
        
        # メモリプール
        self.memory_pool = MemoryPool()
        
        # 統計情報
        self.events_received = 0
        self.events_processed = 0
        self.batches_created = 0
        self.start_time = None
        self.is_running = False
        
        # パフォーマンス測定
        self.response_times = deque(maxlen=10000)
        
        # 初期化
        self._initialize_workers()
    
    def _initialize_workers(self):
        """ワーカー初期化"""
        for i in range(self.num_workers):
            circuit_breaker = CircuitBreaker()
            worker = EventWorker(i, circuit_breaker)
            self.workers.append(worker)
    
    def subscribe(self, event_type: str, callback: Callable, worker_id: Optional[int] = None):
        """イベントサブスクライバー登録"""
        if worker_id is not None:
            # 特定ワーカーに登録
            if 0 <= worker_id < len(self.workers):
                self.workers[worker_id].subscribe(event_type, callback)
        else:
            # 全ワーカーに登録
            for worker in self.workers:
                worker.subscribe(event_type, callback)
    
    async def publish_event(self, event_type: str, symbol: str, data: Dict,
                           priority: EventPriority = EventPriority.NORMAL):
        """イベント発行"""
        event_time = time.perf_counter()
        
        # 優先度付きイベント作成
        priority_event = PriorityEvent(
            priority=priority,
            timestamp=event_time,
            event_type=event_type,
            symbol=symbol,
            data=data
        )
        
        # バッチに追加試行
        if not await self._try_add_to_batch(priority_event):
            # バッチに追加できない場合は新しいバッチ作成
            await self._create_new_batch(priority_event)
        
        self.events_received += 1
    
    async def _try_add_to_batch(self, event: PriorityEvent) -> bool:
        """既存バッチへの追加試行"""
        if self.current_batch and self.current_batch.can_add():
            self.current_batch.add(event)
            return True
        return False
    
    async def _create_new_batch(self, event: PriorityEvent):
        """新しいバッチ作成"""
        # 既存バッチをキューに送信
        if self.current_batch:
            await self.batch_queue.put(self.current_batch)
        
        # 新しいバッチ作成
        self.current_batch = self.memory_pool.get_batch()
        self.current_batch.add(event)
        self.batches_created += 1
    
    async def start(self):
        """エンジン開始"""
        self.is_running = True
        self.start_time = time.perf_counter()
        
        print(f"🚀 高度イベント駆動エンジン開始 ({self.num_workers}ワーカー)")
        
        # ワーカータスク開始
        for worker in self.workers:
            task = asyncio.create_task(self._worker_loop(worker))
            self.worker_tasks.append(task)
        
        # バッチフラッシュタスク
        flush_task = asyncio.create_task(self._batch_flush_loop())
        self.worker_tasks.append(flush_task)
        
        return self.worker_tasks
    
    async def _worker_loop(self, worker: EventWorker):
        """ワーカーループ"""
        worker.is_running = True
        
        while self.is_running:
            try:
                # バッチ取得（タイムアウト付き）
                batch = await asyncio.wait_for(
                    self.batch_queue.get(), timeout=0.1
                )
                
                # バッチ処理
                result = await worker.process_batch(batch)
                
                # 統計更新
                self.events_processed += result['processed']
                
                # レスポンス時間記録
                if result['duration_ms'] > 0:
                    self.response_times.append(result['duration_ms'])
                
                # メモリプールに返却
                self.memory_pool.return_batch(batch)
                
            except asyncio.TimeoutError:
                continue  # タイムアウトは正常
            except Exception as e:
                print(f"❌ ワーカー{worker.worker_id}: ループエラー {e}")
                await asyncio.sleep(0.1)
        
        worker.is_running = False
    
    async def _batch_flush_loop(self):
        """バッチ定期フラッシュ"""
        while self.is_running:
            await asyncio.sleep(0.005)  # 5ms間隔
            
            # 現在のバッチをフラッシュ
            if self.current_batch and self.current_batch.events:
                age_ms = (time.perf_counter() - self.current_batch.created_at) * 1000
                
                if age_ms >= self.current_batch.max_age_ms:
                    await self.batch_queue.put(self.current_batch)
                    self.current_batch = None
    
    def stop(self):
        """エンジン停止"""
        self.is_running = False
        
        # 残りのバッチを処理
        if self.current_batch:
            asyncio.create_task(self.batch_queue.put(self.current_batch))
        
        print("🛑 高度イベント駆動エンジン停止")
        
        # 統計表示
        self._print_final_stats()
    
    def get_performance_stats(self) -> Dict:
        """パフォーマンス統計"""
        if not self.response_times:
            return {}
        
        times = list(self.response_times)
        sorted_times = sorted(times)
        
        return {
            'events_received': self.events_received,
            'events_processed': self.events_processed,
            'batches_created': self.batches_created,
            'avg_response_time': statistics.mean(times),
            'max_response_time': max(times),
            'min_response_time': min(times),
            'p95_response_time': sorted_times[int(len(sorted_times) * 0.95)],
            'p99_response_time': sorted_times[int(len(sorted_times) * 0.99)],
            'throughput_events_per_second': self._calculate_throughput(),
            'worker_stats': [worker.get_stats() for worker in self.workers]
        }
    
    def _calculate_throughput(self) -> float:
        """スループット計算"""
        if not self.start_time:
            return 0.0
        
        elapsed = time.perf_counter() - self.start_time
        return self.events_processed / max(elapsed, 0.001)
    
    def _print_final_stats(self):
        """最終統計表示"""
        stats = self.get_performance_stats()
        
        if stats:
            print("\n📊 高度エンジン パフォーマンス統計:")
            print(f"  受信イベント: {stats['events_received']:,}")
            print(f"  処理イベント: {stats['events_processed']:,}")
            print(f"  作成バッチ: {stats['batches_created']:,}")
            print(f"  平均応答時間: {stats['avg_response_time']:.2f}ms")
            print(f"  95%タイル: {stats['p95_response_time']:.2f}ms")
            print(f"  スループット: {stats['throughput_events_per_second']:.0f}イベント/秒")
            
            print(f"\n👥 ワーカー統計:")
            for worker_stat in stats['worker_stats']:
                worker_id = worker_stat['worker_id']
                processed = worker_stat['events_processed']
                avg_time = worker_stat['avg_processing_time']
                cb_stats = worker_stat['circuit_breaker']
                
                print(f"  ワーカー{worker_id}: {processed:,}イベント, "
                      f"平均{avg_time:.2f}ms, "
                      f"CB:{cb_stats['state']}")


async def demo_advanced_engine():
    """高度エンジンデモ"""
    print("=" * 80)
    print("⚡ 高度イベント駆動エンジン デモ")
    print("=" * 80)
    
    # エンジン初期化
    engine = AdvancedEventEngine(num_workers=4)
    
    # ダミーハンドラー登録
    async def price_handler(event):
        # 軽量な処理のシミュレート
        await asyncio.sleep(0.0001)
    
    async def signal_handler(event):
        # やや重い処理のシミュレート
        await asyncio.sleep(0.001)
    
    engine.subscribe("PRICE_UPDATE", price_handler)
    engine.subscribe("SIGNAL_CHECK", signal_handler)
    
    # エンジン開始
    tasks = await engine.start()
    
    try:
        # 高負荷テスト (60秒間)
        print("🔥 60秒間の高負荷テスト開始")
        
        test_duration = 60
        start_test = time.perf_counter()
        
        while (time.perf_counter() - start_test) < test_duration:
            # 複数通貨ペアの価格データ
            symbols = ["USDJPY", "EURJPY", "EURUSD", "GBPJPY", "AUDJPY"]
            
            for symbol in symbols:
                import random
                
                # 価格更新イベント（通常優先度）
                await engine.publish_event(
                    "PRICE_UPDATE",
                    symbol,
                    {
                        'bid': 150.0 + random.gauss(0, 0.1),
                        'ask': 150.003 + random.gauss(0, 0.1),
                        'volume': random.randint(1000, 5000)
                    },
                    EventPriority.NORMAL
                )
                
                # 時々シグナルイベント（高優先度）
                if random.random() < 0.1:  # 10%の確率
                    await engine.publish_event(
                        "SIGNAL_CHECK",
                        symbol,
                        {'signal': random.choice([1, 2]), 'confidence': random.random()},
                        EventPriority.HIGH
                    )
            
            # 少し待機
            await asyncio.sleep(0.001)
        
        # 処理完了待機
        await asyncio.sleep(2.0)
        
    finally:
        engine.stop()
        
        # タスクのキャンセル
        for task in tasks:
            task.cancel()


if __name__ == "__main__":
    asyncio.run(demo_advanced_engine())