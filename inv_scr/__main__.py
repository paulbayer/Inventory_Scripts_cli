from inv_scr.functions.all_my_instances import all_my_instances
from inv_scr.core import ArgumentsClass
import logging

parser = ArgumentsClass.CommonArguments()
parser.my_parser.add_argument(
		"operation",
		help="The operation you were hoping to run.")
parser.version()
parser.verbosity()
parser.multiregion()
parser.multiprofile()
args = parser.my_parser.parse_args()

operation = args.operation

def main(arguments):
	if operation in ['instances', 'instance', ]:
		all_my_instances(, kwargs['Regions'], kwargs['verbose'])
	else:
		print("Goodbye")
	# if True:  # Logic for functions
	#     test_print("foo")


if __name__ == '__main__':
	Profiles = args.Profiles
	Regions = args.Regions
	verbose = args.loglevel
	logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")
	main(args)
