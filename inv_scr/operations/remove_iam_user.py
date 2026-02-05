#!/usr/bin/env python3
"""
Remove IAM user operation
Removes IAM users from AWS accounts with proper cleanup of associated resources

## TODO: Consider updating this tool to remove Identity Center users as well

This operation performs a comprehensive cleanup of an IAM user including:
- Access keys (all keys are deleted)
- MFA devices (deactivated and deleted)
- Signing certificates
- SSH public keys
- Service-specific credentials
- Console password (login profile)
- Attached managed policies (detached)
- Inline policies (deleted)
- Group memberships (removed)
- The IAM user itself

Safety features:
- Searches across all accessible accounts to find the user
- Displays all resources that will be removed before proceeding
- Requires explicit confirmation unless +force flag is used
- Supports --dry-run mode to preview changes without executing them
- Provides detailed success/error reporting for each resource

Usage examples:
  # Preview what would be removed
  inv_scr remove-iam-user +username john.doe --dry-run
  
  # Remove with confirmation prompt
  inv_scr remove-iam-user +username john.doe --profiles prod
  
  # Remove without confirmation
  inv_scr remove-iam-user +username john.doe +force --profiles prod
"""

import logging
import boto3
from typing import List, Dict, Any
from colorama import Fore, init

from tqdm.auto import tqdm
from botocore.exceptions import ClientError

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import (
    get_all_credentials,
    display_results,
)

__version__ = "2026.02.05"
init()

def add_operation_args(parser):
    """
    Add operation-specific arguments for remove-iam-user operation.
    
    Args:
        parser: CommonArguments parser instance to add arguments to
    """
    local = parser.my_parser.add_argument_group('remove-iam-user', 'Remove IAM user options')
    local.add_argument(
        "+username", "+user-name",
        dest="pUsername",
        metavar="USERNAME",
        help="IAM username to remove (required)",
    )
    local.add_argument(
        "+force",
        dest="pForce",
        action="store_true",
        help="Force removal without confirmation prompts",
    )
    local.add_argument(
        "--dry-run",
        dest="pDryRun",
        action="store_true",
        help="Show what would be removed without actually removing anything",
    )
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"Remove IAM user operation version {__version__}",
    )


