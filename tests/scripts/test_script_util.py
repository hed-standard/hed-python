import unittest
import os
import shutil
from hed import load_schema_version
from hed.scripts.script_util import add_extension, sort_base_schemas, validate_all_schema_formats, validate_schema
import contextlib


class TestAddExtension(unittest.TestCase):

    def test_regular_extension(self):
        """Test that regular extensions are added correctly."""
        self.assertEqual(add_extension("filename", ".txt"), "filename.txt")
        self.assertEqual(add_extension("document", ".pdf"), "document.pdf")

    def test_tsv_extension(self):
        """Test that .tsv extensions are handled differently."""
        # Assuming the function correctly handles paths with directories
        self.assertEqual(add_extension(os.path.normpath("path/to/filename"), ".tsv"),
                         os.path.normpath("path/to/hedtsv/filename"))
        # Testing with a basename only
        self.assertEqual(add_extension("filename", ".tsv"), os.path.normpath("hedtsv/filename"))

    def test_empty_extension(self):
        """Test adding an empty extension."""
        self.assertEqual(add_extension("filename", ""), "filename")

    def test_none_extension(self):
        """Test behavior with None as extension."""
        with self.assertRaises(TypeError):
            add_extension("filename", None)


class TestSortBaseSchemas(unittest.TestCase):
    TEST_DIR = 'test_directory'

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(cls.TEST_DIR):
            os.makedirs(cls.TEST_DIR)
        os.chdir(cls.TEST_DIR)
        cls.create_stub_files()

    @classmethod
    def tearDownClass(cls):
        os.chdir('..')
        shutil.rmtree(cls.TEST_DIR)

    @classmethod
    def create_stub_files(cls):
        filenames = [
            "test_schema.mediawiki",
            os.path.normpath("hedtsv/test_schema/test_schema_Tag.tsv"),
            "other_schema.xml",
            os.path.normpath("hedtsv/wrong_folder/wrong_name_Tag.tsv"),
            os.path.normpath("prerelease/hedtsv/test_schema/test_schema_Tag.tsv"),
            os.path.normpath("not_hedtsv/test_schema/test_schema_Tag.tsv")
        ]
        for filename in filenames:
            filepath = os.path.normpath(filename)
            directory = os.path.dirname(filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write('')  # Create an empty file

    def test_mixed_file_types(self):
        filenames = [
            "test_schema.mediawiki",
            os.path.normpath("hedtsv/test_schema/test_schema_Tag.tsv"),
            "other_schema.xml"
        ]
        expected = {
            "test_schema": {".mediawiki", ".tsv"},
            "other_schema": {".xml"}
        }
        with contextlib.redirect_stdout(None):
            result = sort_base_schemas(filenames)
        self.assertEqual(dict(result), expected)

    def test_tsv_in_correct_subfolder(self):
        filenames = [
            os.path.normpath("hedtsv/test_schema/test_schema_Tag.tsv"),
            os.path.normpath("hedtsv/test_schema/test_schema_Tag.tsv"),
            os.path.normpath("hedtsv/wrong_folder/wrong_name_Tag.tsv")  # Should be ignored
        ]
        expected = {
            "test_schema": {".tsv"}
        }
        with contextlib.redirect_stdout(None):
            result = sort_base_schemas(filenames)
        self.assertEqual(dict(result), expected)

    def test_tsv_in_correct_subfolder2(self):
        filenames = [
            os.path.normpath("prerelease/hedtsv/test_schema/test_schema_Tag.tsv"),
            os.path.normpath("prerelease/hedtsv/test_schema/test_schema_Tag.tsv"),
            os.path.normpath("prerelease/hedtsv/wrong_folder/wrong_name_Tag.tsv")  # Should be ignored
        ]
        expected = {
            os.path.normpath("prerelease/test_schema"): {".tsv"}
        }
        with contextlib.redirect_stdout(None):
            result = sort_base_schemas(filenames)
        self.assertEqual(dict(result), expected)

    def test_ignored_files(self):
        filenames = [
            "test_schema.mediawiki",
            os.path.normpath("not_hedtsv/test_schema/test_schema_Tag.tsv")  # Should be ignored
        ]
        expected = {
            "test_schema": {".mediawiki"}
        }
        with contextlib.redirect_stdout(None):
            result = sort_base_schemas(filenames)
        self.assertEqual(dict(result), expected)

    def test_empty_input(self):
        filenames = []
        expected = {}
        with contextlib.redirect_stdout(None):
            result = sort_base_schemas(filenames)
        self.assertEqual(dict(result), expected)


class TestValidateAllSchemaFormats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Determine the path to save schemas based on the location of this test file
        cls.base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schemas')
        if not os.path.exists(cls.base_path):
            os.makedirs(cls.base_path)
        cls.basename = "test_schema"

    def test_error_no_error(self):
        """Test the function with correctly saved schemas in all three formats."""
        # Load specific schema versions and save them correctly
        schema = load_schema_version("8.3.0")
        schema.save_as_xml(os.path.join(self.base_path, self.basename + ".xml"))
        schema.save_as_dataframes(os.path.join(self.base_path, "hedtsv", self.basename))
        with contextlib.redirect_stdout(None):
            issues = validate_all_schema_formats(os.path.join(self.base_path, self.basename))
        self.assertTrue(issues)
        self.assertIn("Error loading schema", issues[0])

        schema.save_as_mediawiki(os.path.join(self.base_path, self.basename + ".mediawiki"))

        with contextlib.redirect_stdout(None):
            self.assertEqual(validate_all_schema_formats(os.path.join(self.base_path, self.basename)), [])

        schema_incorrect = load_schema_version("8.2.0")
        schema_incorrect.save_as_dataframes(os.path.join(self.base_path, "hedtsv", self.basename))

        # Validate and expect errors
        with contextlib.redirect_stdout(None):
            issues = validate_all_schema_formats(os.path.join(self.base_path, self.basename))
        self.assertTrue(issues)
        self.assertIn("Error loading schema: No columns to parse from file", issues[0])

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
