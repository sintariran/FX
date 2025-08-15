#!/usr/bin/env python3
"""
戦略シグナル生成デバッグ

他通貨ペアで取引が発生しない原因を調査:
- ATR計算の妥当性確認
- 閾値設定の適正性検証
- シグナル生成ロジックの診断
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
from backtesting.currency_adaptive_strategy import CurrencyAdaptiveStrategy


def debug_strategy_signals():
    """戦略シグナル生成のデバッグ"""
    
    print("=" * 80)
    print("🔍 戦略シグナル生成デバッグ")
    print("=" * 80)
    
    pairs = ["USDJPY", "EURJPY", "EURUSD", "GBPJPY"]
    
    for pair in pairs:
        print(f"\n{'='*60}")
        print(f"🔬 {pair} シグナル生成診断")
        print(f"{'='*60}")
        
        # データ読み込み
        data_file = f"./data/histdata/{pair}_M15_3months.csv"
        if not os.path.exists(data_file):
            print(f"❌ データファイルなし: {data_file}")
            continue
        
        # 最初の100足を読み込み
        market_data = []
        with open(data_file, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 100:
                    break
                market_data.append({
                    'timestamp': row['timestamp'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close'])
                })
        
        # 戦略初期化
        strategy = CurrencyAdaptiveStrategy(pair)
        
        # デバッグ情報収集
        debug_info = {
            'total_signals': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'wait_signals': 0,
            'atr_values': [],
            'range_values': [],
            'threshold_violations': 0,
            'consecutive_losses': 0
        }
        
        print(f"📊 設定パラメータ:")
        for key, value in strategy.params.items():
            print(f"  {key}: {value}")
        
        # シグナル生成テスト
        print(f"\n🎯 シグナル生成テスト（足20-60）:")
        print(f"足番 | 時刻  | レンジ | ATR    | 閾値   | 判定   | 信号")
        print(f"-" * 65)
        
        for i in range(20, min(60, len(market_data))):
            candle = market_data[i]
            
            # ATR計算
            current_atr = strategy.calculate_adaptive_atr(market_data[max(0, i-15):i+1])
            adaptive_threshold = current_atr * strategy.params["atr_multiplier"]
            current_range = candle['high'] - candle['low']
            
            # シグナル生成
            signal = strategy.generate_signal(candle, i, market_data)
            
            # デバッグ情報更新
            debug_info['total_signals'] += 1
            debug_info['atr_values'].append(current_atr)
            debug_info['range_values'].append(current_range)
            
            if signal == 1:
                debug_info['buy_signals'] += 1
                signal_text = "BUY"
            elif signal == 2:
                debug_info['sell_signals'] += 1
                signal_text = "SELL"
            else:
                debug_info['wait_signals'] += 1
                signal_text = "WAIT"
            
            # 閾値違反チェック
            if current_range < adaptive_threshold:
                debug_info['threshold_violations'] += 1
                range_status = "もみ"
            else:
                range_status = "動き"
            
            # ボラティリティ調整
            if pair == "USDJPY" or pair == "EURJPY" or pair == "GBPJPY":
                # 円ペアは異なるスケール
                range_display = f"{current_range:.1f}"
                atr_display = f"{current_atr:.1f}"
                threshold_display = f"{adaptive_threshold:.1f}"
            else:
                # EUR/USDはpips表示
                range_display = f"{current_range*10000:.1f}"
                atr_display = f"{current_atr*10000:.1f}"
                threshold_display = f"{adaptive_threshold*10000:.1f}"
            
            print(f"{i:2d}   | {candle['timestamp'][11:16]} | {range_display:6s} | {atr_display:6s} | {threshold_display:6s} | {range_status:4s} | {signal_text}")
        
        # 統計サマリー
        print(f"\n📈 統計サマリー:")
        avg_atr = sum(debug_info['atr_values']) / len(debug_info['atr_values']) if debug_info['atr_values'] else 0
        avg_range = sum(debug_info['range_values']) / len(debug_info['range_values']) if debug_info['range_values'] else 0
        
        print(f"平均ATR: {avg_atr:.6f}")
        print(f"平均レンジ: {avg_range:.6f}")
        print(f"平均閾値: {avg_atr * strategy.params['atr_multiplier']:.6f}")
        print(f"もみ判定率: {debug_info['threshold_violations']/debug_info['total_signals']*100:.1f}%")
        
        print(f"\n🎯 シグナル分布:")
        print(f"BUY信号: {debug_info['buy_signals']}回")
        print(f"SELL信号: {debug_info['sell_signals']}回")
        print(f"WAIT信号: {debug_info['wait_signals']}回")
        print(f"シグナル率: {(debug_info['buy_signals'] + debug_info['sell_signals'])/debug_info['total_signals']*100:.1f}%")
        
        # 問題診断
        print(f"\n🔍 問題診断:")
        if debug_info['buy_signals'] + debug_info['sell_signals'] == 0:
            print("❌ エントリーシグナルが全く発生していません")
            
            if debug_info['threshold_violations'] / debug_info['total_signals'] > 0.8:
                print("  → もみ判定が多すぎる（閾値が高すぎる可能性）")
                suggested_threshold = avg_atr * 0.8
                print(f"  → 推奨閾値: {suggested_threshold:.6f} (現在の80%)")
            
            print("  → 同逆・行帰判定ロジックの見直しが必要")
        
        elif (debug_info['buy_signals'] + debug_info['sell_signals']) / debug_info['total_signals'] < 0.1:
            print("⚠️ エントリーシグナルが少なすぎます")
            print("  → パラメータ調整または判定ロジックの緩和が必要")
        
        else:
            print("✅ シグナル生成は正常範囲内")


def suggest_parameter_optimization():
    """パラメータ最適化提案"""
    
    print(f"\n{'='*80}")
    print(f"💡 パラメータ最適化提案")
    print(f"{'='*80}")
    
    pairs_analysis = {
        "USDJPY": {
            "issue": "ATR値が大きすぎて閾値が高くなりすぎ",
            "solution": "atr_multiplierを1.5→0.8に削減",
            "new_params": {
                "momi_threshold": 0.0008,
                "atr_multiplier": 0.8,
                "profit_target": 0.0012,
                "stop_loss": 0.0006
            }
        },
        "EURJPY": {
            "issue": "円ペア特有の大きなATR値",
            "solution": "atr_multiplierを1.8→1.0に削減",
            "new_params": {
                "momi_threshold": 0.0012,
                "atr_multiplier": 1.0,
                "profit_target": 0.0018,
                "stop_loss": 0.0009
            }
        },
        "EURUSD": {
            "issue": "解決済み（29回取引成功）",
            "solution": "現在のパラメータを維持",
            "new_params": {
                "momi_threshold": 0.0025,
                "atr_multiplier": 2.0,
                "profit_target": 0.004,
                "stop_loss": 0.002
            }
        },
        "GBPJPY": {
            "issue": "最も高いボラティリティで閾値過大",
            "solution": "atr_multiplierを2.2→1.2に大幅削減",
            "new_params": {
                "momi_threshold": 0.002,
                "atr_multiplier": 1.2,
                "profit_target": 0.0030,
                "stop_loss": 0.0015
            }
        }
    }
    
    for pair, analysis in pairs_analysis.items():
        print(f"\n📊 {pair}:")
        print(f"  問題: {analysis['issue']}")
        print(f"  解決策: {analysis['solution']}")
        print(f"  新パラメータ:")
        for key, value in analysis['new_params'].items():
            print(f"    {key}: {value}")
    
    print(f"\n🚀 次のアクションプラン:")
    print(f"1. パラメータ調整版の実装")
    print(f"2. 最適化バックテストの実行")
    print(f"3. 全通貨ペアでの取引実現")
    print(f"4. 総合パフォーマンスの向上確認")


if __name__ == "__main__":
    debug_strategy_signals()
    suggest_parameter_optimization()