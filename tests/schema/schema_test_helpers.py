"""
Shared utility functions for schema tests.

Provides helper decorators and functions for creating temporary files and schema folders in tests.
"""

import functools
import os
import shutil
import tempfile

from hed import schema


def get_temp_filename(extension):
    """
    Create a temporary filename with the given extension.

    Parameters:
        extension (str): File extension (e.g., ".xml", ".mediawiki")

    Returns:
        str: Path to temporary file
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
        filename = temp_file.name
    return filename


def with_temp_file(extension):
    """
    Decorator that creates a temporary file for testing and cleans it up afterward.

    Parameters:
        extension (str): File extension (e.g., ".xml", ".mediawiki")

    Returns:
        function: Decorated test function that receives a 'filename' parameter

    Example:
        @with_temp_file(".xml")
        def test_save_xml(self, filename):
            schema.save_as_xml(filename)
            # filename is automatically created and cleaned up
    """

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            # Create a temporary file with the given extension
            filename = get_temp_filename(extension)
            try:
                # Call the test function with the filename
                return test_func(*args, filename=filename, **kwargs)
            finally:
                # Clean up: Remove the temporary file
                if os.path.exists(filename):
                    os.remove(filename)

        return wrapper

    return decorator


def bundled_standard_path(version):
    """
    Return the path of a released standard schema bundled with hedtools.

    Parameters:
        version (str): A released standard version (e.g., "8.4.0").

    Returns:
        str: Path to the bundled XML file in hed/schema/schema_data.
    """
    return os.path.join(os.path.dirname(schema.__file__), "schema_data", f"HED{version}.xml")


def make_xml_folder(versions, copies=()):
    """
    Build a temporary folder to pass as xml_folder: fixture files plus bundled standard schemas.

    A version string loaded with xml_folder is looked up only in that folder, so a test that names a
    released standard there needs the file on disk; it comes from the bundle instead of a copy in tests/data.

    Parameters:
        versions (list[str]): Released standard versions copied from the bundle into the folder root.
        copies (list[tuple[str, str]]): (source, target) pairs; a source file or folder is copied into the
            target subfolder ("" for the root).

    Returns:
        str: Path to the new folder; the caller removes it with shutil.rmtree.
    """
    folder = tempfile.mkdtemp()
    for source, target in copies:
        destination = os.path.join(folder, target)
        if os.path.isdir(source):
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            os.makedirs(destination, exist_ok=True)
            shutil.copy(source, destination)
    for version in versions:
        shutil.copy(bundled_standard_path(version), folder)
    return folder
