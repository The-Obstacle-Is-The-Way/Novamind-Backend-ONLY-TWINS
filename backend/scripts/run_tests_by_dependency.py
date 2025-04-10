#!/usr/bin/env python3
"""
Multi-Stage Test Runner for Novamind Digital Twin Platform

This script runs tests in order of dependency level:
1. Standalone tests (no external dependencies)
2. VENV-only tests (require Python packages but no external services)
3. DB-required tests (require database connections)

The script supports configurable test execution, environment setup,
and comprehensive reporting.

Usage:
    python run_tests_by_dependency.py [options]

Options:
    --standalone-only    Run only standalone tests
    --venv-only          Run only VENV-dependent tests
    --db-only            Run only DB-dependent tests
    --all                Run all tests (default)
    --verbose, -v        Verbose output
    --xml                Generate XML reports
    --html               Generate HTML coverage reports
    --ci                 Run in CI mode (fail fast)
    --cleanup            Clean up test environment after running
"""

import os
import sys
import time
import argparse
import logging
import subprocess
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("test_runner")

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TestStage:
    """Represents a stage of testing with specific dependencies."""

    def __init__(
        self, 
        name: str, 
        marker: str, 
        requires_env: bool = False, 
        description: str = ""
    ):
        """Initialize a test stage.
        
        Args:
            name: Stage name
            marker: Pytest marker to use for selecting tests
            requires_env: Whether this stage requires the test environment
            description: Human-readable description of this stage
        """
        self.name = name
        self.marker = marker
        self.requires_env = requires_env
        self.description = description or name
        self.results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0,
            "duration": 0,
            "exit_code": None,
        }

    def get_marker_expression(self, exclude_previous: List[str] = None) -> str:
        """Get the pytest marker expression for this stage.
        
        Args:
            exclude_previous: Previous stage markers to exclude
            
        Returns:
            Marker expression string
        """
        expression = self.marker
        
        if exclude_previous:
            for prev_marker in exclude_previous:
                expression += f" and not {prev_marker}"
                
        return expression


