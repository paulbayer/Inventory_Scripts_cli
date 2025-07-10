#!/usr/bin/env python3
"""
Elastic Load Balancers inventory operation
"""

import logging
from queue import Queue
from threading import Thread
from time import time
from tqdm.auto import tqdm
from botocore.exceptions import ClientError
from colorama import Fore, init

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

init()
__version__ = "2025.07.10"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('elbs', 'Elastic Load Balancers specific options')
    local.add_argument(
        "-f", "--fragment",
        dest="pFragments",
        nargs='*',
        metavar="string fragment",
        default=["all"],
        help="List of fragments of the load balancer name(s) you want to check for."
    )
    local.add_argument(
        "-e", "--exact",
        dest="pExact",
        action="store_true",
        help="Use this flag to make sure that ONLY the string you specified will be identified"
    )
    local.add_argument(
        "-s", "--status",
        dest="pStatus",
        metavar="Load balancer status",
        default="active",
        help="String that determines whether we only see 'active' or other statuses too"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"Elastic Load Balancers operation version {__version__}"
    )

def find_all_elbs(fAllCredentials: list, fFragments: list = None, fStatus: str = "active") -> list:
    """
    Find all Elastic Load Balancers from all accounts/regions within the credentials supplied
    """
    
    class FindLoadBalancers(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials, c_fragment, c_status = self.queue.get()
                logging.info(f"De-queued info for account number {c_account_credentials['AccountId']}")
                try:
                    LoadBalancers = Inventory_Modules.find_load_balancers2(c_account_credentials, c_fragment, c_status)
                    lb_count = len(LoadBalancers) if LoadBalancers else 0
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {lb_count} load balancers")
                    
                    if LoadBalancers:
                        for lb in LoadBalancers:
                            AllLoadBalancers.append({
                                'MgmtAccount': c_account_credentials['MgmtAccount'],
                                'AccountId': c_account_credentials['AccountId'],
                                'Region': c_account_credentials['Region'],
                                'ParentProfile': c_account_credentials.get('ParentProfile', 'Unknown'),
                                'Name': lb['LoadBalancerName'],
                                'Status': lb['State']['Code'],
                                'DNSName': lb['DNSName']
                            })
                        
                except KeyError as my_Error:
                    logging.error(f"Account Access failed - trying to access {c_account_credentials['AccountId']}")
                    logging.info(f"Actual Error: {my_Error}")
                    pass
                except AttributeError as my_Error:
                    logging.error(f"Error: Likely that one of the supplied profiles was wrong")
                    logging.warning(my_Error)
                    continue
                except ClientError as my_Error:
                    if "AuthFailure" in str(my_Error):
                        logging.error(f"Authorization Failure accessing account {c_account_credentials['AccountId']} in {c_account_credentials['Region']} region")
                        logging.warning(f"It's possible that the region {c_account_credentials['Region']} hasn't been opted-into")
                        continue
                    else:
                        logging.error(f"Error: Likely throttling errors from too much activity")
                        logging.warning(my_Error)
                        continue
                finally:
                    pbar.update()
                    self.queue.task_done()

    ###########

    checkqueue = Queue()
    AllLoadBalancers = []
    WorkerThreads = min(len(fAllCredentials), 10)

    pbar = tqdm(
        desc=f'Finding load balancers from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )

    for x in range(WorkerThreads):
        worker = FindLoadBalancers(checkqueue)
        worker.daemon = True
        worker.start()

    for credential in fAllCredentials:
        logging.info(f"Beginning to queue data - starting with {credential['AccountId']}")
        try:
            checkqueue.put((credential, fFragments, fStatus))
        except ClientError as my_Error:
            if "AuthFailure" in str(my_Error):
                logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']} region")
                logging.warning(f"It's possible that the region {credential['Region']} hasn't been opted-into")
                pass
    checkqueue.join()
    pbar.close()
    return AllLoadBalancers

def run(args):
    """Main execution function for ELB operation"""
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
    pFragments = getattr(args, 'pFragments', ['all'])
    pExact = getattr(args, 'pExact', False)
    pStatus = getattr(args, 'pStatus', 'active')
    
    print("Searching for Elastic Load Balancers...")
    print(f"Operation version: {__version__}")
    print(f"Looking for load balancers with fragments: {Fore.RED}{pFragments}{Fore.RESET}")
    print(f"Status filter: {Fore.RED}{pStatus}{Fore.RESET}")
    if pExact:
        print(f"Using {Fore.RED}exact match{Fore.RESET} for load balancer names")
    else:
        print(f"Using {Fore.RED}contains match{Fore.RESET} for load balancer names")
    
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
    
    # Find all load balancers
    AllLoadBalancers = find_all_elbs(CredentialList, pFragments, pStatus)
    
    if timing:
        timing.milestone("elbs_found", f"Found {len(AllLoadBalancers)} load balancers")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'Name': {'DisplayOrder': 5, 'Heading': 'Name'},
        'Status': {'DisplayOrder': 6, 'Heading': 'Status'},
        'DNSName': {'DisplayOrder': 7, 'Heading': 'DNS Name'}
    }

    sorted_elbs = sorted(AllLoadBalancers, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['Region'], d['Name']
    ))
    
    display_results(sorted_elbs, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllLoadBalancers)} Elastic Load Balancers across {AccountNum} accounts and {RegionNum} regions")