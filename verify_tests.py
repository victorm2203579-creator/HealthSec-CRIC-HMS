#!/usr/bin/env python
"""
verify_tests.py
===============
Verification script for test suite completeness.

This script counts test methods and validates test file structure.
"""

import os
import re
from pathlib import Path

def count_tests_in_file(filepath):
    """Count test methods in a test file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Find all test methods (def test_*)
    test_methods = re.findall(r'def (test_\w+)', content)

    # Find all test classes
    test_classes = re.findall(r'class (\w*Tests?)\(TestCase\)', content)

    return test_methods, test_classes

def main():
    """Verify test suite completeness."""
    project_root = Path(__file__).parent
    test_files = [
        'accounts/tests.py',
        'monitoring/tests.py',
        'risk_engine/tests.py',
        'compliance/tests.py',
        'alerts/tests.py',
        'audit/tests.py',
    ]

    total_tests = 0
    total_classes = 0

    print("=" * 70)
    print("HEALTHSEC TEST SUITE VERIFICATION")
    print("=" * 70)
    print()

    for test_file in test_files:
        filepath = project_root / test_file

        if filepath.exists():
            methods, classes = count_tests_in_file(filepath)
            test_count = len(methods)
            class_count = len(classes)

            total_tests += test_count
            total_classes += class_count

            status = "[OK]"
            print(f"{status}  {test_file}")
            print(f"       Tests: {test_count} | Classes: {class_count}")

            # Show first few test methods
            if methods:
                print(f"       Sample tests: {', '.join(methods[:3])}")
            print()
        else:
            print(f"[ERROR] MISSING  {test_file}")
            print()

    # Check fixtures
    print("-" * 70)
    print("FIXTURES")
    print("-" * 70)

    fixtures = [
        'fixtures/test_users.json',
        'fixtures/test_patient_records.json',
        'fixtures/test_threat_events.json',
    ]

    for fixture in fixtures:
        filepath = project_root / fixture
        if filepath.exists():
            size_kb = filepath.stat().st_size / 1024
            print(f"[OK]  {fixture} ({size_kb:.1f} KB)")
        else:
            print(f"[ERROR] MISSING  {fixture}")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Test Files:       {len(test_files)}")
    print(f"Total Test Classes:     {total_classes}")
    print(f"Total Test Methods:     {total_tests}")
    print(f"Estimated Assertions:   {total_tests * 2} (approx 2 per test)")
    print()
    print("Documentation:")
    test_guide = project_root / 'TEST_GUIDE.md'
    print(f"[OK]  {test_guide.name}" if test_guide.exists() else f"[ERROR] MISSING  {test_guide.name}")

    print()
    print("=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("""
1. Run all tests:
   python manage.py test

2. Run specific app tests:
   python manage.py test accounts
   python manage.py test monitoring
   python manage.py test risk_engine
   python manage.py test compliance
   python manage.py test alerts
   python manage.py test audit

3. Run tests with coverage:
   pip install coverage
   coverage run --source='.' manage.py test
   coverage report

4. Load fixtures (optional):
   python manage.py loaddata fixtures/test_users.json
   python manage.py loaddata fixtures/test_patient_records.json
   python manage.py loaddata fixtures/test_threat_events.json

5. Read the test guide:
   cat TEST_GUIDE.md
""")
    print("=" * 70)

if __name__ == '__main__':
    main()
