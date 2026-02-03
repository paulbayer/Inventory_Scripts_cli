#!/usr/bin/env python3
"""
CloudFormation StackSets inventory operation with modification capabilities
"""

import logging
import sys
from time import time, sleep
from botocore.exceptions import ClientError
from colorama import Fore, Style, init
from tqdm.auto import tqdm

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import (
    get_all_credentials, display_results, find_stacksets2, find_stack_instances2,
    delete_stack_instances3, delete_stackset3, check_stack_set_status3, random_string
)

init()
__version__ = "2026.02.03"
ERASE_LINE = '\x1b[2K'
SLEEP_INTERVAL = 5


def check_accounts_in_org(fCredentials: dict, fAccountList: list) -> dict:
    """
    Compare stackset accounts against Organization accounts
    
    Args:
        fCredentials: Credential dictionary with account access
        fAccountList: List of account IDs found in stacksets
        
    Returns:
        dict with RemovedAccounts and InaccessibleAccounts
    """
    from inv_scr.core.account_class import aws_acct_access
    from inv_scr.core.Inventory_Modules import get_child_access3
    
    # Get org accounts
    aws_acct = aws_acct_access(fCredentials.get('Profile'))
    org_account_list = [acct['AccountId'] for acct in aws_acct.ChildAccounts]
    
    logging.info(f"Found {len(org_account_list)} accounts in Org, {len(fAccountList)} unique accounts in stacksets")
    
    removed_accounts = list(set(fAccountList) - set(org_account_list))
    inaccessible_accounts = []
    
    # Check accessibility of accounts
    for account_id in fAccountList:
        logging.debug(f"Checking access to account {account_id}")
        try:
            creds = get_child_access3(aws_acct, account_id)
            if creds.get('AccessError'):
                inaccessible_accounts.append({
                    'AccountId': account_id,
                    'Success': creds.get('Success', False),
                    'RolesTried': creds.get('RolesTried', [])
                })
        except Exception as e:
            logging.warning(f"Error checking access to account {account_id}: {e}")
    
    return {
        'RemovedAccounts': removed_accounts,
        'InaccessibleAccounts': inaccessible_accounts,
        'AccountList': fAccountList
    }


def delete_stack_instances(fCredentials: dict, fRegion: str, fStackSetName: str,
                          fRetain: bool, fAccountList: list, fRegionList: list,
                          fPermissionModel: str = 'SELF_MANAGED',
                          fDeploymentTargets: dict = None) -> dict:
    """
    Delete stack instances from a stackset
    
    Args:
        fCredentials: Credential dictionary with account access
        fRegion: AWS region where the stackset is managed
        fStackSetName: Name of the stackset to modify
        fRetain: Whether to retain stacks in child accounts after deletion
        fAccountList: List of account IDs to remove instances from
        fRegionList: List of regions to remove instances from
        fPermissionModel: Permission model (SELF_MANAGED or SERVICE_MANAGED)
        fDeploymentTargets: Deployment targets for SERVICE_MANAGED stacksets
        
    Returns:
        dict with Success status, OperationId, or ErrorMessage
    """
    from inv_scr.core.account_class import aws_acct_access
    
    logging.info(f"Removing instances from {fStackSetName} StackSet")
    
    if ((fAccountList is None or not fAccountList) and fPermissionModel.upper() == 'SELF_MANAGED') or \
       (fRegionList is None or not fRegionList):
        logging.error("AccountList and RegionList cannot be null for SELF_MANAGED")
        return {'Success': True, 'ErrorMessage': "Failed - Account List or Region List was null"}
    
    if fPermissionModel == 'SERVICE_MANAGED' and fDeploymentTargets is None:
        logging.error("SERVICE_MANAGED stackset requires deployment targets")
        return {'Success': False, 'ErrorMessage': "Failed - No deployment target provided"}
    
    try:
        aws_acct = aws_acct_access(fCredentials.get('Profile'))
        operation_id = f"DeleteInstances-{random_string(5)}"
        
        result = delete_stack_instances3(
            aws_acct, fRegion, fRegionList, fStackSetName, fRetain,
            operation_id, fAccountList, fPermissionModel, fDeploymentTargets
        )
        
        if result.get('Success'):
            return {'Success': True, 'OperationId': result['OperationId']}
        else:
            return {'Success': False, 'ErrorMessage': result.get('ErrorMessage')}
            
    except ClientError as e:
        if e.response['Error']['Code'] == 'StackSetNotFoundException':
            logging.info("StackSet not found, ignoring...")
            return {'Success': False, 'ErrorMessage': "Failed - StackSet not found"}
        else:
            logging.error(f"Error deleting stack instances: {e}")
            return {'Success': False, 'ErrorMessage': f"Failed - {str(e)}"}
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return {'Success': False, 'ErrorMessage': f"Failed - {str(e)}"}


