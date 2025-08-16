# Task Completion Checklist

## When a Development Task is Completed

### 1. Code Quality Checks (Required)
```bash
# Format code with Black
black src/ tests/

# Lint with Flake8
flake8 src/ tests/

# Type check with MyPy
mypy src/
```

### 2. Testing (Required)
```bash
# Run basic functionality test
python3 simple_test.py

# Run integration tests (if dependencies available)
python3 test_system_integration.py

# Run comprehensive test suite
python3 run_all_tests.py
```

### 3. Performance Validation (For Core Logic Changes)
- Verify execution times meet targets from memo files:
  - Overall: <19ms
  - Momi processing: <77ms
  - OP branching: <101.3ms
  - Overshoot: <550.6ms
  - Time combination: <564.9ms

### 4. Database Consistency (If Data Changes)
```bash
# Verify database integrity
python3 -c "from src.utils.database import DatabaseManager; db = DatabaseManager('./data/fx_trading.db'); print('DB OK')"
```

### 5. Documentation Updates (If Required)
- Update relevant files in `docs/` if business logic changes
- Maintain memo file references for traceability
- Update CLAUDE.md if system architecture changes

### 6. Environment Verification
```bash
# Demo account only until system verification complete
grep "OANDA_ENV=practice" .env || echo "WARNING: Verify demo mode"
```

### 7. Git Workflow (If Applicable)
```bash
git add .
git commit -m "descriptive message"
# Do NOT push to production until full validation
```

## Critical Notes
- **NEVER use live trading** until complete system verification
- **Always test with demo account first**
- **Verify PKG ID format compliance** for any PKG system changes
- **Maintain functional DAG architecture** - no branching search patterns
- **Preserve memo file encoding** (Shift-JIS) for original files