# Migration Guide: From Individual Scripts to Unified CLI

This guide helps you migrate from using individual inventory scripts to the new unified AWS Inventory CLI.

## Quick Reference

| Old Script                         | New Command              | Notes                |
| ---------------------------------- | ------------------------ | -------------------- |
| `all_my_instances.py`              | `inv_scr instances`      | ✅ Fully implemented |
| `all_my_vpcs.py`                   | `inv_scr vpcs`           | ✅ Fully implemented |
| `all_my_cfnstacks.py`              | `inv_scr cfnstacks`      | ✅ Fully implemented |
| `all_my_cfnstacksets.py`           | `inv_scr cfnstacksets`   | ✅ Fully implemented |
| `all_my_ebs_volumes.py`            | `inv_scr ebs-volumes`    | ✅ Fully implemented |
| `all_my_elbs.py`                   | `inv_scr elbs`           | ✅ Fully implemented |
| `all_my_functions.py`              | `inv_scr functions`      | ✅ Fully implemented |
| `all_my_orgs.py`                   | `inv_scr orgs`           | ✅ Fully implemented |
| `all_my_rds_instances.py`          | `inv_scr rds-instances`  | ✅ Fully implemented |
| `all_my_directories.py`            | `inv_scr directories`    | 🚧 Coming soon       |
| `all_my_ecs_clusters_and_tasks.py` | `inv_scr ecs-clusters`   | 🚧 Coming soon       |
| `all_my_enis.py`                   | `inv_scr enis`           | 🚧 Coming soon       |
| `all_my_gas.py`                    | `inv_scr gas`            | 🚧 Coming soon       |
| `all_my_gd-detectors.py`           | `inv_scr gd-detectors`   | 🚧 Coming soon       |
| `all_my_phzs.py`                   | `inv_scr phzs`           | 🚧 Coming soon       |
| `all_my_policies.py`               | `inv_scr policies`       | 🚧 Coming soon       |
| `all_my_roles.py`                  | `inv_scr roles`          | 🚧 Coming soon       |
| `all_my_saml_providers.py`         | `inv_scr saml-providers` | 🚧 Coming soon       |
| `all_my_subnets.py`                | `inv_scr subnets`        | 🚧 Coming soon       |
| `all_my_tgws.py`                   | `inv_scr tgws`           | 🚧 Coming soon       |
| `all_my_topics.py`                 | `inv_scr topics`         | 🚧 Coming soon       |

## Migration Examples

### EC2 Instances

**Old way:**

```bash
python all_my_instances.py --profiles prod dev --regions us-east-1 --status running
```

**New way:**

```bash
inv_scr instances --profiles prod dev --regions us-east-1 --status running
```

### VPCs

**Old way:**

```bash
python all_my_vpcs.py --profiles all --regions all --default
```

**New way:**

```bash
inv_scr vpcs --profiles all --regions all --default
```

## Benefits of Migration

### 1. Shared Components

- Common argument parsing
- Consistent credential management
- Unified output formatting
- Shared error handling

### 2. Easier Maintenance

- Single codebase to maintain
- Consistent updates across all operations
- Centralized configuration

### 3. Better User Experience

- Single command to remember (`inv_scr`)
- Consistent interface across all operations
- Built-in help system
- Operation discovery with `inv_scr list`

### 4. Enhanced Features

- Better progress indicators
- Consistent timing and performance metrics
- Standardized file output
- Improved error messages

## Implementation Status

### ✅ Fully Implemented (9 operations - 41% complete)

- **instances**: Complete EC2 instance inventory with all original features
- **vpcs**: Complete VPC inventory with all original features
- **cfnstacks**: Complete CloudFormation stacks inventory
- **cfnstacksets**: Complete CloudFormation StackSets inventory
- **ebs-volumes**: Complete EBS volumes inventory
- **elbs**: Complete Elastic Load Balancers inventory
- **functions**: Complete Lambda functions inventory
- **orgs**: Complete AWS Organizations inventory
- **rds-instances**: Complete RDS instances inventory

### 🚧 Coming Soon (12 operations remaining)

The following operations are currently placeholders that show a "coming soon" message. They will be implemented with the same functionality as the original scripts, plus the benefits of the unified architecture:

- **directories**: AWS Directory Service inventory
- **ecs-clusters**: ECS clusters and tasks inventory
- **enis**: Elastic Network Interfaces inventory
- **gas**: Global Accelerator inventory
- **gd-detectors**: GuardDuty detectors inventory
- **phzs**: Private Hosted Zones inventory
- **policies**: IAM policies inventory
- **roles**: IAM roles inventory
- **saml-providers**: SAML providers inventory
- **subnets**: VPC subnets inventory
- **tgws**: Transit Gateways inventory
- **topics**: SNS topics inventory

## Backward Compatibility

The original individual scripts in the `inv_scr/functions/` directory are still available and functional. You can continue using them while migrating to the new unified CLI.

However, we recommend migrating to the new CLI as:

1. New features will only be added to the unified CLI
2. Bug fixes will be prioritized for the unified CLI
3. The individual scripts may be deprecated in future versions

## Migration Strategy

### Phase 1: Parallel Usage

- Install the new unified CLI
- Test it alongside your existing scripts
- Gradually replace script usage with CLI commands

### Phase 2: Full Migration

- Update any automation or scripts to use the new CLI
- Remove dependencies on individual scripts
- Take advantage of new unified features

### Phase 3: Cleanup

- Remove old individual scripts from your workflows
- Update documentation and runbooks
- Train team members on the new CLI

## Getting Help

### Command Help

```bash
# General help
inv_scr --help

# Operation-specific help
inv_scr instances --help
inv_scr vpcs --help

# List all operations
inv_scr list
```

### Common Issues

**Q: My old script arguments don't work**
A: Most arguments are the same, but check the help for any operation-specific changes.

**Q: The output format looks different**
A: The new CLI uses a consistent output format. Use `--filename` to save to file if needed.

**Q: Performance seems different**
A: The new CLI uses optimized threading and credential management. Use `--timing` to compare performance.

**Q: I need a feature that's not implemented yet**
A: Continue using the original script until the operation is fully implemented, or contribute to the implementation.

## Contributing

If you'd like to help implement the remaining operations:

1. Look at the implemented operations (`instances.py`, `vpcs.py`) as examples
2. Copy the pattern from the original script in `inv_scr/functions/`
3. Adapt it to the new operation structure
4. Test thoroughly
5. Submit a pull request

The goal is to maintain 100% feature parity with the original scripts while gaining the benefits of the unified architecture.