def add_stack_instances(fCredentials: dict, fRegion: str, fStackSetName: str,
                       fAccountList: list, fRegionList: list) -> dict:
    """
    Add stack instances to a stackset
    
    Args:
        fCredentials: Credential dictionary with account access
        fRegion: AWS region where the stackset is managed
        fStackSetName: Name of the stackset to modify
        fAccountList: List of account IDs to add instances to
        fRegionList: List of regions to add instances to
        
    Returns:
        dict with Success status, OperationId, or ErrorMessage
    """
    from inv_scr.core.account_class import aws_acct_access
    
    try:
        aws_acct = aws_acct_access(fCredentials.get('Profile'))
        cfn_client = aws_acct.session.client('cloudformation', region_name=fRegion)
        operation_id = f"Add-Instances-{random_string(6)}"
        
        response = cfn_client.create_stack_instances(
            StackSetName=fStackSetName,
            Accounts=fAccountList,
            Regions=fRegionList,
            OperationPreferences={
                'RegionConcurrencyType': 'PARALLEL',
                'MaxConcurrentPercentage': 100,
                'FailureToleranceCount': 0
            },
            OperationId=operation_id,
            CallAs='SELF'
        )
        
        return {'Success': True, 'OperationId': operation_id}
        
    except Exception as e:
        logging.error(f"Error adding stack instances: {e}")
        return {'Success': False, 'ErrorMessage': str(e)}


def refresh_stackset(fCredentials: dict, fRegion: str, fStackSetName: str,
                    fPermissionModel: str) -> dict:
    """
    Refresh a stackset with current configuration
    
    Args:
        fCredentials: Credential dictionary with account access (must contain AccessKeyId, SecretAccessKey, SessionToken)
        fRegion: AWS region where the stackset is managed
        fStackSetName: Name of the stackset to refresh
        fPermissionModel: Permission model (SELF_MANAGED or SERVICE_MANAGED)
        
    Returns:
        dict with Success status, OperationId, or ErrorMessage
    """
    import boto3
    
    try:
        logging.debug(f"Refreshing stackset {fStackSetName} in account {fCredentials['AccountId']} region {fRegion}")
        
        # Create boto3 session using the credentials for the account where the stackset resides
        session_aws = boto3.Session(
            region_name=fRegion,
            aws_access_key_id=fCredentials['AccessKeyId'],
            aws_secret_access_key=fCredentials['SecretAccessKey'],
            aws_session_token=fCredentials['SessionToken']
        )
        cfn_client = session_aws.client('cloudformation')
        
        # Get current stackset attributes
        stackset_attrs = cfn_client.describe_stack_set(StackSetName=fStackSetName)
        stackset = stackset_attrs['StackSet']
        
        # Build update parameters
        update_params = {
            'StackSetName': fStackSetName,
            'UsePreviousTemplate': True,
            'Capabilities': stackset.get('Capabilities', []),
            'OperationPreferences': {
                'RegionConcurrencyType': 'PARALLEL',
                'FailureToleranceCount': 0,
                'MaxConcurrentPercentage': 100
            }
        }
        
        # Add AdministrationRoleARN only for SELF_MANAGED
        if fPermissionModel != 'SERVICE_MANAGED':
            update_params['AdministrationRoleARN'] = stackset.get('AdministrationRoleARN')

        logging.debug(f"Update Params: {update_params}")
        response = cfn_client.update_stack_set(**update_params)
        logging.debug(f"Response: {response}")

        return {'Success': True, 'OperationId': response['OperationId']}
        
    except Exception as e:
        logging.error(f"Error refreshing stackset: {e}")
        return {'Success': False, 'ErrorMessage': str(e)}


