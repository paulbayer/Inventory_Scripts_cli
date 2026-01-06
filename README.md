# AWS Inventory Scripts CLI

A unified command-line tool for finding AWS resources across one or more AWS Organizations. This tool consolidates multiple inventory scripts into a single, easy-to-use CLI with shared components and consistent output formatting.

## Features

- **Unified Interface**: Single CLI tool with multiple operations instead of separate scripts
- **Multi-Account Support**: Works across AWS Organizations with automatic credential management
- **Multi-Region Support**: Search across all regions or specify specific regions
- **Flexible Authentication**: Supports AWS profiles, environment variables, and cross-account roles
- **Consistent Output**: Standardized display and optional file output for all operations
- **Extensible**: Easy to add new inventory operations

## Requirements

- Python 3.6+
- boto3
- Valid AWS credentials (profiles, environment variables, or IAM roles)

## Installation

### From Source
```bash
git clone <repository-url>
cd inventory_scripts_cli
pip install -e .
```

### Using Make
```bash
make install
```

## Usage

### List Available Operations
```bash
inv_scr list
```

### Basic Usage
```bash
# Find EC2 instances across all profiles and regions
inv_scr instances --profiles all --regions all

# Find VPCs in specific profiles and regions
inv_scr vpcs --profiles prod-profile dev-profile --regions us-east-1 us-west-2

# Find only running EC2 instances
inv_scr instances --status running --profiles my-profile

# Save results to file
inv_scr vpcs --profiles my-profile --filename vpc-inventory.txt
```

### Common Options

- `--profiles` / `-p`: Specify AWS profiles to use (default: all available profiles)
- `--regions` / `-r`: Specify regions to search (default: us-east-1, use 'all' for all opted-in regions)
- `--accounts` / `-a`: Limit to specific account numbers
- `--skip` / `-k`: Skip specific account numbers
- `--skipprofiles` / `-kp`: Skip specific profiles
- `--rootonly`: Only search root accounts, not child accounts
- `--access_rolename`: Specify roles for cross-account access
- `--filename`: Save output to file
- `--timing`: Show execution timing
- `--verbose` / `-v`: Increase verbosity (use -vv, -vvv for more detail)

### Available Operations

| Operation | Description |
|-----------|-------------|
| `cfnstacks` | Find CloudFormation stacks |
| `cfnstacksets` | Find CloudFormation stack sets |
| `directories` | Find AWS Directory Service directories |
| `ebs-volumes` | Find EBS volumes |
| `ecs-clusters` | Find ECS clusters and tasks |
| `elbs` | Find Elastic Load Balancers |
| `enis` | Find Elastic Network Interfaces |
| `functions` | Find Lambda functions |
| `gas` | Find Global Accelerator accelerators |
| `gd-detectors` | Find GuardDuty detectors |
| `instances` | Find EC2 instances across accounts |
| `orgs` | Find AWS Organizations information |
| `phzs` | Find Private Hosted Zones |
| `policies` | Find IAM policies |
| `rds-instances` | Find RDS instances |
| `roles` | Find IAM roles |
| `saml-providers` | Find SAML identity providers |
| `subnets` | Find VPC subnets |
| `tgws` | Find Transit Gateways |
| `topics` | Find SNS topics |
| `vpcs` | Find VPCs across accounts |

### Operation-Specific Options

Each operation may have specific options. Use `--help` with any operation to see available options:

```bash
inv_scr instances --help
inv_scr vpcs --help
```

## Examples

### Find All EC2 Instances
```bash
# All instances across all profiles and regions
inv_scr instances --profiles all --regions all

# Only running instances in production profile
inv_scr instances --profiles prod --status running --regions us-east-1
```

### Find VPCs
```bash
# All VPCs in specific regions
inv_scr vpcs --regions us-east-1 eu-west-1

# Only default VPCs
inv_scr vpcs --default --profiles all --regions all
```

### Cross-Account Access
```bash
# Use specific role for child account access
inv_scr instances --profiles org-master --access_rolename OrganizationAccountAccessRole

# Skip certain accounts
inv_scr vpcs --profiles all --skip 123456789012 987654321098
```

## Migration from Individual Scripts

If you were previously using individual scripts like `all_my_instances.py`, the equivalent commands are:

- `all_my_instances.py` → `inv_scr instances`
- `all_my_vpcs.py` → `inv_scr vpcs`
- `all_my_cfnstacks.py` → `inv_scr cfnstacks`
- etc.

All the same command-line options are supported, just use the new unified interface.

## Development

### Adding New Operations

1. Create a new file in `inv_scr/operations/` (e.g., `new_resource.py`)
2. Implement the required functions:
   ```python
   def add_operation_args(parser):
       """Add operation-specific arguments"""
       pass
   
   def run(args):
       """Main execution function"""
       pass
   ```
3. Add the operation to the `OPERATIONS` dict in `inv_scr/cli.py`

### Project Structure

```
inv_scr/
├── cli.py              # Main CLI entry point
├── __main__.py         # Module execution entry
├── core/               # Shared core functionality
│   ├── ArgumentsClass.py
│   ├── account_class.py
│   ├── Inventory_Modules.py
│   └── ...
├── operations/         # Individual inventory operations
│   ├── instances.py
│   ├── vpcs.py
│   └── ...
legacy_operations/      # Legacy individual scripts (deprecated)
```

## Troubleshooting

### Authentication Issues
- Ensure your AWS profiles are properly configured
- Check that cross-account roles exist and have proper permissions
- Use `--verbose` for detailed authentication debugging

### Region Issues
- Some regions may not be opted-in for your account
- Use `--regions all` to search all opted-in regions
- Check AWS console for region opt-in status

### Performance
- Use `--timing` to identify slow operations
- Consider limiting regions or accounts for faster execution
- The tool uses threading for parallel execution across accounts/regions

