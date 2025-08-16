"""
ノードID自動採番ユーティリティ
PKG DAGノードのIDを自動生成・管理
"""

import logging
from typing import Dict, Set, Optional, List
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class NodeIDGenerator:
    """ノードID自動採番クラス"""
    
    def __init__(self, timeframe: str = "3", period: str = "9", currency: str = "1"):
        """
        初期化
        
        Args:
            timeframe: 時間足コード（1=1分, 2=5分, 3=15分, 4=30分, 5=1時間, 6=4時間）
            period: 周期コード（9=共通, その他=TSML周期）
            currency: 通貨コード（1=USDJPY, 2=EURUSD, 3=EURJPY）
        """
        self.timeframe = timeframe
        self.period = period
        self.currency = currency
        self.prefix = f"{timeframe}{period}{currency}"
        
        # 階層ごとのカウンタ
        self.counters: Dict[int, int] = {}
        
        # 使用済みIDの追跡
        self.used_ids: Set[str] = set()
        
        # ID形式の正規表現
        self.id_pattern = re.compile(r'^(\d{3})\^(\d+)-(\d{3})$')
    
    def generate(self, layer: int, reserve: bool = True) -> str:
        """
        次の利用可能なIDを生成
        
        Args:
            layer: 階層番号
            reserve: 生成したIDを予約するか
            
        Returns:
            生成されたPKG ID
        """
        if layer < 0:
            raise ValueError(f"Invalid layer number: {layer}")
        
        # 該当階層のカウンタを初期化または取得
        if layer not in self.counters:
            self.counters[layer] = 0
        
        # 次の連番を探索
        while True:
            self.counters[layer] += 1
            
            # 999を超えたらエラー
            if self.counters[layer] > 999:
                raise ValueError(
                    f"Exceeded maximum sequence number (999) for layer {layer}"
                )
            
            # ID生成
            node_id = f"{self.prefix}^{layer}-{self.counters[layer]:03d}"
            
            # 未使用なら返す
            if node_id not in self.used_ids:
                if reserve:
                    self.used_ids.add(node_id)
                return node_id
    
    def reserve_id(self, node_id: str) -> bool:
        """
        既存のIDを予約（使用済みとしてマーク）
        
        Args:
            node_id: 予約するID
            
        Returns:
            予約成功ならTrue
        """
        if not self.is_valid_id(node_id):
            logger.error(f"Invalid ID format: {node_id}")
            return False
        
        if node_id in self.used_ids:
            logger.warning(f"ID already reserved: {node_id}")
            return False
        
        self.used_ids.add(node_id)
        
        # カウンタを更新
        match = self.id_pattern.match(node_id)
        if match:
            layer = int(match.group(2))
            seq = int(match.group(3))
            
            if layer not in self.counters or self.counters[layer] < seq:
                self.counters[layer] = seq
        
        return True
    
    def is_valid_id(self, node_id: str) -> bool:
        """
        ID形式の妥当性を検証
        
        Args:
            node_id: 検証するID
            
        Returns:
            有効ならTrue
        """
        match = self.id_pattern.match(node_id)
        if not match:
            return False
        
        # プレフィックスが一致するか確認
        prefix = match.group(1)
        if prefix != self.prefix:
            logger.warning(
                f"ID prefix mismatch: expected {self.prefix}, got {prefix}"
            )
            return False
        
        return True
    
    def is_available(self, node_id: str) -> bool:
        """
        IDが利用可能か確認
        
        Args:
            node_id: 確認するID
            
        Returns:
            利用可能ならTrue
        """
        return node_id not in self.used_ids
    
    def bulk_generate(self, layer: int, count: int) -> List[str]:
        """
        複数のIDを一括生成
        
        Args:
            layer: 階層番号
            count: 生成する個数
            
        Returns:
            生成されたIDのリスト
        """
        ids = []
        for _ in range(count):
            ids.append(self.generate(layer, reserve=True))
        return ids
    
    def load_existing_ids(self, ids: List[str]):
        """
        既存のIDリストを読み込んで予約
        
        Args:
            ids: 既存のIDリスト
        """
        for node_id in ids:
            self.reserve_id(node_id)
        
        logger.info(f"Loaded {len(self.used_ids)} existing IDs")
    
    def get_next_sequence(self, layer: int) -> int:
        """
        指定階層の次の連番を取得（生成はしない）
        
        Args:
            layer: 階層番号
            
        Returns:
            次の連番
        """
        return self.counters.get(layer, 0) + 1
    
    def get_statistics(self) -> Dict[str, any]:
        """
        ID生成統計を取得
        
        Returns:
            統計情報
        """
        stats = {
            'prefix': self.prefix,
            'total_reserved': len(self.used_ids),
            'layers_used': len(self.counters),
            'max_sequence_by_layer': dict(self.counters),
            'timeframe': self.timeframe,
            'period': self.period,
            'currency': self.currency
        }
        
        # 階層ごとの使用数をカウント
        layer_counts = {}
        for node_id in self.used_ids:
            match = self.id_pattern.match(node_id)
            if match:
                layer = int(match.group(2))
                layer_counts[layer] = layer_counts.get(layer, 0) + 1
        
        stats['ids_per_layer'] = layer_counts
        
        return stats
    
    def reset_layer(self, layer: int):
        """
        特定階層のカウンタをリセット
        
        Args:
            layer: リセットする階層
        """
        if layer in self.counters:
            del self.counters[layer]
        
        # 該当階層のIDを削除
        to_remove = []
        for node_id in self.used_ids:
            match = self.id_pattern.match(node_id)
            if match and int(match.group(2)) == layer:
                to_remove.append(node_id)
        
        for node_id in to_remove:
            self.used_ids.remove(node_id)
        
        logger.info(f"Reset layer {layer}: removed {len(to_remove)} IDs")
    
    def export_to_file(self, filepath: Path):
        """
        使用済みIDをファイルにエクスポート
        
        Args:
            filepath: 出力ファイルパス
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            for node_id in sorted(self.used_ids):
                f.write(f"{node_id}\n")
        
        logger.info(f"Exported {len(self.used_ids)} IDs to {filepath}")
    
    def import_from_file(self, filepath: Path):
        """
        ファイルからIDをインポート
        
        Args:
            filepath: 入力ファイルパス
        """
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            ids = [line.strip() for line in f if line.strip()]
        
        self.load_existing_ids(ids)
        logger.info(f"Imported {len(ids)} IDs from {filepath}")


class MultiTimeframeIDManager:
    """複数時間足のID管理クラス"""
    
    # 時間足コード定義
    TIMEFRAME_CODES = {
        'M1': '1',   # 1分足
        'M5': '2',   # 5分足
        'M15': '3',  # 15分足
        'M30': '4',  # 30分足
        'H1': '5',   # 1時間足
        'H4': '6'    # 4時間足
    }
    
    # 通貨ペアコード定義
    CURRENCY_CODES = {
        'USDJPY': '1',
        'EURUSD': '2',
        'EURJPY': '3'
    }
    
    def __init__(self, period: str = "9"):
        """
        初期化
        
        Args:
            period: 周期コード（デフォルト: 9=共通）
        """
        self.period = period
        self.generators: Dict[str, NodeIDGenerator] = {}
    
    def get_generator(self, timeframe: str, currency: str) -> NodeIDGenerator:
        """
        指定時間足・通貨ペアのID生成器を取得
        
        Args:
            timeframe: 時間足（M1, M5, M15, M30, H1, H4）
            currency: 通貨ペア（USDJPY, EURUSD, EURJPY）
            
        Returns:
            NodeIDGenerator インスタンス
        """
        key = f"{timeframe}_{currency}"
        
        if key not in self.generators:
            tf_code = self.TIMEFRAME_CODES.get(timeframe, '3')
            cur_code = self.CURRENCY_CODES.get(currency, '1')
            
            self.generators[key] = NodeIDGenerator(
                timeframe=tf_code,
                period=self.period,
                currency=cur_code
            )
        
        return self.generators[key]
    
    def generate_id(self, timeframe: str, currency: str, layer: int) -> str:
        """
        IDを生成
        
        Args:
            timeframe: 時間足
            currency: 通貨ペア
            layer: 階層番号
            
        Returns:
            生成されたID
        """
        generator = self.get_generator(timeframe, currency)
        return generator.generate(layer)
    
    def get_all_statistics(self) -> Dict[str, Dict[str, any]]:
        """
        全ジェネレータの統計を取得
        
        Returns:
            統計情報の辞書
        """
        stats = {}
        for key, generator in self.generators.items():
            stats[key] = generator.get_statistics()
        return stats