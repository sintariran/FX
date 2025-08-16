#!/usr/bin/env python3
"""
通貨ペア適応型バックテスト実行

EURUSD問題解決後の本格バックテスト:
- 通貨ペア別最適パラメータ
- ATRベース動的閾値
- ボラティリティ適応型判定
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
import json
from datetime import datetime
from backtesting.backtest_engine import BacktestEngine
from backtesting.optimized_strategy import OptimizedStrategy


def run_adaptive_backtest():
    """改良版バックテスト実行"""
    
    print("=" * 80)
    print("🎯 最適化戦略バックテスト実行")
    print("=" * 80)
    print("期間: 2023年10月1日 〜 2024年1月1日（3ヶ月間）")
    print("改良点: 通貨ペア別閾値、ATR動的調整、ボラティリティ適応")
    print("=" * 80)
    
    # テスト対象通貨ペア
    pairs = ["USDJPY", "EURJPY", "EURUSD", "GBPJPY"]
    
    all_results = {}
    
    for pair in pairs:
        print(f"\n{'='*70}")
        print(f"📊 {pair} 適応型バックテスト開始")
        print(f"{'='*70}")
        
        # データファイル確認
        data_file = f"./data/histdata/{pair}_M15_3months.csv"
        
        if not os.path.exists(data_file):
            print(f"❌ ファイルが見つかりません: {data_file}")
            continue
        
        # データ読み込み
        market_data = []
        with open(data_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                market_data.append({
                    'timestamp': row['timestamp'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume']) if 'volume' in row else 0.0
                })
        
        print(f"✅ データ読み込み完了: {len(market_data)}足")
        
        # バックテストエンジン初期化
        engine = BacktestEngine(initial_balance=1000000)
        strategy = OptimizedStrategy(pair)
        
        print(f"💰 初期資金: ¥{engine.initial_balance:,}")
        
        # バックテスト実行
        entry_signals = 0
        trade_count = 0
        current_position = None
        
        for i, candle in enumerate(market_data):
            # 最低限のデータが蓄積されるまで待機
            if i < 20:
                continue
            
            signal = strategy.generate_signal(candle, i, market_data)
            
            # エントリー信号処理
            if signal in [1, 2] and current_position is None:  # 新規エントリー
                direction = signal  # 1=買い, 2=売り
                entry_price = candle['close']
                
                # ポジションオープン
                position = engine.open_position(
                    timestamp=candle['timestamp'],
                    price=entry_price,
                    direction=direction,
                    size=1.0
                )
                
                current_position = position
                entry_signals += 1
                
                print(f"📈 エントリー {entry_signals}: {candle['timestamp']} "
                      f"{'BUY' if direction == 1 else 'SELL'} @ {entry_price:.6f}")
            
            # エグジット処理（利確・損切り）
            elif current_position and current_position.is_open:
                current_price = candle['close']
                should_exit = False
                exit_reason = ""
                
                # 利確・損切り判定
                if current_position.direction == 1:  # 買いポジション
                    profit_target = current_position.entry_price * (1 + strategy.params["profit_target"])
                    stop_loss = current_position.entry_price * (1 - strategy.params["stop_loss"])
                    
                    if current_price >= profit_target:
                        should_exit = True
                        exit_reason = "利確"
                    elif current_price <= stop_loss:
                        should_exit = True
                        exit_reason = "損切り"
                        
                else:  # 売りポジション
                    profit_target = current_position.entry_price * (1 - strategy.params["profit_target"])
                    stop_loss = current_position.entry_price * (1 + strategy.params["stop_loss"])
                    
                    if current_price <= profit_target:
                        should_exit = True
                        exit_reason = "利確"
                    elif current_price >= stop_loss:
                        should_exit = True
                        exit_reason = "損切り"
                
                # エグジット実行
                if should_exit:
                    pnl = engine.close_position(
                        position=current_position,
                        timestamp=candle['timestamp'],
                        price=current_price
                    )
                    
                    trade_count += 1
                    result = "利益" if pnl > 0 else "損失"
                    strategy.update_performance("loss" if pnl < 0 else "win")
                    
                    print(f"📉 エグジット {trade_count}: {candle['timestamp']} "
                          f"CLOSE @ {current_price:.6f} | {exit_reason} | "
                          f"PnL: ¥{pnl:,.0f} ({result})")
                    
                    current_position = None
        
        # 残ポジションのクローズ
        if current_position and current_position.is_open:
            final_candle = market_data[-1]
            final_pnl = engine.close_position(
                position=current_position,
                timestamp=final_candle['timestamp'],
                price=final_candle['close']
            )
            trade_count += 1
            print(f"📉 最終クローズ: ¥{final_pnl:,.0f}")
        
        # 結果計算
        results = engine.calculate_performance()
        
        # 結果表示
        print(f"\n{'='*50}")
        print(f"📊 {pair} バックテスト結果サマリー")
        print(f"{'='*50}")
        print(f"初期資金:     ¥{results['initial_balance']:,}")
        print(f"最終資金:     ¥{results['final_balance']:,}")
        print(f"総損益:       ¥{results['total_pnl']:,}")
        print(f"収益率:       {results['return_pct']:.2f}%")
        print(f"総取引数:     {results['total_trades']}回")
        print(f"勝ちトレード: {results['winning_trades']}回")
        print(f"負けトレード: {results['losing_trades']}回")
        print(f"勝率:         {results['win_rate']:.1f}%")
        print(f"最大DD:       {results['max_drawdown']:.2f}%")
        
        # 改善効果の表示
        if pair == "EURUSD":
            print(f"\n🎉 EURUSD改善効果:")
            print(f"  従来取引数: 5回 → 改良後: {results['total_trades']}回")
            print(f"  従来勝率:  20% → 改良後: {results['win_rate']:.1f}%")
            print(f"  従来収益: -0.01% → 改良後: {results['return_pct']:.2f}%")
        
        # 結果保存
        all_results[pair] = results
        
        # JSON保存
        result_file = f"./data/{pair}_optimized_backtest_results.json"
        with open(result_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # トレード履歴CSV保存
        trades_file = f"./data/{pair}_optimized_backtest_trades.csv"
        engine.save_trade_history(trades_file)
        
        print(f"💾 結果保存: {result_file}")
        print(f"💾 履歴保存: {trades_file}")
    
    # 全体サマリー
    print(f"\n{'='*80}")
    print(f"🏆 適応型バックテスト全体サマリー")
    print(f"{'='*80}")
    
    total_pnl = 0
    total_trades = 0
    profitable_pairs = 0
    
    for pair, result in all_results.items():
        total_pnl += result['total_pnl']
        total_trades += result['total_trades']
        if result['return_pct'] > 0:
            profitable_pairs += 1
        
        print(f"{pair:8s}: {result['return_pct']:+7.2f}% | "
              f"{result['total_trades']:3d}回 | "
              f"勝率{result['win_rate']:5.1f}% | "
              f"¥{result['total_pnl']:>8,.0f}")
    
    print(f"{'='*80}")
    print(f"合計損益: ¥{total_pnl:,}")
    print(f"合計取引: {total_trades}回")
    print(f"収益通貨: {profitable_pairs}/{len(all_results)}ペア")
    
    # パフォーマンス判定
    if total_pnl > 0 and profitable_pairs >= len(all_results) // 2:
        print(f"\n🎉 適応型戦略成功！")
        print(f"   通貨ペア別最適化により全体パフォーマンス向上")
    else:
        print(f"\n⚠️ さらなる最適化が必要")
        print(f"   個別通貨ペアのパラメータ調整を推奨")
    
    return all_results


if __name__ == "__main__":
    results = run_adaptive_backtest()
    print(f"\n✅ 適応型バックテスト完了")