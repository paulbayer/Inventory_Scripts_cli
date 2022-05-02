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
