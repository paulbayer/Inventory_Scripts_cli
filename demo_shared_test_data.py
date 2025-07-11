#!/usr/bin/env python3
"""
Demonstration of the new shared test data system

This script shows how to use the centralized test data for consistent,
maintainable testing across all operations.
"""

from tests.shared_test_data import (
    SharedTestAccounts, 
    SharedTestRegions, 
    SharedCredentialBuilder,
    TestScenarios,
    ResponseBuilder
)

def demo_accounts_and_regions():
    """Demonstrate centralized account and region management"""
    print("🏢 Shared Test Accounts")
    print("=" * 25)
    
    # Access predefined accounts
    print(f"Master Account: {SharedTestAccounts.MASTER_ACCOUNT}")
    print(f"Dev Account: {SharedTestAccounts.DEV_ACCOUNT}")
    print(f"Staging Account: {SharedTestAccounts.STAGING_ACCOUNT}")
    
    # Get account collections
    org_accounts = SharedTestAccounts.get_org_accounts()
    print(f"\nOrganizational Accounts ({len(org_accounts)}):")
    for account in org_accounts:
        print(f"  - {account}")
    
    print(f"\n🌍 Shared Test Regions")
    print("=" * 23)
    
    # Access predefined regions
    print(f"Primary Region: {SharedTestRegions.US_EAST_1}")
    print(f"Secondary Region: {SharedTestRegions.US_WEST_2}")
    
    # Get region collections
    primary_regions = SharedTestRegions.get_primary_regions()
    print(f"\nPrimary Regions ({len(primary_regions)}):")
    for region in primary_regions:
        print(f"  - {region}")

def demo_credential_building():
    """Demonstrate credential building patterns"""
    print(f"\n🔑 Credential Building Patterns")
    print("=" * 32)
    
    # Single account, single region
    simple_creds = SharedCredentialBuilder.single_account_single_region()
    print(f"Simple Credentials: {len(simple_creds)} credential(s)")
    print(f"  Account: {simple_creds[0]['AccountId']}")
    print(f"  Region: {simple_creds[0]['Region']}")
    
    # Multi-account, single region
    multi_account_creds = SharedCredentialBuilder.multi_account_single_region()
    print(f"\nMulti-Account Credentials: {len(multi_account_creds)} credential(s)")
    accounts = set(c['AccountId'] for c in multi_account_creds)
    print(f"  Accounts: {', '.join(accounts)}")
    print(f"  Region: {multi_account_creds[0]['Region']}")
    
    # Single account, multi-region
    multi_region_creds = SharedCredentialBuilder.single_account_multi_region()
    print(f"\nMulti-Region Credentials: {len(multi_region_creds)} credential(s)")
    regions = set(c['Region'] for c in multi_region_creds)
    print(f"  Account: {multi_region_creds[0]['AccountId']}")
    print(f"  Regions: {', '.join(regions)}")
    
    # Complex organizational structure
    complex_creds = SharedCredentialBuilder.complex_org_structure()
    print(f"\nComplex Org Credentials: {len(complex_creds)} credential(s)")
    accounts = set(c['AccountId'] for c in complex_creds)
    regions = set(c['Region'] for c in complex_creds)
    print(f"  Accounts: {len(accounts)} unique")
    print(f"  Regions: {len(regions)} unique")
    print(f"  Total combinations: {len(accounts)} × {len(regions)} = {len(complex_creds)}")

def demo_test_scenarios():
    """Demonstrate pre-built test scenarios"""
    print(f"\n🎭 Pre-Built Test Scenarios")
    print("=" * 28)
    
    scenarios = ['simple', 'multi_account', 'multi_region', 'enterprise']
    
    for scenario_name in scenarios:
        scenario = TestScenarios.get_scenario_by_name(scenario_name)
        print(f"\n{scenario_name.upper()} Scenario:")
        print(f"  Description: {scenario['description']}")
        print(f"  Credentials: {len(scenario['credentials'])}")
        
        if 'accounts' in scenario:
            print(f"  Accounts: {len(scenario['accounts'])}")
        if 'regions' in scenario:
            print(f"  Regions: {len(scenario['regions'])}")

