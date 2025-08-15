"""
リアルタイム取引エンジン
Week 3: 実際の取引システム実装
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import threading
import time
import queue


class MarketDataStream:
    """マーケットデータストリーミング"""
    
    def __init__(self, symbols: List[str] = ["USDJPY", "EURJPY"]):
        self.symbols = symbols
        self.subscribers = []
        self.is_running = False
        self.data_queue = queue.Queue()
        
    def subscribe(self, callback: Callable):
        """データ受信時のコールバック登録"""
        self.subscribers.append(callback)
    
    def start_stream(self):
        """ストリーミング開始"""
        self.is_running = True
        
        # 別スレッドでデータ生成（実際のAPIではWebSocket接続）
        thread = threading.Thread(target=self._generate_market_data)
        thread.daemon = True
        thread.start()
        
        print("📡 マーケットデータストリーミング開始")
    
    def stop_stream(self):
        """ストリーミング停止"""
        self.is_running = False
        print("🛑 マーケットデータストリーミング停止")
    
    def _generate_market_data(self):
        """市場データ生成（デモ用）"""
        import random
        
        # 基準価格
        base_prices = {
            "USDJPY": 150.0,
            "EURJPY": 162.0,
            "EURUSD": 1.065,
            "GBPJPY": 185.0
        }
        
        current_prices = base_prices.copy()
        
        while self.is_running:
            for symbol in self.symbols:
                # ランダムな価格変動
                change = random.gauss(0, 0.001)
                current_prices[symbol] *= (1 + change)
                
                # マーケットデータ作成
                tick_data = {
                    'symbol': symbol,
                    'timestamp': datetime.now().isoformat(),
                    'bid': current_prices[symbol] * 0.9998,
                    'ask': current_prices[symbol] * 1.0002,
                    'mid': current_prices[symbol],
                    'volume': random.randint(100, 1000)
                }
                
                # 全サブスクライバーに通知
                for callback in self.subscribers:
                    try:
                        callback(tick_data)
                    except Exception as e:
                        print(f"❌ コールバックエラー: {e}")
            
            # 1秒待機（実際は瞬時）
            time.sleep(1.0)


class Position:
    """ポジション管理"""
    
    def __init__(self, symbol: str, direction: int, size: float, 
                 entry_price: float, entry_time: str):
        self.symbol = symbol
        self.direction = direction  # 1: 買い, 2: 売り
        self.size = size
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.current_pnl = 0.0
        self.is_open = True
        
    def update_pnl(self, current_price: float):
        """未実現損益更新"""
        if self.direction == 1:  # 買い
            self.current_pnl = (current_price - self.entry_price) * self.size
        else:  # 売り
            self.current_pnl = (self.entry_price - current_price) * self.size
        
        return self.current_pnl


class RiskManager:
    """リスク管理システム"""
    
    def __init__(self, max_exposure: float = 100000,
                 max_positions: int = 5,
                 max_daily_loss: float = 50000):
        self.max_exposure = max_exposure
        self.max_positions = max_positions  
        self.max_daily_loss = max_daily_loss
        self.daily_pnl = 0.0
        self.start_date = datetime.now().date()
        
    def check_entry_allowed(self, symbol: str, size: float, 
                           current_positions: List[Position]) -> bool:
        """エントリー可否判定"""
        
        # 日付変更チェック
        if datetime.now().date() != self.start_date:
            self.daily_pnl = 0.0
            self.start_date = datetime.now().date()
        
        # 1. ポジション数制限
        if len(current_positions) >= self.max_positions:
            print(f"⚠️  最大ポジション数制限: {self.max_positions}")
            return False
        
        # 2. エクスポージャー制限
        total_exposure = sum(abs(pos.size * pos.entry_price) 
                           for pos in current_positions)
        if total_exposure + size > self.max_exposure:
            print(f"⚠️  最大エクスポージャー制限: ¥{self.max_exposure:,.0f}")
            return False
        
        # 3. 日次損失制限
        if self.daily_pnl <= -self.max_daily_loss:
            print(f"⚠️  日次最大損失制限: ¥{self.max_daily_loss:,.0f}")
            return False
        
        return True
    
    def update_daily_pnl(self, realized_pnl: float):
        """実現損益更新"""
        self.daily_pnl += realized_pnl


class RealtimeEngine:
    """リアルタイム取引エンジン"""
    
    def __init__(self, initial_balance: float = 1000000):
        self.balance = initial_balance
        self.positions: List[Position] = []
        self.market_stream = MarketDataStream()
        self.risk_manager = RiskManager()
        self.strategy = None
        self.is_running = False
        
        # パフォーマンス追跡
        self.trade_count = 0
        self.total_pnl = 0.0
        self.start_time = None
        
        # 価格履歴（15分足生成用）
        self.price_history = {}
        self.current_candles = {}
        
    def set_strategy(self, strategy):
        """取引戦略設定"""
        self.strategy = strategy
        
    def start(self):
        """エンジン開始"""
        if not self.strategy:
            print("❌ 取引戦略が設定されていません")
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        
        # マーケットデータサブスクライブ
        self.market_stream.subscribe(self._on_market_data)
        self.market_stream.start_stream()
        
        print("🚀 リアルタイム取引エンジン開始")
        print(f"📊 初期資金: ¥{self.balance:,.0f}")
        
    def stop(self):
        """エンジン停止"""
        self.is_running = False
        self.market_stream.stop_stream()
        
        # 全ポジションクローズ
        self._close_all_positions()
        
        # サマリー表示
        self._print_summary()
        
    def _on_market_data(self, tick_data: Dict):
        """マーケットデータ受信時の処理"""
        if not self.is_running:
            return
        
        symbol = tick_data['symbol']
        price = tick_data['mid']
        timestamp = tick_data['timestamp']
        
        # 価格履歴更新
        self._update_price_history(symbol, tick_data)
        
        # 未実現損益更新
        self._update_unrealized_pnl(symbol, price)
        
        # 15分足キャンドル生成
        candle_data = self._get_current_candle(symbol)
        
        if candle_data:
            # ストラテジーシグナル取得
            signal = self.strategy.generate_signal(candle_data, symbol)
            
            # シグナル処理
            self._process_signal(symbol, signal, price, timestamp)
    
    def _update_price_history(self, symbol: str, tick_data: Dict):
        """価格履歴更新（15分足用）"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append({
            'timestamp': tick_data['timestamp'],
            'price': tick_data['mid'],
            'bid': tick_data['bid'],
            'ask': tick_data['ask']
        })
        
        # 過去24時間分のみ保持
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.price_history[symbol] = [
            p for p in self.price_history[symbol]
            if datetime.fromisoformat(p['timestamp']) > cutoff_time
        ]
    
    def _get_current_candle(self, symbol: str) -> Optional[Dict]:
        """現在の15分足キャンドル取得"""
        if symbol not in self.price_history or not self.price_history[symbol]:
            return None
        
        # 最新の15分間のデータ取得
        now = datetime.now()
        minute_start = now.replace(second=0, microsecond=0)
        minute_start = minute_start.replace(minute=(minute_start.minute // 15) * 15)
        
        # 15分間のティックデータ取得
        candle_ticks = []
        for tick in self.price_history[symbol]:
            tick_time = datetime.fromisoformat(tick['timestamp'])
            if tick_time >= minute_start:
                candle_ticks.append(tick)
        
        if not candle_ticks:
            return None
        
        # OHLC生成
        prices = [t['price'] for t in candle_ticks]
        return {
            'timestamp': minute_start.isoformat(),
            'open': prices[0],
            'high': max(prices),
            'low': min(prices),
            'close': prices[-1],
            'volume': len(candle_ticks)
        }
    
    def _update_unrealized_pnl(self, symbol: str, price: float):
        """未実現損益更新"""
        for position in self.positions:
            if position.symbol == symbol:
                position.update_pnl(price)
    
    def _process_signal(self, symbol: str, signal: int, 
                       price: float, timestamp: str):
        """シグナル処理"""
        if signal == 0:  # クローズ
            self._close_position(symbol, price, timestamp)
        elif signal in [1, 2]:  # エントリー
            self._open_position(symbol, signal, price, timestamp)
    
    def _open_position(self, symbol: str, direction: int, 
                      price: float, timestamp: str):
        """ポジションオープン"""
        size = 10000  # 1万通貨固定
        
        # リスクチェック
        if not self.risk_manager.check_entry_allowed(symbol, size, self.positions):
            return
        
        # 新規ポジション作成
        position = Position(symbol, direction, size, price, timestamp)
        self.positions.append(position)
        self.trade_count += 1
        
        direction_str = "買い" if direction == 1 else "売り"
        print(f"📈 {symbol} {direction_str} エントリー @ {price:.3f} (¥{size:,.0f})")
    
    def _close_position(self, symbol: str, price: float, timestamp: str):
        """ポジションクローズ"""
        for position in self.positions[:]:
            if position.symbol == symbol and position.is_open:
                # 実現損益計算
                realized_pnl = position.update_pnl(price)
                self.balance += realized_pnl
                self.total_pnl += realized_pnl
                
                # リスク管理更新
                self.risk_manager.update_daily_pnl(realized_pnl)
                
                # ポジション削除
                self.positions.remove(position)
                
                print(f"📉 {symbol} クローズ @ {price:.3f} "
                      f"(PnL: ¥{realized_pnl:,.0f})")
                break
    
    def _close_all_positions(self):
        """全ポジションクローズ"""
        print("🔄 全ポジションクローズ中...")
        for position in self.positions[:]:
            # 最後の価格で強制クローズ
            self._close_position(position.symbol, position.entry_price, 
                               datetime.now().isoformat())
    
    def _print_summary(self):
        """サマリー表示"""
        if self.start_time:
            duration = datetime.now() - self.start_time
            
            print("\n" + "=" * 60)
            print("📊 リアルタイム取引結果")
            print("=" * 60)
            print(f"稼働時間: {duration}")
            print(f"総取引数: {self.trade_count}")
            print(f"最終残高: ¥{self.balance:,.0f}")
            print(f"総損益: ¥{self.total_pnl:,.0f}")
            print(f"リターン: {(self.balance/1000000-1)*100:.2f}%")
            print("=" * 60)


class RealtimeStrategy:
    """リアルタイム用ストラテジー"""
    
    def __init__(self):
        self.candle_history = {}
        
    def generate_signal(self, candle: Dict, symbol: str) -> int:
        """シグナル生成（簡易版）"""
        if symbol not in self.candle_history:
            self.candle_history[symbol] = []
        
        self.candle_history[symbol].append(candle)
        
        # 直近10本のみ保持
        if len(self.candle_history[symbol]) > 10:
            self.candle_history[symbol] = self.candle_history[symbol][-10:]
        
        # 最低3本必要
        if len(self.candle_history[symbol]) < 3:
            return 3  # 待機
        
        # 簡易トレンド判定
        recent = self.candle_history[symbol][-3:]
        
        # 上昇トレンド
        if all(recent[i]['close'] > recent[i-1]['close'] for i in range(1, 3)):
            return 1  # 買い
        
        # 下降トレンド  
        if all(recent[i]['close'] < recent[i-1]['close'] for i in range(1, 3)):
            return 2  # 売り
        
        return 3  # 待機


def main():
    """デモ実行"""
    print("🎯 リアルタイム取引エンジン デモ")
    
    # エンジン初期化
    engine = RealtimeEngine(initial_balance=1000000)
    
    # ストラテジー設定
    strategy = RealtimeStrategy()
    engine.set_strategy(strategy)
    
    # 10秒間稼働
    try:
        engine.start()
        time.sleep(10)
    finally:
        engine.stop()


if __name__ == "__main__":
    main()