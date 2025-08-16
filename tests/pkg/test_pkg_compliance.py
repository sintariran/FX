"""
PKG準拠性テスト
DAGアーキテクチャのルール遵守を検証
"""

import pytest
import re
import sys
import os
from pathlib import Path
from typing import Dict, List, Set

# テスト対象のモジュールをインポート
sys.path.append(str(Path(__file__).parent.parent.parent))

class TestPKGCompliance:
    """PKG準拠性テストスイート"""
    
    @pytest.fixture
    def pkg_nodes(self):
        """テスト用のPKGノード定義"""
        return {
            "391^0-001": {"layer": 0, "deps": []},
            "391^1-001": {"layer": 1, "deps": ["391^0-001"]},
            "391^1-002": {"layer": 1, "deps": ["391^0-002"]},
            "391^2-001": {"layer": 2, "deps": ["391^1-001", "391^1-002"]},
            "391^2-002": {"layer": 2, "deps": ["391^1-001"]},
            "391^3-001": {"layer": 3, "deps": ["391^2-001", "391^2-002"]}
        }
    
    def test_no_horizontal_references(self, pkg_nodes):
        """横参照がないことを確認"""
        violations = []
        
        for node_id, node_info in pkg_nodes.items():
            node_layer = node_info["layer"]
            
            for dep in node_info["deps"]:
                dep_layer = pkg_nodes[dep]["layer"]
                
                if dep_layer == node_layer:
                    violations.append(f"横参照違反: {node_id} → {dep} (同一階層{node_layer})")
                elif dep_layer > node_layer:
                    violations.append(f"逆参照違反: {node_id} → {dep} (上位階層参照)")
        
        assert len(violations) == 0, f"階層参照違反が発見されました: {violations}"
    
    def test_pkg_id_format(self, pkg_nodes):
        """PKG ID形式の正しさを確認"""
        pkg_pattern = re.compile(r'^\d\d\d\^\d+-\d+$')
        
        for node_id in pkg_nodes.keys():
            assert pkg_pattern.match(node_id), f"不正なPKG ID形式: {node_id}"
    
    def test_layer_progression(self, pkg_nodes):
        """階層の連続性を確認"""
        layers = set(node["layer"] for node in pkg_nodes.values())
        sorted_layers = sorted(layers)
        
        # 階層0から始まることを確認
        assert sorted_layers[0] == 0, "階層は0から始まる必要があります"
        
        # 階層が連続していることを確認（飛び階層は許可）
        max_layer = max(sorted_layers)
        assert max_layer >= 0, "階層は0以上である必要があります"
    
    def test_dependency_direction(self, pkg_nodes):
        """依存関係の方向性を確認"""
        for node_id, node_info in pkg_nodes.items():
            node_layer = node_info["layer"]
            
            for dep in node_info["deps"]:
                dep_layer = pkg_nodes[dep]["layer"]
                
                # 下位階層のみ参照可能
                assert dep_layer < node_layer, \
                    f"不正な依存関係: {node_id}(層{node_layer}) → {dep}(層{dep_layer})"
    
    def test_no_circular_dependencies(self, pkg_nodes):
        """循環依存がないことを確認"""
        def has_cycle(node_id: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for dep in pkg_nodes[node_id]["deps"]:
                if dep not in visited:
                    if has_cycle(dep, visited, rec_stack):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        visited = set()
        for node_id in pkg_nodes:
            if node_id not in visited:
                assert not has_cycle(node_id, visited, set()), \
                    f"循環依存が検出されました: {node_id}"

class TestPerformance:
    """パフォーマンステスト"""
    
    def test_response_time_under_30ms(self):
        """30ms以内の応答時間を確認"""
        import time
        from src.pkg.feature_dag.data_collection import create_sample_tick, DataCollectionLayer
        
        # テストデータ作成
        collector = DataCollectionLayer("USDJPY")
        tick = create_sample_tick()
        
        # 実行時間測定
        start_time = time.time()
        result = collector.collect_current_price(tick)
        execution_time = (time.time() - start_time) * 1000
        
        assert execution_time < 30, f"応答時間が30msを超過: {execution_time:.2f}ms"
        assert result is not None, "結果が返されませんでした"

class TestDataIntegrity:
    """データ整合性テスト"""
    
    def test_data_collection_integrity(self):
        """データ収集の整合性を確認"""
        from src.pkg.feature_dag.data_collection import DataCollectionLayer, create_sample_tick
        
        collector = DataCollectionLayer("USDJPY")
        tick = create_sample_tick()
        result = collector.collect_current_price(tick)
        
        # データ整合性の検証
        assert collector.validate_data_integrity(result), "データ整合性チェックに失敗"
        
        # PKG IDの存在確認
        pkg_id_pattern = re.compile(r'^\d\d\d\^0-\d{3}$')
        pkg_ids = [key for key in result.keys() if pkg_id_pattern.match(key)]
        assert len(pkg_ids) > 0, "有効なPKG IDが見つかりません"
    
    def test_quality_score_validation(self):
        """品質スコアの妥当性を確認"""
        from src.pkg.feature_dag.data_collection import DataCollectionLayer, MarketTick
        from datetime import datetime
        
        collector = DataCollectionLayer("USDJPY")
        
        # 正常なティック
        good_tick = MarketTick(
            timestamp=datetime.now(),
            symbol="USDJPY",
            bid=110.0,
            ask=110.003,
            volume=1000.0
        )
        
        quality = collector._assess_data_quality(good_tick)
        assert 0.0 <= quality <= 1.0, f"品質スコアが範囲外: {quality}"
        assert quality > 0.8, "正常データの品質スコアが低すぎます"
        
        # 異常なティック（大きなスプレッド）
        bad_tick = MarketTick(
            timestamp=datetime.now(),
            symbol="USDJPY", 
            bid=110.0,
            ask=111.0,  # 1円のスプレッド（異常）
            volume=1000.0
        )
        
        bad_quality = collector._assess_data_quality(bad_tick)
        assert bad_quality < quality, "異常データの品質スコアが適切に下がっていません"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])