def _find_user_resources(
    credentials: List[Dict[str, Any]],
    username: str,
) -> List[Dict[str, Any]]:
    """
    Find all instances of an IAM user across all accounts.
    
    Args:
        credentials: List of credential dictionaries for AWS accounts
        username: IAM username to search for
    
    Returns:
        List of dictionaries, each containing user information and associated resources for one account
    """
    import boto3
    
    found_users = []
    
    logging.info(f"Searching for user '{username}' across accounts...")
    
    # Search across all accounts for the user
    for cred in tqdm(
        credentials,
        desc=f"Searching for user '{username}'",
        unit="accounts",
    ):
        if not cred.get('Success', True):
            logging.info(
                "%s with roles: %s",
                cred.get('ErrorMessage'),
                cred.get('RolesTried'),
            )
            continue
        
        try:
            # Create IAM client
            session_iam = boto3.Session(
                aws_access_key_id=cred['AccessKeyId'],
                aws_secret_access_key=cred['SecretAccessKey'],
                aws_session_token=cred['SessionToken'],
                region_name='us-east-1',  # IAM is global
            )
            client_iam = session_iam.client('iam')
            
            # Try to get the user
            try:
                user_response = client_iam.get_user(UserName=username)
                
                user_info = {
                    'found': True,
                    'account_id': cred['AccountId'],
                    'mgmt_account': cred.get('MgmtAccount', cred['AccountId']),
                    'credentials': cred,
                    'user_details': user_response['User'],
                    'access_keys': [],
                    'mfa_devices': [],
                    'signing_certificates': [],
                    'ssh_public_keys': [],
                    'service_specific_credentials': [],
                    'login_profile': None,
                    'attached_policies': [],
                    'inline_policies': [],
                    'groups': [],
                }
                
                logging.info(f"Found user '{username}' in account {cred['AccountId']}")
                
                # Get access keys
                try:
                    keys_response = client_iam.list_access_keys(UserName=username)
                    user_info['access_keys'] = keys_response.get('AccessKeyMetadata', [])
                except ClientError as e:
                    logging.warning(f"Could not list access keys: {e}")
                
                # Get MFA devices
                try:
                    mfa_response = client_iam.list_mfa_devices(UserName=username)
                    user_info['mfa_devices'] = mfa_response.get('MFADevices', [])
                except ClientError as e:
                    logging.warning(f"Could not list MFA devices: {e}")
                
                # Get signing certificates
                try:
                    cert_response = client_iam.list_signing_certificates(UserName=username)
                    user_info['signing_certificates'] = cert_response.get('Certificates', [])
                except ClientError as e:
                    logging.warning(f"Could not list signing certificates: {e}")
                
                # Get SSH public keys
                try:
                    ssh_response = client_iam.list_ssh_public_keys(UserName=username)
                    user_info['ssh_public_keys'] = ssh_response.get('SSHPublicKeys', [])
                except ClientError as e:
                    logging.warning(f"Could not list SSH public keys: {e}")
                
                # Get service specific credentials
                try:
                    ssc_response = client_iam.list_service_specific_credentials(UserName=username)
                    user_info['service_specific_credentials'] = ssc_response.get('ServiceSpecificCredentials', [])
                except ClientError as e:
                    logging.warning(f"Could not list service specific credentials: {e}")
                
                # Check for login profile (console password)
                try:
                    login_response = client_iam.get_login_profile(UserName=username)
                    user_info['login_profile'] = login_response.get('LoginProfile')
                except ClientError as e:
                    if e.response['Error']['Code'] != 'NoSuchEntity':
                        logging.warning(f"Could not get login profile: {e}")
                
                # Get attached policies
                try:
                    policies_response = client_iam.list_attached_user_policies(UserName=username)
                    user_info['attached_policies'] = policies_response.get('AttachedPolicies', [])
                except ClientError as e:
                    logging.warning(f"Could not list attached policies: {e}")
                
                # Get inline policies
                try:
                    inline_response = client_iam.list_user_policies(UserName=username)
                    user_info['inline_policies'] = inline_response.get('PolicyNames', [])
                except ClientError as e:
                    logging.warning(f"Could not list inline policies: {e}")
                
                # Get group memberships
                try:
                    groups_response = client_iam.list_groups_for_user(UserName=username)
                    user_info['groups'] = groups_response.get('Groups', [])
                except ClientError as e:
                    logging.warning(f"Could not list groups: {e}")
                
                # Add this user instance to the list
                found_users.append(user_info)
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    # User doesn't exist in this account, continue searching
                    continue
                else:
                    logging.error(f"Error checking for user in account {cred['AccountId']}: {e}")
                    
        except ClientError as e:
            logging.error(f"Error accessing account {cred['AccountId']}: {e}")
    
    return found_users


