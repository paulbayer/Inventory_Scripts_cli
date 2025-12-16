#!/usr/bin/env python3
"""
AWS Inventory CLI - Unified tool for AWS resource inventory across organizations
"""

import sys
import logging
from time import time
from colorama import init, Fore

from inv_scr.core.ArgumentsClass import CommonArguments
from inv_scr.operations import (
    instances, vpcs, cfnstacks, cfnstacksets, directories, 
    ebs_volumes, ecs_clusters, elbs, enis, functions,
    gas, gd_detectors, orgs, phzs, policies, rds_instances,
    roles, saml_providers, subnets, tgws, topics, ram_shares,
    config_recorders, cloudtrail, azs, org_users
)

init()
__version__ = "2025.07.10"

# Available operations mapping
OPERATIONS = {
    'cfnstacks': cfnstacks.run,
    'cfnstacksets': cfnstacksets.run,
    'cloudtrail': cloudtrail.run,
    'azs': azs.run,
    'org-users': org_users.run,
    'directories': directories.run,
    'ebs-volumes': ebs_volumes.run,
    'ecs-clusters': ecs_clusters.run,
    'elbs': elbs.run,
    'enis': enis.run,
    'functions': functions.run,
    'gas': gas.run,
    'gd-detectors': gd_detectors.run,
    'instances': instances.run,
    'orgs': orgs.run,
    'phzs': phzs.run,
    'policies': policies.run,
    'ram-shares': ram_shares.run,
    'rds-instances': rds_instances.run,
    'roles': roles.run,
    'saml-providers': saml_providers.run,
    'subnets': subnets.run,
    'tgws': tgws.run,
    'topics': topics.run,
    'config-recorders': config_recorders.run,
    'vpcs': vpcs.run,
}

def parse_args():
    """Parse command line arguments"""
    import sys
    
    # First, determine which operation is being requested
    operation = None
    if len(sys.argv) > 1 and sys.argv[1] in list(OPERATIONS.keys()) + ['list']:
        operation = sys.argv[1]
    
    parser = CommonArguments()
    parser.my_parser.description = "AWS Inventory CLI - Find resources across AWS Organizations"
    parser.my_parser.add_argument(
        "operation",
        choices=list(OPERATIONS.keys()) + ['list'],
        help="The inventory operation to run. Use 'list' to see all available operations."
    )
    
    # Common arguments
    parser.multiprofile()
    parser.multiregion()
    parser.extendedargs()
    parser.rolestouse()
    parser.rootOnly()
    parser.save_to_file()
    parser.timing()
    parser.verbosity()
    parser.version(__version__)
    
    # Add operation-specific arguments if we know the operation
    if operation and operation != 'list':
        try:
            # Import the operation module and add its specific arguments
            operation_module = __import__(f'inv_scr.operations.{operation.replace("-", "_")}', fromlist=['add_operation_args'])
            if hasattr(operation_module, 'add_operation_args'):
                operation_module.add_operation_args(parser)
        except ImportError:
            pass  # Operation module doesn't exist or doesn't have add_operation_args
    
    # Parse all arguments including operation-specific ones
    return parser.my_parser.parse_args()

def list_operations():
    """List all available operations"""
    print("\nAvailable inventory operations:")
    print("=" * 50)
    
    operation_descriptions = {
        'instances': 'Find EC2 instances across accounts',
        'vpcs': 'Find VPCs across accounts',
        'cfnstacks': 'Find CloudFormation stacks',
        'cfnstacksets': 'Find CloudFormation stack sets',
        'directories': 'Find AWS Directory Service directories',
        'ebs-volumes': 'Find EBS volumes',
        'ecs-clusters': 'Find ECS clusters and tasks',
        'elbs': 'Find Elastic Load Balancers',
        'enis': 'Find Elastic Network Interfaces',
        'functions': 'Find Lambda functions',
        'gas': 'Find Global Accelerator accelerators',
        'gd-detectors': 'Find GuardDuty detectors',
        'config-recorders': 'Find Config recorders and delivery channels',
        'cloudtrail': 'Find CloudTrail coverage',
        'azs': 'Find availability zone coverage',
        'orgs': 'Find AWS Organizations information',
        'phzs': 'Find Private Hosted Zones',
        'policies': 'Find IAM policies',
        'ram-shares': 'Find AWS RAM resource shares',
        'rds-instances': 'Find RDS instances',
        'org-users': 'Find IAM and Identity Center users',
        'roles': 'Find IAM roles',
        'saml-providers': 'Find SAML identity providers',
        'subnets': 'Find VPC subnets',
        'tgws': 'Find Transit Gateways',
        'topics': 'Find SNS topics',
    }
    
    # Sort operations alphabetically for consistent display
    for op, desc in sorted(operation_descriptions.items()):
        print(f"  {op:<15} - {desc}")
    
    print("\nExample usage:")
    print("  inv_scr instances --profiles my-profile --regions us-east-1")
    print("  inv_scr vpcs --profiles profile1 profile2 --regions all")
    print("  inv_scr cfnstacks --help  # For operation-specific help")
    print()

def main():
    """Main CLI entry point"""
    from inv_scr.core.timing import create_timing_context
    
    args = parse_args()
    
    # Create timing context for the entire CLI execution
    with create_timing_context(args, "AWS Inventory CLI") as timing:
        
        # Setup logging
        logging.basicConfig(
            level=args.loglevel, 
            format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
        )
        logging.getLogger("boto3").setLevel(logging.CRITICAL)
        logging.getLogger("botocore").setLevel(logging.CRITICAL)
        logging.getLogger("s3transfer").setLevel(logging.CRITICAL)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)
        
        timing.milestone("setup", "CLI setup and logging configuration")
        
        if args.operation == 'list':
            list_operations()
            return
        
        print(f"\n{Fore.CYAN}AWS Inventory CLI v{__version__}{Fore.RESET}")
        print(f"Running operation: {Fore.GREEN}{args.operation}{Fore.RESET}")
        print()
        
        try:
            # Add timing context to args for operations to use
            args._timing_context = timing
            
            # Run the selected operation
            operation_func = OPERATIONS[args.operation]
            timing.milestone("operation_start", f"Starting {args.operation} operation")
            
            operation_func(args)
            
            timing.milestone("operation_complete", f"Completed {args.operation} operation")
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Operation cancelled by user{Fore.RESET}")
            sys.exit(1)
        except Exception as e:
            print(f"\n{Fore.RED}Error running operation '{args.operation}': {e}{Fore.RESET}")
            logging.exception("Operation failed")
            sys.exit(1)
        
        print(f"\n{Fore.CYAN}Operation completed successfully{Fore.RESET}")
        
        # Timing summary is automatically displayed by context manager

if __name__ == '__main__':
    main()
