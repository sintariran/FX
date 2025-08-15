#!/usr/bin/env python3
"""
FXシステム基本動作確認（依存関係最小版）

Week 1の実装が正しく動作するかの基本確認
"""

import sys
import os

# Pythonの基本ライブラリのみを使用
print("🚀 FXシステム基本動作確認開始\n")

def test_import_modules():
    """作成したモジュールのインポートテスト"""
    print("📦 モジュールインポートテスト...")
    
    sys.path.append('./src')
    
    try:
        # 各モジュールのインポート確認
        print("   - base_indicators.py...")
        from indicators.base_indicators import BaseIndicators, PerformanceTracker
        print("     ✅ BaseIndicators, PerformanceTracker")
        
        print("   - database.py...")
        from utils.database import DatabaseManager
        print("     ✅ DatabaseManager")
        
        print("   - oanda_client.py...")
        from utils.oanda_client import OandaClient, OandaConfig
        print("     ✅ OandaClient, OandaConfig")
        
        print("   - key_concepts.py...")
        from operation_logic.key_concepts import OperationLogicEngine, Direction, TimeFrame
        print("     ✅ OperationLogicEngine, Direction, TimeFrame")
        
        return True
        
    except ImportError as e:
        print(f"     ❌ インポートエラー: {e}")
        return False

def test_core_classes():
    """コアクラスの基本動作テスト"""
    print("\n🧮 コアクラス基本動作テスト...")
    
    sys.path.append('./src')
    
    try:
        from operation_logic.key_concepts import (
            OperationLogicEngine, Direction, TimeFrame, DokyakuJudgment, 
            IkikaeriJudgment, MomiOvershootJudgment
        )
        
        # 判定エンジンの初期化テスト
        print("   - OperationLogicEngine初期化...")
        engine = OperationLogicEngine()
        print("     ✅ エンジン初期化成功")
        
        # 同逆判定テスト
        print("   - DokyakuJudgment計算...")
        dokyaku = DokyakuJudgment()
        test_data = {
            'mhih_direction': Direction.UP,
            'mjih_direction': Direction.UP,
            'mmhmh_direction': Direction.UP,
            'mmjmh_direction': Direction.DOWN,
            'mh_confirm_direction': Direction.UP
        }
        result = dokyaku.calculate(test_data)
        print(f"     ✅ 同逆判定結果: {result[0]}, 信頼度: {result[1]:.3f}")
        
        # 行帰判定テスト
        print("   - IkikaeriJudgment計算...")
        ikikaeri = IkikaeriJudgment()
        iki_data = {
            'current_heikin_direction': Direction.UP,
            'previous_heikin_direction': Direction.UP,
            'high_low_update': True
        }
        iki_result = ikikaeri.calculate(iki_data)
        print(f"     ✅ 行帰判定結果: {iki_result[0]}, 信頼度: {iki_result[1]:.3f}")
        
        # もみ・オーバーシュート判定テスト
        print("   - MomiOvershootJudgment計算...")
        momi = MomiOvershootJudgment()
        momi_data = {
            'range_width': 5.0,  # もみではない
            'os_remaining': 3.0,
            'current_timeframe_conversion': 1.0,
            'breakout_direction': Direction.UP
        }
        momi_result = momi.calculate(momi_data)
        print(f"     ✅ もみ判定結果: {momi_result[0]}, 信頼度: {momi_result[1]:.3f}")
        
        return True
        
    except Exception as e:
        print(f"     ❌ 計算エラー: {e}")
        return False

def test_database_basic():
    """データベースの基本機能テスト"""
    print("\n🗄️  データベース基本機能テスト...")
    
    sys.path.append('./src')
    
    try:
        from utils.database import DatabaseManager
        
        # データベース初期化
        print("   - データベース初期化...")
        db = DatabaseManager("./data/test_basic.db")
        print("     ✅ データベース初期化成功")
        
        # 統計情報取得
        print("   - 統計情報取得...")
        stats = db.get_database_stats()
        print(f"     ✅ 統計取得成功: {stats}")
        
        # テストファイル削除
        if os.path.exists("./data/test_basic.db"):
            os.remove("./data/test_basic.db")
            print("     ✅ テストファイル削除完了")
        
        return True
        
    except Exception as e:
        print(f"     ❌ データベースエラー: {e}")
        return False

def test_config_classes():
    """設定クラスの動作テスト"""
    print("\n⚙️  設定クラステスト...")
    
    sys.path.append('./src')
    
    try:
        from utils.oanda_client import OandaConfig
        
        # OANDA設定テスト
        print("   - OANDA設定作成...")
        config = OandaConfig(
            api_key="test_key",
            account_id="test_account",
            environment="practice"
        )
        print(f"     ✅ Base URL: {config.base_url}")
        print(f"     ✅ Stream URL: {config.stream_url}")
        
        return True
        
    except Exception as e:
        print(f"     ❌ 設定エラー: {e}")
        return False

def check_file_structure():
    """ファイル構造の確認"""
    print("\n📁 ファイル構造確認...")
    
    required_files = [
        "src/indicators/base_indicators.py",
        "src/utils/database.py", 
        "src/utils/oanda_client.py",
        "src/operation_logic/key_concepts.py",
        "docs/02-operation-logic/trading_rules_extract.md",
        "pyproject.toml"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            all_exist = False
    
    return all_exist

def main():
    """基本動作確認メイン"""
    print("=" * 60)
    
    test_results = []
    
    # 各テストの実行
    test_results.append(("ファイル構造", check_file_structure()))
    test_results.append(("モジュールインポート", test_import_modules()))
    test_results.append(("コアクラス動作", test_core_classes()))
    test_results.append(("データベース基本", test_database_basic()))
    test_results.append(("設定クラス", test_config_classes()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📋 基本動作確認結果:")
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 基本動作確認成功！")
        print("📋 Week 1 Day 1-2の実装基盤完了")
        print("📋 次段階: Week 1 Day 3-4のメモファイル徹底分析")
        
        # 次のステップのガイダンス
        print("\n📝 次のステップ:")
        print("   1. OANDA APIキーの設定（.envファイル）")
        print("   2. 実際の価格データでのテスト")
        print("   3. メモファイルロジックの詳細実装")
        print("   4. バックテストシステムの構築")
        
    else:
        print("\n⚠️  一部の基本機能に問題があります")
        print("     上記のFAILした項目を修正してください")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)