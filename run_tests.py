#!/usr/bin/env python3
"""
Test runner for crypto-bot unit tests

This script runs all unit tests and provides a summary of results.
Use this to validate code changes before committing.
"""

import unittest
import sys
import os

def run_tests():
    """Run all unit tests and return results."""
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if result.skipped else 0}")
    
    if result.failures:
        print(f"\nFAILED TESTS ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}")
            
    if result.errors:
        print(f"\nERROR TESTS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        
    print("="*60)
    
    return success

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)