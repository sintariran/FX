"""
DAG設定管理システム
YAML定義の読み込み、検証、トポロジカルソートによる実行順序決定
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

class NodeDefinition:
    """ノード定義クラス"""
    
    def __init__(self, node_id: str, layer: int, function: str, 
                 inputs: List[str], outputs: Dict[str, str], 
                 description: str = ""):
        self.id = node_id
        self.layer = layer
        self.function = function
        self.inputs = inputs
        self.outputs = outputs
        self.description = description
        
        # ID形式検証
        self._validate_id_format()
        
    def _validate_id_format(self):
        """PKG ID形式を検証"""
        pattern = r'^\d{3}\^\d+-\d{3}$'
        if not re.match(pattern, self.id):
            raise ValueError(f"Invalid PKG ID format: {self.id}")
        
        # ID内の階層番号と実際の階層が一致するか確認
        id_parts = self.id.split('^')
        if len(id_parts) == 2:
            layer_seq = id_parts[1].split('-')
            if len(layer_seq) == 2:
                id_layer = int(layer_seq[0])
                if id_layer != self.layer:
                    raise ValueError(
                        f"Layer mismatch in ID {self.id}: "
                        f"ID layer={id_layer}, actual layer={self.layer}"
                    )

class DAGConfigManager:
    """DAG設定管理クラス"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.nodes: Dict[str, NodeDefinition] = {}
        self.layers: Dict[int, List[str]] = defaultdict(list)
        self.execution_order: List[str] = []
        
        if config_path and config_path.exists():
            self.load_config(config_path)
    
    def load_config(self, config_path: Path):
        """YAML設定ファイルを読み込み"""
        try:
            import yaml
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self._parse_config(config)
            self._validate_hierarchy()  # 階層ルールの自動検証
            self._determine_execution_order()
            
            logger.info(f"Loaded DAG configuration from {config_path}")
            logger.info(f"Total nodes: {len(self.nodes)}, Layers: {len(self.layers)}")
            
        except ImportError:
            logger.warning("PyYAML not installed. Using fallback configuration.")
            self._load_fallback_config()
        except Exception as e:
            logger.error(f"Error loading DAG configuration: {e}")
            raise
    
    def _parse_config(self, config: Dict[str, Any]):
        """設定を解析してノードを構築"""
        for section_name, section_nodes in config.items():
            if not isinstance(section_nodes, list):
                continue
            
            for node_data in section_nodes:
                node = NodeDefinition(
                    node_id=node_data['id'],
                    layer=node_data['layer'],
                    function=node_data['function'],
                    inputs=node_data.get('inputs', []),
                    outputs=node_data.get('outputs', {}),
                    description=node_data.get('description', '')
                )
                
                self.nodes[node.id] = node
                self.layers[node.layer].append(node.id)
    
    def _validate_hierarchy(self):
        """階層ルールを自動検証（レビュー改善提案の実装）"""
        violations = []
        
        for node_id, node in self.nodes.items():
            # 各入力ノードをチェック
            for input_id in node.inputs:
                if input_id in self.nodes:
                    input_node = self.nodes[input_id]
                    
                    # 横参照チェック（同階層または上位階層への参照は違反）
                    if input_node.layer >= node.layer:
                        violations.append(
                            f"Horizontal reference violation: "
                            f"{node_id}(layer {node.layer}) → "
                            f"{input_id}(layer {input_node.layer})"
                        )
                    
                    # 階層の連続性チェック（オプション：厳密な階層順序を強制する場合）
                    # if input_node.layer != node.layer - 1:
                    #     logger.warning(
                    #         f"Non-sequential layer reference: "
                    #         f"{node_id}(layer {node.layer}) → "
                    #         f"{input_id}(layer {input_node.layer})"
                    #     )
        
        if violations:
            error_msg = "DAG hierarchy violations detected:\n" + "\n".join(violations)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("DAG hierarchy validation passed: No violations found")
    
    def _determine_execution_order(self):
        """トポロジカルソートによる実行順序決定"""
        # 入次数を計算
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        
        for node_id, node in self.nodes.items():
            for input_id in node.inputs:
                if input_id in self.nodes:
                    graph[input_id].append(node_id)
                    in_degree[node_id] += 1
        
        # 入次数0のノードから開始
        queue = []
        for node_id in self.nodes:
            if in_degree[node_id] == 0:
                queue.append(node_id)
        
        # トポロジカルソート
        self.execution_order = []
        while queue:
            # 同じ階層内でID順にソート（安定した順序のため）
            queue.sort(key=lambda x: (self.nodes[x].layer, x))
            node_id = queue.pop(0)
            self.execution_order.append(node_id)
            
            # 依存するノードの入次数を減らす
            for next_node in graph[node_id]:
                in_degree[next_node] -= 1
                if in_degree[next_node] == 0:
                    queue.append(next_node)
        
        # 循環依存チェック
        if len(self.execution_order) != len(self.nodes):
            raise ValueError("Circular dependency detected in DAG")
    
    def _load_fallback_config(self):
        """YAMLが利用できない場合のフォールバック設定"""
        # 最小限の設定を直接定義
        fallback_nodes = [
            {
                'id': '391^0-001',
                'layer': 0,
                'function': 'collect_current_price',
                'inputs': [],
                'outputs': {'price': 'float'},
                'description': 'Current price collection'
            },
            {
                'id': '391^1-001',
                'layer': 1,
                'function': 'calculate_price_change',
                'inputs': ['391^0-001'],
                'outputs': {'change_pct': 'float'},
                'description': 'Price change calculation'
            }
        ]
        
        config = {'fallback': fallback_nodes}
        self._parse_config(config)
        self._validate_hierarchy()
        self._determine_execution_order()
    
    def get_node(self, node_id: str) -> Optional[NodeDefinition]:
        """ノードIDからノード定義を取得"""
        return self.nodes.get(node_id)
    
    def get_layer_nodes(self, layer: int) -> List[str]:
        """指定階層のノードIDリストを取得"""
        return self.layers.get(layer, [])
    
    def get_execution_order(self) -> List[str]:
        """実行順序を取得"""
        return self.execution_order
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """入力データの検証"""
        # 階層0のノードに必要な入力があるか確認
        layer_0_nodes = self.get_layer_nodes(0)
        
        for node_id in layer_0_nodes:
            node = self.get_node(node_id)
            if node and node.function in ['collect_market_tick', 'collect_current_price']:
                # これらの関数は外部データを必要とする
                required_keys = ['price', 'timestamp']
                for key in required_keys:
                    if key not in inputs:
                        logger.warning(f"Missing required input: {key}")
                        return False
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """DAG統計情報を取得"""
        stats = {
            'total_nodes': len(self.nodes),
            'total_layers': len(self.layers),
            'nodes_per_layer': {
                layer: len(nodes) 
                for layer, nodes in self.layers.items()
            },
            'max_layer_depth': max(self.layers.keys()) if self.layers else 0,
            'execution_steps': len(self.execution_order)
        }
        
        # 依存関係の統計
        total_dependencies = sum(
            len(node.inputs) for node in self.nodes.values()
        )
        stats['total_dependencies'] = total_dependencies
        stats['avg_dependencies_per_node'] = (
            total_dependencies / len(self.nodes) if self.nodes else 0
        )
        
        return stats
    
    def export_graph(self) -> Dict[str, Any]:
        """DAGグラフをエクスポート（可視化用）"""
        graph = {
            'nodes': [],
            'edges': []
        }
        
        for node_id, node in self.nodes.items():
            graph['nodes'].append({
                'id': node_id,
                'layer': node.layer,
                'function': node.function,
                'description': node.description
            })
            
            for input_id in node.inputs:
                if input_id in self.nodes:
                    graph['edges'].append({
                        'from': input_id,
                        'to': node_id
                    })
        
        return graph