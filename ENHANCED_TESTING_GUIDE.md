# Enhanced Testing Guide: Credential-Level Mocking

This guide explains how to use the new credential-level mocking system to thoroughly test your AWS inventory operations, including all data transformation logic and business rules.

## 🎯 What's New

### Before: Basic Function Mocking
```python
# Old approach - only tested mechanics
@patch('inv_scr.operations.instances.get_all_credentials')
@patch('inv_scr.operations.instances.find_all_instances')
def test_run_basic_execution(self, mock_find, mock_creds):
    mock_creds.return_value = [{'AccountId': '123456789012'}]
    mock_find.return_value = [{'InstanceId': 'i-123'}]
    # This only tests that functions are called, not the logic
```

### After: Credential-Level Mocking
```python
# New approach - tests complete logic flow
@patch('inv_scr.operations.instances.get_all_credentials')
@patch('inv_scr.operations.instances.Inventory_Modules.find_account_instances2')
def test_run_with_realistic_data(self, mock_find_account, mock_get_creds):
    # Use realistic credential fixtures
    mock_get_creds.return_value = MockCredentialFixtures.single_account_single_region()
    
    # Use realistic AWS response fixtures
    mock_find_account.return_value = MockAWSResponseFixtures.ec2_instances_response(num_instances=3)
    
    # Test the complete operation including data transformation
    instances.run(mock_args)
    # Now we can verify the actual business logic worked correctly
```

## 🧪 Mock Fixtures Overview

### Credential Fixtures

#### `MockCredentialFixtures.single_account_single_region()`
Perfect for basic testing scenarios:
```python
[{
    'AccountId': '123456789012',
    'Region': 'us-east-1', 
    'MgmtAccount': '123456789012',
    'ParentProfile': 'test-profile',
    'AccessKeyId': 'AKIAIOSFODNN7EXAMPLE',
    'SecretAccessKey': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    'SessionToken': 'example-session-token'
}]
```

#### `MockCredentialFixtures.multi_account_single_region()`
Tests organizational scenarios with multiple AWS accounts:
- 3 different AWS accounts
- Same region (us-east-1)
- Same parent profile (org-profile)

#### `MockCredentialFixtures.single_account_multi_region()`
Tests multi-region deployments:
- Single AWS account
- 3 regions: us-east-1, us-west-2, eu-west-1
- Tests region-specific logic

#### `MockCredentialFixtures.complex_org_structure()`
Tests enterprise scenarios:
- 4 AWS accounts
- 3 regions each
- 12 total credential combinations
- Tests scalability and performance

### AWS Response Fixtures

#### `MockAWSResponseFixtures.ec2_instances_response(num_instances=2)`
Generates realistic EC2 instance data:
```python
{
    'Reservations': [{
        'Instances': [
            {
                'InstanceId': 'i-0000000000000abcdef0',
                'InstanceType': 't3.micro',
                'State': {'Name': 'running'},
                'PublicDnsName': 'ec2-0-0-0-0.compute-1.amazonaws.com',
                'Tags': [
                    {'Key': 'Name', 'Value': 'test-instance-0'},
                    {'Key': 'Environment', 'Value': 'test'}
                ]
            }
        ]
    }]
}
```

#### Other Response Fixtures
- `vpc_response()` - VPC data with CIDR blocks and tags
- `lambda_functions_response()` - Lambda functions with different runtimes
- `cloudformation_stacks_response()` - CloudFormation stacks
- `rds_instances_response()` - RDS database instances

## 🔧 How to Write Enhanced Tests

### Step 1: Import the Fixtures
```python
from tests.mock_fixtures import MockCredentialFixtures, MockAWSResponseFixtures, MockOperationHelpers
```

### Step 2: Set Up Your Test
```python
@patch('inv_scr.operations.instances.get_all_credentials')
@patch('inv_scr.operations.instances.Inventory_Modules.find_account_instances2')
@patch('inv_scr.operations.instances.display_results')
@patch('sys.stdout', new_callable=io.StringIO)
def test_your_scenario(self, mock_stdout, mock_display, mock_find_account, mock_get_creds):
```

### Step 3: Configure Mock Data
```python
# Choose appropriate credential fixture
mock_credentials = MockCredentialFixtures.single_account_single_region()
mock_get_creds.return_value = mock_credentials

# Choose appropriate AWS response fixture  
mock_aws_response = MockAWSResponseFixtures.ec2_instances_response(num_instances=3)
mock_find_account.return_value = mock_aws_response

# Create mock arguments
mock_args = MockOperationHelpers.create_mock_args(pStatus='running')
```

### Step 4: Execute and Verify
```python
# Run the operation
instances.run(mock_args)

# Verify the complete flow
mock_get_creds.assert_called_once()
mock_find_account.assert_called_once_with(mock_credentials[0])
mock_display.assert_called_once()

# Test the actual business logic
display_args = mock_display.call_args[0][0]
self.assertEqual(len(display_args), 3)  # Should have 3 instances

# Verify data transformation
for instance in display_args:
    self.assertEqual(instance['AccountId'], '123456789012')
    self.assertEqual(instance['Region'], 'us-east-1')
    self.assertEqual(instance['ParentProfile'], 'test-profile')
    # Test your specific business logic here
```

## 📋 Test Scenarios You Can Now Cover

