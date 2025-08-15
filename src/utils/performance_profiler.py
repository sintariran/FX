"""
パフォーマンスプロファイラー
レビューフィードバックに基づく性能計測・最適化ツール

各処理の実行時間を詳細に計測し、ボトルネックを特定
"""

import time
import cProfile
import pstats
import io
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class TimingRecord:
    """タイミング記録"""
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self):
        """計測完了"""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration_ms = (self.end_time - self.start_time) * 1000


class PerformanceProfiler:
    """
    パフォーマンスプロファイラー
    
    目標達成状況：
    - 全体: 19ms
    - もみ: 77ms
    - OP分岐: 101.3ms
    - オーバーシュート: 550.6ms
    """
    
    # パフォーマンス目標（ミリ秒）
    TARGETS = {
        '全体': 19.0,
        'もみ': 77.0,
        'OP分岐': 101.3,
        'オーバーシュート': 550.6,
        '時間結合': 564.9,
        '同逆判定': 10.0,  # 推定値
        '行帰判定': 8.0,   # 推定値
        'DAG評価': 15.0,   # 推定値
    }
    
    def __init__(self, enable_cprofile: bool = False):
        """
        Args:
            enable_cprofile: cProfileによる詳細プロファイリング有効化
        """
        self.enable_cprofile = enable_cprofile
        self.timings: List[TimingRecord] = []
        self.operation_stats: Dict[str, List[float]] = defaultdict(list)
        self.active_timings: Dict[str, TimingRecord] = {}
        self.lock = threading.Lock()
        self.profiler: Optional[cProfile.Profile] = None
        
    @contextmanager
    def measure(self, operation: str, **metadata):
        """
        処理時間計測コンテキストマネージャー
        
        Usage:
            with profiler.measure('同逆判定', timeframe='M1'):
                # 処理実行
                pass
        """
        record = TimingRecord(
            operation=operation,
            start_time=time.time(),
            metadata=metadata
        )
        
        # アクティブタイミング登録
        timing_id = f"{operation}_{id(record)}"
        with self.lock:
            self.active_timings[timing_id] = record
        
        try:
            yield record
        finally:
            # 計測完了
            record.complete()
            
            with self.lock:
                self.active_timings.pop(timing_id, None)
                self.timings.append(record)
                self.operation_stats[operation].append(record.duration_ms)
            
            # 目標比較
            if operation in self.TARGETS:
                target = self.TARGETS[operation]
                if record.duration_ms > target:
                    logger.warning(
                        f"⚠️ {operation}: {record.duration_ms:.2f}ms "
                        f"(目標: {target}ms, 超過: {record.duration_ms - target:.2f}ms)"
                    )
                else:
                    logger.debug(
                        f"✅ {operation}: {record.duration_ms:.2f}ms "
                        f"(目標: {target}ms)"
                    )
    
    def start_profiling(self):
        """cProfileによる詳細プロファイリング開始"""
        if self.enable_cprofile and self.profiler is None:
            self.profiler = cProfile.Profile()
            self.profiler.enable()
            logger.info("詳細プロファイリング開始")
    
    def stop_profiling(self) -> Optional[str]:
        """
        cProfileによる詳細プロファイリング停止
        
        Returns:
            プロファイリング結果の文字列
        """
        if self.profiler is not None:
            self.profiler.disable()
            
            # 結果を文字列で取得
            s = io.StringIO()
            ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # 上位20個
            
            result = s.getvalue()
            self.profiler = None
            logger.info("詳細プロファイリング停止")
            
            return result
        return None
    
    def get_statistics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        統計情報取得
        
        Args:
            operation: 特定操作の統計のみ取得（Noneで全体）
        """
        if operation:
            if operation not in self.operation_stats:
                return {}
            
            durations = self.operation_stats[operation]
            if not durations:
                return {}
            
            return {
                'operation': operation,
                'count': len(durations),
                'min_ms': min(durations),
                'max_ms': max(durations),
                'avg_ms': sum(durations) / len(durations),
                'total_ms': sum(durations),
                'target_ms': self.TARGETS.get(operation),
                'target_met': all(d <= self.TARGETS.get(operation, float('inf')) 
                                for d in durations)
            }
        else:
            # 全体統計
            stats = {}
            for op in self.operation_stats:
                stats[op] = self.get_statistics(op)
            
            # サマリー追加
            all_durations = [d for durations in self.operation_stats.values() 
                           for d in durations]
            if all_durations:
                stats['_summary'] = {
                    'total_operations': len(all_durations),
                    'total_time_ms': sum(all_durations),
                    'operations_types': len(self.operation_stats),
                    'targets_met': sum(1 for s in stats.values() 
                                     if s.get('target_met', False))
                }
            
            return stats
    
    def get_bottlenecks(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        ボトルネック特定
        
        Args:
            top_n: 上位N個のボトルネック
            
        Returns:
            ボトルネック操作のリスト
        """
        bottlenecks = []
        
        for operation, durations in self.operation_stats.items():
            if not durations:
                continue
            
            avg_ms = sum(durations) / len(durations)
            target = self.TARGETS.get(operation, float('inf'))
            
            if avg_ms > target:
                bottlenecks.append({
                    'operation': operation,
                    'avg_ms': avg_ms,
                    'target_ms': target,
                    'excess_ms': avg_ms - target,
                    'excess_percent': ((avg_ms - target) / target) * 100,
                    'count': len(durations)
                })
        
        # 超過時間でソート
        bottlenecks.sort(key=lambda x: x['excess_ms'], reverse=True)
        return bottlenecks[:top_n]
    
    def print_summary(self):
        """サマリー出力"""
        print("\n" + "=" * 60)
        print("📊 パフォーマンスサマリー")
        print("=" * 60)
        
        stats = self.get_statistics()
        
        # 操作別統計
        for op, stat in sorted(stats.items()):
            if op == '_summary':
                continue
            
            target = stat.get('target_ms')
            avg = stat.get('avg_ms', 0)
            
            if target:
                if avg <= target:
                    status = "✅"
                    color = ""
                else:
                    status = "⚠️"
                    color = ""
            else:
                status = "📊"
                color = ""
            
            print(f"{status} {op}:")
            print(f"   平均: {avg:.2f}ms")
            if target:
                print(f"   目標: {target}ms")
            print(f"   回数: {stat.get('count', 0)}")
            print(f"   範囲: {stat.get('min_ms', 0):.2f}ms - {stat.get('max_ms', 0):.2f}ms")
            print()
        
        # ボトルネック表示
        bottlenecks = self.get_bottlenecks()
        if bottlenecks:
            print("\n🚨 ボトルネック（目標超過）:")
            for bn in bottlenecks:
                print(f"   {bn['operation']}: "
                      f"{bn['avg_ms']:.2f}ms (目標: {bn['target_ms']}ms, "
                      f"超過: {bn['excess_ms']:.2f}ms = {bn['excess_percent']:.1f}%)")
        
        # サマリー
        if '_summary' in stats:
            summary = stats['_summary']
            print("\n📈 全体統計:")
            print(f"   総操作数: {summary['total_operations']}")
            print(f"   総実行時間: {summary['total_time_ms']:.2f}ms")
            print(f"   操作種類: {summary['operations_types']}")
            print(f"   目標達成: {summary['targets_met']}/{summary['operations_types']}")
    
    def clear(self):
        """統計クリア"""
        with self.lock:
            self.timings.clear()
            self.operation_stats.clear()
            self.active_timings.clear()


