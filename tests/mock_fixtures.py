#!/usr/bin/env python3
"""
Mock fixtures for testing AWS operations with realistic credential and response data

This module provides a clean interface to the shared test data system while maintaining
backward compatibility with existing tests.
"""

from unittest.mock import MagicMock
from typing import List, Dict, Any
from datetime import datetime

# Import shared test data components
from tests.shared_test_data import (
    SharedCredentialBuilder, 
    ResponseBuilder, 
    TestScenarios,
    get_simple_credentials,
    get_multi_account_credentials, 
    get_multi_region_credentials,
    get_complex_credentials
)


class MockCredentialFixtures:
    """Provides realistic mock credentials for testing operations"""
    
    @staticmethod
    def single_account_single_region() -> List[Dict[str, Any]]:
        """Simple single account, single region credential"""
        return get_simple_credentials()
    
    @staticmethod
    def multi_account_single_region() -> List[Dict[str, Any]]:
        """Multiple accounts in single region"""
        return get_multi_account_credentials()
    
    @staticmethod
    def single_account_multi_region() -> List[Dict[str, Any]]:
        """Single account across multiple regions"""
        return get_multi_region_credentials()
    
    @staticmethod
    def complex_org_structure() -> List[Dict[str, Any]]:
        """Complex organizational structure with multiple accounts and regions"""
        return get_complex_credentials()
    
    # New methods using shared test data system
    @staticmethod
    def get_scenario_credentials(scenario_name: str) -> List[Dict[str, Any]]:
        """Get credentials for a named scenario"""
        scenario = TestScenarios.get_scenario_by_name(scenario_name)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        return scenario['credentials']


