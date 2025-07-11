#!/usr/bin/env python3
"""Transit Gateways inventory operation"""

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
    local = parser.my_parser.add_argument_group('tgws', 'Transit Gateways specific options')
    local.add_argument(
        "--type",
        nargs="*",
        choices=['tgw', 'vpc', 'attach', 'rt', 'all'],
        default=['all'],
        help="Which types of resources you want identified: tgw, vpc, attach, rt, or all",
        dest="ResourceTypes",
        action="store"
    )
    local.add_argument(
        "--diagram", "--diag",
        help="Whether to output a diagram for the TGWs and attachments",
        dest="DrawNetworkDiagram",
        action="store_true"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"Transit Gateways operation version {__version__}"
    )

def find_all_tgws(fAllCredentials: list) -> list:
    """
    Find all Transit Gateways from all accounts/regions within the credentials supplied
    """
    
    class FindTGWs(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials = self.queue.get()
                logging.info(f"Processing account {c_account_credentials['AccountId']}")
                try:
                    org_tgws = Inventory_Modules.find_tgws2(c_account_credentials)
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(org_tgws)} TGWs")
                    
                    for tgw in org_tgws:
                        tgw['MgmtAccount'] = c_account_credentials['MgmtAccount']
                        tgw['AccountId'] = c_account_credentials['AccountId']
                        tgw['Region'] = c_account_credentials['Region']
                        tgw['ParentProfile'] = c_account_credentials.get('ParentProfile', 'Unknown')
                        tgw['credentials'] = c_account_credentials
                        tgw['TGWName'] = "None"
                        
                        # Extract Name tag if it exists
                        if 'Tags' in tgw:
                            for tag in tgw['Tags']:
                                if tag['Key'] == 'Name':
                                    tgw['TGWName'] = tag['Value']
                                    break
                    
                    AllTGWs.extend(org_tgws)
                    
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
    AllTGWs = []
    WorkerThreads = min(len(fAllCredentials), 25)

    pbar = tqdm(
        desc=f'Finding TGWs from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )

    # Start worker threads
    for x in range(WorkerThreads):
        worker = FindTGWs(checkqueue)
        worker.daemon = True
        worker.start()

    # Queue all credentials
    for credential in fAllCredentials:
        checkqueue.put(credential)

    checkqueue.join()
    pbar.close()
    return AllTGWs

def find_all_vpcs(fAllCredentials: list) -> list:
    """
    Find all VPCs from all accounts/regions within the credentials supplied
    """
    
    class FindVPCs(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials = self.queue.get()
                logging.info(f"Processing account {c_account_credentials['AccountId']}")
                try:
                    account_vpcs = Inventory_Modules.find_account_vpcs2(c_account_credentials)
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(account_vpcs['Vpcs'])} VPCs")
                    
                    for vpc in account_vpcs['Vpcs']:
                        vpc['MgmtAccount'] = c_account_credentials['MgmtAccount']
                        vpc['AccountId'] = c_account_credentials['AccountId']
                        vpc['Region'] = c_account_credentials['Region']
                        vpc['ParentProfile'] = c_account_credentials.get('ParentProfile', 'Unknown')
                        vpc['VpcName'] = "None"
                        vpc['credentials'] = c_account_credentials
                        
                        # Extract Name tag if it exists
                        if 'Tags' in vpc:
                            for tag in vpc['Tags']:
                                if tag['Key'] == 'Name':
                                    vpc['VpcName'] = tag['Value']
                                    break
                    
                    AllVPCs.extend(account_vpcs['Vpcs'])
                    
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
    AllVPCs = []
    WorkerThreads = min(len(fAllCredentials), 25)

    pbar = tqdm(
        desc=f'Finding VPCs from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )

    # Start worker threads
    for x in range(WorkerThreads):
        worker = FindVPCs(checkqueue)
        worker.daemon = True
        worker.start()

    # Queue all credentials
    for credential in fAllCredentials:
        checkqueue.put(credential)

    checkqueue.join()
    pbar.close()
    return AllVPCs

def combine_all_resources(VPCList: list, TGWList: list, AttachmentList: list = None, RouteTableList: list = None):
    """
    Combines all resources into a single list for display
    """
    AllResources = []
    
    # Add VPCs
    for item in VPCList:
        AllResources.append({
            'ParentProfile': item.get('ParentProfile', 'Unknown'),
            'MgmtAccount': item['MgmtAccount'],
            'AccountId': item['AccountId'],
            'Region': item['Region'],
            'Type': "VPC",
            'ResourceId': item['VpcId'],
            'Name': item['VpcName'],
            'TgwId': 'N/A'
        })
    
    # Add TGWs
    for item in TGWList:
        AllResources.append({
            'ParentProfile': item.get('ParentProfile', 'Unknown'),
            'MgmtAccount': item['MgmtAccount'],
            'AccountId': item['AccountId'],
            'Region': item['Region'],
            'Type': "TGW",
            'ResourceId': item['TransitGatewayId'],
            'Name': item['TGWName'],
            'TgwId': 'N/A'
        })
    
    # Add Attachments if provided
    if AttachmentList:
        for item in AttachmentList:
            AllResources.append({
                'ParentProfile': item.get('ParentProfile', 'Unknown'),
                'MgmtAccount': item['MgmtAccount'],
                'AccountId': item['AccountId'],
                'Region': item['Region'],
                'Type': "TGW Attachment",
                'ResourceId': item['TransitGatewayAttachmentId'],
                'Name': item.get('AttachmentName', 'None'),
                'TgwId': item['TransitGatewayId']
            })
    
    # Add Route Tables if provided
    if RouteTableList:
        for item in RouteTableList:
            AllResources.append({
                'ParentProfile': item.get('ParentProfile', 'Unknown'),
                'MgmtAccount': item['MgmtAccount'],
                'AccountId': item['AccountId'],
                'Region': item['Region'],
                'Type': "Route Table",
                'ResourceId': item['TransitGatewayRouteTableId'],
                'Name': item.get('RTName', 'None'),
                'TgwId': item['TransitGatewayId']
            })
    
    return sorted(AllResources, key=lambda x: (x['ParentProfile'], x['Region'], x['AccountId'], x['Type'], x['ResourceId']))

def run(args):
    """Main execution function for tgws operation"""
    # Get timing context from CLI (if available)
    timing = getattr(args, '_timing_context', None)
    
    # Extract arguments
    pProfiles = args.Profiles
    pRegionList = args.Regions
    pAccounts = args.Accounts
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pAccessRoles = args.AccessRoles
    pResourceTypes = getattr(args, 'ResourceTypes', ['all'])
    pDrawNetwork = getattr(args, 'DrawNetworkDiagram', False)
    pRootOnly = args.RootOnly
    pFilename = args.Filename
    pTiming = args.Time
    
    print("Searching for Transit Gateways and related resources...")
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
    
    # Find resources based on requested types
    TGWsFound = []
    VPCsFound = []
    
    if any(item in ['tgw', 'all'] for item in pResourceTypes):
        TGWsFound = find_all_tgws(CredentialList)
    
    if any(item in ['vpc', 'all'] for item in pResourceTypes):
        VPCsFound = find_all_vpcs(CredentialList)
    
    # TODO: Implement attachments and route tables finding
    # For now, we'll just combine TGWs and VPCs
    AllResources = combine_all_resources(VPCsFound, TGWsFound)
    
    if timing:
        timing.milestone("resources_found", f"Found {len(AllResources)} resources")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'ResourceId': {'DisplayOrder': 5, 'Heading': 'Resource'},
        'Type': {'DisplayOrder': 6, 'Heading': 'Type'},
        'Name': {'DisplayOrder': 7, 'Heading': 'Name'},
        'TgwId': {'DisplayOrder': 8, 'Heading': 'Connected TGW'}
    }

    display_results(AllResources, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    if pDrawNetwork:
        print("Network diagram generation not yet implemented in this version")
    
    print(f"\nFound {len(AllResources)} resources across {AccountNum} accounts and {RegionNum} regions")