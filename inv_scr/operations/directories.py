#!/usr/bin/env python3
"""AWS Directory Service inventory operation"""

import logging
from tqdm.auto import tqdm
from botocore.exceptions import ClientError

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

__version__ = "2025.07.11"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('directories', 'AWS Directory Service specific options')
    local.add_argument(
        "--fragment", "--frag",
        dest="pFragments",
        nargs="*",
        metavar="Directory fragment",
        default=['all'],
        help="String fragment(s) to be looked for in the directory names"
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
        version=f"AWS Directory Service operation version {__version__}"
    )

def find_all_directories(fAllCredentials: list, fFragments: list = None, fExact: bool = False) -> list:
    """
    Find all AWS Directory Service directories from all accounts/regions within the credentials supplied
    """
    AllDirectories = []
    
    for credential in tqdm(fAllCredentials, desc=f"Looking through {len(fAllCredentials)} accounts and regions", unit='credentials'):
        logging.info(f"Looking in account: {credential['AccountId']} in region {credential['Region']}")
        if not credential.get('Success', True):
            continue
        try:
            directories = Inventory_Modules.find_directories2(credential, credential['Region'], fFragments, fExact)
            logging.info(f"Account: {credential['AccountId']} Region: {credential['Region']} Found {len(directories)} directories")
            
            for directory in directories:
                directory.update({
                    'MgmtAccount': credential['MgmtAccount'],
                    'Region': credential['Region'],
                    'AccountId': credential['AccountId'],
                    'ParentProfile': credential.get('ParentProfile', 'Unknown')
                })
                AllDirectories.append(directory)
                
        except TypeError as my_Error:
            logging.info(f"Error: {my_Error}")
            continue
        except ClientError as my_Error:
            if "AuthFailure" in str(my_Error):
                logging.error(f"Account {credential['AccountId']}: Authorization Failure")
            else:
                logging.error(f"AWS API error: {my_Error}")
    
    return AllDirectories

def run(args):
    """Main execution function for directories operation"""
    # Get timing context from CLI (if available)
    timing = getattr(args, '_timing_context', None)
    
    # Extract arguments
    pProfiles = args.Profiles
    pRegionList = args.Regions
    pAccounts = args.Accounts
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pAccessRoles = args.AccessRoles
    pFragments = getattr(args, 'pFragments', ['all'])
    pExact = getattr(args, 'pExact', False)
    pRootOnly = args.RootOnly
    pFilename = args.Filename
    pTiming = args.Time
    
    print("Searching for AWS Directory Service directories...")
    print(f"Operation version: {__version__}")
    
    if timing:
        timing.milestone("args_parsed", "Arguments parsed and validated")
    
    # Get credentials for all accounts
    CredentialList = get_all_credentials(
        pProfiles, pTiming, pSkipProfiles, pSkipAccounts, 
        pRootOnly, pAccounts, pRegionList, pAccessRoles
    )
    
    AccountNum = len(set([acct['AccountId'] for acct in CredentialList]))
    RegionNum = len(set([acct['Region'] for acct in CredentialList]))
    
    print(f"Searching {AccountNum} accounts across {RegionNum} regions")
    
    if timing:
        timing.milestone("credentials_setup", f"Credential setup for {AccountNum} accounts across {RegionNum} regions")
    
    # Find all directories
    AllDirectories = find_all_directories(CredentialList, pFragments, pExact)
    
    if timing:
        timing.milestone("directories_found", f"Found {len(AllDirectories)} directories")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Parent Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Account Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'DirectoryName': {'DisplayOrder': 5, 'Heading': 'Directory Name'},
        'DirectoryId': {'DisplayOrder': 6, 'Heading': 'Directory ID'},
        'HomeRegion': {'DisplayOrder': 7, 'Heading': 'Home Region'},
        'Status': {'DisplayOrder': 8, 'Heading': 'Status'},
        'Type': {'DisplayOrder': 9, 'Heading': 'Type'},
        'Owner': {'DisplayOrder': 10, 'Heading': 'Owner'}
    }

    sorted_directories = sorted(AllDirectories, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['Region'], d.get('DirectoryName', '')
    ))
    
    display_results(sorted_directories, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllDirectories)} directories across {AccountNum} accounts and {RegionNum} regions")