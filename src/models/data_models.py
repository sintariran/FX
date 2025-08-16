#!/usr/bin/env python3
"""
統一データモデル定義

レビュー指摘への対応:
- 重複データクラスの解消
- Direction Enumの統一
- TimeFrameの一貫した表現
- 型安全性の向上
- 全システムで共通利用可能な統一モデル

統一原則:
1. 同じデータ構造は1箇所で定義
2. Enumによる型安全な値管理
3. 明確な命名規則
4. 後方互換性の維持
"""

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
import logging

# ========== 基本Enum定義 ==========

class TimeFrame(IntEnum):
    """
    時間足定義 (統一版)
    
    レビュー指摘: TimeFrameの一貫した表現
    分単位で統一（H1→M60, H4→M240）
    """
    M1 = 1      # 1分足
    M5 = 5      # 5分足  
    M15 = 15    # 15分足
    M30 = 30    # 30分足
    M60 = 60    # 1時間足（旧H1）
    M240 = 240  # 4時間足（旧H4）
    
    @classmethod
    def from_legacy(cls, legacy_value: Union[str, int]) -> 'TimeFrame':
        """レガシー値からの変換（後方互換性）"""
        if isinstance(legacy_value, str):
            mapping = {
                'M1': cls.M1, '1min': cls.M1,
                'M5': cls.M5, '5min': cls.M5,
                'M15': cls.M15, '15min': cls.M15,
                'M30': cls.M30, '30min': cls.M30,
                'H1': cls.M60, '1H': cls.M60, '60min': cls.M60,
                'H4': cls.M240, '4H': cls.M240, '240min': cls.M240
            }
            return mapping.get(legacy_value, cls.M15)
        elif isinstance(legacy_value, int):
            # 直接対応
            try:
                return cls(legacy_value)
            except ValueError:
                # PKG ID体系との対応
                mapping = {1: cls.M1, 2: cls.M5, 3: cls.M15, 4: cls.M30, 5: cls.M60, 6: cls.M240}
                return mapping.get(legacy_value, cls.M15)
        return cls.M15
    
    def to_pkg_id_value(self) -> int:
        """PKG ID体系用の値に変換"""
        mapping = {self.M1: 1, self.M5: 2, self.M15: 3, self.M30: 4, self.M60: 5, self.M240: 6}
        return mapping.get(self, 3)
    
    def to_minutes(self) -> int:
        """分単位の値を返す"""
        return self.value
    
    def __str__(self) -> str:
        return self.name

class Direction(IntEnum):
    """
    方向定義 (統一版)
    
    レビュー指摘: Direction Enumの統一
    全システムで一貫した方向表現
    """
    NEUTRAL = 0  # 中立
    UP = 1       # 上方向（ロング）
    DOWN = 2     # 下方向（ショート）
    
    # エイリアス（後方互換性）
    LONG = UP
    SHORT = DOWN
    
    @classmethod
    def from_legacy(cls, legacy_value: Union[str, int, float]) -> 'Direction':
        """レガシー値からの変換"""
        if isinstance(legacy_value, (int, float)):
            if legacy_value > 0:
                return cls.UP
            elif legacy_value < 0:
                return cls.DOWN
            else:
                return cls.NEUTRAL
        elif isinstance(legacy_value, str):
            mapping = {
                'UP': cls.UP, 'LONG': cls.UP, 'BUY': cls.UP, '1': cls.UP,
                'DOWN': cls.DOWN, 'SHORT': cls.DOWN, 'SELL': cls.DOWN, '2': cls.DOWN,
                'NEUTRAL': cls.NEUTRAL, 'NONE': cls.NEUTRAL, '0': cls.NEUTRAL
            }
            return mapping.get(legacy_value.upper(), cls.NEUTRAL)
        return cls.NEUTRAL
    
    def to_trading_direction(self) -> int:
        """取引システム用の数値に変換"""
        return self.value
    
    def __str__(self) -> str:
        return self.name

