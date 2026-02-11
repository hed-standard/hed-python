import unittest
import os
import shutil
from hed import load_schema_version
from hed.scripts.hed_script_util import (
    add_extension,
    sort_base_schemas,
    validate_all_schema_formats,
    validate_schema,
    validate_all_schemas,
)
import contextlib


class TestAddExtension(unittest.TestCase):

    def test_regular_extension(self):
        """Test that regular extensions are added correctly."""
        self.assertEqual(add_extension("filename", ".txt"), "filename.txt")
        self.assertEqual(add_extension("document", ".pdf"), "document.pdf")

    def test_tsv_extension(self):
        """Test that .tsv extensions are handled differently."""
        # Assuming the function correctly handles paths with directories
        self.assertEqual(
            add_extension(os.path.normpath("path/to/filename"), ".tsv"), os.path.normpath("path/to/hedtsv/filename")
        )
        # Testing with a basename only
        self.assertEqual(add_extension("filename", ".tsv"), os.path.normpath("hedtsv/filename"))

    def test_empty_extension(self):
        """Test adding an empty extension."""
        self.assertEqual(add_extension("filename", ""), "filename")

    def test_none_extension(self):
        """Test behavior with None as extension."""
        with self.assertRaises(TypeError):
            add_extension("filename", None)

    def test_invalid_extension_type(self):
        """Test that non-string extensions raise clear TypeError."""
        with self.assertRaises(TypeError) as cm:
            add_extension("filename", None)
        self.assertIn("extension must be a string", str(cm.exception))

        with self.assertRaises(TypeError):
            add_extension("filename", 123)

        with self.assertRaises(TypeError):
            add_extension("filename", [".xml"])

    def test_case_insensitive_extension(self):
        """Test that TSV extensions are detected case-insensitively, but casing is preserved."""
        # TSV in various cases should all go to hedtsv/ subfolder
        self.assertEqual(add_extension("filename", ".TSV"), os.path.normpath("hedtsv/filename"))
        self.assertEqual(add_extension("filename", ".Tsv"), os.path.normpath("hedtsv/filename"))
        self.assertEqual(add_extension("filename", ".tSv"), os.path.normpath("hedtsv/filename"))

        # Other extensions preserve their original casing (important for case-sensitive filesystems)
        self.assertEqual(add_extension("filename", ".XML"), "filename.XML")
        self.assertEqual(add_extension("filename", ".Xml"), "filename.Xml")
        self.assertEqual(add_extension("filename", ".xml"), "filename.xml")


