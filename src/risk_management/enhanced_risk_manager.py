"""
リスク管理機能強化
レビューフィードバックを反映:

1. ATRベースのポジションサイジング
2. ドローダウン制限・キルスイッチ
3. ポートフォリオレベルのリスク管理
4. 非常時対応策
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
import statistics


@dataclass
class Position:
    """ポジション情報"""
    symbol: str
    direction: int  # 1: 買い, 2: 売り
    size: float
    entry_price: float
    entry_time: datetime
    stop_loss: float = 0.0
    take_profit: float = 0.0
    current_pnl: float = 0.0
    is_open: bool = True


@dataclass
class RiskLimits:
    """リスク制限設定"""
    max_positions: int = 5
    max_exposure: float = 100000  # 最大エクスポージャー
    max_daily_loss: float = 50000  # 日次最大損失
    max_drawdown: float = 0.10  # 最大ドローダウン 10%
    max_risk_per_trade: float = 0.02  # 1取引あたり最大リスク 2%
    consecutive_loss_limit: int = 5  # 連敗制限
    portfolio_correlation_limit: float = 0.8  # 通貨ペア相関制限


class EnhancedRiskManager:
    """強化版リスク管理システム"""
    
    def __init__(self, initial_balance: float, limits: RiskLimits = None):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.limits = limits or RiskLimits()
        
        # ポジション管理
        self.positions: List[Position] = []
        self.closed_positions: List[Position] = []
        
        # 損益履歴
        self.daily_pnl_history = deque(maxlen=30)  # 30日分
        self.trade_results = deque(maxlen=100)  # 直近100取引
        self.consecutive_losses = 0
        
        # ドローダウン追跡
        self.peak_balance = initial_balance
        self.current_drawdown = 0.0
        self.max_drawdown_reached = 0.0
        
        # アラート状態
        self.is_trading_halted = False
        self.halt_reason = None
        self.last_check_time = datetime.now()
        
        # 通貨ペア相関データ（簡易版）
        self.currency_correlations = {
            ('USDJPY', 'EURJPY'): 0.65,
            ('USDJPY', 'GBPJPY'): 0.70,
            ('EURJPY', 'GBPJPY'): 0.85,
            ('EURUSD', 'GBPUSD'): 0.75
        }
    
    def check_entry_allowed(self, symbol: str, direction: int, 
                           entry_price: float, atr: float) -> Dict:
        """エントリー可否の総合判定"""
        
        # 取引停止状態チェック
        if self.is_trading_halted:
            return {
                'allowed': False,
                'reason': f'取引停止中: {self.halt_reason}',
                'position_size': 0
            }
        
        # 1. 基本制限チェック
        basic_check = self._check_basic_limits()
        if not basic_check['allowed']:
            return basic_check
        
        # 2. ドローダウンチェック
        dd_check = self._check_drawdown_limits()
        if not dd_check['allowed']:
            return dd_check
        
        # 3. 連敗チェック
        if self.consecutive_losses >= self.limits.consecutive_loss_limit:
            return {
                'allowed': False,
                'reason': f'連敗制限に達しました: {self.consecutive_losses}回',
                'position_size': 0
            }
        
        # 4. ポートフォリオ相関チェック
        correlation_check = self._check_portfolio_correlation(symbol, direction)
        if not correlation_check['allowed']:
            return correlation_check
        
        # 5. ポジションサイズ計算（ATRベース）
        position_size = self._calculate_position_size(
            symbol, entry_price, atr, direction
        )
        
        if position_size == 0:
            return {
                'allowed': False,
                'reason': 'ポジションサイズが計算できません',
                'position_size': 0
            }
        
        # 6. エクスポージャーチェック
        total_exposure = self._calculate_total_exposure() + position_size * entry_price
        if total_exposure > self.limits.max_exposure:
            return {
                'allowed': False,
                'reason': f'エクスポージャー制限超過: ¥{total_exposure:,.0f} > ¥{self.limits.max_exposure:,.0f}',
                'position_size': 0
            }
        
        return {
            'allowed': True,
            'reason': 'エントリー可能',
            'position_size': position_size,
            'stop_loss': self._calculate_stop_loss(entry_price, atr, direction),
            'take_profit': self._calculate_take_profit(entry_price, atr, direction)
        }
    
    def _check_basic_limits(self) -> Dict:
        """基本制限チェック"""
        # ポジション数制限
        open_positions = [p for p in self.positions if p.is_open]
        if len(open_positions) >= self.limits.max_positions:
            return {
                'allowed': False,
                'reason': f'最大ポジション数制限: {len(open_positions)}/{self.limits.max_positions}'
            }
        
        # 日次損失制限
        today = datetime.now().date()
        today_pnl = self._calculate_daily_pnl(today)
        if today_pnl <= -self.limits.max_daily_loss:
            self._halt_trading(f'日次損失制限達成: ¥{today_pnl:,.0f}')
            return {
                'allowed': False,
                'reason': f'日次損失制限達成: ¥{today_pnl:,.0f}'
            }
        
        return {'allowed': True}
    
    def _check_drawdown_limits(self) -> Dict:
        """ドローダウン制限チェック"""
        self._update_drawdown()
        
        if self.current_drawdown >= self.limits.max_drawdown:
            self._halt_trading(f'最大ドローダウン達成: {self.current_drawdown:.1%}')
            return {
                'allowed': False,
                'reason': f'最大ドローダウン達成: {self.current_drawdown:.1%}'
            }
        
        return {'allowed': True}
    
    def _check_portfolio_correlation(self, symbol: str, direction: int) -> Dict:
        """ポートフォリオ相関チェック"""
        open_positions = [p for p in self.positions if p.is_open]
        
        for position in open_positions:
            # 通貨ペア相関確認
            correlation = self._get_correlation(symbol, position.symbol)
            
            if correlation > self.limits.portfolio_correlation_limit:
                # 同方向ポジションの場合のみ制限
                if position.direction == direction:
                    return {
                        'allowed': False,
                        'reason': f'{symbol}と{position.symbol}の相関が高すぎます: {correlation:.1%}'
                    }
        
        return {'allowed': True}
    
    def _calculate_position_size(self, symbol: str, entry_price: float, 
                                atr: float, direction: int) -> float:
        """ATRベースのポジションサイズ計算"""
        if atr <= 0:
            return 0.0
        
        # リスク金額 = 口座残高 × リスク率
        risk_amount = self.current_balance * self.limits.max_risk_per_trade
        
        # ストップロス距離 = ATR × 2（標準的な倍数）
        stop_distance = atr * 2.0
        
        # ポジションサイズ = リスク金額 ÷ ストップロス距離
        position_size = risk_amount / stop_distance
        
        # 最大50,000通貨に制限
        return min(position_size, 50000)
    
    def _calculate_stop_loss(self, entry_price: float, atr: float, direction: int) -> float:
        """ATRベースのストップロス計算"""
        stop_distance = atr * 2.0
        
        if direction == 1:  # 買い
            return entry_price - stop_distance
        else:  # 売り
            return entry_price + stop_distance
    
    def _calculate_take_profit(self, entry_price: float, atr: float, direction: int) -> float:
        """利確レベル計算（R:Rレシオ = 1:2）"""
        profit_distance = atr * 4.0  # ストップロスの2倍
        
        if direction == 1:  # 買い
            return entry_price + profit_distance
        else:  # 売り
            return entry_price - profit_distance
    
    def add_position(self, symbol: str, direction: int, size: float,
                    entry_price: float, stop_loss: float = 0.0,
                    take_profit: float = 0.0) -> Position:
        """新規ポジション追加"""
        position = Position(
            symbol=symbol,
            direction=direction,
            size=size,
            entry_price=entry_price,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.positions.append(position)
        return position
    
    def close_position(self, position: Position, exit_price: float) -> float:
        """ポジションクローズ"""
        if position.direction == 1:  # 買い
            pnl = (exit_price - position.entry_price) * position.size
        else:  # 売り
            pnl = (position.entry_price - exit_price) * position.size
        
        position.current_pnl = pnl
        position.is_open = False
        
        # 実現損益を残高に反映
        self.current_balance += pnl
        
        # 取引結果記録
        self.trade_results.append({
            'pnl': pnl,
            'timestamp': datetime.now(),
            'symbol': position.symbol
        })
        
        # 連敗カウンター更新
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        self.closed_positions.append(position)
        
        return pnl
    
    def update_unrealized_pnl(self, current_prices: Dict[str, float]):
        """未実現損益更新"""
        total_unrealized = 0.0
        
        for position in self.positions:
            if position.is_open and position.symbol in current_prices:
                current_price = current_prices[position.symbol]
                
                if position.direction == 1:  # 買い
                    pnl = (current_price - position.entry_price) * position.size
                else:  # 売り
                    pnl = (position.entry_price - current_price) * position.size
                
                position.current_pnl = pnl
                total_unrealized += pnl
        
        return total_unrealized
    
    def _update_drawdown(self):
        """ドローダウン更新"""
        current_equity = self.current_balance + sum(
            p.current_pnl for p in self.positions if p.is_open
        )
        
        if current_equity > self.peak_balance:
            self.peak_balance = current_equity
        
        self.current_drawdown = (self.peak_balance - current_equity) / self.peak_balance
        
        if self.current_drawdown > self.max_drawdown_reached:
            self.max_drawdown_reached = self.current_drawdown
    
    def _calculate_total_exposure(self) -> float:
        """総エクスポージャー計算"""
        return sum(
            abs(p.size * p.entry_price) 
            for p in self.positions if p.is_open
        )
    
    def _calculate_daily_pnl(self, target_date) -> float:
        """指定日の損益計算"""
        daily_pnl = 0.0
        
        for trade in self.trade_results:
            if trade['timestamp'].date() == target_date:
                daily_pnl += trade['pnl']
        
        return daily_pnl
    
    def _get_correlation(self, symbol1: str, symbol2: str) -> float:
        """通貨ペア間相関取得"""
        if symbol1 == symbol2:
            return 1.0
        
        pair = (symbol1, symbol2) if symbol1 < symbol2 else (symbol2, symbol1)
        return self.currency_correlations.get(pair, 0.0)
    
    def _halt_trading(self, reason: str):
        """取引停止"""
        self.is_trading_halted = True
        self.halt_reason = reason
        print(f"🚨 取引停止: {reason}")
    
    def resume_trading(self, reason: str = "手動再開"):
        """取引再開"""
        self.is_trading_halted = False
        self.halt_reason = None
        print(f"✅ 取引再開: {reason}")
    
    def get_risk_metrics(self) -> Dict:
        """リスク指標取得"""
        open_positions = [p for p in self.positions if p.is_open]
        
        # 勝率計算
        if self.trade_results:
            winning_trades = sum(1 for t in self.trade_results if t['pnl'] > 0)
            win_rate = winning_trades / len(self.trade_results)
        else:
            win_rate = 0.0
        
        return {
            'current_balance': self.current_balance,
            'peak_balance': self.peak_balance,
            'current_drawdown': self.current_drawdown,
            'max_drawdown_reached': self.max_drawdown_reached,
            'open_positions': len(open_positions),
            'total_exposure': self._calculate_total_exposure(),
            'consecutive_losses': self.consecutive_losses,
            'win_rate': win_rate,
            'total_trades': len(self.trade_results),
            'is_trading_halted': self.is_trading_halted,
            'halt_reason': self.halt_reason
        }
    
    def emergency_close_all(self, current_prices: Dict[str, float]) -> float:
        """緊急全ポジションクローズ"""
        total_pnl = 0.0
        closed_count = 0
        
        for position in self.positions[:]:  # コピーを作成してループ
            if position.is_open and position.symbol in current_prices:
                exit_price = current_prices[position.symbol]
                pnl = self.close_position(position, exit_price)
                total_pnl += pnl
                closed_count += 1
        
        print(f"🆘 緊急クローズ完了: {closed_count}ポジション, 総損益: ¥{total_pnl:,.0f}")
        
        return total_pnl


def demo_risk_management():
    """リスク管理デモ"""
    print("=" * 60)
    print("🛡️ 強化版リスク管理システム デモ")
    print("=" * 60)
    
    # リスク管理初期化
    limits = RiskLimits(
        max_positions=3,
        max_exposure=50000,
        max_daily_loss=10000,
        max_drawdown=0.05,  # 5%
        max_risk_per_trade=0.01  # 1%
    )
    
    risk_manager = EnhancedRiskManager(
        initial_balance=100000,
        limits=limits
    )
    
    # テストケース1: 正常エントリー
    print("\n📊 テスト1: 正常エントリーチェック")
    result = risk_manager.check_entry_allowed("USDJPY", 1, 150.0, 0.30)
    print(f"結果: {result}")
    
    if result['allowed']:
        # ポジション追加
        position = risk_manager.add_position(
            symbol="USDJPY",
            direction=1,
            size=result['position_size'],
            entry_price=150.0,
            stop_loss=result['stop_loss'],
            take_profit=result['take_profit']
        )
        print(f"ポジション追加: {position}")
    
    # テストケース2: 相関制限
    print("\n📊 テスト2: 相関制限チェック")
    result2 = risk_manager.check_entry_allowed("EURJPY", 1, 162.0, 0.35)
    print(f"結果: {result2}")
    
    # テストケース3: 損失シミュレーション
    print("\n📊 テスト3: 損失シミュレーション")
    for i in range(6):  # 連敗をシミュレート
        # ダミーポジション追加・即クローズ（損失）
        pos = risk_manager.add_position("GBPJPY", 1, 10000, 185.0)
        risk_manager.close_position(pos, 184.0)  # 1円の損失
        
        metrics = risk_manager.get_risk_metrics()
        print(f"  取引{i+1}: 連敗数={metrics['consecutive_losses']}, "
              f"残高=¥{metrics['current_balance']:,.0f}")
    
    # テストケース4: エントリーチェック（連敗後）
    print("\n📊 テスト4: 連敗制限チェック")
    result3 = risk_manager.check_entry_allowed("AUDJPY", 1, 97.0, 0.25)
    print(f"結果: {result3}")
    
    # 最終リスク指標表示
    print("\n📈 最終リスク指標:")
    final_metrics = risk_manager.get_risk_metrics()
    for key, value in final_metrics.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    demo_risk_management()