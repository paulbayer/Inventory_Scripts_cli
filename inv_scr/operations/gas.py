#!/usr/bin/env python3
"""Global Accelerator inventory operation"""

import logging
from queue import Queue
from threading import Thread
from tqdm.auto import tqdm
from botocore.exceptions import ClientError
from itertools import chain

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

__version__ = "2025.07.11"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('gas', 'Global Accelerator specific options')
    local.add_argument(
        "-s", "--status",
        dest="pstatus",
        metavar="Global Accelerator Status",
        choices=['DEPLOYED', 'IN_PROGRESS', 'all'],
        default="all",
        help="Filter by Global Accelerator status: 'DEPLOYED', 'IN_PROGRESS', or 'all'"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"Global Accelerator operation version {__version__}"
    )

def find_all_global_accelerators(fAllCredentials: list) -> list:
    """
    Find all Global Accelerators from all accounts within the credentials supplied
    """
    
    class FindGlobalAccelerators(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials = self.queue.get()
                logging.info(f"Processing account {c_account_credentials['AccountId']}")
                try:
                    GlobalAccelerators = Inventory_Modules.find_global_accelerators2(c_account_credentials)
                    logging.info(f"Account: {c_account_credentials['AccountId']} | Found {len(GlobalAccelerators)} global accelerators")
                    
                    for ga in GlobalAccelerators:
                        AllGlobalAccelerators.append({
                            'MgmtAccount': c_account_credentials['MgmtAccount'],
                            'AccountId': c_account_credentials['AccountId'],
                            'Region': 'Global',  # Global Accelerator is a global service
                            'ParentProfile': c_account_credentials.get('ParentProfile', 'Unknown'),
                            'Enabled': ga['Enabled'],
                            'IpSets': ga['IpSets'],
                            'IpAddresses': list(chain(*[_['IpAddresses'] for _ in ga['IpSets']])),
                            'Name': ga['Name'],
                            'Status': ga['Status'],
                            'DNSName': ga['DnsName'],
                            'Listeners': ga.get('Listeners', [])
                        })
                        
                except KeyError as my_Error:
                    logging.error(f"Account access failed for {c_account_credentials['AccountId']}: {my_Error}")
                except AttributeError as my_Error:
                    logging.error(f"Profile error: {my_Error}")
                except ClientError as my_Error:
                    if my_Error.response['Error']['Code'] == 'AccessDeniedException':
                        logging.error(f"Access Denied Error: {my_Error}")
                    elif 'AuthFailure' in str(my_Error):
                        logging.error(f"Authorization failure for account {c_account_credentials['AccountId']}")
                    else:
                        logging.error(f"AWS API error: {my_Error}")
                finally:
                    pbar.update()
                    self.queue.task_done()

    # Initialize shared variables
    checkqueue = Queue()
    AllGlobalAccelerators = []
    WorkerThreads = min(len(fAllCredentials), 4)  # Global Accelerator has lower rate limits

    pbar = tqdm(
        desc=f'Finding global accelerators from {len(fAllCredentials)} account{"" if len(fAllCredentials) == 1 else "s"}',
        total=len(fAllCredentials), 
        unit=' accounts'
    )

    # Start worker threads
    for x in range(WorkerThreads):
        worker = FindGlobalAccelerators(checkqueue)
        worker.daemon = True
        worker.start()

    # Queue all credentials
    for credential in fAllCredentials:
        checkqueue.put(credential)

    checkqueue.join()
    pbar.close()
    return AllGlobalAccelerators

def run(args):
    """Main execution function for gas operation"""
    # Get timing context from CLI (if available)
    timing = getattr(args, '_timing_context', None)
    
    # Extract arguments
    pProfiles = args.Profiles
    pAccounts = args.Accounts
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pAccessRoles = args.AccessRoles
    pStatus = getattr(args, 'pstatus', 'all')
    pRootOnly = args.RootOnly
    pFilename = args.Filename
    pTiming = args.Time
    
    print("Searching for Global Accelerators...")
    print(f"Operation version: {__version__}")
    
    if timing:
        timing.milestone("args_parsed", "Arguments parsed and validated")
    
    # Global Accelerator is only available in us-west-2 region
    pRegionList = ['us-west-2']
    
    # Get credentials for all accounts
    CredentialList = get_all_credentials(
        pProfiles, pTiming, pSkipProfiles, pSkipAccounts, 
        pRootOnly, pAccounts, pRegionList, pAccessRoles
    )
    
    AccountNum = len(set([acct['AccountId'] for acct in CredentialList]))
    
    print(f"Searching {AccountNum} account{'s' if AccountNum != 1 else ''} globally")
    
    if timing:
        timing.milestone("credentials_setup", f"Credential setup for {AccountNum} accounts")
    
    # Find all Global Accelerators
    AllGlobalAccelerators = find_all_global_accelerators(CredentialList)
    
    if timing:
        timing.milestone("gas_found", f"Found {len(AllGlobalAccelerators)} Global Accelerators")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Name': {'DisplayOrder': 4, 'Heading': 'Name'},
        'Status': {'DisplayOrder': 5, 'Heading': 'Status'},
        'DNSName': {'DisplayOrder': 6, 'Heading': 'Public Name'},
        'Listeners': {'DisplayOrder': 7, 'Heading': 'Listeners'},
        'Enabled': {'DisplayOrder': 8, 'Heading': 'Enabled'}
    }

    sorted_gas = sorted(AllGlobalAccelerators, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['Name']
    ))
    
    display_results(sorted_gas, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllGlobalAccelerators)} Global Accelerator{'s' if len(AllGlobalAccelerators) != 1 else ''} across {AccountNum} account{'s' if AccountNum != 1 else ''}")