"""
Week 6: PKG関数システム統合
97個のメモファイルから抽出したPKG関数の統合実行システム
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

from .core_pkg_functions import (
    BasePKGFunction, PKGId, MarketData, OperationSignal,
    TimeFrame, Currency, Period, DokyakuFunction, IkikaerikFunction
)
from .advanced_pkg_functions import (
    MomiFunction, OvershootFunction, TimeKetsugouFunction
)
from .specialized_pkg_functions import (
    KairiFunction, RangeFunction, YochiFunction
)

@dataclass
class PKGExecutionResult:
    """PKG実行結果"""
    pkg_id: PKGId
    signal: Optional[OperationSignal]
    execution_time_ms: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class SystemPerformanceMetrics:
    """システムパフォーマンス指標"""
    total_execution_time_ms: float
    individual_times: Dict[str, float]
    memory_usage_mb: float
    success_rate: float
    signal_count: int

class PKGSystemIntegration:
    """
    PKG関数システム統合クラス
    
    メモファイルから抽出した実行時間目標:
    - 全体: 19ms
    - もみ: 77ms  
    - OP分岐: 101.3ms
    - オーバーシュート: 550.6ms
    - 時間結合: 564.9ms
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.performance_targets = {
            'total_system': 19.0,      # 全体目標: 19ms
            'momi': 77.0,              # もみ判定: 77ms
            'overshoot': 550.6,        # オーバーシュート: 550.6ms
            'time_combination': 564.9,  # 時間結合: 564.9ms
            'dokyaku': 50.0,           # 同逆判定: 推定50ms
            'ikikaeri': 50.0,          # 行帰判定: 推定50ms
            'kairi': 30.0,             # 乖離判断: 推定30ms
            'range': 40.0,             # レンジ判定: 推定40ms
            'yochi': 60.0              # 予知計算: 推定60ms
        }
        
        self.pkg_functions = {}
        self.execution_cache = {}
        self.performance_metrics = []
        
        # PKG関数の初期化
        self._initialize_pkg_functions()
        
    def _initialize_pkg_functions(self):
        """PKG関数の初期化"""
        try:
            # 各PKG関数インスタンスの作成
            base_pkg_configs = [
                ('dokyaku', DokyakuFunction, PKGId(TimeFrame.M1, Period.COMMON, Currency.USDJPY, 1, 1)),
                ('ikikaeri', IkikaerikFunction, PKGId(TimeFrame.M1, Period.COMMON, Currency.USDJPY, 1, 2)),
                ('momi', MomiFunction, PKGId(TimeFrame.M1, Period.COMMON, Currency.USDJPY, 1, 3)),
                ('overshoot', OvershootFunction, PKGId(TimeFrame.M1, Period.COMMON, Currency.USDJPY, 1, 4)),
                ('time_combination', TimeKetsugouFunction, PKGId(TimeFrame.M1, Period.COMMON, Currency.USDJPY, 2, 1)),
                ('kairi', KairiFunction, PKGId(TimeFrame.M1, Period.COMMON, Currency.USDJPY, 1, 5)),
                ('range', RangeFunction, PKGId(TimeFrame.M1, Period.COMMON, Currency.USDJPY, 1, 6)),
                ('yochi', YochiFunction, PKGId(TimeFrame.M1, Period.COMMON, Currency.USDJPY, 1, 7))
            ]
            
            for func_name, func_class, pkg_id in base_pkg_configs:
                self.pkg_functions[func_name] = func_class(pkg_id)
                self.logger.info(f"Initialized PKG function: {func_name} with ID: {pkg_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize PKG functions: {e}")
            raise
    
    async def execute_all_pkg_functions(self, data: Dict[str, Any]) -> List[PKGExecutionResult]:
        """
        全PKG関数の並列実行
        メモファイルの実行時間目標を達成するための最適化実装
        """
        start_time = time.perf_counter()
        
        # 並列実行のためのタスク作成
        tasks = []
        for func_name, pkg_function in self.pkg_functions.items():
            task = asyncio.create_task(
                self._execute_single_pkg_function(func_name, pkg_function, data)
            )
            tasks.append(task)
        
        # 全タスクの並列実行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果の処理
        execution_results = []
        for i, result in enumerate(results):
            func_name = list(self.pkg_functions.keys())[i]
            
            if isinstance(result, Exception):
                execution_results.append(PKGExecutionResult(
                    pkg_id=self.pkg_functions[func_name].pkg_id,
                    signal=None,
                    execution_time_ms=0.0,
                    success=False,
                    error_message=str(result)
                ))
            else:
                execution_results.append(result)
        
        # パフォーマンス指標の記録
        total_time = (time.perf_counter() - start_time) * 1000  # ms
        self._record_performance_metrics(execution_results, total_time)
        
        return execution_results
    
    async def _execute_single_pkg_function(self, func_name: str, 
                                         pkg_function: BasePKGFunction, 
                                         data: Dict[str, Any]) -> PKGExecutionResult:
        """単一PKG関数の実行"""
        start_time = time.perf_counter()
        
        try:
            # キャッシュチェック
            cache_key = self._generate_cache_key(func_name, data)
            if cache_key in self.execution_cache:
                cached_result = self.execution_cache[cache_key]
                self.logger.debug(f"Using cached result for {func_name}")
                return cached_result
            
            # PKG関数の実行
            signal = await asyncio.get_event_loop().run_in_executor(
                None, pkg_function.execute, data
            )
            
            execution_time = (time.perf_counter() - start_time) * 1000  # ms
            
            result = PKGExecutionResult(
                pkg_id=pkg_function.pkg_id,
                signal=signal,
                execution_time_ms=execution_time,
                success=True
            )
            
            # パフォーマンス目標との比較
            target_time = self.performance_targets.get(func_name, 100.0)
            if execution_time > target_time:
                self.logger.warning(
                    f"{func_name} execution time {execution_time:.2f}ms exceeds target {target_time}ms"
                )
            
            # キャッシュに保存（短時間）
            self.execution_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"PKG function {func_name} failed: {e}")
            
            return PKGExecutionResult(
                pkg_id=pkg_function.pkg_id,
                signal=None,
                execution_time_ms=execution_time,
                success=False,
                error_message=str(e)
            )
    
    def execute_synchronized_pkg_functions(self, data: Dict[str, Any]) -> List[PKGExecutionResult]:
        """
        同期実行版（非推奨: パフォーマンス目標達成困難）
        テスト用途や単純な実行の場合に使用
        """
        start_time = time.perf_counter()
        results = []
        
        for func_name, pkg_function in self.pkg_functions.items():
            func_start_time = time.perf_counter()
            
            try:
                signal = pkg_function.execute(data)
                execution_time = (time.perf_counter() - func_start_time) * 1000
                
                results.append(PKGExecutionResult(
                    pkg_id=pkg_function.pkg_id,
                    signal=signal,
                    execution_time_ms=execution_time,
                    success=True
                ))
                
            except Exception as e:
                execution_time = (time.perf_counter() - func_start_time) * 1000
                results.append(PKGExecutionResult(
                    pkg_id=pkg_function.pkg_id,
                    signal=None,
                    execution_time_ms=execution_time,
                    success=False,
                    error_message=str(e)
                ))
        
        total_time = (time.perf_counter() - start_time) * 1000
        self._record_performance_metrics(results, total_time)
        
        return results
    
    def integrate_signals(self, execution_results: List[PKGExecutionResult]) -> Dict[str, Any]:
        """
        PKG関数の結果を統合して最終的な取引信号を生成
        メモファイルの階層的統合ロジックに基づく
        """
        successful_signals = [
            result.signal for result in execution_results 
            if result.success and result.signal is not None
        ]
        
        if not successful_signals:
            return {
                'final_direction': 0,
                'confidence': 0.0,
                'signal_count': 0,
                'integration_method': 'no_signals'
            }
        
        # 信号の重み付け統合
        signal_weights = self._calculate_signal_weights()
        weighted_directions = []
        weighted_confidences = []
        
        for signal in successful_signals:
            weight = signal_weights.get(signal.signal_type, 0.1)
            
            # 方向の重み付け
            if signal.direction == 1:  # 上
                weighted_directions.append(weight * signal.confidence)
            elif signal.direction == 2:  # 下
                weighted_directions.append(-weight * signal.confidence)
            else:  # 中立
                weighted_directions.append(0)
            
            weighted_confidences.append(weight * signal.confidence)
        
        # 最終方向の決定
        total_weighted_direction = sum(weighted_directions)
        
        if total_weighted_direction > 0.3:
            final_direction = 1  # 上
        elif total_weighted_direction < -0.3:
            final_direction = 2  # 下
        else:
            final_direction = 0  # 中立
        
        # 最終信頼度の計算
        final_confidence = np.mean(weighted_confidences) if weighted_confidences else 0.0
        
        # 追加の統合分析
        consensus_analysis = self._analyze_signal_consensus(successful_signals)
        
        return {
            'final_direction': final_direction,
            'confidence': final_confidence,
            'signal_count': len(successful_signals),
            'integration_method': 'weighted_consensus',
            'weighted_direction_score': total_weighted_direction,
            'consensus_analysis': consensus_analysis,
            'individual_signals': [
                {
                    'type': signal.signal_type,
                    'direction': signal.direction,
                    'confidence': signal.confidence,
                    'pkg_id': str(signal.pkg_id)
                }
                for signal in successful_signals
            ]
        }
    
    def _calculate_signal_weights(self) -> Dict[str, float]:
        """
        信号の重み計算
        メモファイルの勝率や重要度に基づく
        """
        return {
            'dokyaku': 0.25,        # 同逆判定: 勝率55.7%で高重要度
            'ikikaeri': 0.20,       # 行帰判定: 継続性判断で重要
            'time_combination': 0.20, # 時間結合: マルチタイムフレーム統合で重要
            'momi': 0.15,           # もみ判定: レンジブレイク予測
            'overshoot': 0.10,      # オーバーシュート: 転換予測
            'kairi': 0.05,          # 乖離判断: 補助指標
            'range': 0.03,          # レンジ判定: 補助指標
            'yochi': 0.02           # 予知計算: 実験的指標
        }
    
    def _analyze_signal_consensus(self, signals: List[OperationSignal]) -> Dict[str, Any]:
        """信号のコンセンサス分析"""
        direction_counts = {1: 0, 2: 0, 0: 0}
        confidence_by_direction = {1: [], 2: [], 0: []}
        
        for signal in signals:
            direction_counts[signal.direction] += 1
            confidence_by_direction[signal.direction].append(signal.confidence)
        
        # 最も多い方向
        dominant_direction = max(direction_counts, key=direction_counts.get)
        consensus_strength = direction_counts[dominant_direction] / len(signals)
        
        # 方向別平均信頼度
        avg_confidence_by_direction = {}
        for direction, confidences in confidence_by_direction.items():
            if confidences:
                avg_confidence_by_direction[direction] = np.mean(confidences)
            else:
                avg_confidence_by_direction[direction] = 0.0
        
        return {
            'dominant_direction': dominant_direction,
            'consensus_strength': consensus_strength,
            'direction_counts': direction_counts,
            'avg_confidence_by_direction': avg_confidence_by_direction,
            'signal_diversity': len([d for d in direction_counts.values() if d > 0])
        }
    
    def _generate_cache_key(self, func_name: str, data: Dict[str, Any]) -> str:
        """キャッシュキーの生成"""
        # 簡易実装: 最新の価格データのハッシュを使用
        market_data = data.get('market_data', [])
        if market_data:
            latest_data = market_data[-1]
            key_data = f"{func_name}_{latest_data.timestamp}_{latest_data.close}"
        else:
            key_data = f"{func_name}_{time.time()}"
        
        return str(hash(key_data))
    
    def _record_performance_metrics(self, results: List[PKGExecutionResult], 
                                  total_time: float):
        """パフォーマンス指標の記録"""
        individual_times = {}
        success_count = 0
        signal_count = 0
        
        for result in results:
            func_name = result.signal.signal_type if result.signal else 'unknown'
            individual_times[func_name] = result.execution_time_ms
            
            if result.success:
                success_count += 1
                if result.signal:
                    signal_count += 1
        
        success_rate = success_count / len(results) if results else 0.0
        
        metrics = SystemPerformanceMetrics(
            total_execution_time_ms=total_time,
            individual_times=individual_times,
            memory_usage_mb=self._get_memory_usage(),
            success_rate=success_rate,
            signal_count=signal_count
        )
        
        self.performance_metrics.append(metrics)
        
        # パフォーマンス目標との比較ログ
        if total_time > self.performance_targets['total_system']:
            self.logger.warning(
                f"Total execution time {total_time:.2f}ms exceeds target "
                f"{self.performance_targets['total_system']}ms"
            )
        else:
            self.logger.info(
                f"Performance target achieved: {total_time:.2f}ms <= "
                f"{self.performance_targets['total_system']}ms"
            )
    
    def _get_memory_usage(self) -> float:
        """メモリ使用量の取得（簡易実装）"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """パフォーマンス統計の取得"""
        if not self.performance_metrics:
            return {'message': 'No performance data available'}
        
        recent_metrics = self.performance_metrics[-10:]  # 直近10件
        
        avg_total_time = np.mean([m.total_execution_time_ms for m in recent_metrics])
        avg_success_rate = np.mean([m.success_rate for m in recent_metrics])
        avg_signal_count = np.mean([m.signal_count for m in recent_metrics])
        
        # 個別関数の平均実行時間
        individual_avg_times = {}
        for metrics in recent_metrics:
            for func_name, exec_time in metrics.individual_times.items():
                if func_name not in individual_avg_times:
                    individual_avg_times[func_name] = []
                individual_avg_times[func_name].append(exec_time)
        
        for func_name in individual_avg_times:
            individual_avg_times[func_name] = np.mean(individual_avg_times[func_name])
        
        # 目標達成状況
        target_achievement = {}
        for func_name, avg_time in individual_avg_times.items():
            target_time = self.performance_targets.get(func_name, 100.0)
            target_achievement[func_name] = {
                'avg_time_ms': avg_time,
                'target_time_ms': target_time,
                'achieved': avg_time <= target_time,
                'ratio': avg_time / target_time if target_time > 0 else float('inf')
            }
        
        return {
            'summary': {
                'avg_total_execution_time_ms': avg_total_time,
                'avg_success_rate': avg_success_rate,
                'avg_signal_count': avg_signal_count,
                'total_target_achieved': avg_total_time <= self.performance_targets['total_system']
            },
            'individual_performance': target_achievement,
            'recent_metrics_count': len(recent_metrics),
            'cache_size': len(self.execution_cache)
        }
    
    def clear_cache(self):
        """キャッシュのクリア"""
        self.execution_cache.clear()
        self.logger.info("PKG execution cache cleared")
    
    def optimize_performance(self):
        """パフォーマンス最適化の実行"""
        # キャッシュサイズの調整
        if len(self.execution_cache) > 1000:
            # 古いキャッシュエントリの削除（簡易実装）
            cache_items = list(self.execution_cache.items())
            self.execution_cache = dict(cache_items[-500:])  # 最新500件を保持
            
        self.logger.info("Performance optimization completed")