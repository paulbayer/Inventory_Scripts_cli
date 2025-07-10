# AWS Inventory CLI Test Suite

This directory contains comprehensive test cases for the AWS Inventory CLI tool. The test suite is designed to ensure reliability, maintainability, and correctness of the unified CLI application.

## Test Structure

### Test Files

| File | Purpose | Coverage |
|------|---------|----------|
| `test_cli.py` | Main CLI functionality tests | CLI entry point, argument parsing, operation routing |
| `test_operations.py` | Operation-specific tests | Individual inventory operations (instances, VPCs, etc.) |
| `test_core.py` | Core module tests | ArgumentsClass, account_class, shared utilities |
| `test_integration.py` | Integration tests | End-to-end CLI functionality, module imports |
| `test_argument_parsing.py` | Comprehensive argument tests | All argument combinations and edge cases |
| `test_runner.py` | Test execution utility | Test runner and suite management |
| `conftest.py` | Test configuration | Fixtures and test setup |

### Test Categories

#### 1. Unit Tests
- **CLI Module Tests** (`test_cli.py`)
  - Operation mapping validation
  - Argument parsing correctness
  - Main function execution paths
  - Error handling (KeyboardInterrupt, exceptions)
  - Help and list functionality

- **Operations Tests** (`test_operations.py`)
  - Individual operation functionality
  - Mock AWS API interactions
  - Data processing and filtering
  - Output formatting

- **Core Module Tests** (`test_core.py`)
  - ArgumentsClass functionality
  - Account class initialization
  - Credential management
  - Region validation

#### 2. Integration Tests
- **CLI Integration** (`test_integration.py`)
  - Command-line interface execution
  - Module import validation
  - Package structure verification
  - End-to-end operation flow

#### 3. Comprehensive Tests
- **Argument Parsing** (`test_argument_parsing.py`)
  - All argument combinations
  - Default value validation
  - Alias functionality
  - Environment variable handling
  - Complex argument scenarios

## Running Tests

### Prerequisites
```bash
# Install the package in development mode
pip install -e .

# Install test dependencies (optional)
pip install coverage pytest
```

### Running All Tests
```bash
# Using unittest discovery
python -m unittest discover tests -v

# Using the Makefile
make unittest

# Using the test runner
python tests/test_runner.py
```

### Running Specific Test Suites
```bash
# Individual test files
python tests/test_cli.py
python tests/test_operations.py
python tests/test_core.py
python tests/test_integration.py
python tests/test_argument_parsing.py

# Using Makefile targets
make test-cli
make test-operations
make test-core
make test-integration
make test-args
```

### Running with Coverage
```bash
# Generate coverage report
make coverage

# Manual coverage
python -m coverage run -m unittest discover tests
python -m coverage report
python -m coverage html
```

## Test Design Principles

### 1. Mocking Strategy
- **AWS API Calls**: All AWS API calls are mocked to avoid actual cloud interactions
- **File System**: File operations are mocked where appropriate
- **Network Calls**: No real network calls are made during testing
- **Credentials**: Mock credentials are used throughout

### 2. Test Isolation
- Each test is independent and can run in any order
- Setup and teardown ensure clean test environments
- No shared state between tests
- Mock objects are reset between tests

### 3. Comprehensive Coverage
- **Happy Path**: Normal operation scenarios
- **Error Handling**: Exception cases and error conditions
- **Edge Cases**: Boundary conditions and unusual inputs
- **Integration**: Cross-module functionality

### 4. Maintainability
- Clear test names describing what is being tested
- Comprehensive docstrings explaining test purpose
- Modular test structure for easy maintenance
- Consistent patterns across test files

## Test Fixtures and Mocks

### Common Fixtures (`conftest.py`)
- `mock_aws_credentials`: Standard AWS credential structure
- `mock_ec2_instances`: Sample EC2 instance data
- `mock_vpcs`: Sample VPC data
- `mock_args`: Standard command-line arguments

