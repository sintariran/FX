#!/usr/bin/env python3
"""
DAG評価エンジン v2 - メモロジック統合版
生データシンボルもPKG ID体系に従う完全統合実装
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
import time
from enum import Enum

# 基本PKG関数のインポート（簡易版、依存なし）
# numpyの依存を避けるため、simple_pkg_test_runnerから借用
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_pkg_test_runner import (
    BasicPKGFunctionFactory,
    PKGId, TimeFrame, Period, Currency
)

@dataclass
class PKGNode:
    """
    PKGノード定義
    生データもPKG関数も同じ構造で扱う
    """
    pkg_id: str  # 例: "391^0-AA001" (生データ) or "391^2-126" (Layer2関数)
    node_type: str  # "RAW_DATA" or "FUNCTION"
    function_type: Optional[str] = None  # Z, SL, MN等（関数の場合）
    function_params: Dict[str, Any] = field(default_factory=dict)
    input_refs: List[str] = field(default_factory=list)  # 入力PKG IDのリスト
    layer: int = 0  # 階層番号（0=生データ、1以降=PKG関数）
    cached_value: Optional[Any] = None
    is_evaluated: bool = False

class DAGEngine:
    """
    関数型DAG評価エンジン
    階層的PKG構造を管理・実行
    """
    
    def __init__(self):
        self.nodes: Dict[str, PKGNode] = {}
        self.raw_data_values: Dict[str, Any] = {}  # 生データの値
        self.execution_order: List[str] = []
        self.logger = logging.getLogger(__name__)
        
        # PKG関数ファクトリー
        self.function_factory = BasicPKGFunctionFactory()
        
    def register_raw_data(self, symbol: str, timeframe: int, period: int, 
                         currency: int, value: Any):
        """
        生データシンボルを登録
        例: AA001 → "191^0-AA001" (1分足, 周期9, USDJPY, Layer0, AA001)
        """
        pkg_id = f"{timeframe}{period}{currency}^0-{symbol}"
        
        node = PKGNode(
            pkg_id=pkg_id,
            node_type="RAW_DATA",
            layer=0,
            cached_value=value,
            is_evaluated=True
        )
        
        self.nodes[pkg_id] = node
        self.raw_data_values[pkg_id] = value
        
        self.logger.debug(f"生データ登録: {pkg_id} = {value}")
        
    def register_function(self, pkg_id: str, function_type: str, 
                         input_refs: List[str], **function_params):
        """
        PKG関数ノードを登録
        例: Z関数でAA001とBA001を減算 → "391^1-001"
        """
        # PKG IDをパース
        parsed_id = PKGId.parse(pkg_id)
        
        node = PKGNode(
            pkg_id=pkg_id,
            node_type="FUNCTION",
            function_type=function_type,
            function_params=function_params,
            input_refs=input_refs,
            layer=parsed_id.layer
        )
        
        self.nodes[pkg_id] = node
        self.logger.debug(f"関数登録: {pkg_id} = {function_type}({input_refs})")
        
    def _topological_sort(self) -> List[str]:
        """
        トポロジカルソートで実行順序を決定
        """
        # 入次数を計算
        in_degree = defaultdict(int)
        adjacency = defaultdict(list)
        
        for pkg_id, node in self.nodes.items():
            for input_ref in node.input_refs:
                adjacency[input_ref].append(pkg_id)
                in_degree[pkg_id] += 1
        
        # 入次数0のノードから開始
        queue = deque([pkg_id for pkg_id in self.nodes 
                      if in_degree[pkg_id] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # 依存先の入次数を減らす
            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 循環依存チェック
        if len(result) != len(self.nodes):
            raise ValueError("循環依存が検出されました")
        
        return result
    
    def evaluate(self, target_pkg_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        DAGを評価して結果を返す
        """
        # 実行順序を決定
        self.execution_order = self._topological_sort()
        
        results = {}
        start_time = time.time()
        
        for pkg_id in self.execution_order:
            node = self.nodes[pkg_id]
            
            # すでに評価済み（生データやキャッシュ）
            if node.is_evaluated:
                results[pkg_id] = node.cached_value
                continue
            
            # 関数ノードの評価
            if node.node_type == "FUNCTION":
                # 入力値を収集
                input_values = {}
                for input_ref in node.input_refs:
                    if input_ref in results:
                        input_values[input_ref] = results[input_ref]
                    else:
                        self.logger.warning(f"入力 {input_ref} が見つかりません")
                
                # PKG関数を実行
                result = self._execute_function(node, input_values)
                
                # 結果を保存
                node.cached_value = result
                node.is_evaluated = True
                results[pkg_id] = result
                
                self.logger.debug(f"評価: {pkg_id} = {result}")
        
        elapsed = time.time() - start_time
        self.logger.info(f"DAG評価完了: {elapsed*1000:.2f}ms")
        
        # 指定されたPKG IDの結果のみ返す
        if target_pkg_ids:
            return {pkg_id: results[pkg_id] for pkg_id in target_pkg_ids 
                   if pkg_id in results}
        
        return results
    
    def _execute_function(self, node: PKGNode, input_values: Dict[str, Any]) -> Any:
        """
        PKG関数を実行
        """
        # PKG IDをパース
        parsed_id = PKGId.parse(node.pkg_id)
        
        # 関数インスタンスを作成（defaultはパラメータではなくデータの一部）
        func_params = {k: v for k, v in node.function_params.items() 
                      if k != 'default'}
        func = self.function_factory.create_function(
            node.function_type, 
            parsed_id,
            **func_params
        )
        
        # 入力データを準備
        if node.function_type == 'Z':
            # Z関数は入力値のリストを期待
            inputs = [input_values.get(ref, 0) for ref in node.input_refs]
            data = {'inputs': inputs}
        elif node.function_type == 'SL':
            # SL関数は条件とオプションを期待
            condition = input_values.get(node.input_refs[0], False) if node.input_refs else False
            options = [input_values.get(ref) for ref in node.input_refs[1:]]
            data = {
                'condition': condition,
                'options': options,
                'default': node.function_params.get('default', 0)
            }
        elif node.function_type == 'CO':
            # CO関数は時系列とターゲットコードを期待
            if len(node.input_refs) == 1:
                # メモ仕様: 単一値の場合は連続和
                data = {'target_code': input_values.get(node.input_refs[0], 0)}
            else:
                # 通常のカウント
                time_series = [input_values.get(ref) for ref in node.input_refs[:-1]]
                target = input_values.get(node.input_refs[-1], 0)
                data = {
                    'time_series': time_series,
                    'target_code': target
                }
        else:
            # その他の関数（MN, RO等）
            data = {}
            if node.input_refs:
                primary_input = input_values.get(node.input_refs[0])
                if node.function_type == 'MN':
                    data['current_time'] = primary_input
                elif node.function_type == 'RO':
                    data['input_value'] = primary_input
        
        # 関数を実行
        return func.execute(data)
    
    def visualize_graph(self) -> str:
        """
        DAGの構造を可視化（テキスト形式）
        """
        layers = defaultdict(list)
        for pkg_id, node in self.nodes.items():
            layers[node.layer].append(pkg_id)
        
        result = ["DAG構造:"]
        for layer in sorted(layers.keys()):
            result.append(f"\nLayer {layer}:")
            for pkg_id in layers[layer]:
                node = self.nodes[pkg_id]
                if node.node_type == "RAW_DATA":
                    result.append(f"  [{pkg_id}] = 生データ")
                else:
                    inputs = ", ".join(node.input_refs[:3])
                    if len(node.input_refs) > 3:
                        inputs += "..."
                    result.append(f"  [{pkg_id}] = {node.function_type}({inputs})")
        
        return "\n".join(result)


