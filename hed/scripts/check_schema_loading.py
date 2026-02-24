#!/usr/bin/env python3
"""Check that all HED schemas in a hed-schemas repository can be loaded.

Attempts to load all non-deprecated schemas in all 4 formats
(XML, MediaWiki, JSON, TSV) from both standard_schema and library_schemas
directories within a hed-schemas repository checkout.

Can be used as:
    1. A console script installed via hedtools: hed_check_schema_loading --schemas-dir /path/to/hed-schemas
    2. Imported and called programmatically from tests or other scripts.

Usage:
    hed_check_schema_loading --schemas-dir /path/to/hed-schemas [OPTIONS]

Options:
    --schemas-dir PATH                      Path to hed-schemas repository root (required)
    --format {xml,mediawiki,json,tsv,all}   Test specific format only (default: all)
    --library LIBRARY                       Test specific library only (default: all)
    --standard-only                         Test only standard schemas (no libraries)
    --exclude-prereleases                   Exclude prerelease schemas (releases only)
    --prerelease-only                       Test only prerelease schemas
    --verbose                               Show detailed success messages

Exit codes:
    0   All schemas loaded successfully
    1   One or more schemas failed to load
    2   Invalid command-line arguments
    130 Interrupted by user
"""

import argparse
import sys
from pathlib import Path

from hed import load_schema

FORMAT_DIR_MAP = {"xml": "hedxml", "mediawiki": "hedwiki", "json": "hedjson", "tsv": "hedtsv"}
FORMAT_EXTENSIONS = {"hedxml": ".xml", "hedwiki": ".mediawiki", "hedjson": ".json"}
ALL_FORMATS = ["xml", "mediawiki", "json", "tsv"]


