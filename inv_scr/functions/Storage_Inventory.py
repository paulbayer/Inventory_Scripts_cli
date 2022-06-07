import os
import sys
import boto3
from inv_scr.core import Inventory_Modules
from inv_scr.core.exceptions import InventoryScriptsExceptions
from botocore.exceptions import ClientError
from colorama import init, Fore

import logging

init()
ERASE_LINE = '\x1b[2K'


def check_accounts_for_buckets(faws_acct, fRegionList=None):
	AllBuckets = []
	if fRegionList is None:
		fRegionList = ['us-east-1']
	elif len(fRegionList) > 1:
		# The list_buckets call is a global call. No need to check more than one region
		fRegionList = [fRegionList[0]]
	Buckets = dict()
	for region in fRegionList:
		try:
			print(f"{ERASE_LINE}Checking account {Fore.RED}{faws_acct.acct_number}{Fore.RESET} in region {Fore.RED}{region}{Fore.RESET}", end='\r')
			Buckets = Inventory_Modules.find_account_bucket3(faws_acct, region)
			logging.info(
					f"Root Account: {faws_acct.MgmtAccount} Account: {faws_acct.acct_number} Region: {region} | Found {len(Buckets)} buckets")
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {faws_acct.acct_number} in {region} region")
				logging.warning(f"It's possible that the region {region} hasn't been opted-into")
				pass
		for y in Buckets:
			OwnerAccountEmail = y['Owner'].get('DisplayName', None)
			OwnerId = y['Owner']['ID']
			for z in y['Buckets']:
				bucket_row = {
					'MgmtAccountId': faws_acct.MgmtAccount,
					'AccountId': faws_acct.acct_number,
					'Region': region,
					'Name': z['Name'],
					'CreationDate' : z['CreationDate'],
					'OwnerAccountEmail': OwnerAccountEmail,
					'OwnerId': OwnerId,
					}
				AllBuckets.append(bucket_row)
	return (AllBuckets)


def check_accounts_for_rds_databases(faws_acct, fRegionList=None):
	AllDatabases = []
	if fRegionList is None:
		fRegionList = ['us-east-1']
	Databases = dict()
	for region in fRegionList:
		try:
			print(f"{ERASE_LINE}Checking account {Fore.RED}{faws_acct.acct_number}{Fore.RESET} in region {Fore.RED}{region}{Fore.RESET}", end='\r')
			Databases = Inventory_Modules.find_account_databases3(faws_acct, region)
			logging.info(
					f"Root Account: {faws_acct.MgmtAccount} Account: {faws_acct.acct_number} Region: {region} | Found {len(Databases)} databases")
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {faws_acct.acct_number} in {region} region")
				logging.warning(f"It's possible that the region {region} hasn't been opted-into")
				pass
		for y in Databases:
			for z in y['DBInstances']:
				database_row = {
					'AccountId': faws_acct.acct_number,
					'MgmtAccountId': faws_acct.MgmtAccount,
					'Region': region,
					'Name': z['DBName'],

					'InstanceID' : z['DBInstanceIdentifier'],
					'InstanceARN' : z['DBInstanceArn'],
					'DBEngine' : z['Engine'],
					'DBEngineVersion' : z['EngineVersion'],
					'ADDomain' : z['DomainMemberships']['Domain'],
					'Status' : z['DBInstanceStatus'],
					'AvailabilityZone' : z['AvailabilityZone'],
					'SecondaryAZ' : z['SecondaryAvailabilityZone'],
					'DBSecGrpName' : z['DBSecurityGroups']['DBSecurityGroupName'],
					
					'VPCSecGrp' : z.get('PublicDnsName', None),
					'DBSubnetGrpName' : z['State']['Name'],
					'DBSubnetGrpVPCID' : z['SubnetId'],
					'StorageEncryption' : z['VpcId'],
					'KMSKeyID' : z['VirtualizationType'],
					'Tags' : z.get('Tags', None),
					'TDEEncryptionARN' : z['SecurityGroups'],
					}
				AllDatabases.append(database_row)
	return (AllDatabases)
