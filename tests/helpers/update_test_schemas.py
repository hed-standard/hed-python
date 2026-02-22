#!/usr/bin/env python3
"""
Update test schemas from hed-schemas submodule.

This script copies non-deprecated schemas from the hed-schemas submodule
to tests/data/schema_tests/ for testing purposes.

Usage:
    python scripts/update_test_schemas.py [--format FORMAT] [--dry-run]

Parameters:
    --format: Schema format to copy (mediawiki, xml, json, tsv). Default: mediawiki
    --dry-run: Show what would be copied without actually copying
    --library: Also copy library schemas. Default: False
"""

import argparse
import shutil
from pathlib import Path


def get_repo_root():
    """Get the root directory of the hed-python repository."""
    # Script is in tests/helpers/, so go up two levels to reach repo root
    script_dir = Path(__file__).parent
    return script_dir.parent.parent


def get_schema_files(schemas_dir, format_name, exclude_deprecated=True):
    """
    Get list of schema files to copy.

    Parameters:
        schemas_dir: Path to the schemas directory (standard_schema or library_schemas/*)
        format_name: Format subdirectory name (hedwiki, hedxml, hedjson, hedtsv)
        exclude_deprecated: If True, exclude files in deprecated/ subdirectories

    Returns:
        list: List of Path objects for schema files to copy
    """
    format_dir = schemas_dir / format_name
    if not format_dir.exists():
        return []

    schema_files = []
    for schema_file in format_dir.glob("**/*"):
        # Skip if it's a directory
        if schema_file.is_dir():
            continue

        # Skip if in deprecated directory
        if exclude_deprecated and "deprecated" in schema_file.parts:
            continue

        # Skip non-schema files
        if schema_file.name in ["README.md", "CHANGELOG.md", "LICENSE"]:
            continue

        schema_files.append(schema_file)

    return schema_files


def get_format_extension(format_name):
    """Get file extension for the format."""
    format_map = {"hedwiki": ".mediawiki", "hedxml": ".xml", "hedjson": ".json", "hedtsv": ".tsv"}
    return format_map.get(format_name, "")


def copy_schemas(source_dir, dest_dir, format_name, dry_run=False):
    """
    Copy schemas from source to destination.

    Parameters:
        source_dir: Path to source schemas directory
        dest_dir: Path to destination directory
        format_name: Format directory name (hedwiki, hedxml, hedjson, hedtsv)
        dry_run: If True, print what would be copied without copying

    Returns:
        int: Number of files copied
    """
    schema_files = get_schema_files(source_dir, format_name)

    if not schema_files:
        print(f"No {format_name} schemas found in {source_dir}")
        return 0

    # Ensure destination directory exists
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)

    copied_count = 0
    for schema_file in schema_files:
        # Get relative path from format directory
        format_dir = source_dir / format_name
        relative_path = schema_file.relative_to(format_dir)

        # Destination file path
        dest_file = dest_dir / relative_path

        if dry_run:
            print(f"Would copy: {schema_file} -> {dest_file}")
        else:
            # Create parent directories if needed
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(schema_file, dest_file)
            print(f"Copied: {relative_path}")

        copied_count += 1

    return copied_count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Update test schemas from hed-schemas submodule")
    parser.add_argument(
        "--format",
        choices=["mediawiki", "xml", "json", "tsv"],
        default="mediawiki",
        help="Schema format to copy (default: mediawiki)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied without actually copying")
    parser.add_argument(
        "--library", action="store_true", help="Also copy library schemas (default: False, only standard schemas)"
    )

    args = parser.parse_args()

    # Get paths
    repo_root = get_repo_root()
    hed_schemas_root = repo_root / "hed-schemas"
    test_schemas_dir = repo_root / "tests" / "data" / "schema_tests"

    # Check if submodule exists
    if not hed_schemas_root.exists():
        print(f"ERROR: hed-schemas submodule not found at {hed_schemas_root}")
        print("Please run: git submodule update --init --recursive")
        return 1

    # Map user-friendly format names to directory names
    format_map = {"mediawiki": "hedwiki", "xml": "hedxml", "json": "hedjson", "tsv": "hedtsv"}
    format_dir_name = format_map[args.format]

    print(f"Updating test schemas (format: {args.format})")
    if args.dry_run:
        print("DRY RUN - no files will be copied")
    print()

    total_copied = 0

    # Copy standard schemas
    print("Standard schemas:")
    print("-" * 60)
    standard_schemas_dir = hed_schemas_root / "standard_schema"
    count = copy_schemas(standard_schemas_dir, test_schemas_dir, format_dir_name, args.dry_run)
    total_copied += count
    print(f"Copied {count} standard schema files\n")

    # Copy library schemas if requested
    if args.library:
        print("Library schemas:")
        print("-" * 60)
        library_schemas_dir = hed_schemas_root / "library_schemas"

        for library_dir in library_schemas_dir.iterdir():
            if not library_dir.is_dir():
                continue

            print(f"  {library_dir.name}:")
            count = copy_schemas(library_dir, test_schemas_dir, format_dir_name, args.dry_run)
            total_copied += count
            if count > 0:
                print(f"  Copied {count} files")
        print()

    print("=" * 60)
    print(f"Total: {total_copied} schema files {'would be' if args.dry_run else ''} copied")

    if args.dry_run:
        print("\nRun without --dry-run to actually copy the files")

    return 0


if __name__ == "__main__":
    exit(main())
