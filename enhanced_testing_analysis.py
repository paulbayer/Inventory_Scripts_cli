#!/usr/bin/env python3
"""
Enhanced Testing Analysis: Current Status and Prioritization

This script analyzes which operations have enhanced testing configured
and prioritizes which operations should get enhanced testing next.
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

def get_operations_with_enhanced_testing() -> Dict[str, List[str]]:
    """Analyze which operations have enhanced testing configured"""
    test_file = Path("tests/test_operations.py")
    if not test_file.exists():
        return {}
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    # Find all enhanced test methods (test_run_with_*)
    enhanced_tests = {}
    
    # Pattern to find test classes and their enhanced methods
    class_pattern = r'class (Test\w+Operation)\(unittest\.TestCase\):'
    method_pattern = r'def (test_run_with_\w+)\('
    
    classes = re.findall(class_pattern, content)
    
    for class_name in classes:
        # Extract operation name from class name
        operation_name = class_name.replace('Test', '').replace('Operation', '').lower()
        
        # Find the class content
        class_start = content.find(f'class {class_name}(unittest.TestCase):')
        if class_start == -1:
            continue
            
        # Find next class or end of file
        next_class = content.find('class Test', class_start + 1)
        if next_class == -1:
            class_content = content[class_start:]
        else:
            class_content = content[class_start:next_class]
        
        # Find enhanced test methods in this class
        enhanced_methods = re.findall(method_pattern, class_content)
        
        if enhanced_methods:
            enhanced_tests[operation_name] = enhanced_methods
    
    return enhanced_tests

def get_all_operations() -> List[str]:
    """Get list of all available operations"""
    cli_file = Path("inv_scr/cli.py")
    if not cli_file.exists():
        return []
    
    with open(cli_file, 'r') as f:
        content = f.read()
    
    # Find OPERATIONS dictionary
    operations_match = re.search(r'OPERATIONS\s*=\s*{([^}]+)}', content, re.DOTALL)
    if not operations_match:
        return []
    
    operations_content = operations_match.group(1)
    operations = []
    
    for line in operations_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and ':' in line:
            match = re.match(r"'([^']+)':", line)
            if match:
                operations.append(match.group(1))
    
    return sorted(operations)

def analyze_operation_complexity() -> Dict[str, Dict]:
    """Analyze operation complexity based on various factors"""
    operations_dir = Path("inv_scr/operations")
    complexity_analysis = {}
    
    for op_file in operations_dir.glob("*.py"):
        if op_file.name == "__init__.py":
            continue
            
        operation_name = op_file.stem
        
        try:
            with open(op_file, 'r') as f:
                content = f.read()
            
            # Analyze complexity factors
            analysis = {
                'file_size': len(content),
                'line_count': len(content.split('\n')),
                'has_filtering': bool(re.search(r'pFragments|pStatus|pExact|pDefault', content)),
                'has_threading': 'Thread' in content or 'Queue' in content,
                'has_tqdm': 'tqdm' in content,
                'argument_count': len(re.findall(r'add_argument\(', content)),
                'complexity_score': 0
            }
            
            # Calculate complexity score
            score = 0
            score += min(analysis['line_count'] / 50, 10)  # Max 10 points for size
            score += 5 if analysis['has_filtering'] else 0
            score += 3 if analysis['has_threading'] else 0
            score += 2 if analysis['has_tqdm'] else 0
            score += analysis['argument_count'] * 1
            
            analysis['complexity_score'] = round(score, 1)
            complexity_analysis[operation_name] = analysis
            
        except Exception as e:
            complexity_analysis[operation_name] = {
                'error': str(e),
                'complexity_score': 0
            }
    
    return complexity_analysis

def get_operation_usage_priority() -> Dict[str, int]:
    """Determine operation usage priority based on common AWS resource types"""
    # Priority based on common usage patterns in AWS environments
    usage_priority = {
        # High priority - Core infrastructure
        'instances': 10,      # EC2 instances - most common
        'vpcs': 9,           # VPCs - already done
        'functions': 8,      # Lambda functions - already done
        'cfnstacks': 9,      # CloudFormation - infrastructure as code
        'rds-instances': 8,  # Databases - critical
        'roles': 8,          # IAM roles - security critical
        'subnets': 7,        # Networking - important
        'elbs': 7,           # Load balancers - common
        
        # Medium-high priority - Common services
        'ebs-volumes': 6,    # Storage - common
        'policies': 6,       # IAM policies - security
        'enis': 5,           # Network interfaces
        'topics': 5,         # SNS topics - messaging
        'cfnstacksets': 6,   # StackSets - multi-account
        
        # Medium priority - Specialized but important
        'ecs-clusters': 5,   # Container orchestration
        'tgws': 4,           # Transit gateways - enterprise
        'directories': 4,    # Directory services
        'orgs': 6,           # Organizations - multi-account
        
        # Lower priority - Specialized services
        'phzs': 3,           # Private hosted zones
        'gd-detectors': 3,   # GuardDuty - security
        'gas': 2,            # Global Accelerator
        'saml-providers': 2, # SAML - specialized auth
    }
    
    return usage_priority

def prioritize_operations_for_enhanced_testing() -> List[Dict]:
    """Prioritize operations for enhanced testing implementation"""
    enhanced_ops = get_operations_with_enhanced_testing()
    all_ops = get_all_operations()
    complexity = analyze_operation_complexity()
    usage_priority = get_operation_usage_priority()
    
    # Operations that need enhanced testing
    needs_testing = []
    
    for op in all_ops:
        # Convert CLI name to operation name for lookup
        op_name = op.replace('-', '_')
        
        if op_name not in enhanced_ops:
            priority_score = usage_priority.get(op, 1)
            complexity_info = complexity.get(op_name, {'complexity_score': 1})
            
            # Calculate total priority score
            total_score = priority_score + (complexity_info.get('complexity_score', 1) * 0.3)
            
            needs_testing.append({
                'operation': op,
                'operation_name': op_name,
                'usage_priority': priority_score,
                'complexity_score': complexity_info.get('complexity_score', 1),
                'total_score': round(total_score, 1),
                'has_filtering': complexity_info.get('has_filtering', False),
                'has_threading': complexity_info.get('has_threading', False),
                'argument_count': complexity_info.get('argument_count', 0),
                'line_count': complexity_info.get('line_count', 0)
            })
    
    # Sort by total score (highest first)
    needs_testing.sort(key=lambda x: x['total_score'], reverse=True)
    
    return needs_testing

def print_enhanced_testing_analysis():
    """Print comprehensive enhanced testing analysis"""
    print("🧪 Enhanced Testing Analysis")
    print("=" * 35)
    
    enhanced_ops = get_operations_with_enhanced_testing()
    all_ops = get_all_operations()
    
    # Current status
    print(f"\n📊 Current Status")
    print("=" * 17)
    print(f"Total Operations: {len(all_ops)}")
    print(f"With Enhanced Testing: {len(enhanced_ops)} ✅")
    print(f"Without Enhanced Testing: {len(all_ops) - len(enhanced_ops)} ⚠️")
    print(f"Enhanced Testing Coverage: {(len(enhanced_ops)/len(all_ops))*100:.1f}%")
    
    # Operations with enhanced testing
    print(f"\n✅ Operations with Enhanced Testing ({len(enhanced_ops)})")
    print("=" * 45)
    for op_name, methods in enhanced_ops.items():
        # Convert back to CLI name
        cli_name = op_name.replace('_', '-')
        if cli_name == 'functions':
            cli_name = 'functions'  # Keep as is
        elif cli_name == 'instances':
            cli_name = 'instances'  # Keep as is
        elif cli_name == 'vpcs':
            cli_name = 'vpcs'  # Keep as is
        
        print(f"  {cli_name:<20} → {len(methods)} enhanced test(s)")
        for method in methods:
            test_type = method.replace('test_run_with_', '').replace('_', ' ').title()
            print(f"    • {test_type}")
    
    # Prioritized list for implementation
    prioritized = prioritize_operations_for_enhanced_testing()
    
    print(f"\n🎯 Priority Queue for Enhanced Testing ({len(prioritized)})")
    print("=" * 45)
    print(f"{'Rank':<4} {'Operation':<20} {'Priority':<8} {'Complexity':<10} {'Score':<6} {'Features'}")
    print("-" * 70)
    
    for i, op in enumerate(prioritized[:15], 1):  # Show top 15
        features = []
        if op['has_filtering']:
            features.append('Filtering')
        if op['has_threading']:
            features.append('Threading')
        if op['argument_count'] > 3:
            features.append('Complex Args')
        
        features_str = ', '.join(features) if features else 'Basic'
        
        print(f"{i:<4} {op['operation']:<20} {op['usage_priority']:<8} {op['complexity_score']:<10} {op['total_score']:<6} {features_str}")

def generate_implementation_recommendations():
    """Generate specific recommendations for implementing enhanced testing"""
    prioritized = prioritize_operations_for_enhanced_testing()
    
    print(f"\n💡 Implementation Recommendations")
    print("=" * 35)
    
    # Top 5 priorities
    top_5 = prioritized[:5]
    
    print(f"\n🚀 Phase 1: High Priority Operations (Implement First)")
    print("=" * 55)
    for i, op in enumerate(top_5, 1):
        print(f"\n{i}. {op['operation'].upper()}")
        print(f"   Priority Score: {op['total_score']}")
        print(f"   Why prioritize:")
        
        if op['usage_priority'] >= 8:
            print("     • High usage - commonly used AWS service")
        if op['has_filtering']:
            print("     • Has filtering logic that needs testing")
        if op['has_threading']:
            print("     • Uses threading - complex execution flow")
        if op['complexity_score'] > 5:
            print("     • Complex operation with multiple features")
        if op['argument_count'] > 3:
            print("     • Multiple arguments - various test scenarios needed")
        
        print(f"   Recommended tests:")
        print("     • Single account credentials test")
        print("     • Multi-account credentials test")
        if op['has_filtering']:
            print("     • Filtering logic test")
        if 'region' in op['operation'] or op['operation'] in ['instances', 'vpcs', 'functions']:
            print("     • Multi-region credentials test")
    
    # Next phase
    next_5 = prioritized[5:10]
    print(f"\n📋 Phase 2: Medium Priority Operations (Implement Second)")
    print("=" * 58)
    for op in next_5:
        reason = "Standard inventory operation"
        if op['has_filtering']:
            reason = "Has filtering capabilities"
        if op['complexity_score'] > 4:
            reason = "Moderately complex operation"
        
        print(f"  • {op['operation']:<20} (Score: {op['total_score']}) - {reason}")
    
    # Implementation strategy
    print(f"\n🔧 Implementation Strategy")
    print("=" * 25)
    print("1. **Start with Phase 1 operations** - highest impact")
    print("2. **Use existing patterns** from instances/vpcs/functions tests")
    print("3. **Focus on business logic** - filtering, data transformation")
    print("4. **Test multi-account scenarios** for organizational operations")
    print("5. **Add error handling tests** for complex operations")
    
    print(f"\n📚 Test Templates Available")
    print("=" * 27)
    print("• Single account test template (from instances)")
    print("• Multi-account test template (from instances)")
    print("• Filtering logic test template (from instances)")
    print("• Multi-region test template (from instances)")
    print("• Shared test data system for consistent data")
    
    print(f"\n⏱️  Estimated Implementation Time")
    print("=" * 32)
    print("• Phase 1 (5 operations): 2-3 hours per operation = 10-15 hours")
    print("• Phase 2 (5 operations): 1-2 hours per operation = 5-10 hours")
    print("• Total estimated time: 15-25 hours")
    print("• Recommended pace: 2-3 operations per week")

def main():
    """Main analysis function"""
    print_enhanced_testing_analysis()
    generate_implementation_recommendations()
    
    print(f"\n🎉 Summary")
    print("=" * 10)
    enhanced_ops = get_operations_with_enhanced_testing()
    all_ops = get_all_operations()
    
    print(f"Current enhanced testing coverage: {len(enhanced_ops)}/{len(all_ops)} operations")
    print(f"Remaining work: {len(all_ops) - len(enhanced_ops)} operations need enhanced testing")
    print(f"Focus on the top 5 prioritized operations for maximum impact!")

if __name__ == "__main__":
    main()