class SchemaLoadTester:
    """Test loading all schemas from a hed-schemas repository checkout.

    Parameters:
        hed_schemas_root (str or Path): Path to the hed-schemas repository root.
        verbose (bool): If True, show detailed success messages.

    Raises:
        FileNotFoundError: If hed_schemas_root does not exist.
    """

    def __init__(self, hed_schemas_root, verbose=False):
        """Initialize the tester.

        Parameters:
            hed_schemas_root (str or Path): Path to the hed-schemas repository root.
            verbose (bool): If True, show detailed success messages.
        """
        self.verbose = verbose
        self.results = {"total": 0, "passed": 0, "failed": 0}
        self.failures = []

        self.hed_schemas_root = Path(hed_schemas_root)

        if not self.hed_schemas_root.exists():
            raise FileNotFoundError(
                f"hed-schemas directory not found at {self.hed_schemas_root}.\n"
                f"Provide a valid path with --schemas-dir or set up the submodule:\n"
                f"  git submodule update --init --recursive"
            )

    def get_schema_files(self, root_dir, format_dir, prerelease=False):
        """Get all schema files in a format directory.

        Parameters:
            root_dir (Path): Root directory (standard_schema or library_schemas/lib_name).
            format_dir (str): Format subdirectory name (hedxml, hedwiki, etc.).
            prerelease (bool): If True, get schemas from prerelease/ subdirectory.

        Returns:
            list: List of Path objects for schema files.
        """
        if prerelease:
            format_path = root_dir / "prerelease"
        else:
            format_path = root_dir / format_dir

        if not format_path.exists():
            return []

        schema_files = []

        if prerelease:
            if format_dir == "hedtsv":
                tsv_path = format_path / "hedtsv"
                if tsv_path.exists():
                    for item in tsv_path.iterdir():
                        if not item.is_dir():
                            continue
                        if (item / f"{item.name}_Tag.tsv").exists():
                            schema_files.append(item)
            else:
                ext = FORMAT_EXTENSIONS.get(format_dir, "")
                if ext:
                    for item in format_path.glob(f"*{ext}"):
                        if item.is_file():
                            schema_files.append(item)
            return sorted(schema_files)

        # Handle TSV format (directories)
        if format_dir == "hedtsv":
            for item in format_path.iterdir():
                if not item.is_dir():
                    continue
                if "deprecated" in item.parts:
                    continue
                if (item / f"{item.name}_Tag.tsv").exists():
                    schema_files.append(item)
        else:
            for schema_file in format_path.rglob("*"):
                if not schema_file.is_file():
                    continue
                if "deprecated" in schema_file.parts:
                    continue
                if schema_file.suffix.lower() not in [".xml", ".mediawiki", ".json"]:
                    continue
                if schema_file.name in ["README.md", "CHANGELOG.md", "LICENSE"]:
                    continue
                schema_files.append(schema_file)

        return sorted(schema_files)

    def try_load_schema(self, schema_path, relative_path):
        """Try to load a single schema file.

        Parameters:
            schema_path (Path): Path to schema file/directory.
            relative_path (Path): Relative path for display purposes.

        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        try:
            schema = load_schema(str(schema_path))

            if schema is None:
                return False, "Schema loaded as None"

            _ = schema.version
            _ = schema.library

            return True, None

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            return False, error_msg

    def _test_format_group(self, root_dir, format_name, prerelease=False, indent=""):
        """Test loading schemas for a single format in a directory.

        Parameters:
            root_dir (Path): Root directory containing format subdirectories.
            format_name (str): Format to test (xml, mediawiki, json, tsv).
            prerelease (bool): If True, look in prerelease/ subdirectory.
            indent (str): Indentation prefix for output.

        Returns:
            bool: True if any schemas were found and tested.
        """
        format_dir = FORMAT_DIR_MAP.get(format_name.lower(), format_name)
        schema_files = self.get_schema_files(root_dir, format_dir, prerelease=prerelease)

        if not schema_files:
            return False

        schema_names = [s.name for s in schema_files]
        print(f"{indent}{format_name.upper()} ({len(schema_files)}): {', '.join(schema_names)}")

        for schema_path in schema_files:
            relative_path = schema_path.relative_to(self.hed_schemas_root)
            self.results["total"] += 1

            success, error = self.try_load_schema(schema_path, relative_path)

            if success:
                self.results["passed"] += 1
                if self.verbose:
                    print(f"{indent}  [PASS] {schema_path.name}")
            else:
                self.results["failed"] += 1
                print(f"{indent}  [FAIL] {schema_path.name}")
                print(f"{indent}    Error: {error}")
                self.failures.append({"path": str(relative_path), "error": error})

        return True

    def test_standard_schemas(self, format_filter=None):
        """Test loading standard schemas.

        Parameters:
            format_filter (str or None): If provided, only test this format.
        """
        print("\n" + "=" * 80)
        print("STANDARD SCHEMAS")
        print("=" * 80)

        standard_dir = self.hed_schemas_root / "standard_schema"

        if not standard_dir.exists():
            print(f"[WARNING] Standard schema directory not found: {standard_dir}")
            return

        formats = [format_filter] if format_filter else ALL_FORMATS

        for format_name in formats:
            self._test_format_group(standard_dir, format_name, indent="\n")

    def test_standard_prereleases(self, format_filter=None):
        """Test all standard prerelease schemas.

        Parameters:
            format_filter (str or None): If specified, only test this format.
        """
        print("\n" + "=" * 80)
        print("STANDARD PRERELEASE SCHEMAS")
        print("=" * 80)

        standard_dir = self.hed_schemas_root / "standard_schema"
        prerelease_dir = standard_dir / "prerelease"

        if not prerelease_dir.exists():
            print("[INFO] No prerelease directory found")
            return

        formats = [format_filter] if format_filter else ALL_FORMATS

        for format_name in formats:
            self._test_format_group(standard_dir, format_name, prerelease=True, indent="\n")

    def test_library_schemas(self, format_filter=None, library_filter=None):
        """Test loading library schemas.

        Parameters:
            format_filter (str or None): If provided, only test this format.
            library_filter (str or None): If provided, only test this library.
        """
        print("\n" + "=" * 80)
        print("LIBRARY SCHEMAS")
        print("=" * 80)

        library_dirs = self._get_library_dirs(library_filter)
        if library_dirs is None:
            return

        formats = [format_filter] if format_filter else ALL_FORMATS

        for library_dir in sorted(library_dirs):
            print(f"\n{library_dir.name.upper()}:")

            for format_name in formats:
                self._test_format_group(library_dir, format_name, indent="  ")

    def test_library_prereleases(self, format_filter=None, library_filter=None):
        """Test all library prerelease schemas.

        Parameters:
            format_filter (str or None): If specified, only test this format.
            library_filter (str or None): If specified, only test this library.
        """
        print("\n" + "=" * 80)
        print("LIBRARY PRERELEASE SCHEMAS")
        print("=" * 80)

        library_dirs = self._get_library_dirs(library_filter)
        if library_dirs is None:
            return

        formats = [format_filter] if format_filter else ALL_FORMATS

        found_any = False
        for library_dir in sorted(library_dirs):
            prerelease_dir = library_dir / "prerelease"

            if not prerelease_dir.exists():
                continue

            library_has_schemas = False

            for format_name in formats:
                format_dir = FORMAT_DIR_MAP.get(format_name.lower(), format_name)
                schema_files = self.get_schema_files(library_dir, format_dir, prerelease=True)

                if not schema_files:
                    continue

                if not library_has_schemas:
                    print(f"\n{library_dir.name.upper()}:")
                    library_has_schemas = True
                    found_any = True

                self._test_format_group(library_dir, format_name, prerelease=True, indent="  ")

        if not found_any:
            print("[INFO] No prerelease schemas found")

    def _get_library_dirs(self, library_filter=None):
        """Get library directories, optionally filtered.

        Parameters:
            library_filter (str or None): If provided, only return this library.

        Returns:
            list or None: List of library Path objects, or None if directory not found.
        """
        libraries_dir = self.hed_schemas_root / "library_schemas"

        if not libraries_dir.exists():
            print(f"[WARNING] Library schemas directory not found: {libraries_dir}")
            return None

        library_dirs = [d for d in libraries_dir.iterdir() if d.is_dir()]

        if library_filter:
            library_dirs = [d for d in library_dirs if d.name == library_filter]
            if not library_dirs:
                print(f"[WARNING] Library '{library_filter}' not found")
                return None

        return library_dirs

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Schemas: {self.results['total']}")
        print(f"Passed:        {self.results['passed']} ({100 * self.results['passed'] // max(1, self.results['total'])}%)")
        print(f"Failed:        {self.results['failed']}")
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


def run_loading_check(
    hed_schemas_root,
    format_filter=None,
    library_filter=None,
    standard_only=False,
    exclude_prereleases=False,
    prerelease_only=False,
    verbose=False,
):
    """Run schema loading checks and return results.

    This is the main programmatic entry point for checking schema loading.
    Can be called from tests or other scripts without going through CLI.

    Parameters:
        hed_schemas_root (str or Path): Path to the hed-schemas repository root.
        format_filter (str or None): If provided, only test this format.
        library_filter (str or None): If provided, only test this library.
        standard_only (bool): If True, test only standard schemas.
        exclude_prereleases (bool): If True, exclude prerelease schemas.
        prerelease_only (bool): If True, test only prerelease schemas.
        verbose (bool): If True, show detailed success messages.

    Returns:
        dict: Results dictionary with keys 'total', 'passed', 'failed',
            and 'failures' (list of dicts with 'path' and 'error').
    """
    tester = SchemaLoadTester(hed_schemas_root, verbose=verbose)

    print("\n" + "=" * 80)
    print("HED SCHEMA LOADING TEST")
    print("=" * 80)
    print(f"Testing schemas from: {tester.hed_schemas_root}")
    if format_filter:
        print(f"Format filter: {format_filter.upper()}")
    if library_filter:
        print(f"Library filter: {library_filter}")
    if standard_only:
        print("Mode: Standard schemas only")
    if prerelease_only:
        print("Mode: Prerelease schemas only")
    elif exclude_prereleases:
        print("Mode: Releases only (prereleases excluded)")

    if prerelease_only:
        if library_filter:
            tester.test_library_prereleases(format_filter, library_filter)
        elif standard_only:
            tester.test_standard_prereleases(format_filter)
        else:
            tester.test_standard_prereleases(format_filter)
            tester.test_library_prereleases(format_filter, None)
    elif exclude_prereleases:
        if library_filter:
            tester.test_library_schemas(format_filter, library_filter)
        elif standard_only:
            tester.test_standard_schemas(format_filter)
        else:
            tester.test_standard_schemas(format_filter)
            tester.test_library_schemas(format_filter, None)
    else:
        if library_filter:
            tester.test_library_schemas(format_filter, library_filter)
            tester.test_library_prereleases(format_filter, library_filter)
        elif standard_only:
            tester.test_standard_schemas(format_filter)
            tester.test_standard_prereleases(format_filter)
        else:
            tester.test_standard_schemas(format_filter)
            tester.test_library_schemas(format_filter, None)
            tester.test_standard_prereleases(format_filter)
            tester.test_library_prereleases(format_filter, None)

    tester.print_summary()

    return {
        **tester.results,
        "failures": tester.failures,
    }


def parse_arguments(arg_list=None):
    """Parse command-line arguments.

    Parameters:
        arg_list (list or None): Arguments to parse, or None for sys.argv.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Check that all HED schemas in a hed-schemas repository can be loaded.")
    parser.add_argument(
        "--schemas-dir",
        required=True,
        help="Path to the hed-schemas repository root directory",
    )
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

    return parser.parse_args(arg_list)


