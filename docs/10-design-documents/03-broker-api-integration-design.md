# FX取引システム ブローカーAPI連携設計書

## 1. 概要

### 1.1 目的
本設計書は、FX取引システムとOANDA v20 APIの連携に関する詳細設計を定義する。

### 1.2 スコープ
- OANDA v20 APIとの接続管理
- リアルタイム価格データの取得
- 取引注文の実行とポジション管理
- エラーハンドリングとリトライ機構

### 1.3 前提条件
- OANDA取引口座（デモ/本番）
- APIアクセストークン
- Python v20ライブラリ（pip install v20）
- 安定したインターネット接続

## 2. API接続設計

### 2.1 接続アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│             FX取引システム                           │
│  ┌─────────────────────────────────────────────┐   │
│  │           API接続マネージャー                 │   │
│  │  ┌───────────┐  ┌──────────┐  ┌─────────┐ │   │
│  │  │ 接続プール │  │ 認証管理 │  │ リトライ │ │   │
│  │  │           │  │          │  │ ロジック │ │   │
│  │  └───────────┘  └──────────┘  └─────────┘ │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │           データストリーミング                 │   │
│  │  ┌───────────┐  ┌──────────┐  ┌─────────┐ │   │
│  │  │ 価格     │  │ イベント │  │ トランザ │ │   │
│  │  │ ストリーム│  │ ストリーム│  │ クション │ │   │
│  │  └───────────┘  └──────────┘  └─────────┘ │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │           取引実行エンジン                     │   │
│  │  ┌───────────┐  ┌──────────┐  ┌─────────┐ │   │
│  │  │ 注文管理  │  │ ポジション│  │ 履歴   │ │   │
│  │  │          │  │ 管理      │  │ 管理    │ │   │
│  │  └───────────┘  └──────────┘  └─────────┘ │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                      │ HTTPS/WebSocket
┌──────────────────────┴──────────────────────────────┐
│                OANDA v20 API                        │
│  ┌─────────────┐  ┌────────────┐  ┌─────────────┐ │
│  │ REST API    │  │ Streaming  │  │ Account     │ │
│  │ Endpoints   │  │ Endpoints  │  │ Management  │ │
│  └─────────────┘  └────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 2.2 接続設定

#### 2.2.1 環境設定
```python
# 環境変数での設定管理
OANDA_ACCOUNT_ID = os.environ['OANDA_ACCOUNT_ID']
OANDA_ACCESS_TOKEN = os.environ['OANDA_ACCESS_TOKEN']
OANDA_ENVIRONMENT = os.environ.get('OANDA_ENV', 'practice')  # practice/live

# API エンドポイント
OANDA_ENDPOINTS = {
    'practice': 'api-fxpractice.oanda.com',
    'live': 'api-fxtrade.oanda.com'
}

# ストリーミングエンドポイント
OANDA_STREAM_ENDPOINTS = {
    'practice': 'stream-fxpractice.oanda.com',
    'live': 'stream-fxtrade.oanda.com'
}
```

#### 2.2.2 接続プール管理
```python
class OandaConnectionPool:
    """OANDA API接続プール管理"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.rest_pool = []
        self.stream_pool = []
        self.lock = threading.Lock()
        
    def get_rest_connection(self) -> v20.Context:
        """REST API接続を取得"""
        with self.lock:
            if self.rest_pool:
                return self.rest_pool.pop()
            else:
                return self._create_rest_connection()
    
    def _create_rest_connection(self) -> v20.Context:
        """新規REST接続を作成"""
        return v20.Context(
            hostname=OANDA_ENDPOINTS[OANDA_ENVIRONMENT],
            port=443,
            token=OANDA_ACCESS_TOKEN,
            ssl=True,
            datetime_format='UNIX'
        )
```

## 3. データストリーミング設計

### 3.1 価格ストリーミング

#### 3.1.1 価格データストリーム
```python
class PriceStreamManager:
    """リアルタイム価格ストリーミング管理"""
    
    def __init__(self, instruments: List[str]):
        self.instruments = instruments
        self.stream_api = None
        self.is_running = False
        self.callbacks = {}
        
    async def start_streaming(self):
        """価格ストリーミング開始"""
        self.stream_api = v20.Context(
            hostname=OANDA_STREAM_ENDPOINTS[OANDA_ENVIRONMENT],
            port=443,
            token=OANDA_ACCESS_TOKEN,
            ssl=True
        )
        
        response = self.stream_api.pricing.stream(
            accountID=OANDA_ACCOUNT_ID,
            instruments=','.join(self.instruments),
            snapshot=True,
            includeHomeConversions=False
        )
        
        self.is_running = True
        await self._process_stream(response)
    
    async def _process_stream(self, response):
        """ストリームデータ処理"""
        async for msg_type, msg in response.stream():
            if msg_type == "pricing.Price":
                await self._handle_price(msg)
            elif msg_type == "pricing.PricingHeartbeat":
                await self._handle_heartbeat(msg)
```

