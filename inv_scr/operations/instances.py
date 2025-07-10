#!/usr/bin/env python3
"""
EC2 Instances inventory operation
"""

import logging
from queue import Queue
from threading import Thread
from time import time
from tqdm.auto import tqdm
from botocore.exceptions import ClientError
from colorama import Fore

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

__version__ = "2025.07.10"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('instances', 'EC2 instances specific options')
    local.add_argument(
        "-s", "--status",
        dest="pStatus",
        choices=['running', 'stopped'],
        type=str,
        default=None,
        help="Filter instances by status: 'running' or 'stopped'. Default shows both"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"EC2 Instances operation version {__version__}"
    )

def find_all_instances(fAllCredentials: list, fStatus: str = None) -> list:
    """
    Find all EC2 instances from all accounts/regions within the credentials supplied
    """
    
    class FindInstances(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials = self.queue.get()
                logging.info(f"Processing account {c_account_credentials['AccountId']}")
                try:
                    Instances = Inventory_Modules.find_account_instances2(c_account_credentials)
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(Instances['Reservations'])} reservations")
                    
                    if 'Reservations' in Instances.keys():
                        for reservation in Instances['Reservations']:
                            for instance in reservation['Instances']:
                                InstanceType = instance['InstanceType']
                                InstanceId = instance['InstanceId']
                                PublicDnsName = instance.get('PublicDnsName', "No Public DNS Name")
                                State = instance['State']['Name']
                                Name = "No Name Tag"
                                
                                # Extract Name tag if it exists
                                if 'Tags' in instance:
                                    for tag in instance['Tags']:
                                        if tag['Key'] == "Name":
                                            Name = tag['Value']
                                            break
                                
                                # Filter by status if specified
                                if fStatus is None or fStatus == State:
                                    AllInstances.append({
                                        'MgmtAccount': c_account_credentials['MgmtAccount'],
                                        'AccountId': c_account_credentials['AccountId'],
                                        'Region': c_account_credentials['Region'],
                                        'State': State,
                                        'InstanceType': InstanceType,
                                        'InstanceId': InstanceId,
                                        'PublicDNSName': PublicDnsName,
                                        'ParentProfile': c_account_credentials.get('ParentProfile', 'Unknown'),
                                        'Name': Name,
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
    AllInstances = []
    WorkerThreads = min(len(fAllCredentials), 25)

    pbar = tqdm(
        desc=f'Finding instances from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )

    # Start worker threads
    for x in range(WorkerThreads):
        worker = FindInstances(checkqueue)
        worker.daemon = True
        worker.start()

    # Queue all credentials
    for credential in fAllCredentials:
        checkqueue.put(credential)

    checkqueue.join()
    pbar.close()
    return AllInstances

def run(args):
    """Main execution function for instances operation"""
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
    
    print("Searching for EC2 instances...")
    
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
    
    # Find all instances
    AllInstances = find_all_instances(CredentialList, pStatus)
    
    if timing:
        timing.milestone("instances_found", f"Found {len(AllInstances)} instances")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'InstanceType': {'DisplayOrder': 5, 'Heading': 'Instance Type'},
        'Name': {'DisplayOrder': 6, 'Heading': 'Name'},
        'InstanceId': {'DisplayOrder': 7, 'Heading': 'Instance ID'},
        'PublicDNSName': {'DisplayOrder': 8, 'Heading': 'Public Name'},
        'State': {'DisplayOrder': 9, 'Heading': 'State', 'Condition': ['running']}
    }

    sorted_instances = sorted(AllInstances, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['Region'], d['AccountId']
    ))
    
    display_results(sorted_instances, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllInstances)} instances across {AccountNum} accounts and {RegionNum} regions")
    print(f"Operation version: {__version__}")