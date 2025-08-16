#!/usr/bin/env python3
"""
Feature DAG Phase 2 テストスイート
データ駆動ノード定義と自動評価順序決定のテスト
"""

import sys
import os
import time
import tempfile
from pathlib import Path
from datetime import datetime
import yaml
import numpy as np

# テスト対象のモジュールをインポート
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_yaml_config_loading():
    """YAML設定ファイルの読み込みテスト"""
    print("🔍 YAML設定読み込みテスト...")
    
    try:
        from src.pkg.feature_dag.dag_config_manager import DAGConfigManager
        
        # デフォルト設定ファイルで初期化
        config_manager = DAGConfigManager()
        config_manager.load_configuration()
        
        # ノード数確認
        node_count = len(config_manager.nodes)
        if node_count == 0:
            print("❌ ノードが読み込まれていません")
            return False
        
        # PKG ID形式確認
        for node_id in config_manager.nodes.keys():
            import re
            if not re.match(r'^\d{3}\^\d+-\d{3}$', node_id):
                print(f"❌ 不正なPKG ID形式: {node_id}")
                return False
        
        print(f"✅ YAML設定読み込みテスト合格 ({node_count}個のノード)")
        return True
        
    except Exception as e:
        print(f"❌ YAML設定読み込みエラー: {e}")
        return False

def test_topological_sort():
    """トポロジカルソートテスト"""
    print("🔍 トポロジカルソートテスト...")
    
    try:
        from src.pkg.feature_dag.dag_config_manager import DAGConfigManager
        
        config_manager = DAGConfigManager()
        config_manager.load_configuration()
        
        # 実行順序を取得
        execution_order = config_manager.get_execution_order()
        
        if not execution_order:
            print("❌ 実行順序が生成されていません")
            return False
        
        # 依存関係の検証
        processed_nodes = set()
        for node_id in execution_order:
            node_def = config_manager.get_node_definition(node_id)
            
            # すべての依存ノードが先に処理されているかチェック
            for dep_id in node_def.inputs:
                if dep_id in config_manager.nodes and dep_id not in processed_nodes:
                    print(f"❌ 依存関係違反: {node_id} は {dep_id} より先に処理されています")
                    return False
            
            processed_nodes.add(node_id)
        
        print(f"✅ トポロジカルソートテスト合格 ({len(execution_order)}個のノード)")
        return True
        
    except Exception as e:
        print(f"❌ トポロジカルソートエラー: {e}")
        return False

def test_feature_extraction_integration():
    """特徴量抽出統合テスト"""
    print("🔍 特徴量抽出統合テスト...")
    
    try:
        from src.pkg.feature_dag.feature_extraction import FeatureExtractionLayer, MarketData
        
        # 特徴量抽出層を初期化
        extractor = FeatureExtractionLayer("USDJPY")
        
        # テストデータ作成
        test_data = MarketData(
            timestamp=datetime.now(),
            symbol="USDJPY",
            bid=110.0,
            ask=110.003,
            volume=1000.0,
            spread=0.003
        )
        
        # 複数回データを処理してヒストリーを構築
        for i in range(5):
            test_data.bid += 0.001 * (i - 2)  # 価格変動
            test_data.ask += 0.001 * (i - 2)
            result = extractor.process_market_data(test_data)
        
        # 結果検証
        if not result:
            print("❌ 結果が返されませんでした")
            return False
        
        # 階層別の結果確認
        layers_found = set()
        for node_id in result.keys():
            if '^' in node_id:
                layer = int(node_id.split('^')[1].split('-')[0])
                layers_found.add(layer)
        
        if len(layers_found) == 0:
            print("❌ PKGノードの結果が見つかりません")
            return False
        
        print(f"✅ 特徴量抽出統合テスト合格 (階層{sorted(layers_found)})")
        return True
        
    except Exception as e:
        print(f"❌ 特徴量抽出統合エラー: {e}")
        return False

