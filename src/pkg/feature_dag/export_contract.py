"""
エクスポート契約システム (Export Contract System)
判定DAGへの標準化されたデータ提供インターフェース
"""

import logging
from typing import Dict, List, Any, Optional, Protocol, runtime_checkable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import statistics
import math

logger = logging.getLogger(__name__)

class DataQuality(Enum):
    """データ品質レベル"""
    EXCELLENT = "excellent"  # 0.9+
    GOOD = "good"           # 0.7-0.9
    FAIR = "fair"           # 0.5-0.7
    POOR = "poor"           # 0.3-0.5
    INVALID = "invalid"     # <0.3

@dataclass
class FeatureMetadata:
    """特徴量メタデータ"""
    source_node: str
    feature_name: str
    data_type: str
    timestamp: datetime
    quality_score: float
    version: str = "1.0"
    
    def get_quality_level(self) -> DataQuality:
        """品質レベルを取得"""
        if self.quality_score >= 0.9:
            return DataQuality.EXCELLENT
        elif self.quality_score >= 0.7:
            return DataQuality.GOOD
        elif self.quality_score >= 0.5:
            return DataQuality.FAIR
        elif self.quality_score >= 0.3:
            return DataQuality.POOR
        else:
            return DataQuality.INVALID

@dataclass
class StandardizedFeature:
    """標準化された特徴量"""
    id: str
    value: float
    metadata: FeatureMetadata
    confidence: float = 1.0
    dependencies: List[str] = field(default_factory=list)

@dataclass
class FeatureBundle:
    """特徴量バンドル（判定DAGへの単一エクスポート単位）"""
    timestamp: datetime
    currency_pair: str
    timeframe: str
    features: Dict[str, StandardizedFeature]
    quality_summary: Dict[str, Any]
    version: str = "1.0"
    
    def get_feature_vector(self, feature_names: Optional[List[str]] = None) -> List[float]:
        """特徴量ベクトルを取得"""
        if feature_names is None:
            feature_names = list(self.features.keys())
        
        vector = []
        for name in feature_names:
            if name in self.features:
                vector.append(self.features[name].value)
            else:
                vector.append(0.0)  # デフォルト値
        
        return vector
    
    def get_high_quality_features(self, min_quality: float = 0.7) -> Dict[str, StandardizedFeature]:
        """高品質特徴量のみを取得"""
        return {
            name: feature for name, feature in self.features.items()
            if feature.metadata.quality_score >= min_quality
        }

@runtime_checkable
class FeatureExporter(Protocol):
    """特徴量エクスポーターインターフェース"""
    
    def export_features(self, raw_features: Dict[str, Any]) -> FeatureBundle:
        """生の特徴量データを標準化してエクスポート"""
        ...
    
    def validate_export(self, bundle: FeatureBundle) -> tuple[bool, List[str]]:
        """エクスポートデータの妥当性を検証"""
        ...

