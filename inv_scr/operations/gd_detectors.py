#!/usr/bin/env python3
"""GuardDuty Detectors inventory operation"""

import logging
import boto3
from queue import Queue
from threading import Thread
from tqdm.auto import tqdm
from botocore.exceptions import ClientError

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

__version__ = "2025.07.11"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('gd-detectors', 'GuardDuty Detectors specific options')
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"GuardDuty Detectors operation version {__version__}"
    )

def find_all_gd_detectors(fAllCredentials: list) -> list:
    """
    Find all GuardDuty detectors from all accounts/regions within the credentials supplied
    """
    
    class FindGDDetectors(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials = self.queue.get()
                logging.info(f"Processing account {c_account_credentials['AccountId']}")
                try:
                    session_aws = boto3.Session(
                        aws_access_key_id=c_account_credentials['AccessKeyId'],
                        aws_secret_access_key=c_account_credentials['SecretAccessKey'],
                        aws_session_token=c_account_credentials['SessionToken'],
                        region_name=c_account_credentials['Region']
                    )
                    client_aws = session_aws.client('guardduty')
                    
                    # List detectors
                    response = client_aws.list_detectors()
                    
                    if len(response['DetectorIds']) > 0:
                        for detector_id in response['DetectorIds']:
                            # Get member accounts for this detector
                            try:
                                admin_acct_response = client_aws.list_members(
                                    DetectorId=detector_id,
                                    OnlyAssociated='False'
                                )
                                member_count = len(admin_acct_response['Members'])
                                is_admin = member_count > 0
                            except ClientError:
                                member_count = 0
                                is_admin = False
                            
                            AllDetectors.append({
                                'MgmtAccount': c_account_credentials['MgmtAccount'],
                                'AccountId': c_account_credentials['AccountId'],
                                'Region': c_account_credentials['Region'],
                                'ParentProfile': c_account_credentials.get('ParentProfile', 'Unknown'),
                                'DetectorId': detector_id,
                                'IsAdminAccount': is_admin,
                                'MemberCount': member_count
                            })
                            
                            logging.info(f"Found detector {detector_id} in account {c_account_credentials['AccountId']} in region {c_account_credentials['Region']}")
                    
                    # List invitations
                    try:
                        invite_response = client_aws.list_invitations()
                        if 'Invitations' in invite_response and invite_response['Invitations']:
                            for invitation in invite_response['Invitations']:
                                AllInvitations.append({
                                    'MgmtAccount': c_account_credentials['MgmtAccount'],
                                    'AccountId': invitation['AccountId'],
                                    'Region': c_account_credentials['Region'],
                                    'ParentProfile': c_account_credentials.get('ParentProfile', 'Unknown'),
                                    'InvitationId': invitation['InvitationId'],
                                    'InvitedAt': invitation.get('InvitedAt', 'Unknown')
                                })
                    except ClientError as e:
                        logging.debug(f"Could not list invitations: {e}")
                        
                except ClientError as my_Error:
                    if "AuthFailure" in str(my_Error):
                        logging.error(f"Authorization failure for account {c_account_credentials['AccountId']} in {c_account_credentials['Region']}")
                    elif "security token included in the request is invalid" in str(my_Error):
                        logging.error(f"Account {c_account_credentials['AccountId']}: The region {c_account_credentials['Region']} isn't enabled")
                    else:
                        logging.error(f"AWS API error: {my_Error}")
                except Exception as my_Error:
                    logging.error(f"Unexpected error: {my_Error}")
                finally:
                    pbar.update()
                    self.queue.task_done()

    # Initialize shared variables
    checkqueue = Queue()
    AllDetectors = []
    AllInvitations = []
    WorkerThreads = min(len(fAllCredentials), 10)

    pbar = tqdm(
        desc=f'Finding GuardDuty detectors from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )

    # Start worker threads
    for x in range(WorkerThreads):
        worker = FindGDDetectors(checkqueue)
        worker.daemon = True
        worker.start()

    # Queue all credentials
    for credential in fAllCredentials:
        checkqueue.put(credential)

    checkqueue.join()
    pbar.close()
    return AllDetectors, AllInvitations

def run(args):
    """Main execution function for gd-detectors operation"""
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
    
    print("Searching for GuardDuty detectors...")
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
    
    # Find all GuardDuty detectors
    AllDetectors, AllInvitations = find_all_gd_detectors(CredentialList)
    
    if timing:
        timing.milestone("detectors_found", f"Found {len(AllDetectors)} detectors and {len(AllInvitations)} invitations")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'DetectorId': {'DisplayOrder': 5, 'Heading': 'Detector ID'},
        'IsAdminAccount': {'DisplayOrder': 6, 'Heading': 'Is Admin'},
        'MemberCount': {'DisplayOrder': 7, 'Heading': '# Members'}
    }

    sorted_detectors = sorted(AllDetectors, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['Region']
    ))
    
    display_results(sorted_detectors, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllDetectors)} GuardDuty detectors and {len(AllInvitations)} invitations across {AccountNum} accounts and {RegionNum} regions")