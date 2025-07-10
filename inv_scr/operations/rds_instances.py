#!/usr/bin/env python3
"""
RDS Instances inventory operation
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
    local = parser.my_parser.add_argument_group('rds-instances', 'RDS Instances specific options')
    local.add_argument(
        "-f", "--fragment",
        dest="pFragments",
        nargs='*',
        metavar="string fragment",
        default=["all"],
        help="List of fragments of the RDS instance name(s) you want to check for."
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
        version=f"RDS Instances operation version {__version__}"
    )

def uniquify_list(non_unique_list: list) -> list:
    """
    This function takes a list of results and returns a list of unique results
    """
    unique_ids = []
    unique_items = []
    for item in non_unique_list:
        if item['DBId'] not in unique_ids:
            unique_ids.append(item['DBId'])
            unique_items.append(item)
    return unique_items

def find_all_rds_instances(fAllCredentials: list) -> list:
    """
    Find all RDS instances from all accounts/regions within the credentials supplied
    """
    
    class FindRDSInstances(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials = self.queue.get()
                logging.info(f"De-queued info for account number {c_account_credentials['AccountId']}")
                try:
                    DBInstances = Inventory_Modules.find_account_rds_instances2(c_account_credentials)
                    instance_count = len(DBInstances['DBInstances']) if 'DBInstances' in DBInstances else 0
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {instance_count} RDS instances")
                    
                    if 'DBInstances' in DBInstances.keys():
                        for RDSinstance in DBInstances['DBInstances']:
                            Name = RDSinstance.get('DBName', 'No Name')
                            LastBackup = RDSinstance.get('LatestRestorableTime', 'No Backups')
                            AllRDSInstances.append({
                                'MgmtAccount': c_account_credentials['MgmtAccount'],
                                'AccountNumber': c_account_credentials['AccountId'],
                                'Region': c_account_credentials['Region'],
                                'ParentProfile': c_account_credentials.get('ParentProfile', 'Unknown'),
                                'InstanceType': RDSinstance['DBInstanceClass'],
                                'State': RDSinstance['DBInstanceStatus'],
                                'DBId': RDSinstance['DBInstanceIdentifier'],
                                'Name': Name,
                                'Size': RDSinstance['AllocatedStorage'],
                                'LastBackup': LastBackup,
                                'Engine': RDSinstance['Engine']
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
                    elif my_Error.response['Error']['Code'] == 'AccessDenied':
                        logging.warning(f"Authorization Failure accessing account {c_account_credentials['AccountId']} in {c_account_credentials['Region']} region")
                        logging.warning(f"It's likely there's an SCP blocking access to this {c_account_credentials['AccountId']} account")
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
    AllRDSInstances = []
    WorkerThreads = min(len(fAllCredentials), 25)

    pbar = tqdm(
        desc=f'Finding RDS instances from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )

    for x in range(WorkerThreads):
        worker = FindRDSInstances(checkqueue)
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
    return AllRDSInstances

def run(args):
    """Main execution function for RDS instances operation"""
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
    
    print("Searching for RDS instances...")
    print(f"Looking for RDS instances with fragments: {Fore.RED}{pFragments}{Fore.RESET}")
    if pExact:
        print(f"Using {Fore.RED}exact match{Fore.RESET} for RDS instance names")
    else:
        print(f"Using {Fore.RED}contains match{Fore.RESET} for RDS instance names")
    
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
    
    # Find all RDS instances
    AllRDSInstances = find_all_rds_instances(CredentialList)
    
    # Remove duplicates
    sorted_results = sorted(AllRDSInstances, key=lambda d: (d['MgmtAccount'], d['AccountNumber'], d['Region'], d['DBId']))
    unique_results = uniquify_list(sorted_results)
    
    if timing:
        timing.milestone("rds_instances_found", f"Found {len(unique_results)} unique RDS instances")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountNumber': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'InstanceType': {'DisplayOrder': 5, 'Heading': 'Instance Type'},
        'Name': {'DisplayOrder': 6, 'Heading': 'DB Name'},
        'DBId': {'DisplayOrder': 7, 'Heading': 'Database ID'},
        'Engine': {'DisplayOrder': 8, 'Heading': 'DB Engine'},
        'Size': {'DisplayOrder': 9, 'Heading': 'Size (GB)'},
        'LastBackup': {'DisplayOrder': 10, 'Heading': 'Latest Backup'},
        'State': {'DisplayOrder': 11, 'Heading': 'State', 'Condition': ['Failed', 'Deleting', 'Maintenance', 'Rebooting', 'Upgrading']}
    }

    display_results(unique_results, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    # Count instances by engine and state
    engine_counts = {}
    state_counts = {}
    for instance in unique_results:
        engine = instance.get('Engine', 'Unknown')
        state = instance.get('State', 'Unknown')
        engine_counts[engine] = engine_counts.get(engine, 0) + 1
        state_counts[state] = state_counts.get(state, 0) + 1
    
    print(f"\nFound {len(unique_results)} RDS instances across {AccountNum} accounts and {RegionNum} regions")
    if engine_counts:
        print("Engine distribution:")
        for engine, count in sorted(engine_counts.items()):
            print(f"  - {engine}: {count}")
    if state_counts:
        print("State distribution:")
        for state, count in sorted(state_counts.items()):
            print(f"  - {state}: {count}")
    print(f"Operation version: {__version__}")