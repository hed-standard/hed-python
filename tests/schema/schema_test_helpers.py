"""
Shared utility functions for schema tests.

Provides helper decorators and functions for creating temporary files in tests.
"""

import functools
import os
import tempfile


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
