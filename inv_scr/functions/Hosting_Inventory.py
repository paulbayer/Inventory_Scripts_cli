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


def check_accounts_for_instances(faws_acct, fRegionList=None):
	AllInstances = []
	instance_row = {}
	if fRegionList is None:
		fRegionList = ['us-east-1']
	Instances = dict()
	for region in fRegionList:
		try:
			print(f"{ERASE_LINE}Checking account {Fore.RED}{faws_acct.acct_number}{Fore.RESET} in region {Fore.RED}{region}{Fore.RESET}", end='\r')
			Instances = Inventory_Modules.find_account_instances3(faws_acct, region)
			logging.info(
					f"Root Account: {faws_acct.MgmtAccount} Account: {faws_acct.acct_number} Region: {region} | Found {len(Instances)} instances")
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {faws_acct.acct_number} in {region} region")
				logging.warning(f"It's possible that the region {region} hasn't been opted-into")
				pass
		for y in Instances:
			for z in y['Instances']:
				Name = "No Name Tag"
				try:
					for x in range(len(z['Tags'])):
						if z['Tags'][x]['Key'] == "Name":
							Name = z['Tags'][x]['Value']
				except KeyError as my_Error:  # This is needed for when there is no "Tags" key within the describe-instances output
					logging.info(my_Error)
					pass
				# if State == 'running':
				# 	fmt = f"%-12s %-12s %-10s %-15s %-20s %-20s %-42s {Fore.RED}%-12s{Fore.RESET}"
				# else:
				# 	fmt = '%-12s %-12s %-10s %-15s %-20s %-20s %-42s %-12s'
				# print(fmt % (
				# 	faws_acct.acct_number, account['AccountId'], region, InstanceType, Name, InstanceId,
				# 	PublicDnsName, State))
				instance_row = {
					'AccountId': faws_acct.acct_number,
					'MgmtAccountId': faws_acct.MgmtAccount,
					'Region': region,
					'Name': Name,
					'AMIId' : z['ImageId'],
					'AvailabilityZone' : z['Placement']['AvailabilityZone'],
					'Hypervisor' : z['Hypervisor'],
					'InstanceId' : z['InstanceId'],
					'InstanceType' : z['InstanceType'],
					'Launch_DateTime' : z['LaunchTime'],
					'PlatformOS' : z['PlatformDetails'],
					'PrivateIPAddress' : z['PrivateIpAddress'],
					'PublicIPAddress' : z.get('PublicIpAddress', None),
					'PublicDnsName' : z.get('PublicDnsName', None),
					'State' : z['State']['Name'],
					'SubnetId' : z['SubnetId'],
					'VPCId' : z['VpcId'],
					'VirtualizationType' : z['VirtualizationType'],
					'Tags' : z.get('Tags', None),
					'SecurityGroups' : z['SecurityGroups'],
					'NetIfaces' : z['NetworkInterfaces'],
					}
				AllInstances.append(instance_row)
	return (AllInstances)
