#!/usr/bin/env python3
"""
Trading DAG Phase 5 テストスイート
注文執行とポジション管理のテスト
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime, timedelta

# テスト対象のモジュールをインポート
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_order_executor_dag():
    """注文執行DAGテスト"""
    print("🔍 注文執行DAGテスト...")
    
    try:
        from src.pkg.trading_dag import OrderExecutorDAG, OrderType, OrderSide, OrderStatus
        from src.pkg.financial_dag import PositionSize, PositionType, RiskMetrics, RiskLevel
        
        # 注文執行DAG初期化
        executor = OrderExecutorDAG("USDJPY")
        
        # テスト用データ
        class MockSignal:
            confidence = 0.8
        
        unified_signal = MockSignal()
        
        position_size = PositionSize(
            timestamp=datetime.now(),
            units=10000,
            lot_size=0.1,
            position_type=PositionType.MINI,
            risk_amount=1000,
            stop_loss_pips=20,
            take_profit_pips=40,
            risk_reward_ratio=2.0,
            kelly_fraction=0.02,
            components={}
        )
        
        risk_metrics = RiskMetrics(
            timestamp=datetime.now(),
            risk_level=RiskLevel.MODERATE,
            var_95=0.02,
            max_drawdown=0.05,
            sharpe_ratio=1.5,
            position_risk=0.01,
            market_risk=0.01,
            components={}
        )
        
        # 注文実行
        order = executor.process(
            unified_signal=unified_signal,
            position_size=position_size,
            risk_metrics=risk_metrics,
            market_data={"spread": 1.0, "volatility": 0.01},
            signal_confidence=0.8,
            market_conditions={"is_trending": True},
            strategy="day_trade",
            current_price=150.00,
            market_volatility=0.01,
            stop_loss_pips=20,
            take_profit_pips=40
        )
        
        # 結果検証
        if order is None:
            print("❌ 注文が生成されませんでした")
            return False
        
        if not hasattr(order, "order_id"):
            print("❌ 注文IDが設定されていません")
            return False
        
        if order.units <= 0:
            print("❌ 注文単位が無効です")
            return False
        
        print(f"✅ 注文執行DAGテスト合格 (注文ID: {order.order_id}, "
              f"単位: {order.units}, 状態: {order.status.value})")
        return True
        
    except Exception as e:
        print(f"❌ 注文執行DAGエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_position_manager_dag():
    """ポジション管理DAGテスト"""
    print("🔍 ポジション管理DAGテスト...")
    
    try:
        from src.pkg.trading_dag import (
            PositionManagerDAG, Position, PositionStatus, AdjustmentType
        )
        
        # ポジション管理DAG初期化
        manager = PositionManagerDAG("USDJPY")
        
        # テスト用ポジション
        positions = [
            Position(
                position_id="POS001",
                order_id="ORD001",
                timestamp=datetime.now() - timedelta(hours=1),
                currency_pair="USDJPY",
                side="buy",
                units=10000,
                entry_price=150.00,
                current_price=151.00,
                stop_loss=149.50,
                take_profit=152.00,
                unrealized_pnl=10000,  # 1円×10000単位
                realized_pnl=0,
                status=PositionStatus.OPEN,
                metadata={}
            ),
            Position(
                position_id="POS002",
                order_id="ORD002",
                timestamp=datetime.now() - timedelta(hours=2),
                currency_pair="USDJPY",
                side="sell",
                units=5000,
                entry_price=151.00,
                current_price=150.50,
                stop_loss=151.50,
                take_profit=149.00,
                unrealized_pnl=2500,  # 0.5円×5000単位
                realized_pnl=0,
                status=PositionStatus.OPEN,
                metadata={}
            )
        ]
        
        # ポジション管理実行
        adjustments = manager.process(
            positions=positions,
            market_data={"volatility": 0.01},
            current_prices={"USDJPY": 151.00},
            risk_metrics={"risk_level": 3}
        )
        
        # 結果検証
        if adjustments is None:
            print("❌ 調整リストが生成されませんでした")
            return False
        
        print(f"✅ ポジション管理DAGテスト合格 (調整数: {len(adjustments)})")
        return True
        
    except Exception as e:
        print(f"❌ ポジション管理DAGエラー: {e}")
        return False

def test_order_types():
    """注文タイプテスト"""
    print("🔍 注文タイプテスト...")
    
    try:
        from src.pkg.trading_dag import OrderType
        
        # 全注文タイプの存在確認
        required_types = ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]
        
        for type_name in required_types:
            if not hasattr(OrderType, type_name):
                print(f"❌ 注文タイプ {type_name} が定義されていません")
                return False
        
        print("✅ 注文タイプテスト合格")
        return True
        
    except Exception as e:
        print(f"❌ 注文タイプエラー: {e}")
        return False

def test_adjustment_types():
    """調整タイプテスト"""
    print("🔍 調整タイプテスト...")
    
    try:
        from src.pkg.trading_dag import AdjustmentType
        
        # 全調整タイプの存在確認
        required_types = [
            "TRAIL_STOP", "BREAKEVEN", "PARTIAL_CLOSE", 
            "ADD_POSITION", "HEDGE"
        ]
        
        for type_name in required_types:
            if not hasattr(AdjustmentType, type_name):
                print(f"❌ 調整タイプ {type_name} が定義されていません")
                return False
        
        print("✅ 調整タイプテスト合格")
        return True
        
    except Exception as e:
        print(f"❌ 調整タイプエラー: {e}")
        return False

def test_hierarchy_compliance():
    """階層準拠性テスト"""
    print("🔍 階層準拠性テスト...")
    
    try:
        from src.pkg.trading_dag import (
            OrderExecutorDAG, PositionManagerDAG, TRADING_LAYER_RANGES
        )
        
        # 注文執行DAGの階層チェック
        executor = OrderExecutorDAG("USDJPY")
        exec_range = TRADING_LAYER_RANGES["order_execution"]
        
        for node_id, node_def in executor.nodes.items():
            layer = node_def["layer"]
            if not (exec_range[0] <= layer <= exec_range[1]):
                print(f"❌ 注文執行DAGの階層違反: {node_id}が階層{layer}にあります")
                return False
        
        # ポジション管理DAGの階層チェック
        manager = PositionManagerDAG("USDJPY")
        mgmt_range = TRADING_LAYER_RANGES["position_management"]
        
        for node_id, node_def in manager.nodes.items():
            layer = node_def["layer"]
            if not (mgmt_range[0] <= layer <= mgmt_range[1]):
                print(f"❌ ポジション管理DAGの階層違反: {node_id}が階層{layer}にあります")
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
        from src.pkg.trading_dag import OrderExecutorDAG, PositionManagerDAG
        
        dags = [
            OrderExecutorDAG("USDJPY"),
            PositionManagerDAG("USDJPY")
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
        from src.pkg.trading_dag import OrderExecutorDAG, PositionManagerDAG
        
        # PKG IDパターン
        pkg_pattern = re.compile(r'^\d{3}\^\d{1,2}-\d{3}$')
        
        dags = [
            OrderExecutorDAG("USDJPY"),
            PositionManagerDAG("USDJPY")
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

def test_trailing_stop_logic():
    """トレーリングストップロジックテスト"""
    print("🔍 トレーリングストップロジックテスト...")
    
    try:
        from src.pkg.trading_dag import PositionManagerDAG, Position, PositionStatus
        
        manager = PositionManagerDAG("USDJPY")
        
        # 利益が出ているポジション
        profitable_position = Position(
            position_id="POS_PROFIT",
            order_id="ORD_PROFIT",
            timestamp=datetime.now(),
            currency_pair="USDJPY",
            side="buy",
            units=10000,
            entry_price=150.00,
            current_price=151.50,  # 1.5円の利益
            stop_loss=149.00,
            take_profit=152.00,
            unrealized_pnl=15000,  # 15%の利益
            realized_pnl=0,
            status=PositionStatus.OPEN,
            metadata={}
        )
        
        # トレーリングストップチェック
        evaluation = {"open_positions": 1}
        pnl_info = {
            "position_pnls": [{
                "position_id": "POS_PROFIT",
                "pnl_pct": 15  # 15%の利益
            }]
        }
        
        result = manager._check_trailing_stop(evaluation, pnl_info)
        
        if not result.get("should_trail"):
            print("❌ トレーリングストップが提案されませんでした")
            return False
        
        if len(result.get("candidates", [])) == 0:
            print("❌ トレーリング候補が空です")
            return False
        
        print("✅ トレーリングストップロジックテスト合格")
        return True
        
    except Exception as e:
        print(f"❌ トレーリングストップエラー: {e}")
        return False

def test_partial_close_logic():
    """部分決済ロジックテスト"""
    print("🔍 部分決済ロジックテスト...")
    
    try:
        from src.pkg.trading_dag import PositionManagerDAG
        
        manager = PositionManagerDAG("USDJPY")
        
        # 大きな利益が出ているケース
        evaluation = {"open_positions": 1}
        pnl_info = {
            "position_pnls": [{
                "position_id": "POS_BIG_PROFIT",
                "pnl_pct": 25  # 25%の利益
            }]
        }
        
        result = manager._check_partial_close(evaluation, pnl_info)
        
        if not result.get("should_partial_close"):
            print("❌ 部分決済が提案されませんでした")
            return False
        
        candidates = result.get("candidates", [])
        if len(candidates) == 0:
            print("❌ 部分決済候補が空です")
            return False
        
        if candidates[0].get("close_percentage") != 50:
            print("❌ 部分決済割合が不正です")
            return False
        
        print("✅ 部分決済ロジックテスト合格")
        return True
        
    except Exception as e:
        print(f"❌ 部分決済エラー: {e}")
        return False

def test_order_validation():
    """注文検証テスト"""
    print("🔍 注文検証テスト...")
    
    try:
        from src.pkg.trading_dag import OrderExecutorDAG
        from src.pkg.financial_dag import RiskMetrics, RiskLevel, PositionSize, PositionType
        
        executor = OrderExecutorDAG("USDJPY")
        
        # 正常なケース
        class ValidSignal:
            confidence = 0.8
        
        valid_size = PositionSize(
            timestamp=datetime.now(),
            units=10000,
            lot_size=0.1,
            position_type=PositionType.MINI,
            risk_amount=1000,
            stop_loss_pips=20,
            take_profit_pips=40,
            risk_reward_ratio=2.0,
            kelly_fraction=0.02,
            components={}
        )
        
        moderate_risk = RiskMetrics(
            timestamp=datetime.now(),
            risk_level=RiskLevel.MODERATE,
            var_95=0.02,
            max_drawdown=0.05,
            sharpe_ratio=1.5,
            position_risk=0.01,
            market_risk=0.01,
            components={}
        )
        
        result = executor._validate_order(ValidSignal(), valid_size, moderate_risk)
        
        if not result.get("is_valid"):
            print("❌ 正常な注文が無効と判定されました")
            return False
        
        # 高リスクケース
        extreme_risk = RiskMetrics(
            timestamp=datetime.now(),
            risk_level=RiskLevel.EXTREME,
            var_95=0.10,
            max_drawdown=0.20,
            sharpe_ratio=0.5,
            position_risk=0.05,
            market_risk=0.05,
            components={}
        )
        
        result = executor._validate_order(ValidSignal(), valid_size, extreme_risk)
        
        if result.get("is_valid"):
            print("❌ 高リスク注文が有効と判定されました")
            return False
        
        print("✅ 注文検証テスト合格")
        return True
        
    except Exception as e:
        print(f"❌ 注文検証エラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("="*80)
    print("🧪 Trading DAG Phase 5 テストスイート")
    print("="*80)
    
    tests = [
        test_order_types,
        test_adjustment_types,
        test_pkg_id_format,
        test_hierarchy_compliance,
        test_horizontal_reference_prevention,
        test_order_executor_dag,
        test_position_manager_dag,
        test_order_validation,
        test_trailing_stop_logic,
        test_partial_close_logic
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
        print("🎉 すべてのテストが合格しました！Phase 5 実装完了です。")
        return True
    else:
        print("⚠️  一部のテストが失敗しました。修正が必要です。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)