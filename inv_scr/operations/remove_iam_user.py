#!/usr/bin/env python3
"""
Remove IAM user operation
Removes IAM users from AWS accounts with proper cleanup of associated resources

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

from tqdm.auto import tqdm
from botocore.exceptions import ClientError

from inv_scr.core import Inventory_Modules
from inv_scr.core.Inventory_Modules import (
    get_all_credentials,
    display_results,
)

__version__ = "2026.01.28"


def add_operation_args(parser):
    """
    Add operation-specific arguments for remove-iam-user operation.
    
    Args:
        parser: CommonArguments parser instance to add arguments to
    """
    local = parser.my_parser.add_argument_group('remove-iam-user', 'Remove IAM user options')
    local.add_argument(
        "+username",
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
) -> Dict[str, Any]:
    """
    Find all resources associated with an IAM user.
    
    Args:
        credentials: List of credential dictionaries for AWS accounts
        username: IAM username to search for
    
    Returns:
        Dictionary containing user information and associated resources
    """
    import boto3
    
    user_info = {
        'found': False,
        'account_id': None,
        'credentials': None,
        'user_details': None,
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
                user_info['found'] = True
                user_info['account_id'] = cred['AccountId']
                user_info['credentials'] = cred
                user_info['user_details'] = user_response['User']
                
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
                
                # User found, stop searching
                break
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    # User doesn't exist in this account, continue searching
                    continue
                else:
                    logging.error(f"Error checking for user in account {cred['AccountId']}: {e}")
                    
        except ClientError as e:
            logging.error(f"Error accessing account {cred['AccountId']}: {e}")
    
    return user_info


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

    # Find the user and their resources
    user_info = _find_user_resources(CredentialList, pUsername)

    if timing:
        timing.milestone("user_search", "User search completed")

    if not user_info['found']:
        print(f"\nUser '{pUsername}' not found in any accessible accounts")
        return

    # Display what will be removed
    print(f"\nFound user '{pUsername}' in account {user_info['account_id']}")
    print("\nResources to be removed:")
    print(f"  - User: {pUsername}")
    
    if user_info['access_keys']:
        print(f"  - Access Keys: {len(user_info['access_keys'])}")
    if user_info['mfa_devices']:
        print(f"  - MFA Devices: {len(user_info['mfa_devices'])}")
    if user_info['signing_certificates']:
        print(f"  - Signing Certificates: {len(user_info['signing_certificates'])}")
    if user_info['ssh_public_keys']:
        print(f"  - SSH Public Keys: {len(user_info['ssh_public_keys'])}")
    if user_info['service_specific_credentials']:
        print(f"  - Service Specific Credentials: {len(user_info['service_specific_credentials'])}")
    if user_info['login_profile']:
        print(f"  - Console Password: Yes")
    if user_info['attached_policies']:
        print(f"  - Attached Policies: {len(user_info['attached_policies'])}")
    if user_info['inline_policies']:
        print(f"  - Inline Policies: {len(user_info['inline_policies'])}")
    if user_info['groups']:
        print(f"  - Group Memberships: {len(user_info['groups'])}")

    # Confirm removal unless force flag is set
    if not pForce and not pDryRun:
        response = input(f"\nAre you sure you want to remove user '{pUsername}' and all associated resources? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Operation cancelled")
            return

    if timing:
        timing.milestone("confirmation", "User confirmation received")

    # Perform the removal
    removal_results = _remove_user_resources(
        user_info['credentials'],
        pUsername,
        user_info,
        pDryRun
    )
    
    if timing:
        timing.milestone("removal_complete", "User removal completed")

    # Display results
    print(f"\n{'[DRY RUN] ' if pDryRun else ''}Removal Results:")
    print("=" * 50)
    
    if removal_results['removed_resources']:
        print(f"\nSuccessfully removed {len(removal_results['removed_resources'])} resource(s):")
        for resource in removal_results['removed_resources']:
            print(f"  ✓ {resource}")
    
    if removal_results['errors']:
        print(f"\nEncountered {len(removal_results['errors'])} error(s):")
        for error in removal_results['errors']:
            print(f"  ✗ {error}")
    
    if removal_results['success']:
        print(f"\n{'[DRY RUN] ' if pDryRun else ''}Successfully removed user '{pUsername}'")
    else:
        print(f"\n{'[DRY RUN] ' if pDryRun else ''}Failed to completely remove user '{pUsername}'")
        print("Some resources may still exist. Check errors above.")
    
    print(f"\n{'[DRY RUN] ' if pDryRun else ''}Operation completed")
