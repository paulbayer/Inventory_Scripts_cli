#!/usr/bin/env python3
"""
AWS Config recorders and delivery channels inventory operation
"""

import logging
from typing import List, Dict, Any

from tqdm.auto import tqdm
from botocore.exceptions import ClientError

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

__version__ = "2025.07.10"


def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group(
        'config-recorders',
        'AWS Config recorder and delivery channel options',
    )
    local.add_argument(
        "--fragment",
        "--frag",
        dest="pFragments",
        nargs="*",
        metavar="Name fragment",
        default=['all'],
        help="String fragment(s) to search for in recorder and delivery channel names.",
    )
    local.add_argument(
        "--exact",
        dest="pExact",
        action="store_true",
        help="Match fragments exactly instead of substring search.",
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"Config recorders operation version {__version__}",
    )


def _matches(fragment_list: List[str], name: str, exact: bool) -> bool:
    if fragment_list is None or 'all' in fragment_list:
        return True
    for fragment in fragment_list:
        if (exact and name == fragment) or (not exact and fragment in name):
            return True
    return False


def _collect_for_credential(
    credential: Dict[str, Any],
    fragments: List[str],
    exact: bool,
) -> List[Dict[str, Any]]:
    """
    Collect config recorders and delivery channels for a single credential/region.
    """
    results: List[Dict[str, Any]] = []
    account_id = credential.get('AccountId') or credential.get('AccountNumber')

    try:
        dcs = Inventory_Modules.find_delivery_channels2(credential, credential['Region'])
        if dcs.get('Success', True):
            for dc in dcs.get('DeliveryChannels', []):
                if _matches(fragments, dc.get('name', ''), exact):
                    results.append(
                        {
                            'ParentProfile': credential.get('ParentProfile', 'Unknown'),
                            'MgmtAccount': credential['MgmtAccount'],
                            'AccountId': account_id,
                            'Region': credential['Region'],
                            'Type': 'Delivery Channel',
                            'Name': dc.get('name', ''),
                            'S3Bucket': dc.get('s3BucketName', ''),
                            'SnsTopic': dc.get('snsTopicARN', ''),
                            'Frequency': dc.get('configSnapshotDeliveryProperties', {}).get(
                                'deliveryFrequency',
                                '',
                            ),
                        }
                    )
    except ClientError as err:
        if "AuthFailure" in str(err):
            logging.error(
                "Authorization failure accessing delivery channels for %s in %s",
                account_id,
                credential['Region'],
            )
        else:
            logging.error("Error retrieving delivery channels for %s: %s", account_id, err)

    try:
        crs = Inventory_Modules.find_config_recorders2(credential, credential['Region'])
        for cr in crs.get('ConfigurationRecorders', []):
            if not _matches(fragments, cr.get('name', ''), exact):
                continue
            recording_group = cr.get('recordingGroup', {})
            results.append(
                {
                    'ParentProfile': credential.get('ParentProfile', 'Unknown'),
                    'MgmtAccount': credential['MgmtAccount'],
                    'AccountId': account_id,
                    'Region': credential['Region'],
                    'Type': 'Config Recorder',
                    'Name': cr.get('name', ''),
                    'RoleArn': cr.get('roleARN', ''),
                    'AllSupported': recording_group.get('allSupported'),
                    'IncludeGlobalResourceTypes': recording_group.get('includeGlobalResourceTypes'),
                    'ResourceTypes': ', '.join(recording_group.get('resourceTypes', [])),
                }
            )
    except ClientError as err:
        if "AuthFailure" in str(err):
            logging.error(
                "Authorization failure accessing config recorder for %s in %s",
                account_id,
                credential['Region'],
            )
        else:
            logging.error("Error retrieving config recorder for %s: %s", account_id, err)

    return results


def run(args):
    """Main execution function for config-recorders operation"""
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
    pFragments = getattr(args, 'pFragments', ['all'])
    pExact = getattr(args, 'pExact', False)

    print("Searching for AWS Config recorders and delivery channels...")
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

    results: List[Dict[str, Any]] = []

    for credential in tqdm(
        CredentialList,
        desc=f"Inspecting {len(CredentialList)} account/region combinations",
        unit='locations',
    ):
        logging.info(
            "Inspecting account %s in region %s",
            credential['AccountId'],
            credential['Region'],
        )
        results.extend(_collect_for_credential(credential, pFragments, pExact))

    if timing:
        timing.milestone(
            "config_items_found",
            f"Found {len(results)} config recorders/delivery channels",
        )

    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'Type': {'DisplayOrder': 5, 'Heading': 'Type'},
        'Name': {'DisplayOrder': 6, 'Heading': 'Name'},
        'S3Bucket': {'DisplayOrder': 7, 'Heading': 'S3 Bucket'},
        'SnsTopic': {'DisplayOrder': 8, 'Heading': 'SNS Topic'},
        'Frequency': {'DisplayOrder': 9, 'Heading': 'Snapshot Freq'},
        'RoleArn': {'DisplayOrder': 10, 'Heading': 'Role ARN'},
        'AllSupported': {'DisplayOrder': 11, 'Heading': 'All Resources'},
        'IncludeGlobalResourceTypes': {'DisplayOrder': 12, 'Heading': 'Include Globals'},
        'ResourceTypes': {'DisplayOrder': 13, 'Heading': 'Resource Types'},
    }

    sorted_results = sorted(
        results,
        key=lambda d: (
            d.get('ParentProfile', ''),
            d['MgmtAccount'],
            d['AccountId'],
            d['Region'],
            d['Type'],
            d['Name'],
        ),
    )

    display_results(sorted_results, display_dict, None, pFilename)

    if timing:
        timing.milestone("results_displayed", "Config recorder results formatted and displayed")

    print(
        f"\nFound {len(sorted_results)} config recorders/delivery channels across {AccountNum} accounts and {RegionNum} regions"
    )
