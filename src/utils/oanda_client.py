"""
OANDA API クライアント
デモ口座での価格データ取得とテスト取引用
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time
import requests
import json
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()


@dataclass
class OandaConfig:
    """OANDA設定"""
    api_key: str
    account_id: str
    environment: str = "practice"  # practice or live
    
    @property
    def base_url(self) -> str:
        if self.environment == "practice":
            return "https://api-fxpractice.oanda.com"
        else:
            return "https://api-fxtrade.oanda.com"
    
    @property
    def stream_url(self) -> str:
        if self.environment == "practice":
            return "https://stream-fxpractice.oanda.com"
        else:
            return "https://stream-fxtrade.oanda.com"


class OandaClient:
    """
    OANDA API クライアント
    価格データ取得、口座情報取得、注文実行等
    """
    
    def __init__(self, config: Optional[OandaConfig] = None):
        if config is None:
            # 環境変数から設定読み込み
            self.config = OandaConfig(
                api_key=os.getenv("OANDA_API_KEY", ""),
                account_id=os.getenv("OANDA_ACCOUNT_ID", ""),
                environment=os.getenv("OANDA_ENV", "practice")
            )
        else:
            self.config = config
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        })
        
        # レート制限対応
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms間隔
    
    def _wait_for_rate_limit(self):
        """レート制限対応の待機"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """API リクエスト実行"""
        self._wait_for_rate_limit()
        
        url = f"{self.config.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        
        if response.status_code != 200:
            raise Exception(f"OANDA API Error: {response.status_code} - {response.text}")
        
        return response.json()
    
    def get_account_info(self) -> Dict:
        """口座情報取得"""
        endpoint = f"/v3/accounts/{self.config.account_id}"
        return self._make_request("GET", endpoint)
    
    def get_instruments(self) -> List[Dict]:
        """取引可能通貨ペア一覧取得"""
        endpoint = f"/v3/accounts/{self.config.account_id}/instruments"
        response = self._make_request("GET", endpoint)
        return response.get("instruments", [])
    
    def get_historical_data(self, 
                           instrument: str = "USD_JPY",
                           granularity: str = "M1",  # M1, M5, M15, M30, H1, H4
                           count: int = 5000,
                           start_time: Optional[str] = None,
                           end_time: Optional[str] = None) -> pd.DataFrame:
        """
        ヒストリカルデータ取得
        
        Args:
            instrument: 通貨ペア（USD_JPY, EUR_USD等）
            granularity: 時間足（M1, M5, M15, M30, H1, H4）
            count: 取得件数（最大5000）
            start_time: 開始時刻（ISO8601形式）
            end_time: 終了時刻（ISO8601形式）
        """
        endpoint = f"/v3/instruments/{instrument}/candles"
        
        params = {
            "granularity": granularity,
            "price": "MBA"  # Mid, Bid, Ask
        }
        
        if start_time and end_time:
            params["from"] = start_time
            params["to"] = end_time
        else:
            params["count"] = count
        
        response = self._make_request("GET", endpoint, params=params)
        candles = response.get("candles", [])
        
        # DataFrameに変換
        data = []
        for candle in candles:
            if candle["complete"]:  # 確定済みのみ
                mid = candle["mid"]
                data.append({
                    "timestamp": pd.to_datetime(candle["time"]),
                    "open": float(mid["o"]),
                    "high": float(mid["h"]),
                    "low": float(mid["l"]),
                    "close": float(mid["c"]),
                    "volume": int(candle["volume"])
                })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)
        
        return df
    
    def get_multi_timeframe_data(self, 
                                 instrument: str = "USD_JPY",
                                 timeframes: List[str] = ["M1", "M5", "M15", "M30"],
                                 days_back: int = 30) -> Dict[str, pd.DataFrame]:
        """
        マルチタイムフレームデータ一括取得
        
        Args:
            instrument: 通貨ペア
            timeframes: 時間足リスト
            days_back: 何日前からのデータか
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        
        data = {}
        for tf in timeframes:
            print(f"取得中: {instrument} {tf}...")
            
            # 時間足に応じて取得件数調整
            if tf == "M1":
                count = min(1440 * days_back, 5000)  # 1日1440分
            elif tf == "M5":
                count = min(288 * days_back, 5000)   # 1日288本
            elif tf == "M15":
                count = min(96 * days_back, 5000)    # 1日96本
            elif tf == "M30":
                count = min(48 * days_back, 5000)    # 1日48本
            else:
                count = 5000
            
            df = self.get_historical_data(
                instrument=instrument,
                granularity=tf,
                count=count
            )
            
            if not df.empty:
                data[tf] = df
                print(f"✅ {tf}: {len(df)} rows取得")
            else:
                print(f"❌ {tf}: データ取得失敗")
        
        return data
    
    def get_current_price(self, instruments: List[str] = ["USD_JPY"]) -> Dict:
        """現在価格取得"""
        instruments_str = ",".join(instruments)
        endpoint = f"/v3/accounts/{self.config.account_id}/pricing"
        params = {"instruments": instruments_str}
        
        response = self._make_request("GET", endpoint, params=params)
        
        prices = {}
        for price in response.get("prices", []):
            instrument = price["instrument"]
            prices[instrument] = {
                "bid": float(price["bids"][0]["price"]),
                "ask": float(price["asks"][0]["price"]),
                "time": price["time"]
            }
        
        return prices
    
    def place_order(self, 
                    instrument: str,
                    units: int,  # 正数=買い、負数=売り
                    order_type: str = "MARKET",
                    stop_loss_price: Optional[float] = None,
                    take_profit_price: Optional[float] = None) -> Dict:
        """
        注文実行（デモ口座でのテスト用）
        
        Args:
            instrument: 通貨ペア
            units: 数量（正数=買い、負数=売り）
            order_type: 注文タイプ（MARKET, LIMIT等）
            stop_loss_price: 損切り価格
            take_profit_price: 利益確定価格
        """
        if self.config.environment != "practice":
            print("⚠️  本番環境での注文は実装時に要注意")
        
        endpoint = f"/v3/accounts/{self.config.account_id}/orders"
        
        order_spec = {
            "type": order_type,
            "instrument": instrument,
            "units": str(units)
        }
        
        # ストップロス設定
        if stop_loss_price:
            order_spec["stopLossOnFill"] = {
                "price": str(stop_loss_price)
            }
        
        # テイクプロフィット設定  
        if take_profit_price:
            order_spec["takeProfitOnFill"] = {
                "price": str(take_profit_price)
            }
        
        data = {"order": order_spec}
        
        return self._make_request("POST", endpoint, json=data)
    
    def get_positions(self) -> List[Dict]:
        """現在のポジション一覧取得"""
        endpoint = f"/v3/accounts/{self.config.account_id}/positions"
        response = self._make_request("GET", endpoint)
        return response.get("positions", [])
    
    def close_position(self, instrument: str, side: str = "ALL") -> Dict:
        """
        ポジション決済
        
        Args:
            instrument: 通貨ペア
            side: LONG, SHORT, ALL
        """
        endpoint = f"/v3/accounts/{self.config.account_id}/positions/{instrument}/close"
        
        data = {}
        if side in ["LONG", "ALL"]:
            data["longUnits"] = "ALL"
        if side in ["SHORT", "ALL"]:
            data["shortUnits"] = "ALL"
        
        return self._make_request("PUT", endpoint, json=data)


