#!/usr/bin/env python3
"""
横参照分析スクリプト
PKGルール違反（同一階層内の参照）を特定する
"""

import os
import re
import ast
import sys
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class NodeReference:
    """ノード参照情報"""
    source_node: str
    target_node: str
    source_file: str
    line_number: int
    line_content: str

@dataclass
class LayerInfo:
    """階層情報"""
    layer_id: int
    nodes: Set[str]
    file_path: str

class HorizontalReferenceAnalyzer:
    """横参照分析器"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.pkg_id_pattern = re.compile(r'(\d)(\d)(\d)\^(\d+)-(\d+)')
        self.layers: Dict[int, LayerInfo] = {}
        self.references: List[NodeReference] = []
        self.violations: List[NodeReference] = []
    
    def analyze(self) -> Dict[str, any]:
        """分析実行"""
        print("🔍 PKG横参照分析を開始...")
        
        # 1. 全Pythonファイルをスキャン
        py_files = list(self.root_dir.rglob("*.py"))
        print(f"📁 分析対象ファイル数: {len(py_files)}")
        
        # 2. PKGノードとその階層を抽出
        self._extract_nodes_and_layers(py_files)
        
        # 3. 参照関係を抽出
        self._extract_references(py_files)
        
        # 4. 横参照違反を特定
        self._identify_violations()
        
        # 5. 結果をまとめ
        return self._generate_report()
    
    def _extract_nodes_and_layers(self, py_files: List[Path]):
        """ノードと階層の抽出"""
        print("🔍 PKGノードと階層を抽出中...")
        
        for file_path in py_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # PKG IDパターンを検索
                matches = self.pkg_id_pattern.findall(content)
                for match in matches:
                    timeframe, period, currency, hierarchy, sequence = match
                    layer_id = int(hierarchy)
                    node_id = f"{timeframe}{period}{currency}^{hierarchy}-{sequence}"
                    
                    if layer_id not in self.layers:
                        self.layers[layer_id] = LayerInfo(
                            layer_id=layer_id,
                            nodes=set(),
                            file_path=str(file_path)
                        )
                    
                    self.layers[layer_id].nodes.add(node_id)
                    
                # 簡易的な階層参照パターンも検索
                layer_patterns = [
                    r'layer(\d+).*layer(\d+)',
                    r'階層(\d+).*階層(\d+)',
                    r'Layer(\d+).*Layer(\d+)'
                ]
                
                for pattern in layer_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        layer1 = int(match.group(1))
                        layer2 = int(match.group(2))
                        if layer1 == layer2:
                            # 同一階層参照の可能性
                            line_num = content[:match.start()].count('\n') + 1
                            line_content = content.split('\n')[line_num - 1].strip()
                            print(f"⚠️  同一階層参照の可能性: {file_path}:{line_num}")
                            print(f"   {line_content}")
            
            except Exception as e:
                print(f"❌ エラー: {file_path} - {e}")
    
    def _extract_references(self, py_files: List[Path]):
        """参照関係の抽出"""
        print("🔍 参照関係を抽出中...")
        
        for file_path in py_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    # PKGノードID同士の参照を検索
                    pkg_ids = self.pkg_id_pattern.findall(line)
                    
                    if len(pkg_ids) >= 2:
                        # 複数のPKG IDが同一行にある場合は参照の可能性
                        for j in range(len(pkg_ids) - 1):
                            source = f"{pkg_ids[j][0]}{pkg_ids[j][1]}{pkg_ids[j][2]}^{pkg_ids[j][3]}-{pkg_ids[j][4]}"
                            target = f"{pkg_ids[j+1][0]}{pkg_ids[j+1][1]}{pkg_ids[j+1][2]}^{pkg_ids[j+1][3]}-{pkg_ids[j+1][4]}"
                            
                            ref = NodeReference(
                                source_node=source,
                                target_node=target,
                                source_file=str(file_path),
                                line_number=i,
                                line_content=line.strip()
                            )
                            self.references.append(ref)
            
            except Exception as e:
                print(f"❌ エラー: {file_path} - {e}")
    
    def _identify_violations(self):
        """横参照違反の特定"""
        print("🔍 横参照違反を特定中...")
        
        for ref in self.references:
            source_layer = self._get_node_layer(ref.source_node)
            target_layer = self._get_node_layer(ref.target_node)
            
            if source_layer is not None and target_layer is not None:
                if source_layer == target_layer:
                    # 同一階層参照 = 横参照違反
                    self.violations.append(ref)
                    print(f"❌ 横参照違反: {ref.source_node} → {ref.target_node}")
                    print(f"   ファイル: {ref.source_file}:{ref.line_number}")
                    print(f"   内容: {ref.line_content}")
                elif source_layer < target_layer:
                    # 上位階層が下位階層を参照 = 逆参照違反
                    print(f"⚠️  逆参照の可能性: {ref.source_node} → {ref.target_node}")
                    print(f"   階層{source_layer} → 階層{target_layer}")
    
    def _get_node_layer(self, node_id: str) -> int:
        """ノードの階層を取得"""
        match = self.pkg_id_pattern.match(node_id)
        if match:
            return int(match.group(4))
        return None
    
    def _generate_report(self) -> Dict[str, any]:
        """分析レポート生成"""
        return {
            'layers_found': len(self.layers),
            'nodes_total': sum(len(layer.nodes) for layer in self.layers.values()),
            'references_total': len(self.references),
            'violations_found': len(self.violations),
            'layers': {lid: {'nodes': list(layer.nodes), 'file': layer.file_path} 
                      for lid, layer in self.layers.items()},
            'violations': [
                {
                    'source': v.source_node,
                    'target': v.target_node,
                    'file': v.source_file,
                    'line': v.line_number,
                    'content': v.line_content
                }
                for v in self.violations
            ]
        }

def main():
    """メイン実行"""
    if len(sys.argv) < 2:
        print("使用法: python analyze_horizontal_references.py <root_directory>")
        print("例: python analyze_horizontal_references.py src/pkg/memo_logic")
        sys.exit(1)
    
    root_dir = sys.argv[1]
    analyzer = HorizontalReferenceAnalyzer(root_dir)
    report = analyzer.analyze()
    
    print("\n" + "="*60)
    print("📊 PKG横参照分析結果")
    print("="*60)
    print(f"発見された階層数: {report['layers_found']}")
    print(f"総ノード数: {report['nodes_total']}")
    print(f"総参照数: {report['references_total']}")
    print(f"横参照違反数: {report['violations_found']}")
    
    if report['violations_found'] > 0:
        print("\n🚨 修正が必要な横参照違反:")
        for violation in report['violations']:
            print(f"  {violation['source']} → {violation['target']}")
            print(f"    場所: {violation['file']}:{violation['line']}")
            print(f"    内容: {violation['content']}")
            print()
    
    print("\n📋 階層別ノード分布:")
    for layer_id in sorted(report['layers'].keys()):
        layer = report['layers'][layer_id]
        print(f"  階層{layer_id}: {len(layer['nodes'])}個のノード")
        for node in sorted(layer['nodes'])[:5]:  # 最初の5個のみ表示
            print(f"    - {node}")
        if len(layer['nodes']) > 5:
            print(f"    ... 他{len(layer['nodes']) - 5}個")
    
    print(f"\n✅ 分析完了。詳細はコードを確認してください。")

if __name__ == "__main__":
    main()