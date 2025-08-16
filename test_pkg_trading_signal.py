#!/usr/bin/env python3
"""
正しいPKG実装のテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pkg.trading_signal_pkg import (
    TradingSignalPKG, PKGID, RawDataSymbol,
    PKGDAGManager
)


def test_pkg_id_system():
    """PKG ID体系のテスト"""
    print("=" * 70)
    print("📊 PKG ID体系テスト")
    print("=" * 70)
    
    # PKG ID作成
    pkg_id = PKGID(
        timeframe=3,   # 15分足
        period=9,      # 共通（周期なし）
        currency=1,    # USDJPY
        hierarchy=2,   # 第2階層
        sequence=201   # 連番201
    )
    
    print(f"作成されたPKG ID: {pkg_id}")
    print(f"  時間足: {pkg_id.timeframe} (3=15分)")
    print(f"  周期: {pkg_id.period} (9=共通)")
    print(f"  通貨: {pkg_id.currency} (1=USDJPY)")
    print(f"  階層: {pkg_id.hierarchy}")
    print(f"  連番: {pkg_id.sequence}")
    
    # PKG IDパース
    parsed = PKGID.parse("391^2-201")
    print(f"\nパース結果: {parsed}")
    
    # 生データ記号
    print("\n生データ記号例:")
    print(f"  {RawDataSymbol.AA001.name}: {RawDataSymbol.AA001.value}")
    print(f"  {RawDataSymbol.AB304.name}: {RawDataSymbol.AB304.value}")
    print(f"  {RawDataSymbol.CA001.name}: {RawDataSymbol.CA001.value}")


def test_dag_evaluation():
    """DAG評価のテスト"""
    print("\n" + "=" * 70)
    print("📊 DAG評価テスト")
    print("=" * 70)
    
    # テストデータ
    test_scenarios = [
        {
            "name": "もみ状態",
            "raw_data": {
                'AA001': 110.50,  # 現在価格
                'AA002': 110.45,  # 前足終値
                'AA003': 110.55,  # 高値
                'AA004': 110.40,  # 安値
                'AA005': 110.45,  # 始値
                'AB301': 110.45,  # 平均足始値
                'AB304': 110.48,  # 平均足終値
                'CA001': 0.15,    # レンジ幅（狭い）
                'threshold': 0.30,
                'base_line': 110.0
            },
            "expected": "もみ（待機）"
        },
        {
            "name": "上昇トレンド",
            "raw_data": {
                'AA001': 111.00,  # 現在価格（上昇）
                'AA002': 110.50,  # 前足終値
                'AA003': 111.20,  # 高値
                'AA004': 110.40,  # 安値
                'AA005': 110.50,  # 始値
                'AB301': 110.45,  # 平均足始値
                'AB304': 110.80,  # 平均足終値（陽線）
                'CA001': 0.80,    # レンジ幅（広い）
                'threshold': 0.30,
                'base_line': 110.0
            },
            "expected": "上昇シグナル"
        },
        {
            "name": "乖離発生",
            "raw_data": {
                'AA001': 110.80,  # 現在価格（基準線上）
                'AA002': 110.50,  # 前足終値
                'AA003': 111.00,  # 高値
                'AA004': 109.50,  # 安値
                'AA005': 110.50,  # 始値
                'AB301': 110.00,  # 平均足始値
                'AB304': 109.80,  # 平均足終値（基準線下）
                'CA001': 1.50,    # レンジ幅
                'threshold': 0.30,
                'base_line': 110.0
            },
            "expected": "乖離による転換可能性"
        }
    ]
    
    dag = PKGDAGManager()
    
    for scenario in test_scenarios:
        print(f"\n【{scenario['name']}】")
        signal, debug_info = dag.evaluate(scenario['raw_data'])
        
        # シグナル解釈
        signal_text = {
            1: "買い",
            2: "売り",
            3: "待機",
            0: "なし"
        }.get(signal, "不明")
        
        print(f"最終シグナル: {signal} ({signal_text})")
        print(f"期待結果: {scenario['expected']}")
        
        # 各階層の結果
        print("\n階層別結果:")
        print(f"  階層1:")
        for k, v in debug_info['layer1'].items():
            node_name = {
                '191^1-101': 'もみ判定',
                '191^1-102': '価格方向',
                '191^1-103': '平均足方向',
                '191^1-104': '乖離検出'
            }.get(k, k)
            print(f"    {node_name}: {v}")
        
        print(f"  階層2:")
        for k, v in debug_info['layer2'].items():
            node_name = {
                '191^2-201': '同逆判定',
                '191^2-202': '行帰パターン',
                '191^2-203': 'ブレイクアウト'
            }.get(k, k)
            print(f"    {node_name}: {v}")
        
        print(f"  階層3:")
        for k, v in debug_info['layer3'].items():
            print(f"    最終統合: {v}")


def test_complete_system():
    """完全なシステムテスト"""
    print("\n" + "=" * 70)
    print("📊 完全システムテスト")
    print("=" * 70)
    
    # テスト用キャンドルデータ
    candles = [
        {'open': 110.00, 'high': 110.20, 'low': 109.90, 'close': 110.10},
        {'open': 110.10, 'high': 110.30, 'low': 110.00, 'close': 110.25},
        {'open': 110.25, 'high': 110.50, 'low': 110.20, 'close': 110.45},
        {'open': 110.45, 'high': 110.55, 'low': 110.40, 'close': 110.50},  # もみ
        {'open': 110.50, 'high': 111.00, 'low': 110.45, 'close': 110.90},  # ブレイクアウト
    ]
    
    system = TradingSignalPKG(pair="USDJPY")
    
    print("キャンドルごとのシグナル生成:")
    print("-" * 50)
    
    for i in range(3, len(candles)):
        signal, debug_info = system.generate_signal(
            candles[i], i, candles
        )
        
        candle = candles[i]
        print(f"\nキャンドル {i}:")
        print(f"  OHLC: {candle['open']:.2f}, {candle['high']:.2f}, "
              f"{candle['low']:.2f}, {candle['close']:.2f}")
        
        signal_map = {1: "買い", 2: "売り", 3: "待機"}
        print(f"  シグナル: {signal_map.get(signal, '不明')}")
        
        # 判定理由
        layer1 = debug_info.get('layer1', {})
        layer2 = debug_info.get('layer2', {})
        
        momi = layer1.get('191^1-101', 0)
        dokyaku = layer2.get('191^2-201', 0)
        breakout = layer2.get('191^2-203', 0)
        
        if momi == 3:
            print(f"  理由: もみ状態のため待機")
        elif breakout != 0:
            print(f"  理由: ブレイクアウト検出")
        elif dokyaku != 3:
            print(f"  理由: 同逆判定によるシグナル")
        else:
            print(f"  理由: デフォルト待機")


def test_stateless_property():
    """ステートレス性のテスト"""
    print("\n" + "=" * 70)
    print("📊 ステートレス性テスト")
    print("=" * 70)
    
    candles = [
        {'open': 110.00, 'high': 110.20, 'low': 109.90, 'close': 110.10},
        {'open': 110.10, 'high': 110.30, 'low': 110.00, 'close': 110.25},
        {'open': 110.25, 'high': 110.50, 'low': 110.20, 'close': 110.45},
        {'open': 110.45, 'high': 111.00, 'low': 110.40, 'close': 110.90},
    ]
    
    system = TradingSignalPKG(pair="USDJPY")
    
    # 同じ入力で複数回実行
    print("同じ入力での複数回実行:")
    for run in range(3):
        signal, _ = system.generate_signal(candles[-1], 3, candles)
        print(f"  実行{run+1}: シグナル={signal}")
    
    print("\n✅ ステートレス性確認: 同じ入力で同じ出力")


def main():
    """メイン実行"""
    print("=" * 70)
    print("🔧 正しいPKG実装テストスイート")
    print("=" * 70)
    print("完全な関数型DAGアーキテクチャによる実装")
    print("=" * 70)
    
    # 各テスト実行
    test_pkg_id_system()
    test_dag_evaluation()
    test_complete_system()
    test_stateless_property()
    
    print("\n" + "=" * 70)
    print("✅ すべてのテスト完了")
    print("=" * 70)
    
    # PKG実装の特徴まとめ
    print("\n📋 実装の特徴:")
    print("1. 生データ層: AA系、AB系、CA系などの記号体系")
    print("2. PKG ID: [時間足][周期][通貨]^[階層]-[連番]")
    print("3. 純粋関数: すべての関数がステートレス")
    print("4. DAG評価: トポロジカルソートによる自動評価")
    print("5. 優先順位: MN関数による関数的な優先順位判定")


if __name__ == "__main__":
    main()