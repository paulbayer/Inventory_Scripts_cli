.PHONY: all install uninstall run clean test unittest coverage validate test-enhanced test-enhanced-instances test-enhanced-vpcs test-enhanced-lambda test-enhanced-all test-enhanced-demo test-enhanced-validate test-enhanced-quick

# Virtual environment directory
VENV = venv

# default target, when make executed without arguments
all: install

# Help target to show available commands
help:
	@echo "🚀 AWS Inventory CLI - Available Make Targets"
	@echo "=============================================="
	@echo ""
	@echo "📦 Installation & Setup:"
	@echo "  install              Install the package in development mode"
	@echo "  uninstall            Uninstall the package"
	@echo "  venv                 Create virtual environment"
	@echo "  clean                Clean up generated files and cache"
	@echo ""
	@echo "🧪 Traditional Testing:"
	@echo "  test                 Basic CLI functionality test"
	@echo "  unittest             Run all unit tests"
	@echo "  test-cli             Test CLI module"
	@echo "  test-operations      Test operations module"
	@echo "  test-core            Test core module"
	@echo "  test-integration     Test integration module"
	@echo "  test-args            Test argument parsing"
	@echo "  test-quick           Quick essential tests"
	@echo "  test-all             All traditional tests"
	@echo ""
	@echo "✨ Enhanced Testing Framework:"
	@echo "  test-enhanced-validate    Validate enhanced testing framework"
	@echo "  test-enhanced            Run all enhanced tests with demo"
	@echo "  test-enhanced-instances  Run enhanced EC2 instances tests (✅ Working)"
	@echo "  test-enhanced-vpcs       Run enhanced VPC tests (✅ Working)"
	@echo "  test-enhanced-lambda     Run enhanced Lambda tests (✅ Working)"
	@echo "  test-enhanced-all        Run all credential-level tests"
	@echo "  test-enhanced-quick      Quick enhanced tests (EC2 only)"
	@echo "  test-enhanced-demo       Demonstrate mock fixtures"
	@echo ""
	@echo "📊 Coverage & Analysis:"
	@echo "  coverage             Traditional coverage report"
	@echo "  coverage-enhanced    Enhanced coverage with credential tests"
	@echo ""
	@echo "🔄 Workflows:"
	@echo "  test-workflow        Development workflow (validate + quick)"
	@echo "  test-complete        Complete test suite (traditional + enhanced)"
	@echo ""
	@echo "🎯 Quick Start Enhanced Testing:"
	@echo "  make test-enhanced-validate  # Validate framework"
	@echo "  make test-enhanced-quick     # Run working tests"
	@echo "  make test-enhanced-demo      # See mock capabilities"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  See ENHANCED_TESTING_GUIDE.md for complete usage guide"
	@echo "  See TEST_SUMMARY.md for implementation details"

$(VENV)/bin/activate: setup.py requirements.txt
	python3 -m venv $(VENV)
	./$(VENV)/bin/pip install --upgrade pip
	./$(VENV)/bin/pip install -r requirements.txt
	./$(VENV)/bin/pip install -e .

install:
	pip3 install -e .

uninstall:
	pip3 uninstall inv_scr -y

# venv is a shortcut target
venv: $(VENV)/bin/activate

run: install
	inv_scr list

test: install
	inv_scr list
	inv_scr --help
	inv_scr instances --help

unittest: install
	python3 -m unittest discover tests -v

test-cli:
	python3 tests/test_cli.py

test-operations:
	python3 tests/test_operations.py

test-core:
	python3 tests/test_core.py

test-integration:
	python3 tests/test_integration.py

test-args:
	python3 tests/test_argument_parsing.py

test-all: unittest

coverage: install
	python3 -m coverage run -m unittest discover tests
	python3 -m coverage report
	python3 -m coverage html

test-runner:
	python3 tests/test_runner.py