#### 3.1.2 価格データ構造
```python
@dataclass
class PriceData:
    """価格データ構造"""
    instrument: str
    time: datetime
    bid: Decimal
    ask: Decimal
    mid: Decimal
    spread: Decimal
    volume: int = 0
    
    @classmethod
    def from_oanda_price(cls, price: dict) -> 'PriceData':
        """OANDA価格データから変換"""
        bid = Decimal(price.bids[0].price) if price.bids else None
        ask = Decimal(price.asks[0].price) if price.asks else None
        
        return cls(
            instrument=price.instrument,
            time=datetime.fromtimestamp(float(price.time)),
            bid=bid,
            ask=ask,
            mid=(bid + ask) / 2 if bid and ask else None,
            spread=ask - bid if bid and ask else None
        )
```

### 3.2 トランザクションストリーミング

```python
class TransactionStreamManager:
    """取引イベントストリーミング管理"""
    
    async def start_streaming(self):
        """トランザクションストリーミング開始"""
        response = self.stream_api.transaction.stream(
            accountID=OANDA_ACCOUNT_ID
        )
        
        async for msg_type, msg in response.stream():
            if msg_type == "transaction.Transaction":
                await self._handle_transaction(msg)
            elif msg_type == "transaction.TransactionHeartbeat":
                await self._handle_heartbeat(msg)
    
    async def _handle_transaction(self, transaction):
        """トランザクション処理"""
        if transaction.type == "ORDER_FILL":
            await self._process_order_fill(transaction)
        elif transaction.type == "STOP_LOSS_ORDER":
            await self._process_stop_loss(transaction)
        elif transaction.type == "TAKE_PROFIT_ORDER":
            await self._process_take_profit(transaction)
```

## 4. 取引実行設計

### 4.1 注文管理

#### 4.1.1 注文種別
```python
class OrderType(Enum):
    """注文種別"""
    MARKET = "MARKET"              # 成行注文
    LIMIT = "LIMIT"                # 指値注文
    STOP = "STOP"                  # 逆指値注文
    MARKET_IF_TOUCHED = "MIT"      # MIT注文
    
class OrderSide(Enum):
    """売買方向"""
    BUY = 1
    SELL = -1
```

#### 4.1.2 注文実行
```python
class OrderExecutor:
    """注文実行エンジン"""
    
    async def execute_market_order(
        self,
        instrument: str,
        units: int,
        side: OrderSide,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None
    ) -> OrderResult:
        """成行注文実行"""
        
        # 注文データ構築
        order_data = {
            "order": {
                "instrument": instrument,
                "units": str(units * side.value),
                "type": "MARKET",
                "positionFill": "DEFAULT"
            }
        }
        
        # ストップロス設定
        if stop_loss:
            order_data["order"]["stopLossOnFill"] = {
                "price": str(stop_loss),
                "timeInForce": "GTC"
            }
        
        # テイクプロフィット設定
        if take_profit:
            order_data["order"]["takeProfitOnFill"] = {
                "price": str(take_profit),
                "timeInForce": "GTC"
            }
        
        # 注文実行
        try:
            response = await self._send_order(order_data)
            return self._process_order_response(response)
        except Exception as e:
            return self._handle_order_error(e)
    
    async def _send_order(self, order_data: dict):
        """注文送信（リトライ機能付き）"""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                api = self.connection_pool.get_rest_connection()
                return api.order.create(
                    accountID=OANDA_ACCOUNT_ID,
                    **order_data
                )
            except v20.errors.V20Error as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    raise
```

### 4.2 ポジション管理

