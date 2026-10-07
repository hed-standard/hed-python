"""The hed-tests test schemas, loaded from the vendored folder without the cache or the network.

hed-tests (the ``spec_tests/hed-tests`` submodule) ships load-ready XML for its test-only libraries
(testaux, testclash, testconflict, testminimal) and their standard partners under
``json_test_data/test_schemas/hedxml/``. ``load_schema_version`` resolves version strings against that
folder when it is passed as ``xml_folder``; a folder lookup is all-or-nothing, so a group that also needs
a released schema from the cache is built from two separately loaded schemas.
"""

import os
import unittest

from hed.schema.hed_schema_io import load_schema_version

TEST_SCHEMAS_DIR = os.path.realpath(
    os.path.join(os.path.dirname(__file__), "../../spec_tests/hed-tests/json_test_data/test_schemas/hedxml")
)
SKIP_REASON = "spec_tests/hed-tests is not checked out: git submodule update --init --recursive"


def test_schemas_available() -> bool:
    """Return True when the hed-tests submodule is checked out."""
    return os.path.isdir(TEST_SCHEMAS_DIR)


def load_test_schema(versions):
    """Load hed-tests test schemas by version string, or a list of them, from the vendored folder.

    Parameters:
        versions (str or list of str): Version strings such as ``testconflict_2.1.0`` or
            ``["testconflict_2.1.0", "testclash_1.0.0"]``, with an optional namespace prefix.

    Returns:
        HedSchema or HedSchemaGroup: The loaded schema or group.

    Raises:
        unittest.SkipTest: When the submodule is not checked out (``git submodule update --init --recursive``).
    """
    if not test_schemas_available():
        raise unittest.SkipTest(SKIP_REASON)
    return load_schema_version(versions, xml_folder=TEST_SCHEMAS_DIR)
