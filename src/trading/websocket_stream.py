"""
WebSocketストリーミング実装
OANDA v20 API WebSocket接続（デモ版含む）
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
import threading
import queue
import time


class OandaWebSocketStream:
    """OANDA WebSocketストリーミング"""
    
    def __init__(self, 
                 api_key: str = "demo-key",
                 account_id: str = "demo-account",
                 environment: str = "practice"):  # practice or trade
        
        self.api_key = api_key
        self.account_id = account_id
        self.environment = environment
        
        # WebSocket URL
        if environment == "practice":
            self.stream_url = "wss://stream-fxpractice.oanda.com"
        else:
            self.stream_url = "wss://stream-fxtrade.oanda.com"
        
        self.pricing_url = f"{self.stream_url}/v3/accounts/{account_id}/pricing/stream"
        
        # 接続管理
        self.websocket = None
        self.is_connected = False
        self.subscribers = []
        self.instruments = ["USD_JPY", "EUR_JPY", "EUR_USD"]
        
    def subscribe(self, callback: Callable):
        """データ受信コールバック登録"""
        self.subscribers.append(callback)
    
    async def connect(self):
        """WebSocket接続（デモ用は常にFalse）"""
        print("⚠️  WebSocket接続をスキップ（デモモード）")
        print(f"📡 実際の接続先: {self.pricing_url}")
        print("🔧 デモモードで代替データストリーミング開始")
        self.is_connected = False
    
    async def start_streaming(self):
        """ストリーミング開始"""
        await self.connect()
        
        if self.is_connected:
            # 実際のWebSocketストリーミング
            await self._real_streaming()
        else:
            # デモストリーミング
            await self._demo_streaming()
    
    async def _real_streaming(self):
        """実際のWebSocketストリーミング（未実装）"""
        print("🔧 実際のWebSocket実装は今後追加予定")
        print("📋 必要ライブラリ: pip install websockets")
        pass
    
    async def _demo_streaming(self):
        """デモストリーミング（WebSocket接続できない場合）"""
        import random
        
        print("🎮 デモストリーミング開始")
        
        # 基準価格
        base_prices = {
            "USD_JPY": 150.0,
            "EUR_JPY": 162.0,
            "EUR_USD": 1.065
        }
        
        current_prices = base_prices.copy()
        
        while True:
            for instrument in self.instruments:
                # ランダム価格変動
                change_rate = random.gauss(0, 0.001)  # 0.1%標準偏差
                current_prices[instrument] *= (1 + change_rate)
                
                # スプレッド設定
                spreads = {
                    "USD_JPY": 0.003,
                    "EUR_JPY": 0.005,
                    "EUR_USD": 0.00003
                }
                
                spread = spreads.get(instrument, 0.003)
                bid = current_prices[instrument] - spread/2
                ask = current_prices[instrument] + spread/2
                
                # OANDA形式の価格データ
                price_data = {
                    "type": "PRICE",
                    "time": datetime.utcnow().isoformat() + "Z",
                    "instrument": instrument,
                    "bids": [{"price": f"{bid:.5f}", "liquidity": 1000000}],
                    "asks": [{"price": f"{ask:.5f}", "liquidity": 1000000}],
                    "closeoutBid": f"{bid:.5f}",
                    "closeoutAsk": f"{ask:.5f}",
                    "status": "tradeable"
                }
                
                # 解析
                parsed_data = self._parse_price_data(price_data)
                
                # 全サブスクライバーに通知
                for callback in self.subscribers:
                    await self._safe_callback(callback, parsed_data)
            
            # 500ms待機（2Hz更新）
            await asyncio.sleep(0.5)
    
    def _parse_price_data(self, data: Dict) -> Dict:
        """OANDA価格データ解析"""
        instrument = data.get("instrument", "")
        
        # Bid/Ask価格取得
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        
        bid_price = float(bids[0]["price"]) if bids else 0.0
        ask_price = float(asks[0]["price"]) if asks else 0.0
        mid_price = (bid_price + ask_price) / 2
        
        return {
            "symbol": instrument.replace("_", ""),  # USD_JPY -> USDJPY
            "timestamp": data.get("time", datetime.utcnow().isoformat()),
            "bid": bid_price,
            "ask": ask_price,
            "mid": mid_price,
            "spread": ask_price - bid_price,
            "status": data.get("status", "unknown")
        }
    
    async def _safe_callback(self, callback: Callable, data: Dict):
        """安全なコールバック実行"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            print(f"❌ コールバックエラー: {e}")
    
    async def disconnect(self):
        """WebSocket切断"""
        self.is_connected = False
        print("🛑 WebSocket切断完了")


