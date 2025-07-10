#!/usr/bin/env python3
"""
VPC inventory operation
"""

import logging
from queue import Queue
from threading import Thread
from time import time
from botocore.exceptions import ClientError
from colorama import Fore

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

__version__ = "2025.07.10"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('vpcs', 'VPC specific options')
    local.add_argument(
        "--default",
        dest="pDefault",
        action="store_true",
        default=False,
        help="Show only default VPCs"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"VPC operation version {__version__}"
    )

def find_all_vpcs(fAllCredentials, fDefaultOnly=False):
    """Find all VPCs from all accounts/regions"""
    
    class FindVPCs(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials, c_default, c_PlaceCount = self.queue.get()
                logging.info(f"Processing account {c_account_credentials['AccountId']}")
                try:
                    Vpcs = Inventory_Modules.find_account_vpcs2(c_account_credentials, c_default)
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(Vpcs['Vpcs'])} VPCs")
                    
                    if 'Vpcs' in Vpcs.keys() and len(Vpcs['Vpcs']) > 0:
                        for vpc in Vpcs['Vpcs']:
                            VpcName = "No name defined"
                            VpcId = vpc['VpcId']
                            IsDefault = vpc['IsDefault']
                            CIDRBlockAssociationSet = vpc['CidrBlockAssociationSet']
                            
                            # Extract Name tag if it exists
                            if 'Tags' in vpc:
                                for tag in vpc['Tags']:
                                    if tag['Key'] == "Name":
                                        VpcName = tag['Value']
                                        break
                            
                            # Handle multiple CIDR blocks
                            for cidr_block in CIDRBlockAssociationSet:
                                AllVPCs.append({
                                    'MgmtAccount': c_account_credentials['MgmtAccount'],
                                    'AccountId': c_account_credentials['AccountId'],
                                    'Region': c_account_credentials['Region'],
                                    'CIDR': cidr_block['CidrBlock'],
                                    'VpcId': VpcId,
                                    'IsDefault': IsDefault,
                                    'VpcName': VpcName
                                })
                                
                except KeyError as my_Error:
                    logging.error(f"Account access failed for {c_account_credentials['AccountId']}: {my_Error}")
                except AttributeError as my_Error:
                    logging.error(f"Profile error: {my_Error}")
                except ClientError as my_Error:
                    if "AuthFailure" in str(my_Error):
                        logging.error(f"Authorization failure for account {c_account_credentials['AccountId']} in {c_account_credentials['Region']}")
                    else:
                        logging.error(f"AWS API error: {my_Error}")
                finally:
                    print(".", end='')
                    self.queue.task_done()

    # Initialize shared variables
    checkqueue = Queue()
    AllVPCs = []
    PlaceCount = 0
    WorkerThreads = min(len(fAllCredentials), 25)
    ERASE_LINE = '\x1b[2K'

    # Start worker threads
    for x in range(WorkerThreads):
        worker = FindVPCs(checkqueue)
        worker.daemon = True
        worker.start()

    # Queue all credentials
    for credential in fAllCredentials:
        print(f"{ERASE_LINE}Checking {credential['AccountId']} in region {credential['Region']} - {PlaceCount + 1} / {len(fAllCredentials)}", end='\r')
        checkqueue.put((credential, fDefaultOnly, PlaceCount))
        PlaceCount += 1

    checkqueue.join()
    return AllVPCs

def run(args):
    """Main execution function for VPCs operation"""
    # Get timing context from CLI (if available)
    timing = getattr(args, '_timing_context', None)
    
    # Extract arguments
    pProfiles = args.Profiles
    pRegionList = args.Regions
    pAccounts = args.Accounts
    pRoles = args.AccessRoles
    pSkipProfiles = args.SkipProfiles
    pSkipAccounts = args.SkipAccounts
    pRootOnly = args.RootOnly
    pTiming = args.Time
    pFilename = args.Filename
    pDefault = getattr(args, 'pDefault', False)
    
    ERASE_LINE = '\x1b[2K'
    
    if pProfiles is not None:
        print(f"Searching for VPCs in profile{'s' if len(pProfiles) > 1 else ''} {pProfiles}")
    else:
        print("Searching for VPCs in default profile")
    print(f"Operation version: {__version__}")

    if timing:
        timing.milestone("args_parsed", "Arguments parsed and validated")

    # Get credentials
    AllCredentials = get_all_credentials(
        pProfiles, pTiming, pSkipProfiles, pSkipAccounts, 
        pRootOnly, pAccounts, pRegionList, pRoles
    )
    
    AllRegionsList = list(set([x['Region'] for x in AllCredentials]))
    AllAccountList = list(set([x['AccountId'] for x in AllCredentials]))
    
    if timing:
        timing.milestone("credentials_setup", f"Credential setup for {len(AllAccountList)} accounts across {len(AllRegionsList)} regions")
    
    # Find VPCs
    All_VPCs_Found = find_all_vpcs(AllCredentials, pDefault)
    
    if timing:
        timing.milestone("vpcs_found", f"Found {len(All_VPCs_Found)} VPC entries")
    
    # Display results
    display_dict = {
        'MgmtAccount': {'DisplayOrder': 1, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 2, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 3, 'Heading': 'Region'},
        'VpcName': {'DisplayOrder': 4, 'Heading': 'VPC Name'},
        'CIDR': {'DisplayOrder': 5, 'Heading': 'CIDR Block'},
        'IsDefault': {'DisplayOrder': 6, 'Heading': 'Default VPC', 'Condition': [True, 1, '1']},
        'VpcId': {'DisplayOrder': 7, 'Heading': 'VPC Id'}
    }

    sorted_AllVPCs = sorted(All_VPCs_Found, key=lambda d: (
        d['MgmtAccount'], d['AccountId'], d['Region'], d['VpcName'], d['CIDR']
    ))
    
    print()
    display_results(sorted_AllVPCs, display_dict, None, pFilename)

    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(ERASE_LINE)
    # Count unique VPCs (some may appear multiple times due to multiple CIDR ranges)
    Num_of_unique_VPCs = len(set([x['VpcId'] for x in sorted_AllVPCs]))
    print(f"Found {Num_of_unique_VPCs}{' default' if pDefault else ''} VPCs across {len(AllAccountList)} accounts and {len(AllRegionsList)} regions")