def validate_arguments(args):
    """Validate command-line arguments for conflicts.

    Parameters:
        args (argparse.Namespace): Parsed arguments from argparse.

    Raises:
        SystemExit: If conflicting arguments are detected (exit code 2).
    """
    errors = []

    if args.library and args.standard_only:
        errors.append("--library and --standard-only are mutually exclusive")

    if args.exclude_prereleases and args.prerelease_only:
        errors.append("--exclude-prereleases and --prerelease-only are mutually exclusive")

    if errors:
        print("\n[ERROR] Conflicting command-line options detected:\n")
        for error in errors:
            print(f"  - {error}")
        print("\nUse --help to see valid option combinations.")
        sys.exit(2)


def main(arg_list=None):
    """Main CLI entry point.

    Parameters:
        arg_list (list or None): Arguments to parse, or None for sys.argv.
    """
    args = parse_arguments(arg_list)
    validate_arguments(args)

    format_filter = None if args.format == "all" else args.format

    try:
        results = run_loading_check(
            hed_schemas_root=args.schemas_dir,
            format_filter=format_filter,
            library_filter=args.library,
            standard_only=args.standard_only,
            exclude_prereleases=args.exclude_prereleases,
            prerelease_only=args.prerelease_only,
            verbose=args.verbose,
        )

        sys.exit(0 if results["failed"] == 0 else 1)

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
