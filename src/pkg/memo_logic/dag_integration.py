"""
Week 6: DAG評価エンジンとメモロジック統合
関数型DAGアーキテクチャによるPKG関数の階層的評価システム
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from collections import defaultdict
import logging
from enum import Enum

# 内部モジュール（外部依存なし実装）
class MarketData:
    """市場データ構造"""
    def __init__(self, timestamp, open, high, low, close, volume):
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

class OperationSignal:
    """オペレーション信号"""
    def __init__(self, pkg_id, signal_type, direction, confidence, timestamp):
        self.pkg_id = pkg_id
        self.signal_type = signal_type
        self.direction = direction
        self.confidence = confidence
        self.timestamp = timestamp

@dataclass
class DAGNode:
    """DAGノード定義"""
    pkg_id: str
    function_name: str
    layer: int
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    execution_order: int = 0
    cache_enabled: bool = True

@dataclass
class DAGExecutionContext:
    """DAG実行コンテキスト"""
    market_data: Dict[str, MarketData]
    signals: Dict[str, OperationSignal]
    cache: Dict[str, Any]
    execution_times: Dict[str, float]
    errors: List[str]

class FunctionalDAGEngine:
    """
    関数型DAGエンジン
    メモファイルのPKG階層構造を実装
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.nodes: Dict[str, DAGNode] = {}
        self.execution_graph: Dict[int, List[DAGNode]] = defaultdict(list)
        self.cache = {}
        self.performance_history = []
        
        # DAGノード初期化
        self._initialize_dag_structure()
        
    def _initialize_dag_structure(self):
        """
        PKG階層構造の初期化
        階層1: 基本指標
        階層2: 演算結果
        階層3: 統合判断
        """
        
        # 階層1: 基本指標ノード
        layer1_nodes = [
            DAGNode("191^1-1", "dokyaku", 1, [], ["dokyaku_signal"]),
            DAGNode("191^1-2", "ikikaeri", 1, [], ["ikikaeri_signal"]),
            DAGNode("191^1-3", "momi", 1, [], ["momi_signal"]),
            DAGNode("191^1-4", "overshoot", 1, [], ["overshoot_signal"]),
            DAGNode("191^1-5", "kairi", 1, [], ["kairi_signal"]),
            DAGNode("191^1-6", "range", 1, [], ["range_signal"]),
            DAGNode("191^1-7", "yochi", 1, [], ["yochi_signal"])
        ]
        
        # 階層2: 演算結果ノード（複数の基本指標を統合）
        layer2_nodes = [
            DAGNode("191^2-1", "time_combination", 2, 
                   ["dokyaku_signal", "ikikaeri_signal"], 
                   ["time_combo_signal"]),
            DAGNode("191^2-2", "trend_analysis", 2,
                   ["kairi_signal", "range_signal"],
                   ["trend_signal"]),
            DAGNode("191^2-3", "volatility_analysis", 2,
                   ["momi_signal", "overshoot_signal"],
                   ["volatility_signal"])
        ]
        
        # 階層3: 統合判断ノード
        layer3_nodes = [
            DAGNode("191^3-1", "final_decision", 3,
                   ["time_combo_signal", "trend_signal", "volatility_signal"],
                   ["final_signal"])
        ]
        
        # ノードの登録
        for node in layer1_nodes + layer2_nodes + layer3_nodes:
            self.nodes[node.pkg_id] = node
            self.execution_graph[node.layer].append(node)
            
        # 実行順序の設定
        self._set_execution_order()
        
    def _set_execution_order(self):
        """トポロジカルソートによる実行順序設定"""
        order = 0
        for layer in sorted(self.execution_graph.keys()):
            for node in self.execution_graph[layer]:
                node.execution_order = order
                order += 1
                
    async def execute_dag(self, market_data: Dict[str, MarketData]) -> DAGExecutionContext:
        """
        DAG実行
        階層ごとに並列実行、階層間は順次実行
        """
        
        context = DAGExecutionContext(
            market_data=market_data,
            signals={},
            cache={},
            execution_times={},
            errors=[]
        )
        
        start_time = time.time()
        
        try:
            # 階層ごとに実行
            for layer in sorted(self.execution_graph.keys()):
                layer_start = time.time()
                
                # 同一階層内は並列実行
                tasks = []
                for node in self.execution_graph[layer]:
                    tasks.append(self._execute_node(node, context))
                    
                # 並列実行の待機
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # エラーチェック
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        error_msg = f"Node {self.execution_graph[layer][i].pkg_id} failed: {result}"
                        context.errors.append(error_msg)
                        self.logger.error(error_msg)
                        
                layer_time = (time.time() - layer_start) * 1000
                self.logger.info(f"Layer {layer} executed in {layer_time:.2f}ms")
                
        except Exception as e:
            context.errors.append(f"DAG execution failed: {e}")
            self.logger.error(f"DAG execution failed: {e}")
            
        total_time = (time.time() - start_time) * 1000
        context.execution_times['total'] = total_time
        
        # パフォーマンス記録
        self.performance_history.append({
            'timestamp': time.time(),
            'total_time_ms': total_time,
            'node_count': len(self.nodes),
            'error_count': len(context.errors)
        })
        
        return context
        
    async def _execute_node(self, node: DAGNode, context: DAGExecutionContext) -> Optional[OperationSignal]:
        """
        個別ノード実行
        純粋関数として副作用なし
        """
        
        start_time = time.time()
        
        try:
            # キャッシュチェック
            if node.cache_enabled and node.pkg_id in self.cache:
                cached_result = self.cache[node.pkg_id]
                if self._is_cache_valid(cached_result):
                    return cached_result['signal']
                    
            # 入力データ収集
            inputs = {}
            for input_key in node.inputs:
                if input_key in context.signals:
                    inputs[input_key] = context.signals[input_key]
                    
            # 関数実行（シミュレーション）
            signal = await self._execute_function(node.function_name, inputs, context.market_data)
            
            # 結果の保存
            if signal:
                for output_key in node.outputs:
                    context.signals[output_key] = signal
                    
                # キャッシュ更新
                if node.cache_enabled:
                    self.cache[node.pkg_id] = {
                        'signal': signal,
                        'timestamp': time.time()
                    }
                    
        except Exception as e:
            self.logger.error(f"Node {node.pkg_id} execution failed: {e}")
            raise
            
        finally:
            execution_time = (time.time() - start_time) * 1000
            context.execution_times[node.pkg_id] = execution_time
            
        return signal
        
    async def _execute_function(self, function_name: str, inputs: Dict, market_data: Dict) -> OperationSignal:
        """
        PKG関数の実行（シミュレーション）
        実際の実装では各PKG関数を呼び出す
        """
        
        # シミュレーション用の遅延
        await asyncio.sleep(0.001)  # 1ms
        
        # 関数ごとの処理（簡略化）
        direction = 0
        confidence = 0.5
        
        if function_name == "dokyaku":
            # 同逆判定シミュレーション
            direction = 1 if len(inputs) % 2 == 0 else -1
            confidence = 0.557  # メモファイル記載の勝率
            
        elif function_name == "ikikaeri":
            # 行帰判定シミュレーション
            direction = 0
            confidence = 0.65
            
        elif function_name == "momi":
            # もみ判定シミュレーション
            direction = 0
            confidence = 0.7
            
        elif function_name == "time_combination":
            # 時間結合シミュレーション
            if inputs:
                # 入力信号の重み付き平均
                total_weight = 0
                weighted_direction = 0
                for signal in inputs.values():
                    weighted_direction += signal.direction * signal.confidence
                    total_weight += signal.confidence
                    
                if total_weight > 0:
                    direction = 1 if weighted_direction > 0 else -1
                    confidence = min(total_weight / len(inputs), 1.0)
                    
        elif function_name == "final_decision":
            # 最終判断
            if inputs:
                # 全信号の統合
                signals = list(inputs.values())
                buy_score = sum(s.confidence for s in signals if s.direction > 0)
                sell_score = sum(s.confidence for s in signals if s.direction < 0)
                
                if buy_score > sell_score * 1.1:  # 10%のマージン
                    direction = 1
                    confidence = buy_score / len(signals)
                elif sell_score > buy_score * 1.1:
                    direction = -1
                    confidence = sell_score / len(signals)
                else:
                    direction = 0
                    confidence = 0.3
                    
        return OperationSignal(
            pkg_id=function_name,
            signal_type=function_name,
            direction=direction,
            confidence=confidence,
            timestamp=time.time()
        )
        
    def _is_cache_valid(self, cached_data: Dict) -> bool:
        """キャッシュ有効性チェック（1秒以内）"""
        if 'timestamp' not in cached_data:
            return False
        age = time.time() - cached_data['timestamp']
        return age < 1.0  # 1秒以内なら有効
        
    def get_performance_summary(self) -> Dict:
        """パフォーマンスサマリー取得"""
        if not self.performance_history:
            return {}
            
        recent = self.performance_history[-100:]  # 直近100件
        
        times = [p['total_time_ms'] for p in recent]
        return {
            'average_ms': sum(times) / len(times),
            'min_ms': min(times),
            'max_ms': max(times),
            'target_ms': 19.0,  # メモファイル記載の目標
            'achievement_rate': sum(1 for t in times if t < 19.0) / len(times)
        }
        
    def visualize_dag(self) -> str:
        """DAG構造の可視化（テキスト形式）"""
        output = []
        output.append("=== PKG DAG Structure ===\n")
        
        for layer in sorted(self.execution_graph.keys()):
            output.append(f"Layer {layer}:")
            for node in self.execution_graph[layer]:
                inputs = ", ".join(node.inputs) if node.inputs else "None"
                outputs = ", ".join(node.outputs) if node.outputs else "None"
                output.append(f"  [{node.pkg_id}] {node.function_name}")
                output.append(f"    Inputs: {inputs}")
                output.append(f"    Outputs: {outputs}")
                
        return "\n".join(output)


