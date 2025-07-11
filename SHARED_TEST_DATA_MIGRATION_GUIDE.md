# Shared Test Data Migration Guide

## 🎯 Overview

The shared test data system eliminates duplication and provides consistent, realistic test data across all operations. This guide shows how to migrate existing tests and create new ones using the centralized system.

## 🏗️ Architecture

### Before: Duplicated Test Data
```python
# In test_operations.py - EC2 tests
mock_credentials = [
    {'AccountId': '123456789012', 'Region': 'us-east-1', ...}
]

# In test_operations.py - VPC tests  
mock_credentials = [
    {'AccountId': '123456789012', 'Region': 'us-east-1', ...}  # Duplicate!
]

# In test_operations.py - Lambda tests
mock_credentials = [
    {'AccountId': '123456789012', 'Region': 'us-east-1', ...}  # Duplicate!
]
```

### After: Shared Test Data System
```python
# In shared_test_data.py - Single source of truth
SharedTestAccounts.MASTER_ACCOUNT = TestAccount("123456789012", "master-account")

# In all test files - Consistent usage
mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
```

## 📋 Migration Steps

### Step 1: Identify Test Data Patterns

Look for these patterns in your existing tests:
- Hardcoded account IDs (`'123456789012'`)
- Hardcoded region codes (`'us-east-1'`)
- Repeated credential structures
- Repeated AWS response structures

### Step 2: Choose Appropriate Scenarios

Map your existing test patterns to shared scenarios:

| Existing Pattern | Shared Scenario | Usage |
|------------------|-----------------|-------|
| Single account, single region | `'simple'` | Basic functionality tests |
| Multiple accounts, single region | `'multi_account'` | Organizational tests |
| Single account, multiple regions | `'multi_region'` | Regional deployment tests |
| Complex multi-account/region | `'enterprise'` | Full enterprise tests |

### Step 3: Update Credential Usage

#### Before:
```python
def test_something(self):
    mock_credentials = [
        {
            'AccountId': '123456789012',
            'Region': 'us-east-1',
            'MgmtAccount': '123456789012',
            'ParentProfile': 'test-profile',
            'AccessKeyId': 'AKIAIOSFODNN7EXAMPLE',
            'SecretAccessKey': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
            'SessionToken': 'example-session-token'
        }
    ]
```

#### After:
```python
def test_something(self):
    mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
    # OR for backward compatibility:
    mock_credentials = MockCredentialFixtures.single_account_single_region()
```

### Step 4: Update AWS Response Usage

#### Before:
```python
def test_ec2_instances(self):
    mock_response = {
        'Reservations': [{
            'Instances': [
                {
                    'InstanceId': 'i-1234567890abcdef0',
                    'InstanceType': 't3.micro',
                    'State': {'Name': 'running'},
                    'Tags': [{'Key': 'Name', 'Value': 'test-instance'}]
                }
            ]
        }]
    }
```

#### After:
```python
def test_ec2_instances(self):
    mock_response = MockAWSResponseFixtures.ec2_instances_response(
        num_instances=1, scenario='simple'
    )
    # More realistic data with proper account/region context
```

## 🔧 Practical Migration Examples

### Example 1: Simple EC2 Test Migration

#### Before:
```python
@patch('inv_scr.operations.instances.get_all_credentials')
@patch('inv_scr.operations.instances.Inventory_Modules.find_account_instances2')
def test_single_account_instances(self, mock_find_account, mock_get_creds):
    # Hardcoded test data
    mock_credentials = [
        {
            'AccountId': '123456789012',
            'Region': 'us-east-1',
            'MgmtAccount': '123456789012',
            'ParentProfile': 'test-profile'
        }
    ]
    
    mock_response = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': 'i-1234567890abcdef0',
                'InstanceType': 't3.micro',
                'State': {'Name': 'running'},
                'Tags': [{'Key': 'Name', 'Value': 'test-instance'}]
            }]
        }]
    }
    
    mock_get_creds.return_value = mock_credentials
    mock_find_account.return_value = mock_response
    
    # Test logic...
```

#### After:
```python
@patch('inv_scr.operations.instances.get_all_credentials')
@patch('inv_scr.operations.instances.Inventory_Modules.find_account_instances2')
def test_single_account_instances(self, mock_find_account, mock_get_creds):
    # Use shared test data
    mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
    mock_response = MockAWSResponseFixtures.ec2_instances_response(
        num_instances=1, scenario='simple'
    )
    
    mock_get_creds.return_value = mock_credentials
    mock_find_account.return_value = mock_response
    
    # Test logic... (same as before)
    
    # But now you can make more realistic assertions:
    display_args = mock_display.call_args[0][0]
    instance = display_args[0]
    self.assertTrue(instance['Name'].startswith('master-account-instance-'))
    self.assertEqual(instance['AccountId'], '123456789012')
```

### Example 2: Multi-Account Test Migration

