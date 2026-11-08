"""The file-version gate for the specification's JSON files (specification Appendix A.6.1)."""

import copy
import json
import os
import unittest

from hed.errors.exceptions import HedExceptions, HedFileError
from hed.validator.util.spec_files import SUPPORTED_FILE_MAJOR, check_file_version

DATA_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "../../hed/validator/data"))


def load_packaged(filename):
    """Return the parsed packaged copy of a specification file."""
    with open(os.path.join(DATA_DIR, filename), encoding="utf-8") as file:
        return json.load(file)


class TestCheckFileVersion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packaged = {filename: load_packaged(filename) for filename in SUPPORTED_FILE_MAJOR}

    def with_version(self, filename, value, key=None):
        """Return a copy of the packaged file with its version key set to value (or removed, for None)."""
        data = copy.deepcopy(self.packaged[filename])
        key = key or SUPPORTED_FILE_MAJOR[filename][0]
        data.pop(SUPPORTED_FILE_MAJOR[filename][0], None)
        if value is not None:
            data[key] = value
        return data

    def assert_refused(self, data, filename):
        with self.assertRaises(HedFileError) as context:
            check_file_version(data, filename)
        self.assertEqual(context.exception.code, HedExceptions.INVALID_FILE_FORMAT)
        self.assertEqual(context.exception.filename, filename)

    def test_the_packaged_files_pass(self):
        for filename, data in self.packaged.items():
            with self.subTest(filename=filename):
                check_file_version(data, filename)

    def test_any_minor_and_patch_number_passes(self):
        for filename in SUPPORTED_FILE_MAJOR:
            for version in ("1.0.0", "1.4.0", "1.0.7", "1.12.30"):
                with self.subTest(filename=filename, version=version):
                    check_file_version(self.with_version(filename, version), filename)

    def test_another_major_number_is_refused(self):
        for filename in SUPPORTED_FILE_MAJOR:
            for version in ("2.0.0", "0.9.0", "10.0.0"):
                with self.subTest(filename=filename, version=version):
                    self.assert_refused(self.with_version(filename, version), filename)

    def test_a_missing_or_malformed_version_is_refused(self):
        for filename in SUPPORTED_FILE_MAJOR:
            for version in (None, "1.0", "v1.0.0", "1.0.0-beta", " 1.0.0", "1.0.0\n", "١.0.0", "", 1, 1.0):
                with self.subTest(filename=filename, version=version):
                    self.assert_refused(self.with_version(filename, version), filename)

    def test_the_other_files_spelling_of_the_key_is_refused(self):
        self.assert_refused(self.with_version("reserved_tags.json", "1.0.0", key="file_version"), "reserved_tags.json")
        self.assert_refused(self.with_version("character_sets.json", "1.0.0", key="fileVersion"), "character_sets.json")

    def test_a_file_that_is_not_an_object_is_refused(self):
        self.assert_refused([], "reserved_tags.json")


if __name__ == "__main__":
    unittest.main()