def monitor_stackset_operations(fCredentials: dict, fOperationsList: list,
                               fSleepInterval: int = 5) -> dict:
    """
    Monitor stackset operations until completion
    
    Args:
        fCredentials: Credential dictionary with account access
        fOperationsList: List of operations to monitor (each with StackSetName and OperationId)
        fSleepInterval: Seconds to wait between status checks
        
    Returns:
        dict mapping stackset names to their final operation status
    """
    from inv_scr.core.account_class import aws_acct_access
    
    if not fOperationsList:
        return {}
    
    aws_acct = aws_acct_access(fCredentials.get('Profile'))
    region = fCredentials.get('Region', 'us-east-1')
    cfn_client = aws_acct.session.client('cloudformation', region_name=region)
    
    print("Monitoring stackset operations (Ctrl-C to quit, operations continue in background)...")
    
    stackset_results = {}
    still_running = True
    
    while still_running:
        still_running = False
        
        for operation in fOperationsList:
            try:
                status_response = cfn_client.describe_stack_set_operation(
                    StackSetName=operation['StackSetName'],
                    OperationId=operation['OperationId']
                )
                
                status = status_response['StackSetOperation']['Status']
                print(f"StackSet: {operation['StackSetName']} | Status: {status}")
                
                still_running = still_running or (status == 'RUNNING')
                stackset_results[operation['StackSetName']] = status
                
            except Exception as e:
                logging.warning(f"Error checking operation status: {e}")
                stackset_results[operation['StackSetName']] = 'UNKNOWN'
        
        if still_running:
            print(f"Waiting {fSleepInterval} seconds before checking again...\n")
            sleep(fSleepInterval)
    
    return stackset_results


def get_deployment_targets(fCredentials: dict, fRegion: str, fStackSetName: str,
                          fAccountList: list = None) -> dict:
    """
    Get deployment target information for SERVICE_MANAGED stacksets
    
    Args:
        fCredentials: Credential dictionary with account access
        fRegion: AWS region where the stackset is managed
        fStackSetName: Name of the stackset to query
        fAccountList: Optional list of specific account IDs (if None, returns all OUs)
        
    Returns:
        dict with Success status and Results containing deployment targets
    """
    try:
        instances = find_stack_instances2(fCredentials, fRegion, fStackSetName)
        
        if fAccountList is None:
            # Get all OUs from instances
            identified_ous = list(set([
                inst.get('OrganizationalUnitId') 
                for inst in instances 
                if inst.get('OrganizationalUnitId')
            ]))
            
            deployment_targets = {
                'OrganizationalUnitIds': identified_ous
            }
        else:
            deployment_targets = {
                'Accounts': fAccountList
            }
        
        return {'Success': True, 'Results': deployment_targets}
        
    except Exception as e:
        logging.error(f"Error getting deployment targets: {e}")
        return {'Success': False, 'ErrorMessage': str(e)}


