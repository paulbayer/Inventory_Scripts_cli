#!/usr/bin/env python3
"""
Shared test data for AWS Inventory CLI enhanced testing

This module provides centralized, reusable test data for all operations,
eliminating duplication and ensuring consistency across test suites.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestAccount:
    """Represents a test AWS account"""
    account_id: str
    name: str
    is_org_master: bool = False
    
    def __str__(self):
        return f"{self.name} ({self.account_id})"


@dataclass
class TestRegion:
    """Represents a test AWS region"""
    code: str
    name: str
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class SharedTestAccounts:
    """Centralized test account definitions"""
    
    # Standard test accounts
    MASTER_ACCOUNT = TestAccount("123456789012", "master-account", is_org_master=True)
    DEV_ACCOUNT = TestAccount("234567890123", "dev-account")
    STAGING_ACCOUNT = TestAccount("345678901234", "staging-account")
    PROD_ACCOUNT = TestAccount("456789012345", "prod-account")
    
    # Additional accounts for complex scenarios
    SECURITY_ACCOUNT = TestAccount("567890123456", "security-account")
    LOGGING_ACCOUNT = TestAccount("678901234567", "logging-account")
    
    @classmethod
    def get_org_accounts(cls) -> List[TestAccount]:
        """Get typical organizational accounts"""
        return [cls.MASTER_ACCOUNT, cls.DEV_ACCOUNT, cls.STAGING_ACCOUNT, cls.PROD_ACCOUNT]
    
    @classmethod
    def get_all_accounts(cls) -> List[TestAccount]:
        """Get all available test accounts"""
        return [
            cls.MASTER_ACCOUNT, cls.DEV_ACCOUNT, cls.STAGING_ACCOUNT, 
            cls.PROD_ACCOUNT, cls.SECURITY_ACCOUNT, cls.LOGGING_ACCOUNT
        ]
    
    @classmethod
    def get_account_by_id(cls, account_id: str) -> Optional[TestAccount]:
        """Get account by ID"""
        for account in cls.get_all_accounts():
            if account.account_id == account_id:
                return account
        return None


class SharedTestRegions:
    """Centralized test region definitions"""
    
    # Primary regions
    US_EAST_1 = TestRegion("us-east-1", "US East (N. Virginia)")
    US_WEST_2 = TestRegion("us-west-2", "US West (Oregon)")
    EU_WEST_1 = TestRegion("eu-west-1", "Europe (Ireland)")
    
    # Additional regions for complex scenarios
    AP_SOUTHEAST_1 = TestRegion("ap-southeast-1", "Asia Pacific (Singapore)")
    CA_CENTRAL_1 = TestRegion("ca-central-1", "Canada (Central)")
    
    @classmethod
    def get_primary_regions(cls) -> List[TestRegion]:
        """Get primary test regions"""
        return [cls.US_EAST_1, cls.US_WEST_2, cls.EU_WEST_1]
    
    @classmethod
    def get_all_regions(cls) -> List[TestRegion]:
        """Get all available test regions"""
        return [
            cls.US_EAST_1, cls.US_WEST_2, cls.EU_WEST_1,
            cls.AP_SOUTHEAST_1, cls.CA_CENTRAL_1
        ]
    
    @classmethod
    def get_region_by_code(cls, region_code: str) -> Optional[TestRegion]:
        """Get region by code"""
        for region in cls.get_all_regions():
            if region.code == region_code:
                return region
        return None


class SharedCredentialBuilder:
    """Builder for creating consistent credential structures"""
    
    @staticmethod
    def build_credential(account: TestAccount, region: TestRegion, 
                        profile: str = "test-profile") -> Dict[str, Any]:
        """Build a single credential dictionary"""
        return {
            'AccountId': account.account_id,
            'Region': region.code,
            'MgmtAccount': SharedTestAccounts.MASTER_ACCOUNT.account_id,
            'ParentProfile': profile,
            'AccessKeyId': f'AKIA{account.account_id[-8:]}EXAMPLE',
            'SecretAccessKey': f'{account.account_id}ExampleSecretKey{region.code}',
            'SessionToken': f'session-token-{account.account_id}-{region.code}'
        }
    
    @classmethod
    def single_account_single_region(cls, account: TestAccount = None, 
                                   region: TestRegion = None) -> List[Dict[str, Any]]:
        """Single account, single region credentials"""
        account = account or SharedTestAccounts.MASTER_ACCOUNT
        region = region or SharedTestRegions.US_EAST_1
        return [cls.build_credential(account, region)]
    
    @classmethod
    def multi_account_single_region(cls, accounts: List[TestAccount] = None,
                                  region: TestRegion = None) -> List[Dict[str, Any]]:
        """Multiple accounts, single region credentials"""
        accounts = accounts or SharedTestAccounts.get_org_accounts()[:3]  # First 3 accounts
        region = region or SharedTestRegions.US_EAST_1
        return [cls.build_credential(account, region) for account in accounts]
    
    @classmethod
    def single_account_multi_region(cls, account: TestAccount = None,
                                  regions: List[TestRegion] = None) -> List[Dict[str, Any]]:
        """Single account, multiple regions credentials"""
        account = account or SharedTestAccounts.MASTER_ACCOUNT
        regions = regions or SharedTestRegions.get_primary_regions()
        return [cls.build_credential(account, region) for region in regions]
    
    @classmethod
    def complex_org_structure(cls, accounts: List[TestAccount] = None,
                            regions: List[TestRegion] = None) -> List[Dict[str, Any]]:
        """Complex organizational structure credentials"""
        accounts = accounts or SharedTestAccounts.get_org_accounts()
        regions = regions or SharedTestRegions.get_primary_regions()
        credentials = []
        for account in accounts:
            for region in regions:
                credentials.append(cls.build_credential(account, region))
        return credentials


class SharedAWSResponseData:
    """Shared AWS API response data templates"""
    
    @staticmethod
    def get_base_ec2_instance(instance_id: str, account: TestAccount, 
                            region: TestRegion, **kwargs) -> Dict[str, Any]:
        """Get base EC2 instance data"""
        defaults = {
            'InstanceType': 't3.micro',
            'State': {'Name': 'running'},
            'PublicDnsName': f'ec2-{instance_id[-4:]}.{region.code}.compute.amazonaws.com',
            'PrivateDnsName': f'ip-10-0-1-{instance_id[-1]}.ec2.internal',
            'LaunchTime': '2023-01-01T12:00:00.000Z',
            'Placement': {'AvailabilityZone': f'{region.code}a'}
        }
        defaults.update(kwargs)
        
        return {
            'InstanceId': instance_id,
            **defaults,
            'Tags': [
                {'Key': 'Name', 'Value': f'{account.name}-instance-{instance_id[-4:]}'},
                {'Key': 'Environment', 'Value': account.name.split('-')[0]},
                {'Key': 'Account', 'Value': account.name}
            ]
        }
    
    @staticmethod
    def get_base_vpc(vpc_id: str, account: TestAccount, region: TestRegion, 
                    cidr_base: int = 10, **kwargs) -> Dict[str, Any]:
        """Get base VPC data"""
        defaults = {
            'State': 'available',
            'IsDefault': False
        }
        defaults.update(kwargs)
        
        return {
            'VpcId': vpc_id,
            'CidrBlock': f'{cidr_base}.0.0.0/16',
            'CidrBlockAssociationSet': [
                {
                    'CidrBlock': f'{cidr_base}.0.0.0/16',
                    'CidrBlockState': {'State': 'associated'}
                }
            ],
            **defaults,
            'Tags': [
                {'Key': 'Name', 'Value': f'{account.name}-vpc-{vpc_id[-4:]}'},
                {'Key': 'Environment', 'Value': account.name.split('-')[0]},
                {'Key': 'Account', 'Value': account.name}
            ]
        }
    
    @staticmethod
    def get_base_lambda_function(function_name: str, account: TestAccount, 
                               region: TestRegion, **kwargs) -> Dict[str, Any]:
        """Get base Lambda function data"""
        defaults = {
            'Runtime': 'python3.9',
            'Handler': 'lambda_function.lambda_handler',
            'CodeSize': 1024,
            'Description': f'Lambda function for {account.name}',
            'Timeout': 30,
            'MemorySize': 128,
            'LastModified': '2023-01-01T12:00:00.000+0000'
        }
        defaults.update(kwargs)
        
        return {
            'FunctionName': function_name,
            'FunctionArn': f'arn:aws:lambda:{region.code}:{account.account_id}:function:{function_name}',
            'Role': f'arn:aws:iam::{account.account_id}:role/{account.name}-lambda-role',
            **defaults,
            'Environment': {
                'Variables': {
                    'ENV': account.name.split('-')[0],
                    'ACCOUNT': account.name,
                    'REGION': region.code
                }
            }
        }
    
    @staticmethod
    def get_base_cfn_stack(stack_name: str, account: TestAccount, region: TestRegion, **kwargs) -> Dict[str, Any]:
        """Get base CloudFormation stack data"""
        defaults = {
            'StackStatus': 'CREATE_COMPLETE',
            'CreationTime': datetime(2023, 1, 1, 12, 0, 0),
            'Description': f'CloudFormation stack for {account.name}',
            'EnableTerminationProtection': False,
            'DriftInformation': {'StackDriftStatus': 'NOT_CHECKED'}
        }
        defaults.update(kwargs)
        
        return {
            'StackName': stack_name,
            'StackId': f'arn:aws:cloudformation:{region.code}:{account.account_id}:stack/{stack_name}/12345678-1234-1234-1234-123456789012',
            **defaults,
            'Tags': [
                {'Key': 'Environment', 'Value': account.name.split('-')[0]},
                {'Key': 'Account', 'Value': account.name},
                {'Key': 'ManagedBy', 'Value': 'CloudFormation'}
            ]
        }
    
    @staticmethod
    def get_base_rds_instance(db_id: str, account: TestAccount, region: TestRegion, **kwargs) -> Dict[str, Any]:
        """Get base RDS instance data"""
        defaults = {
            'DBInstanceClass': 'db.t3.micro',
            'Engine': 'mysql',
            'DBInstanceStatus': 'available',
            'MasterUsername': 'admin',
            'AllocatedStorage': 20,
            'StorageType': 'gp2',
            'StorageEncrypted': True,
            'MultiAZ': False,
            'PubliclyAccessible': False
        }
        defaults.update(kwargs)
        
        return {
            'DBInstanceIdentifier': db_id,
            'DBName': f'{account.name.replace("-", "")}_db_{db_id[-1]}',
            'LatestRestorableTime': datetime(2023, 1, 2, 12, 0, 0),
            **defaults,
            'VpcSecurityGroups': [
                {
                    'VpcSecurityGroupId': f'sg-{account.account_id[-8:]}example',
                    'Status': 'active'
                }
            ],
            'DBSubnetGroup': {
                'DBSubnetGroupName': f'{account.name}-subnet-group',
                'VpcId': f'vpc-{account.account_id[-8:]}example'
            }
        }
    
    @staticmethod
    def get_base_elb(elb_name: str, account: TestAccount, region: TestRegion, **kwargs) -> Dict[str, Any]:
        """Get base ELB data"""
        defaults = {
            'State': {'Code': 'active'},
            'Type': 'application',
            'Scheme': 'internet-facing',
            'IpAddressType': 'ipv4'
        }
        defaults.update(kwargs)
        
        return {
            'LoadBalancerName': elb_name,
            'DNSName': f'{elb_name}-{account.account_id[-4:]}.{region.code}.elb.amazonaws.com',
            'LoadBalancerArn': f'arn:aws:elasticloadbalancing:{region.code}:{account.account_id}:loadbalancer/app/{elb_name}/1234567890123456',
            **defaults,
            'AvailabilityZones': [
                {'ZoneName': f'{region.code}a'},
                {'ZoneName': f'{region.code}b'}
            ],
            'SecurityGroups': [f'sg-{account.account_id[-8:]}example'],
            'VpcId': f'vpc-{account.account_id[-8:]}example'
        }


class TestScenarios:
    """Pre-built test scenarios for common use cases"""
    
    @staticmethod
    def simple_single_account():
        """Simple single account scenario"""
        return {
            'credentials': SharedCredentialBuilder.single_account_single_region(),
            'account': SharedTestAccounts.MASTER_ACCOUNT,
            'region': SharedTestRegions.US_EAST_1,
            'description': 'Single account in us-east-1'
        }
    
    @staticmethod
    def multi_account_org():
        """Multi-account organization scenario"""
        accounts = SharedTestAccounts.get_org_accounts()[:3]
        return {
            'credentials': SharedCredentialBuilder.multi_account_single_region(accounts),
            'accounts': accounts,
            'region': SharedTestRegions.US_EAST_1,
            'description': 'Three accounts in organizational structure'
        }
    
    @staticmethod
    def multi_region_deployment():
        """Multi-region deployment scenario"""
        regions = SharedTestRegions.get_primary_regions()
        return {
            'credentials': SharedCredentialBuilder.single_account_multi_region(regions=regions),
            'account': SharedTestAccounts.MASTER_ACCOUNT,
            'regions': regions,
            'description': 'Single account across three regions'
        }
    
    @staticmethod
    def complex_enterprise():
        """Complex enterprise scenario"""
        accounts = SharedTestAccounts.get_org_accounts()
        regions = SharedTestRegions.get_primary_regions()
        return {
            'credentials': SharedCredentialBuilder.complex_org_structure(accounts, regions),
            'accounts': accounts,
            'regions': regions,
            'description': 'Full enterprise setup with 4 accounts across 3 regions'
        }
    
    @staticmethod
    def get_scenario_by_name(name: str):
        """Get scenario by name"""
        scenarios = {
            'simple': TestScenarios.simple_single_account(),
            'multi_account': TestScenarios.multi_account_org(),
            'multi_region': TestScenarios.multi_region_deployment(),
            'enterprise': TestScenarios.complex_enterprise()
        }
        return scenarios.get(name)


class ResponseBuilder:
    """Builder for creating AWS API responses using shared data"""
    
    @staticmethod
    def build_cfn_stacks_response(scenario_name: str, stacks_per_account: int = 2) -> List[Dict[str, Any]]:
        """Build CloudFormation stacks response for a scenario"""
        scenario = TestScenarios.get_scenario_by_name(scenario_name)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        stacks = []
        account_counter = 0
        
        if 'accounts' in scenario:
            # Multi-account scenario
            for account in scenario['accounts']:
                for i in range(stacks_per_account):
                    stack_name = f'{account.name}-stack-{i}'
                    stacks.append(SharedAWSResponseData.get_base_cfn_stack(
                        stack_name, account, scenario['region']
                    ))
                account_counter += 1
        else:
            # Single account scenario
            account = scenario['account']
            region = scenario.get('region', SharedTestRegions.US_EAST_1)
            for i in range(stacks_per_account):
                stack_name = f'{account.name}-stack-{i}'
                stacks.append(SharedAWSResponseData.get_base_cfn_stack(
                    stack_name, account, region
                ))
        
        return stacks
    
    @staticmethod
    def build_rds_response(scenario_name: str, instances_per_account: int = 2) -> Dict[str, Any]:
        """Build RDS instances response for a scenario"""
        scenario = TestScenarios.get_scenario_by_name(scenario_name)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        instances = []
        account_counter = 0
        
        if 'accounts' in scenario:
            # Multi-account scenario
            for account in scenario['accounts']:
                for i in range(instances_per_account):
                    db_id = f'{account.name.replace("-", "")}-db-{i}'
                    instances.append(SharedAWSResponseData.get_base_rds_instance(
                        db_id, account, scenario['region']
                    ))
                account_counter += 1
        else:
            # Single account scenario
            account = scenario['account']
            region = scenario.get('region', SharedTestRegions.US_EAST_1)
            for i in range(instances_per_account):
                db_id = f'{account.name.replace("-", "")}-db-{i}'
                instances.append(SharedAWSResponseData.get_base_rds_instance(
                    db_id, account, region
                ))
        
        return {'DBInstances': instances}
    
    @staticmethod
    def build_elb_response(scenario_name: str, elbs_per_account: int = 2) -> List[Dict[str, Any]]:
        """Build ELB response for a scenario"""
        scenario = TestScenarios.get_scenario_by_name(scenario_name)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        elbs = []
        account_counter = 0
        
        if 'accounts' in scenario:
            # Multi-account scenario
            for account in scenario['accounts']:
                for i in range(elbs_per_account):
                    elb_name = f'{account.name}-elb-{i}'
                    elbs.append(SharedAWSResponseData.get_base_elb(
                        elb_name, account, scenario['region']
                    ))
                account_counter += 1
        else:
            # Single account scenario
            account = scenario['account']
            region = scenario.get('region', SharedTestRegions.US_EAST_1)
            for i in range(elbs_per_account):
                elb_name = f'{account.name}-elb-{i}'
                elbs.append(SharedAWSResponseData.get_base_elb(
                    elb_name, account, region
                ))
        
        return elbs
    
    @staticmethod
    def build_ec2_response(scenario_name: str, instances_per_account: int = 2) -> Dict[str, Any]:
        """Build EC2 instances response for a scenario"""
        scenario = TestScenarios.get_scenario_by_name(scenario_name)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        instances = []
        account_counter = 0
        
        # Handle different scenario types
        if 'accounts' in scenario:
            # Multi-account scenario
            for account in scenario['accounts']:
                for i in range(instances_per_account):
                    instance_id = f'i-{str(account_counter).zfill(8)}{str(i).zfill(8)}abcdef{i}'
                    instances.append(SharedAWSResponseData.get_base_ec2_instance(
                        instance_id, account, scenario['region']
                    ))
                account_counter += 1
        else:
            # Single account scenario
            account = scenario['account']
            region = scenario.get('region', SharedTestRegions.US_EAST_1)
            for i in range(instances_per_account):
                instance_id = f'i-{str(i).zfill(17)}abcdef{i}'
                instances.append(SharedAWSResponseData.get_base_ec2_instance(
                    instance_id, account, region
                ))
        
        return {
            'Reservations': [{
                'Instances': instances,
                'ReservationId': 'r-1234567890abcdef0',
                'OwnerId': scenario.get('account', scenario.get('accounts', [SharedTestAccounts.MASTER_ACCOUNT])[0]).account_id
            }]
        }
    
    @staticmethod
    def build_vpc_response(scenario_name: str, vpcs_per_account: int = 2) -> Dict[str, Any]:
        """Build VPC response for a scenario"""
        scenario = TestScenarios.get_scenario_by_name(scenario_name)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        vpcs = []
        account_counter = 0
        
        if 'accounts' in scenario:
            # Multi-account scenario
            for account in scenario['accounts']:
                for i in range(vpcs_per_account):
                    vpc_id = f'vpc-{str(account_counter).zfill(8)}{str(i).zfill(8)}abcdef{i}'
                    vpcs.append(SharedAWSResponseData.get_base_vpc(
                        vpc_id, account, scenario['region'], cidr_base=10+account_counter+i
                    ))
                account_counter += 1
        else:
            # Single account scenario
            account = scenario['account']
            region = scenario.get('region', SharedTestRegions.US_EAST_1)
            for i in range(vpcs_per_account):
                vpc_id = f'vpc-{str(i).zfill(8)}abcdef{i}'
                vpcs.append(SharedAWSResponseData.get_base_vpc(
                    vpc_id, account, region, cidr_base=10+i, IsDefault=(i==0)
                ))
        
        return {'Vpcs': vpcs}
    
    @staticmethod
    def build_lambda_response(scenario_name: str, functions_per_account: int = 2) -> List[Dict[str, Any]]:
        """Build Lambda functions response for a scenario"""
        scenario = TestScenarios.get_scenario_by_name(scenario_name)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        functions = []
        account_counter = 0
        
        if 'accounts' in scenario:
            # Multi-account scenario
            for account in scenario['accounts']:
                for i in range(functions_per_account):
                    function_name = f'{account.name}-function-{i}'
                    functions.append(SharedAWSResponseData.get_base_lambda_function(
                        function_name, account, scenario['region'],
                        Runtime='python3.9' if i % 2 == 0 else 'nodejs18.x'
                    ))
                account_counter += 1
        else:
            # Single account scenario
            account = scenario['account']
            region = scenario.get('region', SharedTestRegions.US_EAST_1)
            for i in range(functions_per_account):
                function_name = f'{account.name}-function-{i}'
                functions.append(SharedAWSResponseData.get_base_lambda_function(
                    function_name, account, region,
                    Runtime='python3.9' if i % 2 == 0 else 'nodejs18.x'
                ))
        
        return functions


# Convenience functions for backward compatibility and easy access
def get_simple_credentials():
    """Get simple single account credentials"""
    return SharedCredentialBuilder.single_account_single_region()

def get_multi_account_credentials():
    """Get multi-account credentials"""
    return SharedCredentialBuilder.multi_account_single_region()

def get_multi_region_credentials():
    """Get multi-region credentials"""
    return SharedCredentialBuilder.single_account_multi_region()

def get_complex_credentials():
    """Get complex organizational credentials"""
    return SharedCredentialBuilder.complex_org_structure()