#!/usr/bin/env python3
"""
Migration Status Analysis: Functions to Operations

This script analyzes which functional scripts have been migrated to operations
versus those that still need to be migrated.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

def get_functions_list() -> List[str]:
    """Get list of all functional scripts"""
    functions_dir = Path("inv_scr/functions")
    if not functions_dir.exists():
        return []
    
    functions = []
    for file in functions_dir.glob("*.py"):
        if file.name != "__init__.py":
            functions.append(file.name)
    
    return sorted(functions)

def get_operations_list() -> List[str]:
    """Get list of all operation modules"""
    operations_dir = Path("inv_scr/operations")
    if not operations_dir.exists():
        return []
    
    operations = []
    for file in operations_dir.glob("*.py"):
        if file.name != "__init__.py":
            operations.append(file.name)
    
    return sorted(operations)

def get_cli_operations() -> Dict[str, str]:
    """Get operations registered in CLI"""
    cli_file = Path("inv_scr/cli.py")
    if not cli_file.exists():
        return {}
    
    operations = {}
    with open(cli_file, 'r') as f:
        content = f.read()
        
        # Find the OPERATIONS dictionary
        operations_match = re.search(r'OPERATIONS\s*=\s*{([^}]+)}', content, re.DOTALL)
        if operations_match:
            operations_content = operations_match.group(1)
            
            # Extract operation mappings
            for line in operations_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and ':' in line:
                    # Extract 'operation-name': module.run pattern
                    match = re.match(r"'([^']+)':\s*([^,]+)", line)
                    if match:
                        cli_name = match.group(1)
                        module_ref = match.group(2).strip()
                        operations[cli_name] = module_ref
    
    return operations

def analyze_function_to_operation_mapping() -> Dict[str, Dict]:
    """Analyze mapping between functions and operations"""
    
    # Mapping patterns for function names to operation names
    function_to_operation_patterns = {
        # Direct mappings
        'all_my_instances.py': 'instances.py',
        'all_my_vpcs.py': 'vpcs.py', 
        'all_my_vpcs2.py': 'vpcs.py',  # Alternative VPC script
        'all_my_cfnstacks.py': 'cfnstacks.py',
        'all_my_cfnstacksets.py': 'cfnstacksets.py',
        'all_my_directories.py': 'directories.py',
        'all_my_ebs_volumes.py': 'ebs_volumes.py',
        'all_my_ecs_clusters_and_tasks.py': 'ecs_clusters.py',
        'all_my_elbs.py': 'elbs.py',
        'all_my_enis.py': 'enis.py',
        'all_my_functions.py': 'functions.py',
        'all_my_gas.py': 'gas.py',
        'all_my_gd-detectors.py': 'gd_detectors.py',
        'all_my_orgs.py': 'orgs.py',
        'all_my_phzs.py': 'phzs.py',
        'all_my_policies.py': 'policies.py',
        'all_my_rds_instances.py': 'rds_instances.py',
        'all_my_roles.py': 'roles.py',
        'all_my_saml_providers.py': 'saml_providers.py',
        'all_my_subnets.py': 'subnets.py',
        'all_my_tgws.py': 'tgws.py',
        'all_my_topics.py': 'topics.py',
    }
    
    functions = get_functions_list()
    operations = get_operations_list()
    cli_operations = get_cli_operations()
    
    analysis = {
        'migrated': [],
        'not_migrated': [],
        'utility_scripts': [],
        'operations_without_functions': [],
        'cli_registered': list(cli_operations.keys())
    }
    
    # Check each function
    for func in functions:
        if func in function_to_operation_patterns:
            expected_operation = function_to_operation_patterns[func]
            if expected_operation in operations:
                analysis['migrated'].append({
                    'function': func,
                    'operation': expected_operation,
                    'cli_name': get_cli_name_for_operation(expected_operation, cli_operations)
                })
            else:
                analysis['not_migrated'].append({
                    'function': func,
                    'expected_operation': expected_operation,
                    'reason': 'Operation file missing'
                })
        else:
            # Check if it's a utility/special purpose script
            if is_utility_script(func):
                analysis['utility_scripts'].append(func)
            else:
                analysis['not_migrated'].append({
                    'function': func,
                    'expected_operation': 'Unknown',
                    'reason': 'No clear operation mapping'
                })
    
    # Check for operations without corresponding functions
    migrated_operations = {item['operation'] for item in analysis['migrated']}
    for op in operations:
        if op not in migrated_operations:
            analysis['operations_without_functions'].append(op)
    
    return analysis

def get_cli_name_for_operation(operation_file: str, cli_operations: Dict[str, str]) -> str:
    """Get CLI name for an operation file"""
    operation_module = operation_file.replace('.py', '')
    for cli_name, module_ref in cli_operations.items():
        if operation_module in module_ref:
            return cli_name
    return 'Not registered'

def is_utility_script(filename: str) -> bool:
    """Determine if a script is a utility/special purpose script"""
    utility_patterns = [
        'ALZ_CheckAccount.py',
        'CT_CheckAccount.py',
        'DrawOrg.py',
        'RunOnMultiAccounts.py',
        'SC_Products_to_CFN_Stacks.py',
        'SumUpFlowLogs.py',
        'Update_AWS_Actions.py',
        'UpdateRoleToMemberAccounts.py',
        'UpdateStackSetFromAnother.py',
        'azs_across_accounts.py',
        'check_all_cloudtrail.py',
        'delete_bucket_objects.py',
        'enable_drift_detection.py',
        'enable_drift_detection_stacksets.py',
        'find_my_LZ_versions.py',
        'find_orphaned_stacks.py',
        'find_security_groups.py',
        'last_stackset_operations.py',
        'lock_down_stack_sets_role.py',
        'mod_my_cfnstacksets.py',
        'move_stack_instances.py',
        'my_org_users.py',
        'my_ssm_parameters.py',
        'network_diagram.py',
        'put_s3_public_block.py',
        'read_stackset_results.py',
        'recover_stack_ids.py',
        'test_function.py',
        'update_retention_on_all_my_cw_groups.py',
        'verify_security_groups.py',
        'all_my_config_recorders_and_delivery_channels.py'  # Specialized config script
    ]
    
    return filename in utility_patterns

def print_analysis():
    """Print comprehensive migration analysis"""
    analysis = analyze_function_to_operation_mapping()
    
    print("🔄 AWS Inventory CLI - Migration Status Analysis")
    print("=" * 55)
    
    # Summary statistics
    total_functions = len(get_functions_list())
    migrated_count = len(analysis['migrated'])
    not_migrated_count = len(analysis['not_migrated'])
    utility_count = len(analysis['utility_scripts'])
    
    print(f"\n📊 Summary Statistics")
    print("=" * 22)
    print(f"Total Functions: {total_functions}")
    print(f"Migrated to Operations: {migrated_count} ✅")
    print(f"Not Yet Migrated: {not_migrated_count} ⚠️")
    print(f"Utility Scripts: {utility_count} 🔧")
    print(f"Migration Progress: {(migrated_count/(total_functions-utility_count))*100:.1f}%")
    
    # Migrated functions
    print(f"\n✅ Successfully Migrated ({migrated_count})")
    print("=" * 30)
    for item in analysis['migrated']:
        cli_status = "✅ Registered" if item['cli_name'] != 'Not registered' else "❌ Not registered"
        print(f"  {item['function']:<35} → {item['operation']:<20} → CLI: {item['cli_name']:<15} {cli_status}")
    
    # Not migrated functions
    if analysis['not_migrated']:
        print(f"\n⚠️  Not Yet Migrated ({not_migrated_count})")
        print("=" * 25)
        for item in analysis['not_migrated']:
            print(f"  {item['function']:<35} → {item['expected_operation']:<20} ({item['reason']})")
    
    # Utility scripts
    if analysis['utility_scripts']:
        print(f"\n🔧 Utility Scripts ({utility_count})")
        print("=" * 20)
        print("These are specialized scripts that may not need migration:")
        for script in analysis['utility_scripts']:
            print(f"  {script}")
    
    # Operations without functions
    if analysis['operations_without_functions']:
        print(f"\n🆕 Operations Without Original Functions ({len(analysis['operations_without_functions'])})")
        print("=" * 45)
        print("These operations may be new or refactored:")
        for op in analysis['operations_without_functions']:
            print(f"  {op}")
    
    # CLI registration status
    print(f"\n🖥️  CLI Registration Status")
    print("=" * 27)
    print(f"Total CLI Operations: {len(analysis['cli_registered'])}")
    print("Registered Operations:")
    for cli_name in sorted(analysis['cli_registered']):
        print(f"  inv_scr {cli_name}")

def generate_migration_recommendations():
    """Generate recommendations for completing the migration"""
    analysis = analyze_function_to_operation_mapping()
    
    print(f"\n💡 Migration Recommendations")
    print("=" * 30)
    
    if not analysis['not_migrated']:
        print("🎉 All inventory functions have been successfully migrated!")
        print("✅ Your migration is complete!")
    else:
        print("📋 Functions still needing migration:")
        for item in analysis['not_migrated']:
            if item['reason'] == 'Operation file missing':
                print(f"  1. Create {item['expected_operation']} based on {item['function']}")
            else:
                print(f"  1. Analyze {item['function']} to determine appropriate operation structure")
    
    print(f"\n🔧 Utility Scripts Analysis:")
    print("These scripts serve specialized purposes and may not need migration:")
    
    categories = {
        'Account Validation': ['ALZ_CheckAccount.py', 'CT_CheckAccount.py'],
        'Organization Management': ['DrawOrg.py', 'my_org_users.py'],
        'CloudFormation Tools': ['find_orphaned_stacks.py', 'mod_my_cfnstacksets.py', 'move_stack_instances.py'],
        'Security Tools': ['find_security_groups.py', 'verify_security_groups.py', 'lock_down_stack_sets_role.py'],
        'Maintenance Tools': ['delete_bucket_objects.py', 'update_retention_on_all_my_cw_groups.py'],
        'Analysis Tools': ['network_diagram.py', 'SumUpFlowLogs.py', 'check_all_cloudtrail.py']
    }
    
    for category, scripts in categories.items():
        matching_scripts = [s for s in analysis['utility_scripts'] if s in scripts]
        if matching_scripts:
            print(f"  {category}: {len(matching_scripts)} scripts")
    
    print(f"\n🎯 Next Steps:")
    if analysis['not_migrated']:
        print("  1. Complete migration of remaining inventory functions")
        print("  2. Add enhanced testing for newly migrated operations")
        print("  3. Update documentation")
    print("  4. Consider creating operations for frequently used utility scripts")
    print("  5. Maintain utility scripts for specialized use cases")

def main():
    """Main analysis function"""
    print_analysis()
    generate_migration_recommendations()
    
    print(f"\n📚 Files Generated:")
    print("  • This analysis shows current migration status")
    print("  • Use this information to prioritize remaining migration work")
    print("  • Focus on inventory functions first, utility scripts second")

if __name__ == "__main__":
    main()