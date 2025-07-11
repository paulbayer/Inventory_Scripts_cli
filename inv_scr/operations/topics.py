#!/usr/bin/env python3
"""SNS Topics inventory operation"""

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
    local = parser.my_parser.add_argument_group('topics', 'SNS Topics specific options')
    local.add_argument(
        "--fragment", "--frag",
        dest="pFragments",
        nargs="*",
        metavar="Topic fragment",
        default=None,
        help="String fragment(s) to be looked for in the topic names"
    )
    local.add_argument(
        "--exact",
        dest="pExact",
        action="store_true",
        help="Look for exact match of fragment, instead of substring"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"SNS Topics operation version {__version__}"
    )

def find_all_topics(fAllCredentials: list, ftopic_frag: list = None, fexact: bool = False) -> list:
    """
    Find all SNS topics from all accounts/regions within the credentials supplied
    """
    
    class FindTopics(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials = self.queue.get()
                logging.info(f"Processing account {c_account_credentials['AccountId']}")
                try:
                    account_topics = Inventory_Modules.find_sns_topics2(c_account_credentials, ftopic_frag, fexact)
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(account_topics)} topics")
                    
                    for topic in account_topics:
                        AllTopics.append({
                            'MgmtAccount': c_account_credentials['MgmtAccount'],
                            'AccountId': c_account_credentials['AccountId'],
                            'Region': c_account_credentials['Region'],
                            'ParentProfile': c_account_credentials.get('ParentProfile', 'Unknown'),
                            'TopicName': topic,
                            'TopicArn': f"arn:aws:sns:{c_account_credentials['Region']}:{c_account_credentials['AccountId']}:{topic}"
                        })
                        
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
    AllTopics = []
    WorkerThreads = min(len(fAllCredentials), 25)

    pbar = tqdm(
        desc=f'Finding SNS topics from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )

    # Start worker threads
    for x in range(WorkerThreads):
        worker = FindTopics(checkqueue)
        worker.daemon = True
        worker.start()

    # Queue all credentials
    for credential in fAllCredentials:
        checkqueue.put(credential)

    checkqueue.join()
    pbar.close()
    return AllTopics

def run(args):
    """Main execution function for topics operation"""
    # Get timing context from CLI (if available)
    timing = getattr(args, '_timing_context', None)
    
    # Extract arguments
    pProfiles = args.Profiles
    pRegionList = args.Regions
    pAccounts = args.Accounts
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pAccessRoles = args.AccessRoles
    pFragments = getattr(args, 'pFragments', None)
    pExact = getattr(args, 'pExact', False)
    pRootOnly = args.RootOnly
    pFilename = args.Filename
    pTiming = args.Time
    
    print("Searching for SNS topics...")
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
    
    # Find all topics
    AllTopics = find_all_topics(CredentialList, pFragments, pExact)
    
    if timing:
        timing.milestone("topics_found", f"Found {len(AllTopics)} topics")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'TopicName': {'DisplayOrder': 5, 'Heading': 'Topic Name'},
        'TopicArn': {'DisplayOrder': 6, 'Heading': 'Topic ARN'}
    }

    sorted_topics = sorted(AllTopics, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['Region'], d['TopicName']
    ))
    
    display_results(sorted_topics, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllTopics)} topics across {AccountNum} accounts and {RegionNum} regions")