#!/usr/bin/env python3
"""
Test script to validate the RAM shares test fix
"""

import sys
import traceback

def test_import():
    """Test if we can import the test class without errors"""
    try:
        from tests.test_operations import TestRamSharesOperation
        print("✅ Successfully imported TestRamSharesOperation")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        return False

def test_method_exists():
    """Test if the test_add_operation_args method exists"""
    try:
        from tests.test_operations import TestRamSharesOperation
        test_instance = TestRamSharesOperation()
        
        if hasattr(test_instance, 'test_add_operation_args'):
            print("✅ test_add_operation_args method exists")
            return True
        else:
            print("❌ test_add_operation_args method not found")
            return False
    except Exception as e:
        print(f"❌ Error checking method: {e}")
        return False

def test_ram_shares_import():
    """Test if we can import ram_shares module"""
    try:
        from inv_scr.operations import ram_shares
        print("✅ Successfully imported ram_shares module")
        
        if hasattr(ram_shares, 'add_operation_args'):
            print("✅ ram_shares.add_operation_args exists")
        else:
            print("❌ ram_shares.add_operation_args not found")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error importing ram_shares: {e}")
        return False

def main():
    """Run all validation tests"""
    print("=== RAM Shares Test Fix Validation ===\n")
    
    tests = [
        ("Import Test", test_import),
        ("Method Exists Test", test_method_exists), 
        ("RAM Shares Module Test", test_ram_shares_import)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        result = test_func()
        results.append(result)
        print()
    
    if all(results):
        print("🎉 All validation tests passed! The import fix was successful.")
        return True
    else:
        print("❌ Some validation tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)