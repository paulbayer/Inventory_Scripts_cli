# AWS Inventory CLI - Testing Guide

This guide will help you effectively use the test suite, understand test results, and ensure all tests are working properly.

## 🚀 Quick Start

### 1. Initial Setup
```bash
# Ensure the package is installed in development mode
pip install -e .

# Install optional test dependencies for enhanced features
pip install coverage pytest
```

### 2. Verify Installation
```bash
# Test that the CLI is working
inv_scr list

# Run a quick smoke test
make test-quick
```

### 3. Run All Tests
```bash
# Run the complete test suite
make unittest
```

## 📋 Test Execution Methods

### Method 1: Using Makefile (Recommended)
```bash
# Run all tests with verbose output
make unittest

# Run specific test categories
make test-cli          # CLI functionality tests
make test-operations   # Operation-specific tests  
make test-core         # Core module tests
make test-integration  # Integration tests
make test-args         # Argument parsing tests

# Quick validation (runs fastest essential tests)
make test-quick

# Generate coverage report
make coverage
```

### Method 2: Direct Python Execution
```bash
# Run all tests using unittest discovery
python3 -m unittest discover tests -v

# Run specific test files
python3 tests/test_cli.py
python3 tests/test_operations.py
python3 tests/test_core.py
python3 tests/test_integration.py
python3 tests/test_argument_parsing.py

# Run specific test classes
python3 -m unittest tests.test_cli.TestCLI -v

# Run individual test methods
python3 -m unittest tests.test_cli.TestCLI.test_operations_mapping_exists -v
```

### Method 3: Using the Test Runner
```bash
# Run all tests with the custom test runner
python3 tests/test_runner.py

# Run specific test module
python3 tests/test_runner.py tests.test_cli
```

## 🔍 Understanding Test Output

### Successful Test Run
```
test_operations_mapping_exists (tests.test_cli.TestCLI.test_operations_mapping_exists)
Test that OPERATIONS mapping contains all expected operations ... ok
test_version_defined (tests.test_cli.TestCLI.test_version_defined)
Test that version is properly defined ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.001s

OK
```

### Failed Test Example
```
test_example_failure (tests.test_cli.TestCLI.test_example_failure)
Test that demonstrates a failure ... FAIL

======================================================================
FAIL: test_example_failure (tests.test_cli.TestCLI.test_example_failure)
Test that demonstrates a failure
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_cli.py", line 45, in test_example_failure
    self.assertEqual(actual, expected)
AssertionError: 'actual_value' != 'expected_value'

----------------------------------------------------------------------
Ran 1 tests in 0.001s

FAILED (failures=1)
```

### Test Status Indicators
- **`.`** - Test passed
- **`F`** - Test failed (assertion error)
- **`E`** - Test error (exception occurred)
- **`s`** - Test skipped
- **`x`** - Expected failure

## 🧪 Test Categories Explained

### 1. CLI Tests (`test_cli.py`)
**Purpose**: Validate main CLI functionality
```bash
# Run CLI tests
make test-cli

# What it tests:
# - Operation mapping correctness
# - Argument parsing
# - Main function execution
# - Error handling
# - Help system functionality
```

### 2. Operations Tests (`test_operations.py`)
**Purpose**: Test individual inventory operations
```bash
# Run operations tests
make test-operations

# What it tests:
# - Instances operation functionality
# - VPCs operation functionality
# - Placeholder operations structure
# - Mock AWS API interactions
# - Data processing and filtering
```

### 3. Core Tests (`test_core.py`)
**Purpose**: Test shared core functionality
```bash
# Run core tests
make test-core

# What it tests:
# - ArgumentsClass functionality
# - Account class initialization
# - Credential management
# - Region validation
```

### 4. Integration Tests (`test_integration.py`)
**Purpose**: Test end-to-end functionality
```bash
# Run integration tests
make test-integration

# What it tests:
# - CLI command execution
# - Module import validation
# - Package structure verification
# - Cross-module communication
```

### 5. Argument Tests (`test_argument_parsing.py`)
**Purpose**: Comprehensive argument validation
```bash
# Run argument tests
make test-args

# What it tests:
# - All CLI argument combinations
# - Default value handling
# - Argument aliases
# - Environment variable integration
# - Complex scenarios
```

## 📊 Coverage Analysis

### Generate Coverage Report
```bash
# Generate coverage report
make coverage

# This will create:
# - Terminal coverage summary
# - HTML coverage report in htmlcov/
```

### Understanding Coverage Output
```
Name                                 Stmts   Miss  Cover
--------------------------------------------------------
inv_scr/__init__.py                      0      0   100%
inv_scr/cli.py                          95     12    87%
inv_scr/operations/instances.py        120     25    79%
inv_scr/operations/vpcs.py             110     20    82%
--------------------------------------------------------
TOTAL                                  325     57    82%
```

