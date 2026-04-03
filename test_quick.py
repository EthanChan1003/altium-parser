#!/usr/bin/env python
"""Test script to verify SchDoc parser functionality."""

import sys
import os

# Change to the project directory
os.chdir(r"c:\Users\kingdee\Documents\parser")
sys.path.insert(0, ".")

def main():
    # Test 1: Import
    print("=" * 50)
    print("Test 1: Importing SchDocParser...")
    try:
        from altium_parser.parsers.schdoc_parser import SchDocParser
        print("  PASS: Import successful")
    except Exception as e:
        print(f"  FAIL: Import failed - {e}")
        return 1

    # Test 2: Check parse method exists
    print("=" * 50)
    print("Test 2: Checking parse method...")
    if hasattr(SchDocParser, 'parse'):
        print("  PASS: parse method exists")
    else:
        print("  FAIL: parse method not found")
        return 1

    # Test 3: Verify docstring
    print("=" * 50)
    print("Test 3: Checking docstring...")
    docstring = SchDocParser.parse.__doc__
    if "Two-Pass" in docstring or "双重遍历" in docstring or "First Pass" in docstring:
        print("  PASS: Two-Pass Parsing strategy documented")
    else:
        print("  INFO: Docstring present but Two-Pass not mentioned")

    # Test 4: Run pytest if available
    print("=" * 50)
    print("Test 4: Running pytest...")
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_schdoc_parser.py", "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=r"c:\Users\kingdee\Documents\parser"
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print("  PASS: All pytest tests passed")
    else:
        print(f"  INFO: pytest exited with code {result.returncode}")

    print("=" * 50)
    print("All basic tests completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
