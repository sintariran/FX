#!/usr/bin/env python3
"""
Feature DAG Phase 2 簡易テストスイート
PyYAML不要バージョン
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime

# テスト対象のモジュールをインポート
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_feature_extraction_basic():
    """基本的な特徴量抽出テスト"""
    print("🔍 基本特徴量抽出テスト...")
    
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
        
        # データ処理
        result = extractor.process_market_data(test_data)
        
        # 結果検証
        if not result:
            print("❌ 結果が返されませんでした")
            return False
        
        print("✅ 基本特徴量抽出テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ 基本特徴量抽出エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_manager_without_yaml():
    """YAML不要でのコンフィグマネージャーテスト"""
    print("🔍 設定管理テスト（YAML不要）...")
    
    try:
        from src.pkg.feature_dag.dag_config_manager import DAGConfigManager, NodeDefinition
        
        # 設定管理を初期化（YAML無しでテスト）
        config_manager = DAGConfigManager()
        
        # 手動でテストノードを追加
        test_nodes = {
            "391^0-001": NodeDefinition(
                id="391^0-001",
                layer=0,
                function="test_function",
                inputs=[],
                outputs={"output": "float"},
                parameters={"param": 1.0}
            ),
            "391^1-001": NodeDefinition(
                id="391^1-001", 
                layer=1,
                function="test_function_2",
                inputs=["391^0-001"],
                outputs={"output2": "float"},
                parameters={"param2": 2.0}
            )
        }
        
        config_manager.nodes = test_nodes
        config_manager._build_dag_structure()
        
        # 実行順序テスト
        execution_order = config_manager.get_execution_order()
        expected_order = ["391^0-001", "391^1-001"]
        
        if execution_order != expected_order:
            print(f"❌ 実行順序が期待と異なります: {execution_order}")
            return False
        
        # 依存関係検証
        is_valid, errors = config_manager.validate_dependencies()
        if not is_valid:
            print(f"❌ 依存関係エラー: {errors}")
            return False
        
        print("✅ 設定管理テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ 設定管理エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_export_contract_basic():
    """基本エクスポート契約テスト"""
    print("🔍 基本エクスポート契約テスト...")
    
    try:
        from src.pkg.feature_dag.export_contract import StandardFeatureExporter
        
        # テスト用の生データ
        raw_features = {
            "391^1-001": {
                "price_change": 0.001,
                "price_change_pct": 0.0001,
                "price_momentum": 0.0005
            },
            "391^2-001": {
                "unified_signal": 0.7,
                "signal_strength": 0.8
            }
        }
        
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
        
        print(f"✅ 基本エクスポート契約テスト合格 ({len(bundle.features)}個の特徴量)")
        return True
        
    except Exception as e:
        print(f"❌ 基本エクスポート契約エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_basic():
    """基本パフォーマンステスト"""
    print("🔍 基本パフォーマンステスト（30ms以内）...")
    
    try:
        from src.pkg.feature_dag.data_collection import DataCollectionLayer, create_sample_tick
        
        collector = DataCollectionLayer("USDJPY")
        tick = create_sample_tick()
        
        # パフォーマンス測定
        start_time = time.time()
        result = collector.collect_current_price(tick)
        execution_time = (time.time() - start_time) * 1000
        
        if execution_time > 30:
            print(f"❌ 実行時間が30msを超過: {execution_time:.2f}ms")
            return False
        
        if not result:
            print("❌ 結果が返されませんでした")
            return False
        
        print(f"✅ 基本パフォーマンステスト合格: {execution_time:.2f}ms")
        return True
        
    except Exception as e:
        print(f"❌ 基本パフォーマンスエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pkg_id_validation():
    """PKG ID形式検証テスト"""
    print("🔍 PKG ID形式検証テスト...")
    
    try:
        from src.pkg.feature_dag.dag_config_manager import NodeDefinition
        
        # 正常なPKG ID
        valid_ids = ["391^0-001", "291^1-002", "191^2-126"]
        for pkg_id in valid_ids:
            try:
                node = NodeDefinition(
                    id=pkg_id,
                    layer=0,
                    function="test",
                    inputs=[],
                    outputs={},
                    parameters={}
                )
                # 正常に作成できればOK
            except ValueError:
                print(f"❌ 正常なPKG ID {pkg_id} が無効と判定されました")
                return False
        
        # 異常なPKG ID
        invalid_ids = ["invalid", "39^1-001", "3911-001", "391-001"]
        for pkg_id in invalid_ids:
            try:
                node = NodeDefinition(
                    id=pkg_id,
                    layer=0,
                    function="test",
                    inputs=[],
                    outputs={},
                    parameters={}
                )
                print(f"❌ 異常なPKG ID {pkg_id} が有効と判定されました")
                return False
            except ValueError:
                # 正常にエラーになればOK
                pass
        
        print("✅ PKG ID形式検証テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ PKG ID形式検証エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_collection_quality():
    """データ収集品質テスト"""
    print("🔍 データ収集品質テスト...")
    
    try:
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
        if quality < 0.8:
            print(f"❌ 正常データの品質スコアが低すぎます: {quality}")
            return False
        
        # 異常なティック（大きなスプレッド）
        bad_tick = MarketTick(
            timestamp=datetime.now(),
            symbol="USDJPY", 
            bid=110.0,
            ask=111.0,  # 1円のスプレッド（異常）
            volume=1000.0
        )
        
        bad_quality = collector._assess_data_quality(bad_tick)
        if bad_quality >= quality:
            print(f"❌ 異常データの品質スコアが適切に下がっていません: {bad_quality} >= {quality}")
            return False
        
        print(f"✅ データ収集品質テスト合格 (正常: {quality:.2f}, 異常: {bad_quality:.2f})")
        return True
        
    except Exception as e:
        print(f"❌ データ収集品質エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_directory_structure():
    """ディレクトリ構造テスト"""
    print("🔍 ディレクトリ構造テスト...")
    
    try:
        required_files = [
            "src/pkg/feature_dag/__init__.py",
            "src/pkg/feature_dag/data_collection.py",
            "src/pkg/feature_dag/feature_extraction.py",
            "src/pkg/feature_dag/dag_config_manager.py",
            "src/pkg/feature_dag/export_contract.py",
            "src/pkg/feature_dag/node_definitions.yaml"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ 不足ファイル: {missing_files}")
            return False
        
        print("✅ ディレクトリ構造テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ ディレクトリ構造エラー: {e}")
        return False

def test_imports():
    """インポートテスト"""
    print("🔍 インポートテスト...")
    
    try:
        # メインパッケージのインポート
        from src.pkg.feature_dag import (
            DataCollectionLayer, FeatureExtractionLayer, DAGConfigManager,
            StandardFeatureExporter, FeatureBundle
        )
        
        print("✅ インポートテスト合格")
        return True
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ インポートエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("="*80)
    print("🧪 Feature DAG Phase 2 簡易テストスイート")
    print("="*80)
    
    tests = [
        test_directory_structure,
        test_imports,
        test_pkg_id_validation,
        test_config_manager_without_yaml,
        test_data_collection_quality,
        test_feature_extraction_basic,
        test_export_contract_basic,
        test_performance_basic
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