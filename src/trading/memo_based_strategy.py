#!/usr/bin/env python3
"""
メモベースの取引戦略実装
97個のメモファイルから抽出した4つのコア概念を統合した取引システム

核心オペレーション:
1. 同逆判定（Dokyaku）: 前々足乖離による方向判断（勝率55.7%～56.1%）
2. 行帰判定（Ikikaeri）: 前足の動きから今足の方向予測
3. もみ・オーバーシュート判定: レンジ相場とブレイクアウト検出
4. 時間結合: マルチタイムフレーム統合（1M, 5M, 15M, 30M）
"""

import sys
import os
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接インポートでnumpy依存を回避
try:
    from pkg.memo_logic.core_pkg_functions import (
        DokyakuFunction, IkikaerikFunction, MarketData, OperationSignal,
        TimeFrame, Currency, Period, PKGId
    )
except ImportError:
    # フォールバック: 直接ファイルからインポート
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "core_pkg_functions", 
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "pkg", "memo_logic", "core_pkg_functions.py")
    )
    core_pkg_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core_pkg_module)
    
    DokyakuFunction = core_pkg_module.DokyakuFunction
    IkikaerikFunction = core_pkg_module.IkikaerikFunction
    MarketData = core_pkg_module.MarketData
    OperationSignal = core_pkg_module.OperationSignal
    TimeFrame = core_pkg_module.TimeFrame
    Currency = core_pkg_module.Currency
    Period = core_pkg_module.Period
    PKGId = core_pkg_module.PKGId

class TradeDirection(Enum):
    """取引方向"""
    LONG = 1    # 買い（上方向）
    SHORT = 2   # 売り（下方向）
    NEUTRAL = 0 # 中立

class EntrySignalType(Enum):
    """エントリーシグナルタイプ"""
    DOKYAKU_BASED = "dokyaku_based"      # 同逆判定ベース
    IKIKAERI_BASED = "ikikaeri_based"    # 行帰判定ベース
    MOMI_BREAKOUT = "momi_breakout"      # もみブレイクアウト
    TIME_SYNC = "time_sync"              # 時間足同期

@dataclass
class TradeSetup:
    """取引セットアップ"""
    direction: TradeDirection
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    signal_type: EntrySignalType
    timeframe: TimeFrame
    timestamp: datetime
    metadata: Dict = None

@dataclass  
class TradingState:
    """取引状態管理"""
    current_position: Optional[TradeDirection]
    entry_price: Optional[float]
    position_size: float
    unrealized_pnl: float
    total_trades: int
    winning_trades: int
    current_drawdown: float
    max_drawdown: float