def test_export_contract():
    """エクスポート契約テスト"""
    print("🔍 エクスポート契約テスト...")
    
    try:
        from src.pkg.feature_dag.export_contract import StandardFeatureExporter
        from src.pkg.feature_dag.feature_extraction import FeatureExtractionLayer, MarketData
        
        # データ生成
        extractor = FeatureExtractionLayer("USDJPY")
        test_data = MarketData(
            timestamp=datetime.now(),
            symbol="USDJPY", 
            bid=110.0,
            ask=110.003,
            volume=1000.0,
            spread=0.003
        )
        
        raw_features = extractor.process_market_data(test_data)
        
        # エクスポーター初期化
        exporter = StandardFeatureExporter("USDJPY", "M1")
        
        # エクスポート実行
        bundle = exporter.export_features(raw_features)
        
        # 結果検証
        if not bundle.features:
            print("❌ エクスポートされた特徴量がありません")
            return False
        
        # 妥当性検証
        is_valid, errors = exporter.validate_export(bundle)
        if not is_valid:
            print(f"❌ エクスポート妥当性エラー: {errors}")
            return False
        
        # 品質チェック
        if bundle.quality_summary.get("overall_quality", 0) < 0.3:
            print(f"❌ 品質が低すぎます: {bundle.quality_summary.get('overall_quality')}")
            return False
        
        print(f"✅ エクスポート契約テスト合格 ({len(bundle.features)}個の特徴量)")
        return True
        
    except Exception as e:
        print(f"❌ エクスポート契約エラー: {e}")
        return False

def test_performance_requirements():
    """パフォーマンス要件テスト"""
    print("🔍 パフォーマンス要件テスト（30ms以内）...")
    
    try:
        from src.pkg.feature_dag.feature_extraction import FeatureExtractionLayer, MarketData
        
        extractor = FeatureExtractionLayer("USDJPY")
        test_data = MarketData(
            timestamp=datetime.now(),
            symbol="USDJPY",
            bid=110.0,
            ask=110.003,
            volume=1000.0,
            spread=0.003
        )
        
        # ウォームアップ
        extractor.process_market_data(test_data)
        
        # パフォーマンス測定
        start_time = time.time()
        result = extractor.process_market_data(test_data)
        execution_time = (time.time() - start_time) * 1000
        
        if execution_time > 30:
            print(f"❌ 実行時間が30msを超過: {execution_time:.2f}ms")
            return False
        
        if not result:
            print("❌ 結果が返されませんでした")
            return False
        
        print(f"✅ パフォーマンス要件テスト合格: {execution_time:.2f}ms")
        return True
        
    except Exception as e:
        print(f"❌ パフォーマンス要件エラー: {e}")
        return False

def test_ai_agent_parameterization():
    """AI エージェント用パラメータ化テスト"""
    print("🔍 AI エージェント用パラメータ化テスト...")
    
    try:
        from src.pkg.feature_dag.dag_config_manager import DAGConfigManager
        
        config_manager = DAGConfigManager()
        config_manager.load_configuration()
        
        # AI探索設定の取得
        ai_config = config_manager.get_ai_exploration_config()
        
        if not ai_config:
            print("❌ AI探索設定が見つかりません")
            return False
        
        # 探索パラメータの確認
        exploration_params = ai_config.get('exploration_parameters', [])
        if not exploration_params:
            print("❌ 探索パラメータが設定されていません")
            return False
        
        # パラメータ更新テスト
        test_node_id = list(config_manager.nodes.keys())[0]
        new_params = {"test_param": 0.5}
        
        config_manager.update_node_parameters(test_node_id, new_params)
        
        # 更新確認
        updated_node = config_manager.get_node_definition(test_node_id)
        if "test_param" not in updated_node.parameters:
            print("❌ パラメータ更新が反映されていません")
            return False
        
        print(f"✅ AI エージェント用パラメータ化テスト合格 ({len(exploration_params)}個のパラメータ)")
        return True
        
    except Exception as e:
        print(f"❌ AI エージェント用パラメータ化エラー: {e}")
        return False

def test_horizontal_reference_prevention():
    """横参照防止テスト"""
    print("🔍 横参照防止テスト...")
    
    try:
        from src.pkg.feature_dag.dag_config_manager import DAGConfigManager
        
        config_manager = DAGConfigManager()
        config_manager.load_configuration()
        
        # 依存関係の妥当性検証
        is_valid, errors = config_manager.validate_dependencies()
        
        if not is_valid:
            print(f"❌ 依存関係エラー: {errors}")
            return False
        
        # 特に横参照がないことを確認
        for node_id, node in config_manager.nodes.items():
            for input_id in node.inputs:
                if input_id in config_manager.nodes:
                    input_layer = config_manager.nodes[input_id].layer
                    if input_layer >= node.layer:
                        print(f"❌ 横参照違反: {node_id}(層{node.layer}) → {input_id}(層{input_layer})")
                        return False
        
        print("✅ 横参照防止テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ 横参照防止エラー: {e}")
        return False

