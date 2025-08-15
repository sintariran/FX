#!/usr/bin/env python3
"""
FXシステム統合テスト

Week 1 Day 1-2の実装完了確認とメモロジック統合テスト
"""

import sys
import os
sys.path.append('./src')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 作成したモジュールのインポート
from indicators.base_indicators import BaseIndicators, PerformanceTracker
from utils.database import DatabaseManager
from utils.oanda_client import OandaClient
from operation_logic.key_concepts import OperationLogicEngine, Direction, TimeFrame

def test_indicators_calculation():
    """基本指標計算のテスト"""
    print("🧮 基本指標計算テスト開始...")
    
    # サンプルデータ作成
    dates = pd.date_range('2024-01-01', periods=100, freq='1min')
    sample_data = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 150,
        'high': np.random.randn(100).cumsum() + 151,
        'low': np.random.randn(100).cumsum() + 149,
        'close': np.random.randn(100).cumsum() + 150
    }, index=dates)
    
    indicators = BaseIndicators()
    
    # 平均足計算テスト
    ha_result = indicators.calculate_heikin_ashi(sample_data)
    assert 'ha_open' in ha_result.columns, "平均足計算失敗"
    assert 'ha_direction' in ha_result.columns, "平均足方向計算失敗"
    print(f"✅ 平均足計算: {len(ha_result)} rows")
    
    # OsMA計算テスト
    osma_result = indicators.calculate_osma(sample_data)
    assert 'osma' in osma_result.columns, "OsMA計算失敗"
    print(f"✅ OsMA計算: {len(osma_result)} rows")
    
    # 移動平均計算テスト
    ma_result = indicators.calculate_moving_averages(sample_data)
    assert 'ma_10' in ma_result.columns, "移動平均計算失敗"
    print(f"✅ 移動平均計算: {len(ma_result)} rows")
    
    # レンジ境界計算テスト
    range_result = indicators.calculate_range_boundaries(sample_data)
    assert 'range_high' in range_result.columns, "レンジ計算失敗"
    print(f"✅ レンジ境界計算: {len(range_result)} rows")
    
    # 同逆判定基礎データテスト
    dokyaku_result = indicators.calculate_dokyaku_base(sample_data)
    assert 'deviation_direction' in dokyaku_result.columns, "同逆基礎計算失敗"
    print(f"✅ 同逆判定基礎計算: {len(dokyaku_result)} rows")
    
    # 行帰判定基礎データテスト
    ikikaeri_result = indicators.calculate_ikikaeri_base(sample_data, ha_result)
    assert 'ikikaeri_pattern' in ikikaeri_result.columns, "行帰基礎計算失敗"
    print(f"✅ 行帰判定基礎計算: {len(ikikaeri_result)} rows")
    
    print("✅ 基本指標計算テスト完了\n")
    return True

def test_database_operations():
    """データベース操作のテスト"""
    print("🗄️  データベース操作テスト開始...")
    
    # テスト用データベース
    db = DatabaseManager("./data/test_integration.db")
    
    # サンプル価格データ
    test_df = pd.DataFrame({
        'open': [150.0, 150.1, 150.2],
        'high': [150.1, 150.3, 150.4],
        'low': [149.9, 150.0, 150.1],
        'close': [150.1, 150.2, 150.3],
        'volume': [1000, 1100, 1200]
    }, index=pd.date_range('2024-01-01 00:00', periods=3, freq='1min'))
    
    # 価格データ保存テスト
    db.save_price_data("USD_JPY", "M1", test_df)
    
    # 読み込みテスト
    loaded_df = db.load_price_data("USD_JPY", "M1")
    assert len(loaded_df) == 3, "データベース読み込み失敗"
    print("✅ 価格データ保存・読み込み成功")
    
    # 平均足データ保存テスト
    ha_df = test_df.copy()
    ha_df['ha_open'] = 150.0
    ha_df['ha_high'] = 150.4
    ha_df['ha_low'] = 149.9
    ha_df['ha_close'] = 150.3
    ha_df['ha_direction'] = 1
    
    db.save_heikin_ashi_data("USD_JPY", "M1", ha_df)
    print("✅ 平均足データ保存成功")
    
    # オペレーション信号保存テスト
    signals = {
        'dokyaku': 1,
        'ikikaeri': 1,
        'momi': 0,
        'overshoot': 0,
        'overall': 1
    }
    signal_id = db.save_operation_signal("USD_JPY", "M1", datetime.now(), signals, 0.75)
    assert signal_id > 0, "信号保存失敗"
    print("✅ オペレーション信号保存成功")
    
    # 統計情報確認
    stats = db.get_database_stats()
    print(f"✅ データベース統計: {stats}")
    
    # テストファイル削除
    os.remove("./data/test_integration.db")
    print("✅ データベース操作テスト完了\n")
    return True

