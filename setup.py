from setuptools import setup

setup(
	name='inv_scr',  # Update Name
	packages=['inv_scr'],  # Name of CLI
	version='0.1.0',  # Version
	description='A cli for Inventory Scripts',  # Description
	author='Paul Bayer',  # Author
	url='https://gitlab.aws.dev/paulbaye/inventory_scripts_cli',  # To be updated
	author_email='paulbaye@amazon.com',  # Email
	download_url='https://gitlab.aws.dev/paulbaye/inventory_scripts_cli',  # To be updated
	keywords=['aws', 'python', 'inventory', 'readiness', 'cloud', 'maturity'],  # Key words for cli
	classifiers=[],
	install_requires=[
		"boto3",  # Add all packages
		"colorama",
		"botocore",
		"logging"
		],
	setup_requires=[],
	tests_require=[],
	entry_points={
		'console_scripts': [
			'inv_scr = inv_scr.__main__:main',
			],
		},
	)