### 1. Data Transformation Logic
```python
def test_instance_name_extraction_logic(self):
    """Test that instance names are correctly extracted from tags"""
    # Mock response with various tag scenarios
    mock_response = {
        'Reservations': [{
            'Instances': [
                {
                    'InstanceId': 'i-withname',
                    'Tags': [{'Key': 'Name', 'Value': 'my-server'}]
                },
                {
                    'InstanceId': 'i-noname',
                    'Tags': [{'Key': 'Environment', 'Value': 'prod'}]
                },
                {
                    'InstanceId': 'i-notags'
                    # No tags at all
                }
            ]
        }]
    }
    
    # Test that your logic handles all cases correctly
    # - Extracts name when present
    # - Uses "No Name Tag" when missing
    # - Handles instances with no tags
```

### 2. Filtering Logic
```python
def test_status_filtering_logic(self):
    """Test that status filtering works correctly"""
    # Create mixed instance states
    # Test that only requested states are returned
    # Verify edge cases (empty results, all filtered out)
```

### 3. Multi-Account Scenarios
```python
def test_multi_account_data_aggregation(self):
    """Test that data from multiple accounts is correctly aggregated"""
    # Use multi-account credentials
    # Mock different responses per account
    # Verify account attribution is correct
    # Test account-specific error handling
```

### 4. Multi-Region Scenarios
```python
def test_multi_region_data_handling(self):
    """Test that multi-region data is handled correctly"""
    # Use multi-region credentials
    # Mock different responses per region
    # Verify region attribution
    # Test region-specific failures
```

### 5. Error Handling
```python
def test_aws_api_error_handling(self):
    """Test that AWS API errors are handled gracefully"""
    # Mock AWS API exceptions
    # Verify error logging
    # Ensure partial failures don't break everything
```

### 6. Performance with Large Datasets
```python
def test_large_dataset_handling(self):
    """Test performance with large numbers of resources"""
    # Use fixtures with many resources
    # Verify threading works correctly
    # Test memory usage patterns
```

## 🚀 Running the Enhanced Tests

### Quick Test Run
```bash
# Run the enhanced test runner
python3 run_enhanced_tests.py
```

### Individual Test Categories
```bash
# Run just EC2 instance enhanced tests
python3 -m unittest \
  tests.test_operations.TestInstancesOperation.test_run_with_single_account_credentials \
  tests.test_operations.TestInstancesOperation.test_run_with_multi_account_credentials \
  -v

# Run just VPC enhanced tests  
python3 -m unittest \
  tests.test_operations.TestVPCsOperation.test_run_with_comprehensive_vpc_data \
  tests.test_operations.TestVPCsOperation.test_run_with_default_vpc_filtering \
  -v
```

### Specific Test Patterns
```bash
# Run all enhanced credential tests
python3 -m unittest discover tests -k "credential" -v

# Run all filtering logic tests
python3 -m unittest discover tests -k "filtering" -v

# Run all multi-account tests
python3 -m unittest discover tests -k "multi_account" -v
```

## 🎯 Benefits of This Approach

### ✅ What You Now Test
1. **Complete Data Flow**: From credentials → AWS API → data transformation → display
2. **Business Logic**: Filtering, sorting, data extraction, error handling
3. **Multi-Account/Region**: Complex organizational scenarios
4. **Edge Cases**: Empty responses, missing data, malformed responses
5. **Performance**: Threading, large datasets, timeout handling
6. **Error Scenarios**: AWS API failures, credential issues, network problems

### ✅ Confidence Improvements
- **Refactoring Safety**: Changes to data transformation logic are caught
- **Business Rule Validation**: Filtering and processing logic is verified
- **Integration Confidence**: Full operation flow is tested
- **Regression Prevention**: Complex scenarios are automatically tested

## 📈 Extending the Framework

### Adding New Operations
1. Create AWS response fixtures for your operation
2. Add credential-level mocking tests
3. Test operation-specific business logic
4. Add to the enhanced test runner

### Adding New Scenarios
1. Create new credential fixtures for your use case
2. Create corresponding AWS response fixtures
3. Write tests that combine them
4. Document the new scenario

### Example: Adding S3 Bucket Operation
```python
# In mock_fixtures.py
@staticmethod
def s3_buckets_response(num_buckets: int = 2) -> Dict[str, Any]:
    """Mock S3 list_buckets response"""
    buckets = []
    for i in range(num_buckets):
        buckets.append({
            'Name': f'test-bucket-{i}',
            'CreationDate': '2023-01-01T12:00:00.000Z'
        })
    return {'Buckets': buckets}

# In test_operations.py
@patch('inv_scr.operations.s3_buckets.get_all_credentials')
@patch('inv_scr.operations.s3_buckets.Inventory_Modules.find_account_s3_buckets2')
def test_s3_buckets_with_credentials(self, mock_find_account, mock_get_creds):
    mock_get_creds.return_value = MockCredentialFixtures.single_account_single_region()
    mock_find_account.return_value = MockAWSResponseFixtures.s3_buckets_response(num_buckets=5)
    
    # Test your S3 bucket operation logic
```

## 🎉 Success Metrics

You'll know the enhanced testing is working when:

1. **Tests catch real bugs** in data transformation logic
2. **Refactoring is safer** because business logic is tested
3. **New features** can be developed with confidence
4. **Edge cases** are automatically covered
5. **Multi-account scenarios** work correctly in production

The enhanced testing framework gives you the confidence to modify and extend your AWS inventory operations while ensuring all the business logic continues to work correctly! 🚀