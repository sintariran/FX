"""
DAG構成管理システム
データ駆動ノード定義と自動評価順序決定（レビューフィードバック対応）
"""

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None
import logging
from typing import Dict, List, Any, Tuple, Set, Optional
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class NodeDefinition:
    """ノード定義データクラス"""
    id: str
    layer: int
    function: str
    inputs: List[str]
    outputs: Dict[str, str]
    parameters: Dict[str, Any]
    
    def __post_init__(self):
        """PKG ID形式の検証"""
        import re
        if not re.match(r'^\d{3}\^\d+-\d{3}$', self.id):
            raise ValueError(f"Invalid PKG ID format: {self.id}")

@dataclass 
class DAGStructure:
    """DAG構造データクラス"""
    nodes: Dict[str, NodeDefinition]
    execution_order: List[str]
    layer_groups: Dict[int, List[str]]
    dependency_graph: Dict[str, List[str]]

class DAGConfigManager:
    """DAG構成管理クラス"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.nodes: Dict[str, NodeDefinition] = {}
        self.dag_structure: Optional[DAGStructure] = None
        
    def _get_default_config_path(self) -> str:
        """デフォルト設定ファイルパスを取得"""
        current_dir = Path(__file__).parent
        return str(current_dir / "node_definitions.yaml")
    
    def load_configuration(self) -> None:
        """YAML設定ファイルを読み込み"""
        if not YAML_AVAILABLE:
            logger.warning("YAML not available, using default configuration")
            self._load_default_configuration()
            return
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
            self._parse_node_definitions(config)
            self._build_dag_structure()
            
            logger.info(f"Successfully loaded {len(self.nodes)} nodes from {self.config_path}")
            
        except Exception as e:
            logger.warning(f"Failed to load YAML configuration: {e}, using default")
            self._load_default_configuration()
    
    def _load_default_configuration(self) -> None:
        """デフォルト設定を読み込み（YAML不要）"""
        # 最小限のデフォルトノード定義
        default_nodes = {
            "391^0-001": NodeDefinition(
                id="391^0-001",
                layer=0,
                function="collect_current_price",
                inputs=[],
                outputs={"price": "float", "timestamp": "datetime", "quality_score": "float"},
                parameters={"currency": "USDJPY", "timeout_ms": 100}
            ),
            "391^1-001": NodeDefinition(
                id="391^1-001",
                layer=1,
                function="calculate_heikin_ashi", 
                inputs=["391^0-001"],
                outputs={"ha_open": "float", "ha_high": "float", "ha_low": "float", "ha_close": "float", "ha_direction": "int"},
                parameters={"smoothing_factor": 0.1}
            ),
            "391^2-001": NodeDefinition(
                id="391^2-001",
                layer=2,
                function="calculate_deviation_metrics",
                inputs=["391^1-001"],
                outputs={"deviation_score": "float", "deviation_direction": "int", "confidence_level": "float"},
                parameters={"deviation_threshold": 0.02, "lookback_periods": 50}
            ),
            "391^5-001": NodeDefinition(
                id="391^5-001",
                layer=5,
                function="export_feature_summary",
                inputs=["391^2-001"],
                outputs={"feature_vector": "array", "metadata": "object", "quality_metrics": "object"},
                parameters={"export_format": "standardized", "include_metadata": True, "quality_threshold": 0.8}
            )
        }
        
        self.nodes = default_nodes
        self._build_dag_structure()
        logger.info(f"Loaded default configuration with {len(self.nodes)} nodes")
    
    def _parse_node_definitions(self, config: Dict[str, Any]) -> None:
        """ノード定義を解析"""
        self.nodes.clear()
        
        # 各カテゴリのノードを解析
        for category in ['data_collection', 'basic_indicators', 'composite_indicators', 
                        'pattern_recognition', 'timeframe_integration', 'export_layer']:
            if category in config:
                for node_config in config[category]:
                    node = NodeDefinition(
                        id=node_config['id'],
                        layer=node_config['layer'],
                        function=node_config['function'],
                        inputs=node_config['inputs'],
                        outputs=node_config['outputs'],
                        parameters=node_config['parameters']
                    )
                    self.nodes[node.id] = node
    
    def _build_dag_structure(self) -> None:
        """DAG構造を構築"""
        # 依存関係グラフの構築
        dependency_graph = self._build_dependency_graph()
        
        # トポロジカルソートによる実行順序決定
        execution_order = self._topological_sort(dependency_graph)
        
        # 階層別グループ化
        layer_groups = self._group_by_layer()
        
        self.dag_structure = DAGStructure(
            nodes=self.nodes,
            execution_order=execution_order,
            layer_groups=layer_groups,
            dependency_graph=dependency_graph
        )
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """依存関係グラフを構築"""
        graph = defaultdict(list)
        
        for node_id, node in self.nodes.items():
            for input_id in node.inputs:
                if input_id in self.nodes:
                    graph[input_id].append(node_id)
        
        return dict(graph)
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """トポロジカルソートによる実行順序決定"""
        # 入次数を計算
        in_degree = defaultdict(int)
        all_nodes = set(self.nodes.keys())
        
        for node_id in all_nodes:
            in_degree[node_id] = 0
        
        for node_id, node in self.nodes.items():
            for input_id in node.inputs:
                if input_id in all_nodes:
                    in_degree[node_id] += 1
        
        # トポロジカルソート実行
        queue = deque([node for node in all_nodes if in_degree[node] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # 依存ノードの入次数を減算
            for dependent in graph.get(current, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # 循環依存の検出
        if len(result) != len(all_nodes):
            remaining = all_nodes - set(result)
            raise ValueError(f"Circular dependency detected in nodes: {remaining}")
        
        return result
    
    def _group_by_layer(self) -> Dict[int, List[str]]:
        """階層別にノードをグループ化"""
        layer_groups = defaultdict(list)
        
        for node_id, node in self.nodes.items():
            layer_groups[node.layer].append(node_id)
        
        # 各階層内でIDでソート
        for layer in layer_groups:
            layer_groups[layer].sort()
        
        return dict(layer_groups)
    
    def get_execution_order(self) -> List[str]:
        """実行順序を取得"""
        if not self.dag_structure:
            raise RuntimeError("Configuration not loaded. Call load_configuration() first.")
        return self.dag_structure.execution_order
    
    def get_node_definition(self, node_id: str) -> NodeDefinition:
        """ノード定義を取得"""
        if node_id not in self.nodes:
            raise KeyError(f"Node {node_id} not found")
        return self.nodes[node_id]
    
    def get_layer_nodes(self, layer: int) -> List[str]:
        """指定階層のノード一覧を取得"""
        if not self.dag_structure:
            raise RuntimeError("Configuration not loaded")
        return self.dag_structure.layer_groups.get(layer, [])
    
    def validate_dependencies(self) -> Tuple[bool, List[str]]:
        """依存関係の妥当性を検証"""
        errors = []
        
        for node_id, node in self.nodes.items():
            # 入力ノードの存在確認
            for input_id in node.inputs:
                if input_id not in self.nodes:
                    errors.append(f"Node {node_id} references missing input: {input_id}")
            
            # 階層制約の確認（下位階層のみ参照可能）
            for input_id in node.inputs:
                if input_id in self.nodes:
                    input_layer = self.nodes[input_id].layer
                    if input_layer >= node.layer:
                        errors.append(
                            f"Invalid layer reference: {node_id}(layer {node.layer}) "
                            f"→ {input_id}(layer {input_layer})"
                        )
        
        return len(errors) == 0, errors
    
    def generate_dot_graph(self) -> str:
        """Graphviz DOT形式でグラフを生成"""
        if not self.dag_structure:
            raise RuntimeError("Configuration not loaded")
        
        lines = ["digraph FeatureDAG {"]
        lines.append("  rankdir=TB;")
        lines.append("  node [shape=box];")
        
        # ノードの定義
        for node_id, node in self.nodes.items():
            label = f"{node_id}\\n{node.function}"
            color = self._get_layer_color(node.layer)
            lines.append(f'  "{node_id}" [label="{label}", fillcolor="{color}", style=filled];')
        
        # エッジの定義
        for node_id, node in self.nodes.items():
            for input_id in node.inputs:
                if input_id in self.nodes:
                    lines.append(f'  "{input_id}" -> "{node_id}";')
        
        lines.append("}")
        return "\n".join(lines)
    
    def _get_layer_color(self, layer: int) -> str:
        """階層に応じた色を取得"""
        colors = {
            0: "lightblue",
            1: "lightgreen", 
            2: "lightyellow",
            3: "lightcoral",
            4: "lightpink",
            5: "lightgray"
        }
        return colors.get(layer, "white")
    
    def get_ai_exploration_config(self) -> Dict[str, Any]:
        """AI エージェント探索用設定を取得"""
        if not YAML_AVAILABLE:
            return self._get_default_ai_config()
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
            return config.get('ai_agent_config', {})
        except Exception as e:
            logger.warning(f"Failed to load AI exploration config: {e}")
            return self._get_default_ai_config()
    
    def _get_default_ai_config(self) -> Dict[str, Any]:
        """デフォルトAI探索設定を取得"""
        return {
            "exploration_parameters": [
                {
                    "parameter": "deviation_threshold",
                    "range": [0.01, 0.05],
                    "step": 0.001,
                    "description": "乖離判定の閾値"
                },
                {
                    "parameter": "smoothing_factor", 
                    "range": [0.05, 0.2],
                    "step": 0.01,
                    "description": "平均足スムージング係数"
                }
            ],
            "optimization_targets": [
                {"metric": "prediction_accuracy", "weight": 0.5},
                {"metric": "signal_stability", "weight": 0.3},
                {"metric": "execution_speed", "weight": 0.2}
            ]
        }
    
    def update_node_parameters(self, node_id: str, parameters: Dict[str, Any]) -> None:
        """ノードパラメータを更新（AI エージェント用）"""
        if node_id not in self.nodes:
            raise KeyError(f"Node {node_id} not found")
        
        # パラメータの妥当性確認
        node = self.nodes[node_id]
        for param_name, param_value in parameters.items():
            if param_name not in node.parameters:
                logger.warning(f"Adding new parameter {param_name} to node {node_id}")
        
        # パラメータ更新
        node.parameters.update(parameters)
        logger.info(f"Updated parameters for node {node_id}: {parameters}")