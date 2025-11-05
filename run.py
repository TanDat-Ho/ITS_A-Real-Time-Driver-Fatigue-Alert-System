#!/usr/bin/env python3
"""
Backward compatibility wrapper for run.py
This file redirects all calls to launcher.py to maintain compatibility
with existing documentation and scripts.
"""

import sys
import subprocess
import os

def main():
    """Redirect all calls to launcher.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    launcher_path = os.path.join(script_dir, "launcher.py")
    
    if not os.path.exists(launcher_path):
        print("❌ Error: launcher.py not found!")
        sys.exit(1)
    
    # Pass all arguments to launcher.py
    args = [sys.executable, launcher_path] + sys.argv[1:]
    
    try:
        # Run launcher.py with the same arguments
        result = subprocess.run(args, check=False)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Error running launcher: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()