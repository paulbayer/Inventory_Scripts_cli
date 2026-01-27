# CloudFormation StackSets Operation Enhancement Prompt

## Objective
Enhance the `inv_scr/operations/cfnstacksets.py` operation to include the modification capabilities from the legacy `mod_my_cfnstacksets.py` script, while maintaining the modern architecture and coding standards of the current codebase.

## Current State Analysis

### Existing Functionality (cfnstacksets.py)
The current operation provides **read-only** inventory capabilities:
- Lists CloudFormation StackSets across accounts and regions
- Filters by stackset name fragments (exact or contains matching)
- Filters by status (ACTIVE/DELETED)
- Optionally displays instance counts per stackset
- Uses modern argument parsing and display framework
- Integrates with timing context and standard display utilities

### Legacy Functionality (mod_my_cfnstacksets.py)
The legacy script provides **modification** capabilities:
1. **Delete Operations** (`+delete` flag):
   - Remove stack instances from stacksets
   - Support for both SELF_MANAGED and SERVICE_MANAGED permission models
   - Option to retain stacks in child accounts (`--retain` flag)
   - Automatic stackset deletion when all instances are removed
   - Force deletion option for stuck operations
   - Handles empty stacksets

2. **Add Operations** (`+add` flag):
   - Add new stack instances to existing stacksets
   - Specify accounts and/or regions to add
   - Parallel region deployment with configurable preferences

3. **Refresh Operations** (`+refresh` flag):
   - Re-run existing stacksets with current configuration
   - Uses `UsePreviousTemplate=True` to maintain template
   - Shows drift detection status before refresh
   - Handles both SELF_MANAGED and SERVICE_MANAGED models

4. **Account Validation** (`-check` flag):
   - Compare stackset accounts against Organization accounts
   - Identify closed/suspended accounts still in stacksets
   - Identify inaccessible accounts (role access failures)
   - Highlight orphaned accounts in output

5. **Region Modification** (`-R` flag):
   - Specify regions to add/remove from stacksets
   - Works in conjunction with add/delete operations

6. **Operation Monitoring**:
   - Track stackset operation status in real-time
   - Wait for operations to complete before proceeding
   - Display detailed operation results
   - Show drift status and last operation dates

7. **Enhanced Display**:
   - Detailed status for each stack instance
   - Account-by-region breakdown
   - Highlight problematic instances (non-CURRENT status)
   - Show permission model (SELF_MANAGED vs SERVICE_MANAGED)
   - Optional operation date display (`--date` flag)

## Implementation Requirements

### 1. Argument Additions
Add the following arguments to `add_operation_args()`:

**Important:** The `parser` parameter passed to `add_operation_args()` is a `CommonArguments` instance that already has helper methods like `confirm()`. You should call `parser.confirm()` to add the `+confirm` flag.

```python
def add_operation_args(parser):
    """Add operation-specific arguments"""
    local = parser.my_parser.add_argument_group('cfnstacksets', 'CloudFormation StackSets specific options')
    
    # Existing arguments remain...
    local.add_argument(
        "-f", "--fragment",
        dest="pFragments",
        nargs='*',
        metavar="string fragment",
        default=["all"],
        help="List of fragments of the stackset name(s) you want to check for."
    )
    # ... (keep existing arguments)
    
    # Add the confirm flag using the CommonArguments helper
    parser.confirm()
    
    # Operation mode (mutually exclusive)
    operation_group = local.add_mutually_exclusive_group()
operation_group.add_argument(
    "+delete", "+remove",
    help="Delete stack instances from stacksets",
    action="store_true",
    dest="pDelete"
)
operation_group.add_argument(
    "+add",
    help="Add stack instances to stacksets",
    action="store_true",
    dest="pAdd"
)
operation_group.add_argument(
    "+refresh",
    help="Refresh stacksets with current configuration",
    action="store_true",
    dest="pRefresh"
)

# Modification options
local.add_argument(
    "+R", "+modreg", "+modregion",
    help="Region(s) to add or remove from stacksets",
    nargs="*",
    metavar="region-name",
    dest="pModifyRegions"
)
local.add_argument(
    "+A", "+modacc", "+modacct", "+addacct", "+ModifyAccount",
    help="Account(s) to add or remove from stacksets",
    nargs="*",
    metavar="account-id",
    dest="pModifyAccounts"
)
local.add_argument(
    "--retain", "--disassociate",
    help="Retain stacks in child accounts when removing instances (requires +delete)",
    action="store_true",
    dest="pRetain"
)
local.add_argument(
    "-c", "--check",
    help="Check for closed/suspended accounts in stacksets",
    action="store_true",
    dest="pCheckAccounts"
)
local.add_argument(
    "--date",
    help="Include last operation date in detailed output",
    action="store_true",
    dest="pShowDate"
)

# Note: The +confirm flag is already available via parser.confirm() from ArgumentsClass
# It should be called in add_operation_args() if not already available globally
```

### 2. New Helper Functions to Add

#### a. `check_accounts_in_org()`
```python
def check_accounts_in_org(fCredentials: dict, fAccountList: list) -> dict:
    """
    Compare stackset accounts against Organization accounts
    Returns dict with:
    - RemovedAccounts: accounts not in org
    - InaccessibleAccounts: accounts that can't be accessed
    """
```

#### b. `delete_stack_instances()`
```python
def delete_stack_instances(fCredentials: dict, fRegion: str, fStackSetName: str, 
                          fRetain: bool, fAccountList: list, fRegionList: list,
                          fPermissionModel: str = 'SELF_MANAGED', 
                          fDeploymentTargets: dict = None) -> dict:
    """
    Delete stack instances from a stackset
    Handles both SELF_MANAGED and SERVICE_MANAGED permission models
    Returns dict with Success status and OperationId
    """
```

