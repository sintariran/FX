"""
FX取引システム基本指標計算エンジン
メモ記載の指標定義に基づく実装
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class TimeFrame(Enum):
    """時間足定義"""
    M1 = "1M"
    M5 = "5M"
    M15 = "15M"
    M30 = "30M"
    H1 = "1H"
    H4 = "4H"


@dataclass
class PriceData:
    """価格データ構造"""
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None


@dataclass
class HeikinAshiData:
    """平均足データ構造"""
    timestamp: pd.Timestamp
    ha_open: float
    ha_high: float
    ha_low: float
    ha_close: float
    direction: int  # 1: 陽線, -1: 陰線


class BaseIndicators:
    """
    基本指標計算クラス
    メモ記載の定義に基づく平均足、OsMA等の実装
    """
    
    def __init__(self):
        self.cache = {}  # 計算結果キャッシュ
    
    def calculate_heikin_ashi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        平均足計算
        メモ: 平均足の等速予知による今足と前足の到達距離差分が小さい時の判定
        """
        ha_df = df.copy()
        ha_df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        
        # 初期値設定
        ha_df.loc[0, 'ha_open'] = (df.loc[0, 'open'] + df.loc[0, 'close']) / 2
        
        # 平均足Open計算（前の平均足のOpen+Closeの平均）
        for i in range(1, len(ha_df)):
            ha_df.loc[i, 'ha_open'] = (ha_df.loc[i-1, 'ha_open'] + 
                                       ha_df.loc[i-1, 'ha_close']) / 2
        
        # 平均足High/Low計算
        ha_df['ha_high'] = df[['high', 'ha_open', 'ha_close']].max(axis=1)
        ha_df['ha_low'] = df[['low', 'ha_open', 'ha_close']].min(axis=1)
        
        # 方向判定（陰陽）
        ha_df['ha_direction'] = np.where(
            ha_df['ha_close'] > ha_df['ha_open'], 1, -1
        )
        
        # 転換判定
        ha_df['ha_reversal'] = (ha_df['ha_direction'] != 
                                ha_df['ha_direction'].shift(1)).astype(int)
        
        return ha_df
    
    def calculate_osma(self, df: pd.DataFrame, 
                       fast_period: int = 12, 
                       slow_period: int = 26, 
                       signal_period: int = 9) -> pd.DataFrame:
        """
        OsMA (MACD-Signal) 計算
        メモ: TSML周期（10,15,30,45,60,90,180）での計算
        """
        # MACD計算
        ema_fast = df['close'].ewm(span=fast_period).mean()
        ema_slow = df['close'].ewm(span=slow_period).mean()
        macd = ema_fast - ema_slow
        
        # Signal計算
        signal = macd.ewm(span=signal_period).mean()
        
        # OsMA = MACD - Signal
        osma = macd - signal
        
        result_df = df.copy()
        result_df['macd'] = macd
        result_df['signal'] = signal
        result_df['osma'] = osma
        
        # OsMAの転換点検出
        result_df['osma_direction'] = np.where(osma > 0, 1, -1)
        result_df['osma_reversal'] = (result_df['osma_direction'] != 
                                      result_df['osma_direction'].shift(1)).astype(int)
        
        return result_df
    
    def calculate_moving_averages(self, df: pd.DataFrame, 
                                  periods: List[int] = [10, 30, 90, 180]) -> pd.DataFrame:
        """
        移動平均線計算
        メモ: 10の上/下での方向判定用
        """
        result_df = df.copy()
        
        for period in periods:
            ma_col = f'ma_{period}'
            result_df[ma_col] = df['close'].rolling(window=period).mean()
            
            # 価格と移動平均の位置関係
            position_col = f'price_vs_ma_{period}'
            result_df[position_col] = np.where(
                df['close'] > result_df[ma_col], 1,  # 上
                np.where(df['close'] < result_df[ma_col], -1, 0)  # 下 or 同値
            )
        
        return result_df
    
    def calculate_range_boundaries(self, df: pd.DataFrame, 
                                   period: int = 20) -> pd.DataFrame:
        """
        レンジ境界計算
        メモ: 足レンジ、価格レンジの判定用
        """
        result_df = df.copy()
        
        # 足レンジ（短期境界）
        result_df['range_high'] = df['high'].rolling(window=period).max()
        result_df['range_low'] = df['low'].rolling(window=period).min()
        result_df['range_width'] = result_df['range_high'] - result_df['range_low']
        
        # レンジ抜け判定
        result_df['range_break_up'] = (df['high'] > result_df['range_high'].shift(1)).astype(int)
        result_df['range_break_down'] = (df['low'] < result_df['range_low'].shift(1)).astype(int)
        
        # Pレンジ（長期価格レンジ）
        long_period = period * 3
        result_df['p_range_high'] = df['high'].rolling(window=long_period).max()
        result_df['p_range_low'] = df['low'].rolling(window=long_period).min()
        
        return result_df
    
    def calculate_dokyaku_base(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        同逆判定用基礎データ計算
        メモ: 前々足乖離による方向判断
        """
        result_df = df.copy()
        
        # 前足・前々足の高値安値
        result_df['prev_high'] = df['high'].shift(1)
        result_df['prev_low'] = df['low'].shift(1)
        result_df['prev2_high'] = df['high'].shift(2)
        result_df['prev2_low'] = df['low'].shift(2)
        
        # 乖離計算（前々足からの距離）
        result_df['deviation_from_prev2_high'] = df['close'] - result_df['prev2_high']
        result_df['deviation_from_prev2_low'] = df['close'] - result_df['prev2_low']
        
        # 乖離の方向判定
        result_df['deviation_direction'] = np.where(
            abs(result_df['deviation_from_prev2_high']) < 
            abs(result_df['deviation_from_prev2_low']),
            1,  # 高値寄り
            -1  # 安値寄り
        )
        
        return result_df
    
    def calculate_ikikaeri_base(self, df: pd.DataFrame, ha_df: pd.DataFrame) -> pd.DataFrame:
        """
        行帰判定用基礎データ計算
        メモ: 前足行帰判定、平均足予知による確認
        """
        result_df = df.copy()
        
        # 前足の方向性
        result_df['prev_direction'] = np.where(
            (df['close'].shift(1) > df['open'].shift(1)), 1, -1
        )
        
        # 平均足の方向性
        result_df['ha_prev_direction'] = ha_df['ha_direction'].shift(1)
        
        # 高値安値更新パターン
        result_df['higher_high'] = (df['high'] > df['high'].shift(1)).astype(int)
        result_df['higher_low'] = (df['low'] > df['low'].shift(1)).astype(int)
        result_df['lower_high'] = (df['high'] < df['high'].shift(1)).astype(int)
        result_df['lower_low'] = (df['low'] < df['low'].shift(1)).astype(int)
        
        # 行帰パターン分類
        # 行行: higher_high & higher_low
        # 帰行: lower_high & higher_low  
        # 帰戻: lower_high & lower_low
        # 行帰: higher_high & lower_low
        
        result_df['ikikaeri_pattern'] = 0
        result_df.loc[(result_df['higher_high'] == 1) & 
                      (result_df['higher_low'] == 1), 'ikikaeri_pattern'] = 1  # 行行
        result_df.loc[(result_df['lower_high'] == 1) & 
                      (result_df['higher_low'] == 1), 'ikikaeri_pattern'] = 2  # 帰行
        result_df.loc[(result_df['lower_high'] == 1) & 
                      (result_df['lower_low'] == 1), 'ikikaeri_pattern'] = 3  # 帰戻
        result_df.loc[(result_df['higher_high'] == 1) & 
                      (result_df['lower_low'] == 1), 'ikikaeri_pattern'] = 4  # 行帰
        
        return result_df
    
    def calculate_multi_timeframe_data(self, 
                                       minute_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        マルチタイムフレームデータ統合
        メモ: 時間結合の役割 - 他時間足の動きを用いてオーバーシュート判断
        """
        integrated_data = {}
        
        for timeframe, df in minute_data.items():
            # 各時間足での基本指標計算
            ha_df = self.calculate_heikin_ashi(df)
            osma_df = self.calculate_osma(df)
            ma_df = self.calculate_moving_averages(df)
            range_df = self.calculate_range_boundaries(df)
            dokyaku_df = self.calculate_dokyaku_base(df)
            ikikaeri_df = self.calculate_ikikaeri_base(df, ha_df)
            
            # 統合
            integrated_df = df.copy()
            for col in ha_df.columns:
                if col not in df.columns:
                    integrated_df[col] = ha_df[col]
            
            # 他の指標も同様に統合
            for source_df in [osma_df, ma_df, range_df, dokyaku_df, ikikaeri_df]:
                for col in source_df.columns:
                    if col not in integrated_df.columns:
                        integrated_df[col] = source_df[col]
            
            integrated_data[timeframe] = integrated_df
        
        return integrated_data


class PerformanceTracker:
    """
    パフォーマンス追跡クラス
    メモ記載の処理時間目標（全体19ms、もみ77ms等）の監視
    """
    
    def __init__(self):
        self.timing_data = {}
        self.targets = {
            '全体': 19,  # ms
            'もみ': 77,  # ms
            'OP分岐': 101.3,  # ms
            'オーバーシュート': 550.6,  # ms
            '時間結合': 564.9  # ms
        }
    
    def measure_performance(self, operation_name: str, execution_time: float):
        """パフォーマンス測定記録"""
        if operation_name not in self.timing_data:
            self.timing_data[operation_name] = []
        
        self.timing_data[operation_name].append(execution_time)
        
        # 目標値との比較
        if operation_name in self.targets:
            target = self.targets[operation_name]
            if execution_time > target:
                print(f"⚠️  {operation_name}: {execution_time:.1f}ms (目標: {target}ms)")
            else:
                print(f"✅ {operation_name}: {execution_time:.1f}ms (目標: {target}ms)")
    
    def get_performance_summary(self) -> Dict[str, Dict[str, float]]:
        """パフォーマンスサマリー取得"""
        summary = {}
        for operation, times in self.timing_data.items():
            summary[operation] = {
                'avg': np.mean(times),
                'max': np.max(times),
                'min': np.min(times),
                'target': self.targets.get(operation, 0)
            }
        return summary


if __name__ == "__main__":
    # テスト用の簡単な実行例
    print("基本指標計算エンジン初期化完了")
    
    # サンプルデータでテスト
    sample_data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='1min'),
        'open': np.random.randn(100).cumsum() + 150,
        'high': np.random.randn(100).cumsum() + 151,
        'low': np.random.randn(100).cumsum() + 149,
        'close': np.random.randn(100).cumsum() + 150
    })
    
    indicators = BaseIndicators()
    
    print("平均足計算テスト...")
    ha_result = indicators.calculate_heikin_ashi(sample_data)
    print(f"平均足データ: {len(ha_result)} rows")
    
    print("OsMA計算テスト...")
    osma_result = indicators.calculate_osma(sample_data)
    print(f"OsMAデータ: {len(osma_result)} rows")
    
    print("✅ 基本指標計算エンジンのテスト完了")