#!/usr/bin/env python
"""
Try loading all schemas from the hed-schemas submodule.

This script attempts to load all non-deprecated schemas in all 4 formats
(XML, MediaWiki, JSON, TSV) from both standard_schema and library_schemas.

NOT included in automatic test discovery - run manually:
    python spec_tests/try_loading_all_schemas.py

Usage:
    python spec_tests/try_loading_all_schemas.py [--format FORMAT] [--library LIBRARY]

Options:
    --format {xml,mediawiki,json,tsv,all}  Test specific format only (default: all)
    --library LIBRARY                       Test specific library only (default: all)
    --standard-only                         Test only standard schemas
    --verbose                               Show detailed success messages
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path to import hed
sys.path.insert(0, str(Path(__file__).parent.parent))

from hed import load_schema


class SchemaLoadTester:
    """Test loading all schemas from hed-schemas submodule."""

    def __init__(self, verbose=False):
        """Initialize the tester.

        Parameters:
            verbose: If True, show detailed success messages
        """
        self.verbose = verbose
        self.results = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        self.failures = []

        # Get the path to hed-schemas submodule
        self.hed_schemas_root = Path(__file__).parent / "hed-schemas"

        if not self.hed_schemas_root.exists():
            raise FileNotFoundError(
                f"hed-schemas submodule not found at {self.hed_schemas_root}.\n"
                f"Run: git submodule update --init --recursive"
            )

    def get_format_dir_name(self, format_name):
        """Map user-friendly format name to directory name."""
        format_map = {"xml": "hedxml", "mediawiki": "hedwiki", "json": "hedjson", "tsv": "hedtsv"}
        return format_map.get(format_name.lower(), format_name)

    def get_schema_files(self, root_dir, format_dir, exclude_deprecated=True, prerelease=False):
        """
        Get all schema files in a format directory.

        Parameters:
            root_dir: Root directory (standard_schema or library_schemas/lib_name)
            format_dir: Format subdirectory name (hedxml, hedwiki, etc.)
            exclude_deprecated: If True, skip files in deprecated/ subdirectories
            prerelease: If True, get schemas from prerelease/ subdirectory

        Returns:
            list: List of Path objects for schema files
        """
        # Use prerelease subdirectory if requested
        if prerelease:
            format_path = root_dir / "prerelease"
        else:
            format_path = root_dir / format_dir

        if not format_path.exists():
            return []

        schema_files = []

        # For prerelease, we need to handle the mixed structure
        if prerelease:
            # In prerelease directory, check format-specific subdirectories or root files
            if format_dir == "hedtsv":
                # TSV schemas are in prerelease/hedtsv/
                tsv_path = format_path / "hedtsv"
                if tsv_path.exists():
                    for item in tsv_path.iterdir():
                        if not item.is_dir():
                            continue
                        if (item / f"{item.name}_Tag.tsv").exists():
                            schema_files.append(item)
            elif format_dir == "hedxml":
                # XML files are in prerelease/ root
                for item in format_path.glob("*.xml"):
                    if item.is_file():
                        schema_files.append(item)
            elif format_dir == "hedwiki":
                # MediaWiki files are in prerelease/ root
                for item in format_path.glob("*.mediawiki"):
                    if item.is_file():
                        schema_files.append(item)
            elif format_dir == "hedjson":
                # JSON files are in prerelease/ root
                for item in format_path.glob("*.json"):
                    if item.is_file():
                        schema_files.append(item)
            return sorted(schema_files)

        # Handle TSV format (directories)
        if format_dir == "hedtsv":
            for item in format_path.iterdir():
                if not item.is_dir():
                    continue
                if exclude_deprecated and "deprecated" in item.parts:
                    continue
                # Check if it has the required TSV files
                if (item / f"{item.name}_Tag.tsv").exists():
                    schema_files.append(item)
        else:
            # Handle file formats (XML, MediaWiki, JSON)
            for schema_file in format_path.rglob("*"):
                if not schema_file.is_file():
                    continue
                if exclude_deprecated and "deprecated" in schema_file.parts:
                    continue
                # Skip non-schema files
                if schema_file.suffix.lower() not in [".xml", ".mediawiki", ".json"]:
                    continue
                if schema_file.name in ["README.md", "CHANGELOG.md", "LICENSE"]:
                    continue
                schema_files.append(schema_file)

        return sorted(schema_files)

    def try_load_schema(self, schema_path, relative_path):
        """
        Try to load a single schema file.

        Parameters:
            schema_path: Path to schema file/directory
            relative_path: Relative path for display purposes

        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        try:
            schema = load_schema(str(schema_path))

            # Basic validation that schema loaded
            if schema is None:
                return False, "Schema loaded as None"

            # Try to access basic properties to ensure it's valid
            _ = schema.version
            _ = schema.library

            return True, None

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            return False, error_msg

    def test_standard_schemas(self, format_filter=None):
        """
        Test loading standard schemas.

        Parameters:
            format_filter: If provided, only test this format
        """
        print("\n" + "=" * 80)
        print("STANDARD SCHEMAS")
        print("=" * 80)

        standard_dir = self.hed_schemas_root / "standard_schema"

        if not standard_dir.exists():
            print(f"[WARNING] Standard schema directory not found: {standard_dir}")
            return

        formats = [format_filter] if format_filter else ["xml", "mediawiki", "json", "tsv"]

        for format_name in formats:
            format_dir = self.get_format_dir_name(format_name)
            schema_files = self.get_schema_files(standard_dir, format_dir)

            if not schema_files:
                continue

            # Print format header with schema names inline
            schema_names = [s.name for s in schema_files]
            print(f"\n{format_name.upper()} ({len(schema_files)}): {', '.join(schema_names)}")

            for schema_path in schema_files:
                relative_path = schema_path.relative_to(self.hed_schemas_root)
                self.results["total"] += 1

                success, error = self.try_load_schema(schema_path, relative_path)

                if success:
                    self.results["passed"] += 1
                    if self.verbose:
                        print(f"  [PASS] {schema_path.name}")
                else:
                    self.results["failed"] += 1
                    print(f"  [FAIL] {schema_path.name}")
                    print(f"    Error: {error}")
                    self.failures.append({"path": str(relative_path), "error": error})

    def test_standard_prereleases(self, format_filter=None):
        """
        Test all standard prerelease schemas.

        Parameters:
            format_filter: If specified, only test this format (e.g., 'xml')
        """
        print("\n" + "=" * 80)
        print("STANDARD PRERELEASE SCHEMAS")
        print("=" * 80)

        standard_dir = self.hed_schemas_root / "standard_schema"
        prerelease_dir = standard_dir / "prerelease"

        if not prerelease_dir.exists():
            print("[INFO] No prerelease directory found")
            return

        formats = [format_filter] if format_filter else ["xml", "mediawiki", "json", "tsv"]

        for format_name in formats:
            format_dir = self.get_format_dir_name(format_name)
            schema_files = self.get_schema_files(standard_dir, format_dir, prerelease=True)

            if not schema_files:
                continue

            # Print format header with schema names inline
            schema_names = [s.name for s in schema_files]
            print(f"\n{format_name.upper()} ({len(schema_files)}): {', '.join(schema_names)}")

            for schema_path in schema_files:
                relative_path = schema_path.relative_to(self.hed_schemas_root)
                self.results["total"] += 1

                success, error = self.try_load_schema(schema_path, relative_path)

                if success:
                    self.results["passed"] += 1
                    if self.verbose:
                        print(f"  [PASS] {schema_path.name}")
                else:
                    self.results["failed"] += 1
                    print(f"  [FAIL] {schema_path.name}")
                    print(f"    Error: {error}")
                    self.failures.append({"path": str(relative_path), "error": error})

    def test_library_schemas(self, format_filter=None, library_filter=None):
        """
        Test loading library schemas.

        Parameters:
            format_filter: If provided, only test this format
            library_filter: If provided, only test this library
        """
        print("\n" + "=" * 80)
        print("LIBRARY SCHEMAS")
        print("=" * 80)

        libraries_dir = self.hed_schemas_root / "library_schemas"

        if not libraries_dir.exists():
            print(f"[WARNING] Library schemas directory not found: {libraries_dir}")
            return

        # Get all library directories
        library_dirs = [d for d in libraries_dir.iterdir() if d.is_dir()]

        if library_filter:
            library_dirs = [d for d in library_dirs if d.name == library_filter]
            if not library_dirs:
                print(f"[WARNING] Library '{library_filter}' not found")
                return

        formats = [format_filter] if format_filter else ["xml", "mediawiki", "json", "tsv"]

        for library_dir in sorted(library_dirs):
            print(f"\n{library_dir.name.upper()}:")

            for format_name in formats:
                format_dir = self.get_format_dir_name(format_name)
                schema_files = self.get_schema_files(library_dir, format_dir)

                if not schema_files:
                    continue

                # Print format header with schema names inline
                schema_names = [s.name for s in schema_files]
                print(f"  {format_name.upper()} ({len(schema_files)}): {', '.join(schema_names)}")

                for schema_path in schema_files:
                    relative_path = schema_path.relative_to(self.hed_schemas_root)
                    self.results["total"] += 1

                    success, error = self.try_load_schema(schema_path, relative_path)

                    if success:
                        self.results["passed"] += 1
                        if self.verbose:
                            print(f"    [PASS] {schema_path.name}")
                    else:
                        self.results["failed"] += 1
                        print(f"    [FAIL] {schema_path.name}")
                        print(f"      Error: {error}")
                        self.failures.append({"path": str(relative_path), "error": error})

    def test_library_prereleases(self, format_filter=None, library_filter=None):
        """
        Test all library prerelease schemas.

        Parameters:
            format_filter: If specified, only test this format (e.g., 'xml')
            library_filter: If specified, only test this library
        """
        print("\n" + "=" * 80)
        print("LIBRARY PRERELEASE SCHEMAS")
        print("=" * 80)

        libraries_dir = self.hed_schemas_root / "library_schemas"

        if not libraries_dir.exists():
            print(f"[WARNING] Libraries directory not found: {libraries_dir}")
            return

        # Get all library directories
        library_dirs = [d for d in libraries_dir.iterdir() if d.is_dir()]

        if library_filter:
            library_dirs = [d for d in library_dirs if d.name == library_filter]
            if not library_dirs:
                print(f"[WARNING] Library '{library_filter}' not found")
                return

        formats = [format_filter] if format_filter else ["xml", "mediawiki", "json", "tsv"]

        found_any = False
        for library_dir in sorted(library_dirs):
            prerelease_dir = library_dir / "prerelease"

            if not prerelease_dir.exists():
                continue

            library_has_schemas = False

            for format_name in formats:
                format_dir = self.get_format_dir_name(format_name)
                schema_files = self.get_schema_files(library_dir, format_dir, prerelease=True)

                if not schema_files:
                    continue

                if not library_has_schemas:
                    print(f"\n{library_dir.name.upper()}:")
                    library_has_schemas = True
                    found_any = True

                # Print format header with schema names inline
                schema_names = [s.name for s in schema_files]
                print(f"  {format_name.upper()} ({len(schema_files)}): {', '.join(schema_names)}")

                for schema_path in schema_files:
                    relative_path = schema_path.relative_to(self.hed_schemas_root)
                    self.results["total"] += 1

                    success, error = self.try_load_schema(schema_path, relative_path)

                    if success:
                        self.results["passed"] += 1
                        if self.verbose:
                            print(f"    [PASS] {schema_path.name}")
                    else:
                        self.results["failed"] += 1
                        print(f"    [FAIL] {schema_path.name}")
                        print(f"      Error: {error}")
                        self.failures.append({"path": str(relative_path), "error": error})

        if not found_any:
            print("[INFO] No prerelease schemas found")

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Schemas: {self.results['total']}")
        print(f"Passed:        {self.results['passed']} ({100*self.results['passed']//max(1,self.results['total'])}%)")
        print(f"Failed:        {self.results['failed']}")
        print(f"Skipped:       {self.results['skipped']}")
        print("=" * 80)

        if self.results["failed"] == 0:
            print("[SUCCESS] All schemas loaded successfully!")
        else:
            print(f"\n[WARNING] {self.results['failed']} schema(s) failed to load")
            print("\nFailed schemas:")
            for failure in self.failures:
                print(f"  * {failure['path']}")
                print(f"    {failure['error']}")

        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Try loading all schemas from hed-schemas submodule")
    parser.add_argument(
        "--format",
        choices=["xml", "mediawiki", "json", "tsv", "all"],
        default="all",
        help="Test specific format only (default: all)",
    )
    parser.add_argument("--library", help="Test specific library only (default: all)")
    parser.add_argument("--standard-only", action="store_true", help="Test only standard schemas")
    parser.add_argument("--exclude-prereleases", action="store_true", help="Exclude prerelease schemas (releases only)")
    parser.add_argument("--prerelease-only", action="store_true", help="Test only prerelease schemas")
    parser.add_argument("--verbose", action="store_true", help="Show detailed success messages")

    args = parser.parse_args()

    # Determine format filter
    format_filter = None if args.format == "all" else args.format

    try:
        tester = SchemaLoadTester(verbose=args.verbose)

        print("\n" + "=" * 80)
        print("HED SCHEMA LOADING TEST")
        print("=" * 80)
        print(f"Testing schemas from: {tester.hed_schemas_root}")
        if format_filter:
            print(f"Format filter: {format_filter.upper()}")
        if args.library:
            print(f"Library filter: {args.library}")
        if args.standard_only:
            print("Mode: Standard schemas only")
        if args.prerelease_only:
            print("Mode: Prerelease schemas only")
        elif args.exclude_prereleases:
            print("Mode: Releases only (prereleases excluded)")

        # Determine what to test based on flags
        if args.prerelease_only:
            # Test only prereleases
            if args.library:
                tester.test_library_prereleases(format_filter, args.library)
            elif args.standard_only:
                tester.test_standard_prereleases(format_filter)
            else:
                tester.test_standard_prereleases(format_filter)
                tester.test_library_prereleases(format_filter, None)
        elif args.exclude_prereleases:
            # Test only releases (exclude prereleases)
            if args.library:
                tester.test_library_schemas(format_filter, args.library)
            elif args.standard_only:
                tester.test_standard_schemas(format_filter)
            else:
                tester.test_standard_schemas(format_filter)
                tester.test_library_schemas(format_filter, None)
        else:
            # Test both releases and prereleases (default)
            if args.library:
                tester.test_library_schemas(format_filter, args.library)
                tester.test_library_prereleases(format_filter, args.library)
            elif args.standard_only:
                tester.test_standard_schemas(format_filter)
                tester.test_standard_prereleases(format_filter)
            else:
                tester.test_standard_schemas(format_filter)
                tester.test_library_schemas(format_filter, None)
                tester.test_standard_prereleases(format_filter)
                tester.test_library_prereleases(format_filter, None)

        tester.print_summary()

        # Exit with error code if any failures
        sys.exit(0 if tester.results["failed"] == 0 else 1)

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
