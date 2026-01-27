#!/usr/bin/env python3
"""
Organization users inventory operation (IAM + Identity Center)
"""

import logging
from typing import List, Dict, Any

from tqdm.auto import tqdm
from botocore.exceptions import ClientError

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import (
    get_all_credentials,
    display_results,
    find_iam_users2,
    find_idc_users2,
    find_idc_directory_id2,
)

__version__ = "2025.07.10"


def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('org-users', 'Organization users options')
    local.add_argument(
        "--idc",
        dest="pIdentityCenter",
        action="store_true",
        help="Only include Identity Center users; default is both IAM and Identity Center if no flag is set.",
    )
    local.add_argument(
        "--iam",
        dest="pIAM",
        action="store_true",
        help="Only include IAM users; default is both IAM and Identity Center if no flag is set.",
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"Org users operation version {__version__}",
    )


def _find_all_org_users(
    credentials: List[Dict[str, Any]],
    include_idc: bool,
    include_iam: bool,
) -> List[Dict[str, Any]]:
    """
    Collect IAM and/or Identity Center users across all credentials.
    """
    users: List[Dict[str, Any]] = []
    directories_seen = set()
    iam_accounts_seen = set()  # Track accounts we've already queried for IAM users

    for cred in tqdm(
        credentials,
        desc=f"Looking for users across {len(credentials)} accounts",
        unit="accounts",
    ):
        if not cred.get('Success', True):
            logging.info(
                "%s with roles: %s",
                cred.get('ErrorMessage'),
                cred.get('RolesTried'),
            )
            continue

        # IAM is global - only query once per account, not per region
        if include_iam:
            account_id = cred['AccountId']
            if account_id not in iam_accounts_seen:
                iam_accounts_seen.add(account_id)
                try:
                    iam_users = find_iam_users2(cred)
                    for user in iam_users:
                        users.append(
                            {
                                'MgmtAccount': cred['MgmtAccount'],
                                'AccountId': cred['AccountId'],
                                'Region': cred['Region'],
                                'UserName': user.get('UserName', ''),
                                'PasswordLastUsed': user.get('PasswordLastUsed', ''),
                                'Type': 'IAM',
                            }
                        )
                except ClientError as err:
                    if 'AuthFailure' in str(err):
                        logging.error(
                            "Authorization failure for IAM in %s (%s)",
                            cred['AccountId'],
                            cred['Region'],
                        )

        if include_idc:
            try:
                directory_ids = find_idc_directory_id2(cred)
                for directory_id in directory_ids:
                    if directory_id in directories_seen:
                        continue
                    directories_seen.add(directory_id)
                    idc_users = find_idc_users2(cred, directory_id)
                    for user in idc_users:
                        users.append(
                            {
                                'MgmtAccount': cred['MgmtAccount'],
                                'AccountId': cred['AccountId'],
                                'Region': cred['Region'],
                                'UserName': user.get('UserName', ''),
                                'PasswordLastUsed': user.get('PasswordLastUsed', ''),
                                'Type': 'IdentityCenter',
                            }
                        )
            except ClientError as err:
                if 'AuthFailure' in str(err):
                    logging.error(
                        "Authorization failure for Identity Center in %s (%s)",
                        cred['AccountId'],
                        cred['Region'],
                    )

    return users


def run(args):
    """Main execution function for org-users operation"""
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
    pIdentityCenter = getattr(args, 'pIdentityCenter', False)
    pIAM = getattr(args, 'pIAM', False)

    if not pIAM and not pIdentityCenter:
        pIAM = True
        pIdentityCenter = True

    print("Searching for organization users (IAM / Identity Center)...")
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

    user_list = _find_all_org_users(CredentialList, pIdentityCenter, pIAM)

    if timing:
        timing.milestone("users_found", f"Found {len(user_list)} users")

    display_dict = {
        'MgmtAccount': {'DisplayOrder': 1, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 2, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 3, 'Heading': 'Region'},
        'UserName': {'DisplayOrder': 4, 'Heading': 'User Name'},
        'PasswordLastUsed': {'DisplayOrder': 5, 'Heading': 'Last Used'},
        'Type': {'DisplayOrder': 6, 'Heading': 'Source'},
    }

    sorted_users = sorted(
        user_list,
        key=lambda k: (k['MgmtAccount'], k['AccountId'], k['Region'], k['UserName']),
    )

    display_results(sorted_users, display_dict, None, pFilename)

    if timing:
        timing.milestone("results_displayed", "Org users results formatted and displayed")

    print(
        f"\nFound {len(user_list)} users across {AccountNum} account{'s' if AccountNum != 1 else ''}"
    )