### Coverage Goals
- **Target**: 80%+ overall coverage
- **Critical modules**: 90%+ coverage for CLI and core modules
- **New code**: 100% coverage for new features

## 🐛 Troubleshooting Common Issues

### Issue 1: Import Errors
```bash
# Error: ModuleNotFoundError: No module named 'inv_scr'
# Solution: Install in development mode
pip install -e .

# Verify installation
python3 -c "import inv_scr; print('Success')"
```

### Issue 2: Test Discovery Problems
```bash
# Error: No tests found
# Solution: Run from project root directory
cd /path/to/Inventory_Scripts_cli
python3 -m unittest discover tests -v
```

### Issue 3: Mock-related Failures
```bash
# Error: Mock object has no attribute 'some_method'
# Solution: Check mock setup in test
# Common fix: Ensure proper mock patching paths
```

### Issue 4: Path Issues
```bash
# Error: sys.path issues in tests
# Solution: Tests automatically handle path setup
# If issues persist, run from project root
```

## 🔧 Debugging Tests

### Running Tests with Debug Information
```bash
# Run with maximum verbosity
python3 -m unittest tests.test_cli -v

# Run single test with debugging
python3 -m pdb tests/test_cli.py

# Add debug prints in tests (temporary)
def test_example(self):
    print(f"Debug: value = {some_value}")
    self.assertEqual(actual, expected)
```

### Using Python Debugger
```python
# Add breakpoint in test
import pdb; pdb.set_trace()

# Run test - execution will pause at breakpoint
python3 tests/test_cli.py
```

## ✅ Validating Test Health

### Daily Test Validation
```bash
# Quick health check (runs in ~5 seconds)
make test-quick

# Expected output: All tests pass
# If any fail, investigate immediately
```

### Pre-commit Validation
```bash
# Before committing changes, run:
make unittest

# Ensure 100% pass rate before committing
```

### Comprehensive Validation
```bash
# Full test suite with coverage
make coverage

# Review coverage report
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

## 🎯 Best Practices

### 1. Test Execution Frequency
- **During Development**: Run relevant test category after changes
- **Before Commits**: Run full test suite (`make unittest`)
- **Daily**: Run quick validation (`make test-quick`)
- **Weekly**: Generate coverage report (`make coverage`)

### 2. Interpreting Results
- **All Green**: ✅ Ready to proceed
- **Any Red**: 🚨 Must fix before continuing
- **Coverage Drop**: 📉 Add tests for new code

### 3. Adding New Tests
When adding new functionality:
```bash
# 1. Add tests first (TDD approach)
# 2. Run tests to see them fail
make test-operations

# 3. Implement functionality
# 4. Run tests to see them pass
make test-operations

# 5. Verify overall test suite still passes
make unittest
```

## 🚀 Advanced Usage

### Running Tests in Parallel
```bash
# If you have pytest installed
pytest tests/ -n auto  # Runs tests in parallel
```

### Continuous Testing
```bash
# Watch for file changes and auto-run tests
# (requires installation of watchdog)
pip install pytest-watch
ptw tests/
```

### Performance Testing
```bash
# Time test execution
time make unittest

# Profile test performance
python3 -m cProfile tests/test_runner.py
```

## 📈 Monitoring Test Quality

### Key Metrics to Track
1. **Pass Rate**: Should always be 100%
2. **Coverage**: Target 80%+, critical modules 90%+
3. **Execution Time**: Should remain under 30 seconds
4. **Test Count**: Should grow with new features

### Regular Maintenance
- **Monthly**: Review and update test data
- **Quarterly**: Refactor tests for maintainability
- **With new features**: Add comprehensive test coverage

## 🎉 Success Indicators

### Your test suite is healthy when:
- ✅ All tests pass consistently
- ✅ Coverage is above target thresholds
- ✅ Tests run quickly (under 30 seconds)
- ✅ New features include tests
- ✅ Tests catch real bugs before deployment

### Red flags to watch for:
- 🚨 Intermittent test failures
- 🚨 Decreasing coverage over time
- 🚨 Tests taking too long to run
- 🚨 Tests that don't test real functionality

## 📞 Getting Help

### If tests are failing:
1. **Read the error message carefully**
2. **Check if it's an environment issue** (run `pip install -e .`)
3. **Verify you're in the project root directory**
4. **Check recent changes** that might have broken functionality
5. **Run individual test files** to isolate the problem

### Common commands for investigation:
```bash
# Check CLI is working
inv_scr list

# Test specific functionality
python3 -c "from inv_scr.cli import main; print('CLI import works')"

# Run minimal test
python3 -m unittest tests.test_cli.TestCLI.test_version_defined -v
```

This comprehensive testing guide ensures you can effectively use the test suite to maintain code quality and catch issues early in development! 🎯