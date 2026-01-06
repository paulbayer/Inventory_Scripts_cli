#!/usr/bin/env python3
"""
Install tab completion for inv_scr CLI
"""

import os
import sys
import subprocess
from pathlib import Path


def install_argcomplete():
    """Install argcomplete global completion"""
    try:
        # Check if argcomplete is installed
        import argcomplete
        print("✓ argcomplete is installed")
        
        # Try to activate global completion
        try:
            result = subprocess.run(['activate-global-python-argcomplete'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ Global argcomplete activation successful")
                return True
            else:
                print("⚠ Global argcomplete activation failed, trying user-level...")
                
                # Try user-level activation
                result = subprocess.run(['activate-global-python-argcomplete', '--user'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✓ User-level argcomplete activation successful")
                    return True
                else:
                    print("✗ Argcomplete activation failed")
                    return False
                    
        except FileNotFoundError:
            print("⚠ activate-global-python-argcomplete not found in PATH")
            return False
            
    except ImportError:
        print("✗ argcomplete not installed. Install with: pip install argcomplete")
        return False


def install_bash_completion():
    """Install bash completion script"""
    script_dir = Path(__file__).parent
    completion_script = script_dir / "completion" / "inv_scr_completion.bash"
    
    if not completion_script.exists():
        print(f"✗ Completion script not found: {completion_script}")
        return False
    
    # Try different completion directories
    completion_dirs = [
        Path.home() / ".bash_completion.d",
        Path("/usr/local/etc/bash_completion.d"),
        Path("/etc/bash_completion.d"),
    ]
    
    for comp_dir in completion_dirs:
        if comp_dir.exists() and os.access(comp_dir, os.W_OK):
            target = comp_dir / "inv_scr_completion.bash"
            try:
                import shutil
                shutil.copy2(completion_script, target)
                print(f"✓ Bash completion installed to {target}")
                return True
            except PermissionError:
                continue
    
    # Fallback: suggest manual installation
    print("⚠ Could not install to system completion directory")
    print(f"Manual installation: source {completion_script} in your ~/.bashrc")
    return False


def main():
    """Main installation function"""
    print("Installing tab completion for inv_scr CLI...")
    print("=" * 50)
    
    argcomplete_ok = install_argcomplete()
    bash_ok = install_bash_completion()
    
    print("\nInstallation Summary:")
    print("=" * 20)
    
    if argcomplete_ok:
        print("✓ Python argcomplete: Ready")
        print("  Tab completion will work automatically for:")
        print("  - Operations (instances, vpcs, etc.)")
        print("  - AWS profiles from ~/.aws/config")
        print("  - AWS regions")
    else:
        print("✗ Python argcomplete: Failed")
        print("  Install with: pip install argcomplete")
        print("  Then run: activate-global-python-argcomplete")
    
    if bash_ok:
        print("✓ Bash completion: Installed")
    else:
        print("⚠ Bash completion: Manual setup needed")
        script_path = Path(__file__).parent / "completion" / "inv_scr_completion.bash"
        print(f"  Add to ~/.bashrc: source {script_path}")
    
    print("\nTo test completion:")
    print("  1. Start a new shell or run: source ~/.bashrc")
    print("  2. Type: inv_scr <TAB>")
    print("  3. You should see available operations")


if __name__ == "__main__":
    main()