#### 4.2.1 ポジション追跡
```python
class PositionManager:
    """ポジション管理"""
    
    def __init__(self):
        self.positions = {}  # instrument -> Position
        self.lock = asyncio.Lock()
        
    async def update_position(self, instrument: str):
        """ポジション情報更新"""
        api = self.connection_pool.get_rest_connection()
        
        try:
            response = api.position.get(
                accountID=OANDA_ACCOUNT_ID,
                instrument=instrument
            )
            
            async with self.lock:
                if response.position:
                    self.positions[instrument] = Position(
                        instrument=instrument,
                        units=int(response.position.long.units) + 
                              int(response.position.short.units),
                        average_price=Decimal(response.position.long.averagePrice 
                                            or response.position.short.averagePrice),
                        unrealized_pnl=Decimal(response.position.unrealizedPL),
                        margin_used=Decimal(response.position.marginUsed)
                    )
                else:
                    self.positions.pop(instrument, None)
                    
        except v20.errors.V20Error as e:
            logger.error(f"Position update failed: {e}")
```

#### 4.2.2 ポジション修正
```python
class PositionModifier:
    """ポジション修正機能"""
    
    async def modify_position_stops(
        self,
        instrument: str,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None,
        trailing_stop_distance: Optional[Decimal] = None
    ):
        """ストップロス/テイクプロフィット修正"""
        
        # 既存の取引を取得
        trades = await self._get_open_trades(instrument)
        
        for trade in trades:
            modify_data = {}
            
            if stop_loss is not None:
                modify_data["stopLoss"] = {"price": str(stop_loss)}
                
            if take_profit is not None:
                modify_data["takeProfit"] = {"price": str(take_profit)}
                
            if trailing_stop_distance is not None:
                modify_data["trailingStopLoss"] = {
                    "distance": str(trailing_stop_distance)
                }
            
            if modify_data:
                await self._modify_trade(trade.id, modify_data)
```

## 5. エラーハンドリング

### 5.1 エラー種別と対処

#### 5.1.1 接続エラー
```python
class ConnectionErrorHandler:
    """接続エラーハンドラー"""
    
    async def handle_connection_error(self, error: Exception) -> bool:
        """接続エラー処理"""
        
        if isinstance(error, requests.exceptions.ConnectionError):
            # ネットワークエラー
            logger.error("Network connection error")
            await self._wait_and_reconnect()
            return True
            
        elif isinstance(error, v20.errors.V20Timeout):
            # タイムアウト
            logger.warning("API timeout")
            return True
            
        elif isinstance(error, v20.errors.V20ConnectionError):
            # OANDA接続エラー
            logger.error("OANDA connection error")
            await self._reset_connection()
            return True
            
        return False
    
    async def _wait_and_reconnect(self):
        """指数バックオフで再接続"""
        delays = [1, 2, 4, 8, 16]  # 秒
        
        for delay in delays:
            await asyncio.sleep(delay)
            if await self._test_connection():
                logger.info("Reconnection successful")
                return
                
        raise ConnectionError("Failed to reconnect after multiple attempts")
```

#### 5.1.2 取引エラー
```python
class TradingErrorHandler:
    """取引エラーハンドラー"""
    
    ERROR_ACTIONS = {
        "INSUFFICIENT_MARGIN": "reduce_position_size",
        "STOP_LOSS_ON_FILL_PRICE_DISTANCE_MAXIMUM_EXCEEDED": "adjust_stop_loss",
        "TAKE_PROFIT_ON_FILL_PRICE_DISTANCE_MAXIMUM_EXCEEDED": "adjust_take_profit",
        "MARKET_ORDER_REJECT": "retry_with_limit",
        "BOUNDS_VIOLATION": "check_trading_hours"
    }
    
    async def handle_trading_error(self, error: v20.errors.V20Error) -> OrderResult:
        """取引エラー処理"""
        
        error_type = self._extract_error_type(error)
        action = self.ERROR_ACTIONS.get(error_type)
        
        if action == "reduce_position_size":
            return await self._retry_with_reduced_size(error)
        elif action == "adjust_stop_loss":
            return await self._retry_with_adjusted_stops(error)
        elif action == "retry_with_limit":
            return await self._retry_as_limit_order(error)
        else:
            logger.error(f"Unhandled trading error: {error}")
            raise
```

### 5.2 レート制限対策

```python
class RateLimitManager:
    """レート制限管理（OANDAは制限なしだが、念のため）"""
    
    def __init__(self):
        self.request_times = deque(maxlen=1000)
        self.lock = asyncio.Lock()
        
    async def check_rate_limit(self):
        """レート制限チェック"""
        async with self.lock:
            now = time.time()
            self.request_times.append(now)
            
            # 直近1秒間のリクエスト数を確認
            recent_count = sum(1 for t in self.request_times if now - t < 1.0)
            
            if recent_count > 100:  # 安全マージン
                wait_time = 1.0 - (now - self.request_times[-100])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
```

