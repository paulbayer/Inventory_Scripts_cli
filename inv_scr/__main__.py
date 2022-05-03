import sys
from datetime import datetime

from inv_scr.functions.all_my_specific_functions import all_my_functions
from inv_scr.functions.Network_Inventory import check_accounts_for_vpcs, check_accounts_for_subnets, \
	check_accounts_for_eips
from inv_scr.functions.Hosting_Inventory import check_accounts_for_instances
from inv_scr.core.ArgumentsClass import CommonArguments
from inv_scr.core.account_class import aws_acct_access
from inv_scr.core import Inventory_Modules
from colorama import Fore, init
import logging
import xlsxwriter

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
		print(f"{ERASE_LINE}Checking profile {Fore.RED}{profile}{Fore.RESET} [{NumProfilesDone} of {len(ProfileList)}]",
		      end='\r')
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


def write_to_Excel(data_list, inventory_book):
	"""
	Writes the data from the data list, into the worksheet...
	:param data_list: The entire object, containing all of the data
	:param inventory_book: The entire object, containing all the workbooks
	:return:
	"""
	for inventory_type in data_list:
		tag_cell_formatting = inventory_book[inventory_type]['workbook'].add_format()
		tag_cell_formatting.set_text_wrap(True)
		# tag_cell_formatting.set_column()
		for sub_type in data_list[inventory_type]:
			row = 0
			worksheet = inventory_book[inventory_type][sub_type]
			worksheet.freeze_panes(1, 0)  # Freeze the first row.
			for item in data_list[inventory_type][sub_type]:
				row += 1
				column = 0
				tag_string = ''
				logging.info(f"Starting worksheet for {sub_type}")
				for data_field in inventory_book[inventory_type]['worksheets'][sub_type]['data_fields']:
					logging.error(f"{data_field}: {item[data_field]}")
					if isinstance(item[data_field], list):
						if data_field == 'Tags':
							tag_string = '\n'.join(str(f"{i['Key']} = {i['Value']}") for i in item[data_field])
						elif data_field == 'SecurityGroups':
							tag_string = '\n'.join(str(f"{i['GroupName']} = {i['GroupId']}") for i in item[data_field])
						elif data_field == 'NetIfaces':
							# 'ENI ID', 'ENI Subnet ID', 'ENI EIP Address', 'ENI Primary Private IP','ENI IPv6 Address', 'ENI MAC',
							tag_string = '\n'.join(
									str(f"{key} = {value}") for key, value in enumerate(item[data_field]))
						worksheet.set_column(row, column, 30, )
						worksheet.write(row, column, tag_string, tag_cell_formatting)
					elif isinstance(item[data_field], datetime):
						worksheet.write(row, column, f"{item[data_field].replace(tzinfo=None)} UTC")
					else:
						worksheet.write(row, column, item[data_field])
					column += 1
		logging.info(f"Finished with {inventory_type}")
		inventory_book[inventory_type]['workbook'].close()


# TODO: Create a class for the workbook data

# ProfileList = make_profile_list()
account_object_list = make_account_object_list()

if len(account_object_list) == 1:
	aws_acct = aws_acct_access(Profiles[0])
else:
	aws_acct = aws_acct_access()
RegionList = Inventory_Modules.get_ec2_regions3(aws_acct, Regions)

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
elif operation in ['function', 'functions', 'lambda', ]:
	all_my_functions(account_object, RegionList, Fragments)
