#!/usr/bin/env python
"""
Test Runner Script for CSV2JSON project

This script provides a convenient way to run tests with different configurations.
"""

import argparse
import subprocess
import sys
import os

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run tests for the CSV2JSON-API project")
    
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--auth", action="store_true", help="Run only authentication tests")
    parser.add_argument("--api", action="store_true", help="Run only API tests")
    parser.add_argument("--db", action="store_true", help="Run only database tests")
    parser.add_argument("--cov", action="store_true", help="Generate coverage report")
    parser.add_argument("--file", type=str, help="Run tests from a specific file")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Verbosity level (up to -vvv)")
    
    return parser.parse_args()

def build_command(args):
    """Build the pytest command based on arguments."""
    cmd = ["pytest"]
    
    # Set verbosity
    if args.verbose:
        cmd.extend(["-" + "v" * args.verbose])
    else:
        cmd.append("-v")
    
    # Add markers for test types
    markers = []
    if args.unit:
        markers.append("unit")
    if args.integration:
        markers.append("integration")
    if args.auth:
        markers.append("auth")
    if args.api:
        markers.append("api")
    if args.db:
        markers.append("db")
    
    if markers:
        cmd.append("-m")
        cmd.append(" or ".join(markers))
    
    # Add coverage if requested
    if args.cov:
        cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html"])
    
    # Specific file if provided
    if args.file:
        cmd.append(args.file)
    
    return cmd

def run_tests(cmd):
    """Run the tests with the given command."""
    try:
        subprocess.run(cmd, check=True)
        return 0
    except subprocess.CalledProcessError as e:
        return e.returncode

if __name__ == "__main__":
    args = parse_args()
    cmd = build_command(args)
    
    print(f"Running command: {' '.join(cmd)}")
    sys.exit(run_tests(cmd))
