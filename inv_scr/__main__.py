import sys

from inv_scr.functions.all_my_specific_functions import check_accounts_for_instances, all_my_functions
from inv_scr.core.ArgumentsClass import CommonArguments
from inv_scr.core.account_class import aws_acct_access
from inv_scr.core import Inventory_Modules
from colorama import Fore, init
import logging

init()

parser = CommonArguments()
parser.my_parser.add_argument(
		"operation",
		help="The operation you were hoping to run.")
parser.version()
parser.verbosity()
parser.multiregion()
parser.multiprofile()
parser.multifragment()
parser.orgwide()
args = parser.my_parser.parse_args()

Profiles = args.Profiles
Regions = args.Regions
Fragments = args.Fragments
Orgwide = args.org_wide
verbose = args.loglevel
logging.basicConfig(level=verbose, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)20s() ] %(message)s")

operation = args.operation

ERASE_LINE = '\x1b[2K'

logging.info(f"Provided profiles: {Profiles}")
# logging.info(f"Found profile list: {ProfileList}")


def make_account_object_list():
	# This identifies the profiles that match a specific regex
	ProfileList = Inventory_Modules.get_profiles(['default'], Profiles)
	fAccountObjectList = list()
	NumProfilesDone = 0
	for profile in ProfileList:
		NumProfilesDone += 1
		print(f"{ERASE_LINE}Checking profile {Fore.RED}{profile}{Fore.RESET} [{NumProfilesDone} of {len(ProfileList)}]", end='\r')
		faws_acct = aws_acct_access(profile)
		fAccountObjectList.append(faws_acct)
		if Orgwide:
			if faws_acct.AccountType == 'Root':
				for child_account in faws_acct.ChildAccounts:
					child_account_credentials = Inventory_Modules.get_child_access3(faws_acct,
					                                                                child_account['AccountId'])
					aws_acct_child_access = aws_acct_access(ocredentials=child_account_credentials)
					fAccountObjectList.append(aws_acct_child_access)
	return (fAccountObjectList)


# ProfileList = make_profile_list()
account_object_list = make_account_object_list()

if len(account_object_list) == 1:
	aws_acct = aws_acct_access(ProfileList[0])
else:
	aws_acct = aws_acct_access()
RegionList = Inventory_Modules.get_ec2_regions3(aws_acct, Regions)


def main():
	logging.info(f"The operation to run is {operation}")
	if operation in ['instances', 'instance', ]:
		fmt = '%-12s %-12s %-10s %-15s %-20s %-20s %-42s %-12s'
		print(fmt % (
		"Root Acct #", "Account #", "Region", "InstanceType", "Name", "Instance ID", "Public DNS Name", "State"))
		print(fmt % (
		"-----------", "---------", "------", "------------", "----", "-----------", "---------------", "-----"))
		for account_object in account_object_list:
			instances = check_accounts_for_instances(account_object, RegionList)
			for i in instances:
				if State == 'running':
					fmt = f"%-12s %-12s %-10s %-15s %-20s %-20s %-42s {Fore.RED}%-12s{Fore.RESET}"
				else:
					fmt = f"%-12s %-12s %-10s %-15s %-20s %-20s %-42s %-12s"
				print(fmt % (
					i['MgmtAccountId'], i['AccountId'], i['Region'], i['InstanceType'], i['Name'], i['InstanceId'],
					i['PublicDNSName'], i['State']))
	if operation in ['function', 'functions', 'lambda', ]:
		all_my_functions(account_object, RegionList, Fragments)
	if operation in ['all', 'inventory', ]:
		all_data = list()
		for account_object in account_object_list:
			instance_data = check_accounts_for_instances(account_object, RegionList)
			all_data.extend(instance_data)
			print()
	else:
		print("Goodbye")


# if True:  # Logic for functions
#     test_print("foo")


# sys.exit("Fini")

if __name__ == '__main__':
	main()
print()
print("Thank you for using the script")
print()
