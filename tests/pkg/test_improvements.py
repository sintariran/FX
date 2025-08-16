#!/usr/bin/env python3
"""
アーキテクチャレビュー改善提案の実装テスト
"""

import sys
import os
from pathlib import Path

# テスト対象のモジュールをインポート
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_dag_config_hierarchy_validation():
    """DAGConfigManagerの階層検証機能テスト"""
    print("🔍 DAGConfigManager階層検証テスト...")
    
    try:
        from src.pkg.feature_dag.dag_config_manager import DAGConfigManager, NodeDefinition
        
        # 正常なDAG構造
        manager = DAGConfigManager()
        
        # ノードを手動で追加
        manager.nodes['391^0-001'] = NodeDefinition(
            node_id='391^0-001',
            layer=0,
            function='collect_data',
            inputs=[],
            outputs={},
            description='Data collection'
        )
        
        manager.nodes['391^1-001'] = NodeDefinition(
            node_id='391^1-001',
            layer=1,
            function='process_data',
            inputs=['391^0-001'],  # 下位階層を参照（正常）
            outputs={},
            description='Data processing'
        )
        
        # 階層検証（正常なケース）
        try:
            manager._validate_hierarchy()
            print("✅ 正常な階層構造の検証成功")
        except ValueError:
            print("❌ 正常な構造で検証エラー")
            return False
        
        # 横参照を含む不正なノードを追加
        manager.nodes['391^1-002'] = NodeDefinition(
            node_id='391^1-002',
            layer=1,
            function='invalid_ref',
            inputs=['391^1-001'],  # 同階層を参照（違反）
            outputs={},
            description='Invalid reference'
        )
        
        # 階層検証（違反検出）
        try:
            manager._validate_hierarchy()
            print("❌ 横参照違反が検出されませんでした")
            return False
        except ValueError as e:
            if "Horizontal reference violation" in str(e):
                print("✅ 横参照違反を正しく検出")
                return True
            else:
                print(f"❌ 予期しないエラー: {e}")
                return False
        
    except Exception as e:
        print(f"❌ DAGConfigManager検証エラー: {e}")
        return False

def test_node_id_generator():
    """NodeIDGenerator自動採番テスト"""
    print("🔍 NodeIDGenerator自動採番テスト...")
    
    try:
        from src.pkg.utils.node_id_generator import NodeIDGenerator
        
        # ジェネレータ初期化（15分足、USDJPY）
        generator = NodeIDGenerator(timeframe="3", period="9", currency="1")
        
        # ID生成テスト
        id1 = generator.generate(layer=0)
        if id1 != "391^0-001":
            print(f"❌ 初回生成IDが不正: {id1}")
            return False
        
        id2 = generator.generate(layer=0)
        if id2 != "391^0-002":
            print(f"❌ 連番がインクリメントされません: {id2}")
            return False
        
        # 別階層のID生成
        id3 = generator.generate(layer=1)
        if id3 != "391^1-001":
            print(f"❌ 階層別カウンタが機能していません: {id3}")
            return False
        
        # 一括生成テスト
        bulk_ids = generator.bulk_generate(layer=2, count=3)
        expected = ["391^2-001", "391^2-002", "391^2-003"]
        if bulk_ids != expected:
            print(f"❌ 一括生成が不正: {bulk_ids}")
            return False
        
        # 統計情報取得
        stats = generator.get_statistics()
        if stats['total_reserved'] != 6:  # 6個のIDを生成済み
            print(f"❌ 予約数カウントが不正: {stats['total_reserved']}")
            return False
        
        print("✅ NodeIDGenerator自動採番テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ NodeIDGeneratorエラー: {e}")
        return False

def test_multi_timeframe_id_manager():
    """複数時間足ID管理テスト"""
    print("🔍 複数時間足ID管理テスト...")
    
    try:
        from src.pkg.utils.node_id_generator import MultiTimeframeIDManager
        
        # マネージャー初期化
        manager = MultiTimeframeIDManager(period="9")
        
        # 異なる時間足でID生成
        m1_id = manager.generate_id("M1", "USDJPY", layer=20)
        if not m1_id.startswith("191^20"):
            print(f"❌ M1のID形式が不正: {m1_id}")
            return False
        
        m15_id = manager.generate_id("M15", "USDJPY", layer=40)
        if not m15_id.startswith("391^40"):
            print(f"❌ M15のID形式が不正: {m15_id}")
            return False
        
        h1_id = manager.generate_id("H1", "EURUSD", layer=50)
        if not h1_id.startswith("592^50"):  # 5=H1, 9=共通, 2=EURUSD
            print(f"❌ H1 EURUSDのID形式が不正: {h1_id}")
            return False
        
        # 統計情報確認
        stats = manager.get_all_statistics()
        if len(stats) != 3:  # 3つのジェネレータが作成されているはず
            print(f"❌ ジェネレータ数が不正: {len(stats)}")
            return False
        
        print("✅ 複数時間足ID管理テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ 複数時間足ID管理エラー: {e}")
        return False

def test_id_format_validation():
    """ID形式検証の強化テスト"""
    print("🔍 ID形式検証の強化テスト...")
    
    try:
        from src.pkg.feature_dag.dag_config_manager import NodeDefinition
        
        # 正常なID
        try:
            node = NodeDefinition(
                node_id='391^3-001',
                layer=3,
                function='test',
                inputs=[],
                outputs={},
                description='Test'
            )
            print("✅ 正常なID形式を受け入れ")
        except ValueError:
            print("❌ 正常なIDが拒否されました")
            return False
        
        # ID-階層不一致
        try:
            node = NodeDefinition(
                node_id='391^3-001',
                layer=2,  # IDは階層3だが実際は階層2（不一致）
                function='test',
                inputs=[],
                outputs={},
                description='Test'
            )
            print("❌ ID-階層不一致が検出されませんでした")
            return False
        except ValueError as e:
            if "Layer mismatch" in str(e):
                print("✅ ID-階層不一致を正しく検出")
            else:
                print(f"❌ 予期しないエラー: {e}")
                return False
        
        # 不正な形式
        invalid_ids = [
            '39^1-001',    # プレフィックス3桁未満
            '391^1-1',     # 連番3桁未満
            '3911-001',    # ^なし
            '391-1-001',   # 形式違反
        ]
        
        for invalid_id in invalid_ids:
            try:
                node = NodeDefinition(
                    node_id=invalid_id,
                    layer=1,
                    function='test',
                    inputs=[],
                    outputs={},
                    description='Test'
                )
                print(f"❌ 不正なID形式が受け入れられました: {invalid_id}")
                return False
            except ValueError:
                pass  # 期待通りエラー
        
        print("✅ ID形式検証の強化テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ ID形式検証エラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("="*80)
    print("🧪 アーキテクチャ改善提案実装テスト")
    print("="*80)
    
    tests = [
        test_dag_config_hierarchy_validation,
        test_node_id_generator,
        test_multi_timeframe_id_manager,
        test_id_format_validation
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
        print("🎉 すべての改善実装が正常に動作しています！")
        return True
    else:
        print("⚠️  一部の改善実装に問題があります。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)