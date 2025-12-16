#!/usr/bin/env python3
"""
RAM resource shares inventory operation
"""

import logging
from queue import Queue
from threading import Thread, Lock
from time import time
from typing import List, Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError
from tqdm.auto import tqdm

from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

__version__ = "2025.07.10"


def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('ram-shares', 'AWS RAM shares options')
    local.add_argument(
        "-s",
        "--status",
        dest="pStatus",
        choices=['ACTIVE', 'DELETING', 'FAILED', 'PENDING'],
        type=str,
        default=None,
        help="Filter RAM shares by status. Default is all statuses.",
    )
    local.add_argument(
        "-t",
        "--type",
        dest="pType",
        choices=['OWNED', 'RECEIVED'],
        type=str,
        default=None,
        help="Filter by share type: OWNED (you created) or RECEIVED (shared with you). Default is both.",
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"RAM shares operation version {__version__}",
    )


def _get_ram_shares_for_account(
    ocredentials: Dict[str, Any],
    fStatus: Optional[str],
    fType: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Discover RAM shares for a single account/region.
    """
    session_ram = boto3.Session(
        aws_access_key_id=ocredentials['AccessKeyId'],
        aws_secret_access_key=ocredentials['SecretAccessKey'],
        aws_session_token=ocredentials['SessionToken'],
        region_name=ocredentials['Region'],
    )
    client_ram = session_ram.client('ram')

    shares: List[Dict[str, Any]] = []

    def _collect_shares(owner_type: str, share_type_label: str):
        paginator = client_ram.get_paginator('get_resource_shares')
        for page in paginator.paginate(resourceOwner=owner_type):
            for share in page.get('resourceShares', []):
                if fStatus and share.get('status') != fStatus:
                    continue

                resources: List[Dict[str, Any]] = []
                principals: List[Dict[str, Any]] = []

                try:
                    resources_response = client_ram.get_resource_share_associations(
                        associationType='RESOURCE',
                        resourceShareArns=[share['resourceShareArn']],
                    )
                    resources = resources_response.get('resourceShareAssociations', [])
                except ClientError as err:
                    logging.debug(
                        "Could not retrieve resources for share %s in account %s: %s",
                        share.get('name', 'unknown'),
                        ocredentials['AccountId'],
                        err,
                    )

                if share_type_label == 'OWNED':
                    try:
                        principals_response = client_ram.get_resource_share_associations(
                            associationType='PRINCIPAL',
                            resourceShareArns=[share['resourceShareArn']],
                        )
                        principals = principals_response.get('resourceShareAssociations', [])
                    except ClientError as err:
                        logging.debug(
                            "Could not retrieve principals for share %s in account %s: %s",
                            share.get('name', 'unknown'),
                            ocredentials['AccountId'],
                            err,
                        )

                shares.append(
                    {
                        'ShareType': share_type_label,
                        'ShareArn': share['resourceShareArn'],
                        'ShareName': share.get('name', ''),
                        'Status': share.get('status'),
                        'OwningAccountId': share.get('owningAccountId'),
                        'CreationTime': str(share.get('creationTime', '')),
                        'LastUpdatedTime': str(share.get('lastUpdatedTime', '')),
                        'AllowExternalPrincipals': share.get('allowExternalPrincipals', False),
                        'Tags': share.get('tags', []),
                        'Resources': [
                            {
                                'Arn': res.get('associatedEntity'),
                                'Type': res.get('resourceType', 'Unknown'),
                                'Status': res.get('status', 'Unknown'),
                            }
                            for res in resources
                        ],
                        'SharedWith': [
                            {
                                'Principal': assoc.get('associatedEntity'),
                                'Status': assoc.get('status'),
                            }
                            for assoc in principals
                        ]
                        if share_type_label == 'OWNED'
                        else [f"This account ({ocredentials['AccountId']})"],
                    }
                )

    if fType in (None, 'OWNED'):
        _collect_shares('SELF', 'OWNED')
    if fType in (None, 'RECEIVED'):
        _collect_shares('OTHER-ACCOUNTS', 'RECEIVED')

    return shares


def _find_all_ram_shares(
    fAllCredentials: List[Dict[str, Any]],
    fStatus: Optional[str],
    fType: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Iterate across all provided credentials and collect RAM shares.
    """

    class FindRAMShares(Thread):
        def __init__(self, queue, ram_shares_lock):
            super().__init__()
            self.queue = queue
            self.ram_shares_lock = ram_shares_lock

        def run(self):
            while True:
                credential = self.queue.get()
                logging.info(
                    "Checking RAM shares for account %s in %s",
                    credential['AccountId'],
                    credential['Region'],
                )
                try:
                    ram_shares = _get_ram_shares_for_account(credential, fStatus, fType)
                    logging.info(
                        "Account %s Region %s: Found %d RAM shares",
                        credential['AccountId'],
                        credential['Region'],
                        len(ram_shares),
                    )

                    for share in ram_shares:
                        resource_list = [
                            f"{res['Type']}: {res['Arn']}" for res in share.get('Resources', [])
                        ]

                        if share['ShareType'] == 'OWNED':
                            shared_with = [
                                principal['Principal']
                                if isinstance(principal, dict)
                                else str(principal)
                                for principal in share.get('SharedWith', [])
                            ]
                        else:
                            shared_with = [credential['AccountId']]

                        tag_list = [
                            f"{tag.get('key')}={tag.get('value')}" for tag in share.get('Tags', [])
                        ]

                        formatted = {
                            'ParentProfile': credential.get('ParentProfile', 'Unknown'),
                            'MgmtAccount': credential['MgmtAccount'],
                            'AccountId': credential['AccountId'],
                            'OwnerAccount': share.get('OwningAccountId'),
                            'Region': credential['Region'],
                            'ShareType': share['ShareType'],
                            'ShareName': share['ShareName'],
                            'Status': share['Status'],
                            'ResourceCount': len(resource_list),
                            'Resources': '; '.join(resource_list) if resource_list else 'None',
                            'SharedWithCount': len(shared_with),
                            'SharedWith': '; '.join(shared_with) if shared_with else 'None',
                            'AllowExternalPrincipals': share['AllowExternalPrincipals'],
                            'ShareArn': share['ShareArn'],
                            'CreationTime': share['CreationTime'],
                            'LastUpdatedTime': share['LastUpdatedTime'],
                            'Tags': '; '.join(tag_list) if tag_list else 'None',
                        }
                        with self.ram_shares_lock:
                            AllRAMShares.append(formatted)
                except ClientError as err:
                    logging.error(
                        "Error retrieving RAM shares for account %s in %s: %s",
                        credential['AccountId'],
                        credential['Region'],
                        err,
                    )
                finally:
                    pbar.update()
                    self.queue.task_done()

    AllRAMShares: List[Dict[str, Any]] = []
    ram_shares_lock = Lock()
    WorkerThreads = min(len(fAllCredentials), 30)

    work_queue = Queue()
    pbar = tqdm(
        desc=f'Finding RAM shares from {len(fAllCredentials)} locations',
        total=len(fAllCredentials),
        unit=' locations',
    )

    for _ in range(WorkerThreads):
        worker = FindRAMShares(work_queue, ram_shares_lock)
        worker.daemon = True
        worker.start()

    for credential in fAllCredentials:
        work_queue.put(credential)

    work_queue.join()
    pbar.close()
    return AllRAMShares


def run(args):
    """Main execution function for ram-shares operation"""
    timing = getattr(args, '_timing_context', None)

    pProfiles = args.Profiles
    pRegionList = args.Regions
    pAccounts = args.Accounts
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pRootOnly = args.RootOnly
    pFilename = args.Filename
    pTiming = args.Time
    pAccessRoles = args.AccessRoles
    pStatus = getattr(args, 'pStatus', None)
    pType = getattr(args, 'pType', None)

    print("Searching for RAM shares...")
    print(f"Operation version: {__version__}")

    if timing:
        timing.milestone("args_parsed", "Arguments parsed and validated")

    CredentialList = get_all_credentials(
        pProfiles,
        pTiming,
        pSkipProfiles,
        pSkipAccounts,
        pRootOnly,
        pAccounts,
        pRegionList,
        pAccessRoles,
    )

    AccountNum = len(set(acct['AccountId'] for acct in CredentialList))
    RegionNum = len(set(acct['Region'] for acct in CredentialList))
    print(f"Searching {AccountNum} accounts across {RegionNum} regions")

    if timing:
        timing.milestone(
            "credentials_setup",
            f"Credential setup for {AccountNum} accounts across {RegionNum} regions",
        )

    AllShares = _find_all_ram_shares(CredentialList, pStatus, pType)

    if timing:
        timing.milestone("ram_shares_found", f"Found {len(AllShares)} RAM shares")

    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Viewing Acct'},
        'OwnerAccount': {'DisplayOrder': 4, 'Heading': 'Owner Acct'},
        'Region': {'DisplayOrder': 5, 'Heading': 'Region'},
        'ShareType': {'DisplayOrder': 6, 'Heading': 'Type'},
        'ShareName': {'DisplayOrder': 7, 'Heading': 'Share Name'},
        'Status': {'DisplayOrder': 8, 'Heading': 'Status'},
        'ResourceCount': {'DisplayOrder': 9, 'Heading': '# Resources'},
        'SharedWithCount': {'DisplayOrder': 10, 'Heading': '# Shared With'},
        'AllowExternalPrincipals': {'DisplayOrder': 11, 'Heading': 'Ext Principals'},
        'Resources': {'DisplayOrder': 12, 'Heading': 'Resources'},
        'SharedWith': {'DisplayOrder': 13, 'Heading': 'Shared With'},
        'ShareArn': {'DisplayOrder': 14, 'Heading': 'Share Arn'},
        'CreationTime': {'DisplayOrder': 15, 'Heading': 'Created'},
        'LastUpdatedTime': {'DisplayOrder': 16, 'Heading': 'Updated'},
        'Tags': {'DisplayOrder': 17, 'Heading': 'Tags'},
    }

    sorted_shares = sorted(
        AllShares,
        key=lambda d: (
            d['ParentProfile'],
            d['MgmtAccount'],
            d['AccountId'],
            d['Region'],
            d['ShareType'],
            d['ShareName'],
        ),
    )

    display_results(sorted_shares, display_dict, None, pFilename)

    if timing:
        timing.milestone("results_displayed", "RAM shares results formatted and displayed")

    print(
        f"\nFound {len(AllShares)} RAM shares across {AccountNum} accounts and {RegionNum} regions"
    )
