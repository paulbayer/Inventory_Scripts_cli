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
    config_recorders, cloudtrail, azs, org_users, remove_iam_user
)

init()
__version__ = "2026.01.28"

# Available operations with metadata (alphabetically sorted)
# Ideas for later:
#   'help_text': Detailed help beyond the description
#   'category': Grouping operations (compute, networking, security, etc.)
#   'requires_regions': Validation hints
#   'supports_filtering': Capability flags

OPERATIONS = {
    'azs': {
        'run': azs.run,
        'description': 'Find availability zone coverage across AWS accounts and regions',
    },
    'cfnstacks': {
        'run': cfnstacks.run,
        'description': 'Find CloudFormation stacks across AWS accounts and regions',
    },
    'cfnstacksets': {
        'run': cfnstacksets.run,
        'description': 'Find CloudFormation stack sets across AWS Organizations',
    },
    'cloudtrail': {
        'run': cloudtrail.run,
        'description': 'Find CloudTrail coverage and configuration across accounts',
    },
    'config-recorders': {
        'run': config_recorders.run,
        'description': 'Find AWS Config recorders and delivery channels',
    },
    'directories': {
        'run': directories.run,
        'description': 'Find AWS Directory Service directories across accounts',
    },
    'ebs-volumes': {
        'run': ebs_volumes.run,
        'description': 'Find EBS volumes across AWS accounts and regions',
    },
    'ecs-clusters': {
        'run': ecs_clusters.run,
        'description': 'Find ECS clusters and running tasks across accounts',
    },
    'elbs': {
        'run': elbs.run,
        'description': 'Find Elastic Load Balancers (Classic, Application, Network) across accounts',
    },
    'enis': {
        'run': enis.run,
        'description': 'Find Elastic Network Interfaces across AWS accounts and regions',
    },
    'functions': {
        'run': functions.run,
        'description': 'Find Lambda functions across AWS accounts and regions',
    },
    'gas': {
        'run': gas.run,
        'description': 'Find Global Accelerator accelerators across AWS accounts',
    },
    'gd-detectors': {
        'run': gd_detectors.run,
        'description': 'Find GuardDuty detectors and their configuration across accounts',
    },
    'instances': {
        'run': instances.run,
        'description': 'Find EC2 instances across AWS accounts and regions',
    },
    'org-users': {
        'run': org_users.run,
        'description': 'Find IAM users and Identity Center users across AWS Organizations',
    },
    'orgs': {
        'run': orgs.run,
        'description': 'Find AWS Organizations information and account structure',
    },
    'phzs': {
        'run': phzs.run,
        'description': 'Find Route 53 Private Hosted Zones across AWS accounts',
    },
    'policies': {
        'run': policies.run,
        'description': 'Find IAM policies (managed and inline) across AWS accounts',
    },
    'ram-shares': {
        'run': ram_shares.run,
        'description': 'Find AWS Resource Access Manager (RAM) resource shares',
    },
    'rds-instances': {
        'run': rds_instances.run,
        'description': 'Find RDS database instances across AWS accounts and regions',
    },
    'remove-iam-user': {
        'run': remove_iam_user.run,
        'description': 'Remove an IAM user and all associated resources from AWS accounts',
    },
    'roles': {
        'run': roles.run,
        'description': 'Find IAM roles across AWS accounts',
    },
    'saml-providers': {
        'run': saml_providers.run,
        'description': 'Find SAML identity providers across AWS accounts',
    },
    'subnets': {
        'run': subnets.run,
        'description': 'Find VPC subnets across AWS accounts and regions',
    },
    'tgws': {
        'run': tgws.run,
        'description': 'Find Transit Gateways and their configuration across accounts',
    },
    'topics': {
        'run': topics.run,
        'description': 'Find SNS topics across AWS accounts and regions',
    },
    'vpcs': {
        'run': vpcs.run,
        'description': 'Find VPCs across AWS accounts and regions',
    },
}

def parse_args():
    """Parse command line arguments"""
    import sys
    
    # First, determine which operation is being requested
    operation = None
    if len(sys.argv) > 1 and sys.argv[1] in list(OPERATIONS.keys()) + ['list']:
        operation = sys.argv[1]
    
    parser = CommonArguments()
    
    # Customize description based on the operation
    if operation and operation in OPERATIONS:
        parser.my_parser.description = f"AWS Inventory CLI - {Fore.CYAN}{OPERATIONS[operation]['description']}{Fore.RESET}"
    else:
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
    
    # Setup tab completion
    try:
        import argcomplete
        from inv_scr.completion import setup_completion
        setup_completion(parser.my_parser)
    except ImportError:
        pass  # argcomplete not available
    
    # Parse all arguments including operation-specific ones
    return parser.my_parser.parse_args()

def list_operations():
    """List all available operations"""
    print("\nAvailable inventory operations:")
    print("=" * 50)
    
    # Sort operations alphabetically for consistent display
    for op, metadata in sorted(OPERATIONS.items()):
        print(f"  {op:<15} - {metadata['description']}")
    
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
            operation_func = OPERATIONS[args.operation]['run']
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
