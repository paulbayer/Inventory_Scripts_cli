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

from inv_scr.operations import instances, vpcs, cfnstacks, cfnstacksets, ebs_volumes, elbs, functions, orgs, rds_instances


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
            {'DBId': 'db-2', 'Name': 'test2'},
            {'DBId': 'db-1', 'Name': 'test1'},  # duplicate
            {'DBId': 'db-3', 'Name': 'test3'}
        ]
        
        result = rds_instances.uniquify_list(test_list)
        
        self.assertEqual(len(result), 3)
        db_ids = [item['DBId'] for item in result]
        self.assertEqual(set(db_ids), {'db-1', 'db-2', 'db-3'})

        self.assertEqual(set(db_ids), {'db-1', 'db-2', 'db-3'})


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


if __name__ == '__main__':
    unittest.main()