class MockAWSResponseFixtures:
    """Provides realistic mock AWS API responses for testing"""
    
    @staticmethod
    def ec2_instances_response(num_instances: int = 2, include_tags: bool = True, 
                             scenario: str = 'simple') -> Dict[str, Any]:
        """Mock EC2 describe_instances response"""
        # Use shared test data system for more realistic responses
        try:
            return ResponseBuilder.build_ec2_response(scenario, num_instances)
        except ValueError:
            # Fallback to legacy behavior for backward compatibility
            instances = []
            
            for i in range(num_instances):
                instance = {
                    'InstanceId': f'i-{str(i).zfill(17)}abcdef{i}',
                    'InstanceType': 't3.micro' if i % 2 == 0 else 't3.small',
                    'State': {'Name': 'running' if i % 3 != 2 else 'stopped'},
                    'PublicDnsName': f'ec2-{i}-{i}-{i}-{i}.compute-1.amazonaws.com' if i % 2 == 0 else '',
                    'PrivateDnsName': f'ip-10-0-{i}-{i}.ec2.internal',
                    'LaunchTime': '2023-01-01T12:00:00.000Z',
                    'Placement': {'AvailabilityZone': 'us-east-1a'}
                }
                
                if include_tags:
                    instance['Tags'] = [
                        {'Key': 'Name', 'Value': f'test-instance-{i}'},
                        {'Key': 'Environment', 'Value': 'test'},
                        {'Key': 'Owner', 'Value': 'test-team'}
                    ]
                
                instances.append(instance)
            
            return {
                'Reservations': [
                    {
                        'Instances': instances,
                        'ReservationId': 'r-1234567890abcdef0',
                        'OwnerId': '123456789012'
                    }
                ]
            }
    
    @staticmethod
    def vpc_response(num_vpcs: int = 2, include_tags: bool = True, 
                    scenario: str = 'simple') -> Dict[str, Any]:
        """Mock EC2 describe_vpcs response"""
        # Use shared test data system for more realistic responses
        try:
            return ResponseBuilder.build_vpc_response(scenario, num_vpcs)
        except ValueError:
            # Fallback to legacy behavior for backward compatibility
            vpcs = []
            
            for i in range(num_vpcs):
                vpc = {
                    'VpcId': f'vpc-{str(i).zfill(8)}abcdef{i}',
                    'State': 'available',
                    'CidrBlock': f'10.{i}.0.0/16',
                    'IsDefault': i == 0,
                    'CidrBlockAssociationSet': [
                        {
                            'CidrBlock': f'10.{i}.0.0/16',
                            'CidrBlockState': {'State': 'associated'}
                        }
                    ]
                }
                
                if include_tags:
                    vpc['Tags'] = [
                        {'Key': 'Name', 'Value': f'test-vpc-{i}'},
                        {'Key': 'Environment', 'Value': 'test'}
                    ]
                
                vpcs.append(vpc)
            
            return {'Vpcs': vpcs}
    
    @staticmethod
    def lambda_functions_response(num_functions: int = 2, scenario: str = 'simple') -> List[Dict[str, Any]]:
        """Mock Lambda list_functions response - returns list directly"""
        # Use shared test data system for more realistic responses
        try:
            return ResponseBuilder.build_lambda_response(scenario, num_functions)
        except ValueError:
            # Fallback to legacy behavior for backward compatibility
            functions = []
            
            for i in range(num_functions):
                functions.append({
                    'FunctionName': f'test-function-{i}',
                    'FunctionArn': f'arn:aws:lambda:us-east-1:123456789012:function:test-function-{i}',
                    'Runtime': 'python3.9' if i % 2 == 0 else 'nodejs18.x',
                    'Role': f'arn:aws:iam::123456789012:role/test-lambda-role-{i}',
                    'Handler': 'index.handler',
                    'CodeSize': 1024 * (i + 1),
                    'Description': f'Test Lambda function {i}',
                    'Timeout': 30,
                    'MemorySize': 128,
                    'LastModified': '2023-01-01T12:00:00.000+0000',
                    'Environment': {
                        'Variables': {
                            'ENV': 'test',
                            'FUNCTION_ID': str(i)
                        }
                    }
                })
            
            return functions
    
    @staticmethod
    def cfn_stacks_response(num_stacks: int = 2, scenario: str = 'simple') -> List[Dict[str, Any]]:
        """Mock CloudFormation stacks response - returns list directly"""
        # Use shared test data system for more realistic responses
        try:
            return ResponseBuilder.build_cfn_stacks_response(scenario, num_stacks)
        except ValueError:
            # Fallback to legacy behavior for backward compatibility
            stacks = []
            
            for i in range(num_stacks):
                stacks.append({
                    'StackName': f'test-stack-{i}',
                    'StackId': f'arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack-{i}/12345678-1234-1234-1234-123456789012',
                    'StackStatus': 'CREATE_COMPLETE' if i % 2 == 0 else 'UPDATE_COMPLETE',
                    'CreationTime': datetime(2023, 1, 1, 12, 0, 0),
                    'Description': f'Test CloudFormation stack {i}',
                    'Tags': [
                        {'Key': 'Environment', 'Value': 'test'},
                        {'Key': 'Owner', 'Value': 'test-team'}
                    ]
                })
            
            return stacks
    
    @staticmethod
    def rds_instances_response(num_instances: int = 2, scenario: str = 'simple') -> Dict[str, Any]:
        """Mock RDS instances response"""
        # Use shared test data system for more realistic responses
        try:
            return ResponseBuilder.build_rds_response(scenario, num_instances)
        except ValueError:
            # Fallback to legacy behavior for backward compatibility
            instances = []
            
            for i in range(num_instances):
                instances.append({
                    'DBInstanceIdentifier': f'test-db-{i}',
                    'DBInstanceClass': 'db.t3.micro',
                    'Engine': 'mysql' if i % 2 == 0 else 'postgres',
                    'DBInstanceStatus': 'available',
                    'MasterUsername': 'admin',
                    'DBName': f'testdb{i}',
                    'AllocatedStorage': 20,
                    'LatestRestorableTime': datetime(2023, 1, 2, 12, 0, 0),
                    'VpcSecurityGroups': [
                        {
                            'VpcSecurityGroupId': f'sg-{str(i).zfill(8)}example',
                            'Status': 'active'
                        }
                    ],
                    'DBSubnetGroup': {
                        'DBSubnetGroupName': f'test-subnet-group-{i}',
                        'VpcId': f'vpc-{str(i).zfill(8)}example'
                    },
                    'MultiAZ': False,
                    'PubliclyAccessible': False,
                    'StorageType': 'gp2',
                    'StorageEncrypted': True
                })
            
            return {'DBInstances': instances}
    
    @staticmethod
    def elb_response(num_elbs: int = 2, scenario: str = 'simple') -> List[Dict[str, Any]]:
        """Mock ELB response - returns list directly"""
        # Use shared test data system for more realistic responses
        try:
            return ResponseBuilder.build_elb_response(scenario, num_elbs)
        except ValueError:
            # Fallback to legacy behavior for backward compatibility
            elbs = []
            
            for i in range(num_elbs):
                elbs.append({
                    'LoadBalancerName': f'test-elb-{i}',
                    'DNSName': f'test-elb-{i}-123456789.us-east-1.elb.amazonaws.com',
                    'State': {'Code': 'active'},
                    'Type': 'application',
                    'Scheme': 'internet-facing'
                })
            
            return elbs

    # Legacy methods for backward compatibility
    @staticmethod
    def cloudformation_stacks_response(num_stacks: int = 2) -> Dict[str, Any]:
        """Mock CloudFormation describe_stacks response"""
        stacks = []
        
        for i in range(num_stacks):
            stacks.append({
                'StackName': f'test-stack-{i}',
                'StackId': f'arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack-{i}/12345678-1234-1234-1234-123456789012',
                'StackStatus': 'CREATE_COMPLETE' if i % 2 == 0 else 'UPDATE_COMPLETE',
                'CreationTime': '2023-01-01T12:00:00.000Z',
                'LastUpdatedTime': '2023-01-02T12:00:00.000Z',
                'Description': f'Test CloudFormation stack {i}',
                'Tags': [
                    {'Key': 'Environment', 'Value': 'test'},
                    {'Key': 'Owner', 'Value': 'test-team'}
                ]
            })
        
        return {'Stacks': stacks}
    
    @staticmethod
    def rds_instances_response(num_instances: int = 2, scenario: str = 'simple') -> Dict[str, Any]:
        """Mock RDS describe_db_instances response (supports scenarios)"""
        # Reuse shared test data builder; fall back to legacy structure for backward compatibility.
        try:
            return ResponseBuilder.build_rds_response(scenario, num_instances)
        except ValueError:
            instances = []
            
            for i in range(num_instances):
                instances.append({
                    'DBInstanceIdentifier': f'test-db-{i}',
                    'DBInstanceClass': 'db.t3.micro',
                    'Engine': 'mysql' if i % 2 == 0 else 'postgres',
                    'DBInstanceStatus': 'available',
                    'MasterUsername': 'admin',
                    'DBName': f'testdb{i}',
                    'AllocatedStorage': 20,
                    'LatestRestorableTime': datetime(2023, 1, 2, 12, 0, 0),
                    'VpcSecurityGroups': [
                        {
                            'VpcSecurityGroupId': f'sg-{str(i).zfill(8)}example',
                            'Status': 'active'
                        }
                    ],
                    'DBSubnetGroup': {
                        'DBSubnetGroupName': f'test-subnet-group-{i}',
                        'VpcId': f'vpc-{str(i).zfill(8)}example'
                    },
                    'MultiAZ': False,
                    'PubliclyAccessible': False,
                    'StorageType': 'gp2',
                    'StorageEncrypted': True
                })
            
            return {'DBInstances': instances}


