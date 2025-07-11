#!/usr/bin/env python3
"""IAM Roles inventory operation"""

import logging
import boto3
from tqdm.auto import tqdm
from botocore.exceptions import ClientError

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results, find_in

__version__ = "2025.07.11"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('roles', 'IAM Roles specific options')
    local.add_argument(
        "--fragment", "--frag",
        dest="pFragments",
        nargs="*",
        metavar="Role fragment",
        default=None,
        help="String fragment(s) to be looked for in the role names"
    )
    local.add_argument(
        "--exact",
        dest="pExact",
        action="store_true",
        help="Look for exact match of fragment, instead of substring"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"IAM Roles operation version {__version__}"
    )

def find_all_roles(fAllCredentials: list, frole_fragments: list = None, fexact: bool = False) -> list:
    """
    Find all IAM roles from all accounts within the credentials supplied
    """
    AllRoles = []
    
    print()
    if frole_fragments is None:
        print(f"Listing out all roles across {len(fAllCredentials)} accounts")
    elif fexact:
        print(f"Looking for a role exactly named one of these strings {frole_fragments} across {len(fAllCredentials)} accounts")
    else:
        print(f"Looking for a role containing one of these strings {frole_fragments} across {len(fAllCredentials)} accounts")
    print()

    for account in tqdm(fAllCredentials, desc="Processing accounts", unit="accounts"):
        if not account.get('Success', True):
            continue
            
        try:
            iam_session = boto3.Session(
                aws_access_key_id=account['AccessKeyId'],
                aws_secret_access_key=account['SecretAccessKey'],
                aws_session_token=account['SessionToken'],
                region_name=account['Region']
            )
            iam_client = iam_session.client('iam')
            
            # Get all roles with pagination
            paginator = iam_client.get_paginator('list_roles')
            
            for page in paginator.paginate():
                for role in page['Roles']:
                    AllRoles.append({
                        'MgmtAccount': account['MgmtAccount'],
                        'AccountId': account['AccountId'],
                        'Region': account['Region'],
                        'ParentProfile': account.get('ParentProfile', 'Unknown'),
                        'RoleName': role['RoleName'],
                        'CreateDate': role.get('CreateDate', ''),
                        'AssumeRolePolicyDocument': role.get('AssumeRolePolicyDocument', ''),
                        'Path': role.get('Path', '/'),
                        'MaxSessionDuration': role.get('MaxSessionDuration', 3600)
                    })
                    
        except ClientError as my_Error:
            if "AuthFailure" in str(my_Error):
                logging.error(f"Authorization failure for account {account['AccountId']}")
            else:
                logging.error(f"AWS API error for account {account['AccountId']}: {my_Error}")
        except Exception as my_Error:
            logging.error(f"Unexpected error for account {account['AccountId']}: {my_Error}")

    # Filter roles if fragments specified
    if frole_fragments is None:
        found_roles = AllRoles
    else:
        found_roles = [x for x in AllRoles if find_in([x['RoleName']], frole_fragments, fexact)]
    
    return found_roles

def run(args):
    """Main execution function for roles operation"""
    # Get timing context from CLI (if available)
    timing = getattr(args, '_timing_context', None)
    
    # Extract arguments
    pProfiles = args.Profiles
    pRegionList = args.Regions
    pAccounts = args.Accounts
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pFragments = getattr(args, 'pFragments', None)
    pExact = getattr(args, 'pExact', False)
    pRootOnly = args.RootOnly
    pFilename = args.Filename
    pTiming = args.Time
    
    print("Searching for IAM roles...")
    print(f"Operation version: {__version__}")
    
    if timing:
        timing.milestone("args_parsed", "Arguments parsed and validated")
    
    # Get credentials for all accounts
    CredentialList = get_all_credentials(
        pProfiles, pTiming, pSkipProfiles, pSkipAccounts, 
        pRootOnly, pAccounts, pRegionList
    )
    
    AccountNum = len(set([acct['AccountId'] for acct in CredentialList]))
    
    print(f"Searching {AccountNum} accounts")
    
    if timing:
        timing.milestone("credentials_setup", f"Credential setup for {AccountNum} accounts")
    
    # Find all roles
    AllRoles = find_all_roles(CredentialList, pFragments, pExact)
    
    if timing:
        timing.milestone("roles_found", f"Found {len(AllRoles)} roles")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Parent Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Account Number'},
        'RoleName': {'DisplayOrder': 4, 'Heading': 'Role Name'},
        'Path': {'DisplayOrder': 5, 'Heading': 'Path'},
        'CreateDate': {'DisplayOrder': 6, 'Heading': 'Created'},
        'MaxSessionDuration': {'DisplayOrder': 7, 'Heading': 'Max Session (sec)'}
    }

    sorted_roles = sorted(AllRoles, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['RoleName']
    ))
    
    display_results(sorted_roles, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    if pFragments is None:
        print(f"\nFound {len(AllRoles)} roles across {AccountNum} accounts")
    else:
        print(f"\nFound {len(AllRoles)} instances where role containing {pFragments} was found across {AccountNum} accounts")