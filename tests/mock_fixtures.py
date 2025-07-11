#!/usr/bin/env python3
"""
Mock fixtures for testing AWS operations with realistic credential and response data
"""

from unittest.mock import MagicMock
from typing import List, Dict, Any


class MockCredentialFixtures:
    """Provides realistic mock credentials for testing operations"""
    
    @staticmethod
    def single_account_single_region() -> List[Dict[str, Any]]:
        """Simple single account, single region credential"""
        return [
            {
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'MgmtAccount': '123456789012',
                'ParentProfile': 'test-profile',
                'AccessKeyId': 'AKIAIOSFODNN7EXAMPLE',
                'SecretAccessKey': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
                'SessionToken': 'example-session-token'
            }
        ]
    
    @staticmethod
    def multi_account_single_region() -> List[Dict[str, Any]]:
        """Multiple accounts in single region"""
        return [
            {
                'AccountId': '123456789012',
                'Region': 'us-east-1',
                'MgmtAccount': '123456789012',
                'ParentProfile': 'org-profile',
                'AccessKeyId': 'AKIAIOSFODNN7EXAMPLE',
                'SecretAccessKey': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
                'SessionToken': 'example-session-token-1'
            },
            {
                'AccountId': '234567890123',
                'Region': 'us-east-1',
                'MgmtAccount': '123456789012',
                'ParentProfile': 'org-profile',
                'AccessKeyId': 'AKIAI44QH8DHBEXAMPLE',
                'SecretAccessKey': 'je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY',
                'SessionToken': 'example-session-token-2'
            },
            {
                'AccountId': '345678901234',
                'Region': 'us-east-1',
                'MgmtAccount': '123456789012',
                'ParentProfile': 'org-profile',
                'AccessKeyId': 'AKIAIGCEVSQ6C2EXAMPLE',
                'SecretAccessKey': 'vLBHBhq5pTI2O9AGQkkYk4G+T9rajfEXAMPLEKEY',
                'SessionToken': 'example-session-token-3'
            }
        ]
    
    @staticmethod
    def single_account_multi_region() -> List[Dict[str, Any]]:
        """Single account across multiple regions"""
        regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        credentials = []
        
        for region in regions:
            credentials.append({
                'AccountId': '123456789012',
                'Region': region,
                'MgmtAccount': '123456789012',
                'ParentProfile': 'multi-region-profile',
                'AccessKeyId': 'AKIAIOSFODNN7EXAMPLE',
                'SecretAccessKey': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
                'SessionToken': f'example-session-token-{region}'
            })
        
        return credentials
    
    @staticmethod
    def complex_org_structure() -> List[Dict[str, Any]]:
        """Complex organizational structure with multiple accounts and regions"""
        accounts = ['123456789012', '234567890123', '345678901234', '456789012345']
        regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        credentials = []
        
        for account in accounts:
            for region in regions:
                credentials.append({
                    'AccountId': account,
                    'Region': region,
                    'MgmtAccount': '123456789012',
                    'ParentProfile': 'complex-org-profile',
                    'AccessKeyId': f'AKIA{account[-8:]}EXAMPLE',
                    'SecretAccessKey': f'{account}ExampleSecretKey{region}',
                    'SessionToken': f'session-token-{account}-{region}'
                })
        
        return credentials


class MockAWSResponseFixtures:
    """Provides realistic mock AWS API responses for testing"""
    
    @staticmethod
    def ec2_instances_response(num_instances: int = 2, include_tags: bool = True) -> Dict[str, Any]:
        """Mock EC2 describe_instances response"""
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
    def vpc_response(num_vpcs: int = 2, include_tags: bool = True) -> Dict[str, Any]:
        """Mock EC2 describe_vpcs response"""
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
    def lambda_functions_response(num_functions: int = 2) -> Dict[str, Any]:
        """Mock Lambda list_functions response"""
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
        
        return {'Functions': functions}
    
    @staticmethod
    def rds_instances_response(num_instances: int = 2) -> Dict[str, Any]:
        """Mock RDS describe_db_instances response"""
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
                'InstanceCreateTime': '2023-01-01T12:00:00.000Z',
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
            'pShortform': False,
            'pAccountList': None,
            'pStackId': False,
            'pInstanceCount': False
        }
        
        # Apply defaults and override with provided kwargs
        for key, value in {**defaults, **kwargs}.items():
            setattr(mock_args, key, value)
        
        return mock_args