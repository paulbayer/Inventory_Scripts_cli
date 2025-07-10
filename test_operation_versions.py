#!/usr/bin/env python3
"""
Test script to verify all operations have proper versioning
"""

import subprocess
import sys

def test_operation_version(operation):
    """Test that an operation has version information"""
    try:
        result = subprocess.run([
            'inv_scr', operation, '--operation-version'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and 'operation version' in result.stdout:
            print(f"✅ {operation:<15} - Version: {result.stdout.strip().split()[-1]}")
            return True
        else:
            print(f"❌ {operation:<15} - No version info")
            return False
    except Exception as e:
        print(f"💥 {operation:<15} - Error: {e}")
        return False

def main():
    """Test all operations for version information"""
    print("🔍 Testing Operation Versioning")
    print("=" * 50)
    
    # Define operations list directly
    operations = [
        'cfnstacks', 'cfnstacksets', 'directories', 'ebs-volumes', 'ecs-clusters',
        'elbs', 'enis', 'functions', 'gas', 'gd-detectors', 'instances',
        'orgs', 'phzs', 'policies', 'rds-instances', 'roles', 'saml-providers',
        'subnets', 'tgws', 'topics', 'vpcs'
    ]
    
    print(f"Testing {len(operations)} operations...")
    print()
    
    passed = 0
    total = len(operations)
    
    for operation in sorted(operations):
        if test_operation_version(operation):
            passed += 1
    
    print()
    print("📊 SUMMARY")
    print("=" * 50)
    print(f"Operations with versioning: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL OPERATIONS HAVE VERSIONING!")
        return 0
    else:
        print("⚠️  Some operations missing versioning")
        return 1

if __name__ == '__main__':
    sys.exit(main())