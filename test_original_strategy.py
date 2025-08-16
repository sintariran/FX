#!/usr/bin/env python3
"""
オリジナル戦略でのバックテスト
パフォーマンス悪化の原因を確認
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import csv
from datetime import datetime
from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.memo_strategy import MemoBasedStrategy


def test_original_strategy():
    """オリジナル戦略でテスト"""
    
    print("=" * 70)
    print("🎯 オリジナル戦略バックテスト（元の高パフォーマンス版）")
    print("=" * 70)
    
    # テスト対象（GBPJPYを除く）
    pairs = ["USDJPY", "EURJPY", "EURUSD"]
    
    results = {}
    
    for pair in pairs:
        print(f"\n📊 {pair} テスト開始...")
        
        # データ読み込み
        csv_file = f"./data/{pair}_1week_data.csv"
        if not os.path.exists(csv_file):
            print(f"❌ ファイルなし: {csv_file}")
            continue
            
        candles = []
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['open'] = float(row['open'])
                row['high'] = float(row['high'])
                row['low'] = float(row['low'])
                row['close'] = float(row['close'])
                row['volume'] = float(row.get('volume', 0))
                candles.append(row)
        
        # オリジナル戦略でバックテスト
        strategy = MemoBasedStrategy()
        engine = BacktestEngine(initial_balance=1000000)
        
        result = engine.run_backtest(
            strategy=strategy,
            candles=candles,
            pair=pair
        )
        
        results[pair] = result
        
        # 結果表示
        print(f"  収益: ¥{result['total_pnl']:.2f}")
        print(f"  勝率: {result['win_rate']:.1f}%")
        print(f"  取引回数: {result['total_trades']}")
        print(f"  リターン: {result['return_pct']:.4%}")
    
    # 比較結果
    print("\n" + "=" * 70)
    print("📊 パフォーマンス比較")
    print("=" * 70)
    
    print("\n期待値（以前の高パフォーマンス）:")
    print("  USDJPY: 収益率 +12.35%, 勝率 70.37%, 27取引")
    print("  EURJPY: 収益率 +14.68%, 勝率 58.93%, 56取引")
    print("  EURUSD: 収益率 -0.01%, 勝率 20.00%, 5取引")
    
    print("\n実際（オリジナル戦略）:")
    for pair, result in results.items():
        print(f"  {pair}: 収益率 {result['return_pct']:.2%}, "
              f"勝率 {result['win_rate']:.1f}%, "
              f"{result['total_trades']}取引")
    
    return results


if __name__ == "__main__":
    test_original_strategy()