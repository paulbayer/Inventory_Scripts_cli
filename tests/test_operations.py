#!/usr/bin/env python3
"""
Unit tests for operation modules
"""

import unittest
import sys
from unittest.mock import patch, MagicMock, call
import io

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, '..')

from inv_scr.operations import instances, vpcs, cfnstacks


class TestInstancesOperation(unittest.TestCase):
    """Test cases for the instances operation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_args = MagicMock()
        self.mock_args.Profiles = ['test-profile']
        self.mock_args.Regions = ['us-east-1']
        self.mock_args.Accounts = None
        self.mock_args.SkipAccounts = None
        self.mock_args.SkipProfiles = None
        self.mock_args.AccessRoles = None
        self.mock_args.RootOnly = False
        self.mock_args.Filename = None
        self.mock_args.Time = False
        self.mock_args.pStatus = None

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(instances, 'add_operation_args'))
        self.assertTrue(callable(instances.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(instances, 'run'))
        self.assertTrue(callable(instances.run))

    def test_find_all_instances_function_exists(self):
        """Test that find_all_instances function exists"""
        self.assertTrue(hasattr(instances, 'find_all_instances'))
        self.assertTrue(callable(instances.find_all_instances))

    @patch('inv_scr.operations.instances.get_all_credentials')
    @patch('inv_scr.operations.instances.find_all_instances')
    @patch('inv_scr.operations.instances.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of instances run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock instances found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'InstanceId': 'i-1234567890abcdef0',
                'InstanceType': 't3.micro',
                'State': 'running',
                'Name': 'test-instance',
                'PublicDNSName': 'ec2-1-2-3-4.compute-1.amazonaws.com',
                'ParentProfile': 'test-profile'
            }
        ]
        
        instances.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for EC2 instances", output)

    def test_find_all_instances_empty_credentials(self):
        """Test find_all_instances with empty credentials list"""
        result = instances.find_all_instances([])
        self.assertEqual(result, [])

    @patch('inv_scr.operations.instances.Inventory_Modules.find_account_instances2')
    def test_find_all_instances_with_mock_data(self, mock_find_account):
        """Test find_all_instances with mocked AWS data"""
        # Mock AWS response
        mock_find_account.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890abcdef0',
                            'InstanceType': 't3.micro',
                            'State': {'Name': 'running'},
                            'PublicDnsName': 'ec2-1-2-3-4.compute-1.amazonaws.com',
                            'Tags': [{'Key': 'Name', 'Value': 'test-instance'}]
                        }
                    ]
                }
            ]
        }
        
        credentials = [
            {
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'MgmtAccount': '123456789012',
                'ParentProfile': 'test-profile'
            }
        ]
        
        with patch('inv_scr.operations.instances.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            result = instances.find_all_instances(credentials)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['InstanceId'], 'i-1234567890abcdef0')
        self.assertEqual(result[0]['State'], 'running')
        self.assertEqual(result[0]['Name'], 'test-instance')

    @patch('inv_scr.operations.instances.Inventory_Modules.find_account_instances2')
    def test_find_all_instances_with_status_filter(self, mock_find_account):
        """Test find_all_instances with status filter"""
        # Mock AWS response with both running and stopped instances
        mock_find_account.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-running',
                            'InstanceType': 't3.micro',
                            'State': {'Name': 'running'},
                            'PublicDnsName': 'ec2-running.compute-1.amazonaws.com',
                            'Tags': [{'Key': 'Name', 'Value': 'running-instance'}]
                        },
                        {
                            'InstanceId': 'i-stopped',
                            'InstanceType': 't3.micro',
                            'State': {'Name': 'stopped'},
                            'PublicDnsName': '',
                            'Tags': [{'Key': 'Name', 'Value': 'stopped-instance'}]
                        }
                    ]
                }
            ]
        }
        
        credentials = [
            {
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'MgmtAccount': '123456789012',
                'ParentProfile': 'test-profile'
            }
        ]
        
        with patch('inv_scr.operations.instances.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            # Test filtering for running instances only
            result = instances.find_all_instances(credentials, fStatus='running')
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['InstanceId'], 'i-running')
        self.assertEqual(result[0]['State'], 'running')


class TestVPCsOperation(unittest.TestCase):
    """Test cases for the VPCs operation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_args = MagicMock()
        self.mock_args.Profiles = ['test-profile']
        self.mock_args.Regions = ['us-east-1']
        self.mock_args.Accounts = None
        self.mock_args.AccessRoles = None
        self.mock_args.SkipProfiles = None
        self.mock_args.SkipAccounts = None
        self.mock_args.RootOnly = False
        self.mock_args.Time = False
        self.mock_args.Filename = None
        self.mock_args.pDefault = False

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(vpcs, 'add_operation_args'))
        self.assertTrue(callable(vpcs.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(vpcs, 'run'))
        self.assertTrue(callable(vpcs.run))

    def test_find_all_vpcs_function_exists(self):
        """Test that find_all_vpcs function exists"""
        self.assertTrue(hasattr(vpcs, 'find_all_vpcs'))
        self.assertTrue(callable(vpcs.find_all_vpcs))

    @patch('inv_scr.operations.vpcs.get_all_credentials')
    @patch('inv_scr.operations.vpcs.find_all_vpcs')
    @patch('inv_scr.operations.vpcs.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of VPCs run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1'}
        ]
        
        # Mock VPCs found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'VpcId': 'vpc-12345678',
                'VpcName': 'test-vpc',
                'CIDR': '10.0.0.0/16',
                'IsDefault': False
            }
        ]
        
        vpcs.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()

    @patch('inv_scr.operations.vpcs.Inventory_Modules.find_account_vpcs2')
    def test_find_all_vpcs_with_mock_data(self, mock_find_account):
        """Test find_all_vpcs with mocked AWS data"""
        # Mock AWS response
        mock_find_account.return_value = {
            'Vpcs': [
                {
                    'VpcId': 'vpc-12345678',
                    'IsDefault': False,
                    'CidrBlockAssociationSet': [
                        {'CidrBlock': '10.0.0.0/16'}
                    ],
                    'Tags': [{'Key': 'Name', 'Value': 'test-vpc'}]
                }
            ]
        }
        
        credentials = [
            {
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'MgmtAccount': '123456789012'
            }
        ]
        
        result = vpcs.find_all_vpcs(credentials)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['VpcId'], 'vpc-12345678')
        self.assertEqual(result[0]['VpcName'], 'test-vpc')
        self.assertEqual(result[0]['CIDR'], '10.0.0.0/16')
        self.assertFalse(result[0]['IsDefault'])