class MemoBasedTradingStrategy:
    """メモファイルベースの統合取引戦略"""
    
    def __init__(self, currency_pair: Currency = Currency.USDJPY):
        self.currency_pair = currency_pair
        self.logger = logging.getLogger(__name__)
        
        # PKG関数の初期化
        self.dokyaku_func = DokyakuFunction(self._create_pkg_id(TimeFrame.M15, 1, 1))
        self.ikikaeri_func = IkikaerikFunction(self._create_pkg_id(TimeFrame.M15, 1, 2))
        
        # 取引状態
        self.trading_state = TradingState(
            current_position=None,
            entry_price=None,
            position_size=0.0,
            unrealized_pnl=0.0,
            total_trades=0,
            winning_trades=0,
            current_drawdown=0.0,
            max_drawdown=0.0
        )
        
        # 戦略パラメータ（メモファイルから抽出）
        self.strategy_params = {
            # 同逆判定パラメータ
            'dokyaku_confidence_threshold': 0.55,  # 最低勝率55%
            'dokyaku_mhih_mjih_weight': 0.557,     # MHIH/MJIH一致時勝率
            'dokyaku_mmhmh_mmjmh_weight': 0.561,   # MMHMH/MMJMH一致時勝率
            
            # 行帰判定パラメータ  
            'ikikaeri_continuation_weight': 0.8,   # 行行継続重み
            'ikikaeri_reversal_weight': 0.6,       # 帰戻転換重み
            
            # リスク管理パラメータ
            'max_risk_per_trade': 0.02,           # 1取引あたり最大リスク2%
            'max_drawdown_limit': 0.10,           # 最大ドローダウン10%
            'position_sizing_base': 10000,         # ベースポジションサイズ
            
            # 時間足結合パラメータ
            'timeframe_sync_threshold': 0.7,      # 時間足同期閾値
            'momi_range_pips': 3,                 # もみ判定レンジ幅（pips）
            'overshoot_threshold': 2.0,           # オーバーシュート閾値
        }
    
    def _create_pkg_id(self, timeframe: TimeFrame, layer: int, sequence: int) -> PKGId:
        """PKG ID生成"""
        return PKGId(
            timeframe=timeframe,
            period=Period.COMMON,
            currency=self.currency_pair,
            layer=layer,
            sequence=sequence
        )
    
    def analyze_market_condition(self, market_data: Dict[str, List[MarketData]]) -> Dict[str, any]:
        """市場状況の総合分析"""
        analysis = {
            'dokyaku_signal': None,
            'ikikaeri_signal': None,
            'momi_state': False,
            'overshoot_detected': False,
            'timeframe_sync': False,
            'overall_direction': TradeDirection.NEUTRAL,
            'confidence': 0.0
        }
        
        try:
            # 各時間足のデータを取得
            m1_data = market_data.get('M1', [])
            m5_data = market_data.get('M5', [])
            m15_data = market_data.get('M15', [])
            m30_data = market_data.get('M30', [])
            
            if not m15_data or len(m15_data) < 5:
                return analysis
            
            # 1. 同逆判定の実行
            dokyaku_data = {'market_data': m15_data}
            dokyaku_signal = self.dokyaku_func.execute(dokyaku_data)
            if dokyaku_signal:
                analysis['dokyaku_signal'] = dokyaku_signal
                self.logger.debug(f"同逆判定: {dokyaku_signal.direction}, 信頼度: {dokyaku_signal.confidence}")
            
            # 2. 行帰判定の実行
            ikikaeri_data = {'market_data': m15_data}
            ikikaeri_signal = self.ikikaeri_func.execute(ikikaeri_data)
            if ikikaeri_signal:
                analysis['ikikaeri_signal'] = ikikaeri_signal
                self.logger.debug(f"行帰判定: パターン={ikikaeri_signal.metadata.get('pattern')}")
            
            # 3. もみ・オーバーシュート判定
            analysis['momi_state'] = self._detect_momi_condition(m15_data)
            analysis['overshoot_detected'] = self._detect_overshoot(m15_data)
            
            # 4. マルチタイムフレーム同期確認
            analysis['timeframe_sync'] = self._check_timeframe_sync(
                m1_data, m5_data, m15_data, m30_data
            )
            
            # 5. 統合判断
            overall_direction, confidence = self._integrate_signals(analysis)
            analysis['overall_direction'] = overall_direction
            analysis['confidence'] = confidence
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"市場状況分析エラー: {e}")
            return analysis
    
    def _detect_momi_condition(self, market_data: List[MarketData]) -> bool:
        """もみ（レンジ）状態の検出"""
        if len(market_data) < 10:
            return False
        
        try:
            # 過去10足のレンジ幅を計算
            recent_highs = [bar.high for bar in market_data[-10:]]
            recent_lows = [bar.low for bar in market_data[-10:]]
            
            range_width = max(recent_highs) - min(recent_lows)
            
            # メモファイルより: レンジ幅3pips未満でもみ判定
            momi_threshold = self.strategy_params['momi_range_pips'] * 0.01  # pips to price
            
            is_momi = range_width < momi_threshold
            
            if is_momi:
                self.logger.debug(f"もみ状態検出: レンジ幅={range_width:.4f}")
            
            return is_momi
            
        except Exception as e:
            self.logger.error(f"もみ判定エラー: {e}")
            return False
    
    def _detect_overshoot(self, market_data: List[MarketData]) -> bool:
        """オーバーシュート検出"""
        if len(market_data) < 3:
            return False
        
        try:
            # 前足、今足の取得
            prev_bar = market_data[-2]
            current_bar = market_data[-1]
            
            # 簡易オーバーシュート判定: 前足の変動幅が今足換算で閾値以上
            prev_range = abs(prev_bar.high - prev_bar.low)
            current_range = abs(current_bar.high - current_bar.low)
            
            if current_range == 0:
                return False
            
            overshoot_ratio = prev_range / current_range
            overshoot_detected = overshoot_ratio >= self.strategy_params['overshoot_threshold']
            
            if overshoot_detected:
                self.logger.debug(f"オーバーシュート検出: 比率={overshoot_ratio:.2f}")
            
            return overshoot_detected
            
        except Exception as e:
            self.logger.error(f"オーバーシュート判定エラー: {e}")
            return False
    
    def _check_timeframe_sync(self, m1_data: List[MarketData], 
                            m5_data: List[MarketData],
                            m15_data: List[MarketData], 
                            m30_data: List[MarketData]) -> bool:
        """マルチタイムフレーム同期確認"""
        try:
            # 各時間足の方向を判定
            directions = []
            
            for data in [m1_data, m5_data, m15_data, m30_data]:
                if len(data) >= 2:
                    current = data[-1]
                    previous = data[-2]
                    
                    # 平均足の方向で判定
                    if (current.heikin_ashi_close is not None and 
                        current.heikin_ashi_open is not None):
                        direction = 1 if current.heikin_ashi_close > current.heikin_ashi_open else -1
                        directions.append(direction)
            
            if len(directions) < 2:
                return False
            
            # 方向の一致度を計算
            positive_count = sum(1 for d in directions if d > 0)
            negative_count = sum(1 for d in directions if d < 0)
            
            sync_ratio = max(positive_count, negative_count) / len(directions)
            is_synced = sync_ratio >= self.strategy_params['timeframe_sync_threshold']
            
            if is_synced:
                dominant_direction = "上昇" if positive_count > negative_count else "下降"
                self.logger.debug(f"時間足同期確認: {dominant_direction}方向, 同期率={sync_ratio:.2f}")
            
            return is_synced
            
        except Exception as e:
            self.logger.error(f"時間足同期確認エラー: {e}")
            return False
    
    def _integrate_signals(self, analysis: Dict[str, any]) -> Tuple[TradeDirection, float]:
        """シグナル統合判断"""
        try:
            direction_scores = {TradeDirection.LONG: 0.0, TradeDirection.SHORT: 0.0}
            total_weight = 0.0
            
            # 同逆判定の統合
            if analysis['dokyaku_signal']:
                signal = analysis['dokyaku_signal']
                weight = signal.confidence
                
                if signal.direction == 1:  # 上方向
                    direction_scores[TradeDirection.LONG] += weight
                elif signal.direction == 2:  # 下方向
                    direction_scores[TradeDirection.SHORT] += weight
                
                total_weight += weight
            
            # 行帰判定の統合  
            if analysis['ikikaeri_signal']:
                signal = analysis['ikikaeri_signal']
                weight = signal.confidence * 0.8  # 行帰判定の重み調整
                
                if signal.direction == 1:
                    direction_scores[TradeDirection.LONG] += weight
                elif signal.direction == 2:
                    direction_scores[TradeDirection.SHORT] += weight
                
                total_weight += weight
            
            # 時間足同期ボーナス
            if analysis['timeframe_sync']:
                sync_bonus = 0.2
                # 主要シグナルの方向を強化
                max_direction = max(direction_scores, key=direction_scores.get)
                direction_scores[max_direction] += sync_bonus
                total_weight += sync_bonus
            
            # もみ状態時は信頼度を下げる
            if analysis['momi_state']:
                for direction in direction_scores:
                    direction_scores[direction] *= 0.7
                total_weight *= 0.7
            
            # オーバーシュート時は反転可能性を考慮
            if analysis['overshoot_detected']:
                # 現在のスコアを反転（反転エントリーの示唆）
                long_score = direction_scores[TradeDirection.LONG]
                short_score = direction_scores[TradeDirection.SHORT]
                direction_scores[TradeDirection.LONG] = short_score * 1.1
                direction_scores[TradeDirection.SHORT] = long_score * 1.1
            
            # 最終判定
            if total_weight == 0:
                return TradeDirection.NEUTRAL, 0.0
            
            max_direction = max(direction_scores, key=direction_scores.get)
            max_score = direction_scores[max_direction]
            confidence = max_score / total_weight if total_weight > 0 else 0.0
            
            # 最小信頼度チェック
            min_confidence = self.strategy_params['dokyaku_confidence_threshold']
            if confidence < min_confidence:
                return TradeDirection.NEUTRAL, confidence
            
            return max_direction, confidence
            
        except Exception as e:
            self.logger.error(f"シグナル統合エラー: {e}")
            return TradeDirection.NEUTRAL, 0.0
    
    def generate_trade_setup(self, analysis: Dict[str, any], 
                           current_price: float) -> Optional[TradeSetup]:
        """取引セットアップの生成"""
        
        direction = analysis['overall_direction']
        confidence = analysis['confidence']
        
        if direction == TradeDirection.NEUTRAL or confidence < 0.55:
            return None
        
        try:
            # リスク管理に基づくストップロス・テイクプロフィット設定
            risk_amount = self.strategy_params['position_sizing_base'] * self.strategy_params['max_risk_per_trade']
            
            # メモファイルより: 段階的決済戦略を反映
            if direction == TradeDirection.LONG:
                stop_loss = current_price * 0.995  # 0.5%のストップロス
                take_profit = current_price * 1.015  # 1.5%のテイクプロフィット（3:1のリスクリワード）
            else:  # SHORT
                stop_loss = current_price * 1.005
                take_profit = current_price * 0.985
            
            # エントリーシグナルタイプの決定
            signal_type = EntrySignalType.DOKYAKU_BASED
            if analysis['ikikaeri_signal'] and analysis['ikikaeri_signal'].confidence > 0.7:
                signal_type = EntrySignalType.IKIKAERI_BASED
            elif analysis['momi_state'] and analysis['overshoot_detected']:
                signal_type = EntrySignalType.MOMI_BREAKOUT
            elif analysis['timeframe_sync']:
                signal_type = EntrySignalType.TIME_SYNC
            
            setup = TradeSetup(
                direction=direction,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence=confidence,
                signal_type=signal_type,
                timeframe=TimeFrame.M15,  # メイン時間足
                timestamp=datetime.now(),
                metadata={
                    'dokyaku_confidence': analysis['dokyaku_signal'].confidence if analysis['dokyaku_signal'] else 0.0,
                    'ikikaeri_pattern': analysis['ikikaeri_signal'].metadata.get('pattern') if analysis['ikikaeri_signal'] else 'none',
                    'momi_state': analysis['momi_state'],
                    'overshoot_detected': analysis['overshoot_detected'],
                    'timeframe_sync': analysis['timeframe_sync']
                }
            )
            
            self.logger.info(f"取引セットアップ生成: {direction.name}, 信頼度={confidence:.3f}, タイプ={signal_type.value}")
            
            return setup
            
        except Exception as e:
            self.logger.error(f"取引セットアップ生成エラー: {e}")
            return None
    
    def should_exit_position(self, market_data: Dict[str, List[MarketData]], 
                           current_price: float) -> bool:
        """ポジション決済判定"""
        
        if self.trading_state.current_position is None:
            return False
        
        try:
            # メモファイルベースの決済条件
            
            # 1. 1分の揃いと前足以前のOPFF揃いチェック
            m1_data = market_data.get('M1', [])
            if len(m1_data) >= 3:
                # 1分足の方向揃い確認（簡易実装）
                recent_directions = []
                for bar in m1_data[-3:]:
                    if (bar.heikin_ashi_close is not None and 
                        bar.heikin_ashi_open is not None):
                        direction = 1 if bar.heikin_ashi_close > bar.heikin_ashi_open else -1
                        recent_directions.append(direction)
                
                # 方向が揃っている場合は決済検討
                if len(set(recent_directions)) == 1:
                    self.logger.debug("1分足方向揃いによる決済シグナル")
                    return True
            
            # 2. 時間足の接続点での決済
            current_time = datetime.now()
            # 15分足の境界（簡易チェック）
            if current_time.minute % 15 == 0:
                self.logger.debug("時間足接続点での決済シグナル")
                return True
            
            # 3. 平均足転換による決済
            m15_data = market_data.get('M15', [])
            if len(m15_data) >= 2:
                current_bar = m15_data[-1]
                prev_bar = m15_data[-2]
                
                if (current_bar.heikin_ashi_close is not None and
                    current_bar.heikin_ashi_open is not None and
                    prev_bar.heikin_ashi_close is not None and
                    prev_bar.heikin_ashi_open is not None):
                    
                    current_direction = 1 if current_bar.heikin_ashi_close > current_bar.heikin_ashi_open else -1
                    prev_direction = 1 if prev_bar.heikin_ashi_close > prev_bar.heikin_ashi_open else -1
                    
                    # 平均足が転換した場合
                    if current_direction != prev_direction:
                        self.logger.debug("平均足転換による決済シグナル")
                        return True
            
            # 4. ストップロス・テイクプロフィット確認
            if self.trading_state.current_position == TradeDirection.LONG:
                # ロングポジションの損切り・利確判定は別途実装
                pass
            elif self.trading_state.current_position == TradeDirection.SHORT:
                # ショートポジションの損切り・利確判定は別途実装
                pass
            
            return False
            
        except Exception as e:
            self.logger.error(f"決済判定エラー: {e}")
            return False
    
    def execute_trade(self, setup: TradeSetup) -> bool:
        """取引実行（デモ実装）"""
        try:
            # 実際の取引実行はブローカーAPIと連携
            self.trading_state.current_position = setup.direction
            self.trading_state.entry_price = setup.entry_price
            self.trading_state.total_trades += 1
            
            self.logger.info(f"取引実行: {setup.direction.name} @ {setup.entry_price}, 信頼度={setup.confidence:.3f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"取引実行エラー: {e}")
            return False
    
    def get_strategy_statistics(self) -> Dict[str, any]:
        """戦略統計の取得"""
        win_rate = (self.trading_state.winning_trades / 
                   max(self.trading_state.total_trades, 1)) * 100
        
        return {
            'total_trades': self.trading_state.total_trades,
            'winning_trades': self.trading_state.winning_trades,
            'win_rate': win_rate,
            'current_drawdown': self.trading_state.current_drawdown,
            'max_drawdown': self.trading_state.max_drawdown,
            'unrealized_pnl': self.trading_state.unrealized_pnl,
            'current_position': self.trading_state.current_position.name if self.trading_state.current_position else 'NONE',
            'strategy_params': self.strategy_params
        }


def demo_strategy_execution():
    """戦略実行デモ"""
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("=" * 60)
    print("メモベース取引戦略 - デモ実行")
    print("=" * 60)
    
    # 戦略インスタンス作成
    strategy = MemoBasedTradingStrategy(Currency.USDJPY)
    
    # デモ市場データ（実際はOANDA API等から取得）
    demo_market_data = {
        'M1': [
            MarketData(datetime.now() - timedelta(minutes=i), 150.0+i*0.01, 150.1+i*0.01, 149.9+i*0.01, 150.05+i*0.01, 1000,
                      heikin_ashi_open=150.0+i*0.01, heikin_ashi_high=150.1+i*0.01, 
                      heikin_ashi_low=149.9+i*0.01, heikin_ashi_close=150.05+i*0.01)
            for i in range(10, 0, -1)
        ],
        'M5': [
            MarketData(datetime.now() - timedelta(minutes=i*5), 150.0+i*0.05, 150.2+i*0.05, 149.8+i*0.05, 150.1+i*0.05, 5000,
                      heikin_ashi_open=150.0+i*0.05, heikin_ashi_high=150.2+i*0.05,
                      heikin_ashi_low=149.8+i*0.05, heikin_ashi_close=150.1+i*0.05)
            for i in range(10, 0, -1)
        ],
        'M15': [
            MarketData(datetime.now() - timedelta(minutes=i*15), 150.0+i*0.1, 150.3+i*0.1, 149.7+i*0.1, 150.15+i*0.1, 15000,
                      heikin_ashi_open=150.0+i*0.1, heikin_ashi_high=150.3+i*0.1,
                      heikin_ashi_low=149.7+i*0.1, heikin_ashi_close=150.15+i*0.1)
            for i in range(10, 0, -1)  
        ],
        'M30': [
            MarketData(datetime.now() - timedelta(minutes=i*30), 150.0+i*0.2, 150.5+i*0.2, 149.5+i*0.2, 150.25+i*0.2, 30000,
                      heikin_ashi_open=150.0+i*0.2, heikin_ashi_high=150.5+i*0.2,
                      heikin_ashi_low=149.5+i*0.2, heikin_ashi_close=150.25+i*0.2)
            for i in range(5, 0, -1)
        ]
    }
    
    # 市場分析実行
    print("\n📊 市場状況分析中...")
    analysis = strategy.analyze_market_condition(demo_market_data)
    
    print(f"  同逆判定: {'有効' if analysis['dokyaku_signal'] else '無効'}")
    print(f"  行帰判定: {'有効' if analysis['ikikaeri_signal'] else '無効'}")
    print(f"  もみ状態: {'検出' if analysis['momi_state'] else '通常'}")
    print(f"  オーバーシュート: {'検出' if analysis['overshoot_detected'] else '正常'}")
    print(f"  時間足同期: {'同期中' if analysis['timeframe_sync'] else '非同期'}")
    print(f"  総合方向: {analysis['overall_direction'].name}")
    print(f"  信頼度: {analysis['confidence']:.3f}")
    
    # 取引セットアップ生成
    current_price = 150.25
    print(f"\n💡 取引セットアップ生成 (現在価格: {current_price})")
    
    setup = strategy.generate_trade_setup(analysis, current_price)
    
    if setup:
        print(f"  方向: {setup.direction.name}")
        print(f"  エントリー価格: {setup.entry_price}")
        print(f"  ストップロス: {setup.stop_loss}")
        print(f"  テイクプロフィット: {setup.take_profit}")
        print(f"  信頼度: {setup.confidence:.3f}")
        print(f"  シグナルタイプ: {setup.signal_type.value}")
        
        # デモ取引実行
        print(f"\n⚡ 取引実行中...")
        success = strategy.execute_trade(setup)
        print(f"  実行結果: {'成功' if success else '失敗'}")
        
    else:
        print("  取引条件未達成 - エントリー見送り")
    
    # 戦略統計表示
    print(f"\n📈 戦略統計:")
    stats = strategy.get_strategy_statistics()
    for key, value in stats.items():
        if key != 'strategy_params':
            print(f"  {key}: {value}")
    
    print("\n✅ デモ実行完了")


if __name__ == "__main__":
    demo_strategy_execution()