#!/usr/bin/env python3
"""
AWS Organizations inventory operation
"""

import logging
from time import time
from colorama import Fore, Style, init

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_profiles, get_org_accounts_from_profiles, display_results

init()
__version__ = "2025.07.10"

class OrgsFound:
    """Class to hold organization discovery results"""
    def __init__(self):
        self.orgs_found = []
        self.num_of_org_accounts = 0
        self.stand_alone_accounts = []
        self.closed_accounts = []
        self.failed_profiles = []
        self.account_list = []

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('orgs', 'AWS Organizations specific options')
    local.add_argument(
        '-s', '-q', '--short',
        help="Display only brief listing of the profile accounts, and not the Child Accounts under them",
        action="store_const",
        dest="pShortform",
        const=True,
        default=False
    )
    local.add_argument(
        '-A', '--acct',
        help="Find which Org this account is a part of",
        nargs="*",
        dest="pAccountList",
        default=None
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"AWS Organizations operation version {__version__}"
    )

def find_all_orgs(pProfiles: list, pSkipProfiles: list, pAccountList: list, pTiming: bool, pRootOnly: bool, pFilename: str, pShortform: bool) -> OrgsFound:
    """
    Find all AWS Organizations from the provided profiles
    """
    ProfileList = get_profiles(fSkipProfiles=pSkipProfiles, fprofiles=pProfiles)
    logging.info(f"These profiles were requested: {pProfiles}.")
    logging.warning(f"These profiles are being checked: {ProfileList}.")
    
    print(f"Please bear with us as we run through {len(ProfileList)} profile{'s' if len(ProfileList) != 1 else ''}")
    
    AllProfileAccounts = get_org_accounts_from_profiles(ProfileList)
    if not AllProfileAccounts:
        logging.info(f"No profiles were found, hence we're going to look at the environment variables")
        print(f"No profiles were found, hence we're going to look at the environment variables")
        AllProfileAccounts = get_org_accounts_from_profiles()
    
    AccountList = []
    FailedProfiles = []
    OrgsFoundList = []

    # Print out the results
    if pTiming:
        print()
        print(f"It's taken {Fore.GREEN}{time() - time():.2f}{Fore.RESET} seconds to find {len(ProfileList)} profile accounts...")
        print()
    
    fmt = '%-36s %-15s %-15s %-12s %-10s'
    print("<------------------------------------>")
    print(fmt % ("Profile Name", "Account Number", "Payer Org Acct", "Org ID", "Root Acct?"))
    print(fmt % ("------------", "--------------", "--------------", "------", "----------"))

    for item in AllProfileAccounts:
        logging.error(item)
        if not item['Success']:
            # If the profile failed, don't print anything and continue on.
            FailedProfiles.append(item['profile'])
            logging.error(f"{item['profile']} errored. Message: {item['ErrorMessage']}")
        else:
            if item['RootAcct']:
                # If the account is a root account, capture it for display later
                OrgsFoundList.append(item['MgmtAccount'])
            # Print results for all profiles
            item['AccountId'] = item['aws_acct'].acct_number
            item['AccountStatus'] = item['aws_acct'].AccountStatus
            
            try:
                if pRootOnly and not item['RootAcct']:
                    # If we're only looking for root accounts, and this isn't one, don't print anything and continue on.
                    continue
                else:
                    logging.info(f"{item['profile']} was successful.")
                    print(f"{Fore.RED if item['RootAcct'] else ''}{item['profile']:36s} {item['aws_acct'].acct_number:15s} {item['MgmtAccount']:15s} {str(item['OrgId']):12s} {item['RootAcct']}{Fore.RESET}")
            except TypeError as my_Error:
                logging.error(f"Error - {my_Error} on {item}")
                pass

    print("-------------------")

    if pShortform:
        # The user specified "short-form" which means they don't want any information on child accounts.
        result = OrgsFound()
        result.orgs_found = OrgsFoundList
        result.failed_profiles = FailedProfiles
        return result
    else:
        NumOfOrgAccounts = 0
        ClosedAccounts = []
        FailedAccounts = 0
        account = dict()
        ProfileNameLength = len("Organization's Profile")

        for item in AllProfileAccounts:
            # AllProfileAccounts holds the list of account class objects of the accounts associated with the profiles it found.
            if item['Success'] and not item['RootAcct']:
                account.update(item['aws_acct'].ChildAccounts[0])
                account.update({'Profile': item['profile']})
                AccountList.append(account.copy())
            elif item['Success'] and item['RootAcct']:
                for child_acct in item['aws_acct'].ChildAccounts:
                    account.update(child_acct)
                    account.update({'Profile': item['profile']})
                    ProfileNameLength = max(len(item['profile']), ProfileNameLength) if item['profile'] else len("Organization's Profile")
                    AccountList.append(account.copy())
                    if not child_acct['AccountStatus'] == 'ACTIVE':
                        ClosedAccounts.append(child_acct['AccountId'])

                NumOfOrgAccounts += len(item['aws_acct'].ChildAccounts)
            elif not item['Success']:
                FailedAccounts += 1
                continue

        # Display results on screen
        if pFilename is None:
            fmt = '%-23s %-15s'
            print()
            print(fmt % ("Organization's Profile", "Root Account"))
            print(fmt % ("----------------------", "------------"))
            for item in AllProfileAccounts:
                if item['Success'] and item['RootAcct']:
                    print(f"{item['profile']:{ProfileNameLength + 2}s}", end='') if item['profile'] else print(f"{'No Profile available':{ProfileNameLength + 2}s}", end='')
                    print(f"{Style.BRIGHT}{item['MgmtAccount']:15s}{Style.RESET_ALL}")
                    print(f"\t{'Child Account Number':{len('Child Account Number')}s} {'Child Account Status':{len('Child Account Status')}s} {'Child Email Address'}")
                    for child_acct in item['aws_acct'].ChildAccounts:
                        print(f"\t{Fore.RED if not child_acct['AccountStatus'] == 'ACTIVE' else ''}{child_acct['AccountId']:{len('Child Account Number')}s} {child_acct['AccountStatus']:{len('Child Account Status')}s} {child_acct['AccountEmail']}{Fore.RESET}")

        elif pFilename is not None:
            # The user specified a file name, which means they want a (pipe-delimited) CSV file with the relevant output.
            display_dict = {
                'MgmtAccount': {'DisplayOrder': 1, 'Heading': 'Parent Acct'},
                'AccountId': {'DisplayOrder': 2, 'Heading': 'Account Number'},
                'AccountStatus': {'DisplayOrder': 3, 'Heading': 'Account Status', 'Condition': ['SUSPENDED', 'CLOSED']},
                'AccountEmail': {'DisplayOrder': 4, 'Heading': 'Email'}
            }
            if pRootOnly:
                sorted_Results = sorted(AllProfileAccounts, key=lambda d: (d['MgmtAccount'], d['AccountId']))
            else:
                sorted_Results = sorted(AccountList, key=lambda d: (d['MgmtAccount'], d['AccountId']))
            display_results(sorted_Results, display_dict, "None", pFilename)

        StandAloneAccounts = [x['AccountId'] for x in AccountList if x['MgmtAccount'] == x['AccountId'] and x['AccountEmail'] == 'Not an Org Management Account']
        FailedProfiles = [i['profile'] for i in AllProfileAccounts if not i['Success']]
        OrgsFoundList = [i['MgmtAccount'] for i in AllProfileAccounts if i['RootAcct']]
        StandAloneAccounts.sort()
        FailedProfiles.sort()
        OrgsFoundList.sort()
        ClosedAccounts.sort()

        result = OrgsFound()
        result.orgs_found = OrgsFoundList.copy()
        result.num_of_org_accounts = NumOfOrgAccounts
        result.closed_accounts = ClosedAccounts.copy()
        result.failed_profiles = FailedProfiles.copy()
        result.stand_alone_accounts = StandAloneAccounts.copy()
        result.account_list = AccountList.copy()

        return result

