#!/usr/bin/env python3
"""
簡易PKG準拠テスト（pytest不要）
"""

import sys
import os
import re
import time
from pathlib import Path

# テスト対象のモジュールをインポート
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_no_horizontal_references():
    """横参照がないことを確認"""
    print("🔍 横参照テスト...")
    
    pkg_nodes = {
        "391^0-001": {"layer": 0, "deps": []},
        "391^1-001": {"layer": 1, "deps": ["391^0-001"]},
        "391^1-002": {"layer": 1, "deps": ["391^0-002"]},
        "391^2-001": {"layer": 2, "deps": ["391^1-001", "391^1-002"]},
        "391^2-002": {"layer": 2, "deps": ["391^1-001"]},
        "391^3-001": {"layer": 3, "deps": ["391^2-001", "391^2-002"]}
    }
    
    violations = []
    
    for node_id, node_info in pkg_nodes.items():
        node_layer = node_info["layer"]
        
        for dep in node_info["deps"]:
            if dep in pkg_nodes:
                dep_layer = pkg_nodes[dep]["layer"]
                
                if dep_layer == node_layer:
                    violations.append(f"横参照違反: {node_id} → {dep} (同一階層{node_layer})")
                elif dep_layer > node_layer:
                    violations.append(f"逆参照違反: {node_id} → {dep} (上位階層参照)")
    
    if violations:
        print(f"❌ 階層参照違反が発見されました: {violations}")
        return False
    else:
        print("✅ 横参照テスト合格")
        return True

def test_pkg_id_format():
    """PKG ID形式の正しさを確認"""
    print("🔍 PKG ID形式テスト...")
    
    test_ids = [
        "391^0-001",  # 正常
        "291^1-002",  # 正常
        "191^2-126",  # 正常
        "invalid",    # 異常
        "39^1-001",   # 異常（短い）
        "3911-001"    # 異常（^なし）
    ]
    
    pkg_pattern = re.compile(r'^\d\d\d\^\d+-\d+$')
    failures = []
    
    for test_id in test_ids:
        if test_id in ["invalid", "39^1-001", "3911-001"]:
            # 異常系（失敗すべき）
            if pkg_pattern.match(test_id):
                failures.append(f"異常ID {test_id} が正常と判定された")
        else:
            # 正常系（成功すべき）
            if not pkg_pattern.match(test_id):
                failures.append(f"正常ID {test_id} が異常と判定された")
    
    if failures:
        print(f"❌ PKG ID形式テスト失敗: {failures}")
        return False
    else:
        print("✅ PKG ID形式テスト合格")
        return True

def test_data_collection():
    """データ収集テスト"""
    print("🔍 データ収集テスト...")
    
    try:
        from src.pkg.feature_dag.data_collection import DataCollectionLayer, create_sample_tick
        
        collector = DataCollectionLayer("USDJPY")
        tick = create_sample_tick()
        result = collector.collect_current_price(tick)
        
        # 基本的なチェック
        if not result:
            print("❌ 結果が空です")
            return False
        
        if "timestamp" not in result:
            print("❌ timestampが含まれていません")
            return False
        
        # PKG IDの存在確認
        pkg_pattern = re.compile(r'^\d\d\d\^0-\d{3}$')
        pkg_ids = [key for key in result.keys() if pkg_pattern.match(key)]
        
        if not pkg_ids:
            print("❌ 有効なPKG IDが見つかりません")
            return False
        
        print(f"✅ データ収集テスト合格（PKG ID: {pkg_ids[0]}）")
        return True
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ データ収集テストエラー: {e}")
        return False

def test_response_time():
    """応答時間テスト"""
    print("🔍 応答時間テスト（30ms以内）...")
    
    try:
        from src.pkg.feature_dag.data_collection import DataCollectionLayer, create_sample_tick
        
        collector = DataCollectionLayer("USDJPY")
        tick = create_sample_tick()
        
        # 実行時間測定
        start_time = time.time()
        result = collector.collect_current_price(tick)
        execution_time = (time.time() - start_time) * 1000
        
        if execution_time > 30:
            print(f"❌ 応答時間が30msを超過: {execution_time:.2f}ms")
            return False
        
        print(f"✅ 応答時間テスト合格: {execution_time:.2f}ms")
        return True
        
    except Exception as e:
        print(f"❌ 応答時間テストエラー: {e}")
        return False

def test_directory_structure():
    """ディレクトリ構造テスト"""
    print("🔍 ディレクトリ構造テスト...")
    
    required_dirs = [
        "src/pkg/feature_dag",
        "src/pkg/decision_dag",
        "src/pkg/financial_dag", 
        "src/pkg/trading_dag",
        "tests/pkg"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"❌ 不足ディレクトリ: {missing_dirs}")
        return False
    else:
        print("✅ ディレクトリ構造テスト合格")
        return True

def main():
    """メインテスト実行"""
    print("="*60)
    print("🧪 PKG準拠性簡易テストスイート")
    print("="*60)
    
    tests = [
        test_no_horizontal_references,
        test_pkg_id_format,
        test_directory_structure,
        test_data_collection,
        test_response_time
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
    
    print("="*60)
    print(f"📊 テスト結果: ✅ {passed}個合格, ❌ {failed}個失敗")
    print("="*60)
    
    if failed == 0:
        print("🎉 すべてのテストが合格しました！")
        return True
    else:
        print("⚠️  一部のテストが失敗しました。修正が必要です。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)