"""
DAGキャッシュシステム
レビューフィードバックに基づく性能最適化実装

DAG構造を初回構築後キャッシュし、再利用することで
毎サイクルの再構築オーバーヘッドを削減
"""

from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class DAGNode:
    """DAGノード"""
    id: str
    level: int
    dependencies: Set[str] = field(default_factory=set)
    cache_value: Optional[Any] = None
    cache_timestamp: Optional[float] = None
    
    def is_cache_valid(self, max_age_ms: float = 1000) -> bool:
        """キャッシュの有効性確認"""
        if self.cache_timestamp is None:
            return False
        age_ms = (time.time() - self.cache_timestamp) * 1000
        return age_ms < max_age_ms


class DAGCache:
    """
    DAGキャッシュ管理クラス
    
    性能最適化のためDAG構造とトポロジカルソート結果をキャッシュ
    """
    
    def __init__(self, cache_ttl_ms: float = 60000):
        """
        Args:
            cache_ttl_ms: キャッシュ有効期限（ミリ秒）
        """
        self.nodes: Dict[str, DAGNode] = {}
        self.topological_order: Optional[List[str]] = None
        self.adjacency_list: Dict[str, Set[str]] = {}
        self.reverse_adjacency: Dict[str, Set[str]] = {}
        self.cache_ttl_ms = cache_ttl_ms
        self.dag_built_timestamp: Optional[float] = None
        self.build_time_ms: float = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        
    def add_node(self, node_id: str, level: int, dependencies: Optional[Set[str]] = None):
        """ノード追加"""
        if node_id not in self.nodes:
            self.nodes[node_id] = DAGNode(
                id=node_id,
                level=level,
                dependencies=dependencies or set()
            )
            self.adjacency_list[node_id] = dependencies or set()
            
            # 逆参照も構築
            for dep_id in (dependencies or set()):
                if dep_id not in self.reverse_adjacency:
                    self.reverse_adjacency[dep_id] = set()
                self.reverse_adjacency[dep_id].add(node_id)
    
    def add_edge(self, from_id: str, to_id: str):
        """エッジ追加（from_id -> to_id）"""
        if from_id in self.nodes and to_id in self.nodes:
            self.nodes[to_id].dependencies.add(from_id)
            self.adjacency_list[to_id].add(from_id)
            
            if from_id not in self.reverse_adjacency:
                self.reverse_adjacency[from_id] = set()
            self.reverse_adjacency[from_id].add(to_id)
    
    def is_dag_valid(self) -> bool:
        """DAG構造の有効性確認（循環検出）"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in self.adjacency_list.get(node_id, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    return False
        return True
    
    def build_topological_order(self, force_rebuild: bool = False) -> List[str]:
        """
        トポロジカルソート実行
        
        Args:
            force_rebuild: 強制再構築フラグ
            
        Returns:
            トポロジカル順序のノードIDリスト
        """
        # キャッシュ確認
        if not force_rebuild and self.topological_order is not None:
            if self.dag_built_timestamp:
                age_ms = (time.time() - self.dag_built_timestamp) * 1000
                if age_ms < self.cache_ttl_ms:
                    self.cache_hits += 1
                    logger.debug(f"Topological order cache hit (age: {age_ms:.1f}ms)")
                    return self.topological_order
        
        self.cache_misses += 1
        start_time = time.time()
        
        # Kahn's algorithm
        in_degree = {node_id: len(deps) for node_id, deps in self.adjacency_list.items()}
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # レベル順でソート（同レベル内では安定）
            queue.sort(key=lambda x: self.nodes[x].level)
            node_id = queue.pop(0)
            result.append(node_id)
            
            for neighbor in self.reverse_adjacency.get(node_id, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(self.nodes):
            raise ValueError("DAGに循環が存在します")
        
        self.topological_order = result
        self.dag_built_timestamp = time.time()
        self.build_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Topological order built in {self.build_time_ms:.2f}ms")
        return result
    
    def get_evaluation_order(self) -> List[str]:
        """評価順序取得（キャッシュ利用）"""
        return self.build_topological_order(force_rebuild=False)
    
    def cache_node_value(self, node_id: str, value: Any):
        """ノード値のキャッシュ"""
        if node_id in self.nodes:
            self.nodes[node_id].cache_value = value
            self.nodes[node_id].cache_timestamp = time.time()
    
    def get_cached_value(self, node_id: str, max_age_ms: Optional[float] = None) -> Optional[Any]:
        """キャッシュ値取得"""
        max_age = max_age_ms or self.cache_ttl_ms
        
        if node_id in self.nodes:
            node = self.nodes[node_id]
            if node.is_cache_valid(max_age):
                self.cache_hits += 1
                return node.cache_value
        
        self.cache_misses += 1
        return None
    
    def invalidate_cache(self, node_id: Optional[str] = None):
        """キャッシュ無効化"""
        if node_id:
            # 特定ノードと依存先を無効化
            if node_id in self.nodes:
                self.nodes[node_id].cache_value = None
                self.nodes[node_id].cache_timestamp = None
                
                # 依存先も連鎖的に無効化
                for dependent in self.reverse_adjacency.get(node_id, set()):
                    self.invalidate_cache(dependent)
        else:
            # 全キャッシュ無効化
            for node in self.nodes.values():
                node.cache_value = None
                node.cache_timestamp = None
    
    def get_dependencies(self, node_id: str) -> Set[str]:
        """依存関係取得"""
        if node_id in self.nodes:
            return self.nodes[node_id].dependencies
        return set()
    
    def get_dependents(self, node_id: str) -> Set[str]:
        """依存先取得"""
        return self.reverse_adjacency.get(node_id, set())
    
    def get_level_nodes(self, level: int) -> List[str]:
        """特定レベルのノード取得"""
        return [node_id for node_id, node in self.nodes.items() if node.level == level]
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            'node_count': len(self.nodes),
            'edge_count': sum(len(deps) for deps in self.adjacency_list.values()),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': self.cache_hits / max(1, self.cache_hits + self.cache_misses),
            'build_time_ms': self.build_time_ms,
            'max_level': max((node.level for node in self.nodes.values()), default=0)
        }
    
    def clear(self):
        """DAG全体をクリア"""
        self.nodes.clear()
        self.adjacency_list.clear()
        self.reverse_adjacency.clear()
        self.topological_order = None
        self.dag_built_timestamp = None
        self.cache_hits = 0
        self.cache_misses = 0


class OptimizedDAGEvaluator:
    """
    最適化されたDAG評価エンジン
    
    キャッシュとバッチ処理により高速化
    """
    
    def __init__(self, cache: DAGCache):
        self.cache = cache
        self.evaluation_count = 0
        self.total_evaluation_time_ms = 0
        
    def evaluate(self, 
                input_values: Dict[str, Any],
                evaluation_func: callable,
                use_cache: bool = True) -> Dict[str, Any]:
        """
        DAG評価実行
        
        Args:
            input_values: 入力値の辞書
            evaluation_func: 各ノードの評価関数 func(node_id, dependencies) -> value
            use_cache: キャッシュ使用フラグ
            
        Returns:
            各ノードの評価結果
        """
        start_time = time.time()
        results = {}
        
        # トポロジカル順序で評価
        order = self.cache.get_evaluation_order()
        
        for node_id in order:
            # キャッシュ確認
            if use_cache:
                cached_value = self.cache.get_cached_value(node_id, max_age_ms=1000)
                if cached_value is not None:
                    results[node_id] = cached_value
                    continue
            
            # 依存値収集
            dependencies = {}
            for dep_id in self.cache.get_dependencies(node_id):
                if dep_id in results:
                    dependencies[dep_id] = results[dep_id]
                elif dep_id in input_values:
                    dependencies[dep_id] = input_values[dep_id]
            
            # 評価実行
            value = evaluation_func(node_id, dependencies)
            results[node_id] = value
            
            # キャッシュ保存
            if use_cache:
                self.cache.cache_node_value(node_id, value)
        
        self.evaluation_count += 1
        self.total_evaluation_time_ms += (time.time() - start_time) * 1000
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """評価統計取得"""
        avg_time = self.total_evaluation_time_ms / max(1, self.evaluation_count)
        return {
            'evaluation_count': self.evaluation_count,
            'total_evaluation_time_ms': self.total_evaluation_time_ms,
            'average_evaluation_time_ms': avg_time,
            'cache_statistics': self.cache.get_statistics()
        }


if __name__ == "__main__":
    # テスト実行
    print("🧪 DAGキャッシュシステムテスト")
    
    # DAG構築
    cache = DAGCache(cache_ttl_ms=5000)
    
    # ノード追加（PKGシステムを模擬）
    # レベル1: 基本指標
    cache.add_node("191^1-1", level=1)  # 平均足
    cache.add_node("191^1-2", level=1)  # OsMA
    
    # レベル2: 演算
    cache.add_node("191^2-1", level=2, dependencies={"191^1-1"})
    cache.add_node("191^2-2", level=2, dependencies={"191^1-1", "191^1-2"})
    
    # レベル3: 統合判断
    cache.add_node("191^3-1", level=3, dependencies={"191^2-1", "191^2-2"})
    
    # DAG検証
    assert cache.is_dag_valid(), "DAGに循環が存在"
    
    # トポロジカルソート
    order = cache.build_topological_order()
    print(f"✅ トポロジカル順序: {order}")
    
    # キャッシュテスト
    order2 = cache.get_evaluation_order()  # キャッシュヒット
    assert order == order2, "キャッシュ不整合"
    
    # 統計表示
    stats = cache.get_statistics()
    print(f"📊 統計情報:")
    print(f"   ノード数: {stats['node_count']}")
    print(f"   エッジ数: {stats['edge_count']}")
    print(f"   キャッシュヒット率: {stats['cache_hit_rate']:.2%}")
    print(f"   構築時間: {stats['build_time_ms']:.2f}ms")
    
    print("\n✅ DAGキャッシュシステムテスト完了")