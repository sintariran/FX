# Suggested Development Commands

## Testing Commands
```bash
# Basic system test (no external dependencies)
python3 simple_test.py

# Full integration test (requires pandas, numpy)
python3 test_system_integration.py

# Run all test suites
python3 run_all_tests.py

# Pytest (if available)
pytest tests/
```

## Code Quality Commands
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Run all code quality checks together
black src/ && flake8 src/ && mypy src/
```

## Database Operations
```bash
# Initialize database
python3 -c "from src.utils.database import DatabaseManager; DatabaseManager('./data/fx_trading.db')"

# Import historical data (if available)
python3 src/data/historical_data_fetcher.py
```

## Environment Setup
```bash
# Install dependencies (Poetry)
poetry install

# Or with pip
pip install -r requirements.txt

# Create environment file from template
cp .env.template .env
# Then edit .env with OANDA credentials

# Create production environment
cp production.env.template production.env
```

## Development Workflow
```bash
# Start development
1. Activate virtual environment
2. Run: python3 simple_test.py (verify basic functionality)
3. Run: python3 test_system_integration.py (full test)
4. Code changes
5. Run: black src/ && flake8 src/ && mypy src/
6. Run tests again

# Deployment (production)
./deploy.sh
```

## OANDA API Setup
```bash
# Required environment variables in .env:
OANDA_API_KEY=your_api_key
OANDA_ACCOUNT_ID=your_account_id
OANDA_ENV=practice  # or 'live' for production
```

## Performance Profiling
```bash
# Memory profiling
python3 -m memory_profiler script_name.py

# Performance profiling with py-spy
py-spy top --pid <process_id>
```

## System Utilities (macOS)
```bash
# File operations
ls -la                    # List files
find . -name "*.py"       # Find Python files
grep -r "pattern" src/    # Search in source

# Git operations
git status
git add .
git commit -m "message"
git push origin feature/branch-name

# Process monitoring
ps aux | grep python      # Find Python processes
kill -9 <pid>            # Kill process
```