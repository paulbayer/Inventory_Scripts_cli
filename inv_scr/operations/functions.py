#!/usr/bin/env python3
"""
Lambda Functions inventory operation
"""

import logging
from queue import Queue
from threading import Thread
from time import time
from tqdm.auto import tqdm
from botocore.exceptions import ClientError
from colorama import Fore, init

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

init()
__version__ = "2025.07.10"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('functions', 'Lambda Functions specific options')
    local.add_argument(
        "-f", "--fragment",
        dest="pFragments",
        nargs='*',
        metavar="string fragment",
        default=["all"],
        help="List of fragments of the function name(s) you want to check for."
    )
    local.add_argument(
        "-e", "--exact",
        dest="pExact",
        action="store_true",
        help="Use this flag to make sure that ONLY the string you specified will be identified"
    )
    local.add_argument(
        "--runtime", "--run", "--rt",
        dest="pRuntime",
        nargs="*",
        metavar="language and version",
        default=None,
        help="Language runtime(s) you're looking for within your accounts"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"Lambda Functions operation version {__version__}"
    )

def find_all_lambda_functions(fAllCredentials: list, fFragments: list = None) -> list:
    """
    Find all Lambda functions from all accounts/regions within the credentials supplied
    """
    
    class FindFunctions(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials, c_fragment_list = self.queue.get()
                logging.info(f"De-queued info for account {c_account_credentials['AccountId']}")
                try:
                    Functions = Inventory_Modules.find_lambda_functions2(c_account_credentials, c_account_credentials['Region'], c_fragment_list)
                    function_count = len(Functions) if Functions else 0
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {function_count} functions")
                    
                    if Functions:
                        for function in Functions:
                            function['MgmtAccount'] = c_account_credentials['MgmtAccount']
                            function['AccountId'] = c_account_credentials['AccountId']
                            function['Region'] = c_account_credentials['Region']
                            function['ParentProfile'] = c_account_credentials.get('ParentProfile', 'Unknown')
                            # Clean up the Role ARN to just show the role name
                            if 'Role' in function:
                                role_arn = function['Role']
                                if '/' in role_arn:
                                    function['Role'] = role_arn[role_arn.find("/") + 1:]
                        AllFunctions.extend(Functions)
                        
                except KeyError as my_Error:
                    logging.error(f"Account Access failed - trying to access {c_account_credentials['AccountId']}")
                    logging.info(f"Actual Error: {my_Error}")
                    pass
                except AttributeError as my_Error:
                    logging.error(f"Error: Likely that one of the supplied profiles was wrong")
                    logging.warning(my_Error)
                    continue
                except ClientError as my_Error:
                    if 'AuthFailure' in str(my_Error):
                        logging.error(f"Authorization Failure accessing account {c_account_credentials['AccountId']} in {c_account_credentials['Region']} region")
                        logging.warning(f"It's possible that the region {c_account_credentials['Region']} hasn't been opted-into")
                        continue
                    else:
                        logging.error(f"Error: Likely throttling errors from too much activity")
                        logging.warning(my_Error)
                        continue
                finally:
                    pbar.update()
                    self.queue.task_done()

    ###########

    checkqueue = Queue()
    AllFunctions = []
    WorkerThreads = min(len(fAllCredentials), 25)

    pbar = tqdm(
        desc=f'Finding Lambda functions from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )

    for x in range(WorkerThreads):
        worker = FindFunctions(checkqueue)
        worker.daemon = True
        worker.start()

    for credential in fAllCredentials:
        logging.info(f"Beginning to queue data - starting with {credential['AccountId']}")
        try:
            checkqueue.put((credential, fFragments))
        except ClientError as my_Error:
            if "AuthFailure" in str(my_Error):
                logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']} region")
                logging.warning(f"It's possible that the region {credential['Region']} hasn't been opted-into")
                pass
    checkqueue.join()
    pbar.close()
    return AllFunctions

def run(args):
    """Main execution function for Lambda functions operation"""
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
    pRuntime = getattr(args, 'pRuntime', None)
    
    print("Searching for Lambda functions...")
    print(f"Looking for functions with fragments: {Fore.RED}{pFragments}{Fore.RESET}")
    if pRuntime:
        print(f"Filtering by runtime: {Fore.RED}{pRuntime}{Fore.RESET}")
    if pExact:
        print(f"Using {Fore.RED}exact match{Fore.RESET} for function names")
    else:
        print(f"Using {Fore.RED}contains match{Fore.RESET} for function names")
    
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
    
    # Combine fragments and runtime filters
    full_list_to_look_for = pFragments + pRuntime if pRuntime is not None else pFragments
    
    # Find all functions
    AllFunctions = find_all_lambda_functions(CredentialList, full_list_to_look_for)
    
    if timing:
        timing.milestone("functions_found", f"Found {len(AllFunctions)} Lambda functions")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'FunctionName': {'DisplayOrder': 5, 'Heading': 'Function Name'},
        'Runtime': {'DisplayOrder': 6, 'Heading': 'Runtime'},
        'Role': {'DisplayOrder': 7, 'Heading': 'Role'}
    }

    # Apply runtime filtering to display if specified
    if pRuntime is not None:
        display_dict['Runtime']['Condition'] = pRuntime

    sorted_functions = sorted(AllFunctions, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['Region'], d['FunctionName']
    ))
    
    display_results(sorted_functions, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllFunctions)} Lambda functions across {AccountNum} accounts and {RegionNum} regions")
    print(f"Operation version: {__version__}")