#!/usr/bin/env python3
"""
CloudFormation Stacks inventory operation
"""

import logging
from queue import Queue
from threading import Thread
from tqdm.auto import tqdm
from time import time
from botocore.exceptions import ClientError
from colorama import Fore, init

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

init()
__version__ = "2025.07.10"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('cfnstacks', 'CloudFormation stacks specific options')
    local.add_argument(
        "-s", "--status",
        dest="pStatus",
        nargs='*',
        choices=['CREATE_IN_PROGRESS', 'CREATE_FAILED', 'CREATE_COMPLETE', 'ROLLBACK_IN_PROGRESS',
                 'ROLLBACK_FAILED', 'ROLLBACK_COMPLETE', 'DELETE_IN_PROGRESS', 'DELETE_FAILED', 'DELETE_COMPLETE',
                 'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_COMPLETE', 'UPDATE_FAILED',
                 'UPDATE_ROLLBACK_IN_PROGRESS', 'UPDATE_ROLLBACK_FAILED', 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
                 'UPDATE_ROLLBACK_COMPLETE', 'REVIEW_IN_PROGRESS', 'IMPORT_IN_PROGRESS', 'IMPORT_COMPLETE',
                 'IMPORT_ROLLBACK_IN_PROGRESS', 'IMPORT_ROLLBACK_FAILED', 'IMPORT_ROLLBACK_COMPLETE', 'all', 'All', 'ALL'],
        default=None,
        help="List of statuses that determines which statuses we see. Default is all ACTIVE statuses. 'All' will capture all statuses"
    )
    local.add_argument(
        "-f", "--fragment",
        dest="pFragments",
        nargs='*',
        metavar="string fragment",
        default=["all"],
        help="List of fragments of the stack name(s) you want to check for."
    )
    local.add_argument(
        "-e", "--exact",
        dest="pExact",
        action="store_true",
        help="Use this flag to make sure that ONLY the string you specified will be identified"
    )
    local.add_argument(
        "--stackid",
        dest="pStackId",
        action="store_true",
        help="Flag that determines whether we display the Stack IDs as well"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"CloudFormation Stacks operation version {__version__}"
    )

def find_all_cfnstacks(fAllCredentials: list, fStackfrag: list = None, fstatus: list = None, fStackIdFlag: bool = False) -> list:
    """
    Find all CloudFormation stacks from all accounts/regions within the credentials supplied
    """
    
    class FindStacks(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials = self.queue.get()
                logging.info(f"De-queued info for account number {c_account_credentials['AccountId']}")
                try:
                    Stacks = Inventory_Modules.find_stacks2(c_account_credentials, c_account_credentials['Region'], fStackfrag, fstatus)
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(Stacks)} Stacks")
                    
                    if Stacks and len(Stacks) > 0:
                        for stack in Stacks:
                            StackName = stack['StackName']
                            StackStatus = stack['StackStatus']
                            StackID = stack['StackId']
                            StackCreate = stack['CreationTime']
                            AllStacks.append({
                                'MgmtAccount': c_account_credentials['MgmtAccount'],
                                'AccountId': c_account_credentials['AccountId'],
                                'Region': c_account_credentials['Region'],
                                'StackName': StackName,
                                'StackCreate': StackCreate.strftime("%Y-%m-%d"),
                                'StackStatus': StackStatus,
                                'StackArn': StackID if fStackIdFlag else 'None',
                                'ParentProfile': c_account_credentials.get('ParentProfile', 'Unknown')
                            })
                            
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
    AllStacks = []
    WorkerThreads = min(len(fAllCredentials), 25)

    pbar = tqdm(
        desc=f'Finding stacks from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )
    for x in range(WorkerThreads):
        worker = FindStacks(checkqueue)
        worker.daemon = True
        worker.start()

    for credential in fAllCredentials:
        logging.info(f"Beginning to queue data - starting with {credential['AccountId']}")
        try:
            checkqueue.put(credential)
        except ClientError as my_Error:
            if "AuthFailure" in str(my_Error):
                logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']} region")
                logging.warning(f"It's possible that the region {credential['Region']} hasn't been opted-into")
                pass
    checkqueue.join()
    pbar.close()
    return AllStacks

def run(args):
    """Main execution function for CloudFormation stacks operation"""
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
    pStatus = getattr(args, 'pStatus', None)
    pFragments = getattr(args, 'pFragments', ['all'])
    pExact = getattr(args, 'pExact', False)
    pStackId = getattr(args, 'pStackId', False)
    
    print("Searching for CloudFormation stacks...")
    print(f"Operation version: {__version__}")
    print(f"Looking for stacks with fragments: {Fore.RED}{pFragments}{Fore.RESET}")
    if pFragments == ['all']:
        print(f"Matching {Fore.RED}all{Fore.RESET} stack names")
    elif pExact:
        print(f"Matching stacknames{Fore.RED}exactly{Fore.RESET}")
    else:
        print(f"Matching any stackset that {Fore.RED}contains a match{Fore.RESET}")
    
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
    
    # Find all stacks
    AllStacks = find_all_cfnstacks(CredentialList, pFragments, pStatus, pStackId)
    
    if timing:
        timing.milestone("stacks_found", f"Found {len(AllStacks)} CloudFormation stacks")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'StackStatus': {'DisplayOrder': 5, 'Heading': 'Stack Status'},
        'StackCreate': {'DisplayOrder': 6, 'Heading': 'Create Date'},
        'StackName': {'DisplayOrder': 7, 'Heading': 'Stack Name'},
        'StackArn': {'DisplayOrder': 8, 'Heading': 'Stack ID'}
    }

    sorted_stacks = sorted(AllStacks, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['Region'], d['StackName']
    ))
    
    display_results(sorted_stacks, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllStacks)} CloudFormation stacks across {AccountNum} accounts and {RegionNum} region{'' if RegionNum == 1 else 's'}")