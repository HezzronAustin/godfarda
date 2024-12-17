#!/usr/bin/env python3
"""Test runner for the AI Tools Ecosystem.

This script discovers and runs all tests in the project.
"""

import unittest
import sys
import os

def run_tests():
    """Discover and run all tests in the project."""
    # Add the src directory to the Python path
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    sys.path.insert(0, src_dir)

    # Discover all tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(src_dir, 'tools')
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return 0 if tests passed, 1 if any failed
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())