async def test_dag_integration():
    """DAG統合テスト"""
    print("=" * 60)
    print("DAG評価エンジン統合テスト")
    print("=" * 60)
    
    # エンジン初期化
    engine = FunctionalDAGEngine()
    
    # DAG構造の表示
    print("\n" + engine.visualize_dag())
    
    # テスト用市場データ
    market_data = {
        'USDJPY': MarketData(
            timestamp=time.time(),
            open=110.00,
            high=110.05,
            low=109.95,
            close=110.02,
            volume=1000
        )
    }
    
    # DAG実行テスト（10回）
    print("\n実行テスト開始...")
    for i in range(10):
        context = await engine.execute_dag(market_data)
        
        if i == 0:
            print(f"\n実行 {i+1}:")
            print(f"  総実行時間: {context.execution_times.get('total', 0):.2f}ms")
            print(f"  生成信号数: {len(context.signals)}")
            print(f"  エラー数: {len(context.errors)}")
            
            if 'final_signal' in context.signals:
                final = context.signals['final_signal']
                print(f"  最終判断: 方向={final.direction}, 信頼度={final.confidence:.3f}")
                
    # パフォーマンスサマリー
    summary = engine.get_performance_summary()
    print("\nパフォーマンスサマリー:")
    print(f"  平均実行時間: {summary.get('average_ms', 0):.2f}ms")
    print(f"  最小実行時間: {summary.get('min_ms', 0):.2f}ms")
    print(f"  最大実行時間: {summary.get('max_ms', 0):.2f}ms")
    print(f"  目標達成率: {summary.get('achievement_rate', 0)*100:.1f}%")
    
    print("\n✅ DAG統合テスト完了")
    

if __name__ == "__main__":
    # 非同期実行
    asyncio.run(test_dag_integration())