class TestPlaceholderOperations(unittest.TestCase):
    """Test cases for placeholder operations"""

    def test_cfnstacks_placeholder(self):
        """Test that cfnstacks operation is a placeholder"""
        self.assertTrue(hasattr(cfnstacks, 'run'))
        self.assertTrue(callable(cfnstacks.run))
        
        mock_args = MagicMock()
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            cfnstacks.run(mock_args)
            output = mock_stdout.getvalue()
            self.assertIn("Implementation coming soon", output)

    def test_all_placeholder_operations_have_required_functions(self):
        """Test that all placeholder operations have required functions"""
        placeholder_operations = [
            'cfnstacks', 'cfnstacksets', 'directories', 'ebs_volumes',
            'ecs_clusters', 'elbs', 'enis', 'functions', 'gas',
            'gd_detectors', 'orgs', 'phzs', 'policies', 'rds_instances',
            'roles', 'saml_providers', 'subnets', 'tgws', 'topics'
        ]
        
        for operation_name in placeholder_operations:
            try:
                module = __import__(f'inv_scr.operations.{operation_name}', fromlist=['run', 'add_operation_args'])
                self.assertTrue(hasattr(module, 'run'))
                self.assertTrue(hasattr(module, 'add_operation_args'))
                self.assertTrue(callable(module.run))
                self.assertTrue(callable(module.add_operation_args))
            except ImportError as e:
                self.fail(f"Failed to import operation module {operation_name}: {e}")


if __name__ == '__main__':
    unittest.main()