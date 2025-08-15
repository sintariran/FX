"""
本番環境デプロイ設定
Week 5: Production Environment Configuration

機能:
1. 環境変数管理
2. セキュリティ設定
3. 本番用パラメータ調整
4. ログ設定
5. 監視設定
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Environment(Enum):
    """環境種別"""
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """データベース設定"""
    host: str
    port: int
    name: str
    user: str
    password: str
    ssl_mode: str = "require"
    connection_timeout: int = 30
    pool_size: int = 10


@dataclass
class ApiConfig:
    """API設定"""
    oanda_api_key: str
    oanda_account_id: str
    oanda_environment: str  # practice or live
    rate_limit_per_second: int = 100
    request_timeout: int = 30
    retry_attempts: int = 3


@dataclass
class TradingConfig:
    """取引設定"""
    initial_balance: float
    max_positions: int
    max_exposure: float
    max_daily_loss: float
    max_drawdown: float
    max_risk_per_trade: float
    allowed_symbols: list
    trading_hours_start: str = "09:00"
    trading_hours_end: str = "17:00"
    timezone: str = "Asia/Tokyo"


@dataclass
class PerformanceConfig:
    """パフォーマンス設定"""
    num_workers: int
    event_batch_size: int
    response_time_target_ms: float
    memory_limit_mb: int
    cpu_limit_percent: float


@dataclass
class SecurityConfig:
    """セキュリティ設定"""
    encryption_key: str
    jwt_secret: str
    ssl_cert_path: str
    ssl_key_path: str
    allowed_ips: list
    api_rate_limit: int = 1000
    session_timeout_minutes: int = 30


@dataclass
class MonitoringConfig:
    """監視設定"""
    log_level: str
    log_file_path: str
    metrics_endpoint: str
    alert_email: str
    slack_webhook_url: str
    health_check_interval: int = 30
    alert_thresholds: Dict[str, float] = None


class ProductionConfig:
    """本番環境設定管理"""
    
    def __init__(self, environment: Environment = Environment.PRODUCTION, template_mode: bool = False):
        self.environment = environment
        self.template_mode = template_mode
        self._load_environment_variables()
        if not template_mode:
            self._validate_configuration()
        self._setup_logging()
    
    def _load_environment_variables(self):
        """環境変数読み込み"""
        
        # データベース設定
        self.database = DatabaseConfig(
            host=self._get_env("DB_HOST", "localhost"),
            port=int(self._get_env("DB_PORT", "5432")),
            name=self._get_env("DB_NAME", "fx_trading"),
            user=self._get_env("DB_USER", "fx_user"),
            password=self._get_required_env("DB_PASSWORD"),
            ssl_mode=self._get_env("DB_SSL_MODE", "require"),
            connection_timeout=int(self._get_env("DB_CONNECTION_TIMEOUT", "30")),
            pool_size=int(self._get_env("DB_POOL_SIZE", "10"))
        )
        
        # API設定
        self.api = ApiConfig(
            oanda_api_key=self._get_required_env("OANDA_API_KEY"),
            oanda_account_id=self._get_required_env("OANDA_ACCOUNT_ID"),
            oanda_environment=self._get_env("OANDA_ENV", "practice"),
            rate_limit_per_second=int(self._get_env("API_RATE_LIMIT", "100")),
            request_timeout=int(self._get_env("API_TIMEOUT", "30")),
            retry_attempts=int(self._get_env("API_RETRY_ATTEMPTS", "3"))
        )
        
        # 取引設定
        self.trading = TradingConfig(
            initial_balance=float(self._get_env("TRADING_INITIAL_BALANCE", "1000000")),
            max_positions=int(self._get_env("TRADING_MAX_POSITIONS", "5")),
            max_exposure=float(self._get_env("TRADING_MAX_EXPOSURE", "500000")),
            max_daily_loss=float(self._get_env("TRADING_MAX_DAILY_LOSS", "50000")),
            max_drawdown=float(self._get_env("TRADING_MAX_DRAWDOWN", "0.05")),
            max_risk_per_trade=float(self._get_env("TRADING_MAX_RISK_PER_TRADE", "0.02")),
            allowed_symbols=self._get_env("TRADING_ALLOWED_SYMBOLS", "USDJPY,EURJPY,EURUSD").split(","),
            trading_hours_start=self._get_env("TRADING_HOURS_START", "09:00"),
            trading_hours_end=self._get_env("TRADING_HOURS_END", "17:00"),
            timezone=self._get_env("TRADING_TIMEZONE", "Asia/Tokyo")
        )
        
        # パフォーマンス設定
        self.performance = PerformanceConfig(
            num_workers=int(self._get_env("PERF_NUM_WORKERS", "6")),
            event_batch_size=int(self._get_env("PERF_BATCH_SIZE", "50")),
            response_time_target_ms=float(self._get_env("PERF_RESPONSE_TARGET_MS", "19.0")),
            memory_limit_mb=int(self._get_env("PERF_MEMORY_LIMIT_MB", "1024")),
            cpu_limit_percent=float(self._get_env("PERF_CPU_LIMIT_PERCENT", "80.0"))
        )
        
        # セキュリティ設定
        self.security = SecurityConfig(
            encryption_key=self._get_required_env("ENCRYPTION_KEY"),
            jwt_secret=self._get_required_env("JWT_SECRET"),
            ssl_cert_path=self._get_env("SSL_CERT_PATH", ""),
            ssl_key_path=self._get_env("SSL_KEY_PATH", ""),
            allowed_ips=self._get_env("ALLOWED_IPS", "").split(",") if self._get_env("ALLOWED_IPS") else [],
            api_rate_limit=int(self._get_env("SEC_API_RATE_LIMIT", "1000")),
            session_timeout_minutes=int(self._get_env("SEC_SESSION_TIMEOUT", "30"))
        )
        
        # 監視設定
        alert_thresholds = {
            "response_time_ms": float(self._get_env("ALERT_RESPONSE_TIME_MS", "50.0")),
            "error_rate_percent": float(self._get_env("ALERT_ERROR_RATE_PERCENT", "5.0")),
            "memory_usage_percent": float(self._get_env("ALERT_MEMORY_USAGE_PERCENT", "80.0")),
            "cpu_usage_percent": float(self._get_env("ALERT_CPU_USAGE_PERCENT", "80.0")),
            "drawdown_percent": float(self._get_env("ALERT_DRAWDOWN_PERCENT", "3.0"))
        }
        
        self.monitoring = MonitoringConfig(
            log_level=self._get_env("LOG_LEVEL", "INFO"),
            log_file_path=self._get_env("LOG_FILE_PATH", "/var/log/fx_trading.log"),
            metrics_endpoint=self._get_env("METRICS_ENDPOINT", "http://localhost:8086"),
            alert_email=self._get_env("ALERT_EMAIL", ""),
            slack_webhook_url=self._get_env("SLACK_WEBHOOK_URL", ""),
            health_check_interval=int(self._get_env("HEALTH_CHECK_INTERVAL", "30")),
            alert_thresholds=alert_thresholds
        )
    
    def _get_env(self, key: str, default: str = "") -> str:
        """環境変数取得"""
        return os.getenv(key, default)
    
    def _get_required_env(self, key: str) -> str:
        """必須環境変数取得"""
        value = os.getenv(key)
        if not value:
            if self.template_mode:
                return f"REQUIRED_{key}_VALUE"
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def _validate_configuration(self):
        """設定検証"""
        errors = []
        
        # 取引設定検証
        if self.trading.max_drawdown <= 0 or self.trading.max_drawdown > 1:
            errors.append("max_drawdown must be between 0 and 1")
        
        if self.trading.max_risk_per_trade <= 0 or self.trading.max_risk_per_trade > 0.1:
            errors.append("max_risk_per_trade must be between 0 and 0.1 (10%)")
        
        if self.trading.initial_balance <= 0:
            errors.append("initial_balance must be positive")
        
        # API設定検証
        if self.api.oanda_environment not in ["practice", "live"]:
            errors.append("oanda_environment must be 'practice' or 'live'")
        
        # パフォーマンス設定検証
        if self.performance.num_workers <= 0 or self.performance.num_workers > 20:
            errors.append("num_workers must be between 1 and 20")
        
        if self.performance.response_time_target_ms <= 0:
            errors.append("response_time_target_ms must be positive")
        
        # 本番環境専用検証
        if self.environment == Environment.PRODUCTION:
            if self.api.oanda_environment != "live":
                errors.append("Production environment must use live OANDA environment")
            
            if not self.security.ssl_cert_path or not self.security.ssl_key_path:
                errors.append("SSL certificates are required for production")
            
            if not self.monitoring.alert_email and not self.monitoring.slack_webhook_url:
                errors.append("Alert notification method is required for production")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def _setup_logging(self):
        """ログ設定"""
        
        # ログレベル設定
        log_level = getattr(logging, self.monitoring.log_level.upper())
        
        # フォーマッター設定
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - '
            '[%(filename)s:%(lineno)d] - PID:%(process)d'
        )
        
        # ファイルハンドラー
        if self.monitoring.log_file_path:
            try:
                file_handler = logging.FileHandler(self.monitoring.log_file_path)
                file_handler.setFormatter(formatter)
                file_handler.setLevel(log_level)
                
                # ルートロガー設定
                logger = logging.getLogger()
                logger.setLevel(log_level)
                logger.addHandler(file_handler)
                
            except Exception as e:
                print(f"Warning: Could not setup file logging: {e}")
        
        # コンソールハンドラー（開発環境のみ）
        if self.environment != Environment.PRODUCTION:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(log_level)
            
            logger = logging.getLogger()
            logger.addHandler(console_handler)
    
    def get_oanda_url(self) -> str:
        """OANDA API URL取得"""
        if self.api.oanda_environment == "live":
            return "https://api-fxtrade.oanda.com"
        else:
            return "https://api-fxpractice.oanda.com"
    
    def get_oanda_stream_url(self) -> str:
        """OANDA Stream URL取得"""
        if self.api.oanda_environment == "live":
            return "https://stream-fxtrade.oanda.com"
        else:
            return "https://stream-fxpractice.oanda.com"
    
    def is_production(self) -> bool:
        """本番環境判定"""
        return self.environment == Environment.PRODUCTION
    
    def to_dict(self) -> Dict[str, Any]:
        """設定辞書変換（機密情報除外）"""
        config_dict = {
            "environment": self.environment.value,
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "name": self.database.name,
                "user": self.database.user,
                "ssl_mode": self.database.ssl_mode,
                "connection_timeout": self.database.connection_timeout,
                "pool_size": self.database.pool_size
            },
            "api": {
                "oanda_environment": self.api.oanda_environment,
                "rate_limit_per_second": self.api.rate_limit_per_second,
                "request_timeout": self.api.request_timeout,
                "retry_attempts": self.api.retry_attempts
            },
            "trading": {
                "initial_balance": self.trading.initial_balance,
                "max_positions": self.trading.max_positions,
                "max_exposure": self.trading.max_exposure,
                "max_daily_loss": self.trading.max_daily_loss,
                "max_drawdown": self.trading.max_drawdown,
                "max_risk_per_trade": self.trading.max_risk_per_trade,
                "allowed_symbols": self.trading.allowed_symbols,
                "trading_hours_start": self.trading.trading_hours_start,
                "trading_hours_end": self.trading.trading_hours_end,
                "timezone": self.trading.timezone
            },
            "performance": {
                "num_workers": self.performance.num_workers,
                "event_batch_size": self.performance.event_batch_size,
                "response_time_target_ms": self.performance.response_time_target_ms,
                "memory_limit_mb": self.performance.memory_limit_mb,
                "cpu_limit_percent": self.performance.cpu_limit_percent
            },
            "monitoring": {
                "log_level": self.monitoring.log_level,
                "health_check_interval": self.monitoring.health_check_interval,
                "alert_thresholds": self.monitoring.alert_thresholds
            }
        }
        
        return config_dict
    
    def save_config_template(self, file_path: str):
        """設定テンプレートファイル保存"""
        template = {
            "# Database Configuration": None,
            "DB_HOST": "localhost",
            "DB_PORT": "5432", 
            "DB_NAME": "fx_trading",
            "DB_USER": "fx_user",
            "DB_PASSWORD": "your_db_password_here",
            
            "# OANDA API Configuration": None,
            "OANDA_API_KEY": "your_oanda_api_key_here",
            "OANDA_ACCOUNT_ID": "your_oanda_account_id_here",
            "OANDA_ENV": "practice",  # practice or live
            
            "# Trading Configuration": None,
            "TRADING_INITIAL_BALANCE": "1000000",
            "TRADING_MAX_POSITIONS": "5",
            "TRADING_MAX_EXPOSURE": "500000",
            "TRADING_MAX_DAILY_LOSS": "50000",
            "TRADING_MAX_DRAWDOWN": "0.05",
            "TRADING_MAX_RISK_PER_TRADE": "0.02",
            "TRADING_ALLOWED_SYMBOLS": "USDJPY,EURJPY,EURUSD",
            
            "# Security Configuration": None,
            "ENCRYPTION_KEY": "your_32_character_encryption_key_here",
            "JWT_SECRET": "your_jwt_secret_here",
            "SSL_CERT_PATH": "/path/to/ssl/cert.pem",
            "SSL_KEY_PATH": "/path/to/ssl/key.pem",
            
            "# Monitoring Configuration": None,
            "LOG_LEVEL": "INFO",
            "LOG_FILE_PATH": "/var/log/fx_trading.log",
            "ALERT_EMAIL": "admin@example.com",
            "SLACK_WEBHOOK_URL": "https://hooks.slack.com/your_webhook_url",
            
            "# Performance Configuration": None,
            "PERF_NUM_WORKERS": "6",
            "PERF_RESPONSE_TARGET_MS": "19.0",
            "PERF_MEMORY_LIMIT_MB": "1024"
        }
        
        with open(file_path, 'w') as f:
            f.write("# FX Trading System - Production Configuration Template\n")
            f.write("# Copy this file to .env and fill in the actual values\n\n")
            
            for key, value in template.items():
                if value is None:
                    f.write(f"\n{key}\n")
                else:
                    f.write(f"{key}={value}\n")


def load_production_config(env_file: Optional[str] = None) -> ProductionConfig:
    """本番設定読み込み"""
    
    # .envファイル読み込み
    if env_file and os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    # 環境判定
    env_name = os.getenv('ENVIRONMENT', 'production')
    environment = Environment(env_name)
    
    return ProductionConfig(environment)


def main():
    """設定テンプレート生成"""
    print("🏗️ Production Configuration Template Generator")
    print("=" * 60)
    
    # テンプレート生成
    config = ProductionConfig(Environment.DEVELOPMENT, template_mode=True)
    template_path = "production.env.template"
    config.save_config_template(template_path)
    
    print(f"✅ Configuration template saved to: {template_path}")
    print("\n📋 Next steps:")
    print("1. Copy the template to .env file")
    print("2. Fill in the actual values")
    print("3. Set ENVIRONMENT=production for production deployment")
    print("4. Ensure all required environment variables are set")
    
    # 設定例表示
    print(f"\n📊 Configuration Overview:")
    config_dict = config.to_dict()
    print(json.dumps(config_dict, indent=2))


if __name__ == "__main__":
    main()