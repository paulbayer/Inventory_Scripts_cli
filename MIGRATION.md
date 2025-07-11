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
| `all_my_subnets.py`                | `inv_scr subnets`        | ✅ Fully implemented |
| `all_my_phzs.py`                   | `inv_scr phzs`           | ✅ Fully implemented |
| `all_my_enis.py`                   | `inv_scr enis`           | ✅ Fully implemented |
| `all_my_ecs_clusters_and_tasks.py` | `inv_scr ecs-clusters`   | ✅ Fully implemented |
| `all_my_directories.py`            | `inv_scr directories`    | ✅ Fully implemented |
| `all_my_gas.py`                    | `inv_scr gas`            | ✅ Fully implemented |
| `all_my_gd-detectors.py`           | `inv_scr gd-detectors`   | ✅ Fully implemented |
| `all_my_policies.py`               | `inv_scr policies`       | ✅ Fully implemented |
| `all_my_roles.py`                  | `inv_scr roles`          | ✅ Fully implemented |
| `all_my_saml_providers.py`         | `inv_scr saml-providers` | ✅ Fully implemented |
| `all_my_tgws.py`                   | `inv_scr tgws`           | ✅ Fully implemented |
| `all_my_topics.py`                 | `inv_scr topics`         | ✅ Fully implemented |

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

### VPC Subnets

**Old way:**

```bash
python all_my_subnets.py --profiles prod dev --regions us-east-1 --ipaddress 10.0.1.100
```

**New way:**

```bash
inv_scr subnets --profiles prod dev --regions us-east-1 --ipaddress 10.0.1.100
```

### Private Hosted Zones

**Old way:**

```bash
python all_my_phzs.py --profiles all
```

**New way:**

```bash
inv_scr phzs --profiles all
```

### Elastic Network Interfaces

**Old way:**

```bash
python all_my_enis.py --profiles prod --regions us-east-1 --public-only
```

**New way:**

```bash
inv_scr enis --profiles prod --regions us-east-1 --public-only
```

### ECS Clusters

**Old way:**

```bash
python all_my_ecs_clusters_and_tasks.py --profiles prod --regions us-east-1 --status running
```

**New way:**

```bash
inv_scr ecs-clusters --profiles prod --regions us-east-1 --status running
```

### AWS Directory Service

**Old way:**

```bash
python all_my_directories.py --profiles all --regions us-east-1 --fragment MyDirectory
```

**New way:**

```bash
inv_scr directories --profiles all --regions us-east-1 --fragment MyDirectory
```

### Global Accelerator

**Old way:**

```bash
python all_my_gas.py --profiles prod --status DEPLOYED
```

**New way:**

```bash
inv_scr gas --profiles prod --status DEPLOYED
```

### GuardDuty Detectors

**Old way:**

```bash
python all_my_gd-detectors.py --profiles all --regions us-east-1
```

**New way:**

```bash
inv_scr gd-detectors --profiles all --regions us-east-1
```

### IAM Policies

**Old way:**

```bash
python all_my_policies.py --profiles prod --fragment S3 --action s3:GetObject
```

**New way:**

```bash
inv_scr policies --profiles prod --fragment S3 --action s3:GetObject
```

### IAM Roles

**Old way:**

```bash
python all_my_roles.py --profiles all --fragment Lambda --exact
```

**New way:**

```bash
inv_scr roles --profiles all --fragment Lambda --exact
```

### SAML Providers

**Old way:**

```bash
python all_my_saml_providers.py --profiles prod --regions us-east-1
```

**New way:**

```bash
inv_scr saml-providers --profiles prod --regions us-east-1
```

### Transit Gateways

**Old way:**

```bash
python all_my_tgws.py --profiles all --regions us-east-1 --type tgw --diagram
```

**New way:**

```bash
inv_scr tgws --profiles all --regions us-east-1 --type tgw --diagram
```

### SNS Topics

**Old way:**

```bash
python all_my_topics.py --profiles prod --regions us-east-1 --fragment alerts
```

**New way:**

```bash
inv_scr topics --profiles prod --regions us-east-1 --fragment alerts
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

### ✅ Fully Implemented (21 operations - 100% complete)

**Core Infrastructure:**
- **instances**: Complete EC2 instance inventory with all original features
- **vpcs**: Complete VPC inventory with all original features
- **subnets**: Complete VPC subnets inventory with IP filtering
- **enis**: Complete Elastic Network Interfaces inventory with IP and public-only filtering
- **elbs**: Complete Elastic Load Balancers inventory
- **tgws**: Complete Transit Gateways inventory with VPC and attachment discovery

**Compute & Containers:**
- **functions**: Complete Lambda functions inventory
- **ecs-clusters**: Complete ECS clusters, services and tasks inventory

**Storage:**
- **ebs-volumes**: Complete EBS volumes inventory

**CloudFormation:**
- **cfnstacks**: Complete CloudFormation stacks inventory
- **cfnstacksets**: Complete CloudFormation StackSets inventory

**Identity & Access Management:**
- **roles**: Complete IAM roles inventory with fragment filtering
- **policies**: Complete IAM policies inventory with action searching
- **saml-providers**: Complete SAML providers inventory

**Security:**
- **gd-detectors**: Complete GuardDuty detectors inventory

**Networking & Content Delivery:**
- **gas**: Complete Global Accelerator inventory

**Directory Services:**
- **directories**: Complete AWS Directory Service inventory

**DNS:**
- **phzs**: Complete Private Hosted Zones inventory

**Messaging:**
- **topics**: Complete SNS topics inventory

**Organizations:**
- **orgs**: Complete AWS Organizations inventory

## 🎉 Migration Complete!

All 21 operations have been successfully migrated from individual scripts to the unified CLI architecture. Every operation maintains 100% feature parity with the original scripts while benefiting from:

- Consistent argument parsing and validation
- Unified credential management
- Standardized progress indicators
- Enhanced error handling and logging
- Consistent output formatting
- Built-in timing and performance metrics

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