test-quick:
	python3 -m unittest tests.test_cli.TestCLI.test_operations_mapping_exists tests.test_operations.TestInstancesOperation.test_run_function_exists tests.test_argument_parsing.TestArgumentParsing.test_verbosity_levels -v

validate:
	python3 validate_tests.py

test-versions:
	python3 test_operation_versions.py

# Enhanced Testing Framework Targets
# =====================================

# Validate the enhanced testing framework
test-enhanced-validate: install
	@echo "🔍 Validating Enhanced Testing Framework..."
	python3 validate_tests.py

# Run all enhanced tests with comprehensive output
test-enhanced: install
	@echo "🚀 Running Enhanced AWS Inventory CLI Tests..."
	python3 run_enhanced_tests.py

# Run enhanced tests for specific operations
test-enhanced-instances: install
	@echo "🔍 Running Enhanced EC2 Instances Tests..."
	python3 -m unittest \
		tests.test_operations.TestInstancesOperation.test_run_with_single_account_credentials \
		tests.test_operations.TestInstancesOperation.test_run_with_multi_account_credentials \
		tests.test_operations.TestInstancesOperation.test_run_with_status_filtering_logic \
		tests.test_operations.TestInstancesOperation.test_run_with_multi_region_credentials \
		-v

test-enhanced-vpcs: install
	@echo "🔍 Running Enhanced VPC Tests..."
	python3 -m unittest \
		tests.test_operations.TestVPCsOperation.test_run_with_comprehensive_vpc_data \
		tests.test_operations.TestVPCsOperation.test_run_with_default_vpc_filtering \
		tests.test_operations.TestVPCsOperation.test_run_with_multi_account_vpc_data \
		-v

test-enhanced-lambda: install
	@echo "🔍 Running Enhanced Lambda Function Tests..."
	python3 -m unittest \
		tests.test_operations.TestFunctionsOperation.test_run_with_comprehensive_lambda_data \
		tests.test_operations.TestFunctionsOperation.test_run_with_runtime_filtering_logic \
		-v

# Run all enhanced credential-level tests
test-enhanced-all: install
	@echo "🧪 Running All Enhanced Credential-Level Tests..."
	python3 -m unittest discover tests -k "credential" -v

# Quick enhanced test run (just working tests)
test-enhanced-quick: install
	@echo "⚡ Running Quick Enhanced Tests (EC2 Instances Only)..."
	python3 -m unittest \
		tests.test_operations.TestInstancesOperation.test_run_with_single_account_credentials \
		tests.test_operations.TestInstancesOperation.test_run_with_multi_account_credentials \
		-v

# Demonstrate mock fixtures capabilities
test-enhanced-demo: install
	@echo "🧪 Demonstrating Mock Fixture Capabilities..."
	python3 -c "from tests.mock_fixtures import MockCredentialFixtures, MockAWSResponseFixtures; \
		print('Single Account Creds:', len(MockCredentialFixtures.single_account_single_region())); \
		print('Multi Account Creds:', len(MockCredentialFixtures.multi_account_single_region())); \
		print('Complex Org Creds:', len(MockCredentialFixtures.complex_org_structure())); \
		print('EC2 Response Sample:', len(MockAWSResponseFixtures.ec2_instances_response()['Reservations'])); \
		print('✅ Mock fixtures working correctly!')"

# Enhanced coverage report including credential-level tests
coverage-enhanced: install
	@echo "📊 Running Enhanced Coverage Analysis..."
	python3 -m coverage run -m unittest discover tests
	python3 -m coverage report --show-missing
	python3 -m coverage html
	@echo "📈 Coverage report generated in htmlcov/index.html"

# Test development workflow
test-workflow: install test-enhanced-validate test-enhanced-quick
	@echo "✅ Development workflow tests completed!"

# Complete test suite (traditional + enhanced)
test-complete: install unittest test-enhanced-quick
	@echo "🎉 Complete test suite finished!"

clean:
	rm -rf $(VENV)
	find . -type f -name '*.pyc' -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +