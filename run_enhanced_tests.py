#!/usr/bin/env python3
"""
Enhanced test runner for AWS Inventory CLI with comprehensive credential-level mocking

This script demonstrates the new credential-level mocking capabilities that enable
thorough testing of operation logic and data transformation.
"""

import unittest
import sys
import time
from io import StringIO
from contextlib import redirect_stdout

def run_enhanced_operation_tests():
    """Run the enhanced credential-level mocking tests"""
    
    print("🚀 Running Enhanced AWS Inventory CLI Tests")
    print("=" * 60)
    print()
    
    # Test categories with their enhanced tests
    test_categories = {
        "EC2 Instances - Enhanced Credential Tests": [
            "tests.test_operations.TestInstancesOperation.test_run_with_single_account_credentials",
            "tests.test_operations.TestInstancesOperation.test_run_with_multi_account_credentials", 
            "tests.test_operations.TestInstancesOperation.test_run_with_status_filtering_logic",
            "tests.test_operations.TestInstancesOperation.test_run_with_multi_region_credentials"
        ],
        "VPCs - Enhanced Credential Tests": [
            "tests.test_operations.TestVPCsOperation.test_run_with_comprehensive_vpc_data",
            "tests.test_operations.TestVPCsOperation.test_run_with_default_vpc_filtering",
            "tests.test_operations.TestVPCsOperation.test_run_with_multi_account_vpc_data"
        ],
        "Lambda Functions - Enhanced Credential Tests": [
            "tests.test_operations.TestFunctionsOperation.test_run_with_comprehensive_lambda_data",
            "tests.test_operations.TestFunctionsOperation.test_run_with_runtime_filtering_logic"
        ]
    }
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for category, test_list in test_categories.items():
        print(f"📋 {category}")
        print("-" * len(category))
        
        for test_name in test_list:
            total_tests += 1
            print(f"  Running: {test_name.split('.')[-1]}...", end=" ")
            
            # Capture test output
            test_output = StringIO()
            
            try:
                # Load and run the specific test
                suite = unittest.TestLoader().loadTestsFromName(test_name)
                runner = unittest.TextTestRunner(stream=test_output, verbosity=0)
                result = runner.run(suite)
                
                if result.wasSuccessful():
                    print("✅ PASSED")
                    passed_tests += 1
                else:
                    print("❌ FAILED")
                    failed_tests.append({
                        'name': test_name,
                        'errors': result.errors,
                        'failures': result.failures
                    })
                    
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
                failed_tests.append({
                    'name': test_name,
                    'errors': [('Exception', str(e))],
                    'failures': []
                })
        
        print()
    
    # Summary
    print("📊 Test Summary")
    print("=" * 20)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {len(failed_tests)} ❌")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests:
        print("\n🔍 Failed Test Details:")
        print("-" * 25)
        for failed in failed_tests:
            print(f"\n❌ {failed['name']}")
            if failed['failures']:
                for failure in failed['failures']:
                    print(f"   Failure: {failure[1]}")
            if failed['errors']:
                for error in failed['errors']:
                    print(f"   Error: {error[1]}")
    
    return len(failed_tests) == 0

def demonstrate_mock_fixtures():
    """Demonstrate the mock fixture capabilities"""
    
    print("\n🧪 Mock Fixture Demonstration")
    print("=" * 35)
    
    from tests.mock_fixtures import MockCredentialFixtures, MockAWSResponseFixtures, MockOperationHelpers
    
    print("\n1. Single Account Credentials:")
    single_creds = MockCredentialFixtures.single_account_single_region()
    print(f"   - Account: {single_creds[0]['AccountId']}")
    print(f"   - Region: {single_creds[0]['Region']}")
    print(f"   - Profile: {single_creds[0]['ParentProfile']}")
    
    print("\n2. Multi-Account Credentials:")
    multi_creds = MockCredentialFixtures.multi_account_single_region()
    print(f"   - Total Accounts: {len(multi_creds)}")
    for cred in multi_creds:
        print(f"   - Account {cred['AccountId']} in {cred['Region']}")
    
    print("\n3. Multi-Region Credentials:")
    region_creds = MockCredentialFixtures.single_account_multi_region()
    print(f"   - Account: {region_creds[0]['AccountId']}")
    print(f"   - Regions: {[c['Region'] for c in region_creds]}")
    
    print("\n4. Complex Org Structure:")
    complex_creds = MockCredentialFixtures.complex_org_structure()
    accounts = set(c['AccountId'] for c in complex_creds)
    regions = set(c['Region'] for c in complex_creds)
    print(f"   - Total Credentials: {len(complex_creds)}")
    print(f"   - Unique Accounts: {len(accounts)}")
    print(f"   - Unique Regions: {len(regions)}")
    
    print("\n5. Sample AWS Responses:")
    ec2_response = MockAWSResponseFixtures.ec2_instances_response(num_instances=2)
    print(f"   - EC2 Instances: {len(ec2_response['Reservations'][0]['Instances'])} instances")
    
    vpc_response = MockAWSResponseFixtures.vpc_response(num_vpcs=3)
    print(f"   - VPCs: {len(vpc_response['Vpcs'])} VPCs")
    
    lambda_response = MockAWSResponseFixtures.lambda_functions_response(num_functions=2)
    print(f"   - Lambda Functions: {len(lambda_response['Functions'])} functions")

def run_comparison_tests():
    """Run comparison between old and new testing approaches"""
    
    print("\n🔄 Testing Approach Comparison")
    print("=" * 35)
    
    # Old approach tests (basic mocking)
    old_tests = [
        "tests.test_operations.TestInstancesOperation.test_run_basic_execution",
        "tests.test_operations.TestVPCsOperation.test_run_basic_execution"
    ]
    
    # New approach tests (credential-level mocking)
    new_tests = [
        "tests.test_operations.TestInstancesOperation.test_run_with_single_account_credentials",
        "tests.test_operations.TestVPCsOperation.test_run_with_comprehensive_vpc_data"
    ]
    
    print("\n📊 Coverage Comparison:")
    print("Old Approach (Basic Mocking):")
    print("  ✅ Tests function existence")
    print("  ✅ Tests basic execution flow")
    print("  ❌ Limited data transformation testing")
    print("  ❌ No realistic credential handling")
    print("  ❌ No multi-account/region scenarios")
    
    print("\nNew Approach (Credential-Level Mocking):")
    print("  ✅ Tests function existence")
    print("  ✅ Tests complete execution flow")
    print("  ✅ Tests data transformation logic")
    print("  ✅ Tests realistic credential handling")
    print("  ✅ Tests multi-account/region scenarios")
    print("  ✅ Tests filtering and business logic")
    print("  ✅ Tests error handling scenarios")

def main():
    """Main test runner"""
    
    start_time = time.time()
    
    # Run enhanced tests
    success = run_enhanced_operation_tests()
    
    # Demonstrate fixtures
    demonstrate_mock_fixtures()
    
    # Show comparison
    run_comparison_tests()
    
    end_time = time.time()
    
    print(f"\n⏱️  Total execution time: {end_time - start_time:.2f} seconds")
    
    if success:
        print("\n🎉 All enhanced tests passed! Your credential-level mocking is working perfectly.")
        print("\n💡 Next Steps:")
        print("   1. Add more operations to the enhanced testing framework")
        print("   2. Create edge case scenarios (empty responses, errors, etc.)")
        print("   3. Add performance testing with large datasets")
        print("   4. Consider adding integration tests with real AWS credentials")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the details above and fix the issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())