def display_stackset_health(fStackSets: list, fShowDetails: bool = False,
                           fRemovedAccounts: list = None,
                           fInaccessibleAccounts: list = None,
                           fShowDate: bool = False) -> None:
    """
    Display comprehensive stackset health information
    
    Args:
        fStackSets: List of stackset records to display
        fShowDetails: Whether to show detailed instance-level information
        fRemovedAccounts: List of account IDs that are no longer in the organization
        fInaccessibleAccounts: List of account info dicts for inaccessible accounts
        fShowDate: Whether to include last operation date in output
        
    Returns:
        None (prints formatted output to console)
    """
    if not fStackSets:
        return
    
    # Group by stackset name
    summary = {}
    permission_models = {}
    
    for record in fStackSets:
        stackset_name = record.get('StackSetName')
        stack_status = record.get('StackStatus')  # Note: StackStatus not Status
        
        permission_models[stackset_name] = record.get('PermissionModel', 'SELF_MANAGED')
        
        if stackset_name not in summary:
            summary[stackset_name] = {}
        
        if stack_status not in summary[stackset_name]:
            summary[stackset_name][stack_status] = []
        
        summary[stackset_name][stack_status].append({
            'Account': record.get('ChildAccount'),
            'Region': record.get('ChildRegion'),
            'DetailedStatus': record.get('DetailedStatus'),
            'StatusReason': record.get('StatusReason'),
            'LastOperation': record.get('LastOperationId')
        })
    
    # Print summary
    print()
    for stackset_name, status_counts in sorted(summary.items()):
        perm_model = permission_models.get(stackset_name, 'SELF_MANAGED')
        print(f"{stackset_name} ({perm_model}):")
        
        for stack_status, instances in status_counts.items():
            if stack_status is None:
                print(f"\t{Fore.RED}--Empty stackset--{Fore.RESET}")
            else:
                color = '' if stack_status == 'CURRENT' else Fore.RED
                print(f"\t{color}{stack_status}: {len(instances)} instances{Fore.RESET}")
            
            if fShowDetails and instances:
                # Group by account
                by_account = {}
                for inst in instances:
                    acct = inst['Account']
                    if acct and acct not in by_account:
                        by_account[acct] = {
                            'Regions': [],
                            'DetailedStatus': inst['DetailedStatus'],
                            'StatusReason': inst['StatusReason']
                        }
                    if acct:
                        by_account[acct]['Regions'].append(inst['Region'])
                
                for acct, info in sorted(by_account.items()):
                    # Highlight orphaned accounts
                    if fRemovedAccounts and acct in fRemovedAccounts:
                        print(f"{Style.BRIGHT}{Fore.MAGENTA}\t\t{acct}: {info['Regions']} "
                              f"<-- Orphaned account!{Style.RESET_ALL}")
                    else:
                        print(f"\t\t{acct}: {info['Regions']}")
                    
                    # Show detailed status if not CURRENT
                    if stack_status != 'CURRENT' and info['DetailedStatus']:
                        print(f"\t\t\t{Fore.RED}Detailed Status: {info['DetailedStatus']}{Fore.RESET}")
                        if info['StatusReason']:
                            print(f"\t\t\tReason: {info['StatusReason']}")
    
    print()
    if fRemovedAccounts:
        print(f"{Fore.YELLOW}Found {len(fRemovedAccounts)} accounts in stacksets "
              f"that are not in the Organization{Fore.RESET}")
        for acct in fRemovedAccounts:
            print(f"  - {acct}")
        print()
    
    if fInaccessibleAccounts:
        print(f"{Fore.YELLOW}Found {len(fInaccessibleAccounts)} inaccessible accounts{Fore.RESET}")
        for acct_info in fInaccessibleAccounts:
            print(f"  - {acct_info['AccountId']}: Roles tried: {acct_info.get('RolesTried', [])}")
        print()


def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('cfnstacksets', 'CloudFormation StackSets specific options')
    
    # Existing read-only arguments
    local.add_argument(
        "-f", "--fragment",
        dest="pFragments",
        nargs='*',
        metavar="string fragment",
        default=["all"],
        help="List of fragments of the stackset name(s) you want to check for."
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
        metavar="CloudFormation status",
        default="ACTIVE",
        choices=['active', 'ACTIVE', 'Active', 'deleted', 'DELETED', 'Deleted'],
        help="String that determines whether we only see 'ACTIVE' or 'DELETED' stacksets. Default is 'ACTIVE'"
    )
    local.add_argument(
        "-i", "--instances",
        dest="pInstanceCount",
        action="store_true",
        default=False,
        help="Flag to determine whether you want to see the instance totals for each stackset"
    )
    
    # Add confirm flag using CommonArguments helper
    parser.confirm()
    
    # Operation mode (mutually exclusive)
    operation_group = local.add_mutually_exclusive_group()
    operation_group.add_argument(
        "+delete", "+remove",
        help="Delete stack instances from stacksets",
        action="store_true",
        dest="pDelete"
    )
    operation_group.add_argument(
        "+add",
        help="Add stack instances to stacksets",
        action="store_true",
        dest="pAdd"
    )
    operation_group.add_argument(
        "+refresh",
        help="Refresh stacksets with current configuration",
        action="store_true",
        dest="pRefresh"
    )
    
    # Modification options
    local.add_argument(
        "+R", "+modreg", "+modregion",
        help="Region(s) to add or remove from stacksets",
        nargs="*",
        metavar="region-name",
        dest="pModifyRegions"
    )
    local.add_argument(
        "+A", "+modacc", "+modacct", "+addacct", "+ModifyAccount",
        help="Account(s) to add or remove from stacksets",
        nargs="*",
        metavar="account-id",
        dest="pModifyAccounts"
    )
    local.add_argument(
        "--retain", "--disassociate",
        help="Retain stacks in child accounts when removing instances (requires +delete)",
        action="store_true",
        dest="pRetain"
    )
    local.add_argument(
        "-c", "--check",
        help="Check for closed/suspended accounts in stacksets",
        action="store_true",
        dest="pCheckAccounts"
    )
    local.add_argument(
        "--date",
        help="Include last operation date in detailed output",
        action="store_true",
        dest="pShowDate"
    )
    
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"CloudFormation StackSets operation version {__version__}"
    )