def benchmark_function(func: Callable, *args, iterations: int = 100, **kwargs) -> Dict[str, float]:
    """
    関数のベンチマーク実行
    
    Args:
        func: ベンチマーク対象関数
        iterations: 実行回数
        
    Returns:
        統計情報
    """
    profiler = PerformanceProfiler()
    
    # ウォームアップ
    for _ in range(min(10, iterations // 10)):
        func(*args, **kwargs)
    
    # 本計測
    for i in range(iterations):
        with profiler.measure(func.__name__):
            func(*args, **kwargs)
    
    stats = profiler.get_statistics(func.__name__)
    return {
        'function': func.__name__,
        'iterations': iterations,
        'avg_ms': stats['avg_ms'],
        'min_ms': stats['min_ms'],
        'max_ms': stats['max_ms'],
        'total_ms': stats['total_ms']
    }


if __name__ == "__main__":
    # テスト実行
    print("🧪 パフォーマンスプロファイラーテスト")
    
    profiler = PerformanceProfiler()
    
    # 各処理をシミュレート
    import random
    
    # 同逆判定シミュレート
    with profiler.measure('同逆判定', timeframe='M1'):
        time.sleep(random.uniform(0.008, 0.012))  # 8-12ms
    
    # もみ判定シミュレート  
    with profiler.measure('もみ', timeframe='M1'):
        time.sleep(random.uniform(0.070, 0.080))  # 70-80ms
    
    # OP分岐シミュレート
    with profiler.measure('OP分岐', timeframe='M1'):
        time.sleep(random.uniform(0.095, 0.110))  # 95-110ms
    
    # 全体処理シミュレート
    with profiler.measure('全体'):
        time.sleep(random.uniform(0.018, 0.022))  # 18-22ms
    
    # 目標超過ケース
    with profiler.measure('全体'):
        time.sleep(0.025)  # 25ms (目標19ms超過)
    
    # サマリー表示
    profiler.print_summary()
    
    # ボトルネック確認
    bottlenecks = profiler.get_bottlenecks()
    assert len(bottlenecks) > 0, "ボトルネック検出失敗"
    
    print("\n✅ パフォーマンスプロファイラーテスト完了")