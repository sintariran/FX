#!/usr/bin/env python3
"""
PKG関数マネージャー - 真の関数型DAGアーキテクチャ実装

レビュー指摘事項への対応:
- 手動統合から関数型DAG処理への移行
- PKGFunctionManagerによる自動依存関係解決
- 階層チェックと自動実行順序決定
- メモロジックのDAG化

設計原則:
1. 各判定クラスをPKGFunctionとして登録
2. 依存関係を自動解決
3. 階層一貫性を検証
4. キャッシュによる効率化
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import time
from datetime import datetime

# PKG基本要素のインポート
from core_pkg_functions import (
    BasePKGFunction, PKGId, TimeFrame, Currency, Period,
    MarketData, OperationSignal,
    DokyakuFunction, IkikaerikFunction, PKGFunctionFactory
)

class FunctionLevel(Enum):
    """PKG関数の階層レベル"""
    RAW_DATA = 0      # Layer 0: 生データ（AA001-329, BA001-BB999, CA001-142）
    INDICATORS = 1    # Layer 1: 基本指標（平均足、移動平均、OsMA等）
    OPERATIONS = 2    # Layer 2: 基本演算（Z, SL, OR, AND, CO, SG等）
    JUDGMENTS = 3     # Layer 3: 判定関数（同逆、行帰、もみ/OS等）
    INTEGRATION = 4   # Layer 4: 統合判断（時間結合、総合信号）

@dataclass
class PKGNodeDefinition:
    """PKG関数ノードの定義"""
    pkg_id: PKGId
    function_type: str
    function_instance: Optional[BasePKGFunction] = None
    input_dependencies: List[PKGId] = field(default_factory=list)
    layer: int = 0
    cached_result: Optional[Any] = None
    last_evaluation_time: Optional[datetime] = None
    evaluation_count: int = 0
    
    def __str__(self) -> str:
        return f"PKGNode({self.pkg_id}, {self.function_type}, L{self.layer})"

class PKGFunctionManager:
    """
    PKG関数の完全管理システム
    
    機能:
    - DAG構築と依存関係解決
    - 階層一貫性検証
    - 自動実行順序決定
    - キャッシュ管理
    - パフォーマンス監視
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # PKG関数レジストリ
        self.nodes: Dict[str, PKGNodeDefinition] = {}  # str(PKGId) -> PKGNodeDefinition
        self.raw_data_store: Dict[str, Any] = {}
        
        # DAG管理
        self.execution_order: List[str] = []
        self.layer_groups: Dict[int, List[str]] = defaultdict(list)
        
        # PKG関数ファクトリー
        self.function_factory = PKGFunctionFactory()
        
        # パフォーマンス追跡
        self.performance_stats = {
            'total_evaluations': 0,
            'cache_hits': 0,
            'total_execution_time': 0.0,
            'layer_execution_times': defaultdict(float)
        }
        
        self.logger.info("PKGFunctionManager initialized")
    
    def register_raw_data_symbol(self, symbol: str, timeframe: TimeFrame,
                                period: Period, currency: Currency, 
                                value: Any) -> PKGId:
        """
        生データシンボルをPKG ID体系で登録
        
        例: AA001 → PKGId(M15, COMMON, USDJPY, 0, AA001)
        """
        # 生データのPKG ID生成
        sequence = self._symbol_to_sequence(symbol)
        pkg_id = PKGId(timeframe, period, currency, 0, sequence)
        pkg_id_str = str(pkg_id)
        
        # ノード定義作成
        node = PKGNodeDefinition(
            pkg_id=pkg_id,
            function_type="RAW_DATA",
            layer=0,
            cached_result=value,
            last_evaluation_time=datetime.now()
        )
        
        self.nodes[pkg_id_str] = node
        self.raw_data_store[pkg_id_str] = value
        self.layer_groups[0].append(pkg_id_str)
        
        self.logger.debug(f"生データ登録: {pkg_id_str} = {value}")
        return pkg_id
    
    def register_pkg_function(self, pkg_id: PKGId, function_type: str,
                            input_dependencies: List[PKGId], 
                            **function_params) -> None:
        """
        PKG関数をDAGに登録
        
        Args:
            pkg_id: PKG関数のID
            function_type: 関数タイプ（'Dokyaku', 'Ikikaeri', 'Z', 'SL'等）
            input_dependencies: 依存する入力PKG IDのリスト
            **function_params: 関数固有のパラメータ
        """
        pkg_id_str = str(pkg_id)
        
        # 階層一貫性チェック
        if not self._validate_layer_consistency(pkg_id, input_dependencies):
            raise ValueError(f"階層一貫性違反: {pkg_id_str}")
        
        # 関数インスタンス作成
        try:
            function_instance = self.function_factory.create_function(
                function_type, pkg_id
            )
            if hasattr(function_instance, 'configure'):
                function_instance.configure(**function_params)
        except Exception as e:
            self.logger.error(f"関数作成エラー {pkg_id_str}: {e}")
            raise
        
        # ノード定義作成
        node = PKGNodeDefinition(
            pkg_id=pkg_id,
            function_type=function_type,
            function_instance=function_instance,
            input_dependencies=input_dependencies,
            layer=pkg_id.layer
        )
        
        self.nodes[pkg_id_str] = node
        self.layer_groups[pkg_id.layer].append(pkg_id_str)
        
        # 実行順序を無効化（再計算が必要）
        self.execution_order = []
        
        self.logger.info(f"PKG関数登録: {pkg_id_str} = {function_type}")
        self.logger.debug(f"  依存関係: {[str(dep) for dep in input_dependencies]}")
    
    def register_memo_logic_as_dag(self, currency: Currency = Currency.USDJPY,
                                  timeframe: TimeFrame = TimeFrame.M15) -> None:
        """
        メモロジック（4コア概念）をDAG構造で登録
        
        これがレビュー指摘の核心: 手動統合→DAG化
        """
        self.logger.info("メモロジックのDAG化を開始")
        
        # ダミー生データを登録（実際は市場データから取得）
        base_data_ids = []
        for i, symbol in enumerate(['AA001', 'AA002', 'BB001', 'CA001']):
            raw_id = self.register_raw_data_symbol(
                symbol, timeframe, Period.COMMON, currency, 0.0
            )
            base_data_ids.append(raw_id)
        
        # Layer 3: 判定関数群をDAG化
        
        # 同逆判定関数
        dokyaku_id = PKGId(timeframe, Period.COMMON, currency, 3, 1)
        self.register_pkg_function(
            dokyaku_id, 
            'Dokyaku',
            base_data_ids[:2]  # AA001, AA002に依存
        )
        
        # 行帰判定関数
        ikikaeri_id = PKGId(timeframe, Period.COMMON, currency, 3, 2)
        self.register_pkg_function(
            ikikaeri_id,
            'Ikikaeri', 
            base_data_ids[1:3]  # AA002, BB001に依存
        )
        
        # もみ・オーバーシュート判定関数
        momi_os_id = PKGId(timeframe, Period.COMMON, currency, 3, 3)
        self.register_pkg_function(
            momi_os_id,
            'MomiOvershoot',
            base_data_ids[2:]  # BB001, CA001に依存
        )
        
        # Layer 4: 統合判断関数
        integration_id = PKGId(timeframe, Period.COMMON, currency, 4, 1)
        self.register_pkg_function(
            integration_id,
            'SignalIntegration',
            [dokyaku_id, ikikaeri_id, momi_os_id]  # Layer3の結果を統合
        )
        
        self.logger.info(f"メモロジックDAG化完了: {len(self.nodes)}ノード")
    
    def evaluate_dag(self, target_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        DAG全体を評価して結果を返す
        
        これがレビュー指摘への回答: 自動DAG処理
        """
        start_time = time.time()
        
        # 実行順序の決定（トポロジカルソート）
        if not self.execution_order:
            self.execution_order = self._compute_execution_order()
        
        results = {}
        layer_times = defaultdict(float)
        
        # 階層順に実行
        for pkg_id_str in self.execution_order:
            layer_start = time.time()
            node = self.nodes[pkg_id_str]
            
            # キャッシュチェック
            if self._is_cache_valid(node):
                results[pkg_id_str] = node.cached_result
                self.performance_stats['cache_hits'] += 1
                continue
            
            # 関数実行
            try:
                if node.function_type == "RAW_DATA":
                    # 生データは既にキャッシュ済み
                    result = node.cached_result
                else:
                    # 依存データを収集
                    input_data = self._collect_input_data(node, results)
                    
                    # PKG関数を実行
                    result = node.function_instance.execute(input_data)
                    
                    # 統計更新
                    node.evaluation_count += 1
                    node.last_evaluation_time = datetime.now()
                
                # 結果をキャッシュ
                node.cached_result = result
                results[pkg_id_str] = result
                
                layer_time = time.time() - layer_start
                layer_times[node.layer] += layer_time
                
                self.logger.debug(f"評価完了: {pkg_id_str} = {result} ({layer_time*1000:.2f}ms)")
                
            except Exception as e:
                self.logger.error(f"評価エラー {pkg_id_str}: {e}")
                results[pkg_id_str] = None
        
        # 性能統計更新
        total_time = time.time() - start_time
        self.performance_stats['total_evaluations'] += 1
        self.performance_stats['total_execution_time'] += total_time
        for layer, layer_time in layer_times.items():
            self.performance_stats['layer_execution_times'][layer] += layer_time
        
        self.logger.info(f"DAG評価完了: {total_time*1000:.2f}ms, {len(results)}ノード")
        
        # 指定されたIDの結果のみ返す
        if target_ids:
            return {pkg_id: results.get(pkg_id) for pkg_id in target_ids 
                   if pkg_id in results}
        
        return results
    
    def get_integrated_trading_signal(self, market_data: Dict[str, List[MarketData]],
                                    currency: Currency = Currency.USDJPY) -> Dict[str, Any]:
        """
        統合取引信号の取得
        
        これが旧OperationLogicEngineの代替: DAG自動処理
        """
        # 市場データをPKG生データとして登録
        self._update_raw_data_from_market(market_data, currency)
        
        # DAGを評価
        results = self.evaluate_dag()
        
        # Layer4の統合判断結果を取得
        integration_key = None
        for pkg_id_str, node in self.nodes.items():
            if node.layer == 4 and node.function_type == 'SignalIntegration':
                integration_key = pkg_id_str
                break
        
        if integration_key and integration_key in results:
            integration_result = results[integration_key]
            
            return {
                'overall_direction': self._extract_direction(integration_result),
                'confidence': self._extract_confidence(integration_result),
                'dokyaku_signal': results.get(self._find_function_id('Dokyaku')),
                'ikikaeri_signal': results.get(self._find_function_id('Ikikaeri')),
                'momi_overshoot_signal': results.get(self._find_function_id('MomiOvershoot')),
                'raw_results': results
            }
        else:
            self.logger.warning("統合判断結果が見つかりません")
            return {'overall_direction': 0, 'confidence': 0.0}
    
    def validate_hierarchy_consistency(self) -> Tuple[bool, List[str]]:
        """
        階層一貫性の検証
        
        上位層が下位層のみを参照しているかチェック
        """
        violations = []
        
        for pkg_id_str, node in self.nodes.items():
            for dep_id in node.input_dependencies:
                dep_str = str(dep_id)
                if dep_str in self.nodes:
                    dep_node = self.nodes[dep_str]
                    if dep_node.layer >= node.layer:
                        violations.append(
                            f"{pkg_id_str}(L{node.layer}) が "
                            f"{dep_str}(L{dep_node.layer}) に依存"
                        )
                else:
                    violations.append(f"未登録依存: {pkg_id_str} -> {dep_str}")
        
        is_valid = len(violations) == 0
        
        if is_valid:
            self.logger.info("階層一貫性検証: OK")
        else:
            self.logger.error(f"階層一貫性違反: {len(violations)}件")
            for violation in violations:
                self.logger.error(f"  - {violation}")
        
        return is_valid, violations
    
    def get_performance_report(self) -> Dict[str, Any]:
        """パフォーマンスレポートの取得"""
        total_evals = self.performance_stats['total_evaluations']
        if total_evals == 0:
            return {'message': '実行履歴なし'}
        
        avg_time = self.performance_stats['total_execution_time'] / total_evals
        cache_hit_rate = self.performance_stats['cache_hits'] / total_evals * 100
        
        return {
            'total_evaluations': total_evals,
            'average_execution_time_ms': avg_time * 1000,
            'cache_hit_rate_percent': cache_hit_rate,
            'layer_performance': {
                f"Layer_{layer}": time_ms * 1000 / total_evals 
                for layer, time_ms in self.performance_stats['layer_execution_times'].items()
            },
            'registered_functions': len(self.nodes),
            'layers_used': sorted(self.layer_groups.keys())
        }
    
    def visualize_dag_structure(self) -> str:
        """DAG構造の可視化"""
        lines = ["PKG関数型DAG構造:", "=" * 50]
        
        for layer in sorted(self.layer_groups.keys()):
            layer_name = FunctionLevel(layer).name if layer < 5 else f"CUSTOM_L{layer}"
            lines.append(f"\n{layer_name} (Layer {layer}):")
            
            nodes = self.layer_groups[layer]
            for pkg_id_str in sorted(nodes):
                node = self.nodes[pkg_id_str]
                if node.function_type == "RAW_DATA":
                    lines.append(f"  📊 {pkg_id_str} = 生データ")
                else:
                    deps = [str(dep) for dep in node.input_dependencies[:2]]
                    if len(node.input_dependencies) > 2:
                        deps.append("...")
                    dep_str = ", ".join(deps) if deps else "なし"
                    lines.append(f"  🔧 {pkg_id_str} = {node.function_type}({dep_str})")
        
        lines.append(f"\n実行順序: {len(self.execution_order)}ノード")
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    # ======== プライベートメソッド ========
    
    def _symbol_to_sequence(self, symbol: str) -> int:
        """シンボルをシーケンス番号に変換"""
        # AA001 → 1, BB123 → 123 等の簡易マッピング
        if symbol.startswith(('AA', 'BA', 'CA')):
            return int(symbol[2:])
        return hash(symbol) % 10000
    
    def _validate_layer_consistency(self, pkg_id: PKGId, dependencies: List[PKGId]) -> bool:
        """階層一貫性の事前チェック"""
        for dep in dependencies:
            if dep.layer >= pkg_id.layer:
                return False
        return True
    
    def _compute_execution_order(self) -> List[str]:
        """トポロジカルソートで実行順序を決定"""
        in_degree = defaultdict(int)
        adjacency = defaultdict(list)
        
        # 依存関係グラフ構築
        for pkg_id_str, node in self.nodes.items():
            for dep in node.input_dependencies:
                dep_str = str(dep)
                if dep_str in self.nodes:
                    adjacency[dep_str].append(pkg_id_str)
                    in_degree[pkg_id_str] += 1
        
        # 入次数0のノードから開始
        queue = deque([pkg_id for pkg_id in self.nodes if in_degree[pkg_id] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 循環依存チェック
        if len(result) != len(self.nodes):
            remaining = set(self.nodes.keys()) - set(result)
            raise ValueError(f"循環依存検出: {remaining}")
        
        return result
    
    def _is_cache_valid(self, node: PKGNodeDefinition) -> bool:
        """キャッシュの有効性チェック"""
        if node.cached_result is None:
            return False
        if node.function_type == "RAW_DATA":
            return True  # 生データは常に有効
        # 実装を簡素化: 常に再評価
        return False
    
    def _collect_input_data(self, node: PKGNodeDefinition, results: Dict[str, Any]) -> Dict[str, Any]:
        """入力データの収集"""
        input_data = {}
        
        # 基本的な入力収集
        inputs = []
        for dep in node.input_dependencies:
            dep_str = str(dep)
            if dep_str in results:
                inputs.append(results[dep_str])
        
        # 関数タイプ別のデータ形式
        if node.function_type in ['Dokyaku', 'Ikikaeri', 'MomiOvershoot']:
            # メモロジック関数は market_data 形式
            input_data['market_data'] = inputs if inputs else []
        else:
            # 一般的なPKG関数は inputs 形式
            input_data['inputs'] = inputs
        
        return input_data
    
    def _update_raw_data_from_market(self, market_data: Dict[str, List[MarketData]],
                                   currency: Currency):
        """市場データからPKG生データを更新"""
        # 実装簡略化: M15データのみ使用
        m15_data = market_data.get('M15', [])
        if m15_data:
            current_bar = m15_data[-1]
            # ダミー更新
            for pkg_id_str in list(self.raw_data_store.keys()):
                self.raw_data_store[pkg_id_str] = current_bar.close
                self.nodes[pkg_id_str].cached_result = current_bar.close
    
    def _find_function_id(self, function_type: str) -> Optional[str]:
        """関数タイプからPKG IDを検索"""
        for pkg_id_str, node in self.nodes.items():
            if node.function_type == function_type:
                return pkg_id_str
        return None
    
    def _extract_direction(self, signal) -> int:
        """信号から方向を抽出"""
        if isinstance(signal, OperationSignal):
            return signal.direction
        return 0
    
    def _extract_confidence(self, signal) -> float:
        """信号から信頼度を抽出"""
        if isinstance(signal, OperationSignal):
            return signal.confidence
        return 0.0


# 使用例: 旧手動統合の置き換え
def demo_pkg_function_manager():
    """PKGFunctionManagerのデモ"""
    logging.basicConfig(level=logging.INFO)
    
    manager = PKGFunctionManager()
    
    # メモロジックをDAG化
    manager.register_memo_logic_as_dag()
    
    # DAG構造を表示
    print(manager.visualize_dag_structure())
    
    # 階層一貫性チェック
    is_valid, violations = manager.validate_hierarchy_consistency()
    print(f"\n階層一貫性: {'✓' if is_valid else '✗'}")
    
    # ダミー市場データで評価
    dummy_market_data = {
        'M15': [MarketData(
            timestamp=datetime.now(),
            open=150.0, high=150.1, low=149.9, close=150.05,
            volume=1000, 
            heikin_ashi_close=150.02, heikin_ashi_open=149.98
        )]
    }
    
    # 統合取引信号を取得
    signal = manager.get_integrated_trading_signal(dummy_market_data)
    print(f"\n統合取引信号: {signal}")
    
    # パフォーマンスレポート
    perf_report = manager.get_performance_report()
    print(f"\nパフォーマンス: {perf_report}")

if __name__ == "__main__":
    demo_pkg_function_manager()