def find_all_cfnstacksets(fAllCredentials: list, fFragments: list = None, fStatus: str = "ACTIVE", fInstanceCount: bool = False, fGetInstances: bool = False) -> list:
    """
    Find all CloudFormation StackSets from all accounts/regions within the credentials supplied
    
    Args:
        fAllCredentials: List of credential dictionaries
        fFragments: List of stackset name fragments to match
        fStatus: Status filter (ACTIVE/DELETED)
        fInstanceCount: Whether to include instance counts (for summary view)
        fGetInstances: Whether to return individual stack instances (for detailed view)
        
    Returns:
        List of stackset records or stack instance records depending on fGetInstances
    """
    All_Results = []
    
    for credential in fAllCredentials:
        if not credential.get('Success', True):
            logging.error(f"Failure for account {credential['AccountId']} in region {credential['Region']}")
            continue
            
        print(f"{ERASE_LINE}{Fore.RED}Checking Account: {credential['AccountId']} Region: {credential['Region']} for stacksets matching {fFragments} with status: {fStatus}{Fore.RESET}", end="\r")
        
        try:
            StackSets = Inventory_Modules.find_stacksets2(credential, fFragments, fStatus)
            logging.info(f"Account: {credential['AccountId']} | Region: {credential['Region']} | Found {len(StackSets)} StackSets")
            
            if not StackSets:
                logging.info(f"Connected to account {credential['AccountId']} in region {credential['Region']}, but found no stacksets")
            else:
                print(f"{ERASE_LINE}{Fore.RED}Account: {credential['AccountId']} Region: {credential['Region']} Found {len(StackSets)} StackSets{Fore.RESET}", end="\r")

            # TODO: There is a significant pause here, while the operation goes through every stackset, to count the instances.
            # We need to better inform the user what this delay is for...
            for stack in StackSets:
                # Get permission model from stackset
                permission_model = stack.get('PermissionModel', 'SELF_MANAGED')
                
                # If we need instances (for modifications or detailed view)
                if fGetInstances or fInstanceCount:
                    milestone = time()
                    try:
                        ListOfStackInstances = Inventory_Modules.find_stack_instances2(credential, credential['Region'], stack['StackSetName'])
                        logging.info(f"Found {len(ListOfStackInstances)} instances for {stack['StackSetName']} in {credential['Region']}, which took {time() - milestone:.2f} seconds")
                        
                        if fGetInstances:
                            # Return individual stack instances (like legacy script)
                            if len(ListOfStackInstances) == 0:
                                # Empty stackset - add a placeholder record
                                All_Results.append({
                                    'ParentAccountNumber': credential['AccountId'],
                                    'ChildAccount': None,
                                    'ChildRegion': None,
                                    'StackStatus': None,
                                    'DetailedStatus': None,
                                    'StatusReason': None,
                                    'OrganizationalUnitId': None,
                                    'PermissionModel': permission_model,
                                    'StackSetName': stack['StackSetName'],
                                    'LastOperationId': None,
                                    'ParentProfile': credential.get('ParentProfile', 'Unknown'),
                                    'Region': credential['Region']
                                })
                            else:
                                for instance in ListOfStackInstances:
                                    All_Results.append({
                                        'ParentAccountNumber': credential['AccountId'],
                                        'ChildAccount': instance.get('Account'),
                                        'ChildRegion': instance.get('Region'),
                                        'StackStatus': instance.get('Status'),
                                        'DetailedStatus': instance.get('StackInstanceStatus', {}).get('DetailedStatus'),
                                        'StatusReason': instance.get('StatusReason'),
                                        'OrganizationalUnitId': instance.get('OrganizationalUnitId'),
                                        'PermissionModel': permission_model,
                                        'StackSetName': stack['StackSetName'],
                                        'LastOperationId': instance.get('LastOperationId'),
                                        'ParentProfile': credential.get('ParentProfile', 'Unknown'),
                                        'Region': credential['Region']
                                    })
                        else:
                            # Return stackset summary with instance count
                            All_Results.append({
                                'MgmtAccount': credential['MgmtAccount'],
                                'AccountId': credential['AccountId'],
                                'Region': credential['Region'],
                                'StackSetName': stack['StackSetName'],
                                'Status': stack['Status'],
                                'InstanceNum': len(ListOfStackInstances),
                                'ParentProfile': credential.get('ParentProfile', 'Unknown')
                            })
                    except Exception as e:
                        logging.warning(f"Failed to get instances for {stack['StackSetName']}: {e}")
                        if not fGetInstances:
                            # Still add stackset record even if instance fetch failed
                            All_Results.append({
                                'MgmtAccount': credential['MgmtAccount'],
                                'AccountId': credential['AccountId'],
                                'Region': credential['Region'],
                                'StackSetName': stack['StackSetName'],
                                'Status': stack['Status'],
                                'InstanceNum': 'Error',
                                'ParentProfile': credential.get('ParentProfile', 'Unknown')
                            })
                else:
                    # Simple stackset listing without instances
                    All_Results.append({
                        'MgmtAccount': credential['MgmtAccount'],
                        'AccountId': credential['AccountId'],
                        'Region': credential['Region'],
                        'StackSetName': stack['StackSetName'],
                        'Status': stack['Status'],
                        'InstanceNum': 'N/A',
                        'ParentProfile': credential.get('ParentProfile', 'Unknown')
                    })
                
        except ClientError as my_Error:
            if 'AuthFailure' in str(my_Error):
                logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']} region")
            else:
                logging.error(f"Error accessing account {credential['AccountId']}: {my_Error}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error for account {credential['AccountId']}: {e}")
            continue
    
    return All_Results


