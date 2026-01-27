#!/usr/bin/env python3
"""Elastic Network Interfaces inventory operation"""

import logging
import socket
from queue import Queue
from threading import Thread
from tqdm.auto import tqdm
from botocore.exceptions import ClientError
from colorama import Fore

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

__version__ = "2025.07.11"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('enis', 'Elastic Network Interfaces specific options')
    local.add_argument(
        "--ipaddress", "--ip",
        dest="pipaddresses",
        nargs="*",
        metavar="IP address",
        default=None,
        help="IP address(es) you're looking for within your accounts"
    )
    local.add_argument(
        "--fqdn", "--name",
        dest="pDNSNames",
        nargs="*",
        metavar="Fully Qualified Domain Name",
        default=None,
        help="DNS Name(s) you're looking to find within your accounts"
    )
    local.add_argument(
        "--public-only", "--po",
        action="store_true",
        dest="ppublic",
        help="Whether you want to return only those results with a Public IP"
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"Elastic Network Interfaces operation version {__version__}"
    )

def find_all_enis(fAllCredentials: list, fip: list = None, fPublicOnly: bool = False) -> list:
    """
    Find all ENIs from all accounts/regions within the credentials supplied
    """
    
    class FindENIs(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                c_account_credentials = self.queue.get()
                logging.info(f"Processing account {c_account_credentials['AccountId']}")
                try:
                    account_enis = Inventory_Modules.find_account_enis2(c_account_credentials, c_account_credentials['Region'], fip)
                    logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(account_enis)} ENIs")
                    
                    for eni in account_enis:
                        eni['MgmtAccount'] = c_account_credentials['MgmtAccount']
                        eni['ParentProfile'] = c_account_credentials.get('ParentProfile', 'Unknown')
                        
                        # Filter by public IP if requested
                        if fPublicOnly and eni.get('PublicIp', 'No Public IP') == "No Public IP":
                            continue
                        
                        AllENIs.append(eni)
                        
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
    AllENIs = []
    WorkerThreads = min(len(fAllCredentials), 25)

    pbar = tqdm(
        desc=f'Finding ENIs from {len(fAllCredentials)} locations',
        total=len(fAllCredentials), 
        unit=' locations'
    )

    # Start worker threads
    for x in range(WorkerThreads):
        worker = FindENIs(checkqueue)
        worker.daemon = True
        worker.start()

    # Queue all credentials
    for credential in fAllCredentials:
        checkqueue.put(credential)

    checkqueue.join()
    pbar.close()
    return AllENIs


def resolve_names_to_ips(f_fqdns: list = None):
    """
    Resolves names to IPs before we begin to search
    @param f_fqdns: A list of names that need to be resolved to external IP addresses, to search on
    @return: A list - containing the IP addresses for the names passed in
    """
    # Resolve FQDNs to IP addresses using DNS lookup
    resolved_ips = []
    for fqdn in f_fqdns:
        try:
            # Get all IP addresses for the FQDN
            result = socket.getaddrinfo(fqdn, None)
            # Extract unique IP addresses from the result
            ips = {'fqdn': fqdn, 'IPs': list(set([addr[4][0] for addr in result]))}
            resolved_ips.append(ips)
            logging.info(f"Resolved {fqdn} to IPs: {ips}")
        except socket.gaierror as e:
            logging.warning(f"Failed to resolve {fqdn}: {e}")

    return resolved_ips

def run(args):
    """Main execution function for enis operation"""
    # Get timing context from CLI (if available)
    timing = getattr(args, '_timing_context', None)
    
    # Extract arguments
    pProfiles = args.Profiles
    pRegionList = args.Regions
    pAccounts = args.Accounts
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pAccessRoles = args.AccessRoles
    pIPaddressList = getattr(args, 'pipaddresses', None)
    pDNSNames = getattr(args, 'pDNSNames', None)
    pPublicOnly = getattr(args, 'ppublic', False)
    pRootOnly = args.RootOnly
    pFilename = args.Filename
    pTiming = args.Time
    verbose = args.loglevel
    
    print("Searching for Elastic Network Interfaces...")
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
    
    # Resolve FQDNs to IPs and add to IP address list
    fqdn_resolutions = []
    if pDNSNames is not None:
        fqdn_resolutions = resolve_names_to_ips(pDNSNames)
        fqdn_ips = [ip for x in fqdn_resolutions for ip in x['IPs']]
        
        if pIPaddressList is None:
            pIPaddressList = fqdn_ips
        else:
            pIPaddressList.extend(fqdn_ips)
    
    # Find all ENIs
    AllENIs = find_all_enis(CredentialList, pIPaddressList, pPublicOnly)
    
    if timing:
        timing.milestone("enis_found", f"Found {len(AllENIs)} ENIs")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'PrivateDnsName': {'DisplayOrder': 5, 'Heading': 'ENI Name'},
        'Status': {'DisplayOrder': 6, 'Heading': 'Status', 'Condition': ['available', 'attaching', 'detaching']},
        'PublicIp': {'DisplayOrder': 7, 'Heading': 'Public IP Address'},
        'ENIId': {'DisplayOrder': 8, 'Heading': 'ENI Id'},
        'PrivateIpAddress': {'DisplayOrder': 9, 'Heading': 'Assoc. IP'}
    }

    sorted_enis = sorted(AllENIs, key=lambda d: (
        d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['Region'], d.get('ENIId', '')
    ))
    
    display_results(sorted_enis, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    # Show summary of detached ENIs (potential cost savings)
    detached_enis = [x for x in AllENIs if x.get('Status') in ['available', 'attaching', 'detaching']]
    
    print(f"\nFound {len(AllENIs)} ENIs{' with public IPs' if pPublicOnly else ''} across {AccountNum} accounts and {RegionNum} regions")
    if detached_enis:
        print(f"Found {len(detached_enis)} ENIs that are not listed as 'in-use' and may be costing additional money while unused.")
    
    # Display DNS resolution results if FQDNs were provided
    if pDNSNames is not None and verbose < 50:
        print(f"\nYou asked me to resolve {len(pDNSNames)} DNS Names")
        for fqdn in fqdn_resolutions:
            print(f"    DNS Name: {Fore.RED}{fqdn['fqdn']}{Fore.RESET} resolved to {Fore.RED}{fqdn['IPs']}{Fore.RESET}")