"""
素材DAG - データ収集層（階層0）
生データの収集と正規化を行う

PKG ID範囲: [timeframe][period][currency]^0-[001-099]
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import time
from datetime import datetime

@dataclass
class MarketTick:
    """市場ティックデータ"""
    timestamp: datetime
    symbol: str
    bid: float
    ask: float
    volume: float = 0.0

@dataclass 
class OHLCVData:
    """OHLCV価格データ"""
    timestamp: datetime
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class DataCollectionLayer:
    """
    階層0: データ収集層
    
    責務:
    - ティックデータの受信
    - OHLCV データの生成
    - データ品質チェック
    - 正規化処理
    """
    
    def __init__(self, symbol: str = "USDJPY"):
        self.symbol = symbol
        self.currency_code = self._get_currency_code(symbol)
    
    def _get_currency_code(self, symbol: str) -> int:
        """通貨ペアコードを取得"""
        currency_map = {
            "USDJPY": 1,
            "EURUSD": 2, 
            "EURJPY": 3,
            "GBPJPY": 4
        }
        return currency_map.get(symbol, 1)
    
    def _get_timeframe_code(self, timeframe: str) -> int:
        """時間足コードを取得"""
        timeframe_map = {
            "M1": 1, "1M": 1,
            "M5": 2, "5M": 2,
            "M15": 3, "15M": 3,
            "M30": 4, "30M": 4,
            "H1": 5, "1H": 5,
            "H4": 6, "4H": 6
        }
        return timeframe_map.get(timeframe, 3)
    
    def collect_current_price(self, tick: MarketTick) -> Dict[str, Any]:
        """
        391^0-001: 現在価格収集
        
        Args:
            tick: 市場ティックデータ
            
        Returns:
            Dict: PKG形式のデータ
        """
        tf_code = 9  # 共通
        period_code = 9  # 共通
        pkg_id = f"{tf_code}{period_code}{self.currency_code}^0-001"
        
        return {
            pkg_id: tick.bid,  # BID価格を使用
            "timestamp": tick.timestamp,
            "symbol": tick.symbol,
            "quality_score": self._assess_data_quality(tick)
        }
    
    def collect_ohlcv(self, ohlcv: OHLCVData) -> Dict[str, Any]:
        """
        各時間足のOHLCV収集
        
        Args:
            ohlcv: OHLCV価格データ
            
        Returns:
            Dict: 複数PKG IDのデータ
        """
        tf_code = self._get_timeframe_code(ohlcv.timeframe)
        period_code = 9  # 共通
        
        base_id_template = f"{tf_code}{period_code}{self.currency_code}^0"
        
        return {
            f"{base_id_template}-002": ohlcv.open,    # 始値
            f"{base_id_template}-003": ohlcv.high,    # 高値  
            f"{base_id_template}-004": ohlcv.low,     # 安値
            f"{base_id_template}-005": ohlcv.close,   # 終値
            f"{base_id_template}-006": ohlcv.volume,  # 出来高
            "timestamp": ohlcv.timestamp,
            "symbol": ohlcv.symbol,
            "timeframe": ohlcv.timeframe,
            "is_closed": True  # バー確定フラグ
        }
    
    def collect_historical_data(self, historical_data: list) -> Dict[str, Any]:
        """
        ヒストリカルデータの一括収集
        
        Args:
            historical_data: 過去データのリスト
            
        Returns:
            Dict: 時系列データ
        """
        collected_data = {}
        
        for data_point in historical_data:
            if isinstance(data_point, OHLCVData):
                point_data = self.collect_ohlcv(data_point)
                collected_data.update(point_data)
        
        return collected_data
    
    def _assess_data_quality(self, tick: MarketTick) -> float:
        """
        データ品質スコアの評価
        
        Args:
            tick: ティックデータ
            
        Returns:
            float: 品質スコア（0.0-1.0）
        """
        quality_score = 1.0
        
        # スプレッドチェック
        if tick.ask > 0 and tick.bid > 0:
            spread = tick.ask - tick.bid
            relative_spread = spread / tick.bid
            
            # 異常なスプレッドの検出
            if relative_spread > 0.01:  # 1%以上のスプレッド
                quality_score *= 0.5
            elif relative_spread > 0.005:  # 0.5%以上のスプレッド
                quality_score *= 0.8
        else:
            quality_score = 0.0  # 無効な価格
        
        # タイムスタンプの新しさ
        if tick.timestamp:
            time_diff = datetime.now() - tick.timestamp
            if time_diff.total_seconds() > 60:  # 1分以上古い
                quality_score *= 0.7
        
        return quality_score
    
    def validate_data_integrity(self, data: Dict[str, Any]) -> bool:
        """
        データ整合性の検証
        
        Args:
            data: 収集されたデータ
            
        Returns:
            bool: 整合性OK/NG
        """
        required_fields = ["timestamp", "symbol"]
        
        # 必須フィールドの確認
        for field in required_fields:
            if field not in data:
                return False
        
        # PKG IDフォーマットの確認
        import re
        pkg_pattern = re.compile(r'^\d\d\d\^0-\d{3}$')
        
        pkg_ids = [key for key in data.keys() if pkg_pattern.match(key)]
        if not pkg_ids:
            return False
        
        # 価格データの妥当性
        for pkg_id in pkg_ids:
            value = data[pkg_id]
            if not isinstance(value, (int, float)) or value <= 0:
                return False
        
        return True

# データ収集の便利関数
def create_sample_tick(symbol: str = "USDJPY", price: float = 110.0) -> MarketTick:
    """テスト用のサンプルティック作成"""
    return MarketTick(
        timestamp=datetime.now(),
        symbol=symbol,
        bid=price,
        ask=price + 0.003,  # 3pipsスプレッド
        volume=1000.0
    )

def create_sample_ohlcv(symbol: str = "USDJPY", timeframe: str = "15M") -> OHLCVData:
    """テスト用のサンプルOHLCV作成"""
    base_price = 110.0
    return OHLCVData(
        timestamp=datetime.now(),
        symbol=symbol,
        timeframe=timeframe,
        open=base_price,
        high=base_price + 0.05,
        low=base_price - 0.03,
        close=base_price + 0.02,
        volume=5000.0
    )