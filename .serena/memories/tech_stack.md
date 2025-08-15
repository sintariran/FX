# Tech Stack and Dependencies

## Core Technologies
- **Python**: 3.11+ (primary language)
- **Package Management**: Poetry (pyproject.toml) + pip (requirements.txt for production)
- **Database**: SQLite (local development), PostgreSQL (production)
- **API Integration**: OANDA v20 API for forex data and trading

## Key Libraries
### Data Processing
- pandas 2.1.0+ (data manipulation)
- numpy 1.24.0+ (numerical computations)
- ta-lib 0.4.28 (technical analysis indicators)

### Web & API
- fastapi 0.104.1 (API framework)
- uvicorn 0.24.0 (ASGI server)
- httpx 0.25.2 / aiohttp 3.9.1 (HTTP clients)
- websockets 12.0 (real-time data streams)
- oandapyv20 0.7.2 (OANDA API client)

### Visualization & Analysis
- matplotlib 3.8.0 (plotting)
- plotly 5.17.0 (interactive charts)
- streamlit 1.28.0 (dashboard)
- seaborn 0.13.0 (statistical visualization)
- jupyter 1.0.0 (notebooks)

### Development & Testing
- pytest 7.4.0+ (testing framework)
- black 23.0.0+ (code formatting)
- flake8 6.0.0+ (linting)
- mypy 1.6.0+ (type checking)

### Production
- gunicorn 21.2.0 (WSGI server)
- prometheus_client 0.19.0 (monitoring)
- structlog 23.2.0 (logging)
- cryptography 42.0.0 (security)

## File Structure
```
FX/
├── src/                    # Source code
│   ├── indicators/         # Technical indicators
│   ├── operation_logic/    # Core trading logic from memo files
│   ├── utils/             # Database, OANDA client utilities
│   ├── pkg/               # PKG system implementation
│   ├── trading/           # Real-time trading engine
│   └── monitoring/        # Error handling and monitoring
├── docs/                  # Comprehensive documentation (UTF-8)
├── メモ/                  # Original 97 memo files (Shift-JIS)
├── data/                  # Historical data and databases
└── tests/                 # Test suites
```