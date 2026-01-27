#!/usr/bin/env python3
"""
Unit tests for operation modules
"""

import unittest
import sys
import socket
from unittest.mock import patch, MagicMock, call
import io
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, '..')

from inv_scr.operations import (
    instances, vpcs, cfnstacks, cfnstacksets, ebs_volumes, elbs, functions, orgs,
    rds_instances, subnets, phzs, enis, ecs_clusters, directories, gas, gd_detectors,
    policies, roles, saml_providers, tgws, topics, ram_shares, config_recorders,
    cloudtrail, azs, org_users
)
from tests.mock_fixtures import MockCredentialFixtures, MockAWSResponseFixtures, MockOperationHelpers


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

    # Enhanced credential-level mocking tests
    @patch('inv_scr.operations.instances.get_all_credentials')
    @patch('inv_scr.operations.instances.Inventory_Modules.find_account_instances2')
    @patch('inv_scr.operations.instances.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_single_account_credentials(self, mock_stdout, mock_display, mock_find_account, mock_get_creds):
        """Test complete run flow with single account credentials and realistic AWS response"""
        # Use shared test data system for more realistic and consistent data
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials
        
        # Use scenario-based AWS response for consistency
        mock_aws_response = MockAWSResponseFixtures.ec2_instances_response(num_instances=3, scenario='simple')
        mock_find_account.return_value = mock_aws_response
        
        # Create mock args using helper
        mock_args = MockOperationHelpers.create_mock_args(pStatus=None)
        
        with patch('inv_scr.operations.instances.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            instances.run(mock_args)
        
        # Verify credential handling
        mock_get_creds.assert_called_once()
        
        # Verify AWS API was called with correct credentials
        mock_find_account.assert_called_once_with(mock_credentials[0])
        
        # Verify display was called with processed results
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]  # First positional argument
        
        # Verify data transformation logic using shared test data
        self.assertEqual(len(display_args), 3)  # Should have 3 instances
        for instance in display_args:
            self.assertEqual(instance['AccountId'], '123456789012')
            self.assertEqual(instance['Region'], 'us-east-1')
            self.assertEqual(instance['ParentProfile'], 'test-profile')
            # Verify realistic instance naming from shared data
            self.assertTrue(instance['Name'].startswith('master-account-instance-'))
            self.assertIn(instance['State'], ['running', 'stopped'])

    @patch('inv_scr.operations.instances.get_all_credentials')
    @patch('inv_scr.operations.instances.Inventory_Modules.find_account_instances2')
    @patch('inv_scr.operations.instances.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_multi_account_credentials(self, mock_stdout, mock_display, mock_find_account, mock_get_creds):
        """Test complete run flow with multiple account credentials"""
        # Use multi-account credential fixture
        mock_credentials = MockCredentialFixtures.multi_account_single_region()
        mock_get_creds.return_value = mock_credentials
        
        # Mock different responses for different accounts
        def side_effect(credential):
            account_id = credential['AccountId']
            if account_id == '123456789012':
                return MockAWSResponseFixtures.ec2_instances_response(num_instances=2)
            elif account_id == '234567890123':
                return MockAWSResponseFixtures.ec2_instances_response(num_instances=1)
            else:
                return {'Reservations': []}  # Empty response for third account
        
        mock_find_account.side_effect = side_effect
        
        mock_args = MockOperationHelpers.create_mock_args()
        
        with patch('inv_scr.operations.instances.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            instances.run(mock_args)
        
        # Verify credentials were processed
        mock_get_creds.assert_called_once()
        
        # Verify AWS API was called for each account
        self.assertEqual(mock_find_account.call_count, 3)
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have instances from first two accounts (2 + 1 = 3 total)
        self.assertEqual(len(display_args), 3)
        
        # Verify account distribution
        account_counts = {}
        for instance in display_args:
            account_id = instance['AccountId']
            account_counts[account_id] = account_counts.get(account_id, 0) + 1
        
        self.assertEqual(account_counts.get('123456789012', 0), 2)
        self.assertEqual(account_counts.get('234567890123', 0), 1)
        self.assertEqual(account_counts.get('345678901234', 0), 0)

    @patch('inv_scr.operations.instances.get_all_credentials')
    @patch('inv_scr.operations.instances.Inventory_Modules.find_account_instances2')
    @patch('inv_scr.operations.instances.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_status_filtering_logic(self, mock_stdout, mock_display, mock_find_account, mock_get_creds):
        """Test that status filtering logic works correctly with realistic data"""
        mock_credentials = MockCredentialFixtures.single_account_single_region()
        mock_get_creds.return_value = mock_credentials
        
        # Create response with mixed instance states
        mock_aws_response = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-running1',
                            'InstanceType': 't3.micro',
                            'State': {'Name': 'running'},
                            'PublicDnsName': 'ec2-running1.compute-1.amazonaws.com',
                            'Tags': [{'Key': 'Name', 'Value': 'running-instance-1'}]
                        },
                        {
                            'InstanceId': 'i-stopped1',
                            'InstanceType': 't3.small',
                            'State': {'Name': 'stopped'},
                            'PublicDnsName': '',
                            'Tags': [{'Key': 'Name', 'Value': 'stopped-instance-1'}]
                        },
                        {
                            'InstanceId': 'i-running2',
                            'InstanceType': 't3.medium',
                            'State': {'Name': 'running'},
                            'PublicDnsName': 'ec2-running2.compute-1.amazonaws.com',
                            'Tags': [{'Key': 'Name', 'Value': 'running-instance-2'}]
                        }
                    ]
                }
            ]
        }
        mock_find_account.return_value = mock_aws_response
        
        # Test filtering for running instances only
        mock_args = MockOperationHelpers.create_mock_args(pStatus='running')
        
        with patch('inv_scr.operations.instances.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            instances.run(mock_args)
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should only have running instances (2 out of 3)
        self.assertEqual(len(display_args), 2)
        for instance in display_args:
            self.assertEqual(instance['State'], 'running')
            self.assertIn(instance['InstanceId'], ['i-running1', 'i-running2'])

    @patch('inv_scr.operations.instances.get_all_credentials')
    @patch('inv_scr.operations.instances.Inventory_Modules.find_account_instances2')
    @patch('inv_scr.operations.instances.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_multi_region_credentials(self, mock_stdout, mock_display, mock_find_account, mock_get_creds):
        """Test complete run flow with multi-region credentials"""
        mock_credentials = MockCredentialFixtures.single_account_multi_region()
        mock_get_creds.return_value = mock_credentials
        
        # Mock different responses for different regions
        def side_effect(credential):
            region = credential['Region']
            if region == 'us-east-1':
                return MockAWSResponseFixtures.ec2_instances_response(num_instances=2)
            elif region == 'us-west-2':
                return MockAWSResponseFixtures.ec2_instances_response(num_instances=1)
            else:  # eu-west-1
                return {'Reservations': []}  # Empty response
        
        mock_find_account.side_effect = side_effect
        
        mock_args = MockOperationHelpers.create_mock_args()
        
        with patch('inv_scr.operations.instances.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            instances.run(mock_args)
        
        # Verify AWS API was called for each region
        self.assertEqual(mock_find_account.call_count, 3)
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have instances from first two regions (2 + 1 = 3 total)
        self.assertEqual(len(display_args), 3)
        
        # Verify region distribution
        region_counts = {}
        for instance in display_args:
            region = instance['Region']
            region_counts[region] = region_counts.get(region, 0) + 1
        
        self.assertEqual(region_counts.get('us-east-1', 0), 2)
        self.assertEqual(region_counts.get('us-west-2', 0), 1)
        self.assertEqual(region_counts.get('eu-west-1', 0), 0)


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

    # Enhanced credential-level mocking tests for VPCs
    @patch('inv_scr.operations.vpcs.get_all_credentials')
    @patch('inv_scr.operations.vpcs.Inventory_Modules.find_account_vpcs2')
    @patch('inv_scr.operations.vpcs.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_comprehensive_vpc_data(self, mock_stdout, mock_display, mock_find_account, mock_get_creds):
        """Test complete VPC run flow with comprehensive credential and response mocking"""
        # Use mock credential fixture
        mock_credentials = MockCredentialFixtures.single_account_single_region()
        mock_get_creds.return_value = mock_credentials
        
        # Use mock AWS response fixture
        mock_aws_response = MockAWSResponseFixtures.vpc_response(num_vpcs=2)
        mock_find_account.return_value = mock_aws_response
        
        # Create mock args using helper
        mock_args = MockOperationHelpers.create_mock_args(pDefault=False)
        
        vpcs.run(mock_args)
        
        # Verify credential handling
        mock_get_creds.assert_called_once()
        
        # Verify AWS API was called with correct credentials and default flag
        mock_find_account.assert_called_once_with(mock_credentials[0], False)
        
        # Verify display was called with processed results
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Verify data transformation logic
        self.assertEqual(len(display_args), 2)  # Should have 2 VPCs
        for i, vpc in enumerate(display_args):
            self.assertEqual(vpc['AccountId'], '123456789012')
            self.assertEqual(vpc['Region'], 'us-east-1')
            self.assertEqual(vpc['VpcId'], f'vpc-{str(i).zfill(8)}abcdef{i}')
            self.assertEqual(vpc['VpcName'], f'master-account-vpc-def{i}')
            expected_cidr = '10.0.0.0/16' if i == 0 else '11.0.0.0/16'
            self.assertEqual(vpc['CIDR'], expected_cidr)
            self.assertEqual(vpc['IsDefault'], i == 0)  # First VPC is default

    @patch('inv_scr.operations.vpcs.get_all_credentials')
    @patch('inv_scr.operations.vpcs.Inventory_Modules.find_account_vpcs2')
    @patch('inv_scr.operations.vpcs.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_default_vpc_filtering(self, mock_stdout, mock_display, mock_find_account, mock_get_creds):
        """Test VPC filtering logic for default VPCs"""
        mock_credentials = MockCredentialFixtures.single_account_single_region()
        mock_get_creds.return_value = mock_credentials
        
        # Create response with mix of default and non-default VPCs
        mock_aws_response = {
            'Vpcs': [
                {
                    'VpcId': 'vpc-default123',
                    'IsDefault': True,
                    'CidrBlockAssociationSet': [{'CidrBlock': '172.31.0.0/16'}],
                    'Tags': [{'Key': 'Name', 'Value': 'default-vpc'}]
                },
                {
                    'VpcId': 'vpc-custom456',
                    'IsDefault': False,
                    'CidrBlockAssociationSet': [{'CidrBlock': '10.0.0.0/16'}],
                    'Tags': [{'Key': 'Name', 'Value': 'custom-vpc'}]
                }
            ]
        }
        mock_find_account.return_value = mock_aws_response
        
        # Test filtering for default VPCs only
        mock_args = MockOperationHelpers.create_mock_args(pDefault=True)
        
        vpcs.run(mock_args)
        
        # Verify AWS API was called with correct credentials and default flag
        mock_find_account.assert_called_once_with(mock_credentials[0], True)
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have both VPCs since filtering happens in AWS API, not in our logic
        self.assertEqual(len(display_args), 2)
        # Verify that the data transformation worked correctly
        for vpc in display_args:
            self.assertIn(vpc['VpcId'], ['vpc-default123', 'vpc-custom456'])
            self.assertIn(vpc['VpcName'], ['default-vpc', 'custom-vpc'])

    @patch('inv_scr.operations.vpcs.get_all_credentials')
    @patch('inv_scr.operations.vpcs.Inventory_Modules.find_account_vpcs2')
    @patch('inv_scr.operations.vpcs.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_multi_account_vpc_data(self, mock_stdout, mock_display, mock_find_account, mock_get_creds):
        """Test VPC operation across multiple accounts"""
        mock_credentials = MockCredentialFixtures.multi_account_single_region()
        mock_get_creds.return_value = mock_credentials
        
        # Mock different VPC responses for different accounts
        # Note: find_account_vpcs2 takes (credential, defaultOnly) parameters
        def side_effect(credential, default_only=False):
            account_id = credential['AccountId']
            if account_id == '123456789012':
                return MockAWSResponseFixtures.vpc_response(num_vpcs=2)
            elif account_id == '234567890123':
                return MockAWSResponseFixtures.vpc_response(num_vpcs=1)
            else:
                return {'Vpcs': []}  # Empty response for third account
        
        mock_find_account.side_effect = side_effect
        
        mock_args = MockOperationHelpers.create_mock_args()
        
        vpcs.run(mock_args)
        
        # Verify AWS API was called for each account
        self.assertEqual(mock_find_account.call_count, 3)
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have VPCs from first two accounts (2 + 1 = 3 total)
        self.assertEqual(len(display_args), 3)
        
        # Verify account distribution
        account_counts = {}
        for vpc in display_args:
            account_id = vpc['AccountId']
            account_counts[account_id] = account_counts.get(account_id, 0) + 1
        
        self.assertEqual(account_counts.get('123456789012', 0), 2)
        self.assertEqual(account_counts.get('234567890123', 0), 1)
        self.assertEqual(account_counts.get('345678901234', 0), 0)


class TestCfnStacksOperation(unittest.TestCase):
    """Test cases for the CloudFormation stacks operation"""

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
        self.mock_args.pFragments = ['all']
        self.mock_args.pExact = False
        self.mock_args.pStackId = False

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(cfnstacks, 'add_operation_args'))
        self.assertTrue(callable(cfnstacks.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(cfnstacks, 'run'))
        self.assertTrue(callable(cfnstacks.run))

    def test_find_all_cfnstacks_function_exists(self):
        """Test that find_all_cfnstacks function exists"""
        self.assertTrue(hasattr(cfnstacks, 'find_all_cfnstacks'))
        self.assertTrue(callable(cfnstacks.find_all_cfnstacks))

    @patch('inv_scr.operations.cfnstacks.get_all_credentials')
    @patch('inv_scr.operations.cfnstacks.find_all_cfnstacks')
    @patch('inv_scr.operations.cfnstacks.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of cfnstacks run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock stacks found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'StackName': 'test-stack',
                'StackStatus': 'CREATE_COMPLETE',
                'StackCreate': '2023-01-01',
                'ParentProfile': 'test-profile'
            }
        ]
        
        cfnstacks.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for CloudFormation stacks", output)

    def test_find_all_cfnstacks_empty_credentials(self):
        """Test find_all_cfnstacks with empty credentials list"""
        result = cfnstacks.find_all_cfnstacks([])
        self.assertEqual(result, [])

    # Enhanced credential-level mocking tests for CloudFormation Stacks
    @patch('inv_scr.operations.cfnstacks.get_all_credentials')
    @patch('inv_scr.operations.cfnstacks.Inventory_Modules.find_stacks2')
    @patch('inv_scr.operations.cfnstacks.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_single_account_credentials(self, mock_stdout, mock_display, mock_find_stacks, mock_get_creds):
        """Test complete CloudFormation stacks run flow with single account credentials"""
        # Use shared test data system
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials
        
        # Use scenario-based AWS response
        mock_stacks_list = MockAWSResponseFixtures.cfn_stacks_response(num_stacks=3, scenario='simple')
        mock_find_stacks.return_value = mock_stacks_list
        
        # Create mock args
        mock_args = MockOperationHelpers.create_mock_args(
            pFragments=['all'], pStatus=None, pExact=False, pStackId=False
        )
        
        with patch('inv_scr.operations.cfnstacks.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            cfnstacks.run(mock_args)
        
        # Verify credential handling
        mock_get_creds.assert_called_once()
        
        # Verify AWS API was called with correct parameters
        mock_find_stacks.assert_called_once_with(
            mock_credentials[0], mock_credentials[0]['Region'], ['all'], None
        )
        
        # Verify display was called with processed results
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Verify data transformation logic
        self.assertEqual(len(display_args), 3)  # Should have 3 stacks
        for stack in display_args:
            self.assertEqual(stack['AccountId'], '123456789012')
            self.assertEqual(stack['Region'], 'us-east-1')
            self.assertEqual(stack['ParentProfile'], 'test-profile')
            self.assertTrue(stack['StackName'].startswith('master-account-stack-'))
            self.assertIn(stack['StackStatus'], ['CREATE_COMPLETE', 'UPDATE_COMPLETE'])
            self.assertEqual(stack['StackArn'], 'None')  # Default when pStackId=False

    @patch('inv_scr.operations.cfnstacks.get_all_credentials')
    @patch('inv_scr.operations.cfnstacks.Inventory_Modules.find_stacks2')
    @patch('inv_scr.operations.cfnstacks.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_multi_account_credentials(self, mock_stdout, mock_display, mock_find_stacks, mock_get_creds):
        """Test CloudFormation stacks operation across multiple accounts"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('multi_account')
        mock_get_creds.return_value = mock_credentials
        
        # Mock different stack responses for different accounts
        def side_effect(credential, region, fragments, status):
            account_id = credential['AccountId']
            if account_id == '123456789012':  # master-account
                return MockAWSResponseFixtures.cfn_stacks_response(2, scenario='simple')
            elif account_id == '234567890123':  # dev-account
                return MockAWSResponseFixtures.cfn_stacks_response(1, scenario='simple')
            else:
                return []  # Empty response for third account
        
        mock_find_stacks.side_effect = side_effect
        
        mock_args = MockOperationHelpers.create_mock_args(pFragments=['all'])
        
        with patch('inv_scr.operations.cfnstacks.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            cfnstacks.run(mock_args)
        
        # Verify AWS API was called for each account
        self.assertEqual(mock_find_stacks.call_count, 3)
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have stacks from first two accounts (2 + 1 = 3 total)
        self.assertEqual(len(display_args), 3)
        
        # Verify account distribution
        account_counts = {}
        for stack in display_args:
            account_id = stack['AccountId']
            account_counts[account_id] = account_counts.get(account_id, 0) + 1
        
        self.assertEqual(account_counts.get('123456789012', 0), 2)
        self.assertEqual(account_counts.get('234567890123', 0), 1)
        self.assertEqual(account_counts.get('345678901234', 0), 0)

    @patch('inv_scr.operations.cfnstacks.get_all_credentials')
    @patch('inv_scr.operations.cfnstacks.Inventory_Modules.find_stacks2')
    @patch('inv_scr.operations.cfnstacks.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_status_filtering_logic(self, mock_stdout, mock_display, mock_find_stacks, mock_get_creds):
        """Test CloudFormation stack status filtering logic"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials
        
        # Create response with mixed stack statuses
        mixed_stacks = [
            {
                'StackName': 'successful-stack',
                'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/successful-stack/12345678-1234-1234-1234-123456789012',
                'StackStatus': 'CREATE_COMPLETE',
                'CreationTime': datetime(2023, 1, 1, 12, 0, 0),
                'Description': 'Successfully created stack'
            },
            {
                'StackName': 'failed-stack',
                'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/failed-stack/12345678-1234-1234-1234-123456789012',
                'StackStatus': 'CREATE_FAILED',
                'CreationTime': datetime(2023, 1, 1, 12, 0, 0),
                'Description': 'Failed to create stack'
            },
            {
                'StackName': 'updating-stack',
                'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/updating-stack/12345678-1234-1234-1234-123456789012',
                'StackStatus': 'UPDATE_IN_PROGRESS',
                'CreationTime': datetime(2023, 1, 1, 12, 0, 0),
                'Description': 'Stack being updated'
            }
        ]
        mock_find_stacks.return_value = mixed_stacks
        
        # Test filtering for CREATE_COMPLETE status only
        mock_args = MockOperationHelpers.create_mock_args(
            pFragments=['all'], pStatus=['CREATE_COMPLETE']
        )
        
        with patch('inv_scr.operations.cfnstacks.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            cfnstacks.run(mock_args)
        
        # Verify AWS API was called with status filter
        mock_find_stacks.assert_called_once_with(
            mock_credentials[0], mock_credentials[0]['Region'], ['all'], ['CREATE_COMPLETE']
        )
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have all 3 stacks (filtering happens in AWS API, not in our logic)
        self.assertEqual(len(display_args), 3)
        for stack in display_args:
            self.assertIn(stack['StackStatus'], ['CREATE_COMPLETE', 'CREATE_FAILED', 'UPDATE_IN_PROGRESS'])

    @patch('inv_scr.operations.cfnstacks.get_all_credentials')
    @patch('inv_scr.operations.cfnstacks.Inventory_Modules.find_stacks2')
    @patch('inv_scr.operations.cfnstacks.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_fragment_filtering_logic(self, mock_stdout, mock_display, mock_find_stacks, mock_get_creds):
        """Test CloudFormation stack fragment filtering logic"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials
        
        # Create response with stacks that match fragment
        filtered_stacks = [
            {
                'StackName': 'web-app-stack',
                'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/web-app-stack/12345678-1234-1234-1234-123456789012',
                'StackStatus': 'CREATE_COMPLETE',
                'CreationTime': datetime(2023, 1, 1, 12, 0, 0),
                'Description': 'Web application stack'
            },
            {
                'StackName': 'web-db-stack',
                'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/web-db-stack/12345678-1234-1234-1234-123456789012',
                'StackStatus': 'CREATE_COMPLETE',
                'CreationTime': datetime(2023, 1, 1, 12, 0, 0),
                'Description': 'Web database stack'
            }
        ]
        mock_find_stacks.return_value = filtered_stacks
        
        # Test filtering for 'web' fragment
        mock_args = MockOperationHelpers.create_mock_args(
            pFragments=['web'], pExact=False
        )
        
        with patch('inv_scr.operations.cfnstacks.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            cfnstacks.run(mock_args)
        
        # Verify AWS API was called with fragment filter
        mock_find_stacks.assert_called_once_with(
            mock_credentials[0], mock_credentials[0]['Region'], ['web'], None
        )
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have 2 stacks matching the fragment
        self.assertEqual(len(display_args), 2)
        for stack in display_args:
            self.assertIn('web', stack['StackName'].lower())

    @patch('inv_scr.operations.cfnstacks.get_all_credentials')
    @patch('inv_scr.operations.cfnstacks.Inventory_Modules.find_stacks2')
    @patch('inv_scr.operations.cfnstacks.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_stack_id_flag(self, mock_stdout, mock_display, mock_find_stacks, mock_get_creds):
        """Test CloudFormation stack ID display logic"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials
        
        mock_stacks_list = MockAWSResponseFixtures.cfn_stacks_response(num_stacks=2, scenario='simple')
        mock_find_stacks.return_value = mock_stacks_list
        
        # Test with StackId flag enabled
        mock_args = MockOperationHelpers.create_mock_args(
            pFragments=['all'], pStackId=True
        )
        
        with patch('inv_scr.operations.cfnstacks.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            cfnstacks.run(mock_args)
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Verify StackArn is populated when pStackId=True
        for stack in display_args:
            self.assertNotEqual(stack['StackArn'], 'None')
            self.assertTrue(stack['StackArn'].startswith('arn:aws:cloudformation:'))


class TestCfnStackSetsOperation(unittest.TestCase):
    """Test cases for the CloudFormation StackSets operation"""

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
        self.mock_args.pFragments = ['all']
        self.mock_args.pExact = False
        self.mock_args.pStatus = 'ACTIVE'
        self.mock_args.pInstanceCount = False

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(cfnstacksets, 'add_operation_args'))
        self.assertTrue(callable(cfnstacksets.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(cfnstacksets, 'run'))
        self.assertTrue(callable(cfnstacksets.run))

    def test_find_all_cfnstacksets_function_exists(self):
        """Test that find_all_cfnstacksets function exists"""
        self.assertTrue(hasattr(cfnstacksets, 'find_all_cfnstacksets'))
        self.assertTrue(callable(cfnstacksets.find_all_cfnstacksets))

    @patch('inv_scr.operations.cfnstacksets.get_all_credentials')
    @patch('inv_scr.operations.cfnstacksets.find_all_cfnstacksets')
    @patch('inv_scr.operations.cfnstacksets.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of cfnstacksets run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock stacksets found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'StackSetName': 'test-stackset',
                'Status': 'ACTIVE',
                'ParentProfile': 'test-profile'
            }
        ]
        
        cfnstacksets.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for CloudFormation StackSets", output)


class TestEbsVolumesOperation(unittest.TestCase):
    """Test cases for the EBS volumes operation"""

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
        self.mock_args.pFragments = ['all']
        self.mock_args.pExact = False

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(ebs_volumes, 'add_operation_args'))
        self.assertTrue(callable(ebs_volumes.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(ebs_volumes, 'run'))
        self.assertTrue(callable(ebs_volumes.run))

    def test_find_all_ebs_volumes_function_exists(self):
        """Test that find_all_ebs_volumes function exists"""
        self.assertTrue(hasattr(ebs_volumes, 'find_all_ebs_volumes'))
        self.assertTrue(callable(ebs_volumes.find_all_ebs_volumes))

    @patch('inv_scr.operations.ebs_volumes.get_all_credentials')
    @patch('inv_scr.operations.ebs_volumes.find_all_ebs_volumes')
    @patch('inv_scr.operations.ebs_volumes.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of ebs_volumes run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock volumes found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'VolumeId': 'vol-12345678',
                'VolumeName': 'test-volume',
                'State': 'available',
                'Size': 100,
                'ParentProfile': 'test-profile'
            }
        ]
        
        ebs_volumes.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for EBS volumes", output)


class TestElbsOperation(unittest.TestCase):
    """Test cases for the Elastic Load Balancers operation"""

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
        self.mock_args.pFragments = ['all']
        self.mock_args.pExact = False
        self.mock_args.pStatus = 'active'

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(elbs, 'add_operation_args'))
        self.assertTrue(callable(elbs.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(elbs, 'run'))
        self.assertTrue(callable(elbs.run))

    def test_find_all_elbs_function_exists(self):
        """Test that find_all_elbs function exists"""
        self.assertTrue(hasattr(elbs, 'find_all_elbs'))
        self.assertTrue(callable(elbs.find_all_elbs))

    @patch('inv_scr.operations.elbs.get_all_credentials')
    @patch('inv_scr.operations.elbs.find_all_elbs')
    @patch('inv_scr.operations.elbs.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of elbs run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock load balancers found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'Name': 'test-elb',
                'Status': 'active',
                'DNSName': 'test-elb-123456789.us-east-1.elb.amazonaws.com',
                'ParentProfile': 'test-profile'
            }
        ]
        
        elbs.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for Elastic Load Balancers", output)

    # Enhanced credential-level mocking tests for Elastic Load Balancers
    @patch('inv_scr.operations.elbs.get_all_credentials')
    @patch('inv_scr.operations.elbs.Inventory_Modules.find_load_balancers2')
    @patch('inv_scr.operations.elbs.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_single_account_credentials(self, mock_stdout, mock_display, mock_find_elbs, mock_get_creds):
        """Test complete ELB run flow with single account credentials"""
        # Use shared test data system
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials
        
        # Use scenario-based AWS response
        mock_elbs_list = MockAWSResponseFixtures.elb_response(num_elbs=2, scenario='simple')
        mock_find_elbs.return_value = mock_elbs_list
        
        # Create mock args
        mock_args = MockOperationHelpers.create_mock_args(
            pFragments=['all'], pStatus='active', pExact=False
        )
        
        with patch('inv_scr.operations.elbs.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            elbs.run(mock_args)
        
        # Verify credential handling
        mock_get_creds.assert_called_once()
        
        # Verify AWS API was called with correct parameters
        # Note: find_load_balancers2 is called with (credential, fragments, status) in the queue
        self.assertEqual(mock_find_elbs.call_count, 1)
        
        # Verify display was called with processed results
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Verify data transformation logic
        self.assertEqual(len(display_args), 2)  # Should have 2 ELBs
        for elb in display_args:
            self.assertEqual(elb['AccountId'], '123456789012')
            self.assertEqual(elb['Region'], 'us-east-1')
            self.assertEqual(elb['ParentProfile'], 'test-profile')
            self.assertTrue(elb['Name'].startswith('master-account-elb-'))
            self.assertEqual(elb['Status'], 'active')
            self.assertTrue(elb['DNSName'].endswith('.us-east-1.elb.amazonaws.com'))

    @patch('inv_scr.operations.elbs.get_all_credentials')
    @patch('inv_scr.operations.elbs.Inventory_Modules.find_load_balancers2')
    @patch('inv_scr.operations.elbs.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_multi_account_credentials(self, mock_stdout, mock_display, mock_find_elbs, mock_get_creds):
        """Test ELB operation across multiple accounts"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('multi_account')
        mock_get_creds.return_value = mock_credentials
        
        # Mock different ELB responses for different accounts
        def side_effect(credential, fragments, status):
            account_id = credential['AccountId']
            if account_id == '123456789012':  # master-account
                return MockAWSResponseFixtures.elb_response(2, scenario='simple')
            elif account_id == '234567890123':  # dev-account
                return MockAWSResponseFixtures.elb_response(1, scenario='simple')
            else:
                return []  # Empty response for third account
        
        mock_find_elbs.side_effect = side_effect
        
        mock_args = MockOperationHelpers.create_mock_args(pFragments=['all'], pStatus='active')
        
        with patch('inv_scr.operations.elbs.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            elbs.run(mock_args)
        
        # Verify AWS API was called for each account
        self.assertEqual(mock_find_elbs.call_count, 3)
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have ELBs from first two accounts (2 + 1 = 3 total)
        self.assertEqual(len(display_args), 3)
        
        # Verify account distribution
        account_counts = {}
        for elb in display_args:
            account_id = elb['AccountId']
            account_counts[account_id] = account_counts.get(account_id, 0) + 1
        
        self.assertEqual(account_counts.get('123456789012', 0), 2)
        self.assertEqual(account_counts.get('234567890123', 0), 1)
        self.assertEqual(account_counts.get('345678901234', 0), 0)

    @patch('inv_scr.operations.elbs.get_all_credentials')
    @patch('inv_scr.operations.elbs.Inventory_Modules.find_load_balancers2')
    @patch('inv_scr.operations.elbs.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_status_filtering_logic(self, mock_stdout, mock_display, mock_find_elbs, mock_get_creds):
        """Test ELB status filtering logic"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials
        
        # Create response with mixed ELB statuses
        mixed_elbs = [
            {
                'LoadBalancerName': 'active-elb',
                'DNSName': 'active-elb-123456789.us-east-1.elb.amazonaws.com',
                'State': {'Code': 'active'},
                'Type': 'application'
            },
            {
                'LoadBalancerName': 'provisioning-elb',
                'DNSName': 'provisioning-elb-123456789.us-east-1.elb.amazonaws.com',
                'State': {'Code': 'provisioning'},
                'Type': 'application'
            },
            {
                'LoadBalancerName': 'failed-elb',
                'DNSName': 'failed-elb-123456789.us-east-1.elb.amazonaws.com',
                'State': {'Code': 'failed'},
                'Type': 'application'
            }
        ]
        mock_find_elbs.return_value = mixed_elbs
        
        # Test filtering for active status only
        mock_args = MockOperationHelpers.create_mock_args(
            pFragments=['all'], pStatus='active'
        )
        
        with patch('inv_scr.operations.elbs.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            elbs.run(mock_args)
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have all 3 ELBs (filtering happens in AWS API, not in our logic)
        self.assertEqual(len(display_args), 3)
        for elb in display_args:
            self.assertIn(elb['Status'], ['active', 'provisioning', 'failed'])

    @patch('inv_scr.operations.elbs.get_all_credentials')
    @patch('inv_scr.operations.elbs.Inventory_Modules.find_load_balancers2')
    @patch('inv_scr.operations.elbs.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_fragment_filtering_logic(self, mock_stdout, mock_display, mock_find_elbs, mock_get_creds):
        """Test ELB fragment filtering logic"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials
        
        # Create response with ELBs that match fragment
        filtered_elbs = [
            {
                'LoadBalancerName': 'web-app-elb',
                'DNSName': 'web-app-elb-123456789.us-east-1.elb.amazonaws.com',
                'State': {'Code': 'active'},
                'Type': 'application'
            },
            {
                'LoadBalancerName': 'web-api-elb',
                'DNSName': 'web-api-elb-123456789.us-east-1.elb.amazonaws.com',
                'State': {'Code': 'active'},
                'Type': 'application'
            }
        ]
        mock_find_elbs.return_value = filtered_elbs
        
        # Test filtering for 'web' fragment
        mock_args = MockOperationHelpers.create_mock_args(
            pFragments=['web'], pStatus='active', pExact=False
        )
        
        with patch('inv_scr.operations.elbs.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            elbs.run(mock_args)
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have 2 ELBs matching the fragment
        self.assertEqual(len(display_args), 2)
        for elb in display_args:
            self.assertIn('web', elb['Name'].lower())


class TestFunctionsOperation(unittest.TestCase):
    """Test cases for the Lambda functions operation"""

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
        self.mock_args.pFragments = ['all']
        self.mock_args.pExact = False
        self.mock_args.pRuntime = None
        self.mock_args.pNewRuntime = None
        self.mock_args.Fix = False
        self.mock_args.Force = False

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(functions, 'add_operation_args'))
        self.assertTrue(callable(functions.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(functions, 'run'))
        self.assertTrue(callable(functions.run))

    def test_find_all_lambda_functions_function_exists(self):
        """Test that find_all_lambda_functions function exists"""
        self.assertTrue(hasattr(functions, 'find_all_lambda_functions'))
        self.assertTrue(callable(functions.find_all_lambda_functions))

    @patch('inv_scr.operations.functions.get_all_credentials')
    @patch('inv_scr.operations.functions.find_all_lambda_functions')
    @patch('inv_scr.operations.functions.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of functions run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock functions found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'FunctionName': 'test-function',
                'Runtime': 'python3.9',
                'Role': 'test-role',
                'ParentProfile': 'test-profile'
            }
        ]
        
        functions.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for Lambda functions", output)

    # Enhanced credential-level mocking tests for Lambda functions
    @patch('inv_scr.operations.functions.get_all_credentials')
    @patch('inv_scr.operations.functions.find_lambda_functions2')
    @patch('inv_scr.operations.functions.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_comprehensive_lambda_data(self, mock_stdout, mock_display, mock_find_account, mock_get_creds):
        """Test complete Lambda functions run flow with comprehensive credential and response mocking"""
        # Use mock credential fixture
        mock_credentials = MockCredentialFixtures.single_account_single_region()
        mock_get_creds.return_value = mock_credentials
        
        # Use mock AWS response fixture - return list of functions directly
        mock_functions_list = [
            {
                'FunctionName': 'test-function-0',
                'Runtime': 'python3.9',
                'Role': 'arn:aws:iam::123456789012:role/test-lambda-role-0',
                'Handler': 'lambda_function.lambda_handler',
                'CodeSize': 1024,
                'Description': 'Test Lambda function 0',
                'Timeout': 30,
                'MemorySize': 128
            },
            {
                'FunctionName': 'test-function-1',
                'Runtime': 'nodejs18.x',
                'Role': 'arn:aws:iam::123456789012:role/test-lambda-role-1',
                'Handler': 'index.handler',
                'CodeSize': 2048,
                'Description': 'Test Lambda function 1',
                'Timeout': 60,
                'MemorySize': 256
            }
        ]
        mock_find_account.return_value = mock_functions_list
        
        # Create mock args using helper
        mock_args = MockOperationHelpers.create_mock_args(pFragments=['all'], pRuntime=None, Fix=False, pNewRuntime=None)
        
        with patch('inv_scr.operations.functions.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            functions.run(mock_args)
        
        # Verify credential handling
        mock_get_creds.assert_called_once()
        
        # Verify AWS API was called with correct credentials, region, and fragments
        mock_find_account.assert_called_once_with(mock_credentials[0], 'us-east-1', ['all'])
        
        # Verify display was called with processed results
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Verify data transformation logic
        self.assertEqual(len(display_args), 2)  # Should have 2 functions
        for i, function in enumerate(display_args):
            self.assertEqual(function['AccountId'], '123456789012')
            self.assertEqual(function['Region'], 'us-east-1')
            self.assertEqual(function['FunctionName'], f'test-function-{i}')
            self.assertIn(function['Runtime'], ['python3.9', 'nodejs18.x'])
            self.assertEqual(function['ParentProfile'], 'test-profile')
            # Verify role name extraction logic
            self.assertEqual(function['Role'], f'test-lambda-role-{i}')

    @patch('inv_scr.operations.functions.get_all_credentials')
    @patch('inv_scr.operations.functions.find_lambda_functions2')
    @patch('inv_scr.operations.functions.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_runtime_filtering_logic(self, mock_stdout, mock_display, mock_find_account, mock_get_creds):
        """Test Lambda function runtime filtering logic"""
        mock_credentials = MockCredentialFixtures.single_account_single_region()
        mock_get_creds.return_value = mock_credentials
        
        # Create response with mixed runtimes - return list directly
        mock_functions_list = [
            {
                'FunctionName': 'python-function-1',
                'Runtime': 'python3.9',
                'Role': 'arn:aws:iam::123456789012:role/python-role',
                'Handler': 'lambda_function.lambda_handler',
                'CodeSize': 1024,
                'Description': 'Python function 1',
                'Timeout': 30,
                'MemorySize': 128
            },
            {
                'FunctionName': 'node-function-1',
                'Runtime': 'nodejs18.x',
                'Role': 'arn:aws:iam::123456789012:role/node-role',
                'Handler': 'index.handler',
                'CodeSize': 2048,
                'Description': 'Node.js function 1',
                'Timeout': 60,
                'MemorySize': 256
            },
            {
                'FunctionName': 'python-function-2',
                'Runtime': 'python3.11',
                'Role': 'arn:aws:iam::123456789012:role/python-role-2',
                'Handler': 'lambda_function.lambda_handler',
                'CodeSize': 1536,
                'Description': 'Python function 2',
                'Timeout': 45,
                'MemorySize': 512
            }
        ]
        mock_find_account.return_value = mock_functions_list
        
        # Test filtering for Python runtime only
        mock_args = MockOperationHelpers.create_mock_args(pFragments=['all'], pRuntime=['python'], Fix=False, pNewRuntime=None)
        
        with patch('inv_scr.operations.functions.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            functions.run(mock_args)
        
        # Verify AWS API was called with correct parameters (fragments + runtime)
        mock_find_account.assert_called_once_with(mock_credentials[0], 'us-east-1', ['all', 'python'])
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have all 3 functions (filtering by runtime happens in the find_lambda_functions2 function)
        self.assertEqual(len(display_args), 3)
        for function in display_args:
            self.assertEqual(function['AccountId'], '123456789012')
            self.assertEqual(function['Region'], 'us-east-1')
            self.assertEqual(function['ParentProfile'], 'test-profile')
            # Verify role name extraction logic worked
            self.assertNotIn('arn:aws:iam::', function['Role'])

    def test_update_function_runtime_function_exists(self):
        """Test that update_function_runtime function exists"""
        self.assertTrue(hasattr(functions, 'update_function_runtime'))
        self.assertTrue(callable(functions.update_function_runtime))

    @patch('inv_scr.operations.functions.boto3.Session')
    @patch('inv_scr.operations.functions.tqdm')
    def test_update_function_runtime_basic(self, mock_tqdm, mock_session):
        """Test basic runtime update functionality"""
        # Mock progress bar
        mock_pbar = MagicMock()
        mock_tqdm.return_value = mock_pbar
        
        # Mock boto3 session and client
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        
        # Mock successful update response
        mock_client.update_function_configuration.return_value = {
            'FunctionName': 'test-function',
            'Runtime': 'python3.11',
            'Role': 'arn:aws:iam::123456789012:role/test-role'
        }
        mock_client.get_function_configuration.return_value = {
            'LastUpdateStatus': 'Successful'
        }
        
        # Test data
        functions_to_update = [
            {
                'FunctionName': 'test-function',
                'Runtime': 'python3.9',
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'AccessKeyId': 'AKIATEST',
                'SecretAccessKey': 'secret',
                'SessionToken': 'token'
            }
        ]
        
        result = functions.update_function_runtime(functions_to_update, 'python3.11')
        
        # Verify boto3 session was created with correct credentials
        mock_session.assert_called_once_with(
            aws_access_key_id='AKIATEST',
            aws_secret_access_key='secret',
            aws_session_token='token',
            region_name='us-east-1'
        )
        
        # Verify update was called
        mock_client.update_function_configuration.assert_called_once_with(
            FunctionName='test-function',
            Runtime='python3.11'
        )
        
        # Verify result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['FunctionName'], 'test-function')
        self.assertEqual(result[0]['Runtime'], 'python3.11')

    @patch('inv_scr.operations.functions.get_all_credentials')
    @patch('inv_scr.operations.functions.find_all_lambda_functions')
    @patch('inv_scr.operations.functions.update_function_runtime')
    @patch('inv_scr.operations.functions.display_results')
    @patch('builtins.input', return_value='y')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_runtime_update(self, mock_stdout, mock_input, mock_display, mock_update, mock_find, mock_creds):
        """Test complete run flow with runtime update"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock functions found with old runtime
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'FunctionName': 'test-function',
                'Runtime': 'python3.9',
                'Role': 'test-role',
                'ParentProfile': 'test-profile',
                'AccessKeyId': 'AKIATEST',
                'SecretAccessKey': 'secret',
                'SessionToken': 'token'
            }
        ]
        
        # Mock successful update
        mock_update.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'FunctionName': 'test-function',
                'Runtime': 'python3.11',
                'Role': 'test-role',
                'ParentProfile': 'test-profile'
            }
        ]
        
        # Set up args for runtime update
        self.mock_args.pRuntime = ['python3.9']
        self.mock_args.pNewRuntime = 'python3.11'
        self.mock_args.Fix = True
        self.mock_args.Force = False
        
        functions.run(self.mock_args)
        
        # Verify functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_update.assert_called_once()
        
        # Verify update was called with correct parameters
        update_args = mock_update.call_args[0]
        self.assertEqual(len(update_args[0]), 1)  # One function to update
        self.assertEqual(update_args[1], 'python3.11')  # New runtime
        
        # Verify display was called twice (original results + updated results)
        self.assertEqual(mock_display.call_count, 2)
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Found 1 functions with runtime matching", output)
        self.assertIn("Updating Runtime for 1 functions", output)

    @patch('inv_scr.operations.functions.get_all_credentials')
    @patch('inv_scr.operations.functions.find_all_lambda_functions')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_fix_but_no_new_runtime(self, mock_stdout, mock_find, mock_creds):
        """Test run with --fix but no +new_runtime parameter"""
        # Mock credentials and functions
        mock_creds.return_value = [{'AccountId': '123456789012', 'Region': 'us-east-1'}]
        mock_find.return_value = []
        
        # Set up args with fix but no new runtime
        self.mock_args.Fix = True
        self.mock_args.pNewRuntime = None
        
        with self.assertRaises(SystemExit) as cm:
            functions.run(self.mock_args)
        
        self.assertEqual(cm.exception.code, 8)
        output = mock_stdout.getvalue()
        self.assertIn("didn't supply a new runtime", output)

    @patch('inv_scr.operations.functions.get_all_credentials')
    @patch('inv_scr.operations.functions.find_all_lambda_functions')
    @patch('builtins.input', return_value='n')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_runtime_update_cancelled(self, mock_stdout, mock_input, mock_find, mock_creds):
        """Test runtime update when user cancels"""
        # Mock credentials and functions
        mock_creds.return_value = [{'AccountId': '123456789012', 'Region': 'us-east-1'}]
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'FunctionName': 'test-function',
                'Runtime': 'python3.9',
                'ParentProfile': 'test-profile',
                'AccessKeyId': 'test',
                'SecretAccessKey': 'test',
                'SessionToken': 'test'
            }
        ]
        
        # Set up args for runtime update
        self.mock_args.pRuntime = ['python3.9']
        self.mock_args.pNewRuntime = 'python3.11'
        self.mock_args.Fix = True
        self.mock_args.Force = False
        
        functions.run(self.mock_args)
        
        # Check output contains cancellation message
        output = mock_stdout.getvalue()
        self.assertIn("Runtime update cancelled", output)


class TestOrgsOperation(unittest.TestCase):
    """Test cases for the AWS Organizations operation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_args = MagicMock()
        self.mock_args.Profiles = ['test-profile']
        self.mock_args.SkipAccounts = None
        self.mock_args.SkipProfiles = None
        self.mock_args.RootOnly = False
        self.mock_args.Filename = None
        self.mock_args.Time = False
        self.mock_args.pShortform = False
        self.mock_args.pAccountList = None

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(orgs, 'add_operation_args'))
        self.assertTrue(callable(orgs.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(orgs, 'run'))
        self.assertTrue(callable(orgs.run))

    def test_find_all_orgs_function_exists(self):
        """Test that find_all_orgs function exists"""
        self.assertTrue(hasattr(orgs, 'find_all_orgs'))
        self.assertTrue(callable(orgs.find_all_orgs))

    def test_orgs_found_class_exists(self):
        """Test that OrgsFound class exists"""
        self.assertTrue(hasattr(orgs, 'OrgsFound'))
        self.assertTrue(callable(orgs.OrgsFound))

    def test_add_operation_args_creates_arguments(self):
        """Test that add_operation_args properly creates argument groups and arguments"""
        mock_parser = MagicMock()
        mock_group = MagicMock()
        mock_parser.my_parser.add_argument_group.return_value = mock_group
        
        orgs.add_operation_args(mock_parser)
        
        # Verify argument group was created
        mock_parser.my_parser.add_argument_group.assert_called_once_with('orgs', 'AWS Organizations specific options')
        
        # Verify arguments were added (should be called 3 times for the 3 arguments)
        self.assertEqual(mock_group.add_argument.call_count, 3)
        
        # Check specific argument calls
        calls = mock_group.add_argument.call_args_list
        
        # First call should be for --short argument
        self.assertIn('-s', calls[0][0])
        self.assertIn('--short', calls[0][0])
        
        # Second call should be for --acct argument
        self.assertIn('-A', calls[1][0])
        self.assertIn('--acct', calls[1][0])
        
        # Third call should be for --operation-version
        self.assertIn('--operation-version', calls[2][0])

    def _create_mock_account_class(self, acct_number, account_status='ACTIVE', child_accounts=None):
        """Helper to create mock account class objects"""
        mock_account = MagicMock()
        mock_account.acct_number = acct_number
        mock_account.AccountStatus = account_status
        mock_account.ChildAccounts = child_accounts or []
        return mock_account

    def _create_profile_account_data(self, profile, acct_number, success=True, root_acct=False, 
                                   mgmt_account=None, org_id=None, error_msg=None, 
                                   account_status='ACTIVE', child_accounts=None):
        """Helper to create profile account data structure"""
        data = {
            'profile': profile,
            'Success': success,
            'RootAcct': root_acct,
            'MgmtAccount': mgmt_account or acct_number,
            'OrgId': org_id,
            'aws_acct': self._create_mock_account_class(acct_number, account_status, child_accounts)
        }
        
        if not success:
            data['ErrorMessage'] = error_msg or f"Failed to access {profile}"
            
        return data

    @patch('inv_scr.operations.orgs.get_org_accounts_from_profiles')
    @patch('inv_scr.operations.orgs.get_profiles')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_find_all_orgs_with_failed_profiles(self, mock_stdout, mock_get_profiles, mock_get_org_accounts):
        """Test find_all_orgs handles failed profiles correctly"""
        # Setup mock profiles
        mock_get_profiles.return_value = ['profile1', 'profile2', 'profile3']
        
        # Setup mock account data with some failures
        mock_profile_accounts = [
            self._create_profile_account_data('profile1', '123456789012', success=True, root_acct=True, 
                                            mgmt_account='123456789012', org_id='o-example123'),
            self._create_profile_account_data('profile2', '234567890123', success=False, 
                                            error_msg="Access denied"),
            self._create_profile_account_data('profile3', '345678901234', success=False, 
                                            error_msg="Profile not found")
        ]
        
        mock_get_org_accounts.return_value = mock_profile_accounts
        
        # Call function
        result = orgs.find_all_orgs(['profile1', 'profile2', 'profile3'], [], None, False, False, None, False)
        
        # Verify results
        self.assertEqual(len(result.orgs_found), 1)
        self.assertEqual(result.orgs_found[0], '123456789012')
        self.assertEqual(len(result.failed_profiles), 2)
        self.assertIn('profile2', result.failed_profiles)
        self.assertIn('profile3', result.failed_profiles)

    @patch('inv_scr.operations.orgs.get_org_accounts_from_profiles')
    @patch('inv_scr.operations.orgs.get_profiles')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_find_all_orgs_with_child_accounts(self, mock_stdout, mock_get_profiles, mock_get_org_accounts):
        """Test find_all_orgs processes child accounts correctly"""
        # Setup mock profiles
        mock_get_profiles.return_value = ['org-master']
        
        # Create child accounts with different statuses
        child_accounts = [
            {'AccountId': '111111111111', 'AccountStatus': 'ACTIVE', 'AccountEmail': 'child1@example.com'},
            {'AccountId': '222222222222', 'AccountStatus': 'SUSPENDED', 'AccountEmail': 'child2@example.com'},
            {'AccountId': '333333333333', 'AccountStatus': 'CLOSED', 'AccountEmail': 'child3@example.com'},
            {'AccountId': '444444444444', 'AccountStatus': 'ACTIVE', 'AccountEmail': 'child4@example.com'}
        ]
        
        # Setup mock account data with child accounts
        mock_profile_accounts = [
            self._create_profile_account_data('org-master', '123456789012', success=True, root_acct=True,
                                            mgmt_account='123456789012', org_id='o-example123',
                                            child_accounts=child_accounts)
        ]
        
        mock_get_org_accounts.return_value = mock_profile_accounts
        
        # Call function
        result = orgs.find_all_orgs(['org-master'], [], None, False, False, None, False)
        
        # Verify results
        self.assertEqual(len(result.orgs_found), 1)
        self.assertEqual(result.orgs_found[0], '123456789012')
        self.assertEqual(result.num_of_org_accounts, 4)  # Total child accounts
        self.assertEqual(len(result.closed_accounts), 2)  # SUSPENDED and CLOSED accounts
        self.assertIn('222222222222', result.closed_accounts)
        self.assertIn('333333333333', result.closed_accounts)
        self.assertEqual(len(result.account_list), 4)  # All child accounts in account list

    @patch('inv_scr.operations.orgs.get_org_accounts_from_profiles')
    @patch('inv_scr.operations.orgs.get_profiles')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_find_all_orgs_with_different_account_statuses(self, mock_stdout, mock_get_profiles, mock_get_org_accounts):
        """Test find_all_orgs handles different account statuses correctly"""
        # Setup mock profiles
        mock_get_profiles.return_value = ['profile1', 'profile2', 'profile3']
        
        # Setup accounts with different statuses
        mock_profile_accounts = [
            self._create_profile_account_data('profile1', '123456789012', success=True, root_acct=False,
                                            mgmt_account='999999999999', account_status='ACTIVE'),
            self._create_profile_account_data('profile2', '234567890123', success=True, root_acct=False,
                                            mgmt_account='999999999999', account_status='SUSPENDED'),
            self._create_profile_account_data('profile3', '345678901234', success=True, root_acct=False,
                                            mgmt_account='999999999999', account_status='CLOSED')
        ]
        
        # Add child account data for non-root accounts
        for profile_data in mock_profile_accounts:
            if not profile_data['RootAcct']:
                profile_data['aws_acct'].ChildAccounts = [{
                    'AccountId': profile_data['aws_acct'].acct_number,
                    'AccountStatus': profile_data['aws_acct'].AccountStatus,
                    'AccountEmail': f"{profile_data['profile']}@example.com",
                    'MgmtAccount': profile_data['MgmtAccount']
                }]
        
        mock_get_org_accounts.return_value = mock_profile_accounts
        
        # Call function
        result = orgs.find_all_orgs(['profile1', 'profile2', 'profile3'], [], None, False, False, None, False)
        
        # Verify results
        self.assertEqual(len(result.account_list), 3)
        
        # Check that accounts with different statuses are properly tracked
        account_statuses = [acc['AccountStatus'] for acc in result.account_list]
        self.assertIn('ACTIVE', account_statuses)
        self.assertIn('SUSPENDED', account_statuses)
        self.assertIn('CLOSED', account_statuses)

    @patch('inv_scr.operations.orgs.find_all_orgs')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_shortform_flag(self, mock_stdout, mock_find):
        """Test run function with shortform flag enabled"""
        mock_args = MockOperationHelpers.create_mock_args(pShortform=True)
        
        # Mock response
        mock_response = orgs.OrgsFound()
        mock_response.orgs_found = ['123456789012']
        mock_response.num_of_org_accounts = 5
        mock_response.stand_alone_accounts = []
        mock_response.closed_accounts = []
        mock_response.failed_profiles = []
        mock_response.account_list = []
        
        mock_find.return_value = mock_response
        
        orgs.run(mock_args)
        
        # Check that shortform message is displayed
        output = mock_stdout.getvalue()
        self.assertIn("short form", output)
        self.assertIn("showing only profile accounts", output)

    @patch('inv_scr.operations.orgs.find_all_orgs')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_root_only_flag(self, mock_stdout, mock_find):
        """Test run function with root only flag enabled"""
        mock_args = MockOperationHelpers.create_mock_args(RootOnly=True)
        
        # Mock response
        mock_response = orgs.OrgsFound()
        mock_response.orgs_found = ['123456789012']
        mock_response.num_of_org_accounts = 5
        mock_response.stand_alone_accounts = []
        mock_response.closed_accounts = []
        mock_response.failed_profiles = []
        mock_response.account_list = []
        
        mock_find.return_value = mock_response
        
        orgs.run(mock_args)
        
        # Check that root only message is displayed
        output = mock_stdout.getvalue()
        self.assertIn("root accounts only", output)

    @patch('inv_scr.operations.orgs.find_all_orgs')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_account_list(self, mock_stdout, mock_find):
        """Test run function with specific account list"""
        mock_args = MockOperationHelpers.create_mock_args(pAccountList=['123456789012', '234567890123'])
        
        # Mock response with account list
        mock_response = orgs.OrgsFound()
        mock_response.orgs_found = ['999999999999']
        mock_response.num_of_org_accounts = 2
        mock_response.stand_alone_accounts = []
        mock_response.closed_accounts = []
        mock_response.failed_profiles = []
        mock_response.account_list = [
            {
                'AccountId': '123456789012',
                'Profile': 'profile1',
                'MgmtAccount': '999999999999',
                'AccountStatus': 'ACTIVE',
                'AccountEmail': 'test1@example.com'
            },
            {
                'AccountId': '234567890123',
                'Profile': 'profile2',
                'MgmtAccount': '999999999999',
                'AccountStatus': 'ACTIVE',
                'AccountEmail': 'test2@example.com'
            }
        ]
        
        mock_find.return_value = mock_response
        
        orgs.run(mock_args)
        
        # Check that account search message and results are displayed
        output = mock_stdout.getvalue()
        self.assertIn("Looking for specific accounts", output)
        self.assertIn("Found the requested account number", output)
        self.assertIn("123456789012", output)
        self.assertIn("234567890123", output)

    @patch('inv_scr.operations.orgs.find_all_orgs')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_standalone_accounts(self, mock_stdout, mock_find):
        """Test run function displays standalone accounts correctly"""
        mock_args = MockOperationHelpers.create_mock_args()
        
        # Mock response with standalone accounts
        mock_response = orgs.OrgsFound()
        mock_response.orgs_found = ['999999999999']
        mock_response.num_of_org_accounts = 1
        mock_response.stand_alone_accounts = ['111111111111', '222222222222']
        mock_response.closed_accounts = []
        mock_response.failed_profiles = []
        mock_response.account_list = []
        
        mock_find.return_value = mock_response
        
        orgs.run(mock_args)
        
        # Check that standalone accounts are displayed
        output = mock_stdout.getvalue()
        self.assertIn("following accounts are Standalone", output)
        self.assertIn("111111111111", output)
        self.assertIn("222222222222", output)

    @patch('inv_scr.operations.orgs.find_all_orgs')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_closed_accounts(self, mock_stdout, mock_find):
        """Test run function displays closed accounts correctly"""
        mock_args = MockOperationHelpers.create_mock_args()
        
        # Mock response with closed accounts
        mock_response = orgs.OrgsFound()
        mock_response.orgs_found = ['999999999999']
        mock_response.num_of_org_accounts = 3
        mock_response.stand_alone_accounts = []
        mock_response.closed_accounts = ['333333333333', '444444444444']
        mock_response.failed_profiles = []
        mock_response.account_list = []
        
        mock_find.return_value = mock_response
        
        orgs.run(mock_args)
        
        # Check that closed accounts are displayed
        output = mock_stdout.getvalue()
        self.assertIn("closed or suspended", output)
        self.assertIn("333333333333", output)
        self.assertIn("444444444444", output)

    @patch('inv_scr.operations.orgs.find_all_orgs')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_failed_profiles_display(self, mock_stdout, mock_find):
        """Test run function displays failed profiles correctly"""
        mock_args = MockOperationHelpers.create_mock_args()
        
        # Mock response with failed profiles
        mock_response = orgs.OrgsFound()
        mock_response.orgs_found = ['999999999999']
        mock_response.num_of_org_accounts = 1
        mock_response.stand_alone_accounts = []
        mock_response.closed_accounts = []
        mock_response.failed_profiles = ['failed-profile1', 'failed-profile2']
        mock_response.account_list = []
        
        mock_find.return_value = mock_response
        
        orgs.run(mock_args)
        
        # Check that failed profiles are displayed
        output = mock_stdout.getvalue()
        self.assertIn("following profiles failed", output)
        self.assertIn("failed-profile1", output)
        self.assertIn("failed-profile2", output)

    @patch('inv_scr.operations.orgs.get_org_accounts_from_profiles')
    @patch('inv_scr.operations.orgs.get_profiles')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_find_all_orgs_shortform_mode(self, mock_stdout, mock_get_profiles, mock_get_org_accounts):
        """Test find_all_orgs in shortform mode returns limited data"""
        # Setup mock profiles
        mock_get_profiles.return_value = ['profile1']
        
        # Setup mock account data
        mock_profile_accounts = [
            self._create_profile_account_data('profile1', '123456789012', success=True, root_acct=True,
                                            mgmt_account='123456789012', org_id='o-example123')
        ]
        
        mock_get_org_accounts.return_value = mock_profile_accounts
        
        # Call function in shortform mode
        result = orgs.find_all_orgs(['profile1'], [], None, False, False, None, True)
        
        # Verify shortform results (should have limited data)
        self.assertEqual(len(result.orgs_found), 1)
        self.assertEqual(result.orgs_found[0], '123456789012')
        self.assertEqual(result.num_of_org_accounts, 0)  # Not populated in shortform
        self.assertEqual(len(result.account_list), 0)  # Not populated in shortform
        self.assertEqual(len(result.closed_accounts), 0)  # Not populated in shortform

    @patch('inv_scr.operations.orgs.find_all_orgs')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_find):
        """Test basic execution of orgs run function"""
        # Mock orgs found
        mock_response = orgs.OrgsFound()
        mock_response.orgs_found = ['123456789012']
        mock_response.num_of_org_accounts = 5
        mock_response.stand_alone_accounts = []
        mock_response.closed_accounts = []
        mock_response.failed_profiles = []
        mock_response.account_list = []
        
        mock_find.return_value = mock_response
        
        orgs.run(self.mock_args)
        
        # Verify that the function was called
        mock_find.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for AWS Organizations", output)

    @patch('inv_scr.operations.orgs.get_org_accounts_from_profiles')
    @patch('inv_scr.operations.orgs.get_profiles')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_find_all_orgs_with_timing_enabled(self, mock_stdout, mock_get_profiles, mock_get_org_accounts):
        """Test find_all_orgs with timing enabled shows timing information"""
        # Setup mock profiles
        mock_get_profiles.return_value = ['profile1']
        
        # Setup mock account data
        mock_profile_accounts = [
            self._create_profile_account_data('profile1', '123456789012', success=True, root_acct=True,
                                            mgmt_account='123456789012', org_id='o-example123')
        ]
        
        mock_get_org_accounts.return_value = mock_profile_accounts
        
        # Call function with timing enabled
        result = orgs.find_all_orgs(['profile1'], [], None, True, False, None, False)
        
        # Check that timing output is present
        output = mock_stdout.getvalue()
        self.assertIn("taken", output)
        self.assertIn("seconds", output)


class TestRdsInstancesOperation(unittest.TestCase):
    """Test cases for the RDS instances operation"""

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
        self.mock_args.pFragments = ['all']
        self.mock_args.pExact = False

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(rds_instances, 'add_operation_args'))
        self.assertTrue(callable(rds_instances.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(rds_instances, 'run'))
        self.assertTrue(callable(rds_instances.run))

    def test_find_all_rds_instances_function_exists(self):
        """Test that find_all_rds_instances function exists"""
        self.assertTrue(hasattr(rds_instances, 'find_all_rds_instances'))
        self.assertTrue(callable(rds_instances.find_all_rds_instances))

    def test_uniquify_list_function_exists(self):
        """Test that uniquify_list function exists"""
        self.assertTrue(hasattr(rds_instances, 'uniquify_list'))
        self.assertTrue(callable(rds_instances.uniquify_list))

    @patch('inv_scr.operations.rds_instances.get_all_credentials')
    @patch('inv_scr.operations.rds_instances.find_all_rds_instances')
    @patch('inv_scr.operations.rds_instances.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of rds_instances run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock RDS instances found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountNumber': '123456789012',
                'Region': 'us-east-1',
                'DBId': 'test-db-instance',
                'Name': 'test-db',
                'Engine': 'mysql',
                'State': 'available',
                'ParentProfile': 'test-profile'
            }
        ]
        
        rds_instances.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for RDS instances", output)

    def test_uniquify_list_removes_duplicates(self):
        """Test that uniquify_list removes duplicate entries"""
        test_list = [
            {'DBId': 'db-1', 'Name': 'test1'},
            {'DBId': 'db-1', 'Name': 'test1'},  # Duplicate
            {'DBId': 'db-2', 'Name': 'test2'}
        ]
        
        result = rds_instances.uniquify_list(test_list)
        
        self.assertEqual(len(result), 2)
        db_ids = [item['DBId'] for item in result]
        self.assertEqual(db_ids, ['db-1', 'db-2'])

    # Enhanced credential-level mocking tests for RDS Instances
    @patch('inv_scr.operations.rds_instances.get_all_credentials')
    @patch('inv_scr.operations.rds_instances.Inventory_Modules.find_account_rds_instances2')
    @patch('inv_scr.operations.rds_instances.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_single_account_credentials(self, mock_stdout, mock_display, mock_find_rds, mock_get_creds):
        """Test complete RDS instances run flow with single account credentials"""
        # Use shared test data system
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials
        
        # Use scenario-based AWS response
        mock_rds_response = MockAWSResponseFixtures.rds_instances_response(num_instances=2, scenario='simple')
        mock_find_rds.return_value = mock_rds_response
        
        # Create mock args
        mock_args = MockOperationHelpers.create_mock_args(
            pFragments=['all'], pExact=False
        )
        
        with patch('inv_scr.operations.rds_instances.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            rds_instances.run(mock_args)
        
        # Verify credential handling
        mock_get_creds.assert_called_once()
        
        # Verify AWS API was called with correct credentials
        mock_find_rds.assert_called_once_with(mock_credentials[0])
        
        # Verify display was called with processed results
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Verify data transformation logic
        self.assertEqual(len(display_args), 2)  # Should have 2 RDS instances
        for instance in display_args:
            self.assertEqual(instance['AccountNumber'], '123456789012')
            self.assertEqual(instance['Region'], 'us-east-1')
            self.assertEqual(instance['ParentProfile'], 'test-profile')
            self.assertTrue(instance['DBId'].startswith('masteraccount'))
            self.assertIn(instance['Engine'], ['mysql', 'postgres'])
            self.assertEqual(instance['State'], 'available')

    @patch('inv_scr.operations.rds_instances.get_all_credentials')
    @patch('inv_scr.operations.rds_instances.Inventory_Modules.find_account_rds_instances2')
    @patch('inv_scr.operations.rds_instances.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_multi_account_credentials(self, mock_stdout, mock_display, mock_find_rds, mock_get_creds):
        """Test RDS instances operation across multiple accounts"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('multi_account')
        mock_get_creds.return_value = mock_credentials
        
        # Mock different RDS responses for different accounts
        def side_effect(credential):
            account_id = credential['AccountId']
            if account_id == '123456789012':  # master-account
                response = MockAWSResponseFixtures.rds_instances_response(2, scenario='simple')
            elif account_id == '234567890123':  # dev-account
                response = MockAWSResponseFixtures.rds_instances_response(1, scenario='simple')
            else:
                response = {'DBInstances': []}  # Empty response for third account

            # Make DB identifiers account-unique so uniqueness logic does not drop cross-account results
            for inst in response.get('DBInstances', []):
                inst['DBInstanceIdentifier'] = f"{account_id}-{inst['DBInstanceIdentifier']}"
            return response
        
        mock_find_rds.side_effect = side_effect
        
        mock_args = MockOperationHelpers.create_mock_args(pFragments=['all'])
        
        with patch('inv_scr.operations.rds_instances.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            rds_instances.run(mock_args)
        
        # Verify AWS API was called for each account
        self.assertEqual(mock_find_rds.call_count, 3)
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have RDS instances from first two accounts (2 + 1 = 3 total)
        self.assertEqual(len(display_args), 3)
        
        # Verify account distribution
        account_counts = {}
        for instance in display_args:
            account_id = instance['AccountNumber']
            account_counts[account_id] = account_counts.get(account_id, 0) + 1
        
        self.assertEqual(account_counts.get('123456789012', 0), 2)
        self.assertEqual(account_counts.get('234567890123', 0), 1)
        self.assertEqual(account_counts.get('345678901234', 0), 0)

    @patch('inv_scr.operations.rds_instances.get_all_credentials')
    @patch('inv_scr.operations.rds_instances.Inventory_Modules.find_account_rds_instances2')
    @patch('inv_scr.operations.rds_instances.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_fragment_filtering_logic(self, mock_stdout, mock_display, mock_find_rds, mock_get_creds):
        """Test RDS instances fragment filtering logic"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials
        
        # Create response with mixed DB instance names
        mixed_rds_response = {
            'DBInstances': [
                {
                    'DBInstanceIdentifier': 'prod-mysql-db',
                    'DBInstanceClass': 'db.t3.micro',
                    'Engine': 'mysql',
                    'DBInstanceStatus': 'available',
                    'DBName': 'proddb',
                    'AllocatedStorage': 20,
                    'LatestRestorableTime': datetime(2023, 1, 2, 12, 0, 0)
                },
                {
                    'DBInstanceIdentifier': 'dev-postgres-db',
                    'DBInstanceClass': 'db.t3.small',
                    'Engine': 'postgres',
                    'DBInstanceStatus': 'available',
                    'DBName': 'devdb',
                    'AllocatedStorage': 50,
                    'LatestRestorableTime': datetime(2023, 1, 2, 12, 0, 0)
                },
                {
                    'DBInstanceIdentifier': 'test-mysql-db',
                    'DBInstanceClass': 'db.t3.micro',
                    'Engine': 'mysql',
                    'DBInstanceStatus': 'available',
                    'DBName': 'testdb',
                    'AllocatedStorage': 10,
                    'LatestRestorableTime': datetime(2023, 1, 2, 12, 0, 0)
                }
            ]
        }
        mock_find_rds.return_value = mixed_rds_response
        
        # Test filtering for 'prod' fragment
        mock_args = MockOperationHelpers.create_mock_args(
            pFragments=['prod'], pExact=False
        )
        
        with patch('inv_scr.operations.rds_instances.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            rds_instances.run(mock_args)
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have all 3 instances (filtering happens in AWS API, not in our logic)
        self.assertEqual(len(display_args), 3)
        for instance in display_args:
            self.assertIn(instance['DBId'], ['prod-mysql-db', 'dev-postgres-db', 'test-mysql-db'])

    @patch('inv_scr.operations.rds_instances.get_all_credentials')
    @patch('inv_scr.operations.rds_instances.Inventory_Modules.find_account_rds_instances2')
    @patch('inv_scr.operations.rds_instances.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_uniquification_logic(self, mock_stdout, mock_display, mock_find_rds, mock_get_creds):
        """Test RDS instances uniquification logic"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials
        
        # Create response with duplicate DB instances (simulating multi-region scenario)
        duplicate_rds_response = {
            'DBInstances': [
                {
                    'DBInstanceIdentifier': 'duplicate-db',
                    'DBInstanceClass': 'db.t3.micro',
                    'Engine': 'mysql',
                    'DBInstanceStatus': 'available',
                    'DBName': 'duplicatedb',
                    'AllocatedStorage': 20,
                    'LatestRestorableTime': datetime(2023, 1, 2, 12, 0, 0)
                },
                {
                    'DBInstanceIdentifier': 'unique-db',
                    'DBInstanceClass': 'db.t3.small',
                    'Engine': 'postgres',
                    'DBInstanceStatus': 'available',
                    'DBName': 'uniquedb',
                    'AllocatedStorage': 50,
                    'LatestRestorableTime': datetime(2023, 1, 2, 12, 0, 0)
                }
            ]
        }
        mock_find_rds.return_value = duplicate_rds_response
        
        mock_args = MockOperationHelpers.create_mock_args(pFragments=['all'])
        
        with patch('inv_scr.operations.rds_instances.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            
            rds_instances.run(mock_args)
        
        # Verify display was called
        mock_display.assert_called_once()
        display_args = mock_display.call_args[0][0]
        
        # Should have 2 unique instances
        self.assertEqual(len(display_args), 2)
        db_ids = [instance['DBId'] for instance in display_args]
        self.assertEqual(len(set(db_ids)), 2)  # All unique
        self.assertIn('duplicate-db', db_ids)
        self.assertIn('unique-db', db_ids)


class TestPlaceholderOperations(unittest.TestCase):
    """Test cases for placeholder operations"""

    def test_all_placeholder_operations_have_required_functions(self):
        """Test that all placeholder operations have required functions"""
        placeholder_operations = [
            'directories', 'ecs_clusters', 'enis', 'gas',
            'gd_detectors', 'phzs', 'policies',
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


class TestRamSharesOperation(unittest.TestCase):
    """Test cases for RAM shares operation"""

    @patch('inv_scr.operations.ram_shares.get_all_credentials')
    @patch('inv_scr.operations.ram_shares._find_all_ram_shares')
    @patch('inv_scr.operations.ram_shares.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_mocked_shares(self, mock_stdout, mock_display, mock_find_ram, mock_get_creds):
        """Validate RAM shares run flow with mocked data"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials

        mock_find_ram.return_value = [
            {
                'ParentProfile': 'test-profile',
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'OwnerAccount': '123456789012',
                'Region': 'us-east-1',
                'ShareType': 'OWNED',
                'ShareName': 'test-share',
                'Status': 'ACTIVE',
                'ResourceCount': 1,
                'SharedWithCount': 1,
                'AllowExternalPrincipals': False,
                'Resources': 'ec2: arn:aws:ec2:us-east-1:123456789012:subnet/subnet-123456',
                'SharedWith': '123456789012',
                'ShareArn': 'arn:aws:ram:us-east-1:123456789012:resource-share/abc',
                'CreationTime': '2024-01-01T00:00:00Z',
                'LastUpdatedTime': '2024-01-02T00:00:00Z',
                'Tags': 'env=test'
            }
        ]

        mock_args = MockOperationHelpers.create_mock_args(pStatus=None, pType=None)

        with patch('inv_scr.operations.ram_shares.tqdm') as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value = mock_pbar
            ram_shares.run(mock_args)

        mock_get_creds.assert_called_once()
        mock_find_ram.assert_called_once()
        mock_display.assert_called_once()

        display_args = mock_display.call_args[0][0]
        self.assertEqual(len(display_args), 1)
        self.assertEqual(display_args[0]['ShareName'], 'test-share')
        self.assertEqual(display_args[0]['ShareType'], 'OWNED')
        self.assertEqual(display_args[0]['Region'], 'us-east-1')

    def test_add_operation_args(self):
        """Test argument parser setup for ram_shares operation"""
        # Create a mock parser
        mock_parser = MagicMock()
        mock_group = MagicMock()
        mock_parser.my_parser.add_argument_group.return_value = mock_group
        
        # Test the argument setup
        ram_shares.add_operation_args(mock_parser)
        
        # Verify argument group was created
        mock_parser.my_parser.add_argument_group.assert_called_once_with('ram-shares', 'AWS RAM shares options')
        
        # Verify arguments were added (3 arguments: status, type, and version)
        self.assertEqual(mock_group.add_argument.call_count, 3)

    @patch('inv_scr.operations.ram_shares.boto3.Session')
    @patch('inv_scr.operations.ram_shares.logging')
    def test_get_ram_shares_for_account_client_error(self, mock_logging, mock_session):
        """Test error handling in _get_ram_shares_for_account when AWS API fails"""
        from botocore.exceptions import ClientError
        
        # Setup mock credentials
        mock_credentials = {
            'AccessKeyId': 'test-key',
            'SecretAccessKey': 'test-secret',
            'SessionToken': 'test-token',
            'Region': 'us-east-1',
            'AccountId': '123456789012'
        }
        
        # Setup mock client that raises ClientError
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        
        # Mock paginator that returns shares
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                'resourceShares': [
                    {
                        'resourceShareArn': 'arn:aws:ram:us-east-1:123456789012:resource-share/test',
                        'name': 'test-share',
                        'status': 'ACTIVE',
                        'owningAccountId': '123456789012',
                        'creationTime': '2024-01-01T00:00:00Z',
                        'lastUpdatedTime': '2024-01-02T00:00:00Z',
                        'allowExternalPrincipals': False,
                        'tags': []
                    }
                ]
            }
        ]
        
        # Make get_resource_share_associations raise ClientError
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
        mock_client.get_resource_share_associations.side_effect = ClientError(error_response, 'GetResourceShareAssociations')
        
        # Call the function with specific type to get only one share type
        result = ram_shares._get_ram_shares_for_account(mock_credentials, None, 'OWNED')
        
        # Verify error was logged and function still returns results
        mock_logging.debug.assert_called()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)  # Should still return the share even with API errors

    @patch('inv_scr.operations.ram_shares.boto3.Session')
    def test_get_ram_shares_for_account_with_filters(self, mock_session):
        """Test _get_ram_shares_for_account with status and type filters"""
        # Setup mock credentials
        mock_credentials = {
            'AccessKeyId': 'test-key',
            'SecretAccessKey': 'test-secret',
            'SessionToken': 'test-token',
            'Region': 'us-east-1',
            'AccountId': '123456789012'
        }
        
        # Setup mock client
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        
        # Mock paginator with shares of different statuses
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                'resourceShares': [
                    {
                        'resourceShareArn': 'arn:aws:ram:us-east-1:123456789012:resource-share/active',
                        'name': 'active-share',
                        'status': 'ACTIVE',
                        'owningAccountId': '123456789012',
                        'creationTime': '2024-01-01T00:00:00Z',
                        'lastUpdatedTime': '2024-01-02T00:00:00Z',
                        'allowExternalPrincipals': False,
                        'tags': []
                    },
                    {
                        'resourceShareArn': 'arn:aws:ram:us-east-1:123456789012:resource-share/pending',
                        'name': 'pending-share',
                        'status': 'PENDING',
                        'owningAccountId': '123456789012',
                        'creationTime': '2024-01-01T00:00:00Z',
                        'lastUpdatedTime': '2024-01-02T00:00:00Z',
                        'allowExternalPrincipals': False,
                        'tags': []
                    }
                ]
            }
        ]
        
        # Mock successful API responses
        mock_client.get_resource_share_associations.return_value = {
            'resourceShareAssociations': []
        }
        
        # Test with status filter - should only return ACTIVE shares
        result = ram_shares._get_ram_shares_for_account(mock_credentials, 'ACTIVE', 'OWNED')
        
        # Should only get the ACTIVE share
        active_shares = [share for share in result if share['Status'] == 'ACTIVE']
        pending_shares = [share for share in result if share['Status'] == 'PENDING']
        
        self.assertGreater(len(active_shares), 0)
        self.assertEqual(len(pending_shares), 0)

    @patch('inv_scr.operations.ram_shares._get_ram_shares_for_account')
    @patch('inv_scr.operations.ram_shares.tqdm')
    @patch('inv_scr.operations.ram_shares.logging')
    def test_find_all_ram_shares_with_client_error(self, mock_logging, mock_tqdm, mock_get_shares):
        """Test error handling in _find_all_ram_shares when individual account processing fails"""
        from botocore.exceptions import ClientError
        
        # Setup mock credentials
        mock_credentials = [
            {
                'AccessKeyId': 'test-key',
                'SecretAccessKey': 'test-secret',
                'SessionToken': 'test-token',
                'Region': 'us-east-1',
                'AccountId': '123456789012',
                'ParentProfile': 'test-profile',
                'MgmtAccount': '123456789012'
            }
        ]
        
        # Setup mock progress bar
        mock_pbar = MagicMock()
        mock_tqdm.return_value = mock_pbar
        
        # Make _get_ram_shares_for_account raise ClientError
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
        mock_get_shares.side_effect = ClientError(error_response, 'GetResourceShares')
        
        # Call the function
        result = ram_shares._find_all_ram_shares(mock_credentials, None, None)
        
        # Verify error was logged and function returns empty list
        mock_logging.error.assert_called()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
        
        # Verify progress bar was updated
        mock_pbar.update.assert_called()

    @patch('inv_scr.operations.ram_shares._get_ram_shares_for_account')
    @patch('inv_scr.operations.ram_shares.tqdm')
    def test_find_all_ram_shares_threading(self, mock_tqdm, mock_get_shares):
        """Test threading behavior in _find_all_ram_shares"""
        # Setup mock credentials for multiple accounts
        mock_credentials = []
        for i in range(5):
            mock_credentials.append({
                'AccessKeyId': f'test-key-{i}',
                'SecretAccessKey': f'test-secret-{i}',
                'SessionToken': f'test-token-{i}',
                'Region': 'us-east-1',
                'AccountId': f'12345678901{i}',
                'ParentProfile': 'test-profile',
                'MgmtAccount': f'12345678901{i}'
            })
        
        # Setup mock progress bar
        mock_pbar = MagicMock()
        mock_tqdm.return_value = mock_pbar
        
        # Mock successful share retrieval
        mock_get_shares.return_value = [
            {
                'ShareType': 'OWNED',
                'ShareArn': 'arn:aws:ram:us-east-1:123456789012:resource-share/test',
                'ShareName': 'test-share',
                'Status': 'ACTIVE',
                'OwningAccountId': '123456789012',
                'CreationTime': '2024-01-01T00:00:00Z',
                'LastUpdatedTime': '2024-01-02T00:00:00Z',
                'AllowExternalPrincipals': False,
                'Tags': [],
                'Resources': [],
                'SharedWith': []
            }
        ]
        
        # Call the function
        result = ram_shares._find_all_ram_shares(mock_credentials, None, None)
        
        # Verify all credentials were processed
        self.assertEqual(mock_get_shares.call_count, 5)
        self.assertIsInstance(result, list)
        
        # Verify progress bar was updated for each credential
        self.assertEqual(mock_pbar.update.call_count, 5)

    @patch('inv_scr.operations.ram_shares.get_all_credentials')
    @patch('inv_scr.operations.ram_shares._find_all_ram_shares')
    @patch('inv_scr.operations.ram_shares.display_results')
    def test_run_with_filters(self, mock_display, mock_find_ram, mock_get_creds):
        """Test run function with status and type filters"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials
        mock_find_ram.return_value = []
        
        # Create mock args with filters
        mock_args = MockOperationHelpers.create_mock_args(pStatus='ACTIVE', pType='OWNED')
        
        with patch('inv_scr.operations.ram_shares.tqdm'):
            ram_shares.run(mock_args)
        
        # Verify _find_all_ram_shares was called with the correct filters
        mock_find_ram.assert_called_once_with(mock_credentials, 'ACTIVE', 'OWNED')

    @patch('inv_scr.operations.ram_shares.get_all_credentials')
    @patch('inv_scr.operations.ram_shares._find_all_ram_shares')
    @patch('inv_scr.operations.ram_shares.display_results')
    def test_run_with_timing_context(self, mock_display, mock_find_ram, mock_get_creds):
        """Test run function with timing context"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials
        mock_find_ram.return_value = []
        
        # Create mock args with timing context
        mock_timing = MagicMock()
        mock_args = MockOperationHelpers.create_mock_args()
        mock_args._timing_context = mock_timing
        
        with patch('inv_scr.operations.ram_shares.tqdm'):
            ram_shares.run(mock_args)
        
        # Verify timing milestones were called
        expected_calls = [
            call("args_parsed", "Arguments parsed and validated"),
            call("credentials_setup", unittest.mock.ANY),
            call("ram_shares_found", unittest.mock.ANY),
            call("results_displayed", "RAM shares results formatted and displayed")
        ]
        
        for expected_call in expected_calls:
            self.assertIn(expected_call, mock_timing.milestone.call_args_list)


class TestConfigRecordersOperation(unittest.TestCase):
    """Test cases for Config recorders operation"""

    @patch('inv_scr.operations.config_recorders.get_all_credentials')
    @patch('inv_scr.operations.config_recorders._collect_for_credential')
    @patch('inv_scr.operations.config_recorders.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_mocked_config_items(self, mock_stdout, mock_display, mock_collect, mock_get_creds):
        """Validate config recorders run flow with mocked data"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials

        mock_collect.return_value = [
            {
                'ParentProfile': 'test-profile',
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'Type': 'Config Recorder',
                'Name': 'test-recorder',
                'RoleArn': 'arn:aws:iam::123456789012:role/config',
                'AllSupported': True,
                'IncludeGlobalResourceTypes': True,
                'ResourceTypes': ''
            },
            {
                'ParentProfile': 'test-profile',
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'Type': 'Delivery Channel',
                'Name': 'test-delivery-channel',
                'S3Bucket': 'config-bucket',
                'SnsTopic': 'arn:aws:sns:us-east-1:123456789012:config',
                'Frequency': 'TwentyFour_Hours'
            }
        ]

        mock_args = MockOperationHelpers.create_mock_args(pFragments=['all'], pExact=False)

        with patch('inv_scr.operations.config_recorders.tqdm') as mock_tqdm:
            mock_tqdm.side_effect = lambda *args, **kwargs: mock_credentials  # ensure iteration
            config_recorders.run(mock_args)

        mock_get_creds.assert_called_once()
        self.assertEqual(mock_collect.call_count, len(mock_credentials))
        mock_display.assert_called_once()

        display_args = mock_display.call_args[0][0]
        self.assertEqual(len(display_args), 2)
        names = {item['Name'] for item in display_args}
        self.assertIn('test-recorder', names)
        self.assertIn('test-delivery-channel', names)


class TestCloudTrailOperation(unittest.TestCase):
    """Test cases for CloudTrail operation"""

    @patch('inv_scr.operations.cloudtrail.get_all_credentials')
    @patch('inv_scr.operations.cloudtrail._find_cloudtrails')
    @patch('inv_scr.operations.cloudtrail.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_mocked_trails(self, mock_stdout, mock_display, mock_find, mock_get_creds):
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials

        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'TrailName': 'org-trail',
                'OrgTrail': 'OrgTrail',
                'Bucket': 'org-bucket',
                'MultiRegion': True,
                'HomeRegion': 'us-east-1',
            }
        ]

        mock_args = MockOperationHelpers.create_mock_args()
        cloudtrail.run(mock_args)

        mock_get_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()

        display_args = mock_display.call_args[0][0]
        self.assertEqual(len(display_args), 1)
        self.assertEqual(display_args[0]['TrailName'], 'org-trail')


class TestAZsOperation(unittest.TestCase):
    """Test cases for AZ coverage operation"""

    @patch('inv_scr.operations.azs.get_all_credentials')
    @patch('inv_scr.operations.azs._collect_azs')
    @patch('inv_scr.operations.azs.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_mocked_azs(self, mock_stdout, mock_display, mock_collect, mock_get_creds):
        mock_credentials = MockCredentialFixtures.single_account_single_region()
        mock_get_creds.return_value = mock_credentials

        mock_collect.return_value = [
            {
                'ParentProfile': 'test-profile',
                'MgmtAccount': '123456789012',
                'AccountNumber': '123456789012',
                'Region': 'us-east-1',
                'ZoneName': 'us-east-1a',
                'ZoneId': 'use1-az1',
                'ZoneType': 'availability-zone',
            }
        ]

        mock_args = MockOperationHelpers.create_mock_args()
        azs.run(mock_args)

        mock_get_creds.assert_called_once()
        mock_collect.assert_called_once()
        mock_display.assert_called_once()

        display_args = mock_display.call_args[0][0]
        self.assertEqual(len(display_args), 1)
        self.assertEqual(display_args[0]['ZoneName'], 'us-east-1a')


class TestOrgUsersOperation(unittest.TestCase):
    """Test cases for org-users operation"""

    @patch('inv_scr.operations.org_users.get_all_credentials')
    @patch('inv_scr.operations.org_users.find_iam_users2')
    @patch('inv_scr.operations.org_users.find_idc_directory_id2')
    @patch('inv_scr.operations.org_users.find_idc_users2')
    @patch('inv_scr.operations.org_users.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_mocked_users(self, mock_stdout, mock_display, mock_idc_users, mock_idc_dirs, mock_iam_users, mock_get_creds):
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_get_creds.return_value = mock_credentials

        mock_iam_users.return_value = [
            {'UserName': 'iam-user-1', 'PasswordLastUsed': '2024-01-01'}
        ]
        mock_idc_dirs.return_value = ['dir-1234']
        mock_idc_users.return_value = [
            {'UserName': 'idc-user-1', 'PasswordLastUsed': '2024-01-02'}
        ]

        mock_args = MockOperationHelpers.create_mock_args(pIAM=True, pIdentityCenter=True)
        org_users.run(mock_args)

        mock_get_creds.assert_called_once()
        mock_iam_users.assert_called_once()
        mock_idc_dirs.assert_called_once()
        mock_idc_users.assert_called_once()
        mock_display.assert_called_once()

        display_args = mock_display.call_args[0][0]
        names = {user['UserName'] for user in display_args}
        self.assertIn('iam-user-1', names)
        self.assertIn('idc-user-1', names)


if __name__ == '__main__':
    unittest.main()


class TestSubnetsOperation(unittest.TestCase):
    """Test cases for the VPC subnets operation"""

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
        self.mock_args.pipaddresses = None

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(subnets, 'add_operation_args'))
        self.assertTrue(callable(subnets.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(subnets, 'run'))
        self.assertTrue(callable(subnets.run))

    def test_find_all_subnets_function_exists(self):
        """Test that find_all_subnets function exists"""
        self.assertTrue(hasattr(subnets, 'find_all_subnets'))
        self.assertTrue(callable(subnets.find_all_subnets))

    @patch('inv_scr.operations.subnets.get_all_credentials')
    @patch('inv_scr.operations.subnets.find_all_subnets')
    @patch('inv_scr.operations.subnets.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of subnets run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock subnets found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'SubnetId': 'subnet-12345678',
                'SubnetName': 'test-subnet',
                'CidrBlock': '10.0.1.0/24',
                'VPCId': 'vpc-12345678',
                'AvailableIpAddressCount': 250,
                'ParentProfile': 'test-profile'
            }
        ]
        
        subnets.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for VPC subnets", output)

    def test_find_all_subnets_empty_credentials(self):
        """Test find_all_subnets with empty credentials list"""
        result = subnets.find_all_subnets([])
        self.assertEqual(result, [])


class TestPhzsOperation(unittest.TestCase):
    """Test cases for the Private Hosted Zones operation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_args = MagicMock()
        self.mock_args.Profiles = ['test-profile']
        self.mock_args.Accounts = None
        self.mock_args.SkipAccounts = None
        self.mock_args.SkipProfiles = None
        self.mock_args.RootOnly = False
        self.mock_args.Filename = None
        self.mock_args.Time = False

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(phzs, 'add_operation_args'))
        self.assertTrue(callable(phzs.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(phzs, 'run'))
        self.assertTrue(callable(phzs.run))

    def test_find_all_hosted_zones_function_exists(self):
        """Test that find_all_hosted_zones function exists"""
        self.assertTrue(hasattr(phzs, 'find_all_hosted_zones'))
        self.assertTrue(callable(phzs.find_all_hosted_zones))

    @patch('inv_scr.operations.phzs.get_all_credentials')
    @patch('inv_scr.operations.phzs.find_all_hosted_zones')
    @patch('inv_scr.operations.phzs.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of phzs run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock hosted zones found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'Global',
                'PHZName': 'example.internal.',
                'Records': 5,
                'PHZId': '/hostedzone/Z123456789',
                'ParentProfile': 'test-profile'
            }
        ]
        
        phzs.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for Private Hosted Zones", output)

    def test_find_all_hosted_zones_empty_credentials(self):
        """Test find_all_hosted_zones with empty credentials list"""
        result = phzs.find_all_hosted_zones([])
        self.assertEqual(result, [])


class TestEnisOperation(unittest.TestCase):
    """Test cases for the Elastic Network Interfaces operation"""

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
        self.mock_args.pipaddresses = None
        self.mock_args.pDNSNames = None
        self.mock_args.ppublic = False
        self.mock_args.loglevel = 50

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(enis, 'add_operation_args'))
        self.assertTrue(callable(enis.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(enis, 'run'))
        self.assertTrue(callable(enis.run))

    def test_find_all_enis_function_exists(self):
        """Test that find_all_enis function exists"""
        self.assertTrue(hasattr(enis, 'find_all_enis'))
        self.assertTrue(callable(enis.find_all_enis))

    @patch('inv_scr.operations.enis.get_all_credentials')
    @patch('inv_scr.operations.enis.find_all_enis')
    @patch('inv_scr.operations.enis.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of enis run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock ENIs found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'ENIId': 'eni-12345678',
                'PrivateDnsName': 'ip-10-0-1-100.ec2.internal',
                'Status': 'in-use',
                'PublicIp': '54.123.45.67',
                'PrivateIpAddress': '10.0.1.100',
                'ParentProfile': 'test-profile'
            }
        ]
        
        enis.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for Elastic Network Interfaces", output)

    def test_find_all_enis_empty_credentials(self):
        """Test find_all_enis with empty credentials list"""
        result = enis.find_all_enis([])
        self.assertEqual(result, [])

    def test_resolve_names_to_ips_function_exists(self):
        """Test that resolve_names_to_ips function exists"""
        self.assertTrue(hasattr(enis, 'resolve_names_to_ips'))
        self.assertTrue(callable(enis.resolve_names_to_ips))

    @patch('socket.getaddrinfo')
    def test_resolve_names_to_ips_single_fqdn(self, mock_getaddrinfo):
        """Test resolving a single FQDN to IP addresses"""
        # Mock DNS resolution returning IPv4 address
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('93.184.216.34', 0))
        ]
        
        result = enis.resolve_names_to_ips(['example.com'])
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['fqdn'], 'example.com')
        self.assertIn('93.184.216.34', result[0]['IPs'])
        mock_getaddrinfo.assert_called_once_with('example.com', None)

    @patch('socket.getaddrinfo')
    def test_resolve_names_to_ips_multiple_fqdns(self, mock_getaddrinfo):
        """Test resolving multiple FQDNs to IP addresses"""
        # Mock DNS resolution for different domains
        def mock_dns_lookup(fqdn, port):
            if fqdn == 'example.com':
                return [(2, 1, 6, '', ('93.184.216.34', 0))]
            elif fqdn == 'test.example.com':
                return [(2, 1, 6, '', ('192.0.2.1', 0))]
            return []
        
        mock_getaddrinfo.side_effect = mock_dns_lookup
        
        result = enis.resolve_names_to_ips(['example.com', 'test.example.com'])
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['fqdn'], 'example.com')
        self.assertIn('93.184.216.34', result[0]['IPs'])
        self.assertEqual(result[1]['fqdn'], 'test.example.com')
        self.assertIn('192.0.2.1', result[1]['IPs'])

    @patch('socket.getaddrinfo')
    def test_resolve_names_to_ips_multiple_ips_per_fqdn(self, mock_getaddrinfo):
        """Test resolving FQDN that returns multiple IP addresses"""
        # Mock DNS resolution returning multiple IPs
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('93.184.216.34', 0)),
            (2, 1, 6, '', ('93.184.216.35', 0)),
            (10, 1, 6, '', ('2606:2800:220:1:248:1893:25c8:1946', 0))
        ]
        
        result = enis.resolve_names_to_ips(['example.com'])
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['fqdn'], 'example.com')
        # Should have both IPv4 and IPv6 addresses
        self.assertGreaterEqual(len(result[0]['IPs']), 2)

    @patch('socket.getaddrinfo')
    def test_resolve_names_to_ips_dns_failure(self, mock_getaddrinfo):
        """Test handling of DNS resolution failure"""
        # Mock DNS resolution failure
        mock_getaddrinfo.side_effect = socket.gaierror("Name or service not known")
        
        result = enis.resolve_names_to_ips(['nonexistent.invalid'])
        
        # Should return empty list for failed resolution
        self.assertEqual(len(result), 0)

    @patch('socket.getaddrinfo')
    def test_resolve_names_to_ips_partial_failure(self, mock_getaddrinfo):
        """Test handling when some FQDNs resolve and others fail"""
        def mock_dns_lookup(fqdn, port):
            if fqdn == 'example.com':
                return [(2, 1, 6, '', ('93.184.216.34', 0))]
            else:
                raise socket.gaierror("Name or service not known")
        
        mock_getaddrinfo.side_effect = mock_dns_lookup
        
        result = enis.resolve_names_to_ips(['example.com', 'nonexistent.invalid'])
        
        # Should return only the successful resolution
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['fqdn'], 'example.com')

    @patch('inv_scr.operations.enis.get_all_credentials')
    @patch('inv_scr.operations.enis.find_all_enis')
    @patch('inv_scr.operations.enis.display_results')
    @patch('inv_scr.operations.enis.resolve_names_to_ips')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_fqdn_parameter(self, mock_stdout, mock_resolve, mock_display, mock_find, mock_creds):
        """Test run function with FQDN parameter"""
        # Set up FQDN parameter
        self.mock_args.pDNSNames = ['example.com']
        
        # Mock DNS resolution
        mock_resolve.return_value = [
            {'fqdn': 'example.com', 'IPs': ['93.184.216.34']}
        ]
        
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock ENIs found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'ENIId': 'eni-12345678',
                'PrivateDnsName': 'ip-10-0-1-100.ec2.internal',
                'Status': 'in-use',
                'PublicIp': '93.184.216.34',
                'PrivateIpAddress': '10.0.1.100',
                'ParentProfile': 'test-profile'
            }
        ]
        
        enis.run(self.mock_args)
        
        # Verify DNS resolution was called
        mock_resolve.assert_called_once_with(['example.com'])
        
        # Verify find_all_enis was called with resolved IPs
        call_args = mock_find.call_args
        self.assertIn('93.184.216.34', call_args[0][1])

    @patch('inv_scr.operations.enis.get_all_credentials')
    @patch('inv_scr.operations.enis.find_all_enis')
    @patch('inv_scr.operations.enis.display_results')
    @patch('inv_scr.operations.enis.resolve_names_to_ips')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_fqdn_and_ipaddress(self, mock_stdout, mock_resolve, mock_display, mock_find, mock_creds):
        """Test run function with both FQDN and IP address parameters"""
        # Set up both FQDN and IP parameters
        self.mock_args.pDNSNames = ['example.com']
        self.mock_args.pipaddresses = ['1.2.3.4']
        
        # Mock DNS resolution
        mock_resolve.return_value = [
            {'fqdn': 'example.com', 'IPs': ['93.184.216.34']}
        ]
        
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock ENIs found
        mock_find.return_value = []
        
        enis.run(self.mock_args)
        
        # Verify find_all_enis was called with both original and resolved IPs
        call_args = mock_find.call_args
        ip_list = call_args[0][1]
        self.assertIn('1.2.3.4', ip_list)
        self.assertIn('93.184.216.34', ip_list)

    @patch('inv_scr.operations.enis.get_all_credentials')
    @patch('inv_scr.operations.enis.find_all_enis')
    @patch('inv_scr.operations.enis.display_results')
    @patch('inv_scr.operations.enis.resolve_names_to_ips')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_with_fqdn_verbose_output(self, mock_stdout, mock_resolve, mock_display, mock_find, mock_creds):
        """Test run function displays DNS resolution results in verbose mode"""
        # Set up FQDN parameter and verbose logging
        self.mock_args.pDNSNames = ['example.com', 'test.example.com']
        self.mock_args.loglevel = 40  # Less than 50 to trigger verbose output
        
        # Mock DNS resolution
        mock_resolve.return_value = [
            {'fqdn': 'example.com', 'IPs': ['93.184.216.34']},
            {'fqdn': 'test.example.com', 'IPs': ['192.0.2.1', '192.0.2.2']}
        ]
        
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock ENIs found
        mock_find.return_value = []
        
        enis.run(self.mock_args)
        
        # Check output contains DNS resolution information
        output = mock_stdout.getvalue()
        self.assertIn("resolve 2 DNS Names", output)
        self.assertIn("example.com", output)
        self.assertIn("test.example.com", output)


class TestEcsClustersOperation(unittest.TestCase):
    """Test cases for the ECS Clusters operation"""

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
        self.assertTrue(hasattr(ecs_clusters, 'add_operation_args'))
        self.assertTrue(callable(ecs_clusters.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(ecs_clusters, 'run'))
        self.assertTrue(callable(ecs_clusters.run))

    def test_find_all_clusters_and_tasks_function_exists(self):
        """Test that find_all_clusters_and_tasks function exists"""
        self.assertTrue(hasattr(ecs_clusters, 'find_all_clusters_and_tasks'))
        self.assertTrue(callable(ecs_clusters.find_all_clusters_and_tasks))

    @patch('inv_scr.operations.ecs_clusters.get_all_credentials')
    @patch('inv_scr.operations.ecs_clusters.find_all_clusters_and_tasks')
    @patch('inv_scr.operations.ecs_clusters.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of ecs_clusters run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock ECS clusters found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'ClusterName': 'test-cluster',
                'Status': 'Active',
                'TaskCount': 5,
                'ServiceCount': 2,
                'ParentProfile': 'test-profile'
            }
        ]
        
        ecs_clusters.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for ECS clusters", output)

    def test_find_all_clusters_and_tasks_empty_credentials(self):
        """Test find_all_clusters_and_tasks with empty credentials list"""
        result = ecs_clusters.find_all_clusters_and_tasks([])
        self.assertEqual(result, [])


# if __name__ == '__main__':
#     unittest.main()

class TestDirectoriesOperation(unittest.TestCase):
    """Test cases for the AWS Directory Service operation"""

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
        self.mock_args.pFragments = ['all']
        self.mock_args.pExact = False

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(directories, 'add_operation_args'))
        self.assertTrue(callable(directories.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(directories, 'run'))
        self.assertTrue(callable(directories.run))

    def test_find_all_directories_function_exists(self):
        """Test that find_all_directories function exists"""
        self.assertTrue(hasattr(directories, 'find_all_directories'))
        self.assertTrue(callable(directories.find_all_directories))

    @patch('inv_scr.operations.directories.get_all_credentials')
    @patch('inv_scr.operations.directories.find_all_directories')
    @patch('inv_scr.operations.directories.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of directories run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock directories found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'DirectoryName': 'test-directory',
                'DirectoryId': 'd-12345678',
                'Status': 'Active',
                'Type': 'MicrosoftAD',
                'ParentProfile': 'test-profile'
            }
        ]
        
        directories.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for AWS Directory Service directories", output)

    def test_find_all_directories_empty_credentials(self):
        """Test find_all_directories with empty credentials list"""
        result = directories.find_all_directories([])
        self.assertEqual(result, [])


class TestGasOperation(unittest.TestCase):
    """Test cases for the Global Accelerator operation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_args = MagicMock()
        self.mock_args.Profiles = ['test-profile']
        self.mock_args.Accounts = None
        self.mock_args.SkipAccounts = None
        self.mock_args.SkipProfiles = None
        self.mock_args.AccessRoles = None
        self.mock_args.RootOnly = False
        self.mock_args.Filename = None
        self.mock_args.Time = False
        self.mock_args.pstatus = 'all'

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(gas, 'add_operation_args'))
        self.assertTrue(callable(gas.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(gas, 'run'))
        self.assertTrue(callable(gas.run))

    def test_find_all_global_accelerators_function_exists(self):
        """Test that find_all_global_accelerators function exists"""
        self.assertTrue(hasattr(gas, 'find_all_global_accelerators'))
        self.assertTrue(callable(gas.find_all_global_accelerators))

    @patch('inv_scr.operations.gas.get_all_credentials')
    @patch('inv_scr.operations.gas.find_all_global_accelerators')
    @patch('inv_scr.operations.gas.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of gas run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-west-2', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock global accelerators found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'Global',
                'Name': 'test-accelerator',
                'Status': 'DEPLOYED',
                'DNSName': 'a1234567890abcdef.awsglobalaccelerator.com',
                'ParentProfile': 'test-profile'
            }
        ]
        
        gas.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for Global Accelerators", output)

    def test_find_all_global_accelerators_empty_credentials(self):
        """Test find_all_global_accelerators with empty credentials list"""
        result = gas.find_all_global_accelerators([])
        self.assertEqual(result, [])


class TestGdDetectorsOperation(unittest.TestCase):
    """Test cases for the GuardDuty Detectors operation"""

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

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(gd_detectors, 'add_operation_args'))
        self.assertTrue(callable(gd_detectors.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(gd_detectors, 'run'))
        self.assertTrue(callable(gd_detectors.run))

    def test_find_all_gd_detectors_function_exists(self):
        """Test that find_all_gd_detectors function exists"""
        self.assertTrue(hasattr(gd_detectors, 'find_all_gd_detectors'))
        self.assertTrue(callable(gd_detectors.find_all_gd_detectors))

    @patch('inv_scr.operations.gd_detectors.get_all_credentials')
    @patch('inv_scr.operations.gd_detectors.find_all_gd_detectors')
    @patch('inv_scr.operations.gd_detectors.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of gd_detectors run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock detectors found
        mock_find.return_value = ([
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'DetectorId': '12345678901234567890',
                'IsAdminAccount': True,
                'MemberCount': 5,
                'ParentProfile': 'test-profile'
            }
        ], [])  # Empty invitations list
        
        gd_detectors.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for GuardDuty detectors", output)

    def test_find_all_gd_detectors_empty_credentials(self):
        """Test find_all_gd_detectors with empty credentials list"""
        detectors, invitations = gd_detectors.find_all_gd_detectors([])
        self.assertEqual(detectors, [])
        self.assertEqual(invitations, [])


class TestPoliciesOperation(unittest.TestCase):
    """Test cases for the IAM Policies operation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_args = MagicMock()
        self.mock_args.Profiles = ['test-profile']
        self.mock_args.Accounts = None
        self.mock_args.SkipAccounts = None
        self.mock_args.SkipProfiles = None
        self.mock_args.RootOnly = False
        self.mock_args.Filename = None
        self.mock_args.Time = False
        self.mock_args.pFragments = ['all']
        self.mock_args.pExact = False
        self.mock_args.paction = None
        self.mock_args.pcmp = False

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(policies, 'add_operation_args'))
        self.assertTrue(callable(policies.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(policies, 'run'))
        self.assertTrue(callable(policies.run))

    def test_find_all_policies_function_exists(self):
        """Test that find_all_policies function exists"""
        self.assertTrue(hasattr(policies, 'find_all_policies'))
        self.assertTrue(callable(policies.find_all_policies))

    @patch('inv_scr.operations.policies.get_all_credentials')
    @patch('inv_scr.operations.policies.find_all_policies')
    @patch('inv_scr.operations.policies.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of policies run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock policies found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountNumber': '123456789012',
                'Region': 'us-east-1',
                'PolicyName': 'test-policy',
                'Action': 's3:GetObject',
                'ParentProfile': 'test-profile'
            }
        ]
        
        policies.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for IAM policies", output)

    def test_find_all_policies_empty_credentials(self):
        """Test find_all_policies with empty credentials list"""
        result = policies.find_all_policies([])
        self.assertEqual(result, [])


class TestRolesOperation(unittest.TestCase):
    """Test cases for the IAM Roles operation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_args = MagicMock()
        self.mock_args.Profiles = ['test-profile']
        self.mock_args.Regions = ['us-east-1']
        self.mock_args.Accounts = None
        self.mock_args.SkipAccounts = None
        self.mock_args.SkipProfiles = None
        self.mock_args.RootOnly = False
        self.mock_args.Filename = None
        self.mock_args.Time = False
        self.mock_args.pFragments = None
        self.mock_args.pExact = False

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(roles, 'add_operation_args'))
        self.assertTrue(callable(roles.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(roles, 'run'))
        self.assertTrue(callable(roles.run))

    def test_find_all_roles_function_exists(self):
        """Test that find_all_roles function exists"""
        self.assertTrue(hasattr(roles, 'find_all_roles'))
        self.assertTrue(callable(roles.find_all_roles))

    @patch('inv_scr.operations.roles.get_all_credentials')
    @patch('inv_scr.operations.roles.find_all_roles')
    @patch('inv_scr.operations.roles.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of roles run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock roles found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'RoleName': 'test-role',
                'Path': '/',
                'CreateDate': '2023-01-01',
                'ParentProfile': 'test-profile'
            }
        ]
        
        roles.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for IAM roles", output)

    def test_find_all_roles_empty_credentials(self):
        """Test find_all_roles with empty credentials list"""
        result = roles.find_all_roles([])
        self.assertEqual(result, [])


class TestSamlProvidersOperation(unittest.TestCase):
    """Test cases for the SAML Providers operation"""

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

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(saml_providers, 'add_operation_args'))
        self.assertTrue(callable(saml_providers.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(saml_providers, 'run'))
        self.assertTrue(callable(saml_providers.run))

    def test_find_all_saml_providers_function_exists(self):
        """Test that find_all_saml_providers function exists"""
        self.assertTrue(hasattr(saml_providers, 'find_all_saml_providers'))
        self.assertTrue(callable(saml_providers.find_all_saml_providers))

    @patch('inv_scr.operations.saml_providers.get_all_credentials')
    @patch('inv_scr.operations.saml_providers.find_all_saml_providers')
    @patch('inv_scr.operations.saml_providers.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of saml_providers run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock SAML providers found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountNumber': '123456789012',
                'Region': 'us-east-1',
                'IdpName': 'test-saml-provider',
                'Arn': 'arn:aws:iam::123456789012:saml-provider/test-saml-provider',
                'ParentProfile': 'test-profile'
            }
        ]
        
        saml_providers.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for SAML providers", output)

    def test_find_all_saml_providers_empty_credentials(self):
        """Test find_all_saml_providers with empty credentials list"""
        result = saml_providers.find_all_saml_providers([])
        self.assertEqual(result, [])


class TestTgwsOperation(unittest.TestCase):
    """Test cases for the Transit Gateways operation"""

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
        self.mock_args.ResourceTypes = ['all']
        self.mock_args.DrawNetworkDiagram = False

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(tgws, 'add_operation_args'))
        self.assertTrue(callable(tgws.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(tgws, 'run'))
        self.assertTrue(callable(tgws.run))

    def test_find_all_tgws_function_exists(self):
        """Test that find_all_tgws function exists"""
        self.assertTrue(hasattr(tgws, 'find_all_tgws'))
        self.assertTrue(callable(tgws.find_all_tgws))

    def test_find_all_vpcs_function_exists(self):
        """Test that find_all_vpcs function exists"""
        self.assertTrue(hasattr(tgws, 'find_all_vpcs'))
        self.assertTrue(callable(tgws.find_all_vpcs))

    @patch('inv_scr.operations.tgws.get_all_credentials')
    @patch('inv_scr.operations.tgws.find_all_tgws')
    @patch('inv_scr.operations.tgws.find_all_vpcs')
    @patch('inv_scr.operations.tgws.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find_vpcs, mock_find_tgws, mock_creds):
        """Test basic execution of tgws run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock TGWs and VPCs found
        mock_find_tgws.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'TransitGatewayId': 'tgw-12345678',
                'TGWName': 'test-tgw',
                'ParentProfile': 'test-profile'
            }
        ]
        
        mock_find_vpcs.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'VpcId': 'vpc-12345678',
                'VpcName': 'test-vpc',
                'ParentProfile': 'test-profile'
            }
        ]
        
        tgws.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find_tgws.assert_called_once()
        mock_find_vpcs.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for Transit Gateways", output)

    def test_find_all_tgws_empty_credentials(self):
        """Test find_all_tgws with empty credentials list"""
        result = tgws.find_all_tgws([])
        self.assertEqual(result, [])

    def test_find_all_vpcs_empty_credentials(self):
        """Test find_all_vpcs with empty credentials list"""
        result = tgws.find_all_vpcs([])
        self.assertEqual(result, [])


class TestTopicsOperation(unittest.TestCase):
    """Test cases for the SNS Topics operation"""

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
        self.mock_args.pFragments = None
        self.mock_args.pExact = False

    def test_add_operation_args_function_exists(self):
        """Test that add_operation_args function exists"""
        self.assertTrue(hasattr(topics, 'add_operation_args'))
        self.assertTrue(callable(topics.add_operation_args))

    def test_run_function_exists(self):
        """Test that run function exists"""
        self.assertTrue(hasattr(topics, 'run'))
        self.assertTrue(callable(topics.run))

    def test_find_all_topics_function_exists(self):
        """Test that find_all_topics function exists"""
        self.assertTrue(hasattr(topics, 'find_all_topics'))
        self.assertTrue(callable(topics.find_all_topics))

    @patch('inv_scr.operations.topics.get_all_credentials')
    @patch('inv_scr.operations.topics.find_all_topics')
    @patch('inv_scr.operations.topics.display_results')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_basic_execution(self, mock_stdout, mock_display, mock_find, mock_creds):
        """Test basic execution of topics run function"""
        # Mock credentials
        mock_creds.return_value = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', 'MgmtAccount': '123456789012'}
        ]
        
        # Mock topics found
        mock_find.return_value = [
            {
                'MgmtAccount': '123456789012',
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'TopicName': 'test-topic',
                'TopicArn': 'arn:aws:sns:us-east-1:123456789012:test-topic',
                'ParentProfile': 'test-profile'
            }
        ]
        
        topics.run(self.mock_args)
        
        # Verify that the functions were called
        mock_creds.assert_called_once()
        mock_find.assert_called_once()
        mock_display.assert_called_once()
        
        # Check output contains expected text
        output = mock_stdout.getvalue()
        self.assertIn("Searching for SNS topics", output)

    def test_find_all_topics_empty_credentials(self):
        """Test find_all_topics with empty credentials list"""
        result = topics.find_all_topics([])
        self.assertEqual(result, [])
