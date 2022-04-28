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
		# if 'Reservations' in Instances.keys():
		for y in Instances:
			for z in y['Instances']:
				InstanceType = z['InstanceType']
				InstanceId = z['InstanceId']
				PublicDnsName = z['PublicDnsName']
				State = z['State']['Name']
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
					'InstanceType': InstanceType,
					'InstanceId': InstanceId,
					'PublicDNSName': PublicDnsName,
					'State': State,
					'Name': Name,
					}
		AllInstances.append(instance_row)
	return (AllInstances)


def all_my_functions(faws_acct, fRegions, fFragments):

	def left(s, amount):
		return s[:amount]

	def right(s, amount):
		return s[-amount:]

	def mid(s, offset, amount):
		return s[offset - 1:offset + amount - 1]

	##########################
	ERASE_LINE = '\x1b[2K'
	NumFunctionsFound = 0
	print()
	print(f"Looking through {len(fRegions)} regions and {len(fProfiles)} profiles")
	print()
	fmt = '%-20s %-10s %-40s %-12s %-35s'
	print(fmt % ("Profile", "Region", "Function Name", "Runtime", "Role"))
	print(fmt % ("-------", "------", "-------------", "-------", "----"))

	for region in fRegions:
		try:
			Functions = Inventory_Modules.find_lambda_functions3(faws_acct, region, fFragments)
			# FunctionNum = len(Functions['Functions'])
			print(f"{ERASE_LINE}Account: {Fore.RED}{faws_acct.account_num}{Fore.RESET} Region: {Fore.RED}{region}{Fore.RESET} Found {Fore.RED}{len(Functions)}{Fore.RESET} functions", end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{ERASE_LINE + profile}: Authorization Failure")
		if len(Functions) > 0:
			for function in Functions:
				# print("Y:",y,"Number:",len(Functions['Functions']))
				# print("Function Name:",Functions['Functions'][y]['FunctionName'])
				FunctionName = function['FunctionName']
				Runtime = function['Runtime'] if 'Runtime' in function.keys() else None
				Rolet = function['Role']
				Role = mid(Rolet, Rolet.find("/") + 2, len(Rolet))
				print(fmt % (profile, region, FunctionName, Runtime, Role))
				NumFunctionsFound += 1
	print(ERASE_LINE)
	print(f"Found {NumFunctionsFound} functions across {len(fProfiles)} profiles across {len(fRegions)} regions")
	print()
	print("Thank you for using this script")
	print()