def run(args):
    """Main execution function for AWS Organizations operation"""
    # Get timing context from CLI (if available)
    timing = getattr(args, '_timing_context', None)
    
    # Extract arguments
    pProfiles = args.Profiles
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pRootOnly = args.RootOnly
    pFilename = args.Filename
    pTiming = args.Time
    pShortform = getattr(args, 'pShortform', False)
    pAccountList = getattr(args, 'pAccountList', None)
    
    print("Searching for AWS Organizations...")
    print(f"\nOperation version: {__version__}")
    if pShortform:
        print(f"Using {Fore.RED}short form{Fore.RESET} - showing only profile accounts, not child accounts")
    if pRootOnly:
        print(f"Showing {Fore.RED}root accounts only{Fore.RESET}")
    if pAccountList:
        print(f"Looking for specific accounts: {Fore.RED}{pAccountList}{Fore.RESET}")
    
    if timing:
        timing.milestone("args_parsed", "Arguments parsed and validated")
    
    # Find all organizations
    response = find_all_orgs(pProfiles, pSkipProfiles, pAccountList, pTiming, pRootOnly, pFilename, pShortform)
    
    if timing:
        timing.milestone("orgs_found", f"Found {len(response.orgs_found)} organizations")
    
    # Display summary with numbers...
    print()
    print(f"Number of Organizations: {len(response.orgs_found)}")
    print(f"Number of Organization Accounts: {response.num_of_org_accounts}")
    print(f"Number of Standalone Accounts: {len(response.stand_alone_accounts)}")
    print(f"Number of suspended or closed accounts: {len(response.closed_accounts)}")
    print(f"Number of profiles that failed: {len(response.failed_profiles)}")
    
    # Show detailed lists if verbose
    if len(response.orgs_found) > 0 or len(response.stand_alone_accounts) > 0 or len(response.closed_accounts) > 0 or len(response.failed_profiles) > 0:
        if response.orgs_found:
            print(f"The following accounts are the Org Accounts: {response.orgs_found}")
        if response.stand_alone_accounts:
            print(f"The following accounts are Standalone: {response.stand_alone_accounts}")
        if response.closed_accounts:
            print(f"The following accounts are closed or suspended: {response.closed_accounts}")
        if response.failed_profiles:
            print(f"The following profiles failed: {response.failed_profiles}")
        print("----------------------")
    
    # Show specific account information if requested
    if pAccountList is not None:
        print(f"Found the requested account number{'s' if len(response.account_list) != 1 else ''}:")
        for acct in response.account_list:
            if acct['AccountId'] in pAccountList:
                print(f"Profile: {acct['Profile']} | Org: {acct['MgmtAccount']} | Account: {acct['AccountId']} | Status: {acct['AccountStatus']} | Email: {acct['AccountEmail']}")
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    