class StandardFeatureExporter:
    """標準特徴量エクスポーター"""
    
    def __init__(self, currency_pair: str = "USDJPY", timeframe: str = "M1"):
        self.currency_pair = currency_pair
        self.timeframe = timeframe
        self.feature_mapping = self._initialize_feature_mapping()
        self.version = "1.0"
        
    def _initialize_feature_mapping(self) -> Dict[str, Dict[str, Any]]:
        """特徴量マッピング設定を初期化"""
        return {
            # 価格関連特徴量
            "price_change": {
                "description": "価格変化",
                "expected_range": [-0.01, 0.01],
                "normalization": "none"
            },
            "price_change_pct": {
                "description": "価格変化率",
                "expected_range": [-0.05, 0.05],
                "normalization": "minmax"
            },
            "price_momentum": {
                "description": "価格モメンタム",
                "expected_range": [-0.02, 0.02],
                "normalization": "zscore"
            },
            
            # 平均足関連特徴量
            "ha_direction": {
                "description": "平均足方向",
                "expected_range": [-1, 1],
                "normalization": "none"
            },
            
            # レンジ関連特徴量
            "range_width": {
                "description": "レンジ幅",
                "expected_range": [0, 0.01],
                "normalization": "minmax"
            },
            "range_position": {
                "description": "レンジ内位置",
                "expected_range": [0, 1],
                "normalization": "none"
            },
            "volatility_index": {
                "description": "ボラティリティ指数",
                "expected_range": [0, 0.01],
                "normalization": "minmax"
            },
            
            # 乖離関連特徴量
            "deviation_score": {
                "description": "乖離スコア",
                "expected_range": [0, 0.1],
                "normalization": "minmax"
            },
            "deviation_direction": {
                "description": "乖離方向",
                "expected_range": [-1, 1],
                "normalization": "none"
            },
            "confidence_level": {
                "description": "信頼度",
                "expected_range": [0, 1],
                "normalization": "none"
            },
            
            # パターン関連特徴量
            "momi_score": {
                "description": "もみ合いスコア",
                "expected_range": [0, 1],
                "normalization": "none"
            },
            "dokyaku_score": {
                "description": "同逆スコア",
                "expected_range": [0, 1],
                "normalization": "none"
            },
            
            # 統合信号
            "unified_signal": {
                "description": "統合信号",
                "expected_range": [0, 1],
                "normalization": "none"
            },
            "signal_strength": {
                "description": "信号強度",
                "expected_range": [0, 1],
                "normalization": "none"
            }
        }
    
    def export_features(self, raw_features: Dict[str, Any]) -> FeatureBundle:
        """生の特徴量データを標準化してエクスポート"""
        timestamp = datetime.now()
        standardized_features = {}
        
        # 生データから特徴量を抽出・標準化
        for node_id, node_data in raw_features.items():
            if isinstance(node_data, dict):
                for feature_name, value in node_data.items():
                    if isinstance(value, (int, float)) and feature_name in self.feature_mapping:
                        
                        # 標準化処理
                        normalized_value = self._normalize_feature(feature_name, float(value))
                        
                        # 品質スコア計算
                        quality_score = self._calculate_quality_score(feature_name, normalized_value)
                        
                        # メタデータ作成
                        metadata = FeatureMetadata(
                            source_node=node_id,
                            feature_name=feature_name,
                            data_type="float",
                            timestamp=timestamp,
                            quality_score=quality_score,
                            version=self.version
                        )
                        
                        # 標準化特徴量作成
                        feature_id = f"{self.currency_pair}_{self.timeframe}_{feature_name}"
                        standardized_features[feature_id] = StandardizedFeature(
                            id=feature_id,
                            value=normalized_value,
                            metadata=metadata,
                            confidence=quality_score,
                            dependencies=[node_id]
                        )
        
        # 品質サマリー計算
        quality_summary = self._calculate_quality_summary(standardized_features)
        
        return FeatureBundle(
            timestamp=timestamp,
            currency_pair=self.currency_pair,
            timeframe=self.timeframe,
            features=standardized_features,
            quality_summary=quality_summary,
            version=self.version
        )
    
    def _normalize_feature(self, feature_name: str, value: float) -> float:
        """特徴量の正規化"""
        mapping = self.feature_mapping.get(feature_name, {})
        normalization = mapping.get("normalization", "none")
        expected_range = mapping.get("expected_range", [-1, 1])
        
        if normalization == "none":
            return value
        elif normalization == "minmax":
            # [0, 1]に正規化
            min_val, max_val = expected_range
            if max_val != min_val:
                normalized = (value - min_val) / (max_val - min_val)
                return max(0.0, min(1.0, normalized))
            else:
                return 0.5
        elif normalization == "zscore":
            # 標準化（平均0、標準偏差1）
            # 簡易版：期待範囲の中央を平均、範囲の1/4を標準偏差と仮定
            mean = sum(expected_range) / 2
            std = (expected_range[1] - expected_range[0]) / 4
            if std > 0:
                return (value - mean) / std
            else:
                return 0.0
        else:
            return value
    
    def _calculate_quality_score(self, feature_name: str, value: float) -> float:
        """特徴量の品質スコアを計算"""
        mapping = self.feature_mapping.get(feature_name, {})
        expected_range = mapping.get("expected_range", [-1, 1])
        
        # 範囲内チェック
        min_val, max_val = expected_range
        if min_val <= value <= max_val:
            range_score = 1.0
        else:
            # 範囲外の場合、距離に応じてスコア減少
            if value < min_val:
                distance = min_val - value
            else:
                distance = value - max_val
            
            range_width = max_val - min_val
            penalty = min(1.0, distance / range_width)
            range_score = max(0.0, 1.0 - penalty)
        
        # 有効性チェック
        validity_score = 1.0
        if math.isnan(value) or math.isinf(value):
            validity_score = 0.0
        elif abs(value) > 1000:  # 異常に大きな値
            validity_score = 0.1
        
        return range_score * validity_score
    
    def _calculate_quality_summary(self, features: Dict[str, StandardizedFeature]) -> Dict[str, Any]:
        """品質サマリーを計算"""
        if not features:
            return {"overall_quality": 0.0, "feature_count": 0}
        
        quality_scores = [f.metadata.quality_score for f in features.values()]
        confidence_scores = [f.confidence for f in features.values()]
        
        # 品質レベル別カウント
        quality_levels = {}
        for feature in features.values():
            level = feature.metadata.get_quality_level().value
            quality_levels[level] = quality_levels.get(level, 0) + 1
        
        return {
            "overall_quality": statistics.mean(quality_scores),
            "feature_count": len(features),
            "quality_distribution": quality_levels,
            "avg_confidence": statistics.mean(confidence_scores),
            "min_quality": min(quality_scores),
            "max_quality": max(quality_scores),
            "valid_feature_ratio": sum(1 for score in quality_scores if score >= 0.3) / len(quality_scores)
        }
    
    def validate_export(self, bundle: FeatureBundle) -> tuple[bool, List[str]]:
        """エクスポートデータの妥当性を検証"""
        errors = []
        
        # 基本的な妥当性チェック
        if not bundle.features:
            errors.append("No features in bundle")
        
        if bundle.quality_summary.get("overall_quality", 0) < 0.3:
            errors.append("Overall quality too low")
        
        # 必須特徴量の存在チェック
        required_features = ["unified_signal", "signal_strength"]
        for req_feature in required_features:
            if not any(req_feature in feature_id for feature_id in bundle.features.keys()):
                errors.append(f"Missing required feature: {req_feature}")
        
        # 各特徴量の妥当性チェック
        for feature_id, feature in bundle.features.items():
            if feature.metadata.quality_score < 0.1:
                errors.append(f"Feature {feature_id} has very low quality: {feature.metadata.quality_score}")
            
            if math.isnan(feature.value) or math.isinf(feature.value):
                errors.append(f"Feature {feature_id} has invalid value: {feature.value}")
        
        return len(errors) == 0, errors
    
    def get_feature_schema(self) -> Dict[str, Any]:
        """特徴量スキーマを取得"""
        return {
            "version": self.version,
            "currency_pair": self.currency_pair,
            "timeframe": self.timeframe,
            "features": self.feature_mapping,
            "bundle_schema": {
                "timestamp": "datetime",
                "features": "Dict[str, StandardizedFeature]",
                "quality_summary": "Dict[str, Any]"
            }
        }

