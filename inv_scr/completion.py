#!/usr/bin/env python3
"""
Tab completion support for inv_scr CLI
"""

try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False

from inv_scr.cli import OPERATIONS


def operation_completer(prefix, parsed_args, **kwargs):
    """Custom completer for operations"""
    operations = list(OPERATIONS.keys()) + ['list']
    return [op for op in operations if op.startswith(prefix)]


def profile_completer(prefix, parsed_args, **kwargs):
    """Custom completer for AWS profiles"""
    try:
        import boto3
        session = boto3.Session()
        profiles = session.available_profiles
        return [profile for profile in profiles if profile.startswith(prefix)]
    except Exception:
        return []


def region_completer(prefix, parsed_args, **kwargs):
    """Custom completer for AWS regions"""
    try:
        import boto3
        ec2 = boto3.client('ec2', region_name='us-east-1')
        regions = [r['RegionName'] for r in ec2.describe_regions()['Regions']]
        regions.append('all')  # Add the special 'all' option
        return [region for region in regions if region.startswith(prefix)]
    except Exception:
        # Fallback to common regions if API call fails
        common_regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-central-1', 'ap-southeast-1',
            'ap-southeast-2', 'ap-northeast-1', 'all'
        ]
        return [region for region in common_regions if region.startswith(prefix)]


def setup_completion(parser):
    """Setup argcomplete for the parser"""
    if not ARGCOMPLETE_AVAILABLE:
        return  # Skip if argcomplete not available
    
    # Find existing arguments and set completers
    for action in parser._actions:
        if hasattr(action, 'dest'):
            if action.dest == 'operation':
                action.completer = operation_completer
            elif action.dest in ['profiles', 'Profile']:
                action.completer = profile_completer
            elif action.dest in ['regions', 'Regions']:
                action.completer = region_completer
    
    # Enable argcomplete
    argcomplete.autocomplete(parser)