class Currency(IntEnum):
    """通貨ペア定義（PKG ID体系対応）"""
    USDJPY = 1
    EURUSD = 2  
    EURJPY = 3
    
    def __str__(self) -> str:
        return self.name

class Period(IntEnum):
    """周期定義（TSML周期、PKG ID体系対応）"""
    COMMON = 9      # 共通（周期なし）
    PERIOD_10 = 10
    PERIOD_15 = 15
    PERIOD_30 = 30
    PERIOD_45 = 45
    PERIOD_60 = 60
    PERIOD_90 = 90
    PERIOD_180 = 180

# ========== 統一データクラス ==========

@dataclass
class PriceData:
    """
    価格データの統一定義
    
    base_indicators.py と key_concepts.py の重複を解消
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None
    
    def __post_init__(self):
        """データ検証"""
        if self.high < max(self.open, self.close):
            logging.warning(f"高値が始値/終値より低い: {self}")
        if self.low > min(self.open, self.close):
            logging.warning(f"安値が始値/終値より高い: {self}")
    
    @property
    def typical_price(self) -> float:
        """典型価格 (HLC/3)"""
        return (self.high + self.low + self.close) / 3
    
    @property
    def price_range(self) -> float:
        """価格レンジ (高値-安値)"""
        return self.high - self.low
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }

@dataclass
class HeikinAshiData:
    """
    平均足データの統一定義
    
    Direction Enum統一対応
    """
    timestamp: datetime
    ha_open: float
    ha_high: float
    ha_low: float
    ha_close: float
    direction: Direction  # 統一されたDirection Enum
    is_reversal: bool = False
    strength: Optional[float] = None
    
    @classmethod
    def from_price_data(cls, price_data: PriceData, 
                       prev_ha: Optional['HeikinAshiData'] = None) -> 'HeikinAshiData':
        """価格データから平均足を計算"""
        # 平均足計算
        ha_close = (price_data.open + price_data.high + price_data.low + price_data.close) / 4
        
        if prev_ha:
            ha_open = (prev_ha.ha_open + prev_ha.ha_close) / 2
        else:
            ha_open = (price_data.open + price_data.close) / 2
        
        ha_high = max(price_data.high, ha_open, ha_close)
        ha_low = min(price_data.low, ha_open, ha_close)
        
        # 方向判定
        direction = Direction.UP if ha_close > ha_open else Direction.DOWN
        
        # 転換判定
        is_reversal = False
        if prev_ha:
            prev_direction = Direction.UP if prev_ha.ha_close > prev_ha.ha_open else Direction.DOWN
            is_reversal = (direction != prev_direction)
        
        return cls(
            timestamp=price_data.timestamp,
            ha_open=ha_open,
            ha_high=ha_high,
            ha_low=ha_low,
            ha_close=ha_close,
            direction=direction,
            is_reversal=is_reversal
        )
    
    @property
    def body_size(self) -> float:
        """実体の大きさ"""
        return abs(self.ha_close - self.ha_open)
    
    @property
    def upper_shadow(self) -> float:
        """上ヒゲの長さ"""
        return self.ha_high - max(self.ha_open, self.ha_close)
    
    @property
    def lower_shadow(self) -> float:
        """下ヒゲの長さ"""
        return min(self.ha_open, self.ha_close) - self.ha_low

@dataclass
class MarketData:
    """
    市場データの統一定義
    
    複数箇所の重複定義を統合
    PriceData + HeikinAshiData + 追加指標を含む完全版
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    # 平均足データ（オプション）
    heikin_ashi_open: Optional[float] = None
    heikin_ashi_high: Optional[float] = None
    heikin_ashi_low: Optional[float] = None
    heikin_ashi_close: Optional[float] = None
    
    # 追加指標（オプション）
    sma_20: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    macd: Optional[float] = None
    signal: Optional[float] = None
    osma: Optional[float] = None
    
    # 判定結果（オプション）
    ha_direction: Optional[Direction] = None
    trend_direction: Optional[Direction] = None
    
    # メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初期化後処理"""
        # 平均足方向の自動計算
        if (self.heikin_ashi_open is not None and 
            self.heikin_ashi_close is not None and 
            self.ha_direction is None):
            self.ha_direction = (Direction.UP if self.heikin_ashi_close > self.heikin_ashi_open 
                               else Direction.DOWN)
    
    @classmethod
    def from_price_data(cls, price_data: PriceData, **kwargs) -> 'MarketData':
        """PriceDataから変換"""
        return cls(
            timestamp=price_data.timestamp,
            open=price_data.open,
            high=price_data.high,
            low=price_data.low,
            close=price_data.close,
            volume=price_data.volume or 0.0,
            **kwargs
        )
    
    @property
    def price_data(self) -> PriceData:
        """PriceDataとして取得"""
        return PriceData(
            timestamp=self.timestamp,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume
        )
    
    @property
    def heikin_ashi_data(self) -> Optional[HeikinAshiData]:
        """HeikinAshiDataとして取得"""
        if (self.heikin_ashi_open is not None and 
            self.heikin_ashi_close is not None):
            return HeikinAshiData(
                timestamp=self.timestamp,
                ha_open=self.heikin_ashi_open,
                ha_high=self.heikin_ashi_high or self.heikin_ashi_close,
                ha_low=self.heikin_ashi_low or self.heikin_ashi_open,
                ha_close=self.heikin_ashi_close,
                direction=self.ha_direction or Direction.NEUTRAL
            )
        return None
    
    def calculate_heikin_ashi(self, prev_bar: Optional['MarketData'] = None) -> None:
        """平均足を計算して設定"""
        ha_close = (self.open + self.high + self.low + self.close) / 4
        
        if prev_bar and prev_bar.heikin_ashi_open is not None:
            ha_open = (prev_bar.heikin_ashi_open + prev_bar.heikin_ashi_close) / 2
        else:
            ha_open = (self.open + self.close) / 2
        
        ha_high = max(self.high, ha_open, ha_close)
        ha_low = min(self.low, ha_open, ha_close)
        
        self.heikin_ashi_open = ha_open
        self.heikin_ashi_high = ha_high
        self.heikin_ashi_low = ha_low
        self.heikin_ashi_close = ha_close
        self.ha_direction = Direction.UP if ha_close > ha_open else Direction.DOWN