def _remove_user_resources(
    credentials: Dict[str, Any],
    username: str,
    user_info: Dict[str, Any],
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Remove all resources associated with an IAM user.
    
    Args:
        credentials: Credential dictionary for the AWS account
        username: IAM username to remove
        user_info: Dictionary containing user resources to remove
        dry_run: If True, only show what would be removed
    
    Returns:
        Dictionary containing removal results and any errors
    """
    import boto3
    
    results = {
        'success': False,
        'removed_resources': [],
        'errors': [],
    }
    
    if dry_run:
        logging.info(f"[DRY RUN] Would remove user '{username}' and all associated resources")
        results['success'] = True
        return results
    
    try:
        # Create IAM client
        session_iam = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name='us-east-1',  # IAM is global
        )
        client_iam = session_iam.client('iam')
        
        # Remove access keys
        for key in user_info['access_keys']:
            try:
                client_iam.delete_access_key(
                    UserName=username,
                    AccessKeyId=key['AccessKeyId']
                )
                results['removed_resources'].append(f"Access Key: {key['AccessKeyId']}")
                logging.info(f"Deleted access key: {key['AccessKeyId']}")
            except ClientError as e:
                error_msg = f"Failed to delete access key {key['AccessKeyId']}: {e}"
                results['errors'].append(error_msg)
                logging.error(error_msg)
        
        # Deactivate and delete MFA devices
        for mfa in user_info['mfa_devices']:
            try:
                client_iam.deactivate_mfa_device(
                    UserName=username,
                    SerialNumber=mfa['SerialNumber']
                )
                client_iam.delete_virtual_mfa_device(
                    SerialNumber=mfa['SerialNumber']
                )
                results['removed_resources'].append(f"MFA Device: {mfa['SerialNumber']}")
                logging.info(f"Deleted MFA device: {mfa['SerialNumber']}")
            except ClientError as e:
                error_msg = f"Failed to delete MFA device {mfa['SerialNumber']}: {e}"
                results['errors'].append(error_msg)
                logging.error(error_msg)
        
        # Delete signing certificates
        for cert in user_info['signing_certificates']:
            try:
                client_iam.delete_signing_certificate(
                    UserName=username,
                    CertificateId=cert['CertificateId']
                )
                results['removed_resources'].append(f"Signing Certificate: {cert['CertificateId']}")
                logging.info(f"Deleted signing certificate: {cert['CertificateId']}")
            except ClientError as e:
                error_msg = f"Failed to delete signing certificate {cert['CertificateId']}: {e}"
                results['errors'].append(error_msg)
                logging.error(error_msg)
        
        # Delete SSH public keys
        for ssh_key in user_info['ssh_public_keys']:
            try:
                client_iam.delete_ssh_public_key(
                    UserName=username,
                    SSHPublicKeyId=ssh_key['SSHPublicKeyId']
                )
                results['removed_resources'].append(f"SSH Public Key: {ssh_key['SSHPublicKeyId']}")
                logging.info(f"Deleted SSH public key: {ssh_key['SSHPublicKeyId']}")
            except ClientError as e:
                error_msg = f"Failed to delete SSH public key {ssh_key['SSHPublicKeyId']}: {e}"
                results['errors'].append(error_msg)
                logging.error(error_msg)
        
        # Delete service specific credentials
        for ssc in user_info['service_specific_credentials']:
            try:
                client_iam.delete_service_specific_credential(
                    UserName=username,
                    ServiceSpecificCredentialId=ssc['ServiceSpecificCredentialId']
                )
                results['removed_resources'].append(f"Service Specific Credential: {ssc['ServiceSpecificCredentialId']}")
                logging.info(f"Deleted service specific credential: {ssc['ServiceSpecificCredentialId']}")
            except ClientError as e:
                error_msg = f"Failed to delete service specific credential {ssc['ServiceSpecificCredentialId']}: {e}"
                results['errors'].append(error_msg)
                logging.error(error_msg)
        
        # Delete login profile (console password)
        if user_info['login_profile']:
            try:
                client_iam.delete_login_profile(UserName=username)
                results['removed_resources'].append("Console Password")
                logging.info("Deleted login profile (console password)")
            except ClientError as e:
                error_msg = f"Failed to delete login profile: {e}"
                results['errors'].append(error_msg)
                logging.error(error_msg)
        
        # Detach managed policies
        for policy in user_info['attached_policies']:
            try:
                client_iam.detach_user_policy(
                    UserName=username,
                    PolicyArn=policy['PolicyArn']
                )
                results['removed_resources'].append(f"Detached Policy: {policy['PolicyName']}")
                logging.info(f"Detached policy: {policy['PolicyName']}")
            except ClientError as e:
                error_msg = f"Failed to detach policy {policy['PolicyName']}: {e}"
                results['errors'].append(error_msg)
                logging.error(error_msg)
        
        # Delete inline policies
        for policy_name in user_info['inline_policies']:
            try:
                client_iam.delete_user_policy(
                    UserName=username,
                    PolicyName=policy_name
                )
                results['removed_resources'].append(f"Inline Policy: {policy_name}")
                logging.info(f"Deleted inline policy: {policy_name}")
            except ClientError as e:
                error_msg = f"Failed to delete inline policy {policy_name}: {e}"
                results['errors'].append(error_msg)
                logging.error(error_msg)
        
        # Remove from groups
        for group in user_info['groups']:
            try:
                client_iam.remove_user_from_group(
                    UserName=username,
                    GroupName=group['GroupName']
                )
                results['removed_resources'].append(f"Removed from Group: {group['GroupName']}")
                logging.info(f"Removed from group: {group['GroupName']}")
            except ClientError as e:
                error_msg = f"Failed to remove from group {group['GroupName']}: {e}"
                results['errors'].append(error_msg)
                logging.error(error_msg)
        
        # Finally, delete the user
        try:
            client_iam.delete_user(UserName=username)
            results['removed_resources'].append(f"IAM User: {username}")
            results['success'] = True
            logging.info(f"Deleted IAM user: {username}")
        except ClientError as e:
            error_msg = f"Failed to delete user {username}: {e}"
            results['errors'].append(error_msg)
            results['success'] = False
            logging.error(error_msg)
    
    except Exception as e:
        error_msg = f"Unexpected error during removal: {e}"
        results['errors'].append(error_msg)
        results['success'] = False
        logging.error(error_msg)
    
    return results


def run(args):
    """
    Main execution function for remove-iam-user operation.
    
    Args:
        args: Parsed command line arguments
    """
    timing = getattr(args, '_timing_context', None)

    pProfiles = args.Profiles
    pRegionList = args.Regions
    pAccounts = args.Accounts
    pSkipAccounts = args.SkipAccounts
    pSkipProfiles = args.SkipProfiles
    pRootOnly = args.RootOnly
    pTiming = args.Time
    pAccessRoles = args.AccessRoles
    pUsername = getattr(args, 'pUsername', None)
    pForce = getattr(args, 'pForce', False)
    pDryRun = getattr(args, 'pDryRun', False)

    # Validate required arguments
    if not pUsername:
        print("Error: +username is required for remove-iam-user operation")
        print("Usage: inv_scr remove-iam-user +username <USERNAME>")
        return

    print("Remove IAM User Operation")
    print(f"Operation version: {__version__}")
    print(f"Target username: {pUsername}")
    if pDryRun:
        print("Mode: DRY RUN (no changes will be made)")
    print()

    if timing:
        timing.milestone("args_parsed", "Arguments parsed and validated")

    # Get credentials (IAM is global, so we only need one region per account)
    CredentialList = get_all_credentials(
        pProfiles,
        pTiming,
        pSkipProfiles,
        pSkipAccounts,
        pRootOnly,
        pAccounts,
        ['us-east-1'],  # IAM is global, only need one region
        pAccessRoles,
    )

    AccountNum = len(set(acct['AccountId'] for acct in CredentialList))
    print(f"Searching for user '{pUsername}' across {AccountNum} account(s)...")

    if timing:
        timing.milestone(
            "credentials_setup",
            f"Credential setup for {AccountNum} accounts",
        )

    # Find the user and their resources across all accounts
    found_users = _find_user_resources(CredentialList, pUsername)

    if timing:
        timing.milestone("user_search", "User search completed")

    if not found_users:
        print(f"\nUser '{pUsername}' not found in any accessible accounts")
        return

    # Display all found instances of the user
    print(f"\nFound user '{pUsername}' in {len(found_users)} account(s):")
    print("=" * 80)
    
    for idx, user_info in enumerate(found_users, 1):
        print(f"\n{idx}. Account: {user_info['account_id']} (Mgmt Account: {user_info['mgmt_account']})")
        print(f"   User ID: {user_info['user_details'].get('UserId', 'N/A')}")
        print(f"   Created: {user_info['user_details'].get('CreateDate', 'N/A')}")
        
        # Count resources
        resource_count = 0
        resource_details = []
        
        if user_info['access_keys']:
            count = len(user_info['access_keys'])
            resource_count += count
            resource_details.append(f"Access Keys: {count}")
        
        if user_info['mfa_devices']:
            count = len(user_info['mfa_devices'])
            resource_count += count
            resource_details.append(f"MFA Devices: {count}")
        
        if user_info['signing_certificates']:
            count = len(user_info['signing_certificates'])
            resource_count += count
            resource_details.append(f"Signing Certificates: {count}")
        
        if user_info['ssh_public_keys']:
            count = len(user_info['ssh_public_keys'])
            resource_count += count
            resource_details.append(f"SSH Keys: {count}")
        
        if user_info['service_specific_credentials']:
            count = len(user_info['service_specific_credentials'])
            resource_count += count
            resource_details.append(f"Service Credentials: {count}")
        
        if user_info['login_profile']:
            resource_count += 1
            resource_details.append("Console Password: Yes")
        
        if user_info['attached_policies']:
            count = len(user_info['attached_policies'])
            resource_count += count
            resource_details.append(f"Attached Policies: {count}")
        
        if user_info['inline_policies']:
            count = len(user_info['inline_policies'])
            resource_count += count
            resource_details.append(f"Inline Policies: {count}")
        
        if user_info['groups']:
            count = len(user_info['groups'])
            resource_count += count
            resource_details.append(f"Group Memberships: {count}")
        
        print(f"   Total Resources: {resource_count}")
        if resource_details:
            print(f"   Resources: {', '.join(resource_details)}")

    print("\n" + "=" * 80)
    print(f"\nTotal: {len(found_users)} user instance(s) found across {AccountNum} accounts")
    
    # In dry-run mode, just show what would be done
    if pDryRun:
        print("\n[DRY RUN] No changes will be made")
        return

    # Confirm removal unless force flag is set
    if not pForce:
        print(f"\nThis will remove user '{pUsername}' from ALL {len(found_users)} account(s) listed above.")
        response = input(f"Are you sure you want to proceed? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print(f"{Fore.RED}Operation cancelled{Fore.RESET}")
            return

    if timing:
        timing.milestone("confirmation", "User confirmation received")

    # Remove the user from each account
    print(f"\nRemoving user '{pUsername}' from {len(found_users)} account(s)...")
    
    all_results = []
    for idx, user_info in enumerate(found_users, 1):
        print(f"\n[{idx}/{len(found_users)}] Processing account {user_info['account_id']}...")
        
        removal_results = _remove_user_resources(
            user_info['credentials'],
            pUsername,
            user_info,
            pDryRun
        )
        
        removal_results['account_id'] = user_info['account_id']
        all_results.append(removal_results)
    
    if timing:
        timing.milestone("removal_complete", "User removal completed")

    # Display consolidated results
    print("\n" + "=" * 80)
    print("REMOVAL SUMMARY")
    print("=" * 80)
    
    total_removed = 0
    total_errors = 0
    successful_accounts = []
    failed_accounts = []
    
    for result in all_results:
        account_id = result['account_id']
        
        if result['success']:
            successful_accounts.append(account_id)
            total_removed += len(result['removed_resources'])
        else:
            failed_accounts.append(account_id)
        
        total_errors += len(result['errors'])
        
        print(f"\nAccount {account_id}:")
        if result['removed_resources']:
            print(f"  ✓ Removed {len(result['removed_resources'])} resource(s)")
            for resource in result['removed_resources']:
                print(f"    - {resource}")
        
        if result['errors']:
            print(f"  ✗ {len(result['errors'])} error(s)")
            for error in result['errors']:
                print(f"    - {error}")
    
    print("\n" + "=" * 80)
    print(f"Successfully removed from {len(successful_accounts)} account(s): {', '.join(successful_accounts)}")
    
    if failed_accounts:
        print(f"Failed to remove from {len(failed_accounts)} account(s): {', '.join(failed_accounts)}")
    
    print(f"Total resources removed: {total_removed}")
    if total_errors > 0:
        print(f"Total errors encountered: {total_errors}")
    
    print(f"\nIAM User Removal operation completed")