class StreamingDataCollector:
    """ストリーミングデータ収集・保存"""
    
    def __init__(self, output_file: str = "./data/streaming_data.json"):
        self.output_file = output_file
        self.data_buffer = []
        self.max_buffer_size = 1000
        
    async def on_price_data(self, price_data: Dict):
        """価格データ受信時の処理"""
        # タイムスタンプ追加
        price_data["received_at"] = datetime.now().isoformat()
        
        # バッファに追加
        self.data_buffer.append(price_data)
        
        # コンソール表示
        symbol = price_data["symbol"]
        bid = price_data["bid"]
        ask = price_data["ask"]
        spread = price_data["spread"]
        
        print(f"💹 {symbol}: Bid={bid:.5f}, Ask={ask:.5f}, "
              f"Spread={spread*10000:.1f}pips")
        
        # バッファサイズチェック
        if len(self.data_buffer) >= self.max_buffer_size:
            await self._flush_buffer()
    
    async def _flush_buffer(self):
        """バッファをファイルに書き出し"""
        if not self.data_buffer:
            return
        
        try:
            with open(self.output_file, "a") as f:
                for data in self.data_buffer:
                    f.write(json.dumps(data) + "\n")
            
            print(f"💾 {len(self.data_buffer)}件のデータを保存")
            self.data_buffer = []
            
        except Exception as e:
            print(f"❌ データ保存エラー: {e}")


class StreamingTradingEngine:
    """ストリーミング対応取引エンジン"""
    
    def __init__(self):
        self.websocket_stream = OandaWebSocketStream()
        self.data_collector = StreamingDataCollector()
        self.is_running = False
        
        # 価格データキャッシュ
        self.latest_prices = {}
        self.price_history = {}
        
    async def start(self):
        """エンジン開始"""
        print("🚀 ストリーミング取引エンジン開始")
        
        # データ収集コールバック登録
        self.websocket_stream.subscribe(self._on_price_update)
        self.websocket_stream.subscribe(self.data_collector.on_price_data)
        
        # ストリーミング開始
        self.is_running = True
        await self.websocket_stream.start_streaming()
    
    async def _on_price_update(self, price_data: Dict):
        """価格更新時の処理"""
        symbol = price_data["symbol"]
        
        # 最新価格更新
        self.latest_prices[symbol] = price_data
        
        # 価格履歴更新
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append(price_data)
        
        # 過去1時間分のみ保持
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.price_history[symbol] = [
            p for p in self.price_history[symbol]
            if datetime.fromisoformat(p["received_at"]) > cutoff_time
        ]
        
        # 取引ロジック（今後実装）
        await self._check_trading_signals(symbol, price_data)
    
    async def _check_trading_signals(self, symbol: str, price_data: Dict):
        """取引シグナルチェック"""
        # TODO: メモベースストラテジーと連携
        pass
    
    async def stop(self):
        """エンジン停止"""
        self.is_running = False
        await self.websocket_stream.disconnect()
        
        # 残りデータを保存
        await self.data_collector._flush_buffer()
        print("🛑 ストリーミング取引エンジン停止")


async def demo_streaming():
    """ストリーミングデモ"""
    print("=" * 60)
    print("🎯 WebSocketストリーミング デモ")
    print("=" * 60)
    
    engine = StreamingTradingEngine()
    
    try:
        # 10秒間ストリーミング
        await asyncio.wait_for(engine.start(), timeout=10.0)
    except asyncio.TimeoutError:
        print("⏰ デモ時間終了")
    finally:
        await engine.stop()


def main():
    """メイン実行"""
    asyncio.run(demo_streaming())


if __name__ == "__main__":
    main()