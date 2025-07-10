# AWS Inventory CLI - Versioning Guide

This guide explains the comprehensive versioning system implemented for the AWS Inventory CLI, which provides version tracking for both the main CLI and individual operations.

## 🎯 Versioning Overview

The AWS Inventory CLI uses a **dual-versioning system**:

1. **Main CLI Version**: Tracks changes to the overall CLI framework, argument parsing, and core functionality
2. **Operation-Specific Versions**: Tracks changes to individual inventory operations (instances, VPCs, etc.)

## 📋 Version Information

### Main CLI Version
- **Current Version**: `2025.07.10`
- **Location**: `inv_scr/cli.py` (`__version__` variable)
- **Scope**: Core CLI functionality, argument parsing, operation routing, shared components

### Operation Versions
- **Current Version**: `2025.07.10` (all operations)
- **Location**: Each operation file (`inv_scr/operations/*.py`)
- **Scope**: Individual operation functionality, AWS API interactions, data processing

## 🔍 Checking Versions

### Main CLI Version
```bash
# Check main CLI version
inv_scr --version
```
**Output:**
```
Version: 2025.07.10
```

### Operation-Specific Versions
```bash
# Check individual operation versions
inv_scr instances --operation-version
inv_scr vpcs --operation-version
inv_scr cfnstacks --operation-version
```

**Output Examples:**
```
EC2 Instances operation version 2025.07.10
VPC operation version 2025.07.10
CloudFormation Stacks operation version 2025.07.10
```

### All Operations Version Check
```bash
# Test all operations for versioning
make test-versions
```

## 🏗️ Version Display During Execution

When operations run, they display both the main CLI version and their specific operation version:

```bash
inv_scr cfnstacks
```

**Output:**
```
AWS Inventory CLI v2025.07.10          # Main CLI version
Running operation: cfnstacks

CloudFormation stacks inventory - Implementation coming soon!
This will search for CloudFormation stacks across your AWS accounts.
Operation version: 2025.07.10          # Operation-specific version

Operation completed successfully
```

## 📊 Version Testing

### Automated Version Validation
```bash
# Test that all operations have versioning
make test-versions

# Validate overall CLI health (includes version checks)
make validate
```

### Manual Version Verification
```bash
# Check specific operations
inv_scr instances --operation-version
inv_scr vpcs --operation-version

# Verify version display during execution
inv_scr cfnstacks | grep "version"
```

## 🔧 Implementation Details

### Main CLI Versioning
Located in `inv_scr/cli.py`:
```python
__version__ = "2025.07.10"

# Added to argument parser
parser.version(__version__)
```

### Operation Versioning
Each operation file includes:
```python
__version__ = "2025.07.10"

def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('operation-name', 'Operation specific options')
    local.add_argument(
        "--operation-version",
        action="version",
        version=f"Operation Name operation version {__version__}"
    )

def run(args):
    """Main execution function"""
    # ... operation logic ...
    print(f"Operation version: {__version__}")
```

## 📅 Version History and Maintenance

### When to Update Versions

#### Main CLI Version (`inv_scr/cli.py`)
Update when making changes to:
- CLI argument parsing
- Operation routing logic
- Core CLI functionality
- Shared components
- Major architectural changes

#### Operation Versions (`inv_scr/operations/*.py`)
Update when making changes to:
- Individual operation functionality
- AWS API interactions
- Data processing logic
- Output formatting
- Operation-specific features

### Version Format
- **Format**: `YYYY.MM.DD`
- **Example**: `2025.01.01` (January 1st, 2025)
- **Rationale**: Date-based versioning provides clear chronological tracking

### Version Update Process
1. **Identify Scope**: Determine if changes affect main CLI or specific operations
2. **Update Version**: Modify `__version__` variable in appropriate file(s)
3. **Test Versioning**: Run `make test-versions` to verify all versions work
4. **Validate Changes**: Run `make validate` to ensure overall functionality
5. **Document Changes**: Update relevant documentation

## 🎯 Benefits of Dual Versioning

### 1. **Granular Change Tracking**
- Track when individual operations were last modified
- Identify which operations need updates
- Understand the maturity of different components

### 2. **Maintenance Visibility**
- Quickly identify outdated operations
- Plan updates based on version age
- Prioritize development efforts

### 3. **Debugging Support**
- Correlate issues with specific operation versions
- Identify when problems were introduced
- Support troubleshooting efforts

### 4. **Development Workflow**
- Independent versioning for different components
- Clear separation of concerns
- Better change management

## 📋 Version Management Best Practices

### 1. **Regular Version Updates**
- Update versions when making functional changes
- Don't update versions for documentation-only changes
- Use consistent date format (YYYY.MM.DD)

### 2. **Version Testing**
```bash
# Before committing changes
make test-versions  # Verify all operations have versioning
make validate      # Ensure overall functionality
```

### 3. **Version Documentation**
- Document significant changes in commit messages
- Reference version numbers in issue tracking
- Maintain changelog for major updates

### 4. **Automated Validation**
The versioning system includes automated validation:
- `test_operation_versions.py` - Tests all operations for version info
- `validate_tests.py` - Includes version validation in health checks
- Makefile targets for easy testing

## 🔍 Troubleshooting Versioning

### Issue: Operation Version Not Displayed
```bash
# Check if operation has version argument
inv_scr operation-name --operation-version

# Verify version variable exists in operation file
grep "__version__" inv_scr/operations/operation-name.py
```

### Issue: Version Conflict with Main CLI
The system uses `--operation-version` for operations and `--version` for main CLI to avoid conflicts.

### Issue: Missing Version Information
```bash
# Run version test to identify missing versions
make test-versions

# Check specific operation file structure
cat inv_scr/operations/operation-name.py | grep -A5 -B5 "__version__"
```

## 📈 Future Enhancements

### Planned Improvements
1. **Semantic Versioning**: Consider moving to semantic versioning (x.y.z)
2. **Version History**: Maintain changelog for each operation
3. **Automated Version Bumping**: Scripts to automatically update versions
4. **Version Compatibility**: Track compatibility between CLI and operation versions

### Integration Opportunities
1. **CI/CD Integration**: Automated version validation in build pipeline
2. **Monitoring**: Track version usage in production environments
3. **Update Notifications**: Alert users when newer versions are available

## 🎉 Summary

The dual-versioning system provides:

- ✅ **Main CLI Version**: `2025.07.10` - Core functionality tracking
- ✅ **Operation Versions**: `2025.07.10` - Individual operation tracking
- ✅ **Easy Version Checking**: `--version` and `--operation-version` arguments
- ✅ **Automated Testing**: `make test-versions` validation
- ✅ **Runtime Display**: Version information shown during execution
- ✅ **Comprehensive Coverage**: All 21 operations have versioning

This versioning system ensures clear tracking of changes, better maintenance visibility, and improved debugging capabilities for the AWS Inventory CLI tool! 🚀