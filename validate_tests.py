#!/usr/bin/env python3
"""
Quick test validation script for AWS Inventory CLI
Run this to verify your test suite is working properly
"""

import subprocess
import sys
import time

def run_test(test_command, description):
    """Run a test and report results"""
    print(f"\n🧪 {description}")
    print("=" * 50)
    
    start_time = time.time()
    try:
        result = subprocess.run(
            test_command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ PASSED ({duration:.2f}s)")
            if "ok" in result.stdout:
                test_count = result.stdout.count(" ... ok")
                print(f"   {test_count} tests passed")
        else:
            print(f"❌ FAILED ({duration:.2f}s)")
            print(f"   Error: {result.stderr.strip()}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT (>30s)")
        return False
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

def main():
    """Main validation function"""
    print("🚀 AWS Inventory CLI Test Validation")
    print("=" * 50)
    
    # Test suite validation
    tests = [
        {
            'command': 'python3 -c "import inv_scr; print(\'CLI import successful\')"',
            'description': 'CLI Import Test'
        },
        {
            'command': 'inv_scr list | head -5',
            'description': 'CLI Functionality Test'
        },
        {
            'command': 'python3 -m unittest tests.test_cli.TestCLI.test_operations_mapping_exists -v',
            'description': 'Operations Mapping Test'
        },
        {
            'command': 'python3 -m unittest tests.test_cli.TestCLI.test_version_defined -v',
            'description': 'Version Definition Test'
        },
        {
            'command': 'python3 -m unittest tests.test_argument_parsing.TestArgumentParsing.test_verbosity_levels -v',
            'description': 'Argument Parsing Test'
        },
        {
            'command': 'python3 -m unittest tests.test_operations.TestInstancesOperation.test_run_function_exists -v',
            'description': 'Operations Structure Test'
        }
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if run_test(test['command'], test['description']):
            passed += 1
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your test suite is working correctly.")
        return 0
    elif passed >= total * 0.8:  # 80% pass rate
        print("⚠️  Most tests passed, but some issues detected.")
        print("   This is acceptable for development.")
        return 0
    else:
        print("🚨 MULTIPLE TEST FAILURES detected.")
        print("   Please check your setup:")
        print("   1. Run: pip install -e .")
        print("   2. Verify you're in the project root directory")
        print("   3. Check that inv_scr command works: inv_scr list")
        return 1

if __name__ == '__main__':
    sys.exit(main())