#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Test Coverage Reports

This script generates comprehensive test coverage reports in various formats
(HTML, XML, JSON) and ensures the project meets the specified coverage thresholds.

Usage:
    python -m backend.scripts.generate_test_coverage [options]

Options:
    --fail-under=N      Fail if coverage is under N percent (default: 80)
    --html              Generate HTML coverage report (default: True)
    --xml               Generate XML coverage report (default: True)
    --json              Generate JSON coverage report (default: True)
    --output=PATH       Path to write reports to (default: coverage_html/)
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 on success, 1 on failure)
    """
    parser = argparse.ArgumentParser(description="Generate test coverage reports.")
    parser.add_argument("--fail-under", type=int, default=80, help="Fail if coverage is under N percent")
    parser.add_argument("--html", action="store_true", default=True, help="Generate HTML coverage report")
    parser.add_argument("--xml", action="store_true", default=True, help="Generate XML coverage report")
    parser.add_argument("--json", action="store_true", default=True, help="Generate JSON coverage report")
    parser.add_argument("--output", type=str, default="coverage_html/", help="Path to write reports to")
    
    args = parser.parse_args()
    
    # Get the base directory
    base_dir = Path(__file__).resolve().parent.parent
    test_dir = base_dir / "app" / "tests"
    
    # Create output directory if it doesn't exist
    output_dir = base_dir / args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build the pytest command
    cmd = [
        str(base_dir / "venv" / "bin" / "python"),
        "-m", "pytest",
        str(test_dir),
        "--cov=app",
        "--cov-report=term-missing",
        f"--cov-fail-under={args.fail_under}",
    ]
    
    if args.html:
        html_dir = output_dir / "html"
        html_dir.mkdir(parents=True, exist_ok=True)
        cmd.append(f"--cov-report=html:{html_dir}")
    
    if args.xml:
        cmd.append("--cov-report=xml:coverage.xml")
    
    if args.json:
        cmd.append("--cov-report=json:coverage.json")
    
    # Run the coverage command
    print("=" * 80)
    print(f"Generating test coverage reports with minimum threshold of {args.fail_under}%")
    print("=" * 80)
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=base_dir,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Print the output
        print("\nSTDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        # Extract coverage from output
        coverage_pct = 0
        for line in result.stdout.split("\n"):
            if "TOTAL" in line and "%" in line:
                parts = line.split()
                for part in parts:
                    if "%" in part:
                        try:
                            coverage_pct = float(part.strip('%'))
                        except:
                            pass
        
        print("\n" + "=" * 80)
        print(f"Coverage: {coverage_pct:.2f}%")
        print("=" * 80)
        
        if coverage_pct < args.fail_under:
            print(f"\n❌ Coverage {coverage_pct:.2f}% is below the threshold of {args.fail_under}%")
            return 1
        else:
            print(f"\n✅ Coverage {coverage_pct:.2f}% meets the threshold of {args.fail_under}%")
            
            if args.html:
                print(f"\nHTML coverage report generated at: {html_dir}")
            
            if args.xml:
                print(f"XML coverage report generated at: {base_dir}/coverage.xml")
            
            if args.json:
                print(f"JSON coverage report generated at: {base_dir}/coverage.json")
                
            return 0
    
    except subprocess.CalledProcessError as e:
        print(f"Error running coverage command: {e}")
        return 1
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())