elif operation in ['all', 'inventory', ]:
	all_data = dict()
	inventory_books = {'network_inventory': {'file_name' : 'Network_Inventory.xlsx',
	                                         'worksheets': {
		                                         'VPCs'   : {
			                                         # SheetName isn't actually needed here, since we use the WorkSheet name anyway
			                                         'SheetName'  : 'VPCs',
			                                         'headings'   : ['Org Account', 'Child Account Number', 'Region',
			                                                         'VPC ID', 'VPC Name', 'Default',
			                                                         'VPC Owner Account', 'IPv4 CIDR Block',
			                                                         'IPv6 CIDR Block', 'Tags'],
			                                         'data_fields': ['MgmtAccountId', 'AccountId', 'Region',
			                                                         'VpcId', 'Name', 'Default', 'OwnerId', 'CidrBlock',
			                                                         'CidrBlock', 'Tags'],
			                                         },
		                                         'Subnets': {
			                                         'SheetName'  : 'Subnets',
			                                         'headings'   : ['Org Account', 'Child Account Number', 'Region',
			                                                         'VPC ID', 'Subnet ID', 'Subnet Name',
			                                                         'Subnet Owner Account',
			                                                         'Availability Zone', 'Availability Zone Id',
			                                                         'IPv4 CIDR Block', 'IPv6 CIDR Block',
			                                                         'Tags'],
			                                         'data_fields': ['MgmtAccountId', 'AccountId', 'Region',
			                                                         'VpcId', 'SubnetId', 'Name', 'OwnerId',
			                                                         'AvailabilityZone', 'AvailabilityZoneId',
			                                                         'CidrBlock', 'Ipv6CidrBlock',
			                                                         'Tags'],
			                                         },
		                                         'EIPs'   : {
			                                         'SheetName'  : 'Subnets',
			                                         'headings'   : ['Org Account', 'Child Account Number', 'Region',
			                                                         'EIP ID', 'Instance ID', 'Public IP',
			                                                         'Network Interface ID', 'EIP Owner',
			                                                         'Private IP',
			                                                         'Network Border Group',
			                                                         'Tags'],
			                                         'data_fields': ['MgmtAccountId', 'AccountId', 'Region',
			                                                         'EIPId', 'InstanceId', 'PublicIP',
			                                                         'NetworkInterfaceId', 'EIPOwner', 'PrivateIP',
			                                                         'Location', 'Tags',
			                                                         ],
			                                         },
		                                         },
	                                         },
	                   'hosting_inventory': {'file_name' : 'Hosting_Inventory.xlsx',
	                                         'worksheets': {
		                                         'Instances': {
			                                         'SheetName'  : 'Instances',
			                                         'headings'   : ['Org Account', 'Child Account Number',
			                                                         'Region',
			                                                         'Name', 'Instance ID', 'Instance Type',
			                                                         'Instance AMI ID',
			                                                         'Private IP Address', 'Public IP Address',
			                                                         'Subnet ID', 'VPC ID', 'Security Group Info',

			                                                         'Availability Zone',
			                                                         'Hypervisor Type', 'Virtualization Type',
			                                                         'Launch DateTime', 'State', 'Network Info',
			                                                         # 'ENI ID', 'ENI Subnet ID', 'ENI EIP Address', 'ENI Primary Private IP','ENI IPv6 Address', 'ENI MAC',
			                                                         'Platform/ OS',
			                                                         'Tags', ],
			                                         'data_fields': ['MgmtAccountId', 'AccountId', 'Region',
			                                                         'Name', 'InstanceId', 'InstanceType',
			                                                         'AMIId', 'PrivateIPAddress', 'PublicIPAddress',
			                                                         'SubnetId', 'VPCId', 'SecurityGroups',
			                                                         'AvailabilityZone', 'Hypervisor',
			                                                         'VirtualizationType',
			                                                         'Launch_DateTime', 'State', 'NetIfaces',
			                                                         'PlatformOS',
			                                                         # 'PublicDNSName',
			                                                         'Tags', ],
			                                         },
		                                         }
	                                         },
	                   }

	# Setup Networking Workbook
	row = 0
	column = 0
	# Setup all the workbooks and worksheets and create all the headers.
	for workbook in inventory_books:
		logging.info(f"Inventory Book: {workbook}")
		inventory_books[workbook]['workbook'] = xlsxwriter.Workbook(inventory_books[workbook]['file_name'])
		header_cell_formatting = inventory_books[workbook]['workbook'].add_format()
		header_cell_formatting.set_bold(True)
		for worksheet in inventory_books[workbook]['worksheets']:
			logging.info(f"Worksheet: {worksheet}")
			inventory_books[workbook][worksheet] = inventory_books[workbook]['workbook'].add_worksheet(worksheet)
			inventory_books[workbook][worksheet].write_row(row, column,
			                                               inventory_books[workbook]['worksheets'][worksheet][
				                                               'headings'],
			                                               header_cell_formatting)

	# Setup the "all_data" dict to capture all the data from the individual sdk calls
	for inventory_type in inventory_books:
		all_data[inventory_type] = dict()
		for worksheet in inventory_books[inventory_type]['worksheets']:
			all_data[inventory_type][worksheet] = list()

	# Go through all accounts, and get the necessary data from every account and insert it into the "all_data" list.
	for account_object in account_object_list:

		# # AWS VPC and Network Inventory
		# VPC Data
		vpc_data = check_accounts_for_vpcs(account_object, RegionList)
		all_data['network_inventory']['VPCs'].extend(vpc_data)
		# Subnets
		subnet_data = check_accounts_for_subnets(account_object, RegionList)
		all_data['network_inventory']['Subnets'].extend(subnet_data)
		# Public IP Addresses(Elastic IPs)
		eip_data = check_accounts_for_eips(account_object, RegionList)
		all_data['network_inventory']['EIPs'].extend(eip_data)

		# # AWS Elastic Load Balancers (ELB) Inventory (NLB, ALB, GWLB)
		# 	ELBs
		# 	ELBs v2
		# # AWS Firewalls Inventory
		# 	Network Firewalls
		# # AWS Gateways Inventory
		# 	API Gateways
		# 	API v2 Gateways
		# 	DirectConnect Gateways
		# 	Transit Gateways
		# 	VPN Gateways
		# 	Internet Gateways
		# 	Customer Gateways
		# 	NAT Gateways
		# # AWS CloudFront Inventory
		# 	AWS CloudFront Distributions
		# # Hosting Inventory
		# 	AWS EC2 Instances
		instance_data = check_accounts_for_instances(account_object, RegionList)
		all_data['hosting_inventory']['Instances'].extend(instance_data)
	# 	AWS AMI Inventory (Active images only)
	# 	S3 Buckets (acting as web server)
	# # Data Repositories Inventory
	# 	S3 Buckets
	# 	RDS Instances
	# 	RDS Snapshots
	# 	RDS Instance Backups
	# 	DynamoDB Tables
	# 	DynamoDB Global Tables
	# 	DynamoDB Backups
	# 	Glacier Vaults
	# 	Amazon SQS
	# 	Amazon SNS
	# 	CloudTrail
	# 	CloudWatch Logs
	# # AWS Containers Inventory
	# 	ECS Clusters
	# 	Maybe ECR Image Repos also?
	# 	EKS Clusters
	# # AWS Lambda Inventory
	# 	Lambda Functions
	# 	Lambda Aliases
	# # AWS KMS Keys Inventory
	# 	KMS Keys
	# 	KMS Key Aliases
	# 	KMS Key Stores
	# # Amazon WorkSpaces Inventory
	# 	WorkSpaces
	# 	WorkSpaces Bundles
	# 	WorkSpaces Images
	# # AWS Organizations (Account) Inventory
	# 	Organizations Accounts
	write_to_Excel(all_data, inventory_books)
	print()
# workbook_network.close()
else:
	print("Goodbye")

print()
print("Thank you for using the script")
print()
