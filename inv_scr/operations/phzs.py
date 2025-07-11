#!/usr/bin/env python3
"""Private Hosted Zones inventory operation"""

import logging
from queue import Queue
from threading import Thread
from tqdm.auto import tqdm
from botocore.exceptions import ClientError

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

__version__ = "2025.07.11"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('phzs', 'Private Hosted Zones specific options')
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"Private Hosted Zones operation version {__version__}"
    )

def find_all_hosted_zones(fAllCredentials: list) -> list:
    """
    Find all private hosted zones from all accounts within the credentials supplied
    """
    
    class FindZones(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials = self.queue.get()
                logging.info(f"Processing account {c_account_credentials['AccountId']}")
                try:
                    HostedZones = Inventory_Modules.find_private_hosted_zones2(c_account_credentials, c_account_credentials['Region'])
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(HostedZones['HostedZones'])} zones")

                    for zone in HostedZones['HostedZones']:
                        AllHostedZones.append({
                            'ParentProfile': c_account_credentials.get('ParentProfile', 'Unknown'),
                            'MgmtAccount': c_account_credentials['MgmtAccount'],
                            'AccountId': c_account_credentials['AccountId'],
                            'Region': 'Global',  # Route53 hosted zones are global
                            'PHZName': zone['Name'],
                            'Records': zone['ResourceRecordSetCount'],
                            'PHZId': zone['Id']
                        })
                        
                except KeyError as my_Error:
                    logging.error(f"Account access failed for {c_account_credentials['AccountId']}: {my_Error}")
                except AttributeError as my_Error:
                    logging.error(f"Profile error: {my_Error}")
                except ClientError as my_Error:
                    if 'AuthFailure' in str(my_Error):
                        logging.error(f"Authorization failure for account {c_account_credentials['AccountId']} in {c_account_credentials['Region']}")
                    else:
                        logging.error(f"AWS API error: {my_Error}")
                finally:
                    pbar.update()
                    self.queue.task_done()

    # Initialize shared variables
    checkqueue = Queue()
    AllHostedZones = []
    WorkerThreads = min(len(fAllCredentials), 25)

    pbar = tqdm(
        desc=f'Finding hosted zones from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )

    # Start worker threads
    for x in range(WorkerThreads):
        worker = FindZones(checkqueue)
        worker.daemon = True
        worker.start()

    # Queue all credentials
    for credential in fAllCredentials:
        checkqueue.put(credential)

    checkqueue.join()
    pbar.close()
    return AllHostedZones

def run(args):
    """Main execution function for phzs operation"""
    # Get timing context from CLI (if available)
    timing = getattr(args, '_timing_context', None)
    
    # Extract arguments
    pProfiles = args.Profiles
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pAccounts = args.Accounts
    pRootOnly = args.RootOnly
    pFilename = args.Filename
    pTiming = args.Time
    
    print("Searching for Private Hosted Zones...")
    print(f"Operation version: {__version__}")
    
    if timing:
        timing.milestone("args_parsed", "Arguments parsed and validated")
    
    # Get credentials for all accounts (PHZs don't need regions, but we'll use the credential system)
    CredentialList = get_all_credentials(
        pProfiles, pTiming, pSkipProfiles, pSkipAccounts, 
        pRootOnly, pAccounts
    )
    
    AccountNum = len(set([acct['AccountId'] for acct in CredentialList]))
    
    print(f"Searching {AccountNum} accounts globally")
    
    if timing:
        timing.milestone("credentials_setup", f"Credential setup for {AccountNum} accounts")
    
    # Find all hosted zones
    AllHostedZones = find_all_hosted_zones(CredentialList)
    
    if timing:
        timing.milestone("zones_found", f"Found {len(AllHostedZones)} hosted zones")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'PHZName': {'DisplayOrder': 5, 'Heading': 'Zone Name'},
        'Records': {'DisplayOrder': 6, 'Heading': '# of Records'},
        'PHZId': {'DisplayOrder': 7, 'Heading': 'Zone ID'}
    }

    sorted_zones = sorted(AllHostedZones, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['PHZName']
    ))
    
    display_results(sorted_zones, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllHostedZones)} Private Hosted Zones across {AccountNum} accounts globally")