# 使用例とテスト
def demo_dag_engine():
    """DAGエンジンのデモ"""
    
    # ロギング設定
    logging.basicConfig(level=logging.DEBUG, 
                       format='%(levelname)s: %(message)s')
    
    engine = DAGEngine()
    
    # 生データの登録（15分足、共通、USDJPY）
    engine.register_raw_data("AA001", 3, 9, 1, 110.50)  # 391^0-AA001
    engine.register_raw_data("AA002", 3, 9, 1, 110.45)  # 391^0-AA002
    engine.register_raw_data("BA001", 3, 9, 1, 0.95)   # 391^0-BA001
    
    # Layer 1: 生データを処理
    # AA001とAA002の差分
    engine.register_function(
        pkg_id="391^1-001",  # 3=15分足, 9=共通, 1=USDJPY
        function_type="Z",
        input_refs=["391^0-AA001", "391^0-AA002"],
        operation_type=2
    )
    
    # BA001を丸める
    engine.register_function(
        pkg_id="391^1-002", 
        function_type="RO",
        input_refs=["391^0-BA001"]
    )
    
    # Layer 2: Layer 1の結果を処理
    # Layer 1の結果を選択
    engine.register_function(
        pkg_id="391^2-001",
        function_type="SL",
        input_refs=["391^1-002", "391^1-001", "391^0-AA001"],  # 条件, 真の値, 偽の値
        default=0
    )
    
    # DAG構造を表示
    print(engine.visualize_graph())
    print("\n" + "="*60)
    
    # 評価実行
    results = engine.evaluate()
    
    print("\n評価結果:")
    for pkg_id in sorted(results.keys()):
        print(f"  {pkg_id} = {results[pkg_id]}")
    
    # 特定のPKG IDの結果を取得
    print(f"\n最終結果 (391^2-001): {results.get('391^2-001')}")

if __name__ == "__main__":
    demo_dag_engine()