#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Legacy Test Script Cleanup Utility

This script cleans up legacy test scripts that have been replaced
by the new unified test runner. It moves them to an archive directory
rather than deleting them immediately, in case they need to be referenced.

Usage:
    python -m backend.scripts.cleanup_legacy_tests
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


def clean_legacy_test_scripts():
    """Clean up legacy test scripts that are now redundant."""
    # Get the base directory
    base_dir = Path(__file__).resolve().parent
    scripts_dir = base_dir
    tests_script_dir = scripts_dir / "tests"
    
    # Create an archive directory
    archive_dir = scripts_dir / "legacy_archive"
    archive_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_archive = archive_dir / f"legacy_tests_{timestamp}"
    current_archive.mkdir(exist_ok=True)
    
    # List of legacy test scripts to archive
    legacy_scripts = [
        # Test runners in scripts/tests
        tests_script_dir / "generate_test_files.py",
        tests_script_dir / "run_comprehensive_test.py",
        tests_script_dir / "run_coverage_check.py",
        tests_script_dir / "run_enhanced_test_v2.py",
        tests_script_dir / "run_enhanced_test.py",
        tests_script_dir / "run_final_test.py",
        tests_script_dir / "run_hipaa_test_coverage.py",
        tests_script_dir / "run_project_cleanup_and_check.py",
        tests_script_dir / "run_test_directly.py",
        tests_script_dir / "run_test_fixed.py",
        tests_script_dir / "run_ultimate_test.py",
        
        # Scripts in the main scripts directory
        scripts_dir / "run_ml_mock_tests.py",
        scripts_dir / "run_hipaa_security_suite.py",
        scripts_dir / "run_temporal_neurotransmitter_service.py",
        scripts_dir / "unified_hipaa_security_suite.py",
    ]
    
    print(f"Archiving legacy test scripts to {current_archive}...")
    
    # Move each script to the archive
    for script_path in legacy_scripts:
        if script_path.exists():
            # Create the destination path
            dest_path = current_archive / script_path.relative_to(scripts_dir)
            
            # Create any necessary parent directories
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"Moving {script_path.relative_to(scripts_dir)} to archive...")
            shutil.move(script_path, dest_path)
        else:
            print(f"Script {script_path.relative_to(scripts_dir)} not found, skipping...")
    
    # Create a README in the archive directory explaining what was archived
    readme_path = current_archive / "README.md"
    with open(readme_path, "w") as f:
        f.write(f"""# Legacy Test Scripts Archive

This directory contains legacy test scripts that were archived on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}.

These scripts have been replaced by the unified test runner (`run_tests.py`) in the parent directory,
which provides a more consistent, maintainable approach to testing that follows clean architecture principles.

## Archived Scripts

The following scripts were archived:

```
{os.linesep.join([str(script.relative_to(scripts_dir)) for script in legacy_scripts if script.exists()])}
```

If you need to reference the functionality in these scripts, please adapt them to work with
the new unified test runner instead of restoring these legacy versions.
""")
    
    print("\nCleanup completed successfully!")
    print(f"Legacy scripts have been archived to: {current_archive}")
    print("If you need to reference any of these scripts, they can be found in the archive directory.")
    print("However, please use the new unified test runner (run_tests.py) for all testing needs.")


if __name__ == "__main__":
    clean_legacy_test_scripts()