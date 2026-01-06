# Tab Completion Troubleshooting Guide

## Overview
The `inv_scr` CLI supports tab completion for operations, AWS profiles, and regions through two methods:
1. **Python argcomplete** (recommended) - Dynamic completion with AWS API integration
2. **Bash completion script** - Static completion as fallback

## Installation

### Quick Setup
```bash
# Install with completion support
make install-completion

# Or manually
python3 install_completion.py
```

### Manual Setup
```bash
# 1. Install argcomplete
pip install argcomplete

# 2. Activate global completion
activate-global-python-argcomplete

# 3. Restart shell or source bashrc
source ~/.bashrc
```

## Common Issues and Fixes

### Issue 1: "argcomplete not found"
**Symptoms:** Completion doesn't work, no error messages
**Solution:**
```bash
pip install argcomplete
activate-global-python-argcomplete --user
```

### Issue 2: "activate-global-python-argcomplete command not found"
**Symptoms:** Installation script reports activation failed
**Solution:**
```bash
# Find where argcomplete was installed
python3 -c "import argcomplete; print(argcomplete.__file__)"

# Add to PATH or use full path
~/.local/bin/activate-global-python-argcomplete --user
```

### Issue 3: Completion works but no AWS profiles/regions
**Symptoms:** Operations complete but `--profiles <TAB>` shows nothing
**Solution:**
- Ensure AWS CLI is configured: `aws configure list-profiles`
- Check AWS credentials: `aws sts get-caller-identity`
- Verify boto3 can access profiles: `python3 -c "import boto3; print(boto3.Session().available_profiles)"`

### Issue 4: CLI broken after adding completion
**Symptoms:** `inv_scr` command fails to run
**Solution:**
The completion integration is designed to fail gracefully. If issues persist:
```bash
# Test CLI without completion
python3 -c "
import sys
sys.argv = ['inv_scr', 'list']
from inv_scr.cli import main
main()
"
```

### Issue 5: Bash completion not working
**Symptoms:** Tab completion doesn't work in bash
**Solution:**
```bash
# Manual bash completion setup
source completion/inv_scr_completion.bash

# Or add to ~/.bashrc
echo "source $(pwd)/completion/inv_scr_completion.bash" >> ~/.bashrc
```

## Testing Completion

### Test Basic Functionality
```bash
# Test operation completion
inv_scr <TAB>
# Should show: azs cfnstacks cfnstacksets cloudtrail ...

# Test profile completion (if AWS configured)
inv_scr instances --profiles <TAB>
# Should show your AWS profiles

# Test region completion
inv_scr vpcs --regions <TAB>
# Should show AWS regions + 'all'
```

### Test with Python
```bash
# Run completion tests
python3 tests/test_completion.py

# Run minimal integration test
python3 test_completion_minimal.py
```

## Verification Commands

### Check Installation Status
```bash
# Check if argcomplete is installed
python3 -c "import argcomplete; print('argcomplete available')"

# Check if completion module loads
python3 -c "from inv_scr.completion import setup_completion; print('completion module OK')"

# Check CLI still works
inv_scr list
```

### Debug Completion
```bash
# Enable argcomplete debug mode
export _ARC_DEBUG=1
inv_scr <TAB>

# Check bash completion manually
source completion/inv_scr_completion.bash
complete -p inv_scr
```

## Fallback Options

If argcomplete doesn't work, you can still use basic bash completion:

### Option 1: Source completion script
```bash
source completion/inv_scr_completion.bash
```

### Option 2: Manual aliases
```bash
# Add to ~/.bashrc
alias inv_scr_instances="inv_scr instances"
alias inv_scr_vpcs="inv_scr vpcs"
alias inv_scr_list="inv_scr list"
```

### Option 3: Use help commands
```bash
# List operations
inv_scr list

# Get operation-specific help
inv_scr instances --help
```

## Uninstalling Completion

If completion causes issues, you can disable it:

```bash
# Remove from bashrc
sed -i '/inv_scr_completion/d' ~/.bashrc

# Remove global argcomplete (if needed)
# This affects all Python tools using argcomplete
activate-global-python-argcomplete --dest=- > /dev/null
```

## Support

If completion issues persist:
1. Run `python3 test_completion_minimal.py` and share output
2. Check that basic CLI works: `inv_scr list`
3. Verify your shell: `echo $SHELL`
4. Check Python/pip versions: `python3 --version && pip3 --version`