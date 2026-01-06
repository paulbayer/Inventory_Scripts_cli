#!/usr/bin/env python3
"""
Simple test runner for region validation tests
"""

import sys
import unittest

# Add the current directory to the path
sys.path.insert(0, '.')

# Import the test modules
from tests.test_region_validation import TestRegionValidation, TestRegionValidationIntegration
from tests.test_core import TestAccountClass

def run_region_validation_tests():
    """Run all region validation tests"""
    print("🧪 Running Region Validation Tests...")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add region validation tests
    suite.addTest(unittest.makeSuite(TestRegionValidation))
    suite.addTest(unittest.makeSuite(TestRegionValidationIntegration))
    
    # Add relevant core tests
    suite.addTest(TestAccountClass('test_validate_region_function_exists'))
    suite.addTest(TestAccountClass('test_validate_region_none_region_defaults_to_us_east_1'))
    suite.addTest(TestAccountClass('test_validate_region_us_east_1_returns_success_immediately'))
    suite.addTest(TestAccountClass('test_validate_region_valid_region_success'))
    suite.addTest(TestAccountClass('test_validate_region_valid_but_not_opted_in'))
    suite.addTest(TestAccountClass('test_validate_region_invalid_region'))
    suite.addTest(TestAccountClass('test_validate_region_api_exception'))
    suite.addTest(TestAccountClass('test_validate_region_uses_session_region_when_none_provided'))
    suite.addTest(TestAccountClass('test_aws_acct_access_region_validation_success'))
    suite.addTest(TestAccountClass('test_aws_acct_access_region_validation_failure'))
    suite.addTest(TestAccountClass('test_aws_acct_access_region_validation_not_opted_in'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"🎯 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if result.wasSuccessful():
        print(f"\n✅ All region validation tests passed!")
        return True
    else:
        print(f"\n❌ Some tests failed!")
        return False

if __name__ == '__main__':
    success = run_region_validation_tests()
    sys.exit(0 if success else 1)