"""
バックテストエンジン実装
Week 2: バックテスト環境構築
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import csv
import json
import os


class BacktestPosition:
    """ポジション管理クラス"""
    
    def __init__(self, entry_time: str, entry_price: float, 
                 direction: int, size: float = 1.0):
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.direction = direction  # 1: 買い, 2: 売り
        self.size = size
        self.exit_time = None
        self.exit_price = None
        self.pnl = 0.0
        self.is_open = True
    
    def close(self, exit_time: str, exit_price: float):
        """ポジションクローズ"""
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.is_open = False
        
        # 損益計算
        if self.direction == 1:  # 買い
            self.pnl = (exit_price - self.entry_price) * self.size
        else:  # 売り
            self.pnl = (self.entry_price - exit_price) * self.size
        
        return self.pnl


class BacktestEngine:
    """バックテストエンジン"""
    
    def __init__(self, initial_balance: float = 1000000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions: List[BacktestPosition] = []
        self.closed_positions: List[BacktestPosition] = []
        self.trade_history = []
        
        # パフォーマンス指標
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_balance = initial_balance
        
    def process_signal(self, timestamp: str, price_data: Dict, 
                       signal: int) -> Optional[str]:
        """
        シグナル処理
        signal: 1=買い, 2=売り, 3=待機, 0=クローズ
        """
        action = None
        
        if signal in [1, 2]:  # エントリーシグナル
            # 既存ポジションがあればクローズ
            if self.positions:
                for pos in self.positions:
                    if pos.is_open:
                        self._close_position(pos, timestamp, price_data['close'])
            
            # 新規ポジション
            position = BacktestPosition(
                entry_time=timestamp,
                entry_price=price_data['close'],
                direction=signal,
                size=self._calculate_position_size()
            )
            self.positions.append(position)
            self.total_trades += 1
            
            action = "BUY" if signal == 1 else "SELL"
            self._log_trade(timestamp, action, price_data['close'])
            
        elif signal == 0:  # クローズシグナル
            for pos in self.positions:
                if pos.is_open:
                    self._close_position(pos, timestamp, price_data['close'])
                    action = "CLOSE"
        
        # ドローダウン計算
        self._update_drawdown()
        
        return action
    
    def _close_position(self, position: BacktestPosition, 
                       exit_time: str, exit_price: float):
        """ポジションクローズ処理"""
        pnl = position.close(exit_time, exit_price)
        self.balance += pnl
        self.total_pnl += pnl
        
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        self.closed_positions.append(position)
        self._log_trade(exit_time, "CLOSE", exit_price, pnl)
    
    def _calculate_position_size(self) -> float:
        """ポジションサイズ計算（固定ロット）"""
        return 10000  # 1万通貨固定
    
    def _update_drawdown(self):
        """ドローダウン更新"""
        if self.balance > self.peak_balance:
            self.peak_balance = self.balance
        
        drawdown = (self.peak_balance - self.balance) / self.peak_balance
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
    
    def _log_trade(self, timestamp: str, action: str, 
                  price: float, pnl: float = 0):
        """取引記録"""
        self.trade_history.append({
            'timestamp': timestamp,
            'action': action,
            'price': price,
            'pnl': pnl,
            'balance': self.balance
        })
    
    def run_backtest(self, price_data: List[Dict], 
                    strategy_func) -> Dict:
        """
        バックテスト実行
        
        Args:
            price_data: 価格データのリスト
            strategy_func: シグナル生成関数
        
        Returns:
            バックテスト結果
        """
        print(f"🚀 バックテスト開始: {len(price_data)}本のキャンドル")
        
        for i, candle in enumerate(price_data):
            # ストラテジーからシグナル取得
            signal = strategy_func(candle, i, price_data)
            
            # シグナル処理
            action = self.process_signal(
                candle['timestamp'],
                candle,
                signal
            )
            
            if action and i % 100 == 0:
                print(f"  {i}/{len(price_data)}: {action} @ {candle['close']:.2f}")
        
        # 残ポジションクローズ
        if price_data:
            last_candle = price_data[-1]
            for pos in self.positions:
                if pos.is_open:
                    self._close_position(
                        pos, 
                        last_candle['timestamp'],
                        last_candle['close']
                    )
        
        return self.get_results()
    
    def get_results(self) -> Dict:
        """バックテスト結果取得"""
        win_rate = (self.winning_trades / self.total_trades * 100 
                   if self.total_trades > 0 else 0)
        
        results = {
            'initial_balance': self.initial_balance,
            'final_balance': self.balance,
            'total_pnl': self.total_pnl,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'max_drawdown': self.max_drawdown * 100,
            'return_pct': (self.balance - self.initial_balance) / self.initial_balance * 100
        }
        
        return results
    
    def save_results(self, filepath: str):
        """結果保存"""
        results = self.get_results()
        
        # サマリー保存
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        # 取引履歴保存
        history_file = filepath.replace('.json', '_trades.csv')
        if self.trade_history:
            with open(history_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.trade_history[0].keys())
                writer.writeheader()
                writer.writerows(self.trade_history)
        
        print(f"💾 結果保存: {filepath}")
    
    def print_results(self):
        """結果表示"""
        results = self.get_results()
        
        print("\n" + "=" * 60)
        print("📊 バックテスト結果")
        print("=" * 60)
        print(f"初期資金:     ¥{results['initial_balance']:,.0f}")
        print(f"最終資金:     ¥{results['final_balance']:,.0f}")
        print(f"総損益:       ¥{results['total_pnl']:,.0f}")
        print(f"リターン:     {results['return_pct']:.2f}%")
        print(f"総取引数:     {results['total_trades']}")
        print(f"勝ち取引:     {results['winning_trades']}")
        print(f"負け取引:     {results['losing_trades']}")
        print(f"勝率:         {results['win_rate']:.1f}%")
        print(f"最大DD:       {results['max_drawdown']:.2f}%")
        print("=" * 60)


def simple_strategy(candle: Dict, index: int, 
                   all_candles: List[Dict]) -> int:
    """
    シンプルなテストストラテジー
    移動平均クロスオーバー
    """
    if index < 20:
        return 3  # データ不足で待機
    
    # 簡易移動平均計算
    prices = [float(c['close']) for c in all_candles[index-20:index]]
    sma20 = sum(prices) / len(prices)
    
    current_price = float(candle['close'])
    
    # クロスオーバー判定
    if current_price > sma20 * 1.002:  # 0.2%上
        return 1  # 買い
    elif current_price < sma20 * 0.998:  # 0.2%下
        return 2  # 売り
    else:
        return 3  # 待機


def main():
    """メイン実行"""
    # データ読み込み
    data_file = "./data/historical/USDJPY_M5_synthetic.csv"
    
    if not os.path.exists(data_file):
        print(f"❌ データファイルが見つかりません: {data_file}")
        return
    
    # CSVデータ読み込み
    with open(data_file, 'r') as f:
        reader = csv.DictReader(f)
        price_data = list(reader)
    
    # float変換
    for candle in price_data:
        candle['open'] = float(candle['open'])
        candle['high'] = float(candle['high'])
        candle['low'] = float(candle['low'])
        candle['close'] = float(candle['close'])
        candle['volume'] = float(candle['volume'])
    
    print(f"📂 データ読み込み完了: {len(price_data)}本")
    
    # バックテスト実行
    engine = BacktestEngine(initial_balance=1000000)
    results = engine.run_backtest(price_data, simple_strategy)
    
    # 結果表示
    engine.print_results()
    
    # 結果保存
    engine.save_results("./data/backtest_results.json")


if __name__ == "__main__":
    main()