def run(args):
    """Main execution function for CloudFormation StackSets operation with modification support"""
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
    pStatus = getattr(args, 'pStatus', 'ACTIVE')
    pInstanceCount = getattr(args, 'pInstanceCount', False)
    
    # Auto-enable instances flag when verbose level 3 (-vvv) is used
    if hasattr(args, 'loglevel') and args.loglevel <= 20:  # INFO level or more verbose
        pInstanceCount = True
        logging.info("Auto-enabling instance count display due to verbose level")
    
    # New modification arguments
    pDelete = getattr(args, 'pDelete', False)
    pAdd = getattr(args, 'pAdd', False)
    pRefresh = getattr(args, 'pRefresh', False)
    pModifyRegions = getattr(args, 'pModifyRegions', None)
    pModifyAccounts = getattr(args, 'pModifyAccounts', None)
    pRetain = getattr(args, 'pRetain', False)
    pCheckAccounts = getattr(args, 'pCheckAccounts', False)
    pShowDate = getattr(args, 'pShowDate', False)
    pConfirm = getattr(args, 'Confirm', False)
    
    # Determine operation mode
    changes_requested = pDelete or pAdd or pRefresh
    
    print("CloudFormation StackSets Operation")
    print(f"Version: {__version__}")
    print(f"Looking for stacksets with fragments: {Fore.RED}{pFragments}{Fore.RESET}")
    print(f"Status filter: {Fore.RED}{pStatus}{Fore.RESET}")
    
    if pExact:
        print(f"Using {Fore.RED}exact match{Fore.RESET} for stackset names")
    else:
        print(f"Using {Fore.RED}contains match{Fore.RESET} for stackset names")
    
    if changes_requested:
        operation = "delete" if pDelete else ("add" if pAdd else "refresh")
        print(f"{Fore.YELLOW}Operation mode: {operation.upper()}{Fore.RESET}")
        if pModifyRegions:
            print(f"Target regions: {Fore.RED}{pModifyRegions}{Fore.RESET}")
        if pModifyAccounts:
            print(f"Target accounts: {Fore.RED}{pModifyAccounts}{Fore.RESET}")
        if pRetain and pDelete:
            print(f"{Fore.YELLOW}Will RETAIN stacks in child accounts{Fore.RESET}")
    
    if pCheckAccounts:
        print(f"{Fore.YELLOW}Will check for orphaned accounts{Fore.RESET}")
    
    print()
    
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
    
    # Find all stacksets with detailed instance information if modifying or showing dates
    get_instances = changes_requested or pCheckAccounts or pShowDate
    AllStackSets = find_all_cfnstacksets(CredentialList, pFragments, pStatus, 
                                        fInstanceCount=pInstanceCount and not get_instances,
                                        fGetInstances=get_instances)
    
    if timing:
        timing.milestone("stacksets_found", f"Found {len(AllStackSets)} CloudFormation StackSets")
    
    # If no stacksets found, exit early
    if not AllStackSets:
        print(f"{Fore.YELLOW}No stacksets found matching criteria{Fore.RESET}")
        return
    
    # Check accounts if requested
    removed_accounts = []
    inaccessible_accounts = []
    if pCheckAccounts:
        unique_accounts = list(set([ss.get('ChildAccount') for ss in AllStackSets if ss.get('ChildAccount')]))
        if unique_accounts and CredentialList:
            account_check = check_accounts_in_org(CredentialList[0], unique_accounts)
            removed_accounts = account_check.get('RemovedAccounts', [])
            inaccessible_accounts = account_check.get('InaccessibleAccounts', [])
    
    # Handle modification operations
    if changes_requested:
        # Group stacksets by name for operations
        stacksets_by_name = {}
        for ss in AllStackSets:
            name = ss['StackSetName']
            if name not in stacksets_by_name:
                stacksets_by_name[name] = []
            stacksets_by_name[name].append(ss)
        
        operations_list = []
        
        if pDelete:
            print(f"\n{Fore.RED}DELETE Operation{Fore.RESET}")
            print(f"Will remove instances from {len(stacksets_by_name)} stackset(s)")
            
            if not pConfirm:
                confirm = input(f"{Fore.YELLOW}Are you sure you want to proceed? (y/n): {Fore.RESET}")
                if confirm.lower() not in ['y', 'yes']:
                    print("Operation cancelled")
                    return
            
            for stackset_name, instances in stacksets_by_name.items():
                # Get unique accounts and regions from instances
                accounts = list(set([i.get('ChildAccount') for i in instances if i.get('ChildAccount')]))
                regions = list(set([i.get('ChildRegion') for i in instances if i.get('ChildRegion')]))
                
                # Apply filters if specified
                if pModifyAccounts:
                    accounts = [a for a in accounts if a in pModifyAccounts]
                if pModifyRegions:
                    regions = [r for r in regions if r in pModifyRegions]
                
                if not accounts or not regions:
                    logging.info(f"No matching instances for {stackset_name} after filtering")
                    continue
                
                # Get permission model from first instance
                perm_model = instances[0].get('PermissionModel', 'SELF_MANAGED')
                deployment_targets = None
                
                if perm_model == 'SERVICE_MANAGED':
                    dt_result = get_deployment_targets(CredentialList[0], CredentialList[0]['Region'], 
                                                      stackset_name, pModifyAccounts)
                    if dt_result.get('Success'):
                        deployment_targets = dt_result['Results']
                
                print(f"Deleting instances from {stackset_name}...")
                result = delete_stack_instances(
                    CredentialList[0], CredentialList[0]['Region'], stackset_name,
                    pRetain, accounts, regions, perm_model, deployment_targets
                )
                
                if result.get('Success'):
                    operations_list.append({
                        'StackSetName': stackset_name,
                        'OperationId': result['OperationId']
                    })
                    print(f"  {Fore.GREEN}✓{Fore.RESET} Initiated deletion")
                else:
                    print(f"  {Fore.RED}✗{Fore.RESET} Failed: {result.get('ErrorMessage')}")
        
        elif pAdd:
            print(f"\n{Fore.GREEN}ADD Operation{Fore.RESET}")
            
            if not pModifyAccounts and not pModifyRegions:
                print(f"{Fore.RED}Error: Must specify accounts (+A) or regions (+R) to add{Fore.RESET}")
                return
            
            for stackset_name in stacksets_by_name.keys():
                # Get existing instances to determine regions if not specified
                instances = stacksets_by_name[stackset_name]
                existing_regions = list(set([i.get('ChildRegion') for i in instances if i.get('ChildRegion')]))
                
                accounts_to_add = pModifyAccounts if pModifyAccounts else []
                regions_to_add = pModifyRegions if pModifyRegions else existing_regions
                
                if not accounts_to_add or not regions_to_add:
                    logging.warning(f"Skipping {stackset_name}: no accounts or regions to add")
                    continue
                
                print(f"Adding instances to {stackset_name}...")
                result = add_stack_instances(
                    CredentialList[0], CredentialList[0]['Region'], stackset_name,
                    accounts_to_add, regions_to_add
                )
                
                if result.get('Success'):
                    operations_list.append({
                        'StackSetName': stackset_name,
                        'OperationId': result['OperationId']
                    })
                    print(f"  {Fore.GREEN}✓{Fore.RESET} Initiated addition")
                else:
                    print(f"  {Fore.RED}✗{Fore.RESET} Failed: {result.get('ErrorMessage')}")
        
        elif pRefresh:
            print(f"\n{Fore.CYAN}REFRESH Operation{Fore.RESET}")
            
            for stackset_name, instances in stacksets_by_name.items():
                perm_model = instances[0].get('PermissionModel', 'SELF_MANAGED')
                parent_account = instances[0].get('ParentAccountNumber')
                parent_region = instances[0].get('Region')
                
                # Find the credential for the account where this stackset resides
                stackset_credential = None
                for cred in CredentialList:
                    if cred['AccountId'] == parent_account and cred['Region'] == parent_region:
                        stackset_credential = cred
                        break
                
                if not stackset_credential:
                    logging.error(f"Could not find credentials for account {parent_account} in region {parent_region}")
                    print(f"  {Fore.RED}✗{Fore.RESET} Failed: No credentials found for parent account")
                    continue
                
                print(f"Refreshing {stackset_name}...")
                result = refresh_stackset(
                    stackset_credential, parent_region, stackset_name, perm_model
                )
                
                if result.get('Success'):
                    operations_list.append({
                        'StackSetName': stackset_name,
                        'OperationId': result['OperationId']
                    })
                    print(f"  {Fore.GREEN}✓{Fore.RESET} Initiated refresh")
                else:
                    print(f"  {Fore.RED}✗{Fore.RESET} Failed: {result.get('ErrorMessage')}")
        
        # Monitor operations if any were started
        if operations_list:
            print(f"\nMonitoring {len(operations_list)} operation(s)...")
            operation_results = monitor_stackset_operations(CredentialList[0], operations_list, SLEEP_INTERVAL)
            
            print(f"\n{Fore.CYAN}Operation Results:{Fore.RESET}")
            for stackset_name, status in operation_results.items():
                color = Fore.GREEN if status == 'SUCCEEDED' else Fore.RED
                print(f"  {stackset_name}: {color}{status}{Fore.RESET}")
            
            # Refresh view after changes
            print(f"\n{Fore.CYAN}Refreshing stackset view...{Fore.RESET}")
            AllStackSets = find_all_cfnstacksets(CredentialList, pFragments, pStatus, fGetInstances=True)
    
    # Display results
    if get_instances or changes_requested:
        # Use enhanced health display for instance-level data
        display_stackset_health(AllStackSets, fShowDetails=True,
                              fRemovedAccounts=removed_accounts,
                              fInaccessibleAccounts=inaccessible_accounts,
                              fShowDate=pShowDate)
    else:
        # Use standard table display for stackset-level data
        display_dict = {
            'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
            'MgmtAccount': {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
            'AccountId': {'DisplayOrder': 3, 'Heading': 'Acct Number'},
            'Region': {'DisplayOrder': 4, 'Heading': 'Region'},
            'Status': {'DisplayOrder': 5, 'Heading': 'Status'},
            'StackSetName': {'DisplayOrder': 6, 'Heading': 'StackSet Name'}
        }
        
        if pInstanceCount:
            display_dict['InstanceNum'] = {'DisplayOrder': 7, 'Heading': '# of Instances'}
        
        sorted_stacksets = sorted(AllStackSets, key=lambda d: (
            d['ParentProfile'], d.get('MgmtAccount', ''), d.get('AccountId', ''), d['Region'], d['StackSetName']
        ))
        
        display_results(sorted_stacksets, display_dict, None, pFilename)
    
    if timing:
        timing.milestone("results_displayed", "Results formatted and displayed")
    
    print(f"\nFound {len(AllStackSets)} CloudFormation StackSet instances across {AccountNum} accounts and {RegionNum} regions")
    # TODO: If the user wants more verbose output, we need to include a summary at the end of what we found, 
    # depending on the parameters they provided. If they asked for "--check", we should provide if there were 
    # orphaned accounts / regions within the stackset. If they provided a "-A" or "-R", we should provide the 
    # status of that operation.