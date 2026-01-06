#!/usr/bin/env python3
"""
Simple syntax test for ram_shares tests
"""

import sys
sys.path.insert(0, '.')

try:
    from inv_scr.operations import ram_shares
    from tests.mock_fixtures import MockOperationHelpers
    from unittest.mock import MagicMock, patch
    print("✅ All imports successful")
    
    # Test creating mock args
    mock_args = MockOperationHelpers.create_mock_args(pStatus='ACTIVE', pType='OWNED')
    print(f"✅ Mock args created: pStatus={mock_args.pStatus}, pType={mock_args.pType}")
    
    # Test calling add_operation_args
    mock_parser = MagicMock()
    mock_group = MagicMock()
    mock_parser.my_parser.add_argument_group.return_value = mock_group
    
    ram_shares.add_operation_args(mock_parser)
    print("✅ add_operation_args called successfully")
    
    print("✅ All syntax tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()