#!/usr/bin/env python3
"""
Check if the spec_tests directory structure is properly set up for local testing.
This script verifies that the required directories and files exist.
"""

import os


def check_directory(path, description):
    """Check if a directory exists and list its contents."""
    print(f"\nChecking {description}:")
    print(f"  Path: {path}")

    if os.path.exists(path):
        if os.path.isdir(path):
            contents = os.listdir(path)
            if contents:
                print(f"  ✅ Directory exists with {len(contents)} items")
                if len(contents) <= 10:  # Show contents if not too many
                    for item in sorted(contents):
                        item_path = os.path.join(path, item)
                        item_type = "📁" if os.path.isdir(item_path) else "📄"
                        print(f"    {item_type} {item}")
                else:
                    print("    (showing first 10 items)")
                    for item in sorted(contents)[:10]:
                        item_path = os.path.join(path, item)
                        item_type = "📁" if os.path.isdir(item_path) else "📄"
                        print(f"    {item_type} {item}")
                return True
            else:
                print("  ⚠️  Directory exists but is empty")
                return False
        else:
            print("  ❌ Path exists but is not a directory")
            return False
    else:
        print("  ❌ Directory does not exist")
        return False


def main():
    """Main function to check spec_tests setup."""
    print("🔍 Checking spec_tests setup for local development")
    print("=" * 60)

    # Get the spec_tests directory
    spec_tests_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Spec tests directory: {spec_tests_dir}")

    # Required directories and their purposes
    required_dirs = [
        ("hed-specification", "HED specification repository"),
        ("hed-specification/tests", "HED specification test directory"),
        ("hed-specification/tests/json_tests", "JSON test files for error testing"),
        ("hed-examples", "HED examples repository"),
        ("hed-examples/datasets", "BIDS datasets for validation testing"),
    ]

    all_good = True

    for dir_name, description in required_dirs:
        full_path = os.path.join(spec_tests_dir, dir_name)
        result = check_directory(full_path, description)
        if not result:
            all_good = False

    # Check for the sidecar file
    sidecar_path = os.path.join(spec_tests_dir, "test_sidecar.json")
    print("\nChecking test sidecar file:")
    print(f"  Path: {sidecar_path}")
    if os.path.exists(sidecar_path):
        print("  ✅ test_sidecar.json exists")
    else:
        print("  ❌ test_sidecar.json does not exist")
        all_good = False

    print("\n" + "=" * 60)
    if all_good:
        print("✅ All required directories and files are present!")
        print("You should be able to run all spec_tests in VS Code.")
        print("\nTo run all tests:")
        print("  python -m unittest discover spec_tests -v")
    else:
        print("⚠️  Some directories are missing, but spec_tests can still run partially.")
        print("Tests that require missing content will be skipped gracefully.")
        print("\nCurrently available: test_hed_cache.py (works without submodules)")
        print("Currently skipped: test_errors.py, validate_bids.py (need submodule content)")
        print("\nTo set up full spec_tests:")
        print("1. Copy the hed-specification repository content to spec_tests/hed-specification/")
        print("2. Copy the hed-examples repository content to spec_tests/hed-examples/")

    print("\nTo run available tests now:")
    print(f"  cd {os.path.dirname(spec_tests_dir)}")
    print("  python -m unittest discover spec_tests -v")


if __name__ == "__main__":
    main()
