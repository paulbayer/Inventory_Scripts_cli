import os
import sys
import boto3
from inv_scr.core import Inventory_Modules
from inv_scr.core.ArgumentsClass import CommonArguments
from inv_scr.core.account_class import aws_acct_access
from inv_scr.core.exceptions import InventoryScriptsExceptions
from botocore.exceptions import ClientError
from colorama import init, Fore

import logging

init()
ERASE_LINE = '\x1b[2K'


def check_accounts_for_vpcs(faws_acct, fRegionList=None):
	all_vpcs = []
	if fRegionList is None:
		fRegionList = ['us-east-1']
	VPCs = dict()
	for region in fRegionList:
		try:
			print(f"{ERASE_LINE}Checking account {Fore.RED}{faws_acct.acct_number}{Fore.RESET} in region {Fore.RED}{region}{Fore.RESET} for VPCs", end='\r')
			VPCs = Inventory_Modules.find_account_vpcs3(faws_acct, region)
			logging.info(
					f"Root Account: {faws_acct.MgmtAccount} Account: {faws_acct.acct_number} Region: {region} | Found {len(VPCs)} vpcs")
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {faws_acct.acct_number} in {region} region")
				logging.warning(f"It's possible that the region {region} hasn't been opted-into")
				pass
		for y in VPCs:
			vpc_tags = y['Tags']
			# TODO: This should be a loop collecting the CidrBlockAssociationSet,
			#  but it's rare that there's more than one, so we'll use this for now.
			CidrBlock = y['CidrBlock']
			OwnerId = y['OwnerId']
			VpcId = y['VpcId']
			Default = y['IsDefault']
			Name = "No Name Tag"
			try:
				for x in vpc_tags:
					if x['Key'] == "Name":
						Name = x['Value']
			except KeyError as my_Error:  # This is needed for when there is no "Tags" key within the describe-instances output
				logging.info(my_Error)
				pass
			vpc_row = {
				'AccountId': faws_acct.acct_number,
				'MgmtAccountId': faws_acct.MgmtAccount,
				'Region': region,
				'CidrBlock': CidrBlock,
				'OwnerId': OwnerId,
				'VpcId': VpcId,
				'Name': Name,
				'Default': Default,
				'Tags': vpc_tags,
				}
			all_vpcs.append(vpc_row)
	return (all_vpcs)


def check_accounts_for_subnets(faws_acct, fRegionList=None):
	all_subnets = []
	if fRegionList is None:
		fRegionList = ['us-east-1']
	for region in fRegionList:
		try:
			print(f"{ERASE_LINE}Checking account {Fore.RED}{faws_acct.acct_number}{Fore.RESET} in region {Fore.RED}{region}{Fore.RESET} for Subnets", end='\r')
			Subnets = Inventory_Modules.find_account_subnets3(faws_acct, region)
			logging.info(
					f"Root Account: {faws_acct.MgmtAccount} Account: {faws_acct.acct_number} Region: {region} | Found {len(Subnets)} subnets")
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {faws_acct.acct_number} in {region} region")
				logging.warning(f"It's possible that the region {region} hasn't been opted-into")
				pass
		for y in Subnets:
			if 'Ipv6CidrBlock' in y['Ipv6CidrBlockAssociationSet']:
				Ipv6CidrBlock = y['Ipv6CidrBlockAssociationSet']['Ipv6CidrBlock']
			else:
				Ipv6CidrBlock = None
			Name = "No Name Tag"
			try:
				for x in y['Tags']:
					if x['Key'] == "Name":
						Name = x['Value']
			except KeyError as my_Error:  # This is needed for when there is no "Tags" key within the describe-instances output
				logging.info(my_Error)
				pass
			subnet_row = {
				'AccountId': faws_acct.acct_number,
				'MgmtAccountId': faws_acct.MgmtAccount,
				'Region': region,
				'CidrBlock' : y['CidrBlock'],
				'Ipv6CidrBlock' : Ipv6CidrBlock,
				'OwnerId' : y['OwnerId'],
				'SubnetId' : y['SubnetId'],
				'Tags' : y['Tags'],
				'VpcId' : y['VpcId'],
				'AvailabilityZone' : y['AvailabilityZone'],
				'AvailabilityZoneId' : y['AvailabilityZoneId'],
				'Name': Name,
				}
			all_subnets.append(subnet_row)
	return (all_subnets)


def check_accounts_for_eips(faws_acct, fRegionList=None):
	all_eips = []
	EIPs = dict()
	if fRegionList is None:
		fRegionList = ['us-east-1']
	for region in fRegionList:
		try:
			print(f"{ERASE_LINE}Checking account {Fore.RED}{faws_acct.acct_number}{Fore.RESET} in region {Fore.RED}{region}{Fore.RESET} for EIPs", end='\r')
			EIPs = Inventory_Modules.find_account_eips3(faws_acct, region)
			logging.info(
					f"Root Account: {faws_acct.MgmtAccount} Account: {faws_acct.acct_number} Region: {region} | Found {len(EIPs)} eips")
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {faws_acct.acct_number} in {region} region")
				logging.warning(f"It's possible that the region {region} hasn't been opted-into")
				pass
		for y in EIPs:
			if 'InstanceId' in y:
				InstanceId = y['InstanceId']
			else:
				InstanceId = None
			Name = "No Name Tag"
			try:
				for x in y['Tags']:
					if x['Key'] == "Name":
						Name = x['Value']
			except KeyError as my_Error:  # This is needed for when there is no "Tags" key within the describe-instances output
				logging.info(my_Error)
				pass
			eip_row = {
				'MgmtAccountId': faws_acct.MgmtAccount,
				'AccountId': faws_acct.acct_number,
				'Region': region,
				'EIPId' : EIPs['AllocationId'],
				'InstanceId': InstanceId,
				'PublicIP' : EIPs['PublicIp'],
				'NetworkInterfaceId' : EIPs['NetworkInterfaceId'],
				'EIPOwner' : EIPs['NetworkInterfaceOwnerId'],
				'PrivateIP' : EIPs['PrivateIpAddress'],
				'Location' : EIPs['NetworkBorderGroup'],
				'Tags' : EIPs['Tags'],
				}
			all_eips.append(eip_row)
	return (all_eips)