def test_custom_yaml_config():
    """カスタムYAML設定テスト"""
    print("🔍 カスタムYAML設定テスト...")
    
    try:
        from src.pkg.feature_dag.dag_config_manager import DAGConfigManager
        
        # テスト用のYAML設定を作成
        test_config = {
            "version": "1.0",
            "description": "Test configuration",
            "data_collection": [
                {
                    "id": "291^0-001",
                    "layer": 0,
                    "function": "test_function",
                    "inputs": [],
                    "outputs": {"test_output": "float"},
                    "parameters": {"test_param": 1.0}
                }
            ],
            "basic_indicators": [
                {
                    "id": "291^1-001", 
                    "layer": 1,
                    "function": "test_function_2",
                    "inputs": ["291^0-001"],
                    "outputs": {"test_output2": "float"},
                    "parameters": {"test_param2": 2.0}
                }
            ]
        }
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name
        
        try:
            # カスタム設定で初期化
            config_manager = DAGConfigManager(temp_path)
            config_manager.load_configuration()
            
            # ノード数確認
            if len(config_manager.nodes) != 2:
                print(f"❌ 期待されるノード数: 2, 実際: {len(config_manager.nodes)}")
                return False
            
            # 実行順序確認
            execution_order = config_manager.get_execution_order()
            if execution_order != ["291^0-001", "291^1-001"]:
                print(f"❌ 期待される実行順序と異なります: {execution_order}")
                return False
            
            print("✅ カスタムYAML設定テスト合格")
            return True
            
        finally:
            # 一時ファイル削除
            os.unlink(temp_path)
        
    except Exception as e:
        print(f"❌ カスタムYAML設定エラー: {e}")
        return False

def test_versioned_export_manager():
    """バージョン管理付きエクスポートマネージャーテスト"""
    print("🔍 バージョン管理付きエクスポートマネージャーテスト...")
    
    try:
        from src.pkg.feature_dag.export_contract import VersionedExportManager, StandardFeatureExporter
        
        manager = VersionedExportManager()
        
        # 複数バージョンのエクスポーターを登録
        exporter_v1 = StandardFeatureExporter("USDJPY", "M1")
        exporter_v2 = StandardFeatureExporter("USDJPY", "M5")
        
        manager.register_exporter("1.0", exporter_v1)
        manager.register_exporter("2.0", exporter_v2)
        
        # バージョン一覧確認
        versions = manager.list_versions()
        if versions != ["1.0", "2.0"]:
            print(f"❌ バージョン一覧が期待と異なります: {versions}")
            return False
        
        # 最新バージョン確認
        latest = manager.get_latest_version()
        if latest != "2.0":
            print(f"❌ 最新バージョンが期待と異なります: {latest}")
            return False
        
        # 指定バージョンのエクスポーター取得
        exporter = manager.get_exporter("1.0")
        if exporter.timeframe != "M1":
            print(f"❌ 取得したエクスポーターが期待と異なります")
            return False
        
        print("✅ バージョン管理付きエクスポートマネージャーテスト合格")
        return True
        
    except Exception as e:
        print(f"❌ バージョン管理付きエクスポートマネージャーエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("="*80)
    print("🧪 Feature DAG Phase 2 テストスイート")
    print("="*80)
    
    tests = [
        test_yaml_config_loading,
        test_topological_sort,
        test_horizontal_reference_prevention,
        test_feature_extraction_integration,
        test_export_contract,
        test_performance_requirements,
        test_ai_agent_parameterization,
        test_custom_yaml_config,
        test_versioned_export_manager
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ テスト実行エラー in {test_func.__name__}: {e}")
            failed += 1
        print()
    
    print("="*80)
    print(f"📊 テスト結果: ✅ {passed}個合格, ❌ {failed}個失敗")
    print("="*80)
    
    if failed == 0:
        print("🎉 すべてのテストが合格しました！Phase 2 実装完了です。")
        return True
    else:
        print("⚠️  一部のテストが失敗しました。修正が必要です。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)