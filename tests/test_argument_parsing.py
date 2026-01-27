#!/usr/bin/env python3
"""
Comprehensive tests for argument parsing functionality
"""

import unittest
import sys
from unittest.mock import patch
import argparse

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, '..')

from inv_scr.core.ArgumentsClass import CommonArguments


class TestArgumentParsing(unittest.TestCase):
    """Test cases for comprehensive argument parsing"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = CommonArguments()

    def test_all_argument_methods_exist(self):
        """Test that all argument methods exist and are callable"""
        methods = [
            'version', 'rootOnly', 'roletouse', 'rolestouse', 'deletion',
            'confirm', 'fix', 'verbosity', 'extendedargs', 'timing',
            'fragment', 'singleprofile', 'multiprofile', 'multiregion',
            'multiregion_nodefault', 'singleregion', 'singleregion_nodefault',
            'save_to_file'
        ]
        
        for method_name in methods:
            self.assertTrue(hasattr(self.parser, method_name))
            self.assertTrue(callable(getattr(self.parser, method_name)))

    def test_complex_argument_combinations(self):
        """Test complex combinations of arguments"""
        # Add all common arguments
        self.parser.multiprofile()
        self.parser.multiregion()
        self.parser.extendedargs()
        self.parser.rolestouse()
        self.parser.rootOnly()
        self.parser.verbosity()
        self.parser.timing()
        self.parser.save_to_file()
        self.parser.fragment()
        
        # Test complex argument combination
        args = self.parser.my_parser.parse_args([
            '--profiles', 'profile1', 'profile2', 'profile3',
            '--regions', 'us-east-1', 'us-west-2', 'eu-west-1',
            '--skip', '123456789012', '987654321098',
            '--account', '111111111111', '222222222222',
            '--access_rolename', 'OrganizationAccountAccessRole', 'AWSControlTowerExecution',
            '--rootonly',
            '--verbose',
            '--timing',
            '--filename', 'output.csv',
            '--fragment', 'test', 'prod'
        ])
        
        self.assertEqual(args.Profiles, ['profile1', 'profile2', 'profile3'])
        self.assertEqual(args.Regions, ['us-east-1', 'us-west-2', 'eu-west-1'])
        self.assertEqual(args.SkipAccounts, ['123456789012', '987654321098'])
        self.assertEqual(args.Accounts, ['111111111111', '222222222222'])
        self.assertEqual(args.AccessRoles, ['OrganizationAccountAccessRole', 'AWSControlTowerExecution'])
        self.assertTrue(args.RootOnly)
        self.assertEqual(args.loglevel, 30)  # WARNING
        self.assertTrue(args.Time)
        self.assertEqual(args.Filename, 'output.csv')
        self.assertEqual(args.Fragments, ['test', 'prod'])

    def test_default_values(self):
        """Test that default values are set correctly"""
        self.parser.multiprofile()
        self.parser.multiregion()
        self.parser.extendedargs()
        self.parser.verbosity()
        self.parser.timing()
        self.parser.rootOnly()
        
        args = self.parser.my_parser.parse_args([])
        
        self.assertIsNone(args.Profiles)
        self.assertEqual(args.Regions, ['us-east-1'])  # Default region
        self.assertIsNone(args.SkipAccounts)
        self.assertIsNone(args.Accounts)
        self.assertFalse(args.RootOnly)
        self.assertEqual(args.loglevel, 50)  # CRITICAL (default)
        self.assertFalse(args.Time)

    def test_single_vs_multi_arguments(self):
        """Test single vs multi argument variations"""
        # Test single profile
        parser1 = CommonArguments()
        parser1.singleprofile()
        args1 = parser1.my_parser.parse_args(['--profile', 'single-profile'])
        self.assertEqual(args1.Profile, 'single-profile')
        
        # Test multi profiles
        parser2 = CommonArguments()
        parser2.multiprofile()
        args2 = parser2.my_parser.parse_args(['--profiles', 'profile1', 'profile2'])
        self.assertEqual(args2.Profiles, ['profile1', 'profile2'])
        
        # Test single region
        parser3 = CommonArguments()
        parser3.singleregion()
        args3 = parser3.my_parser.parse_args(['--region', 'us-west-1'])
        self.assertEqual(args3.Region, 'us-west-1')
        
        # Test multi regions
        parser4 = CommonArguments()
        parser4.multiregion()
        args4 = parser4.my_parser.parse_args(['--regions', 'us-east-1', 'us-west-2'])
        self.assertEqual(args4.Regions, ['us-east-1', 'us-west-2'])

    
    def test_boolean_flags(self):
        """Test boolean flag arguments"""
        self.parser.rootOnly()
        self.parser.timing()
        self.parser.deletion()
        self.parser.confirm()
        self.parser.fix()
        
        # Test all flags enabled
        args = self.parser.my_parser.parse_args([
            '--rootonly', '--timing', '+force', '+confirm', '+fix'
        ])
        
        self.assertTrue(args.RootOnly)
        self.assertTrue(args.Time)
        self.assertTrue(args.Force)
        self.assertTrue(args.Confirm)
        self.assertTrue(args.Fix)

    def test_verbosity_levels(self):
        """Test all verbosity levels"""
        self.parser.verbosity()
        
        # Test each verbosity level
        test_cases = [
            ([], 50),  # Default CRITICAL
            (['-v'], 40),  # ERROR
            (['-vv'], 30),  # WARNING
            (['--verbose'], 30),  # WARNING (same as -vv)
            (['-vvv'], 20),  # INFO
            (['-d'], 10),  # DEBUG
            (['--debug'], 10),  # DEBUG (same as -d)
        ]
        
        for args_list, expected_level in test_cases:
            args = self.parser.my_parser.parse_args(args_list)
            self.assertEqual(args.loglevel, expected_level, 
                           f"Failed for args {args_list}, expected {expected_level}, got {args.loglevel}")

    def test_fragment_arguments(self):
        """Test fragment-related arguments"""
        self.parser.fragment()
        
        # Test default fragments
        args1 = self.parser.my_parser.parse_args([])
        self.assertEqual(args1.Fragments, ['all'])
        self.assertFalse(args1.Exact)
        
        # Test custom fragments
        args2 = self.parser.my_parser.parse_args(['--fragment', 'test1', 'test2', '--exact'])
        self.assertEqual(args2.Fragments, ['test1', 'test2'])
        self.assertTrue(args2.Exact)

    def test_role_arguments(self):
        """Test role-related arguments"""
        # Test single role
        parser1 = CommonArguments()
        parser1.roletouse()
        args1 = parser1.my_parser.parse_args(['--access_rolename', 'SingleRole'])
        self.assertEqual(args1.AccessRole, 'SingleRole')
        
        # Test multiple roles
        parser2 = CommonArguments()
        parser2.rolestouse()
        args2 = parser2.my_parser.parse_args(['--access_rolename', 'Role1', 'Role2', 'Role3'])
        self.assertEqual(args2.AccessRoles, ['Role1', 'Role2', 'Role3'])

    def test_region_variations(self):
        """Test different region argument variations"""
        # Test multiregion with default
        parser1 = CommonArguments()
        parser1.multiregion()
        args1 = parser1.my_parser.parse_args([])
        self.assertEqual(args1.Regions, ['us-east-1'])  # Default
        
        # Test multiregion_nodefault
        parser2 = CommonArguments()
        parser2.multiregion_nodefault()
        args2 = parser2.my_parser.parse_args([])
        self.assertIsNone(args2.Regions)  # No default
        
        # Test singleregion with default
        parser3 = CommonArguments()
        parser3.singleregion()
        args3 = parser3.my_parser.parse_args([])
        self.assertEqual(args3.Region, 'us-east-1')  # Default
        
        # Test singleregion_nodefault
        parser4 = CommonArguments()
        parser4.singleregion_nodefault()
        args4 = parser4.my_parser.parse_args([])
        self.assertIsNone(args4.Region)  # No default

    def test_environment_variable_region_default(self):
        """Test that AWS_DEFAULT_REGION environment variable is used"""
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'eu-central-1'}):
            parser = CommonArguments()
            parser.multiregion()
            args = parser.my_parser.parse_args([])
            self.assertEqual(args.Regions, ['eu-central-1'])

    def test_argument_aliases(self):
        """Test that argument aliases work correctly"""
        self.parser.multiprofile()
        self.parser.multiregion()
        self.parser.extendedargs()
        self.parser.verbosity()
        
        # Test profile aliases
        args1 = self.parser.my_parser.parse_args(['-p', 'profile1'])
        args2 = self.parser.my_parser.parse_args(['-ps', 'profile1'])
        args3 = self.parser.my_parser.parse_args(['--profiles', 'profile1'])
        
        for args in [args1, args2, args3]:
            self.assertEqual(args.Profiles, ['profile1'])
        
        # Test region aliases
        args4 = self.parser.my_parser.parse_args(['-r', 'us-west-1'])
        args5 = self.parser.my_parser.parse_args(['-rs', 'us-west-1'])
        args6 = self.parser.my_parser.parse_args(['--regions', 'us-west-1'])
        
        for args in [args4, args5, args6]:
            self.assertEqual(args.Regions, ['us-west-1'])
        
        # Test skip account aliases
        args7 = self.parser.my_parser.parse_args(['-k', '123456789012'])
        args8 = self.parser.my_parser.parse_args(['-ka', '123456789012'])
        args9 = self.parser.my_parser.parse_args(['--skip', '123456789012'])
        
        for args in [args7, args8, args9]:
            self.assertEqual(args.SkipAccounts, ['123456789012'])


if __name__ == '__main__':
    unittest.main()


class TestEnisOperationArguments(unittest.TestCase):
    """Test cases for ENIs operation-specific arguments"""

    def setUp(self):
        """Set up test fixtures"""
        from inv_scr.operations import enis
        self.parser = CommonArguments()
        self.parser.multiprofile()
        self.parser.multiregion()
        self.parser.extendedargs()
        self.parser.rootOnly()
        self.parser.timing()
        self.parser.save_to_file()
        self.parser.verbosity()
        enis.add_operation_args(self.parser)

    def test_ipaddress_argument(self):
        """Test --ipaddress argument parsing"""
        args = self.parser.my_parser.parse_args(['--ipaddress', '1.2.3.4', '5.6.7.8'])
        self.assertEqual(args.pipaddresses, ['1.2.3.4', '5.6.7.8'])

    def test_ipaddress_alias(self):
        """Test --ip alias for --ipaddress"""
        args = self.parser.my_parser.parse_args(['--ip', '1.2.3.4'])
        self.assertEqual(args.pipaddresses, ['1.2.3.4'])

    def test_fqdn_argument(self):
        """Test --fqdn argument parsing"""
        args = self.parser.my_parser.parse_args(['--fqdn', 'example.com', 'test.example.com'])
        self.assertEqual(args.pDNSNames, ['example.com', 'test.example.com'])

    def test_fqdn_alias(self):
        """Test --name alias for --fqdn"""
        args = self.parser.my_parser.parse_args(['--name', 'example.com'])
        self.assertEqual(args.pDNSNames, ['example.com'])

    def test_fqdn_single_value(self):
        """Test --fqdn with single value"""
        args = self.parser.my_parser.parse_args(['--fqdn', 'example.com'])
        self.assertEqual(args.pDNSNames, ['example.com'])

    def test_fqdn_multiple_values(self):
        """Test --fqdn with multiple values"""
        args = self.parser.my_parser.parse_args(['--fqdn', 'example.com', 'api.example.com', 'www.example.com'])
        self.assertEqual(args.pDNSNames, ['example.com', 'api.example.com', 'www.example.com'])

    def test_public_only_argument(self):
        """Test --public-only argument parsing"""
        args = self.parser.my_parser.parse_args(['--public-only'])
        self.assertTrue(args.ppublic)

    def test_public_only_alias(self):
        """Test --po alias for --public-only"""
        args = self.parser.my_parser.parse_args(['--po'])
        self.assertTrue(args.ppublic)

    def test_combined_ipaddress_and_fqdn(self):
        """Test using both --ipaddress and --fqdn together"""
        args = self.parser.my_parser.parse_args([
            '--ipaddress', '1.2.3.4', '5.6.7.8',
            '--fqdn', 'example.com', 'test.example.com'
        ])
        self.assertEqual(args.pipaddresses, ['1.2.3.4', '5.6.7.8'])
        self.assertEqual(args.pDNSNames, ['example.com', 'test.example.com'])

    def test_fqdn_with_public_only(self):
        """Test --fqdn with --public-only"""
        args = self.parser.my_parser.parse_args([
            '--fqdn', 'example.com',
            '--public-only'
        ])
        self.assertEqual(args.pDNSNames, ['example.com'])
        self.assertTrue(args.ppublic)

    def test_all_enis_arguments_combined(self):
        """Test all ENIs-specific arguments together"""
        args = self.parser.my_parser.parse_args([
            '--profiles', 'profile1', 'profile2',
            '--regions', 'us-east-1', 'us-west-2',
            '--ipaddress', '1.2.3.4',
            '--fqdn', 'example.com', 'test.example.com',
            '--public-only',
            '--verbose'
        ])
        self.assertEqual(args.Profiles, ['profile1', 'profile2'])
        self.assertEqual(args.Regions, ['us-east-1', 'us-west-2'])
        self.assertEqual(args.pipaddresses, ['1.2.3.4'])
        self.assertEqual(args.pDNSNames, ['example.com', 'test.example.com'])
        self.assertTrue(args.ppublic)
        self.assertEqual(args.loglevel, 30)

    def test_fqdn_default_none(self):
        """Test that --fqdn defaults to None when not provided"""
        args = self.parser.my_parser.parse_args([])
        self.assertIsNone(args.pDNSNames)

    def test_ipaddress_default_none(self):
        """Test that --ipaddress defaults to None when not provided"""
        args = self.parser.my_parser.parse_args([])
        self.assertIsNone(args.pipaddresses)

    def test_public_only_default_false(self):
        """Test that --public-only defaults to False when not provided"""
        args = self.parser.my_parser.parse_args([])
        self.assertFalse(args.ppublic)