@dataclass
class IndicatorData:
    """
    テクニカル指標データの統一定義
    """
    timestamp: datetime
    timeframe: TimeFrame
    
    # 移動平均系
    sma_values: Dict[int, float] = field(default_factory=dict)  # {期間: 値}
    ema_values: Dict[int, float] = field(default_factory=dict)  # {期間: 値}
    
    # オシレーター系
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    osma: Optional[float] = None
    
    # RSI系
    rsi_14: Optional[float] = None
    
    # ボリンジャーバンド
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    
    # カスタム指標
    custom_indicators: Dict[str, float] = field(default_factory=dict)
    
    def get_sma(self, period: int) -> Optional[float]:
        """指定期間のSMAを取得"""
        return self.sma_values.get(period)
    
    def set_sma(self, period: int, value: float) -> None:
        """SMAを設定"""
        self.sma_values[period] = value
    
    def get_ema(self, period: int) -> Optional[float]:
        """指定期間のEMAを取得"""
        return self.ema_values.get(period)
    
    def set_ema(self, period: int, value: float) -> None:
        """EMAを設定"""
        self.ema_values[period] = value

# ========== PKG関連データクラス ==========

@dataclass
class PKGId:
    """PKG ID体系（統一版）"""
    timeframe: TimeFrame
    period: Period
    currency: Currency
    layer: int
    sequence: int
    
    def __str__(self) -> str:
        tf_value = self.timeframe.to_pkg_id_value()
        return f"{tf_value}{self.period.value}{self.currency.value}^{self.layer}-{self.sequence}"
    
    @classmethod
    def parse(cls, pkg_id_str: str) -> 'PKGId':
        """PKG ID文字列をパース"""
        try:
            base, layer_seq = pkg_id_str.split('^')
            layer, sequence = layer_seq.split('-')
            
            # TimeFrameの変換
            tf_value = int(base[0])
            timeframe = TimeFrame.from_legacy(tf_value)
            
            period = Period(int(base[1]))
            currency = Currency(int(base[2]))
            
            return cls(timeframe, period, currency, int(layer), int(sequence))
        except Exception as e:
            raise ValueError(f"Invalid PKG ID format: {pkg_id_str}") from e

