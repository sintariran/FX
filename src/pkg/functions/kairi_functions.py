"""
乖離（Kairi）関連のPKG関数
実勢価格と平均足の位置関係の不一致を評価
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class KairiState:
    """乖離状態を表すデータクラス"""
    position_kairi: bool  # 位置の乖離（基準線に対して実勢と平均足が異なる側）
    direction_kairi: bool  # 方向の乖離（実勢の動きと平均足の方向が異なる）
    zenzen_kairi: float   # 前々足からの乖離度（-1～1、0が乖離なし）
    kairi_type: str      # 乖離タイプ（'position', 'direction', 'both', 'none'）
    strength: float      # 乖離の強度（0～1）


class KairiAnalyzer:
    """乖離分析クラス"""
    
    def __init__(self, base_line: float = 10.0):
        """
        Args:
            base_line: 基準線の値（デフォルト10.0）
        """
        self.base_line = base_line
    
    def calculate_heikin_ashi(self, candle: Dict, prev_ha: Optional[Dict] = None) -> Dict:
        """平均足の計算"""
        if prev_ha is None:
            ha_open = (candle['open'] + candle['close']) / 2
        else:
            ha_open = (prev_ha['open'] + prev_ha['close']) / 2
        
        ha_close = (candle['open'] + candle['high'] + candle['low'] + candle['close']) / 4
        ha_high = max(candle['high'], ha_open, ha_close)
        ha_low = min(candle['low'], ha_open, ha_close)
        
        return {
            'open': ha_open,
            'high': ha_high,
            'low': ha_low,
            'close': ha_close
        }
    
    def analyze_kairi(self, candles: List[Dict], index: int) -> KairiState:
        """
        乖離状態の分析
        
        Args:
            candles: キャンドルデータのリスト
            index: 分析対象のインデックス
            
        Returns:
            KairiState: 乖離状態
        """
        if index < 2:
            return KairiState(
                position_kairi=False,
                direction_kairi=False,
                zenzen_kairi=0.0,
                kairi_type='none',
                strength=0.0
            )
        
        # 現在、前足、前々足のデータ
        current = candles[index]
        prev1 = candles[index - 1]
        prev2 = candles[index - 2]
        
        # 平均足計算
        ha_prev2 = self.calculate_heikin_ashi(prev2)
        ha_prev1 = self.calculate_heikin_ashi(prev1, ha_prev2)
        ha_current = self.calculate_heikin_ashi(current, ha_prev1)
        
        # 実勢価格（終値）
        real_current = current['close']
        real_prev1 = prev1['close']
        real_prev2 = prev2['close']
        
        # 1. 位置の乖離判定（基準線に対する位置）
        position_kairi = self._check_position_kairi(
            real_current, ha_current['close'], self.base_line
        )
        
        # 2. 方向の乖離判定
        direction_kairi = self._check_direction_kairi(
            real_current, real_prev1, 
            ha_current['close'], ha_prev1['close']
        )
        
        # 3. 前々足からの乖離計算
        zenzen_kairi = self._calculate_zenzen_kairi(
            real_current, real_prev1, real_prev2,
            ha_current['close'], ha_prev1['close'], ha_prev2['close']
        )
        
        # 乖離タイプの判定
        if position_kairi and direction_kairi:
            kairi_type = 'both'
            strength = 1.0
        elif position_kairi:
            kairi_type = 'position'
            strength = 0.7
        elif direction_kairi:
            kairi_type = 'direction'
            strength = 0.5
        else:
            kairi_type = 'none'
            strength = abs(zenzen_kairi) * 0.3  # 前々足乖離のみの場合
        
        return KairiState(
            position_kairi=position_kairi,
            direction_kairi=direction_kairi,
            zenzen_kairi=zenzen_kairi,
            kairi_type=kairi_type,
            strength=min(1.0, strength)
        )
    
    def _check_position_kairi(self, real_price: float, ha_close: float, 
                              base_line: float) -> bool:
        """
        位置の乖離判定
        実勢価格と平均足が基準線の異なる側にある場合True
        """
        real_above = real_price > base_line
        ha_above = ha_close > base_line
        return real_above != ha_above
    
    def _check_direction_kairi(self, real_current: float, real_prev: float,
                               ha_current: float, ha_prev: float) -> bool:
        """
        方向の乖離判定
        実勢価格の動きと平均足の方向が異なる場合True
        """
        real_direction = 1 if real_current > real_prev else -1
        ha_direction = 1 if ha_current > ha_prev else -1
        return real_direction != ha_direction
    
    def _calculate_zenzen_kairi(self, real_current: float, real_prev1: float, 
                                real_prev2: float, ha_current: float, 
                                ha_prev1: float, ha_prev2: float) -> float:
        """
        前々足からの乖離度計算
        
        Returns:
            -1～1の値（0が乖離なし、正が上方乖離、負が下方乖離）
        """
        # 前々足での実勢と平均足の差
        prev2_diff = (real_prev2 - ha_prev2) / real_prev2 if real_prev2 != 0 else 0
        
        # 現在の実勢と平均足の差
        current_diff = (real_current - ha_current) / real_current if real_current != 0 else 0
        
        # 前々足からの変化
        kairi_change = current_diff - prev2_diff
        
        # -1～1に正規化
        return max(-1.0, min(1.0, kairi_change * 10))


class DokyakuJudgment:
    """同逆判定（前々足乖離による方向判断）"""
    
    def __init__(self):
        self.kairi_analyzer = KairiAnalyzer()
        # 勝率データ（メモファイルより）
        self.win_rates = {
            'MHIH_MJIH': 0.557,  # 55.7%
            'MMHMH_MMJMH': 0.561,  # 56.1%
            'MH_confirmed': 0.558  # 55.8%
        }
    
    def judge_dokyaku(self, candles: List[Dict], index: int) -> Tuple[int, float]:
        """
        同逆判定の実行
        
        Returns:
            (direction, confidence): 方向（1:上, 2:下, 0:なし）と信頼度
        """
        if index < 3:
            return 0, 0.0
        
        # M: 前足、I: 今足、J: 実勢、H: 平均、MM: 前々足
        current = candles[index]      # I: 今足
        prev1 = candles[index - 1]    # M: 前足
        prev2 = candles[index - 2]    # MM: 前々足
        
        # 平均足計算
        ha_prev2 = self.kairi_analyzer.calculate_heikin_ashi(prev2)
        ha_prev1 = self.kairi_analyzer.calculate_heikin_ashi(prev1, ha_prev2)
        ha_current = self.kairi_analyzer.calculate_heikin_ashi(current, ha_prev1)
        
        # MHIH: 前足平均-今足平均の方向
        mhih_direction = self._get_direction(ha_prev1['close'], ha_current['close'])
        
        # MJIH: 前足実勢-今足平均の方向
        mjih_direction = self._get_direction(prev1['close'], ha_current['close'])
        
        # 1. MHIHとMJIHの方向一致性評価
        if mhih_direction == mjih_direction and mhih_direction != 0:
            return mhih_direction, self.win_rates['MHIH_MJIH']
        
        # MMHMH: 前々足平均-前足平均の方向
        mmhmh_direction = self._get_direction(ha_prev2['close'], ha_prev1['close'])
        
        # MMJMH: 前々足実勢-前足平均の方向
        mmjmh_direction = self._get_direction(prev2['close'], ha_prev1['close'])
        
        # 2. 不一致時はMMHMHとMMJMHの方向確認
        if mmhmh_direction == mmjmh_direction and mmhmh_direction != 0:
            return mmhmh_direction, self.win_rates['MMHMH_MMJMH']
        
        # 3. MH確定方向の確認
        mh_direction = self._get_mh_confirmed_direction(
            ha_prev2, ha_prev1, ha_current
        )
        if mh_direction != 0:
            return mh_direction, self.win_rates['MH_confirmed']
        
        return 0, 0.0
    
    def _get_direction(self, value1: float, value2: float, 
                       threshold: float = 0.0001) -> int:
        """方向の判定"""
        diff = value2 - value1
        if abs(diff) < threshold:
            return 0
        return 1 if diff > 0 else 2
    
    def _get_mh_confirmed_direction(self, ha_prev2: Dict, ha_prev1: Dict, 
                                   ha_current: Dict) -> int:
        """MH確定方向の判定"""
        # 3本の平均足の連続性を確認
        prev2_bull = ha_prev2['close'] > ha_prev2['open']
        prev1_bull = ha_prev1['close'] > ha_prev1['open']
        current_bull = ha_current['close'] > ha_current['open']
        
        # 3本連続で同方向
        if prev2_bull and prev1_bull and current_bull:
            return 1
        elif not prev2_bull and not prev1_bull and not current_bull:
            return 2
        
        return 0


class IkikaeriJudgment:
    """行帰判定（相場の波動判定）"""
    
    def judge_ikikaeri(self, candles: List[Dict], index: int, 
                       base_line: float = 10.0) -> str:
        """
        行帰パターンの判定
        
        Returns:
            'iki_iki': 行行（継続）
            'iki_kaeri': 行帰（一時的戻り）
            'kaeri_iki': 帰行（戻りから再進行）
            'kaeri_modori': 帰戻（完全転換）
            'none': 判定不能
        """
        if index < 3:
            return 'none'
        
        current = candles[index]
        prev1 = candles[index - 1]
        prev2 = candles[index - 2]
        
        # 平均足計算
        ha_prev2 = KairiAnalyzer().calculate_heikin_ashi(prev2)
        ha_prev1 = KairiAnalyzer().calculate_heikin_ashi(prev1, ha_prev2)
        ha_current = KairiAnalyzer().calculate_heikin_ashi(current, ha_prev1)
        
        # 平均足の陰陽
        prev2_bull = ha_prev2['close'] > ha_prev2['open']
        prev1_bull = ha_prev1['close'] > ha_prev1['open']
        current_bull = ha_current['close'] > ha_current['open']
        
        # 基準線との位置関係
        prev2_above = prev2['close'] > base_line
        prev1_above = prev1['close'] > base_line
        current_above = current['close'] > base_line
        
        # 高値・安値更新
        high_update = current['high'] > max(prev1['high'], prev2['high'])
        low_update = current['low'] < min(prev1['low'], prev2['low'])
        
        # パターン判定
        if current_bull:  # 現在が陽線
            if prev1_bull:
                if high_update and current_above:
                    return 'iki_iki'  # 上昇継続
                else:
                    return 'iki_kaeri'  # 上昇中の一時的戻り
            else:
                if prev2_bull:
                    return 'kaeri_iki'  # 戻りから再上昇
                else:
                    return 'kaeri_modori'  # 下降から上昇転換
        else:  # 現在が陰線
            if not prev1_bull:
                if low_update and not current_above:
                    return 'iki_iki'  # 下降継続
                else:
                    return 'iki_kaeri'  # 下降中の一時的戻り
            else:
                if not prev2_bull:
                    return 'kaeri_iki'  # 戻りから再下降
                else:
                    return 'kaeri_modori'  # 上昇から下降転換
        
        return 'none'


# PKG関数として登録可能な形式
def pkg_kairi_analysis(candles: List[Dict], index: int, 
                       params: Optional[Dict] = None) -> Dict:
    """
    PKG用乖離分析関数
    
    Returns:
        分析結果の辞書
    """
    base_line = params.get('base_line', 10.0) if params else 10.0
    
    analyzer = KairiAnalyzer(base_line)
    kairi_state = analyzer.analyze_kairi(candles, index)
    
    dokyaku = DokyakuJudgment()
    dokyaku_dir, dokyaku_conf = dokyaku.judge_dokyaku(candles, index)
    
    ikikaeri = IkikaeriJudgment()
    ikikaeri_pattern = ikikaeri.judge_ikikaeri(candles, index, base_line)
    
    return {
        'kairi': {
            'position': kairi_state.position_kairi,
            'direction': kairi_state.direction_kairi,
            'zenzen': kairi_state.zenzen_kairi,
            'type': kairi_state.kairi_type,
            'strength': kairi_state.strength
        },
        'dokyaku': {
            'direction': dokyaku_dir,
            'confidence': dokyaku_conf
        },
        'ikikaeri': {
            'pattern': ikikaeri_pattern,
            'priority': _get_ikikaeri_priority(ikikaeri_pattern)
        }
    }


def _get_ikikaeri_priority(pattern: str) -> int:
    """行帰パターンの優先度取得"""
    priorities = {
        'kaeri_iki': 4,    # 帰行（最優先）
        'iki_iki': 3,      # 行行
        'kaeri_modori': 2, # 帰戻
        'iki_kaeri': 1,    # 行戻
        'none': 0
    }
    return priorities.get(pattern, 0)