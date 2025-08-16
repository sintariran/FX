#!/usr/bin/env python3
"""
Financial DAG Phase 4 テストスイート
リスク計算とポジションサイジングのテスト
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# テスト対象のモジュールをインポート
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_risk_calculator_dag():
    """リスク計算DAGテスト"""
    print("🔍 リスク計算DAGテスト...")
    
    try:
        from src.pkg.financial_dag import RiskCalculatorDAG, RiskLevel
        
        # リスク計算DAG初期化
        risk_dag = RiskCalculatorDAG("USDJPY")
        
        # テスト用データ
        unified_signal = {"signal": "BUY", "confidence": 0.7}
        account_info = {"balance": 100000, "margin_used": 10000}
        market_data = {"volatility": 0.015, "spread": 0.5}
        portfolio_data = {"positions": [{"value": 5000}, {"value": 3000}]}
        historical_data = [
            {"close": 150.00}, {"close": 150.50}, {"close": 149.80},
            {"close": 151.00}, {"close": 150.20}
        ]
        portfolio_history = [
            {"value": 100000}, {"value": 98000}, {"value": 102000},
            {"value": 101000}, {"value": 103000}
        ]
        
        # リスク評価実行
        risk_metrics = risk_dag.process(
            unified_signal, account_info, market_data,
            portfolio_data, historical_data, portfolio_history
        )
        
        # 結果検証
        if risk_metrics is None:
            print("❌ リスクメトリクスが生成されませんでした")
            return False
        
        if not hasattr(risk_metrics, "risk_level"):
            print("❌ リスクレベルが設定されていません")
            return False
        
        if not hasattr(risk_metrics, "var_95"):
            print("❌ VaR(95%)が計算されていません")
            return False
        
        print(f"✅ リスク計算DAGテスト合格 (リスクレベル: {risk_metrics.risk_level.name}, "
              f"VaR: {risk_metrics.var_95:.4f})")
        return True
        
    except Exception as e:
        print(f"❌ リスク計算DAGエラー: {e}")
        return False

def test_position_sizer_dag():
    """ポジションサイジングDAGテスト"""
    print("🔍 ポジションサイジングDAGテスト...")
    
    try:
        from src.pkg.financial_dag import PositionSizerDAG, PositionType
        
        # ポジションサイザー初期化
        sizer_dag = PositionSizerDAG("USDJPY")
        
        # テスト用パラメータ
        account_balance = 100000
        risk_percentage = 0.02
        market_volatility = 0.01
        atr_value = 0.5
        win_rate = 0.55
        avg_win_loss_ratio = 1.5
        
        # ポジションサイズ計算
        position_size = sizer_dag.process(
            account_balance=account_balance,
            risk_percentage=risk_percentage,
            market_volatility=market_volatility,
            atr_value=atr_value,
            win_rate=win_rate,
            avg_win_loss_ratio=avg_win_loss_ratio
        )
        
        # 結果検証
        if position_size is None:
            print("❌ ポジションサイズが生成されませんでした")
            return False
        
        if not hasattr(position_size, "lot_size"):
            print("❌ ロットサイズが計算されていません")
            return False
        
        if position_size.lot_size <= 0:
            print("❌ 無効なロットサイズです")
            return False
        
        print(f"✅ ポジションサイジングDAGテスト合格 (ロットサイズ: {position_size.lot_size:.2f}, "
              f"リスク金額: {position_size.risk_amount:.0f}円)")
        return True
        
    except Exception as e:
        print(f"❌ ポジションサイジングDAGエラー: {e}")
        return False

def test_kelly_criterion():
    """ケリー基準テスト"""
    print("🔍 ケリー基準テスト...")
    
    try:
        from src.pkg.financial_dag import PositionSizerDAG
        
        sizer = PositionSizerDAG("USDJPY")
        
        # 高勝率・高リワードのケース
        position_high = sizer.process(
            account_balance=100000,
            win_rate=0.60,
            avg_win_loss_ratio=2.0,
            kelly_fraction_multiplier=0.25
        )
        
        # 低勝率・低リワードのケース
        position_low = sizer.process(
            account_balance=100000,
            win_rate=0.45,
            avg_win_loss_ratio=1.2,
            kelly_fraction_multiplier=0.25
        )
        
        # ケリー基準による調整確認
        if position_high.kelly_fraction <= position_low.kelly_fraction:
            print("❌ ケリー基準が正しく機能していません")
            return False
        
        print(f"✅ ケリー基準テスト合格 (高勝率: {position_high.kelly_fraction:.3f}, "
              f"低勝率: {position_low.kelly_fraction:.3f})")
        return True
        
    except Exception as e:
        print(f"❌ ケリー基準エラー: {e}")
        return False

def test_risk_levels():
    """リスクレベル分類テスト"""
    print("🔍 リスクレベル分類テスト...")
    
    try:
        from src.pkg.financial_dag import RiskLevel
        
        # 全リスクレベルの存在確認
        required_levels = ["MINIMAL", "LOW", "MODERATE", "HIGH", "EXTREME"]
        
        for level_name in required_levels:
            if not hasattr(RiskLevel, level_name):
                print(f"❌ リスクレベル {level_name} が定義されていません")
                return False
        
        # 値の順序確認
        if RiskLevel.MINIMAL.value >= RiskLevel.LOW.value:
            print("❌ リスクレベルの順序が不正です")
            return False
        
        print("✅ リスクレベル分類テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ リスクレベルエラー: {e}")
        return False

def test_position_types():
    """ポジションタイプテスト"""
    print("🔍 ポジションタイプテスト...")
    
    try:
        from src.pkg.financial_dag import PositionType
        
        # ポジションタイプの存在確認
        if PositionType.MICRO.value != 1000:
            print("❌ マイクロロットの値が不正です")
            return False
        
        if PositionType.MINI.value != 10000:
            print("❌ ミニロットの値が不正です")
            return False
        
        if PositionType.STANDARD.value != 100000:
            print("❌ スタンダードロットの値が不正です")
            return False
        
        print("✅ ポジションタイプテスト合格")
        return True
        
    except Exception as e:
        print(f"❌ ポジションタイプエラー: {e}")
        return False

def test_hierarchy_compliance():
    """階層準拠性テスト"""
    print("🔍 階層準拠性テスト...")
    
    try:
        from src.pkg.financial_dag import (
            RiskCalculatorDAG, PositionSizerDAG, FINANCIAL_LAYER_RANGES
        )
        
        # リスク計算DAGの階層チェック
        risk_dag = RiskCalculatorDAG("USDJPY")
        risk_range = FINANCIAL_LAYER_RANGES["risk_calculation"]
        
        for node_id, node_def in risk_dag.nodes.items():
            layer = node_def["layer"]
            if not (risk_range[0] <= layer <= risk_range[1]):
                print(f"❌ リスク計算DAGの階層違反: {node_id}が階層{layer}にあります")
                return False
        
        # ポジションサイジングDAGの階層チェック
        sizer_dag = PositionSizerDAG("USDJPY")
        sizing_range = FINANCIAL_LAYER_RANGES["position_sizing"]
        
        for node_id, node_def in sizer_dag.nodes.items():
            layer = node_def["layer"]
            if not (sizing_range[0] <= layer <= sizing_range[1]):
                print(f"❌ ポジションサイジングDAGの階層違反: {node_id}が階層{layer}にあります")
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
        from src.pkg.financial_dag import RiskCalculatorDAG, PositionSizerDAG
        
        dags = [
            RiskCalculatorDAG("USDJPY"),
            PositionSizerDAG("USDJPY")
        ]
        
        for dag in dags:
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
        from src.pkg.financial_dag import RiskCalculatorDAG, PositionSizerDAG
        
        # PKG IDパターン
        pkg_pattern = re.compile(r'^\d{3}\^\d{1,2}-\d{3}$')
        
        dags = [
            RiskCalculatorDAG("USDJPY"),
            PositionSizerDAG("USDJPY")
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

def test_var_calculation():
    """VaR計算テスト"""
    print("🔍 VaR計算テスト...")
    
    try:
        from src.pkg.financial_dag import RiskCalculatorDAG
        
        risk_dag = RiskCalculatorDAG("USDJPY")
        
        # ボラティリティの高いデータ
        volatile_data = [
            {"close": 150.00}, {"close": 152.00}, {"close": 148.00},
            {"close": 153.00}, {"close": 147.00}, {"close": 151.00}
        ]
        
        # ボラティリティの低いデータ
        stable_data = [
            {"close": 150.00}, {"close": 150.10}, {"close": 149.90},
            {"close": 150.05}, {"close": 149.95}, {"close": 150.00}
        ]
        
        # リスク評価実行
        risk_volatile = risk_dag.process(
            unified_signal={}, account_info={"balance": 100000},
            market_data={}, portfolio_data={},
            historical_data=volatile_data, portfolio_history=[]
        )
        
        risk_stable = risk_dag.process(
            unified_signal={}, account_info={"balance": 100000},
            market_data={}, portfolio_data={},
            historical_data=stable_data, portfolio_history=[]
        )
        
        # VaRの比較
        if risk_volatile.var_95 <= risk_stable.var_95:
            print("❌ VaR計算が正しくありません")
            return False
        
        print(f"✅ VaR計算テスト合格 (高ボラ: {risk_volatile.var_95:.4f}, "
              f"低ボラ: {risk_stable.var_95:.4f})")
        return True
        
    except Exception as e:
        print(f"❌ VaR計算エラー: {e}")
        return False

def test_drawdown_analysis():
    """ドローダウン分析テスト"""
    print("🔍 ドローダウン分析テスト...")
    
    try:
        from src.pkg.financial_dag import RiskCalculatorDAG
        
        risk_dag = RiskCalculatorDAG("USDJPY")
        
        # ドローダウンシナリオ
        portfolio_with_dd = [
            {"value": 100000}, {"value": 105000}, {"value": 110000},  # ピーク
            {"value": 105000}, {"value": 100000}, {"value": 95000},   # ドローダウン
            {"value": 98000}, {"value": 102000}
        ]
        
        # ドローダウンなしシナリオ
        portfolio_no_dd = [
            {"value": 100000}, {"value": 101000}, {"value": 102000},
            {"value": 103000}, {"value": 104000}, {"value": 105000}
        ]
        
        # リスク評価実行
        risk_with_dd = risk_dag.process(
            unified_signal={}, account_info={"balance": 100000},
            market_data={}, portfolio_data={},
            historical_data=[], portfolio_history=portfolio_with_dd
        )
        
        risk_no_dd = risk_dag.process(
            unified_signal={}, account_info={"balance": 100000},
            market_data={}, portfolio_data={},
            historical_data=[], portfolio_history=portfolio_no_dd
        )
        
        # ドローダウンの比較
        if risk_with_dd.max_drawdown <= risk_no_dd.max_drawdown:
            print("❌ ドローダウン分析が正しくありません")
            return False
        
        print(f"✅ ドローダウン分析テスト合格 (DD有: {risk_with_dd.max_drawdown:.2%}, "
              f"DD無: {risk_no_dd.max_drawdown:.2%})")
        return True
        
    except Exception as e:
        print(f"❌ ドローダウン分析エラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("="*80)
    print("🧪 Financial DAG Phase 4 テストスイート")
    print("="*80)
    
    tests = [
        test_risk_levels,
        test_position_types,
        test_pkg_id_format,
        test_hierarchy_compliance,
        test_horizontal_reference_prevention,
        test_risk_calculator_dag,
        test_position_sizer_dag,
        test_kelly_criterion,
        test_var_calculation,
        test_drawdown_analysis
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
        print("🎉 すべてのテストが合格しました！Phase 4 実装完了です。")
        return True
    else:
        print("⚠️  一部のテストが失敗しました。修正が必要です。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)