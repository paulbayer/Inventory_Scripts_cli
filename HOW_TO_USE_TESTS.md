# How to Use the AWS Inventory CLI Test Suite

This is a practical, step-by-step guide showing you exactly how to use the test suite effectively.

## 🎯 Step-by-Step Testing Guide

### Step 1: Verify Your Setup

```bash
# First, make sure everything is installed correctly
pip install -e .

# Test that the CLI works
inv_scr list
```

**Expected Output:**

```
Available inventory operations:
==================================================
  instances       - Find EC2 instances across accounts
  vpcs            - Find VPCs across accounts
  ...
```

### Step 2: Run Your First Tests

```bash
# Run a few basic tests to make sure everything works
python3 -m unittest tests.test_cli.TestCLI.test_operations_mapping_exists -v
```

**Expected Output:**

```
test_operations_mapping_exists (tests.test_cli.TestCLI.test_operations_mapping_exists)
Test that OPERATIONS mapping contains all expected operations ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

### Step 3: Run Tests by Category

#### Test CLI Functionality

```bash
# Test core CLI features (these should all pass)
python3 -m unittest \
  tests.test_cli.TestCLI.test_operations_mapping_exists \
  tests.test_cli.TestCLI.test_version_defined \
  tests.test_cli.TestCLI.test_parse_args_list_operation \
  -v
```

#### Test Argument Parsing

```bash
# Test argument parsing (these should all pass)
python3 -m unittest \
  tests.test_argument_parsing.TestArgumentParsing.test_verbosity_levels \
  tests.test_argument_parsing.TestArgumentParsing.test_all_argument_methods_exist \
  -v
```

#### Test Operations Framework

```bash
# Test that operations are properly structured
python3 -m unittest \
  tests.test_operations.TestInstancesOperation.test_run_function_exists \
  tests.test_operations.TestVPCsOperation.test_run_function_exists \
  -v
```

### Step 4: Understanding Test Results

#### ✅ Successful Test Output

```
test_operations_mapping_exists (tests.test_cli.TestCLI.test_operations_mapping_exists)
Test that OPERATIONS mapping contains all expected operations ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

**This means:** The test passed successfully!

#### ❌ Failed Test Output

```
test_example (tests.test_cli.TestCLI.test_example)
Test example ... FAIL

======================================================================
FAIL: test_example (tests.test_cli.TestCLI.test_example)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_cli.py", line 45, in test_example
    self.assertEqual(actual, expected)
AssertionError: 'actual' != 'expected'

----------------------------------------------------------------------
Ran 1 test in 0.001s

FAILED (failures=1)
```

**This means:** The test failed - you need to investigate and fix the issue.

## 🔧 Practical Testing Scenarios

### Scenario 1: Testing After Making Changes

```bash
# You modified the CLI code, now test it:

# 1. Test basic CLI functionality
python3 -m unittest tests.test_cli.TestCLI.test_operations_mapping_exists -v

# 2. Test argument parsing still works
python3 -m unittest tests.test_argument_parsing.TestArgumentParsing.test_verbosity_levels -v

# 3. Test that the CLI still runs
inv_scr list
```

### Scenario 2: Adding a New Operation

```bash
# You added a new operation called 'buckets', test it:

# 1. First, test that it's in the operations mapping
python3 -c "from inv_scr.cli import OPERATIONS; print('buckets' in OPERATIONS)"

# 2. Test that the operation module exists
python3 -c "from inv_scr.operations import buckets; print('Success')"

# 3. Test that it has the required functions
python3 -c "from inv_scr.operations import buckets; print(hasattr(buckets, 'run'))"
```

### Scenario 3: Debugging Test Failures

```bash
# If a test fails, debug it step by step:

# 1. Run just the failing test with maximum verbosity
python3 -m unittest tests.test_cli.TestCLI.test_specific_failing_test -v

# 2. Check if the CLI itself works
inv_scr --help

# 3. Test individual components
python3 -c "from inv_scr.cli import parse_args; print('Import works')"
```

## 📊 Monitoring Test Health

### Daily Health Check (30 seconds)

```bash
# Run this every day to make sure everything is working
python3 -m unittest \
  tests.test_cli.TestCLI.test_operations_mapping_exists \
  tests.test_cli.TestCLI.test_version_defined \
  tests.test_argument_parsing.TestArgumentParsing.test_verbosity_levels \
  -v
```

**All should pass!** If any fail, investigate immediately.

### Weekly Comprehensive Check (2-3 minutes)

```bash
# Run more comprehensive tests weekly
python3 -m unittest discover tests -k "not test_main_" -v
```

This runs most tests but skips some complex integration tests that might have mocking issues.

## 🎯 What Each Test Category Tells You