## 6. データ同期とキャッシング

### 6.1 価格データ同期

```python
class PriceDataSynchronizer:
    """価格データ同期管理"""
    
    def __init__(self, redis_client: Redis, db: TimescaleDB):
        self.redis = redis_client
        self.db = db
        self.buffer = {}
        self.buffer_size = 100
        
    async def on_price_update(self, price: PriceData):
        """価格更新時の処理"""
        
        # 1. Redisキャッシュ更新（即座）
        await self._update_redis_cache(price)
        
        # 2. バッファに追加
        self._add_to_buffer(price)
        
        # 3. バッファサイズ確認
        if len(self.buffer[price.instrument]) >= self.buffer_size:
            await self._flush_to_database(price.instrument)
    
    async def _update_redis_cache(self, price: PriceData):
        """Redisキャッシュ更新"""
        key = f"price:{price.instrument}:latest"
        value = {
            "time": price.time.isoformat(),
            "bid": str(price.bid),
            "ask": str(price.ask),
            "mid": str(price.mid),
            "spread": str(price.spread)
        }
        await self.redis.hset(key, mapping=value)
        await self.redis.expire(key, 3600)  # 1時間TTL
```

### 6.2 取引データ同期

```python
class TradeDataSynchronizer:
    """取引データ同期管理"""
    
    async def on_trade_executed(self, trade: TradeExecution):
        """取引実行時の処理"""
        
        # 1. イベントストアに記録
        await self._write_to_event_store(trade)
        
        # 2. データベースに保存
        await self._save_to_database(trade)
        
        # 3. キャッシュ更新
        await self._update_position_cache(trade)
        
    async def _write_to_event_store(self, trade: TradeExecution):
        """イベントストアへの書き込み"""
        event = {
            "timestamp": trade.timestamp.isoformat(),
            "event_type": "TRADE_EXECUTED",
            "data": {
                "order_id": trade.order_id,
                "instrument": trade.instrument,
                "side": trade.side.name,
                "units": trade.units,
                "price": str(trade.price),
                "pnl": str(trade.pnl) if trade.pnl else None
            }
        }
        
        # JSONL形式でファイルに追記
        filename = f"events/{trade.timestamp.strftime('%Y-%m-%d')}.jsonl"
        async with aiofiles.open(filename, 'a') as f:
            await f.write(json.dumps(event) + '\n')
```

## 7. 監視とアラート

### 7.1 接続監視

```python
class ConnectionMonitor:
    """接続状態監視"""
    
    def __init__(self):
        self.health_check_interval = 30  # 秒
        self.last_heartbeat = {}
        self.alert_threshold = 60  # 秒
        
    async def monitor_connections(self):
        """接続監視ループ"""
        while True:
            await asyncio.sleep(self.health_check_interval)
            
            # REST API健全性チェック
            if not await self._check_rest_api():
                await self._alert("REST API connection lost")
                
            # ストリーミング健全性チェック
            for stream_name, last_time in self.last_heartbeat.items():
                if time.time() - last_time > self.alert_threshold:
                    await self._alert(f"Stream {stream_name} heartbeat timeout")
    
    async def _check_rest_api(self) -> bool:
        """REST API健全性チェック"""
        try:
            api = self.connection_pool.get_rest_connection()
            api.account.get(accountID=OANDA_ACCOUNT_ID)
            return True
        except Exception as e:
            logger.error(f"REST API health check failed: {e}")
            return False
```

### 7.2 取引監視

```python
class TradingMonitor:
    """取引活動監視"""
    
    def __init__(self):
        self.metrics = {
            "orders_placed": 0,
            "orders_filled": 0,
            "orders_rejected": 0,
            "total_volume": 0,
            "total_pnl": Decimal("0")
        }
        
    async def on_order_event(self, event: OrderEvent):
        """注文イベント処理"""
        if event.type == "PLACED":
            self.metrics["orders_placed"] += 1
        elif event.type == "FILLED":
            self.metrics["orders_filled"] += 1
            self.metrics["total_volume"] += event.units
        elif event.type == "REJECTED":
            self.metrics["orders_rejected"] += 1
            
            # リジェクト率チェック
            reject_rate = self.metrics["orders_rejected"] / self.metrics["orders_placed"]
            if reject_rate > 0.1:  # 10%以上
                await self._alert(f"High order rejection rate: {reject_rate:.1%}")
```