class VersionedExportManager:
    """バージョン管理付きエクスポートマネージャー"""
    
    def __init__(self):
        self.exporters: Dict[str, StandardFeatureExporter] = {}
        self.version_history: List[str] = []
        
    def register_exporter(self, version: str, exporter: StandardFeatureExporter) -> None:
        """エクスポーターを登録"""
        self.exporters[version] = exporter
        if version not in self.version_history:
            self.version_history.append(version)
            self.version_history.sort()
        
        logger.info(f"Registered feature exporter version {version}")
    
    def get_exporter(self, version: Optional[str] = None) -> StandardFeatureExporter:
        """指定バージョンのエクスポーターを取得"""
        if version is None:
            version = self.get_latest_version()
        
        if version not in self.exporters:
            raise ValueError(f"Exporter version {version} not found")
        
        return self.exporters[version]
    
    def get_latest_version(self) -> str:
        """最新バージョンを取得"""
        if not self.version_history:
            raise RuntimeError("No exporters registered")
        return self.version_history[-1]
    
    def list_versions(self) -> List[str]:
        """利用可能なバージョン一覧を取得"""
        return self.version_history.copy()
    
    def export_with_fallback(self, raw_features: Dict[str, Any], 
                           preferred_version: Optional[str] = None) -> FeatureBundle:
        """フォールバック付きエクスポート"""
        versions_to_try = []
        
        if preferred_version:
            versions_to_try.append(preferred_version)
        
        # 最新バージョンから古いバージョンの順でトライ
        for version in reversed(self.version_history):
            if version not in versions_to_try:
                versions_to_try.append(version)
        
        last_error = None
        for version in versions_to_try:
            try:
                exporter = self.get_exporter(version)
                bundle = exporter.export_features(raw_features)
                
                # 妥当性検証
                is_valid, errors = exporter.validate_export(bundle)
                if is_valid:
                    logger.info(f"Successfully exported with version {version}")
                    return bundle
                else:
                    logger.warning(f"Export validation failed for version {version}: {errors}")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Export failed with version {version}: {e}")
                continue
        
        # 全バージョンで失敗
        raise RuntimeError(f"All export versions failed. Last error: {last_error}")

# デフォルトエクスポートマネージャーのインスタンス
default_export_manager = VersionedExportManager()

# 標準エクスポーターを登録
default_exporter = StandardFeatureExporter()
default_export_manager.register_exporter("1.0", default_exporter)