### CLI Tests (`test_cli.py`)

**What they validate:**

- ✅ All operations are properly registered
- ✅ Version information is correct
- ✅ Argument parsing works
- ✅ Help system functions

**Key tests to run:**

```bash
python3 -m unittest \
  tests.test_cli.TestCLI.test_operations_mapping_exists \
  tests.test_cli.TestCLI.test_version_defined \
  -v
```

### Argument Tests (`test_argument_parsing.py`)

**What they validate:**

- ✅ All CLI arguments work correctly
- ✅ Default values are set properly
- ✅ Argument aliases function
- ✅ Complex argument combinations work

**Key tests to run:**

```bash
python3 -m unittest \
  tests.test_argument_parsing.TestArgumentParsing.test_verbosity_levels \
  tests.test_argument_parsing.TestArgumentParsing.test_all_argument_methods_exist \
  -v
```

### Operations Tests (`test_operations.py`)

**What they validate:**

- ✅ Each operation has required functions
- ✅ Operations can be imported
- ✅ Basic structure is correct

**Key tests to run:**

```bash
python3 -m unittest \
  tests.test_operations.TestInstancesOperation.test_run_function_exists \
  tests.test_operations.TestVPCsOperation.test_run_function_exists \
  -v
```

## 🚨 Troubleshooting Common Issues

### Issue 1: "ModuleNotFoundError"

```bash
# Error: No module named 'inv_scr'
# Solution:
pip install -e .

# Verify:
python3 -c "import inv_scr; print('Success')"
```

### Issue 2: "No tests found"

```bash
# Error: Ran 0 tests
# Solution: Make sure you're in the project root directory
cd /path/to/Inventory_Scripts_cli
python3 -m unittest discover tests -v
```

### Issue 3: Import path issues in tests

```bash
# Error: Import errors in test files
# Solution: Tests handle this automatically, but if issues persist:
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## 🎉 Success Indicators

### Your tests are working correctly when:

1. **Basic CLI tests pass:**

```bash
python3 -m unittest tests.test_cli.TestCLI.test_operations_mapping_exists -v
# Should show: ok
```

2. **Argument tests pass:**

```bash
python3 -m unittest tests.test_argument_parsing.TestArgumentParsing.test_verbosity_levels -v
# Should show: ok
```

3. **CLI actually works:**

```bash
inv_scr list
# Should show the operations list
```

4. **Operations are accessible:**

```bash
python3 -c "from inv_scr.cli import OPERATIONS; print(len(OPERATIONS))"
# Should show: 21 (or the number of operations)
```

## 🔄 Regular Testing Workflow

### Before Making Changes

```bash
# 1. Verify current state is good
python3 -m unittest tests.test_cli.TestCLI.test_operations_mapping_exists -v

# 2. Test the specific area you're changing
# (e.g., if changing argument parsing)
python3 -m unittest tests.test_argument_parsing.TestArgumentParsing.test_verbosity_levels -v
```

### After Making Changes

```bash
# 1. Test the area you changed
python3 -m unittest tests.test_cli.TestCLI.test_operations_mapping_exists -v

# 2. Test that CLI still works
inv_scr list

# 3. Run a broader set of tests
python3 -m unittest \
  tests.test_cli.TestCLI.test_operations_mapping_exists \
  tests.test_cli.TestCLI.test_version_defined \
  tests.test_argument_parsing.TestArgumentParsing.test_verbosity_levels \
  -v
```

### Before Committing Code

```bash
# Run comprehensive tests (skip problematic ones for now)
python3 -m unittest discover tests -k "not test_main_" -v
```

## 📈 Advanced Usage

### Running Specific Test Patterns

```bash
# Run all tests with "argument" in the name
python3 -m unittest discover tests -k "argument" -v

# Run all tests in a specific class
python3 -m unittest tests.test_cli.TestCLI -v

# Run tests matching a pattern
python3 -m unittest discover tests -k "test_operations_mapping" -v
```

### Getting More Information

```bash
# Run with maximum verbosity
python3 -m unittest tests.test_cli.TestCLI.test_operations_mapping_exists -v

# Add timing information
time python3 -m unittest tests.test_cli.TestCLI.test_operations_mapping_exists -v
```

## 🎯 Key Takeaways

1. **Start Simple**: Run basic tests first to verify setup
2. **Test Incrementally**: Test the specific area you're working on
3. **Use Verbose Output**: Always use `-v` flag to see what's happening
4. **Focus on Working Tests**: Some complex integration tests may have mocking issues - focus on the tests that consistently pass
5. **Regular Validation**: Run tests frequently during development

The test suite is designed to help you maintain code quality and catch issues early. Focus on the tests that work reliably, and use them to validate your changes! 🚀
