#!/usr/bin/env python3
"""
Decision DAG Phase 3 テストスイート
5つの時間足別判定DAGと統合システムのテスト
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# テスト対象のモジュールをインポート
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_m1_decision_dag():
    """M1判定DAGテスト"""
    print("🔍 M1判定DAGテスト（スキャルピング）...")
    
    try:
        from src.pkg.decision_dag import M1DecisionDAG, SignalType
        
        # M1 DAG初期化
        m1_dag = M1DecisionDAG("USDJPY")
        
        # テスト用特徴量バンドル
        test_bundle = {
            "features": {
                "USDJPY_M1_price_momentum": {"value": 0.002},  # 上昇モメンタム
                "USDJPY_M1_volume_spike": {"value": 2.5}       # ボリュームスパイク
            },
            "quality_summary": {"overall_quality": 0.8}
        }
        
        # 信号生成
        signal = m1_dag.process(test_bundle)
        
        # 結果検証
        if signal.signal_type == SignalType.NEUTRAL:
            print(f"❌ 期待される信号が生成されませんでした: {signal.signal_type}")
            return False
        
        print(f"✅ M1判定DAGテスト合格 (信号: {signal.signal_type.name}, 信頼度: {signal.confidence:.2f})")
        return True
        
    except Exception as e:
        print(f"❌ M1判定DAGエラー: {e}")
        return False

def test_m15_decision_dag():
    """M15判定DAGテスト（メモファイル核心概念）"""
    print("🔍 M15判定DAGテスト（同逆・行帰・もみ合い）...")
    
    try:
        from src.pkg.decision_dag import M15DecisionDAG, SignalType
        
        # M15 DAG初期化
        m15_dag = M15DecisionDAG("USDJPY")
        
        # テスト用特徴量バンドル（メモ概念を含む）
        test_bundle = {
            "features": {
                "USDJPY_M15_dokyaku_score": {"value": 0.8},    # 同逆スコア高
                "USDJPY_M15_ha_direction": {"value": 1},        # 平均足上昇
                "USDJPY_M15_momi_score": {"value": 0.2},        # トレンド状態
                "USDJPY_M15_price_change_pct": {"value": 0.005} # 価格変化
            },
            "quality_summary": {"overall_quality": 0.7}
        }
        
        # 信号生成
        signal = m15_dag.process(test_bundle)
        
        # メモ概念の検証
        if not hasattr(signal, "dokyaku_score"):
            print("❌ 同逆スコアが記録されていません")
            return False
        
        if not hasattr(signal, "ikikaeri_pattern"):
            print("❌ 行帰パターンが記録されていません")
            return False
        
        if not hasattr(signal, "momi_state"):
            print("❌ もみ合い状態が記録されていません")
            return False
        
        print(f"✅ M15判定DAGテスト合格 (同逆: {signal.dokyaku_score:.2f}, "
              f"行帰: {signal.ikikaeri_pattern}, もみ: {signal.momi_state})")
        return True
        
    except Exception as e:
        print(f"❌ M15判定DAGエラー: {e}")
        return False

def test_unified_decision_system():
    """統合判定システムテスト"""
    print("🔍 統合判定システムテスト...")
    
    try:
        from src.pkg.decision_dag import UnifiedDecisionSystem, TradingStrategy, SignalType
        
        # 統合システム初期化
        unified = UnifiedDecisionSystem("USDJPY", ["M1", "M5", "M15"])
        
        # 各時間足の特徴量バンドル
        feature_bundles = {
            "M1": {
                "features": {"USDJPY_M1_price_momentum": {"value": 0.001}},
                "quality_summary": {"overall_quality": 0.7}
            },
            "M5": {
                "features": {"USDJPY_M5_signal_strength": {"value": 0.6}},
                "quality_summary": {"overall_quality": 0.75}
            },
            "M15": {
                "features": {
                    "USDJPY_M15_momi_score": {"value": 0.5},
                    "USDJPY_M15_dokyaku_score": {"value": 0.7}
                },
                "quality_summary": {"overall_quality": 0.8}
            }
        }
        
        # 統合信号生成
        unified_signal = unified.process(feature_bundles, TradingStrategy.DAY_TRADE)
        
        # 結果検証
        if unified_signal.primary_signal == SignalType.NEUTRAL and unified_signal.confidence == 0.0:
            print("❌ 統合信号が生成されませんでした")
            return False
        
        if unified_signal.strategy != TradingStrategy.DAY_TRADE:
            print(f"❌ 戦略が一致しません: {unified_signal.strategy}")
            return False
        
        print(f"✅ 統合判定システムテスト合格 (信号: {unified_signal.primary_signal.name}, "
              f"戦略: {unified_signal.strategy.value}, 信頼度: {unified_signal.confidence:.2f})")
        return True
        
    except Exception as e:
        print(f"❌ 統合判定システムエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hierarchy_compliance():
    """階層準拠性テスト"""
    print("🔍 階層準拠性テスト...")
    
    try:
        from src.pkg.decision_dag import (
            M1DecisionDAG, M5DecisionDAG, M15DecisionDAG, 
            H1DecisionDAG, H4DecisionDAG, TIMEFRAME_LAYER_RANGES
        )
        
        # 各DAGの階層範囲チェック
        dags = {
            "M1": M1DecisionDAG("USDJPY"),
            "M5": M5DecisionDAG("USDJPY"),
            "M15": M15DecisionDAG("USDJPY"),
            "H1": H1DecisionDAG("USDJPY"),
            "H4": H4DecisionDAG("USDJPY")
        }
        
        for timeframe, dag in dags.items():
            expected_range = TIMEFRAME_LAYER_RANGES[timeframe]
            
            # ノードの階層をチェック
            for node_id, node_def in dag.nodes.items():
                layer = node_def["layer"]
                
                if not (expected_range[0] <= layer <= expected_range[1]):
                    print(f"❌ {timeframe}の階層違反: ノード{node_id}が階層{layer}にあります "
                          f"(期待範囲: {expected_range})")
                    return False
        
        print("✅ 階層準拠性テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ 階層準拠性エラー: {e}")
        return False

def test_horizontal_reference_prevention():
    """横参照防止テスト"""
    print("🔍 横参照防止テスト...")
    
    try:
        from src.pkg.decision_dag import M15DecisionDAG
        
        # M15 DAGで検証
        dag = M15DecisionDAG("USDJPY")
        
        # 各ノードの依存関係をチェック
        for node_id, node_def in dag.nodes.items():
            node_layer = node_def["layer"]
            
            for input_id in node_def["inputs"]:
                if input_id in dag.nodes:
                    input_layer = dag.nodes[input_id]["layer"]
                    
                    # 横参照チェック
                    if input_layer >= node_layer:
                        print(f"❌ 横参照違反: {node_id}(層{node_layer}) → "
                              f"{input_id}(層{input_layer})")
                        return False
        
        print("✅ 横参照防止テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ 横参照防止エラー: {e}")
        return False

def test_pkg_id_format():
    """PKG ID形式テスト"""
    print("🔍 PKG ID形式テスト...")
    
    try:
        import re
        from src.pkg.decision_dag import M1DecisionDAG, M15DecisionDAG, H4DecisionDAG
        
        # PKG IDパターン
        pkg_pattern = re.compile(r'^\d{3}\^\d{1,2}-\d{3}$')
        
        # 各DAGのノードIDをチェック
        dags = [
            M1DecisionDAG("USDJPY"),
            M15DecisionDAG("USDJPY"),
            H4DecisionDAG("USDJPY")
        ]
        
        for dag in dags:
            for node_id in dag.nodes.keys():
                if not pkg_pattern.match(node_id):
                    print(f"❌ 不正なPKG ID形式: {node_id}")
                    return False
        
        print("✅ PKG ID形式テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ PKG ID形式エラー: {e}")
        return False

def test_performance():
    """パフォーマンステスト"""
    print("🔍 パフォーマンステスト（30ms以内）...")
    
    try:
        from src.pkg.decision_dag import UnifiedDecisionSystem
        
        # 統合システム初期化（全時間足）
        unified = UnifiedDecisionSystem("USDJPY")
        
        # テスト用バンドル
        test_bundles = {}
        for tf in ["M1", "M5", "M15", "H1", "H4"]:
            test_bundles[tf] = {
                "features": {},
                "quality_summary": {"overall_quality": 0.7}
            }
        
        # パフォーマンス測定
        start_time = time.time()
        signal = unified.process(test_bundles)
        execution_time = (time.time() - start_time) * 1000
        
        if execution_time > 30:
            print(f"❌ 実行時間が30msを超過: {execution_time:.2f}ms")
            return False
        
        print(f"✅ パフォーマンステスト合格: {execution_time:.2f}ms")
        return True
        
    except Exception as e:
        print(f"❌ パフォーマンスエラー: {e}")
        return False

def test_signal_types():
    """信号タイプテスト"""
    print("🔍 信号タイプテスト...")
    
    try:
        from src.pkg.decision_dag import SignalType
        
        # 全信号タイプの存在確認
        required_types = [
            "BUY_STRONG", "BUY", "BUY_WEAK",
            "NEUTRAL",
            "SELL_WEAK", "SELL", "SELL_STRONG"
        ]
        
        for type_name in required_types:
            if not hasattr(SignalType, type_name):
                print(f"❌ 信号タイプ {type_name} が定義されていません")
                return False
        
        # 値の確認
        if SignalType.BUY_STRONG.value <= SignalType.BUY.value:
            print("❌ 信号強度の順序が不正です")
            return False
        
        print("✅ 信号タイプテスト合格")
        return True
        
    except Exception as e:
        print(f"❌ 信号タイプエラー: {e}")
        return False

def test_strategy_selection():
    """戦略選択テスト"""
    print("🔍 戦略選択テスト...")
    
    try:
        from src.pkg.decision_dag import UnifiedDecisionSystem, TradingStrategy
        
        unified = UnifiedDecisionSystem("USDJPY")
        
        # もみ合い状態 → スキャルピング戦略
        momi_bundles = {
            "M15": {
                "features": {"USDJPY_M15_momi_score": {"value": 0.9}},
                "quality_summary": {"overall_quality": 0.7}
            }
        }
        
        signal = unified.process(momi_bundles)
        if signal.strategy != TradingStrategy.SCALPING:
            print(f"❌ もみ合い時の戦略が不適切: {signal.strategy}")
            return False
        
        # トレンド状態 → スイング戦略
        trend_bundles = {
            "M15": {
                "features": {"USDJPY_M15_momi_score": {"value": 0.2}},
                "quality_summary": {"overall_quality": 0.7}
            }
        }
        
        signal = unified.process(trend_bundles)
        if signal.strategy != TradingStrategy.SWING_TRADE:
            print(f"❌ トレンド時の戦略が不適切: {signal.strategy}")
            return False
        
        print("✅ 戦略選択テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ 戦略選択エラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("="*80)
    print("🧪 Decision DAG Phase 3 テストスイート")
    print("="*80)
    
    tests = [
        test_signal_types,
        test_pkg_id_format,
        test_hierarchy_compliance,
        test_horizontal_reference_prevention,
        test_m1_decision_dag,
        test_m15_decision_dag,
        test_unified_decision_system,
        test_strategy_selection,
        test_performance
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
        print("🎉 すべてのテストが合格しました！Phase 3 実装完了です。")
        return True
    else:
        print("⚠️  一部のテストが失敗しました。修正が必要です。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)