#### Before:
```python
def test_multi_account_scenario(self):
    # Duplicated multi-account setup
    mock_credentials = [
        {'AccountId': '123456789012', 'Region': 'us-east-1', ...},
        {'AccountId': '234567890123', 'Region': 'us-east-1', ...},
        {'AccountId': '345678901234', 'Region': 'us-east-1', ...}
    ]
    
    def side_effect(credential):
        if credential['AccountId'] == '123456789012':
            return {'Reservations': [{'Instances': [...]}]}
        elif credential['AccountId'] == '234567890123':
            return {'Reservations': [{'Instances': [...]}]}
        else:
            return {'Reservations': []}
```

#### After:
```python
def test_multi_account_scenario(self):
    # Use shared multi-account scenario
    mock_credentials = MockCredentialFixtures.get_scenario_credentials('multi_account')
    
    def side_effect(credential):
        account_id = credential['AccountId']
        if account_id == '123456789012':  # master-account
            return MockAWSResponseFixtures.ec2_instances_response(2, scenario='simple')
        elif account_id == '234567890123':  # dev-account
            return MockAWSResponseFixtures.ec2_instances_response(1, scenario='simple')
        else:
            return {'Reservations': []}
    
    # More realistic and maintainable!
```

## 🆕 Creating New Tests with Shared Data

### Template for New Operation Tests

```python
from tests.mock_fixtures import MockCredentialFixtures, MockAWSResponseFixtures, MockOperationHelpers

class TestNewOperation(unittest.TestCase):
    
    def test_simple_scenario(self):
        """Test basic functionality with simple scenario"""
        # Use shared scenario
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('simple')
        mock_response = MockAWSResponseFixtures.your_service_response(scenario='simple')
        
        # Standard test setup...
        
    def test_multi_account_scenario(self):
        """Test multi-account functionality"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('multi_account')
        
        # Use scenario-aware side effects
        def side_effect(credential):
            # Automatically handles all accounts in the scenario
            return MockAWSResponseFixtures.your_service_response(scenario='multi_account')
        
        # Test logic...
        
    def test_enterprise_scenario(self):
        """Test complex enterprise setup"""
        mock_credentials = MockCredentialFixtures.get_scenario_credentials('enterprise')
        # Handles 4 accounts × 3 regions = 12 credentials automatically!
```

## 🔄 Backward Compatibility

The shared test data system maintains full backward compatibility:

```python
# Old methods still work
MockCredentialFixtures.single_account_single_region()
MockCredentialFixtures.multi_account_single_region()
MockAWSResponseFixtures.ec2_instances_response(num_instances=2)

# New methods provide enhanced functionality
MockCredentialFixtures.get_scenario_credentials('simple')
MockAWSResponseFixtures.ec2_instances_response(num_instances=2, scenario='simple')
```

## 📊 Benefits Comparison

| Aspect | Before (Duplicated) | After (Shared) |
|--------|-------------------|----------------|
| **Maintainability** | ❌ Change in 20+ places | ✅ Change in 1 place |
| **Consistency** | ❌ Different test data | ✅ Consistent across tests |
| **Realism** | ❌ Generic IDs | ✅ Realistic account names |
| **Readability** | ❌ Verbose setup | ✅ Clean, focused tests |
| **Extensibility** | ❌ Copy-paste new data | ✅ Add scenarios easily |

## 🚀 Advanced Usage

### Custom Scenarios

```python
# Create custom scenarios for specific needs
def test_security_focused_scenario(self):
    # Use specific accounts
    accounts = [SharedTestAccounts.SECURITY_ACCOUNT, SharedTestAccounts.LOGGING_ACCOUNT]
    credentials = SharedCredentialBuilder.multi_account_single_region(accounts)
    
    # Custom response building
    mock_response = ResponseBuilder.build_ec2_response('custom', instances_per_account=1)
```

### Extending Shared Data

```python
# Add new test accounts in shared_test_data.py
class SharedTestAccounts:
    COMPLIANCE_ACCOUNT = TestAccount("789012345678", "compliance-account")
    
    @classmethod
    def get_security_accounts(cls):
        return [cls.SECURITY_ACCOUNT, cls.COMPLIANCE_ACCOUNT, cls.LOGGING_ACCOUNT]
```

## 📋 Migration Checklist

- [ ] **Identify duplicated test data** in existing tests
- [ ] **Map test patterns** to appropriate shared scenarios
- [ ] **Update credential usage** to use `MockCredentialFixtures.get_scenario_credentials()`
- [ ] **Update response usage** to use scenario-based responses
- [ ] **Test backward compatibility** - ensure existing tests still pass
- [ ] **Enhance assertions** to use realistic data from shared system
- [ ] **Document custom scenarios** if you create any
- [ ] **Update team documentation** about the new system

## 🎉 Success Metrics

You'll know the migration is successful when:

1. **No duplicated test data** across test files
2. **Consistent account/region usage** across all tests
3. **Realistic test data** with meaningful names
4. **Easy test creation** for new operations
5. **Maintainable test suite** - changes in one place affect all tests

The shared test data system transforms your test suite from a maintenance burden into a powerful, consistent testing framework! 🚀