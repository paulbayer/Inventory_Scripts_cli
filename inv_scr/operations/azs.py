#!/usr/bin/env python3
"""
Availability Zones coverage operation
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
    local = parser.my_parser.add_argument_group('azs', 'Availability Zones coverage options')
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"AZ coverage operation version {__version__}",
    )


def _collect_azs(credentials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Collect AZ coverage across all credentials.
    """
    results: List[Dict[str, Any]] = []

    for cred in tqdm(
        credentials,
        desc=f"Gathering AZs from {len(credentials)} locations",
        unit='locations',
    ):
        try:
            azs = Inventory_Modules.get_region_azs2(cred)
            for az in azs:
                if az.get('ZoneType') != 'availability-zone':
                    continue
                results.append(
                    {
                        'ParentProfile': cred.get('ParentProfile', 'Unknown'),
                        'MgmtAccount': cred['MgmtAccount'],
                        'AccountNumber': cred.get('AccountId') or cred.get('AccountNumber'),
                        'Region': az.get('Region', cred['Region']),
                        'ZoneName': az.get('ZoneName'),
                        'ZoneId': az.get('ZoneId'),
                        'ZoneType': az.get('ZoneType'),
                    }
                )
        except ClientError as err:
            if "AuthFailure" in str(err):
                logging.error(
                    "Authorization failure for account %s in %s",
                    cred.get('AccountId') or cred.get('AccountNumber'),
                    cred['Region'],
                )
            else:
                logging.error("AWS API error: %s", err)

    return results


def run(args):
    """Main execution function for azs operation"""
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

    print("Collecting Availability Zone coverage...")
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

    az_results = _collect_azs(CredentialList)

    if timing:
        timing.milestone("azs_found", f"Found {len(az_results)} availability zones")

    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountNumber': {'DisplayOrder': 3, 'Heading': 'Account Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'ZoneName': {'DisplayOrder': 5, 'Heading': 'Zone Name'},
        'ZoneId': {'DisplayOrder': 6, 'Heading': 'Zone Id'},
        'ZoneType': {'DisplayOrder': 7, 'Heading': 'Zone Type'},
    }

    sorted_results = sorted(
        az_results,
        key=lambda d: (
            d['ParentProfile'],
            d['MgmtAccount'],
            d['AccountNumber'],
            d['Region'],
            d['ZoneName'],
        ),
    )

    display_results(sorted_results, display_dict, None, pFilename)

    if timing:
        timing.milestone("results_displayed", "AZ coverage results formatted and displayed")

    print(f"\nFound {len(sorted_results)} AZ entries across {AccountNum} accounts and {RegionNum} regions")
