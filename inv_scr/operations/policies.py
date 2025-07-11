#!/usr/bin/env python3
"""IAM Policies inventory operation"""

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
    local = parser.my_parser.add_argument_group('policies', 'IAM Policies specific options')
    local.add_argument(
        "--fragment", "--frag",
        dest="pFragments",
        nargs="*",
        metavar="Policy fragment",
        default=['all'],
        help="String fragment(s) to be looked for in the policy names"
    )
    local.add_argument(
        "--exact",
        dest="pExact",
        action="store_true",
        help="Look for exact match of fragment, instead of substring"
    )
    local.add_argument(
        "--action",
        dest="paction",
        nargs="*",
        metavar="AWS Action",
        default=None,
        help="An action you're looking for within the policies"
    )
    local.add_argument(
        "--cmp", "--customer_managed_policies",
        dest="pcmp",
        action="store_true",
        help="A flag to specify you're only looking for customer managed policies"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"IAM Policies operation version {__version__}"
    )

def find_all_policies(fAllCredentials: list, fFragments: list = None, fExact: bool = False, fActions: list = None, fCMP: bool = False) -> list:
    """
    Find all IAM policies from all accounts within the credentials supplied
    """
    
    class FindPolicyActions(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials, c_policy, c_action = self.queue.get()
                logging.info(f"Processing policy {c_policy['PolicyName']} for account {c_account_credentials['AccountId']}")
                try:
                    policy_actions = Inventory_Modules.find_policy_action2(c_account_credentials, c_policy, c_action)
                    logging.info(f"Successfully processed policy {c_policy['PolicyName']} for account {c_account_credentials['AccountId']}")
                    
                    if len(policy_actions) > 0:
                        AllPolicies.extend(policy_actions)
                        
                except KeyError as my_Error:
                    logging.error(f"Account access failed for {c_account_credentials['AccountId']}: {my_Error}")
                except AttributeError as my_Error:
                    logging.error(f"Profile error: {my_Error}")
                except ClientError as my_Error:
                    if 'AuthFailure' in str(my_Error):
                        logging.error(f"Authorization failure for account {c_account_credentials['AccountId']}")
                    else:
                        logging.error(f"AWS API error: {my_Error}")
                finally:
                    pbar.update()
                    self.queue.task_done()

    # Initialize shared variables
    checkqueue = Queue()
    AllPolicies = []
    
    # Use us-east-1 as default region for IAM (global service)
    fRegionList = ['us-east-1']
    
    if fFragments is None:
        fFragments = []

    print()
    for credential in fAllCredentials:
        try:
            logging.info(f"Connecting to account {credential['AccountId']}")
            Policies = Inventory_Modules.find_account_policies2(credential, fRegionList[0], fFragments, fExact, fCMP)
            
            if fActions is None:
                # If no actions specified, just return the policies
                for policy in Policies:
                    policy['MgmtAccount'] = credential['MgmtAccount']
                    policy['ParentProfile'] = credential.get('ParentProfile', 'Unknown')
                AllPolicies.extend(Policies)
            else:
                # If actions specified, we need to search within policies
                PlacesToLook = len(Policies) * len(fActions)
                
                pbar = tqdm(
                    desc=f'Searching policy actions from {len(Policies)} policies',
                    total=PlacesToLook, 
                    unit=' policy-actions'
                )
                
                WorkerThreads = min(PlacesToLook, 50)
                
                for x in range(WorkerThreads):
                    worker = FindPolicyActions(checkqueue)
                    worker.daemon = True
                    worker.start()
                
                for policy in Policies:
                    for action in fActions:
                        checkqueue.put((credential, policy, action))
                
                checkqueue.join()
                pbar.close()
                
        except ClientError as my_Error:
            if "AuthFailure" in str(my_Error):
                logging.error(f"Authorization failure accessing account {credential['AccountId']}")

    return AllPolicies

def run(args):
    """Main execution function for policies operation"""
    # Get timing context from CLI (if available)
    timing = getattr(args, '_timing_context', None)
    
    # Extract arguments
    pProfiles = args.Profiles
    pAccounts = args.Accounts
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pFragments = getattr(args, 'pFragments', ['all'])
    pExact = getattr(args, 'pExact', False)
    pActions = getattr(args, 'paction', None)
    pCMP = getattr(args, 'pcmp', False)
    pRootOnly = args.RootOnly
    pFilename = args.Filename
    pTiming = args.Time
    
    print("Searching for IAM policies...")
    print(f"Operation version: {__version__}")
    
    if timing:
        timing.milestone("args_parsed", "Arguments parsed and validated")
    
    # IAM is a global service, so we only need us-east-1
    pRegionList = ['us-east-1']
    
    # Get credentials for all accounts
    CredentialList = get_all_credentials(
        pProfiles, pTiming, pSkipProfiles, pSkipAccounts, 
        pRootOnly, pAccounts, pRegionList
    )
    
    AccountNum = len(set([acct['AccountId'] for acct in CredentialList]))
    
    print(f"Searching {AccountNum} accounts globally")
    
    if timing:
        timing.milestone("credentials_setup", f"Credential setup for {AccountNum} accounts")
    
    # Find all policies
    AllPolicies = find_all_policies(CredentialList, pFragments, pExact, pActions, pCMP)
    
    if timing:
        timing.milestone("policies_found", f"Found {len(AllPolicies)} policies")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountNumber': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'PolicyName': {'DisplayOrder': 5, 'Heading': 'Policy Name'},
        'Action': {'DisplayOrder': 6, 'Heading': 'Action'}
    }

    sorted_policies = sorted(AllPolicies, key=lambda d: (
        d.get('ParentProfile', ''), d.get('MgmtAccount', ''), d.get('AccountNumber', ''), d.get('PolicyName', '')
    ))
    
    display_results(sorted_policies, display_dict, pActions, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllPolicies)} policies across {AccountNum} accounts")
    if pFragments and pFragments != ['all']:
        print(f"that matched the fragment{'s' if len(pFragments) > 1 else ''}: {pFragments}")