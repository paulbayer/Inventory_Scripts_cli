# CloudFormation StackSets Operation - Usage Guide

## Quick Reference

### Read-Only Operations

```bash
# List all active stacksets
inv_scr cfnstacksets

# List stacksets matching a fragment
inv_scr cfnstacksets -f MyStackSet

# List with exact match
inv_scr cfnstacksets -f MyStackSet -e

# Show instance counts
inv_scr cfnstacksets -f MyStackSet -i

# Check for orphaned accounts
inv_scr cfnstacksets -f MyStackSet -c

# Show deleted stacksets
inv_scr cfnstacksets -f MyStackSet -s DELETED
```

### Modification Operations

#### Delete Instances
```bash
# Delete all instances (with confirmation)
inv_scr cfnstacksets -f MyStackSet +delete

# Delete without confirmation
inv_scr cfnstacksets -f MyStackSet +delete +confirm

# Delete specific accounts
inv_scr cfnstacksets -f MyStackSet +delete +A 123456789012 234567890123

# Delete specific regions
inv_scr cfnstacksets -f MyStackSet +delete +R us-east-1 us-west-2

# Delete specific accounts in specific regions
inv_scr cfnstacksets -f MyStackSet +delete +A 123456789012 +R us-east-1

# Delete but retain stacks in child accounts
inv_scr cfnstacksets -f MyStackSet +delete --retain +confirm
```

#### Add Instances
```bash
# Add accounts to all regions
inv_scr cfnstacksets -f MyStackSet +add +A 123456789012

# Add regions to all accounts
inv_scr cfnstacksets -f MyStackSet +add +R eu-west-1 eu-central-1

# Add specific accounts to specific regions
inv_scr cfnstacksets -f MyStackSet +add +A 123456789012 +R us-east-1 us-west-2
```

#### Refresh Stacksets
```bash
# Refresh with current configuration
inv_scr cfnstacksets -f MyStackSet +refresh

# Refresh multiple stacksets
inv_scr cfnstacksets -f MyStack +refresh
```

## Parameter Reference

### Read-Only Parameters (-)

| Parameter | Aliases | Description |
|-----------|---------|-------------|
| `-f` | `--fragment` | Stackset name fragment(s) to match |
| `-e` | `--exact` | Use exact match instead of contains |
| `-s` | `--status` | Filter by status (ACTIVE/DELETED) |
| `-i` | `--instances` | Show instance counts |
| `-c` | `--check` | Check for orphaned accounts |
| `--date` | | Show last operation date |

### Modification Parameters (+)

| Parameter | Aliases | Description |
|-----------|---------|-------------|
| `+delete` | `+remove` | Delete stack instances |
| `+add` | | Add stack instances |
| `+refresh` | | Refresh stacksets |
| `+R` | `+modreg`, `+modregion` | Target region(s) |
| `+A` | `+modacc`, `+modacct`, `+addacct` | Target account(s) |
| `+confirm` | | Skip confirmation prompts |
| `--retain` | `--disassociate` | Retain stacks when deleting |

## Common Workflows

### 1. Audit Stacksets
```bash
# Find all stacksets and check for orphaned accounts
inv_scr cfnstacksets -f all -c -i
```

### 2. Remove Closed Account
```bash
# First, check which stacksets contain the account
inv_scr cfnstacksets -c

# Then remove it from specific stacksets
inv_scr cfnstacksets -f MyStackSet +delete +A 123456789012 +confirm
```

### 3. Add New Account to Existing Stacksets
```bash
# Add account to all regions in stackset
inv_scr cfnstacksets -f MyStackSet +add +A 987654321098
```

### 4. Expand to New Region
```bash
# Add new region to all accounts in stackset
inv_scr cfnstacksets -f MyStackSet +add +R ap-southeast-1
```

### 5. Clean Up Empty Stacksets
```bash
# List stacksets with instance counts
inv_scr cfnstacksets -i

# Delete empty stacksets (they'll be removed automatically after instance deletion)
inv_scr cfnstacksets -f EmptyStackSet +delete +confirm
```

### 6. Refresh After Template Update
```bash
# After updating stackset template, refresh all instances
inv_scr cfnstacksets -f MyStackSet +refresh
```

## Permission Models

### SELF_MANAGED
- Requires explicit account and region lists
- Uses AdministrationRoleARN
- Direct account targeting

### SERVICE_MANAGED
- Uses Organizational Units (OUs)
- Automatically discovers deployment targets
- No AdministrationRoleARN needed

The operation automatically detects and handles both models.

## Output Interpretation

### Read-Only Mode
Standard table format showing:
- Parent Profile
- Management Account
- Account Number
- Region
- Status
- StackSet Name
- Instance Count (if `-i` specified)

### Modification Mode
Enhanced health display showing:
- Stackset name with permission model
- Status breakdown (CURRENT, OUTDATED, etc.)
- Account-by-region grouping
- Orphaned accounts highlighted in MAGENTA
- Detailed status for non-CURRENT instances

### Operation Results
- ✓ (GREEN) - Operation succeeded
- ✗ (RED) - Operation failed
- Status: SUCCEEDED, FAILED, RUNNING, etc.

## Best Practices

1. **Always check first**: Run read-only command before modifications
2. **Use fragments carefully**: Be specific to avoid unintended changes
3. **Test with one stackset**: Verify behavior before bulk operations
4. **Monitor operations**: Watch for completion before next steps
5. **Check orphaned accounts**: Use `-c` regularly to identify cleanup needs
6. **Use `+confirm` in scripts**: For automation, skip interactive prompts
7. **Retain when unsure**: Use `--retain` to keep stacks for manual cleanup

## Troubleshooting

### "No stacksets found"
- Check fragment spelling
- Verify status filter (ACTIVE vs DELETED)
- Ensure you have access to the management account

### "Operation in progress"
- Another operation is running on the stackset
- Wait for completion or check AWS Console
- Use `--timing` to see how long operations take

### "Must specify accounts or regions"
- For `+add`, you must specify what to add
- Use `+A` for accounts or `+R` for regions

### "Permission denied"
- Ensure you have CloudFormation permissions
- Check IAM roles for stackset operations
- Verify cross-account role access

## Safety Features

1. **Confirmation prompts**: Interactive confirmation for destructive operations
2. **Operation monitoring**: Real-time status updates
3. **Detailed logging**: Use `-vvv` for debug information
4. **Dry-run equivalent**: Run read-only first to see what would be affected
5. **Retain option**: Keep stacks in child accounts when deleting instances

## Examples with Multiple Profiles

```bash
# Check stacksets across multiple profiles
inv_scr cfnstacksets -p prod-profile dev-profile -f MyStackSet

# Delete from specific profile
inv_scr cfnstacksets -p prod-profile -f MyStackSet +delete +A 123456789012
```

## Integration with Other Tools

```bash
# Export to file for analysis
inv_scr cfnstacksets -f all -i --filename stacksets.csv

# Use with timing for performance analysis
inv_scr cfnstacksets -f MyStackSet --timing

# Combine with account filtering
inv_scr cfnstacksets -f MyStackSet -a 123456789012 234567890123
```
