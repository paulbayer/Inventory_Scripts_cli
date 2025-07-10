#!/usr/bin/env python3
"""
EBS Volumes inventory operation
"""

import logging
from queue import Queue
from threading import Thread
from time import time
from tqdm.auto import tqdm
from botocore.exceptions import ClientError
from colorama import Fore, init

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results, find_account_volumes2

init()
__version__ = "2025.07.10"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('ebs-volumes', 'EBS Volumes specific options')
    local.add_argument(
        "-f", "--fragment",
        dest="pFragments",
        nargs='*',
        metavar="string fragment",
        default=["all"],
        help="List of fragments of the volume name(s) you want to check for."
    )
    local.add_argument(
        "-e", "--exact",
        dest="pExact",
        action="store_true",
        help="Use this flag to make sure that ONLY the string you specified will be identified"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"EBS Volumes operation version {__version__}"
    )

def find_all_ebs_volumes(fAllCredentials: list, fFragments: list = None) -> list:
    """
    Find all EBS volumes from all accounts/regions within the credentials supplied
    """
    
    class FindVolumes(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials, c_region, c_fragment = self.queue.get()
                logging.info(f"De-queued info for account {c_account_credentials['AccountId']}")
                try:
                    account_volumes = find_account_volumes2(c_account_credentials)
                    volume_count = len(account_volumes) if account_volumes else 0
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {volume_count} volumes")
                    
                    if account_volumes:
                        for volume in account_volumes:
                            volume['MgmtAccount'] = c_account_credentials['MgmtAccount']
                            volume['ParentProfile'] = c_account_credentials.get('ParentProfile', 'Unknown')
                        AllVolumes.extend(account_volumes)
                        
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
    AllVolumes = []
    WorkerThreads = min(len(fAllCredentials), 50)

    pbar = tqdm(
        desc=f'Finding EBS volumes from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )

    for x in range(WorkerThreads):
        worker = FindVolumes(checkqueue)
        worker.daemon = True
        worker.start()

    for credential in fAllCredentials:
        logging.info(f"Beginning to queue data - starting with {credential['AccountId']}")
        try:
            checkqueue.put((credential, credential['Region'], fFragments))
        except ClientError as my_Error:
            if "AuthFailure" in str(my_Error):
                logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']} region")
                logging.warning(f"It's possible that the region {credential['Region']} hasn't been opted-into")
                pass
    checkqueue.join()
    pbar.close()
    return AllVolumes

def run(args):
    """Main execution function for EBS volumes operation"""
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
    
    print("Searching for EBS volumes...")
    print(f"Looking for volumes with fragments: {Fore.RED}{pFragments}{Fore.RESET}")
    if pExact:
        print(f"Using {Fore.RED}exact match{Fore.RESET} for volume names")
    else:
        print(f"Using {Fore.RED}contains match{Fore.RESET} for volume names")
    
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
    
    # Find all volumes
    AllVolumes = find_all_ebs_volumes(CredentialList, pFragments)
    
    if timing:
        timing.milestone("volumes_found", f"Found {len(AllVolumes)} EBS volumes")
    
    # De-duplicate volumes (some may appear multiple times)
    seen = set()
    de_duped_volumes = []
    for volume in AllVolumes:
        key = volume['VolumeId']
        if key not in seen:
            seen.add(key)
            de_duped_volumes.append(volume)
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'VolumeName': {'DisplayOrder': 5, 'Heading': 'Volume Name'},
        'VolumeId': {'DisplayOrder': 6, 'Heading': 'Volume Id'},
        'State': {'DisplayOrder': 7, 'Heading': 'State', 'Condition': ['available', 'creating', 'deleting', 'deleted', 'error']},
        'Size': {'DisplayOrder': 8, 'Heading': 'Size (GBs)'},
        'VolumeType': {'DisplayOrder': 9, 'Heading': 'Type'},
        'Throughput': {'DisplayOrder': 10, 'Heading': 'Throughput'}
    }

    sorted_volumes = sorted(de_duped_volumes, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['Region'], d.get('VolumeName', ''), d.get('Size', 0)
    ))
    
    display_results(sorted_volumes, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    # Calculate orphaned volumes (available or error state)
    orphaned_volumes = [x for x in de_duped_volumes if x.get('State') in ['available', 'error']]
    
    print(f"\nFound {len(de_duped_volumes)} EBS volumes across {AccountNum} accounts and {RegionNum} regions")
    
    if len(orphaned_volumes) > 0:
        print(f"{Fore.RED}Found {len(orphaned_volumes)} volume{'s' if len(orphaned_volumes) != 1 else ''} that aren't attached to anything.")
        print(f"Th{'ese' if len(orphaned_volumes) != 1 else 'is'} {'are' if len(orphaned_volumes) != 1 else 'is'} likely orphaned, and should be considered for deletion to save costs.{Fore.RESET}")
    
    print(f"Operation version: {__version__}")