.PHONY: all install uninstall run clean test unittest coverage validate

# Virtual environment directory
VENV = venv

# default target, when make executed without arguments
all: install

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

clean:
	rm -rf $(VENV)
	find . -type f -name '*.pyc' -delete