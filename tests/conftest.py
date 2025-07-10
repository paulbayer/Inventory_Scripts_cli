#!/usr/bin/env python3
"""
Test configuration and fixtures for AWS Inventory CLI tests
"""

import pytest
import sys
import os
from unittest.mock import MagicMock

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def mock_aws_credentials():
    """Fixture providing mock AWS credentials"""
    return {
        'AccessKeyId': 'AKIAIOSFODNN7EXAMPLE',
        'SecretAccessKey': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        'SessionToken': 'token123',
        'AccountId': '123456789012',
        'Region': 'us-east-1',
        'MgmtAccount': '123456789012',
        'ParentProfile': 'test-profile'
    }

@pytest.fixture
def mock_ec2_instances():
    """Fixture providing mock EC2 instances data"""
    return {
        'Reservations': [
            {
                'Instances': [
                    {
                        'InstanceId': 'i-1234567890abcdef0',
                        'InstanceType': 't3.micro',
                        'State': {'Name': 'running'},
                        'PublicDnsName': 'ec2-1-2-3-4.compute-1.amazonaws.com',
                        'Tags': [{'Key': 'Name', 'Value': 'test-instance'}]
                    },
                    {
                        'InstanceId': 'i-0987654321fedcba0',
                        'InstanceType': 't3.small',
                        'State': {'Name': 'stopped'},
                        'PublicDnsName': '',
                        'Tags': [{'Key': 'Name', 'Value': 'stopped-instance'}]
                    }
                ]
            }
        ]
    }

@pytest.fixture
def mock_vpcs():
    """Fixture providing mock VPC data"""
    return {
        'Vpcs': [
            {
                'VpcId': 'vpc-12345678',
                'IsDefault': False,
                'CidrBlockAssociationSet': [
                    {'CidrBlock': '10.0.0.0/16'}
                ],
                'Tags': [{'Key': 'Name', 'Value': 'test-vpc'}]
            },
            {
                'VpcId': 'vpc-87654321',
                'IsDefault': True,
                'CidrBlockAssociationSet': [
                    {'CidrBlock': '172.31.0.0/16'}
                ],
                'Tags': []
            }
        ]
    }

@pytest.fixture
def mock_args():
    """Fixture providing mock command line arguments"""
    args = MagicMock()
    args.Profiles = ['test-profile']
    args.Regions = ['us-east-1']
    args.Accounts = None
    args.SkipAccounts = None
    args.SkipProfiles = None
    args.AccessRoles = None
    args.RootOnly = False
    args.Filename = None
    args.Time = False
    args.loglevel = 50  # CRITICAL
    return args