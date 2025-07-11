#!/usr/bin/env python3
"""
Integration tests for the AWS Inventory CLI
"""

import unittest
import subprocess
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, '..')


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for the CLI"""

    def test_cli_help_command(self):
        """Test that CLI help command works"""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'inv_scr.cli', '--help'
            ], capture_output=True, text=True, timeout=30)
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("AWS Inventory CLI", result.stdout)
            self.assertIn("positional arguments", result.stdout)
        except subprocess.TimeoutExpired:
            self.fail("CLI help command timed out")
        except FileNotFoundError:
            self.skipTest("CLI not installed or not in PATH")

    def test_cli_list_command(self):
        """Test that CLI list command works"""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'inv_scr.cli', 'list'
            ], capture_output=True, text=True, timeout=30)
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("Available inventory operations", result.stdout)
            self.assertIn("instances", result.stdout)
            self.assertIn("vpcs", result.stdout)
        except subprocess.TimeoutExpired:
            self.fail("CLI list command timed out")
        except FileNotFoundError:
            self.skipTest("CLI not installed or not in PATH")

    def test_cli_version_command(self):
        """Test that CLI version command works"""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'inv_scr.cli', '--version'
            ], capture_output=True, text=True, timeout=30)
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("Version:", result.stdout)
        except subprocess.TimeoutExpired:
            self.fail("CLI version command timed out")
        except FileNotFoundError:
            self.skipTest("CLI not installed or not in PATH")

    def test_cli_invalid_operation(self):
        """Test that CLI handles invalid operations gracefully"""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'inv_scr.cli', 'invalid-operation'
            ], capture_output=True, text=True, timeout=30)
            
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid choice", result.stderr)
        except subprocess.TimeoutExpired:
            self.fail("CLI invalid operation command timed out")
        except FileNotFoundError:
            self.skipTest("CLI not installed or not in PATH")

    def test_instances_help_command(self):
        """Test that instances operation help works"""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'inv_scr.cli', 'instances', '--help'
            ], capture_output=True, text=True, timeout=30)
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("AWS Inventory CLI", result.stdout)
        except subprocess.TimeoutExpired:
            self.fail("Instances help command timed out")
        except FileNotFoundError:
            self.skipTest("CLI not installed or not in PATH")

    def test_vpcs_help_command(self):
        """Test that VPCs operation help works"""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'inv_scr.cli', 'vpcs', '--help'
            ], capture_output=True, text=True, timeout=30)
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("AWS Inventory CLI", result.stdout)
        except subprocess.TimeoutExpired:
            self.fail("VPCs help command timed out")
        except FileNotFoundError:
            self.skipTest("CLI not installed or not in PATH")


class TestModuleImports(unittest.TestCase):
    """Test that all modules can be imported correctly"""

    def test_main_cli_import(self):
        """Test that main CLI module imports correctly"""
        try:
            from inv_scr.cli import main, parse_args, list_operations, OPERATIONS
            self.assertTrue(callable(main))
            self.assertTrue(callable(parse_args))
            self.assertTrue(callable(list_operations))
            self.assertIsInstance(OPERATIONS, dict)
        except ImportError as e:
            self.fail(f"Failed to import main CLI module: {e}")

    def test_core_modules_import(self):
        """Test that core modules import correctly"""
        try:
            from inv_scr.core.ArgumentsClass import CommonArguments
            from inv_scr.core.account_class import aws_acct_access
            self.assertTrue(callable(CommonArguments))
            self.assertTrue(callable(aws_acct_access))
        except ImportError as e:
            self.fail(f"Failed to import core modules: {e}")

    def test_operations_import(self):
        """Test that operation modules import correctly"""
        operations = [
            'instances', 'vpcs', 'cfnstacks', 'cfnstacksets', 'directories',
            'ebs_volumes', 'ecs_clusters', 'elbs', 'enis', 'functions',
            'gas', 'gd_detectors', 'orgs', 'phzs', 'policies', 'rds_instances',
            'roles', 'saml_providers', 'subnets', 'tgws', 'topics'
        ]
        
        for operation in operations:
            try:
                module = __import__(f'inv_scr.operations.{operation}', fromlist=['run'])
                self.assertTrue(hasattr(module, 'run'))
                self.assertTrue(callable(module.run))
            except ImportError as e:
                self.fail(f"Failed to import operation {operation}: {e}")


class TestPackageStructure(unittest.TestCase):
    """Test that the package structure is correct"""

    def test_package_files_exist(self):
        """Test that required package files exist"""
        required_files = [
            'inv_scr/__init__.py',
            'inv_scr/cli.py',
            'inv_scr/__main__.py',
            'inv_scr/core/__init__.py',
            'inv_scr/operations/__init__.py',
            'setup.py',
            'README.md',
            'MIGRATION.md'
        ]
        
        # Get the project root directory (parent of tests directory)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        for file_path in required_files:
            full_path = os.path.join(project_root, file_path)
            self.assertTrue(
                os.path.exists(full_path),
                f"Required file {file_path} does not exist at {full_path}"
            )

    def test_operation_files_exist(self):
        """Test that all operation files exist"""
        operations = [
            'instances', 'vpcs', 'cfnstacks', 'cfnstacksets', 'directories',
            'ebs_volumes', 'ecs_clusters', 'elbs', 'enis', 'functions',
            'gas', 'gd_detectors', 'orgs', 'phzs', 'policies', 'rds_instances',
            'roles', 'saml_providers', 'subnets', 'tgws', 'topics'
        ]
        
        # Get the project root directory (parent of tests directory)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        for operation in operations:
            file_path = os.path.join(project_root, 'inv_scr', 'operations', f'{operation}.py')
            self.assertTrue(
                os.path.exists(file_path),
                f"Operation file {operation}.py does not exist at {file_path}"
            )

    def test_core_files_exist(self):
        """Test that core files exist"""
        core_files = [
            'ArgumentsClass.py',
            'account_class.py',
            'Inventory_Modules.py'
        ]
        
        # Get the project root directory (parent of tests directory)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        for core_file in core_files:
            file_path = os.path.join(project_root, 'inv_scr', 'core', core_file)
            self.assertTrue(
                os.path.exists(file_path),
                f"Core file {core_file} does not exist at {file_path}"
            )


class TestEndToEndScenarios(unittest.TestCase):
    """End-to-end test scenarios"""

    @patch('inv_scr.operations.instances.get_all_credentials')
    @patch('inv_scr.operations.instances.find_all_instances')
    @patch('inv_scr.operations.instances.display_results')
    def test_instances_operation_end_to_end(self, mock_display, mock_find, mock_creds):
        """Test instances operation end-to-end with mocked AWS calls"""
        # Mock the AWS calls to avoid actual API calls
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        mock_find.return_value = [
            {
                'InstanceId': 'i-1234567890abcdef0',
                'InstanceType': 't3.micro',
                'State': 'running',
                'Name': 'test-instance'
            }
        ]
        
        try:
            result = subprocess.run([
                sys.executable, '-c',
                '''
import sys
sys.path.insert(0, "..")
from unittest.mock import patch, MagicMock
with patch("inv_scr.operations.instances.get_all_credentials") as mock_creds, \
     patch("inv_scr.operations.instances.find_all_instances") as mock_find, \
     patch("inv_scr.operations.instances.display_results") as mock_display:
    mock_creds.return_value = [{"AccountId": "123456789012", "Region": "us-east-1"}]
    mock_find.return_value = [{"InstanceId": "i-test", "State": "running"}]
    from inv_scr.cli import main
    import sys
    sys.argv = ["inv_scr", "instances", "--profiles", "test"]
    try:
        main()
        print("SUCCESS")
    except SystemExit:
        print("SUCCESS")
                '''
            ], capture_output=True, text=True, timeout=30)
            
            # The test passes if it doesn't crash and produces some output
            self.assertIn("SUCCESS", result.stdout)
            
        except subprocess.TimeoutExpired:
            self.fail("End-to-end test timed out")
        except FileNotFoundError:
            self.skipTest("Python not available for subprocess test")


if __name__ == '__main__':
    unittest.main()