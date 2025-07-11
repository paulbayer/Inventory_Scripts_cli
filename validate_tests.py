#!/usr/bin/env python3
"""
Quick validation script to ensure the enhanced testing framework is working
"""

import sys
import unittest
from io import StringIO

def validate_mock_fixtures():
    """Validate that mock fixtures are working correctly"""
    print("🔍 Validating Mock Fixtures...")
    
    try:
        from tests.mock_fixtures import MockCredentialFixtures, MockAWSResponseFixtures, MockOperationHelpers
        
        # Test credential fixtures
        single_creds = MockCredentialFixtures.single_account_single_region()
        assert len(single_creds) == 1
        assert single_creds[0]['AccountId'] == '123456789012'
        print("  ✅ Single account credentials fixture working")
        
        multi_creds = MockCredentialFixtures.multi_account_single_region()
        assert len(multi_creds) == 3
        assert len(set(c['AccountId'] for c in multi_creds)) == 3
        print("  ✅ Multi-account credentials fixture working")
        
        region_creds = MockCredentialFixtures.single_account_multi_region()
        assert len(region_creds) == 3
        assert len(set(c['Region'] for c in region_creds)) == 3
        print("  ✅ Multi-region credentials fixture working")
        
        # Test AWS response fixtures
        ec2_response = MockAWSResponseFixtures.ec2_instances_response(num_instances=2)
        assert len(ec2_response['Reservations'][0]['Instances']) == 2
        print("  ✅ EC2 response fixture working")
        
        vpc_response = MockAWSResponseFixtures.vpc_response(num_vpcs=3)
        assert len(vpc_response['Vpcs']) == 3
        print("  ✅ VPC response fixture working")
        
        # Test helper functions
        mock_args = MockOperationHelpers.create_mock_args(pStatus='running')
        assert mock_args.pStatus == 'running'
        assert mock_args.Profiles == ['test-profile']
        print("  ✅ Mock operation helpers working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Mock fixtures validation failed: {e}")
        return False

def validate_enhanced_tests():
    """Validate that enhanced tests can be imported and run"""
    print("\n🧪 Validating Enhanced Tests...")
    
    try:
        # Try to import the test classes
        from tests.test_operations import TestInstancesOperation, TestVPCsOperation, TestFunctionsOperation
        print("  ✅ Enhanced test classes imported successfully")
        
        # Try to run one simple enhanced test
        suite = unittest.TestSuite()
        
        # Add a basic enhanced test
        test_case = TestInstancesOperation('test_run_with_single_account_credentials')
        suite.addTest(test_case)
        
        # Run the test
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=0)
        result = runner.run(suite)
        
        if result.wasSuccessful():
            print("  ✅ Sample enhanced test executed successfully")
            return True
        else:
            print(f"  ❌ Sample enhanced test failed: {result.failures}")
            return False
            
    except Exception as e:
        print(f"  ❌ Enhanced tests validation failed: {e}")
        return False

def validate_test_runner():
    """Validate that the enhanced test runner is working"""
    print("\n🏃 Validating Test Runner...")
    
    try:
        import run_enhanced_tests
        print("  ✅ Enhanced test runner imported successfully")
        
        # Check that main functions exist
        assert hasattr(run_enhanced_tests, 'run_enhanced_operation_tests')
        assert hasattr(run_enhanced_tests, 'demonstrate_mock_fixtures')
        assert hasattr(run_enhanced_tests, 'main')
        print("  ✅ Test runner functions available")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Test runner validation failed: {e}")
        return False

def main():
    """Main validation function"""
    print("🚀 Enhanced Testing Framework Validation")
    print("=" * 45)
    
    validations = [
        validate_mock_fixtures,
        validate_enhanced_tests,
        validate_test_runner
    ]
    
    results = []
    for validation in validations:
        results.append(validation())
    
    print("\n📊 Validation Summary")
    print("=" * 20)
    
    if all(results):
        print("🎉 All validations passed!")
        print("\n✨ Your enhanced testing framework is ready to use!")
        print("\nNext steps:")
        print("  1. Run: python3 run_enhanced_tests.py")
        print("  2. Read: ENHANCED_TESTING_GUIDE.md")
        print("  3. Add more operations to the framework")
        return 0
    else:
        print("❌ Some validations failed!")
        print("\nPlease check the errors above and fix them before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())