@dataclass
class OperationSignal:
    """オペレーション信号（統一版）"""
    pkg_id: PKGId
    signal_type: str
    direction: Direction  # 統一されたDirection
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def direction_value(self) -> int:
        """レガシーシステム用の方向値"""
        return self.direction.to_trading_direction()

# ========== 変換ユーティリティ ==========

class DataModelConverter:
    """データモデル変換ユーティリティ"""
    
    @staticmethod
    def convert_legacy_direction(value: Any) -> Direction:
        """レガシー方向値を統一Directionに変換"""
        return Direction.from_legacy(value)
    
    @staticmethod
    def convert_legacy_timeframe(value: Any) -> TimeFrame:
        """レガシー時間足値を統一TimeFrameに変換"""
        return TimeFrame.from_legacy(value)
    
    @staticmethod
    def migrate_heikin_ashi_data(legacy_data: Dict[str, Any]) -> HeikinAshiData:
        """レガシー平均足データを統一形式に変換"""
        direction_value = legacy_data.get('direction', 0)
        direction = Direction.from_legacy(direction_value)
        
        return HeikinAshiData(
            timestamp=legacy_data['timestamp'],
            ha_open=legacy_data['ha_open'],
            ha_high=legacy_data['ha_high'],
            ha_low=legacy_data['ha_low'],
            ha_close=legacy_data['ha_close'],
            direction=direction
        )
    
    @staticmethod
    def create_market_data_from_dict(data: Dict[str, Any]) -> MarketData:
        """辞書からMarketDataを作成"""
        return MarketData(
            timestamp=data['timestamp'],
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            volume=data.get('volume', 0.0),
            heikin_ashi_open=data.get('heikin_ashi_open'),
            heikin_ashi_high=data.get('heikin_ashi_high'),
            heikin_ashi_low=data.get('heikin_ashi_low'),
            heikin_ashi_close=data.get('heikin_ashi_close'),
            ha_direction=DataModelConverter.convert_legacy_direction(
                data.get('ha_direction', 0)
            )
        )

# ========== テスト・検証 ==========

def validate_data_model_consistency():
    """データモデルの一貫性検証"""
    print("🔍 統一データモデル検証")
    
    # TimeFrame変換テスト
    legacy_timeframes = ['M1', 'M5', 'H1', 'H4', 1, 2, 5, 6]
    for legacy in legacy_timeframes:
        converted = TimeFrame.from_legacy(legacy)
        print(f"  TimeFrame変換: {legacy} → {converted} ({converted.to_minutes()}分)")
    
    # Direction変換テスト
    legacy_directions = [1, -1, 0, 'UP', 'down', 2]
    for legacy in legacy_directions:
        converted = Direction.from_legacy(legacy)
        print(f"  Direction変換: {legacy} → {converted}")
    
    # PKG ID変換テスト
    test_pkg_ids = ["391^2-126", "591^0-AA001", "191^4-999"]
    for pkg_id_str in test_pkg_ids:
        try:
            parsed = PKGId.parse(pkg_id_str)
            print(f"  PKG ID解析: {pkg_id_str} → {parsed}")
        except Exception as e:
            print(f"  PKG ID解析エラー: {pkg_id_str} → {e}")
    
    print("✅ データモデル検証完了")

if __name__ == "__main__":
    validate_data_model_consistency()