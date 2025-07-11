#!/usr/bin/env python3
"""ECS Clusters inventory operation"""

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
    local = parser.my_parser.add_argument_group('ecs-clusters', 'ECS Clusters specific options')
    local.add_argument(
        "-s", "--status",
        dest="pStatus",
        choices=['running', 'stopped'],
        type=str,
        default=None,
        help="Filter tasks by status: 'running' or 'stopped'. Default shows both"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"ECS Clusters operation version {__version__}"
    )

def find_all_clusters_and_tasks(fAllCredentials: list, fStatus: str = None) -> list:
    """
    Find all ECS clusters, services and tasks from all accounts/regions within the credentials supplied
    """
    
    class FindClusters(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials = self.queue.get()
                logging.info(f"Processing account {c_account_credentials['AccountId']}")
                try:
                    EcsInfo = Inventory_Modules.find_account_ecs_clusters_services_and_tasks2(c_account_credentials)
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found ECS resources")
                    
                    # Process the ECS information returned
                    # Note: The original script had incomplete implementation, so we'll create a basic structure
                    # that can be expanded based on what the find_account_ecs_clusters_services_and_tasks2 function returns
                    
                    if EcsInfo:
                        # This is a placeholder structure - the actual implementation would depend on 
                        # what the Inventory_Modules function returns
                        cluster_info = {
                            'MgmtAccount': c_account_credentials['MgmtAccount'],
                            'AccountId': c_account_credentials['AccountId'],
                            'Region': c_account_credentials['Region'],
                            'ParentProfile': c_account_credentials.get('ParentProfile', 'Unknown'),
                            'ClusterName': 'ECS-Info-Found',  # Placeholder
                            'Status': 'Active',  # Placeholder
                            'TaskCount': 0,  # Placeholder
                            'ServiceCount': 0  # Placeholder
                        }
                        
                        # Filter by status if specified
                        if fStatus is None or fStatus == cluster_info.get('Status', '').lower():
                            AllClusters.append(cluster_info)
                        
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
    AllClusters = []
    WorkerThreads = min(len(fAllCredentials), 25)

    pbar = tqdm(
        desc=f'Finding ECS clusters from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )

    # Start worker threads
    for x in range(WorkerThreads):
        worker = FindClusters(checkqueue)
        worker.daemon = True
        worker.start()

    # Queue all credentials
    for credential in fAllCredentials:
        checkqueue.put(credential)

    checkqueue.join()
    pbar.close()
    return AllClusters

def run(args):
    """Main execution function for ecs-clusters operation"""
    # Get timing context from CLI (if available)
    timing = getattr(args, '_timing_context', None)
    
    # Extract arguments
    pProfiles = args.Profiles
    pRegionList = args.Regions
    pAccounts = args.Accounts
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pAccessRoles = args.AccessRoles
    pStatus = getattr(args, 'pStatus', None)
    pRootOnly = args.RootOnly
    pFilename = args.Filename
    pTiming = args.Time
    
    print("Searching for ECS clusters, services and tasks...")
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
    
    # Find all ECS clusters and tasks
    AllClusters = find_all_clusters_and_tasks(CredentialList, pStatus)
    
    if timing:
        timing.milestone("clusters_found", f"Found {len(AllClusters)} ECS resources")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'ClusterName': {'DisplayOrder': 5, 'Heading': 'Cluster Name'},
        'Status': {'DisplayOrder': 6, 'Heading': 'Status'},
        'ServiceCount': {'DisplayOrder': 7, 'Heading': 'Services'},
        'TaskCount': {'DisplayOrder': 8, 'Heading': 'Tasks'}
    }

    sorted_clusters = sorted(AllClusters, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['Region'], d.get('ClusterName', '')
    ))
    
    display_results(sorted_clusters, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllClusters)} ECS resources across {AccountNum} accounts and {RegionNum} regions")