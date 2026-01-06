#!/usr/bin/env python3
"""
Simple test runner for RAM shares operation tests
"""

import sys
import unittest
from io import StringIO

def run_ram_shares_tests():
    """Run RAM shares tests and capture output"""
    
    # Capture test output
    test_output = StringIO()
    
    # Create test suite
    loader = unittest.TestLoader()
    
    try:
        # Import the test class
        from tests.test_operations import TestRamSharesOperation
        
        # Load tests from the class
        suite = loader.loadTestsFromTestCase(TestRamSharesOperation)
        
        # Run tests
        runner = unittest.TextTestRunner(stream=test_output, verbosity=2)
        result = runner.run(suite)
        
        # Get output
        output = test_output.getvalue()
        
        print("=== RAM Shares Test Results ===")
        print(output)
        print(f"\nTests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.failures:
            print("\n=== FAILURES ===")
            for test, traceback in result.failures:
                print(f"FAIL: {test}")
                print(traceback)
        
        if result.errors:
            print("\n=== ERRORS ===")
            for test, traceback in result.errors:
                print(f"ERROR: {test}")
                print(traceback)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = run_ram_shares_tests()
    sys.exit(0 if success else 1)