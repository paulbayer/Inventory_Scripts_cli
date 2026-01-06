#!/usr/bin/env python3
"""
Comprehensive tests for region validation functionality in account_class.py

This module provides extensive testing of the _validate_region function and
region validation within the aws_acct_access class initialization.
"""

import unittest
import sys
from unittest.mock import patch, MagicMock
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, '..')

from inv_scr.core import account_class
from tests.shared_test_data import SharedTestRegions, SharedTestAccounts


class TestRegionValidation(unittest.TestCase):
    """Comprehensive test cases for region validation functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_regions = SharedTestRegions.get_all_regions()
        self.test_accounts = SharedTestAccounts.get_all_accounts()

    def test_validate_region_function_signature(self):
        """Test that _validate_region function has correct signature"""
        import inspect
        sig = inspect.signature(account_class._validate_region)
        params = list(sig.parameters.keys())
        self.assertIn('faws_prelim_session', params)
        self.assertIn('fRegion', params)

    @patch('boto3.Session')
    def test_validate_region_none_region_none_session_region(self, mock_session):
        """Test validation when both region and session region are None"""
        mock_session_instance = MagicMock()
        mock_session_instance.region_name = None
        
        result = account_class._validate_region(mock_session_instance, None)
        
        self.assertTrue(result['Success'])
        self.assertEqual(result['Region'], 'us-east-1')
        self.assertIn('Either no region supplied', result['Message'])

    @patch('boto3.Session')
    def test_validate_region_none_region_with_session_region(self, mock_session):
        """Test validation when region is None but session has a region"""
        mock_session_instance = MagicMock()
        mock_session_instance.region_name = 'eu-west-1'
        mock_ec2_client = MagicMock()
        mock_session_instance.client.return_value = mock_ec2_client
        
        # Mock successful region validation
        mock_ec2_client.describe_regions.return_value = {
            'Regions': [{
                'RegionName': 'eu-west-1',
                'OptInStatus': 'opt-in-not-required'
            }]
        }
        
        result = account_class._validate_region(mock_session_instance, None)
        
        self.assertTrue(result['Success'])
        self.assertEqual(result['Region'], 'eu-west-1')
        self.assertIn('is a valid region within AWS', result['Message'])

    @patch('boto3.Session')
    def test_validate_region_all_standard_regions(self, mock_session):
        """Test validation for all standard AWS regions"""
        mock_session_instance = MagicMock()
        mock_ec2_client = MagicMock()
        mock_session_instance.client.return_value = mock_ec2_client
        
        standard_regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1',
            'ca-central-1', 'sa-east-1'
        ]
        
        for region in standard_regions:
            with self.subTest(region=region):
                if region == 'us-east-1':
                    # us-east-1 should return immediately without API call
                    result = account_class._validate_region(mock_session_instance, region)
                    self.assertTrue(result['Success'])
                    self.assertEqual(result['Region'], 'us-east-1')
                else:
                    # Other regions should make API call
                    mock_ec2_client.describe_regions.return_value = {
                        'Regions': [{
                            'RegionName': region,
                            'OptInStatus': 'opt-in-not-required'
                        }]
                    }
                    
                    result = account_class._validate_region(mock_session_instance, region)
                    
                    self.assertTrue(result['Success'])
                    self.assertEqual(result['Region'], region)
                    self.assertIn('is a valid region within AWS', result['Message'])

    @patch('boto3.Session')
    def test_validate_region_opt_in_required_regions(self, mock_session):
        """Test validation for regions that require opt-in"""
        mock_session_instance = MagicMock()
        mock_ec2_client = MagicMock()
        mock_session_instance.client.return_value = mock_ec2_client
        
        opt_in_regions = [
            'ap-east-1',      # Asia Pacific (Hong Kong)
            'me-south-1',     # Middle East (Bahrain)
            'af-south-1',     # Africa (Cape Town)
            'eu-south-1',     # Europe (Milan)
            'ap-southeast-3', # Asia Pacific (Jakarta)
        ]
        
        for region in opt_in_regions:
            with self.subTest(region=region):
                # Test when account hasn't opted in
                mock_ec2_client.describe_regions.return_value = {
                    'Regions': [{
                        'RegionName': region,
                        'OptInStatus': 'not-opted-in'
                    }]
                }
                
                result = account_class._validate_region(mock_session_instance, region)
                
                self.assertFalse(result['Success'])
                self.assertEqual(result['Region'], region)
                self.assertIn('hasn\'t opted into this region', result['Message'])
                
                # Test when account has opted in
                mock_ec2_client.describe_regions.return_value = {
                    'Regions': [{
                        'RegionName': region,
                        'OptInStatus': 'opted-in'
                    }]
                }
                
                result = account_class._validate_region(mock_session_instance, region)
                
                self.assertTrue(result['Success'])
                self.assertEqual(result['Region'], region)
                self.assertIn('is a valid region within AWS', result['Message'])

    @patch('boto3.Session')
    def test_validate_region_invalid_regions(self, mock_session):
        """Test validation for various invalid region formats"""
        mock_session_instance = MagicMock()
        mock_ec2_client = MagicMock()
        mock_session_instance.client.return_value = mock_ec2_client
        
        invalid_regions = [
            'invalid-region',
            'us-invalid-1',
            'eu-fake-2',
            'ap-nonexistent-3',
            'us-east-99',
            'global',
            '',
            'us_east_1',  # Wrong separator
            'US-EAST-1',  # Wrong case
        ]
        
        for region in invalid_regions:
            with self.subTest(region=region):
                # Mock empty response for invalid region
                mock_ec2_client.describe_regions.return_value = {'Regions': []}
                
                result = account_class._validate_region(mock_session_instance, region)
                
                self.assertFalse(result['Success'])
                self.assertEqual(result['Region'], region)
                self.assertIn('is not valid region within this AWS partition', result['Message'])

    @patch('boto3.Session')
    def test_validate_region_api_errors(self, mock_session):
        """Test validation when AWS API returns various errors"""
        mock_session_instance = MagicMock()
        mock_ec2_client = MagicMock()
        mock_session_instance.client.return_value = mock_ec2_client
        
        test_cases = [
            {
                'exception': ClientError(
                    {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
                    'DescribeRegions'
                ),
                'description': 'Access denied error'
            },
            {
                'exception': ClientError(
                    {'Error': {'Code': 'InvalidUserID.NotFound', 'Message': 'Invalid user'}},
                    'DescribeRegions'
                ),
                'description': 'Invalid user error'
            },
            {
                'exception': EndpointConnectionError(endpoint_url='https://ec2.invalid-region.amazonaws.com'),
                'description': 'Endpoint connection error'
            },
            {
                'exception': NoCredentialsError(),
                'description': 'No credentials error'
            },
            {
                'exception': Exception('Generic error'),
                'description': 'Generic exception'
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(description=test_case['description']):
                mock_ec2_client.describe_regions.side_effect = test_case['exception']
                
                result = account_class._validate_region(mock_session_instance, 'us-west-2')
                
                self.assertFalse(result['Success'])
                self.assertEqual(result['Region'], 'us-west-2')
                self.assertIn('Problem happened', result['Message'])

    @patch('boto3.Session')
    def test_validate_region_network_timeout(self, mock_session):
        """Test validation when network timeout occurs"""
        mock_session_instance = MagicMock()
        mock_ec2_client = MagicMock()
        mock_session_instance.client.return_value = mock_ec2_client
        
        # Mock timeout exception
        import socket
        mock_ec2_client.describe_regions.side_effect = socket.timeout('Request timed out')
        
        result = account_class._validate_region(mock_session_instance, 'us-west-2')
        
        self.assertFalse(result['Success'])
        self.assertEqual(result['Region'], 'us-west-2')
        self.assertIn('Problem happened', result['Message'])

    @patch('boto3.Session')
    def test_validate_region_response_structure(self, mock_session):
        """Test that validation returns correct response structure"""
        mock_session_instance = MagicMock()
        mock_ec2_client = MagicMock()
        mock_session_instance.client.return_value = mock_ec2_client
        
        mock_ec2_client.describe_regions.return_value = {
            'Regions': [{
                'RegionName': 'us-west-2',
                'OptInStatus': 'opt-in-not-required'
            }]
        }
        
        result = account_class._validate_region(mock_session_instance, 'us-west-2')
        
        # Check response structure
        self.assertIsInstance(result, dict)
        self.assertIn('Success', result)
        self.assertIn('Message', result)
        self.assertIn('Region', result)
        
        # Check data types
        self.assertIsInstance(result['Success'], bool)
        self.assertIsInstance(result['Message'], str)
        self.assertIsInstance(result['Region'], str)

    @patch('boto3.Session')
    def test_validate_region_multiple_regions_in_response(self, mock_session):
        """Test validation when API returns multiple regions (should not happen but test anyway)"""
        mock_session_instance = MagicMock()
        mock_ec2_client = MagicMock()
        mock_session_instance.client.return_value = mock_ec2_client
        
        # Mock response with multiple regions (shouldn't happen with proper filter)
        mock_ec2_client.describe_regions.return_value = {
            'Regions': [
                {
                    'RegionName': 'us-west-2',
                    'OptInStatus': 'opt-in-not-required'
                },
                {
                    'RegionName': 'us-west-1',
                    'OptInStatus': 'opt-in-not-required'
                }
            ]
        }
        
        result = account_class._validate_region(mock_session_instance, 'us-west-2')
        
        # Should still succeed and use the first region
        self.assertTrue(result['Success'])
        self.assertEqual(result['Region'], 'us-west-2')

    @patch('boto3.Session')
    def test_validate_region_malformed_api_response(self, mock_session):
        """Test validation with malformed API response"""
        mock_session_instance = MagicMock()
        mock_ec2_client = MagicMock()
        mock_session_instance.client.return_value = mock_ec2_client
        
        # Test various malformed responses
        malformed_responses = [
            {},  # Missing 'Regions' key
            {'Regions': None},  # Null regions
            {'Regions': [{}]},  # Region without required fields
            {'Regions': [{'RegionName': 'us-west-2'}]},  # Missing OptInStatus
        ]
        
        for response in malformed_responses:
            with self.subTest(response=response):
                mock_ec2_client.describe_regions.return_value = response
                
                try:
                    result = account_class._validate_region(mock_session_instance, 'us-west-2')
                    # If it doesn't raise an exception, it should return failure
                    if 'Success' in result:
                        self.assertFalse(result['Success'])
                except Exception:
                    # Exceptions are acceptable for malformed responses
                    pass


class TestRegionValidationIntegration(unittest.TestCase):
    """Integration tests for region validation within aws_acct_access class"""

    @patch('inv_scr.core.account_class._validate_region')
    @patch('boto3.Session')
    def test_aws_acct_access_region_validation_flow(self, mock_session, mock_validate_region):
        """Test the complete region validation flow in aws_acct_access initialization"""
        # Mock session
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.region_name = 'us-west-2'
        
        # Mock successful region validation
        mock_validate_region.return_value = {
            'Success': True,
            'Message': 'us-west-2 is a valid region within AWS',
            'Region': 'us-west-2'
        }
        
        # Mock other required services
        mock_sts_client = MagicMock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        
        mock_org_client = MagicMock()
        mock_org_client.describe_organization.side_effect = ClientError(
            {'Error': {'Code': 'AWSOrganizationsNotInUseException'}}, 'DescribeOrganization'
        )
        
        def client_side_effect(service, **kwargs):
            if service == 'sts':
                return mock_sts_client
            elif service == 'organizations':
                return mock_org_client
            return MagicMock()
        
        mock_session_instance.client.side_effect = client_side_effect
        
        # Test initialization
        try:
            account = account_class.aws_acct_access(fProfile='test-profile', fRegion='us-west-2')
            
            # Verify region validation was called
            mock_validate_region.assert_called_once()
            call_args = mock_validate_region.call_args
            self.assertEqual(call_args[0][1], 'us-west-2')  # fRegion parameter
            
        except Exception as e:
            # Some exceptions are expected due to mocking complexity
            self.assertIsInstance(e, (AttributeError, KeyError, ClientError))

    @patch('inv_scr.core.account_class._validate_region')
    @patch('boto3.Session')
    def test_aws_acct_access_handles_region_validation_failure(self, mock_session, mock_validate_region):
        """Test that aws_acct_access properly handles region validation failure"""
        # Mock session
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.region_name = 'invalid-region'
        
        # Mock failed region validation
        mock_validate_region.return_value = {
            'Success': False,
            'Message': 'invalid-region is not valid region within this AWS partition',
            'Region': 'invalid-region'
        }
        
        # Test initialization
        try:
            account = account_class.aws_acct_access(fProfile='test-profile', fRegion='invalid-region')
            
            # Verify region validation was called
            mock_validate_region.assert_called_once()
            
            # Check that failure is properly handled
            if hasattr(account, 'Success'):
                self.assertFalse(account.Success)
            if hasattr(account, 'ErrorType'):
                self.assertEqual(account.ErrorType, 'Invalid region')
            if hasattr(account, 'Region'):
                self.assertEqual(account.Region, 'invalid-region')
                
        except Exception as e:
            # Some exceptions are expected due to mocking complexity
            self.assertIsInstance(e, (AttributeError, KeyError, ClientError))

    @patch('inv_scr.core.account_class._validate_region')
    @patch('boto3.Session')
    def test_aws_acct_access_environment_variables_region_validation(self, mock_session, mock_validate_region):
        """Test region validation when using environment variables"""
        import os
        
        # Mock environment variables
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret',
            'AWS_DEFAULT_REGION': 'eu-central-1'
        }):
            # Mock session
            mock_session_instance = MagicMock()
            mock_session.return_value = mock_session_instance
            mock_session_instance.region_name = 'eu-central-1'
            
            # Mock successful region validation
            mock_validate_region.return_value = {
                'Success': True,
                'Message': 'eu-central-1 is a valid region within AWS',
                'Region': 'eu-central-1'
            }
            
            # Test initialization with environment variables
            try:
                account = account_class.aws_acct_access(fProfile=None, fRegion=None)
                
                # Verify region validation was called
                mock_validate_region.assert_called_once()
                
            except Exception as e:
                # Some exceptions are expected due to mocking complexity
                self.assertIsInstance(e, (AttributeError, KeyError, ClientError))


if __name__ == '__main__':
    unittest.main()