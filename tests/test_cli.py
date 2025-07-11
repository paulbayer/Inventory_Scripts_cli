#!/usr/bin/env python3
"""
Unit tests for the main CLI module
"""

import unittest
import sys
import io
from unittest.mock import patch, MagicMock, call
import argparse

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, '..')

from inv_scr import cli
from inv_scr.cli import parse_args, list_operations, main, OPERATIONS


class TestCLI(unittest.TestCase):
    """Test cases for the main CLI functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.maxDiff = None

    def test_operations_mapping_exists(self):
        """Test that OPERATIONS mapping contains all expected operations"""
        expected_operations = [
            'instances', 'vpcs', 'cfnstacks', 'cfnstacksets', 'directories',
            'ebs-volumes', 'ecs-clusters', 'elbs', 'enis', 'functions',
            'gas', 'gd-detectors', 'orgs', 'phzs', 'policies', 'rds-instances',
            'roles', 'saml-providers', 'subnets', 'tgws', 'topics'
        ]
        
        for operation in expected_operations:
            self.assertIn(operation, OPERATIONS)
            self.assertTrue(callable(OPERATIONS[operation]))

    def test_version_defined(self):
        """Test that version is properly defined"""
        self.assertTrue(hasattr(cli, '__version__'))
        self.assertIsInstance(cli.__version__, str)
        self.assertRegex(cli.__version__, r'\d{4}\.\d{2}\.\d{2}')

    @patch('sys.argv', ['inv_scr', 'list'])
    def test_parse_args_list_operation(self):
        """Test parsing arguments for list operation"""
        args = parse_args()
        self.assertEqual(args.operation, 'list')

    @patch('sys.argv', ['inv_scr', 'instances', '--profiles', 'test-profile'])
    def test_parse_args_instances_operation(self):
        """Test parsing arguments for instances operation"""
        args = parse_args()
        self.assertEqual(args.operation, 'instances')
        self.assertEqual(args.Profiles, ['test-profile'])

    @patch('sys.argv', ['inv_scr', 'vpcs', '--regions', 'us-east-1', 'us-west-2'])
    def test_parse_args_vpcs_with_regions(self):
        """Test parsing arguments for VPCs with multiple regions"""
        args = parse_args()
        self.assertEqual(args.operation, 'vpcs')
        self.assertEqual(args.Regions, ['us-east-1', 'us-west-2'])

    @patch('sys.argv', ['inv_scr', 'instances', '--timing', '--verbose'])
    def test_parse_args_with_flags(self):
        """Test parsing arguments with timing and verbose flags"""
        args = parse_args()
        self.assertEqual(args.operation, 'instances')
        self.assertTrue(args.Time)
        # Verbose sets loglevel to WARNING (30)
        self.assertEqual(args.loglevel, 30)

    def test_parse_args_invalid_operation(self):
        """Test that invalid operations raise SystemExit"""
        with patch('sys.argv', ['inv_scr', 'invalid-operation']):
            with self.assertRaises(SystemExit):
                parse_args()

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_list_operations_output(self, mock_stdout):
        """Test that list_operations produces expected output"""
        list_operations()
        output = mock_stdout.getvalue()
        
        # Check that the output contains expected elements
        self.assertIn("Available inventory operations:", output)
        self.assertIn("instances", output)
        self.assertIn("vpcs", output)
        self.assertIn("Find EC2 instances across accounts", output)
        self.assertIn("Example usage:", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_list_operations_alphabetical_order(self, mock_stdout):
        """Test that operations are listed in alphabetical order"""
        list_operations()
        output = mock_stdout.getvalue()
        
        # Extract operation names from output
        lines = output.split('\n')
        operation_lines = [line for line in lines if line.strip().startswith('  ') and ' - ' in line]
        
        # Extract operation names (first word after spaces)
        operations = []
        for line in operation_lines:
            op_name = line.strip().split()[0]
            operations.append(op_name)
        
        # Verify they are in alphabetical order
        sorted_operations = sorted(operations)
        self.assertEqual(operations, sorted_operations, 
                        f"Operations not in alphabetical order. Got: {operations}, Expected: {sorted_operations}")

    @patch('inv_scr.cli.parse_args')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_list_operation(self, mock_stdout, mock_parse_args):
        """Test main function with list operation"""
        # Mock the arguments
        mock_args = MagicMock()
        mock_args.operation = 'list'
        mock_args.loglevel = 50  # CRITICAL
        mock_parse_args.return_value = mock_args
        
        main()
        
        output = sys.stdout.getvalue()
        self.assertIn("Available inventory operations:", output)

    @patch('inv_scr.cli.parse_args')
    @patch('inv_scr.operations.instances.run')
    def test_main_instances_operation(self, mock_instances_run, mock_parse_args):
        """Test main function with instances operation"""
        # Mock the arguments
        mock_args = MagicMock()
        mock_args.operation = 'instances'
        mock_args.loglevel = 50  # CRITICAL
        mock_args.Time = False
        mock_parse_args.return_value = mock_args
        
        with patch('sys.stdout', new_callable=io.StringIO):
            main()
        
        # Verify that the instances operation was called
        mock_instances_run.assert_called_once_with(mock_args)

    @patch('inv_scr.cli.parse_args')
    @patch('inv_scr.operations.vpcs.run')
    def test_main_vpcs_operation(self, mock_vpcs_run, mock_parse_args):
        """Test main function with VPCs operation"""
        # Mock the arguments
        mock_args = MagicMock()
        mock_args.operation = 'vpcs'
        mock_args.loglevel = 50  # CRITICAL
        mock_args.Time = False
        mock_parse_args.return_value = mock_args
        
        with patch('sys.stdout', new_callable=io.StringIO):
            main()
        
        # Verify that the VPCs operation was called
        mock_vpcs_run.assert_called_once_with(mock_args)

    @patch('inv_scr.cli.parse_args')
    @patch('inv_scr.operations.instances.run')
    def test_main_with_timing(self, mock_instances_run, mock_parse_args):
        """Test main function with timing enabled"""
        # Mock the arguments
        mock_args = MagicMock()
        mock_args.operation = 'instances'
        mock_args.loglevel = 50  # CRITICAL
        mock_args.Time = True
        mock_parse_args.return_value = mock_args
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            main()
        
        output = mock_stdout.getvalue()
        self.assertIn("operation_complete:", output)

    @patch('inv_scr.cli.parse_args')
    @patch('inv_scr.operations.instances.run')
    def test_main_keyboard_interrupt(self, mock_instances_run, mock_parse_args):
        """Test main function handles KeyboardInterrupt"""
        # Mock the arguments
        mock_args = MagicMock()
        mock_args.operation = 'instances'
        mock_args.loglevel = 50  # CRITICAL
        mock_parse_args.return_value = mock_args
        
        # Make the operation raise KeyboardInterrupt
        mock_instances_run.side_effect = KeyboardInterrupt()
        
        with patch('sys.stdout', new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as cm:
                main()
            
            self.assertEqual(cm.exception.code, 1)

    @patch('inv_scr.cli.parse_args')
    @patch('inv_scr.operations.instances.run')
    def test_main_exception_handling(self, mock_instances_run, mock_parse_args):
        """Test main function handles general exceptions"""
        # Mock the arguments
        mock_args = MagicMock()
        mock_args.operation = 'instances'
        mock_args.loglevel = 50  # CRITICAL
        mock_parse_args.return_value = mock_args
        
        # Make the operation raise a general exception
        mock_instances_run.side_effect = Exception("Test error")
        
        with patch('sys.stdout', new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as cm:
                main()
            
            self.assertEqual(cm.exception.code, 1)

    def test_all_operations_have_run_function(self):
        """Test that all operations in OPERATIONS mapping have a run function"""
        for operation_name, operation_func in OPERATIONS.items():
            self.assertTrue(callable(operation_func))
            # Check that it's actually a function (not just any callable)
            self.assertTrue(hasattr(operation_func, '__call__'))


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI functionality"""

    def test_cli_module_imports(self):
        """Test that all required modules can be imported"""
        try:
            from inv_scr.cli import main, parse_args, list_operations, OPERATIONS
            from inv_scr.core.ArgumentsClass import CommonArguments
            from inv_scr.operations import instances, vpcs
        except ImportError as e:
            self.fail(f"Failed to import required modules: {e}")

    def test_operations_modules_exist(self):
        """Test that all operation modules exist and have required functions"""
        operation_modules = [
            'instances', 'vpcs', 'cfnstacks', 'cfnstacksets', 'directories',
            'ebs_volumes', 'ecs_clusters', 'elbs', 'enis', 'functions',
            'gas', 'gd_detectors', 'orgs', 'phzs', 'policies', 'rds_instances',
            'roles', 'saml_providers', 'subnets', 'tgws', 'topics'
        ]
        
        for module_name in operation_modules:
            try:
                module = __import__(f'inv_scr.operations.{module_name}', fromlist=['run'])
                self.assertTrue(hasattr(module, 'run'))
                self.assertTrue(callable(module.run))
            except ImportError as e:
                self.fail(f"Failed to import operation module {module_name}: {e}")


if __name__ == '__main__':
    unittest.main()