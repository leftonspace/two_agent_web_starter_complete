#!/usr/bin/env python3
"""
STAGE 3 INTEGRATION: Test Runner

Runs all Stage 3 unit tests and reports results.
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test modules
import test_workflow_manager
import test_memory_store
import test_inter_agent_bus


def run_all_tests():
    """Run all Stage 3 tests."""
    print("=" * 70)
    print("STAGE 3 INTEGRATION: Running Unit Tests")
    print("=" * 70)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add tests from each module
    suite.addTests(loader.loadTestsFromModule(test_workflow_manager))
    suite.addTests(loader.loadTestsFromModule(test_memory_store))
    suite.addTests(loader.loadTestsFromModule(test_inter_agent_bus))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()

    if result.wasSuccessful():
        print("✓ ALL TESTS PASSED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