### Mock Patterns
```python
# Mocking AWS API calls
@patch('inv_scr.operations.instances.Inventory_Modules.find_account_instances2')
def test_find_instances(self, mock_find_account):
    mock_find_account.return_value = {...}

# Mocking CLI arguments
@patch('sys.argv', ['inv_scr', 'instances', '--profiles', 'test'])
def test_argument_parsing(self):
    args = parse_args()

# Mocking stdout for output testing
@patch('sys.stdout', new_callable=io.StringIO)
def test_output(self, mock_stdout):
    function_under_test()
    output = mock_stdout.getvalue()
```

## Test Data

### Sample AWS Resources
The test suite includes realistic sample data for:
- EC2 instances (running, stopped, various types)
- VPCs (default, custom, multiple CIDR blocks)
- AWS accounts (root, child, standalone)
- Regions and availability zones
- IAM roles and policies

### Test Scenarios
- **Single Account**: Testing with one AWS account
- **Multi-Account**: Testing across AWS Organizations
- **Multi-Region**: Testing across multiple AWS regions
- **Error Conditions**: Network failures, permission errors
- **Edge Cases**: Empty results, malformed data

## Continuous Integration

### Test Automation
The test suite is designed to run in CI/CD environments:
- No external dependencies (AWS accounts, network)
- Fast execution (all mocked)
- Clear pass/fail indicators
- Detailed error reporting

### Quality Gates
- **Code Coverage**: Minimum 80% coverage target
- **Test Pass Rate**: 100% tests must pass
- **Performance**: Tests complete within reasonable time
- **Reliability**: Tests are deterministic and repeatable

## Adding New Tests

### For New Operations
When adding a new inventory operation:

1. **Create operation tests** in `test_operations.py`:
```python
class TestNewOperation(unittest.TestCase):
    def test_run_function_exists(self):
        self.assertTrue(hasattr(new_operation, 'run'))
    
    def test_basic_execution(self):
        # Test the operation with mocked AWS calls
        pass
```

2. **Update integration tests** in `test_integration.py`:
```python
def test_new_operation_import(self):
    from inv_scr.operations import new_operation
    self.assertTrue(callable(new_operation.run))
```

3. **Add CLI tests** in `test_cli.py`:
```python
def test_new_operation_in_mapping(self):
    self.assertIn('new-operation', OPERATIONS)
```

### For New Features
When adding new CLI features:

1. **Add argument tests** in `test_argument_parsing.py`
2. **Add CLI tests** in `test_cli.py`
3. **Add integration tests** in `test_integration.py`
4. **Update fixtures** in `conftest.py` if needed

## Troubleshooting Tests

### Common Issues

1. **Import Errors**
   - Ensure the package is installed: `pip install -e .`
   - Check Python path configuration
   - Verify all `__init__.py` files exist

2. **Mock Failures**
   - Check mock patch paths are correct
   - Ensure mocks are applied in the right order
   - Verify mock return values match expected structure

3. **Test Isolation Issues**
   - Check for shared state between tests
   - Ensure proper setup/teardown
   - Verify mocks are reset between tests

### Debugging Tips
```bash
# Run tests with verbose output
python -m unittest tests.test_cli -v

# Run a specific test method
python -m unittest tests.test_cli.TestCLI.test_specific_method

# Run with debugging
python -m pdb tests/test_cli.py
```

## Performance Considerations

### Test Execution Speed
- All AWS API calls are mocked for speed
- No actual file I/O operations
- Minimal setup/teardown overhead
- Parallel test execution where possible

### Resource Usage
- Low memory footprint
- No persistent state
- Clean resource cleanup
- Efficient mock object usage

## Future Enhancements

### Planned Improvements
1. **Property-based testing** for argument validation
2. **Performance benchmarking** tests
3. **Security testing** for credential handling
4. **Compatibility testing** across Python versions
5. **Load testing** for large-scale operations

### Test Coverage Goals
- Achieve 90%+ code coverage
- Cover all error conditions
- Test all CLI argument combinations
- Validate all output formats
- Test cross-platform compatibility