class DataCollector:
    """
    データ収集・保存クラス
    ヒストリカルデータの取得と永続化
    """
    
    def __init__(self, oanda_client: OandaClient, data_dir: str = "./data/historical"):
        self.oanda = oanda_client
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def collect_and_save_data(self, 
                              instruments: List[str] = ["USD_JPY"],
                              timeframes: List[str] = ["M1", "M5", "M15", "M30"],
                              days_back: int = 30):
        """
        データ収集・保存実行
        """
        for instrument in instruments:
            print(f"\n📊 {instrument} データ収集開始...")
            
            # マルチタイムフレームデータ取得
            data = self.oanda.get_multi_timeframe_data(
                instrument=instrument,
                timeframes=timeframes,
                days_back=days_back
            )
            
            # 保存
            for tf, df in data.items():
                if not df.empty:
                    filename = f"{instrument}_{tf}_{days_back}days.csv"
                    filepath = os.path.join(self.data_dir, filename)
                    df.to_csv(filepath)
                    print(f"💾 保存: {filepath} ({len(df)} rows)")
            
            print(f"✅ {instrument} データ収集完了")
    
    def load_saved_data(self, 
                        instrument: str = "USD_JPY",
                        timeframes: List[str] = ["M1", "M5", "M15", "M30"],
                        days_back: int = 30) -> Dict[str, pd.DataFrame]:
        """
        保存済みデータ読み込み
        """
        data = {}
        for tf in timeframes:
            filename = f"{instrument}_{tf}_{days_back}days.csv"
            filepath = os.path.join(self.data_dir, filename)
            
            if os.path.exists(filepath):
                df = pd.read_csv(filepath, index_col=0, parse_dates=True)
                data[tf] = df
                print(f"📂 読み込み: {filepath} ({len(df)} rows)")
            else:
                print(f"❌ ファイルなし: {filepath}")
        
        return data


if __name__ == "__main__":
    # テスト実行
    print("🚀 OANDA APIクライアント テスト開始")
    
    # 設定確認
    api_key = os.getenv("OANDA_API_KEY")
    if not api_key:
        print("⚠️  環境変数 OANDA_API_KEY が設定されていません")
        print("   .env ファイルを作成して設定してください")
        exit(1)
    
    # クライアント初期化
    client = OandaClient()
    
    try:
        # 口座情報テスト
        print("\n📋 口座情報取得テスト...")
        account_info = client.get_account_info()
        print(f"✅ 口座ID: {account_info['account']['id']}")
        print(f"✅ 通貨: {account_info['account']['currency']}")
        print(f"✅ 残高: {account_info['account']['balance']}")
        
        # 現在価格テスト
        print("\n💱 現在価格取得テスト...")
        prices = client.get_current_price(["USD_JPY", "EUR_USD"])
        for instrument, price in prices.items():
            print(f"✅ {instrument}: Bid={price['bid']}, Ask={price['ask']}")
        
        # 少量のヒストリカルデータテスト
        print("\n📈 ヒストリカルデータ取得テスト...")
        df = client.get_historical_data("USD_JPY", "M5", count=10)
        print(f"✅ データ取得: {len(df)} rows")
        print(df.head())
        
        print("\n✅ 全テスト完了！OANDA API接続成功")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        print("API設定を確認してください")