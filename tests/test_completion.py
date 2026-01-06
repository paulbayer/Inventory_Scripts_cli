#!/usr/bin/env python3
"""
Test tab completion functionality
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import inv_scr modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from inv_scr.completion import operation_completer, profile_completer, region_completer, ARGCOMPLETE_AVAILABLE
    COMPLETION_AVAILABLE = True
except ImportError:
    COMPLETION_AVAILABLE = False
    ARGCOMPLETE_AVAILABLE = False


class TestCompletion(unittest.TestCase):
    """Test completion functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not COMPLETION_AVAILABLE:
            self.skipTest("completion module not available")
    
    def test_operation_completer(self):
        """Test operation completion"""
        # Test completing 'ins' should return 'instances'
        completions = operation_completer('ins', None)
        self.assertIn('instances', completions)
        
        # Test completing 'vpc' should return 'vpcs'
        completions = operation_completer('vpc', None)
        self.assertIn('vpcs', completions)
        
        # Test completing 'list' should return 'list'
        completions = operation_completer('lis', None)
        self.assertIn('list', completions)
        
        # Test no matches
        completions = operation_completer('xyz', None)
        self.assertEqual(len(completions), 0)
    
    @patch('boto3.Session')
    def test_profile_completer(self, mock_session_class):
        """Test AWS profile completion"""
        # Mock boto3 session
        mock_session = MagicMock()
        mock_session.available_profiles = ['default', 'prod', 'dev', 'test']
        mock_session_class.return_value = mock_session
        
        # Test completing 'pr' should return 'prod'
        completions = profile_completer('pr', None)
        self.assertIn('prod', completions)
        
        # Test completing 'de' should return 'dev'
        completions = profile_completer('de', None)
        self.assertIn('dev', completions)
        
        # Test no matches
        completions = profile_completer('xyz', None)
        self.assertEqual(len(completions), 0)
    
    @patch('boto3.client')
    def test_region_completer(self, mock_client):
        """Test AWS region completion"""
        # Mock EC2 client response
        mock_ec2 = MagicMock()
        mock_ec2.describe_regions.return_value = {
            'Regions': [
                {'RegionName': 'us-east-1'},
                {'RegionName': 'us-west-2'},
                {'RegionName': 'eu-west-1'},
            ]
        }
        mock_client.return_value = mock_ec2
        
        # Test completing 'us' should return US regions
        completions = region_completer('us', None)
        self.assertIn('us-east-1', completions)
        self.assertIn('us-west-2', completions)
        
        # Test completing 'eu' should return EU regions
        completions = region_completer('eu', None)
        self.assertIn('eu-west-1', completions)
        
        # Test 'all' option is included
        completions = region_completer('al', None)
        self.assertIn('all', completions)
    
    def test_region_completer_fallback(self):
        """Test region completer fallback when API fails"""
        with patch('boto3.client', side_effect=Exception("API Error")):
            # Should fall back to common regions
            completions = region_completer('us', None)
            self.assertIn('us-east-1', completions)
            self.assertIn('us-west-2', completions)
            
            # Test that 'all' is available when prefix matches
            completions = region_completer('al', None)
            self.assertIn('all', completions)
    
    def test_argcomplete_availability(self):
        """Test that argcomplete availability is properly detected"""
        # This test will pass whether argcomplete is available or not
        self.assertIsInstance(ARGCOMPLETE_AVAILABLE, bool)
        if ARGCOMPLETE_AVAILABLE:
            # If available, we should be able to import it
            import argcomplete
            self.assertTrue(hasattr(argcomplete, 'autocomplete'))


class TestCompletionIntegration(unittest.TestCase):
    """Test completion integration with CLI"""
    
    def test_cli_imports_without_completion(self):
        """Test that CLI can import even if completion fails"""
        # This should always work
        from inv_scr.cli import OPERATIONS, parse_args
        self.assertIsInstance(OPERATIONS, dict)
        self.assertTrue(len(OPERATIONS) > 0)
    
    def test_completion_setup_graceful_failure(self):
        """Test that completion setup fails gracefully"""
        from inv_scr.completion import setup_completion
        from argparse import ArgumentParser
        
        # Create a mock parser
        parser = ArgumentParser()
        parser.add_argument('operation', choices=['test'])
        
        # This should not raise an exception
        try:
            setup_completion(parser)
        except Exception as e:
            self.fail(f"setup_completion raised an exception: {e}")


if __name__ == '__main__':
    unittest.main()