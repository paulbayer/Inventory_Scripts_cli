#!/usr/bin/env python3
"""SAML Providers inventory operation"""

import logging
from tqdm.auto import tqdm
from botocore.exceptions import ClientError

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import get_all_credentials, display_results

__version__ = "2025.07.11"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('saml-providers', 'SAML Providers specific options')
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"SAML Providers operation version {__version__}"
    )

def find_all_saml_providers(fAllCredentials: list) -> list:
    """
    Find all SAML providers from all accounts within the credentials supplied
    """
    AllSamlProviders = []

    for credential in tqdm(fAllCredentials, desc="Processing accounts", unit="accounts"):
        try:
            if credential.get('AccountStatus', 'ACTIVE') == 'ACTIVE':
                logging.info(f"Getting SAML providers for account {credential['AccountId']}")
                
                try:
                    Idps = Inventory_Modules.find_saml_components_in_acct2(credential)
                    idpNum = len(Idps)
                    logging.info(f"Account: {credential['AccountId']} | Region: {credential['Region']} | Found {idpNum} SAML providers")

                    for idp in Idps:
                        logging.info(f"Arn: {idp['Arn']}")
                        NameStart = idp['Arn'].find('/') + 1
                        IdpName = idp['Arn'][NameStart:]
                        
                        AllSamlProviders.append({
                            'MgmtAccount': credential['MgmtAccount'],
                            'AccountNumber': credential['AccountId'],
                            'Region': credential['Region'],
                            'ParentProfile': credential.get('ParentProfile', 'Unknown'),
                            'IdpName': IdpName,
                            'Arn': idp['Arn'],
                            'CreateDate': idp.get('CreateDate', 'Unknown'),
                            'ValidUntil': idp.get('ValidUntil', 'Unknown')
                        })
                        
                except ClientError as my_Error:
                    if "AuthFailure" in str(my_Error):
                        logging.error(f"Authorization failure for account {credential['AccountId']}")
                    else:
                        logging.error(f"AWS API error for account {credential['AccountId']}: {my_Error}")
            else:
                logging.info(f"Skipping account {credential['AccountId']} since it's SUSPENDED or CLOSED")
                
        except KeyError as my_Error:
            logging.error(f"Key Error: {my_Error}")
            continue
        except Exception as my_Error:
            logging.error(f"Unexpected error for account {credential['AccountId']}: {my_Error}")

    return AllSamlProviders

def run(args):
    """Main execution function for saml-providers operation"""
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
    
    print("Searching for SAML providers...")
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
    
    # Find all SAML providers
    AllSamlProviders = find_all_saml_providers(CredentialList)
    
    if timing:
        timing.milestone("saml_providers_found", f"Found {len(AllSamlProviders)} SAML providers")
    
    # Display results
    display_dict = {
        'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
        'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
        'AccountNumber': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
        'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
        'IdpName': {'DisplayOrder': 5, 'Heading': 'IdP Name'},
        'CreateDate': {'DisplayOrder': 6, 'Heading': 'Created'},
        'ValidUntil': {'DisplayOrder': 7, 'Heading': 'Valid Until'},
        'Arn': {'DisplayOrder': 8, 'Heading': 'Arn'}
    }

    sorted_providers = sorted(AllSamlProviders, key=lambda d: (
        d['ParentProfile'], d['AccountNumber'], d['Region'], d['IdpName']
    ))
    
    display_results(sorted_providers, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllSamlProviders)} SAML providers across {AccountNum} accounts in {RegionNum} regions")