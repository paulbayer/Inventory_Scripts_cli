#!/usr/bin/env python3
"""VPC Subnets inventory operation"""

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
    local = parser.my_parser.add_argument_group('subnets', 'VPC Subnets specific options')
    local.add_argument(
        "--ipaddress", "--ip",
        dest="pipaddresses",
        nargs="*",
        metavar="IP address",
        default=None,
        help="IP address(es) you're looking for within your VPCs"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"VPC Subnets operation version {__version__}"
    )

def find_all_subnets(fAllCredentials: list, fip: list = None) -> list:
    """
    Find all VPC subnets from all accounts/regions within the credentials supplied
    """
    
    class FindSubnets(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials = self.queue.get()
                logging.info(f"Processing account {c_account_credentials['AccountId']}")
                try:
                    account_subnets = Inventory_Modules.find_account_subnets2(c_account_credentials, fip)
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(account_subnets['Subnets'])} subnets")
                    
                    for subnet in account_subnets['Subnets']:
                        subnet['MgmtAccount'] = c_account_credentials['MgmtAccount']
                        subnet['AccountId'] = c_account_credentials['AccountId']
                        subnet['Region'] = c_account_credentials['Region']
                        subnet['ParentProfile'] = c_account_credentials.get('ParentProfile', 'Unknown')
                        subnet['SubnetName'] = "None"
                        
                        # Extract Name tag if it exists
                        if 'Tags' in subnet:
                            for tag in subnet['Tags']:
                                if tag['Key'] == 'Name':
                                    subnet['SubnetName'] = tag['Value']
                                    break
                        
                        subnet['VPCId'] = subnet.get('VpcId', None)
                        AllSubnets.append(subnet)
                        
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
    AllSubnets = []
    WorkerThreads = min(len(fAllCredentials), 25)

    pbar = tqdm(
        desc=f'Finding subnets from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )

    # Start worker threads
    for x in range(WorkerThreads):
        worker = FindSubnets(checkqueue)
        worker.daemon = True
        worker.start()

    # Queue all credentials
    for credential in fAllCredentials:
        checkqueue.put(credential)

    checkqueue.join()
    pbar.close()
    return AllSubnets

def run(args):
    """Main execution function for subnets operation"""
    # Get timing context from CLI (if available)
    timing = getattr(args, '_timing_context', None)
    
    # Extract arguments
    pProfiles = args.Profiles
    pRegionList = args.Regions
    pAccounts = args.Accounts
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pAccessRoles = args.AccessRoles
    pIPaddressList = getattr(args, 'pipaddresses', None)
    pRootOnly = args.RootOnly
    pFilename = args.Filename
    pTiming = args.Time
    
    print("Searching for VPC subnets...")
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
    
    # Find all subnets
    AllSubnets = find_all_subnets(CredentialList, pIPaddressList)
    
    if timing:
        timing.milestone("subnets_found", f"Found {len(AllSubnets)} subnets")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'VPCId': {'DisplayOrder': 5, 'Heading': 'VPC ID'},
        'SubnetName': {'DisplayOrder': 6, 'Heading': 'Subnet Name'},
        'CidrBlock': {'DisplayOrder': 7, 'Heading': 'CIDR Block'},
        'AvailableIpAddressCount': {'DisplayOrder': 8, 'Heading': 'Available IPs'}
    }

    sorted_subnets = sorted(AllSubnets, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['Region'], d['SubnetName']
    ))
    
    display_results(sorted_subnets, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllSubnets)} subnets across {AccountNum} accounts and {RegionNum} regions")