class MockOperationHelpers:
    """Helper methods for setting up operation mocks"""
    
    @staticmethod
    def setup_get_all_credentials_mock(mock_get_creds, credential_fixture):
        """Setup mock for get_all_credentials function"""
        mock_get_creds.return_value = credential_fixture
    
    @staticmethod
    def setup_aws_api_mock(mock_api_call, response_fixture):
        """Setup mock for AWS API calls"""
        mock_api_call.return_value = response_fixture
    
    @staticmethod
    def create_mock_args(**kwargs):
        """Create a mock arguments object with default values"""
        mock_args = MagicMock()
        
        # Default values
        defaults = {
            'Profiles': ['test-profile'],
            'Regions': ['us-east-1'],
            'Accounts': None,
            'SkipAccounts': None,
            'SkipProfiles': None,
            'AccessRoles': None,
            'RootOnly': False,
            'Filename': None,
            'Time': False,
            'loglevel': 50,  # CRITICAL
            'pStatus': None,
            'pFragments': ['all'],
            'pExact': False,
            'pDefault': False,
            'pRuntime': None,
            'pNewRuntime': None,
            'Fix': False,
            'Force': False,
            'pShortform': False,
            'pAccountList': None,
            'pStackId': False,
            'pInstanceCount': False
        }
        
        # Apply defaults and override with provided kwargs
        for key, value in {**defaults, **kwargs}.items():
            setattr(mock_args, key, value)
        
        return mock_args