def test_operation_logic():
    """オペレーションロジックのテスト"""
    print("🧠 オペレーションロジックテスト開始...")
    
    engine = OperationLogicEngine()
    
    # テストデータ作成
    test_data = {
        'dokyaku_data': {
            'mhih_direction': Direction.UP,
            'mjih_direction': Direction.UP,
            'mmhmh_direction': Direction.UP,
            'mmjmh_direction': Direction.DOWN,
            'mh_confirm_direction': Direction.UP,
            'is_transition_bar': False
        },
        'ikikaeri_data': {
            'current_heikin_direction': Direction.UP,
            'previous_heikin_direction': Direction.UP,
            'high_low_update': True,
            'base_line_position': 150.50,
            'current_price': 150.75
        },
        'momi_data': {
            'range_width': 5.0,  # もみではない
            'os_remaining': 3.0,
            'current_timeframe_conversion': 1.0,
            'breakout_direction': Direction.UP,
            'previous_overshoot': Direction.DOWN
        },
        'timeframe_data': {
            'timeframe_directions': {
                TimeFrame.M15: Direction.UP,
                TimeFrame.M5: Direction.UP
            },
            'transition_timings': {
                TimeFrame.M15: False,
                TimeFrame.M5: True
            }
        },
        'previous_heikin_valid': True,
        'period_alignment': True,
        'overshoot_established': True,
        'minute_alignment': False,
        'opff_previous_alignment': False,
        'timeframe_connection_point': False
    }
    
    # 判定実行
    result = engine.make_decision(test_data)
    
    assert 'direction' in result, "判定結果に方向がない"
    assert 'confidence' in result, "判定結果に信頼度がない"
    assert 'entry_signal' in result, "判定結果にエントリー信号がない"
    
    print(f"✅ 判定方向: {result['direction']}")
    print(f"✅ 信頼度: {result['confidence']:.3f}")
    print(f"✅ エントリー信号: {result['entry_signal']}")
    print(f"✅ エグジット信号: {result['exit_signal']}")
    
    # 詳細結果確認
    details = result['details']
    print("✅ 判定詳細:")
    for system, (direction, confidence) in details.items():
        print(f"   {system}: {direction} (信頼度: {confidence:.3f})")
    
    print("✅ オペレーションロジックテスト完了\n")
    return True

def test_performance_tracking():
    """パフォーマンス追跡のテスト"""
    print("📊 パフォーマンス追跡テスト開始...")
    
    tracker = PerformanceTracker()
    
    # 各操作の実行時間をシミュレート
    tracker.measure_performance('全体', 15.5)  # 目標19ms以下
    tracker.measure_performance('もみ', 68.2)  # 目標77ms以下
    tracker.measure_performance('OP分岐', 95.1)  # 目標101.3ms以下
    tracker.measure_performance('オーバーシュート', 520.3)  # 目標550.6ms以下
    
    # サマリー取得
    summary = tracker.get_performance_summary()
    print("✅ パフォーマンスサマリー:")
    for operation, stats in summary.items():
        print(f"   {operation}: 平均 {stats['avg']:.1f}ms (目標: {stats['target']}ms)")
    
    print("✅ パフォーマンス追跡テスト完了\n")
    return True

def test_multi_timeframe_integration():
    """マルチタイムフレーム統合のテスト"""
    print("⏰ マルチタイムフレーム統合テスト開始...")
    
    indicators = BaseIndicators()
    
    # 複数時間足のサンプルデータ作成
    timeframes = ['M1', 'M5', 'M15', 'M30']
    multi_data = {}
    
    for tf in timeframes:
        if tf == 'M1':
            periods = 100
            freq = '1min'
        elif tf == 'M5':
            periods = 50
            freq = '5min'
        elif tf == 'M15':
            periods = 20
            freq = '15min'
        else:  # M30
            periods = 10
            freq = '30min'
        
        dates = pd.date_range('2024-01-01', periods=periods, freq=freq)
        df = pd.DataFrame({
            'open': np.random.randn(periods).cumsum() + 150,
            'high': np.random.randn(periods).cumsum() + 151,
            'low': np.random.randn(periods).cumsum() + 149,
            'close': np.random.randn(periods).cumsum() + 150
        }, index=dates)
        
        multi_data[tf] = df
    
    # マルチタイムフレーム統合計算
    integrated_data = indicators.calculate_multi_timeframe_data(multi_data)
    
    assert len(integrated_data) == 4, "統合データの時間足数が不正"
    
    for tf, df in integrated_data.items():
        assert 'ha_direction' in df.columns, f"{tf}の平均足計算失敗"
        assert 'osma' in df.columns, f"{tf}のOsMA計算失敗"
        assert 'ikikaeri_pattern' in df.columns, f"{tf}の行帰パターン計算失敗"
        print(f"✅ {tf}統合データ: {len(df)} rows")
    
    print("✅ マルチタイムフレーム統合テスト完了\n")
    return True

def main():
    """統合テストメイン実行"""
    print("🚀 FXシステム統合テスト開始\n")
    print("=" * 50)
    
    test_results = []
    
    try:
        # 各テストの実行
        test_results.append(("基本指標計算", test_indicators_calculation()))
        test_results.append(("データベース操作", test_database_operations()))
        test_results.append(("オペレーションロジック", test_operation_logic()))
        test_results.append(("パフォーマンス追跡", test_performance_tracking()))
        test_results.append(("マルチタイムフレーム統合", test_multi_timeframe_integration()))
        
    except Exception as e:
        print(f"❌ テスト実行中にエラー: {e}")
        return False
    
    # 結果サマリー
    print("=" * 50)
    print("📋 テスト結果サマリー:")
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 全テスト成功！Week 1 Day 1-2の実装完了確認")
        print("📋 Week 1 Day 3-4: メモファイル徹底分析の準備完了")
    else:
        print("\n⚠️  一部テストに失敗しました")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)