## 8. パフォーマンス最適化

### 8.1 バッチ処理

```python
class BatchProcessor:
    """バッチ処理最適化"""
    
    def __init__(self):
        self.order_queue = asyncio.Queue(maxsize=100)
        self.batch_size = 10
        self.batch_timeout = 0.1  # 秒
        
    async def process_orders_batch(self):
        """注文のバッチ処理"""
        while True:
            batch = []
            deadline = time.time() + self.batch_timeout
            
            # バッチサイズまで注文を収集
            while len(batch) < self.batch_size and time.time() < deadline:
                try:
                    timeout = deadline - time.time()
                    order = await asyncio.wait_for(
                        self.order_queue.get(), 
                        timeout=max(0, timeout)
                    )
                    batch.append(order)
                except asyncio.TimeoutError:
                    break
            
            if batch:
                await self._execute_batch(batch)
```

### 8.2 キャッシュ戦略

```python
class CacheStrategy:
    """キャッシュ戦略"""
    
    def __init__(self):
        self.price_cache = TTLCache(maxsize=1000, ttl=60)
        self.position_cache = TTLCache(maxsize=100, ttl=300)
        
    async def get_cached_price(self, instrument: str) -> Optional[PriceData]:
        """キャッシュから価格取得"""
        # L1: メモリキャッシュ
        if instrument in self.price_cache:
            return self.price_cache[instrument]
            
        # L2: Redisキャッシュ
        redis_data = await self.redis.hgetall(f"price:{instrument}:latest")
        if redis_data:
            price = PriceData.from_dict(redis_data)
            self.price_cache[instrument] = price
            return price
            
        return None
```

## 9. テストとデバッグ

### 9.1 モックサーバー

```python
class OandaMockServer:
    """開発/テスト用モックサーバー"""
    
    def __init__(self):
        self.prices = {}
        self.orders = {}
        self.positions = {}
        
    async def simulate_price_stream(self, instruments: List[str]):
        """価格ストリームシミュレーション"""
        while True:
            for instrument in instruments:
                # ランダムウォークで価格を生成
                if instrument not in self.prices:
                    self.prices[instrument] = Decimal("100.000")
                    
                change = Decimal(random.gauss(0, 0.0001))
                self.prices[instrument] += change
                
                yield PriceData(
                    instrument=instrument,
                    time=datetime.now(),
                    bid=self.prices[instrument] - Decimal("0.001"),
                    ask=self.prices[instrument] + Decimal("0.001"),
                    mid=self.prices[instrument],
                    spread=Decimal("0.002")
                )
                
            await asyncio.sleep(0.1)
```

### 9.2 デバッグユーティリティ

```python
class DebugLogger:
    """デバッグ用ロガー"""
    
    def __init__(self, enable_request_logging: bool = False):
        self.enable_request_logging = enable_request_logging
        
    def log_api_request(self, method: str, endpoint: str, data: dict):
        """APIリクエストログ"""
        if self.enable_request_logging:
            logger.debug(f"API Request: {method} {endpoint}")
            logger.debug(f"Request Data: {json.dumps(data, indent=2)}")
            
    def log_api_response(self, response: dict):
        """APIレスポンスログ"""
        if self.enable_request_logging:
            logger.debug(f"API Response: {json.dumps(response, indent=2)}")
```

## 10. セキュリティ考慮事項

### 10.1 認証情報管理

```python
class SecureCredentialManager:
    """セキュアな認証情報管理"""
    
    def __init__(self):
        self.key_vault = self._init_key_vault()
        
    def get_api_token(self) -> str:
        """APIトークン取得"""
        # 環境変数から取得（本番環境）
        token = os.environ.get('OANDA_ACCESS_TOKEN')
        
        if not token and self.key_vault:
            # キーボルトから取得
            token = self.key_vault.get_secret('oanda-api-token')
            
        if not token:
            raise ValueError("API token not found")
            
        return token
```

### 10.2 通信セキュリティ

```python
class SecureConnection:
    """セキュアな通信設定"""
    
    def __init__(self):
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = True
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        # IP制限（オプション）
        self.allowed_ips = self._load_allowed_ips()
        
    def create_secure_session(self) -> requests.Session:
        """セキュアなHTTPセッション作成"""
        session = requests.Session()
        session.verify = True
        session.mount('https://', HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=3
        ))
        return session
```

---

最終更新日：2025年1月5日
バージョン：1.0