def demo_response_building():
    """Demonstrate AWS response building"""
    print(f"\n🔧 AWS Response Building")
    print("=" * 25)
    
    # EC2 responses for different scenarios
    print("EC2 Instance Responses:")
    for scenario in ['simple', 'multi_account']:
        try:
            response = ResponseBuilder.build_ec2_response(scenario, instances_per_account=2)
            instances = response['Reservations'][0]['Instances']
            print(f"  {scenario}: {len(instances)} instances")
            
            # Show realistic naming
            for instance in instances[:2]:  # Show first 2
                name_tag = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
                print(f"    - {instance['InstanceId']}: {name_tag}")
        except ValueError as e:
            print(f"  {scenario}: {e}")
    
    # VPC responses
    print(f"\nVPC Responses:")
    for scenario in ['simple', 'multi_account']:
        try:
            response = ResponseBuilder.build_vpc_response(scenario, vpcs_per_account=1)
            vpcs = response['Vpcs']
            print(f"  {scenario}: {len(vpcs)} VPCs")
            
            # Show realistic naming
            for vpc in vpcs[:2]:  # Show first 2
                name_tag = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
                print(f"    - {vpc['VpcId']}: {name_tag} ({vpc['CidrBlock']})")
        except ValueError as e:
            print(f"  {scenario}: {e}")

def demo_backward_compatibility():
    """Demonstrate backward compatibility with existing tests"""
    print(f"\n🔄 Backward Compatibility")
    print("=" * 26)
    
    # Import the updated mock fixtures
    from tests.mock_fixtures import MockCredentialFixtures, MockAWSResponseFixtures
    
    # Show that old methods still work
    print("Legacy Methods Still Work:")
    
    old_simple = MockCredentialFixtures.single_account_single_region()
    print(f"  single_account_single_region(): {len(old_simple)} credential(s)")
    
    old_multi = MockCredentialFixtures.multi_account_single_region()
    print(f"  multi_account_single_region(): {len(old_multi)} credential(s)")
    
    # Show new scenario-based methods
    print(f"\nNew Scenario-Based Methods:")
    
    new_simple = MockCredentialFixtures.get_scenario_credentials('simple')
    print(f"  get_scenario_credentials('simple'): {len(new_simple)} credential(s)")
    
    # Show enhanced response building
    print(f"\nEnhanced Response Building:")
    
    old_response = MockAWSResponseFixtures.ec2_instances_response(num_instances=2)
    print(f"  ec2_instances_response(): {len(old_response['Reservations'][0]['Instances'])} instances")
    
    new_response = MockAWSResponseFixtures.ec2_instances_response(num_instances=2, scenario='simple')
    print(f"  ec2_instances_response(scenario='simple'): {len(new_response['Reservations'][0]['Instances'])} instances")

def demo_test_migration_example():
    """Show how to migrate existing tests to use shared data"""
    print(f"\n📝 Test Migration Example")
    print("=" * 27)
    
    print("BEFORE (Duplicated Test Data):")
    print("""
    def test_multi_account_scenario(self):
        # Duplicated credential creation
        mock_credentials = [
            {'AccountId': '123456789012', 'Region': 'us-east-1', ...},
            {'AccountId': '234567890123', 'Region': 'us-east-1', ...},
            {'AccountId': '345678901234', 'Region': 'us-east-1', ...}
        ]
        
        # Duplicated response creation
        mock_response = {
            'Reservations': [{'Instances': [...]}]
        }
    """)
    
    print("AFTER (Shared Test Data):")
    print("""
    def test_multi_account_scenario(self):
        # Use shared scenario
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('multi_account')
        
        # Use scenario-based response
        mock_response = MockAWSResponseFixtures.ec2_instances_response(
            num_instances=2, scenario='multi_account'
        )
    """)
    
    print("Benefits:")
    print("  ✅ No duplication - single source of truth")
    print("  ✅ Consistent data across all tests")
    print("  ✅ Realistic account/region names")
    print("  ✅ Easy to modify globally")
    print("  ✅ Better maintainability")

def main():
    """Run all demonstrations"""
    print("🚀 Shared Test Data System Demonstration")
    print("=" * 45)
    
    demo_accounts_and_regions()
    demo_credential_building()
    demo_test_scenarios()
    demo_response_building()
    demo_backward_compatibility()
    demo_test_migration_example()
    
    print(f"\n🎉 Summary")
    print("=" * 10)
    print("The shared test data system provides:")
    print("  • Centralized account and region definitions")
    print("  • Consistent credential building patterns")
    print("  • Pre-built scenarios for common use cases")
    print("  • Realistic AWS response generation")
    print("  • Backward compatibility with existing tests")
    print("  • Easy migration path for existing test suites")
    
    print(f"\n📚 Next Steps:")
    print("  1. Migrate existing tests to use shared scenarios")
    print("  2. Add new operations using the shared system")
    print("  3. Extend scenarios for specific use cases")
    print("  4. Enjoy more maintainable and consistent tests! 🚀")

if __name__ == "__main__":
    main()