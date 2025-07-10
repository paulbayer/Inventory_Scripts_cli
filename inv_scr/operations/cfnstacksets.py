#!/usr/bin/env python3
"""
CloudFormation StackSets inventory operation
"""

import logging
from time import time
from botocore.exceptions import ClientError
from colorama import Fore, init

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

init()
__version__ = "2025.07.10"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('cfnstacksets', 'CloudFormation StackSets specific options')
    local.add_argument(
        "-f", "--fragment",
        dest="pFragments",
        nargs='*',
        metavar="string fragment",
        default=["all"],
        help="List of fragments of the stackset name(s) you want to check for."
    )
    local.add_argument(
        "-e", "--exact",
        dest="pExact",
        action="store_true",
        help="Use this flag to make sure that ONLY the string you specified will be identified"
    )
    local.add_argument(
        "-s", "--status",
        dest="pStatus",
        metavar="CloudFormation status",
        default="ACTIVE",
        choices=['active', 'ACTIVE', 'Active', 'deleted', 'DELETED', 'Deleted'],
        help="String that determines whether we only see 'ACTIVE' or 'DELETED' stacksets. Default is 'ACTIVE'"
    )
    local.add_argument(
        "-i", "--instances",
        dest="pInstanceCount",
        action="store_true",
        default=False,
        help="Flag to determine whether you want to see the instance totals for each stackset"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"CloudFormation StackSets operation version {__version__}"
    )

def find_all_cfnstacksets(fAllCredentials: list, fFragments: list = None, fStatus: str = "ACTIVE", fInstanceCount: bool = False) -> list:
    """
    Find all CloudFormation StackSets from all accounts/regions within the credentials supplied
    """
    All_Results = []
    ERASE_LINE = '\x1b[2K'
    
    for credential in fAllCredentials:
        if not credential.get('Success', True):
            logging.error(f"Failure for account {credential['AccountId']} in region {credential['Region']}")
            continue
            
        print(f"{ERASE_LINE}{Fore.RED}Checking Account: {credential['AccountId']} Region: {credential['Region']} for stacksets matching {fFragments} with status: {fStatus}{Fore.RESET}", end="\r")
        
        try:
            StackSets = Inventory_Modules.find_stacksets2(credential, fFragments, fStatus)
            logging.info(f"Account: {credential['AccountId']} | Region: {credential['Region']} | Found {len(StackSets)} StackSets")
            
            if not StackSets:
                logging.info(f"Connected to account {credential['AccountId']} in region {credential['Region']}, but found no stacksets")
            else:
                print(f"{ERASE_LINE}{Fore.RED}Account: {credential['AccountId']} Region: {credential['Region']} Found {len(StackSets)} StackSets{Fore.RESET}", end="\r")
                
            for stack in StackSets:
                ListOfStackInstances = []
                if fInstanceCount:
                    milestone = time()
                    try:
                        ListOfStackInstances = Inventory_Modules.find_stack_instances2(credential, credential['Region'], stack['StackSetName'])
                        logging.info(f"Found {len(ListOfStackInstances)} instances for {stack['StackSetName']} in {credential['Region']}, which took {time() - milestone:.2f} seconds")
                    except Exception as e:
                        logging.warning(f"Failed to get instances for {stack['StackSetName']}: {e}")
                        
                All_Results.append({
                    'MgmtAccount': credential['MgmtAccount'],
                    'AccountId': credential['AccountId'],
                    'Region': credential['Region'],
                    'StackSetName': stack['StackSetName'],
                    'Status': stack['Status'],
                    'InstanceNum': len(ListOfStackInstances) if fInstanceCount else 'N/A',
                    'ParentProfile': credential.get('ParentProfile', 'Unknown')
                })
                
        except ClientError as my_Error:
            if 'AuthFailure' in str(my_Error):
                logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']} region")
            else:
                logging.error(f"Error accessing account {credential['AccountId']}: {my_Error}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error for account {credential['AccountId']}: {e}")
            continue
    
    return All_Results

def run(args):
    """Main execution function for CloudFormation StackSets operation"""
    # Get timing context from CLI (if available)
    timing = getattr(args, '_timing_context', None)
    
    # Extract arguments
    pProfiles = args.Profiles
    pRegionList = args.Regions
    pAccounts = args.Accounts
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pAccessRoles = args.AccessRoles
    pRootOnly = args.RootOnly
    pFilename = args.Filename
    pTiming = args.Time
    pFragments = getattr(args, 'pFragments', ['all'])
    pExact = getattr(args, 'pExact', False)
    pStatus = getattr(args, 'pStatus', 'ACTIVE')
    pInstanceCount = getattr(args, 'pInstanceCount', False)
    
    print("Searching for CloudFormation StackSets...")
    print(f"Operation version: {__version__}")
    print(f"Looking for stacksets with fragments: {Fore.RED}{pFragments}{Fore.RESET}")
    print(f"Status filter: {Fore.RED}{pStatus}{Fore.RESET}")
    if pInstanceCount:
        print(f"Including {Fore.RED}instance counts{Fore.RESET} for each stackset")
    if pExact:
        print(f"Using {Fore.RED}exact match{Fore.RESET} for stackset names")
    else:
        print(f"Using {Fore.RED}contains match{Fore.RESET} for stackset names")
    
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
    
    # Find all stacksets
    AllStackSets = find_all_cfnstacksets(CredentialList, pFragments, pStatus, pInstanceCount)
    
    if timing:
        timing.milestone("stacksets_found", f"Found {len(AllStackSets)} CloudFormation StackSets")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'Status': {'DisplayOrder': 5, 'Heading': 'Status'},
        'StackSetName': {'DisplayOrder': 6, 'Heading': 'StackSet Name'}
    }
    
    if pInstanceCount:
        display_dict['InstanceNum'] = {'DisplayOrder': 7, 'Heading': '# of Instances'}

    sorted_stacksets = sorted(AllStackSets, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['Region'], d['StackSetName']
    ))
    
    display_results(sorted_stacksets, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllStackSets)} CloudFormation StackSets across {AccountNum} accounts and {RegionNum} regions")