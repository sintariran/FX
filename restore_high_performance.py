#!/usr/bin/env python3
"""
高パフォーマンス戦略の復元
元の成功していた15分足戦略を使用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime
from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.backtest_15min import MemoBasedStrategy15Min


def restore_high_performance():
    """高パフォーマンス戦略での再テスト"""
    
    print("=" * 70)
    print("🎯 高パフォーマンス戦略復元（15分足メモベース）")
    print("=" * 70)
    
    # 3ヶ月データで検証
    pairs = ["USDJPY", "EURJPY", "EURUSD"]
    
    for pair in pairs:
        print(f"\n📊 {pair} 高パフォーマンス戦略バックテスト...")
        
        # 15分足3ヶ月データ使用
        csv_file = f"./data/histdata/{pair}_M15_3months.csv"
        
        if not os.path.exists(csv_file):
            print(f"  ❌ データなし: {csv_file}")
            continue
        
        # データ読み込み
        candles = []
        import csv
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['open'] = float(row['open'])
                row['high'] = float(row['high'])
                row['low'] = float(row['low'])
                row['close'] = float(row['close'])
                row['volume'] = float(row.get('volume', 0))
                candles.append(row)
        
        print(f"  📊 データ数: {len(candles)}本（15分足）")
        
        # 高パフォーマンス戦略（15分足最適化版）
        strategy = MemoBasedStrategy15Min()
        engine = BacktestEngine(initial_balance=1000000)
        
        # バックテスト実行
        result = engine.run_backtest(
            price_data=candles,
            strategy_func=strategy.generate_signal
        )
        
        # 結果保存
        output_file = f"./data/{pair}_restored_performance.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # 結果表示
        print(f"\n  📈 結果:")
        print(f"    収益: ¥{result['total_pnl']:,.2f}")
        print(f"    リターン: {result['return_pct']:.2%}")
        print(f"    勝率: {result['win_rate']:.1f}%")
        print(f"    取引回数: {result['total_trades']}")
        print(f"    最大DD: {result['max_drawdown']:.2%}")
        
        # 期待値との比較
        if pair == "USDJPY":
            expected = {"return": 12.35, "win_rate": 70.37, "trades": 27}
        elif pair == "EURJPY":
            expected = {"return": 14.68, "win_rate": 58.93, "trades": 56}
        elif pair == "EURUSD":
            expected = {"return": -0.01, "win_rate": 20.00, "trades": 5}
        else:
            expected = None
        
        if expected:
            print(f"\n  📊 期待値との比較:")
            print(f"    リターン: {expected['return']:.2%} → {result['return_pct']:.2%}")
            print(f"    勝率: {expected['win_rate']:.1f}% → {result['win_rate']:.1f}%")
            print(f"    取引数: {expected['trades']} → {result['total_trades']}")
    
    print("\n" + "=" * 70)
    print("✅ 高パフォーマンス戦略復元完了")
    print("=" * 70)


if __name__ == "__main__":
    restore_high_performance()