#### c. `add_stack_instances()`
```python
def add_stack_instances(fCredentials: dict, fRegion: str, fStackSetName: str,
                       fAccountList: list, fRegionList: list) -> dict:
    """
    Add stack instances to a stackset
    Returns dict with Success status and OperationId
    """
```

#### d. `refresh_stackset()`
```python
def refresh_stackset(fCredentials: dict, fRegion: str, fStackSetName: str,
                    fPermissionModel: str) -> dict:
    """
    Refresh a stackset with current configuration
    Uses UsePreviousTemplate=True
    Returns dict with Success status and OperationId
    """
```

#### e. `monitor_stackset_operations()`
```python
def monitor_stackset_operations(fCredentials: dict, fOperationsList: list,
                               fSleepInterval: int = 5) -> dict:
    """
    Monitor stackset operations until completion
    Returns dict mapping StackSetName to final status
    """
```

#### f. `get_deployment_targets()`
```python
def get_deployment_targets(fCredentials: dict, fRegion: str, fStackSetName: str,
                          fAccountList: list = None) -> dict:
    """
    Get deployment target information for SERVICE_MANAGED stacksets
    Returns dict with OrganizationalUnitIds or Accounts
    """
```

### 3. Enhanced Display Function

Create `display_stackset_health()` to replace/enhance current display:
```python
def display_stackset_health(fStackSets: list, fShowDetails: bool = False,
                           fRemovedAccounts: list = None, 
                           fInaccessibleAccounts: list = None,
                           fShowDate: bool = False) -> None:
    """
    Display comprehensive stackset health information
    - Group by stackset name
    - Show status counts (CURRENT, OUTDATED, etc.)
    - Highlight orphaned accounts
    - Show account-by-region breakdown
    - Display permission model
    - Optional: show last operation dates
    """
```

### 4. Main Execution Flow Updates

Modify `run()` function to:
1. Parse new arguments
2. Determine operation mode (list/delete/add/refresh)
3. For modification operations:
   - Validate required parameters
   - Prompt for confirmation (unless `--confirm` flag)
   - Execute operation
   - Monitor operation status
   - Refresh view after changes
   - Display updated health
4. For account checking:
   - Call `check_accounts_in_org()`
   - Highlight results in display
5. Use enhanced display for all modes

### 5. Integration with Inventory_Modules

Ensure these functions from `Inventory_Modules` are available:
- `find_stacksets2()` - already used
- `find_stack_instances2()` - already used
- `delete_stack_instances3()` - needs to be called
- `delete_stackset3()` - needs to be called
- `check_stack_set_status3()` - needs to be called
- `random_string()` - for operation IDs

### 6. Error Handling

Implement robust error handling for:
- `OperationInProgressException` - another operation running
- `StackSetNotFoundException` - stackset doesn't exist
- `AuthFailure` - credential issues
- Force deletion retry logic for stuck operations
- Empty stackset handling

### 7. Confirmation Prompts

Add confirmation prompts for destructive operations (unless `args.Confirm` is True):
- Before deleting instances
- Before refreshing stacksets
- Option to force deletion if initial attempt fails

Access the confirm flag via `args.Confirm` (set by `parser.confirm()` call).

### 8. Output Enhancements

Enhance output to show:
- Operation progress with progress bars (using tqdm)
- Real-time status updates during operations
- Detailed instance status (CURRENT, OUTDATED, FAILED, etc.)
- Permission model for each stackset
- Drift detection status (for refresh operations)
- Orphaned accounts highlighted in color
- Operation timing information

## Testing Considerations

After implementation, test:
1. **Read-only operations** (ensure backward compatibility)
2. **Delete operations**:
   - SELF_MANAGED stacksets
   - SERVICE_MANAGED stacksets
   - With --retain flag
   - Empty stacksets
   - Force deletion
3. **Add operations**:
   - Adding accounts
   - Adding regions
   - Adding both
4. **Refresh operations**:
   - SELF_MANAGED stacksets
   - SERVICE_MANAGED stacksets
5. **Account checking**:
   - Identify removed accounts
   - Identify inaccessible accounts
6. **Error scenarios**:
   - Operations in progress
   - Invalid parameters
   - Permission issues

## Code Style Requirements

Follow repository guidelines:
- Use 4-space indentation
- Type hints for function parameters
- Descriptive variable names (snake_case)
- Comprehensive docstrings
- Logging at appropriate levels
- Use colorama for colored output (Fore.RED, etc.)
- Maintain compatibility with timing context
- Use existing display_results() framework where appropriate

## Version Update

Update `__version__` to reflect the enhancement (e.g., "2026.01.20")

## Documentation

Update operation help text to reflect new capabilities:
- Describe all operation modes
- Provide examples for common use cases
- Document permission model differences
- Explain --retain vs full deletion

## Migration Notes

This enhancement maintains backward compatibility:
- Existing read-only usage remains unchanged
- New flags are optional and mutually exclusive
- Default behavior (no operation flags) is list-only
- All existing arguments continue to work as before

## Success Criteria

Implementation is complete when:
1. All legacy modification capabilities are available
2. Backward compatibility is maintained
3. Code follows repository style guidelines
4. Error handling is comprehensive
5. Output is clear and informative
6. Operations can be monitored in real-time
7. Account validation works correctly
8. Both permission models are supported