class TestDependencyRunner:
    """Runs tests in order of dependency level."""

    def __init__(self, backend_dir: Path):
        """Initialize the test runner.
        
        Args:
            backend_dir: Backend directory path
        """
        self.backend_dir = backend_dir
        self.stages = [
            TestStage(
                "standalone", 
                "standalone", 
                requires_env=False,
                description="Standalone Tests (No Dependencies)"
            ),
            TestStage(
                "venv", 
                "venv_only", 
                requires_env=False,
                description="VENV-Only Tests (Python Package Dependencies)"
            ),
            TestStage(
                "db", 
                "db_required", 
                requires_env=True,
                description="Database-Required Tests"
            ),
        ]
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = backend_dir / "test-results"
        self.results_dir.mkdir(exist_ok=True)

    def setup_test_environment(self) -> int:
        """Set up the test environment.
        
        Returns:
            Exit code of the setup command
        """
        logger.info(f"{Colors.BLUE}Setting up test environment...{Colors.ENDC}")

        # Run the test environment setup script
        cmd = [str(self.backend_dir / "scripts" / "run_test_environment.sh"), "start"]
        result = subprocess.run(cmd, cwd=str(self.backend_dir))
        
        if result.returncode != 0:
            logger.error(f"{Colors.RED}Failed to set up test environment{Colors.ENDC}")
            return result.returncode
            
        logger.info(f"{Colors.GREEN}Test environment set up successfully{Colors.ENDC}")
        return 0

    def teardown_test_environment(self) -> int:
        """Tear down the test environment.
        
        Returns:
            Exit code of the teardown command
        """
        logger.info(f"{Colors.BLUE}Tearing down test environment...{Colors.ENDC}")
        
        # Run the test environment teardown script
        cmd = [str(self.backend_dir / "scripts" / "run_test_environment.sh"), "stop"]
        result = subprocess.run(cmd, cwd=str(self.backend_dir))
        
        if result.returncode != 0:
            logger.error(f"{Colors.RED}Failed to tear down test environment{Colors.ENDC}")
            return result.returncode
            
        logger.info(f"{Colors.GREEN}Test environment torn down successfully{Colors.ENDC}")
        return 0

    def run_stage(
        self, 
        stage: TestStage, 
        args: argparse.Namespace, 
        exclude_markers: List[str] = None
    ) -> int:
        """Run a test stage.
        
        Args:
            stage: Test stage to run
            args: Command-line arguments
            exclude_markers: Test markers to exclude
            
        Returns:
            Exit code of the pytest run
        """
        logger.info(f"\n{Colors.BOLD}{Colors.BLUE}Running {stage.description}...{Colors.ENDC}")
        
        # Build the pytest command
        marker_expression = stage.get_marker_expression(exclude_markers)
        
        cmd = ["python", "-m", "pytest", "app/tests", "-m", marker_expression]
        
        # Add verbosity flag
        if args.verbose:
            cmd.append("-v")
            
        # Add coverage options
        if args.html or args.xml:
            cmd.append("--cov=app")
            
        # Add XML output
        if args.xml:
            xml_path = self.results_dir / f"{stage.name}-{self.timestamp}.xml"
            cmd.extend([f"--junitxml={xml_path}"])
            
        # Add HTML output
        if args.html:
            html_dir = self.backend_dir / "coverage_html" / stage.name
            html_dir.mkdir(parents=True, exist_ok=True)
            cmd.extend([f"--cov-report=html:{html_dir}"])
            
        # Always include term coverage output
        if args.html or args.xml:
            cmd.append("--cov-report=term-missing")
            
        # Set environment variables
        env = os.environ.copy()
        env["TESTING"] = "1"
        
        if stage.name == "standalone":
            env["TEST_TYPE"] = "standalone"
        elif stage.name == "venv":
            env["TEST_TYPE"] = "venv"
        elif stage.name == "db":
            env["TEST_TYPE"] = "db"
            env["TEST_DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:15432/novamind_test"
            env["TEST_REDIS_URL"] = "redis://localhost:16379/0"
            
        # Run the tests
        start_time = time.time()
        logger.info(f"Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, env=env, cwd=str(self.backend_dir))
        end_time = time.time()
        
        # Update results
        duration = end_time - start_time
        stage.results["duration"] = duration
        stage.results["exit_code"] = result.returncode
        
        # Log results
        if result.returncode == 0:
            logger.info(f"{Colors.GREEN}✅ {stage.description} passed in {duration:.2f}s{Colors.ENDC}")
        else:
            logger.error(f"{Colors.RED}❌ {stage.description} failed with exit code {result.returncode} in {duration:.2f}s{Colors.ENDC}")
            
        return result.returncode

    def run_all_stages(self, args: argparse.Namespace) -> int:
        """Run all test stages.
        
        Args:
            args: Command-line arguments
            
        Returns:
            Overall exit code
        """
        # Determine which stages to run
        stages_to_run = []
        
        if args.standalone_only:
            stages_to_run.append(self.stages[0])  # standalone
        elif args.venv_only:
            stages_to_run.append(self.stages[1])  # venv
        elif args.db_only:
            stages_to_run.append(self.stages[2])  # db
        else:  # run all stages
            stages_to_run = self.stages
            
        # Check if we need to set up the test environment
        needs_env = any(stage.requires_env for stage in stages_to_run)
        if needs_env:
            env_result = self.setup_test_environment()
            if env_result != 0 and args.ci:
                return env_result
                
        # Execute each stage
        overall_success = True
        exclude_markers = []
        
        for stage in stages_to_run:
            result = self.run_stage(stage, args, exclude_markers)
            exclude_markers.append(stage.marker)
            
            if result != 0:
                overall_success = False
                if args.ci:
                    break  # Stop on first failure in CI mode
                    
        # Clean up the test environment if needed
        if needs_env and args.cleanup:
            self.teardown_test_environment()
            
        # Generate overall report
        self.print_summary(stages_to_run)
        
        return 0 if overall_success else 1

    def print_summary(self, stages: List[TestStage]) -> None:
        """Print a summary of test results.
        
        Args:
            stages: Test stages that were run
        """
        logger.info(f"\n{Colors.BOLD}{Colors.BLUE}Test Run Summary{Colors.ENDC}")
        logger.info(f"{Colors.BLUE}{'='*80}{Colors.ENDC}")
        
        total_duration = sum(stage.results["duration"] for stage in stages)
        all_passed = all(stage.results["exit_code"] == 0 for stage in stages)
        
        for stage in stages:
            status = f"{Colors.GREEN}PASSED{Colors.ENDC}" if stage.results["exit_code"] == 0 else f"{Colors.RED}FAILED{Colors.ENDC}"
            logger.info(f"{stage.description}: {status} in {stage.results['duration']:.2f}s")
            
        logger.info(f"{Colors.BLUE}{'='*80}{Colors.ENDC}")
        logger.info(f"Total Duration: {total_duration:.2f}s")
        logger.info(f"Overall Status: {'✅ PASSED' if all_passed else '❌ FAILED'}")
        
        if not all_passed:
            failed_stages = [stage.description for stage in stages if stage.results["exit_code"] != 0]
            logger.info(f"Failed Stages: {', '.join(failed_stages)}")


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Run tests by dependency level")
    
    # Stage selection options
    stage_group = parser.add_mutually_exclusive_group()
    stage_group.add_argument("--standalone-only", action="store_true", help="Run only standalone tests")
    stage_group.add_argument("--venv-only", action="store_true", help="Run only VENV-dependent tests")
    stage_group.add_argument("--db-only", action="store_true", help="Run only DB-dependent tests")
    stage_group.add_argument("--all", action="store_true", help="Run all tests (default)")
    
    # Output options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--xml", action="store_true", help="Generate XML reports")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage reports")
    
    # Behavior options
    parser.add_argument("--ci", action="store_true", help="Run in CI mode (fail fast)")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test environment after running")
    parser.add_argument("--log-level", default="INFO", 
                      choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                      help="Set logging level")
    
    args = parser.parse_args()
    
    # Set log level
    logger.setLevel(getattr(logging, args.log_level))
    
    # Determine the backend directory
    script_dir = Path(__file__).resolve().parent
    backend_dir = script_dir.parent
    
    # Create and run the test runner
    runner = TestDependencyRunner(backend_dir)
    return runner.run_all_stages(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\nTest run interrupted by user")
        sys.exit(130)  # 128 + SIGINT(2)