class TestSortBaseSchemas(unittest.TestCase):
    TEST_DIR = "test_directory"

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(cls.TEST_DIR):
            os.makedirs(cls.TEST_DIR)
        os.chdir(cls.TEST_DIR)
        cls.create_stub_files()

    @classmethod
    def tearDownClass(cls):
        os.chdir("..")
        shutil.rmtree(cls.TEST_DIR)

    @classmethod
    def create_stub_files(cls):
        filenames = [
            "test_schema.mediawiki",
            os.path.normpath("hedtsv/test_schema/test_schema_Tag.tsv"),
            "other_schema.xml",
            os.path.normpath("hedtsv/wrong_folder/wrong_name_Tag.tsv"),
            os.path.normpath("prerelease/hedtsv/test_schema/test_schema_Tag.tsv"),
            os.path.normpath("not_hedtsv/test_schema/test_schema_Tag.tsv"),
        ]
        for filename in filenames:
            filepath = os.path.normpath(filename)
            directory = os.path.dirname(filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(filepath, "w") as f:
                f.write("")  # Create an empty file

    def test_mixed_file_types(self):
        filenames = ["test_schema.mediawiki", os.path.normpath("hedtsv/test_schema/test_schema_Tag.tsv"), "other_schema.xml"]
        expected = {
            "test_schema": {
                ".mediawiki": "test_schema.mediawiki",
                ".tsv": os.path.normpath("hedtsv/test_schema"),
            },
            "other_schema": {".xml": "other_schema.xml"},
        }
        with contextlib.redirect_stdout(None):
            result = sort_base_schemas(filenames)
        self.assertEqual(dict(result), expected)

    def test_tsv_in_correct_subfolder(self):
        filenames = [
            os.path.normpath("hedtsv/test_schema/test_schema_Tag.tsv"),
            os.path.normpath("hedtsv/test_schema/test_schema_Tag.tsv"),
            os.path.normpath("hedtsv/wrong_folder/wrong_name_Tag.tsv"),  # Should be ignored
        ]
        expected = {"test_schema": {".tsv": os.path.normpath("hedtsv/test_schema")}}
        with contextlib.redirect_stdout(None):
            result = sort_base_schemas(filenames)
        self.assertEqual(dict(result), expected)

    def test_tsv_in_correct_subfolder2(self):
        filenames = [
            os.path.normpath("prerelease/hedtsv/test_schema/test_schema_Tag.tsv"),
            os.path.normpath("prerelease/hedtsv/test_schema/test_schema_Tag.tsv"),
            os.path.normpath("prerelease/hedtsv/wrong_folder/wrong_name_Tag.tsv"),  # Should be ignored
        ]
        expected = {os.path.normpath("prerelease/test_schema"): {".tsv": os.path.normpath("prerelease/hedtsv/test_schema")}}
        with contextlib.redirect_stdout(None):
            result = sort_base_schemas(filenames)
        self.assertEqual(dict(result), expected)

    def test_ignored_files(self):
        filenames = [
            "test_schema.mediawiki",
            os.path.normpath("not_hedtsv/test_schema/test_schema_Tag.tsv"),  # Should be ignored
        ]
        expected = {"test_schema": {".mediawiki": "test_schema.mediawiki"}}
        with contextlib.redirect_stdout(None):
            result = sort_base_schemas(filenames)
        self.assertEqual(dict(result), expected)

    def test_empty_input(self):
        filenames = []
        expected = {}
        with contextlib.redirect_stdout(None):
            result = sort_base_schemas(filenames)
        self.assertEqual(dict(result), expected)

    def test_case_insensitive_extensions(self):
        """Test that file extensions are handled case-insensitively for grouping."""
        # Create test files with uppercase extensions using different base names to avoid conflicts
        uppercase_files = [
            "case_test_schema.MEDIAWIKI",
            "case_other_schema.XML",
        ]
        for filename in uppercase_files:
            with open(filename, "w") as f:
                f.write("")  # Create empty file

        try:
            filenames = ["case_test_schema.MEDIAWIKI", "case_other_schema.XML"]
            # Should normalize extensions to lowercase for keys, but preserve original paths
            expected = {
                "case_test_schema": {".mediawiki": "case_test_schema.MEDIAWIKI"},
                "case_other_schema": {".xml": "case_other_schema.XML"},
            }
            with contextlib.redirect_stdout(None):
                result = sort_base_schemas(filenames)
            self.assertEqual(dict(result), expected)
        finally:
            # Clean up
            for filename in uppercase_files:
                if os.path.exists(filename):
                    os.remove(filename)


class TestValidateAllSchemaFormats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Determine the path to save schemas based on the location of this test file
        cls.base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas")
        if not os.path.exists(cls.base_path):
            os.makedirs(cls.base_path)
        cls.basename = "test_schema"

    def test_error_no_error(self):
        """Test the function with correctly saved schemas in all four formats."""
        # Load specific schema versions and save them correctly
        schema = load_schema_version("8.4.0")
        schema.save_as_xml(os.path.join(self.base_path, self.basename + ".xml"))
        schema.save_as_dataframes(os.path.join(self.base_path, "hedtsv", self.basename))
        with contextlib.redirect_stdout(None):
            issues = validate_all_schema_formats(os.path.join(self.base_path, self.basename))
        self.assertTrue(issues)
        self.assertEqual(issues[0], "Error loading schema: No such file or directory")
        schema.save_as_mediawiki(os.path.join(self.base_path, self.basename + ".mediawiki"))
        schema.save_as_json(os.path.join(self.base_path, self.basename + ".json"))

        with contextlib.redirect_stdout(None):
            self.assertEqual(validate_all_schema_formats(os.path.join(self.base_path, self.basename)), [])

        schema_incorrect = load_schema_version("8.2.0")
        schema_incorrect.save_as_dataframes(os.path.join(self.base_path, "hedtsv", self.basename))

        # Validate and expect errors
        with contextlib.redirect_stdout(None):
            issues = validate_all_schema_formats(os.path.join(self.base_path, self.basename))
        self.assertTrue(issues)
        # self.assertIn("Error loading schema: No columns to parse from file", issues[0])

    @classmethod
    def tearDownClass(cls):
        """Remove the entire directory created for testing to ensure a clean state."""
        shutil.rmtree(cls.base_path)  # This will delete the directory and all its contents


class TestValidateSchema(unittest.TestCase):
    def test_load_invalid_extension(self):
        # Verify capital letters fail validation
        with contextlib.redirect_stdout(None):
            self.assertIn("Only fully lowercase extensions ", validate_schema("does_not_matter.MEDIAWIKI")[0])
            self.assertIn("Only fully lowercase extensions ", validate_schema("does_not_matter.Mediawiki")[0])
            self.assertIn("Only fully lowercase extensions ", validate_schema("does_not_matter.XML")[0])
            self.assertIn("Only fully lowercase extensions ", validate_schema("does_not_matter.Xml")[0])
            self.assertIn("Only fully lowercase extensions ", validate_schema("does_not_matter.TSV")[0])
            self.assertNotIn("Only fully lowercase extensions ", validate_schema("does_not_matter.tsv")[0])
            self.assertNotIn("Only fully lowercase extensions ", validate_schema("does_not_matter.xml")[0])
            self.assertNotIn("Only fully lowercase extensions ", validate_schema("does_not_matter.mediawiki")[0])

    def test_uppercase_extension_policy_enforcement(self):
        """Test that uppercase extensions are detected and rejected by validation (case-sensitive filesystem support)."""
        # This test verifies the complete workflow:
        # 1. sort_base_schemas can detect/group files with uppercase extensions
        # 2. validate_all_schemas properly rejects them per repository policy
        # 3. No FileNotFoundError on case-sensitive filesystems

        uppercase_file = "policy_test.XML"
        try:
            # Create a file with uppercase extension
            with open(uppercase_file, "w") as f:
                f.write("")  # Empty file for testing

            # Step 1: sort_base_schemas should find and group the file
            schema_files = sort_base_schemas([uppercase_file])
            self.assertIn("policy_test", schema_files)
            self.assertIn(".xml", schema_files["policy_test"])
            self.assertEqual(schema_files["policy_test"][".xml"], uppercase_file)

            # Step 2: validate_all_schemas should use actual path and reject per policy
            with contextlib.redirect_stdout(None):
                issues = validate_all_schemas(schema_files)

            # Should get policy violation, not FileNotFoundError
            self.assertTrue(len(issues) > 0)
            self.assertIn("Only fully lowercase extensions", issues[0])
            self.assertIn("policy_test.XML", issues[0])

        finally:
            # Clean up
            if os.path.exists(uppercase_file):
                os.remove(uppercase_file)
