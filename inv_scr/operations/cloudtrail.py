#!/usr/bin/env python3
"""
CloudTrail coverage inventory operation
"""

import logging
from queue import Queue
from threading import Thread
from typing import List, Dict, Any

from botocore.exceptions import ClientError
from tqdm.auto import tqdm

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

__version__ = "2025.07.10"


def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('cloudtrail', 'AWS CloudTrail options')
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"CloudTrail operation version {__version__}",
    )


def _find_cloudtrails(credentials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Discover CloudTrails across all provided credential/region combinations.
    """

    class FindCloudTrails(Thread):
        def __init__(self, queue):
            super().__init__()
            self.queue = queue

        def run(self):
            while True:
                cred = self.queue.get()
                try:
                    logging.info(
                        "Checking CloudTrails for account %s in %s",
                        cred['AccountId'],
                        cred['Region'],
                    )
                    trails = Inventory_Modules.find_account_cloudtrail2(
                        cred, cred['Region']
                    )
                    if 'trailList' in trails:
                        for trail in trails['trailList']:
                            AllTrails.append(
                                {
                                    'MgmtAccount': cred['MgmtAccount'],
                                    'AccountId': cred['AccountId'],
                                    'Region': cred['Region'],
                                    'TrailName': trail.get('Name', ''),
                                    'MultiRegion': trail.get('IsMultiRegionTrail', False),
                                    'OrgTrail': 'OrgTrail'
                                    if trail.get('IsOrganizationTrail')
                                    else 'Account Trail',
                                    'Bucket': trail.get('S3BucketName', ''),
                                    'KMS': trail.get('KmsKeyId'),
                                    'CloudWatchLogArn': trail.get(
                                        'CloudWatchLogsLogGroupArn'
                                    ),
                                    'HomeRegion': trail.get('HomeRegion'),
                                    'SNSTopicName': trail.get('SNSTopicName'),
                                }
                            )
                except ClientError as err:
                    if "AuthFailure" in str(err):
                        logging.error(
                            "Authorization failure for account %s in %s",
                            cred['AccountId'],
                            cred['Region'],
                        )
                    else:
                        logging.error("AWS API error: %s", err)
                finally:
                    pbar.update()
                    self.queue.task_done()

    queue = Queue()
    AllTrails: List[Dict[str, Any]] = []
    worker_count = min(len(credentials), 30)
    pbar = tqdm(
        desc=f'Finding CloudTrails from {len(credentials)} locations',
        total=len(credentials),
        unit=' locations',
    )

    for _ in range(worker_count):
        worker = FindCloudTrails(queue)
        worker.daemon = True
        worker.start()

    for cred in credentials:
        if cred.get('Success', True):
            queue.put(cred)

    queue.join()
    pbar.close()
    return AllTrails


def run(args):
    """Main execution function for cloudtrail operation"""
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

    print("Checking for CloudTrails...")
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

    AllTrails = _find_cloudtrails(CredentialList)

    if timing:
        timing.milestone("cloudtrails_found", f"Found {len(AllTrails)} CloudTrails")

    display_dict = {
        'MgmtAccount': {'DisplayOrder': 1, 'Heading': 'Parent Acct'},
        'AccountId': {'DisplayOrder': 2, 'Heading': 'Account Number'},
        'Region': {'DisplayOrder': 3, 'Heading': 'Region'},
        'TrailName': {'DisplayOrder': 4, 'Heading': 'Trail Name'},
        'OrgTrail': {'DisplayOrder': 5, 'Heading': 'Trail Type'},
        'Bucket': {'DisplayOrder': 6, 'Heading': 'S3 Bucket'},
        'MultiRegion': {'DisplayOrder': 7, 'Heading': 'Multi-Region'},
        'HomeRegion': {'DisplayOrder': 8, 'Heading': 'Home Region'},
    }

    sorted_trails = sorted(
        AllTrails,
        key=lambda d: (d['MgmtAccount'], d['AccountId'], d['Region'], d['TrailName']),
    )

    display_results(sorted_trails, display_dict, None, pFilename)

    if timing:
        timing.milestone("results_displayed", "CloudTrail results formatted and displayed")

    print(f"\nFound {len(AllTrails)} trails across {AccountNum} accounts and {RegionNum} regions")
