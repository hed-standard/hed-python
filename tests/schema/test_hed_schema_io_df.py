import unittest
import shutil
import os
import pandas as pd
from hed.errors import HedExceptions, HedFileError
from hed.schema.hed_schema_io import load_schema, load_schema_version, from_dataframes
from hed.schema.schema_io import df_constants as df_constants
from hed.schema.schema_io.df_util import convert_filenames_to_dict, create_empty_dataframes


class TestHedSchemaDF(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output_folder = "test_output/"
        os.makedirs(cls.output_folder, exist_ok=True)
        cls.schema = load_schema_version("8.4.0")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.output_folder)

    def test_saving_default_schemas(self):
        # schema = load_schema_version("8.3.0")
        # schema.save_as_dataframes(self.output_folder + "test_8.tsv")
        #
        # reloaded_schema = load_schema(self.output_folder + "test_8.tsv")
        # self.assertEqual(schema, reloaded_schema)
        #
        schema = load_schema_version("score_1.1.0")

        schema.save_as_dataframes(self.output_folder + "test_score.tsv", save_merged=True)

        reloaded_schema = load_schema(self.output_folder + "test_score.tsv")
        self.assertEqual(schema, reloaded_schema)

        schema = load_schema_version("testlib_3.0.0")
        schema.save_as_dataframes(self.output_folder + "test_testlib.tsv", save_merged=True)

        reloaded_schema = load_schema(self.output_folder + "test_testlib.tsv")
        self.assertEqual(schema, reloaded_schema)

        schema = load_schema_version("testlib_3.0.0")
        schema.save_as_dataframes(self.output_folder + "test_testlib2.tsv", save_merged=False)

        reloaded_schema = load_schema(self.output_folder + "test_testlib2.tsv")
        self.assertEqual(schema, reloaded_schema)

    def test_from_dataframes(self):
        filename = self.output_folder + "test_8_string.tsv"
        self.schema.save_as_dataframes(self.output_folder + "test_8_string.tsv")

        filenames = convert_filenames_to_dict(filename)
        new_file_strings = {}
        for key, value in filenames.items():
            try:
                with open(value, "r") as f:
                    all_lines = f.readlines()
                    new_file_strings[key] = "".join(all_lines)
            except FileNotFoundError:
                pass

        reloaded_schema = from_dataframes(new_file_strings)
        self.assertEqual(self.schema, reloaded_schema)

        dfs = self.schema.get_as_dataframes()
        reloaded_schema = from_dataframes(dfs)
        self.assertEqual(self.schema, reloaded_schema)

    def test_save_load_location(self):
        schema_name = "test_output"
        output_location = self.output_folder + schema_name
        self.schema.save_as_dataframes(output_location)
        expected_location = os.path.join(output_location, f"{schema_name}_Tag.tsv")
        self.assertTrue(os.path.exists(expected_location))

        reloaded_schema = load_schema(output_location)

        self.assertEqual(self.schema, reloaded_schema)

    def test_save_load_location2(self):
        schema_name = "test_output"
        output_location = self.output_folder + schema_name + ".tsv"
        self.schema.save_as_dataframes(output_location)
        expected_location = self.output_folder + schema_name + "_Tag.tsv"
        self.assertTrue(os.path.exists(expected_location))

        reloaded_schema = load_schema(output_location)

        self.assertEqual(self.schema, reloaded_schema)

    def _create_structure_df(self):
        data = {
            "hedId": ["HED_0060010"],
            "rdfs:label": ["LangHeader"],
            "Attributes": ['version="1.0.0", library="lang", withStandard="8.3.0", unmerged="True"'],
            "omn:SubClassOf": ["HedHeader"],
            "dc:description": [""],
            "omn:EquivalentTo": [
                'HedHeader and (inHedSchema some LangSchema) and (version value "1.0.0")'
                + 'and (library value "lang") and (withStandard value "8.3.0")'
                + 'and (unmerged value "True")'
            ],
        }

        df = pd.DataFrame(data)
        return df

    def _add_tag_row(self, tag_df, name, parent):
        new_row = dict.fromkeys(tag_df.columns, "")
        new_row[df_constants.name] = name
        new_row[df_constants.subclass_of] = parent
        return pd.concat([tag_df, pd.DataFrame([new_row])], ignore_index=True)

    def test_loading_out_of_order(self):
        # Verify loading a .tsv file that defines a child before it's parent works
        dataframes = create_empty_dataframes()
        struct_df = self._create_structure_df()
        tag_df = pd.DataFrame([], columns=df_constants.tag_columns, dtype=str)

        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagNameParent", "HedTag")
        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagNameChild", "MadeUpLongTagNameParent")

        dataframes[df_constants.STRUCT_KEY] = struct_df
        dataframes[df_constants.TAG_KEY] = tag_df

        loaded_schema = from_dataframes(dataframes)
        issues = loaded_schema.check_compliance(check_for_warnings=False)
        self.assertEqual(len(issues), 0)

        self.assertEqual(loaded_schema.tags["MadeUpLongTagNameChild"].name, "MadeUpLongTagNameParent/MadeUpLongTagNameChild")
        self.assertEqual(loaded_schema.tags["MadeUpLongTagNameParent"].name, "MadeUpLongTagNameParent")

        tag_df = pd.DataFrame([], columns=df_constants.tag_columns, dtype=str)

        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagNameChild", "MadeUpLongTagNameParent")
        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagNameParent", "HedTag")

        dataframes[df_constants.TAG_KEY] = tag_df

        loaded_out_of_order = from_dataframes(dataframes)
        issues = loaded_schema.check_compliance(check_for_warnings=False)
        self.assertEqual(len(issues), 0)
        self.assertEqual(loaded_schema.tags["MadeUpLongTagNameChild"].name, "MadeUpLongTagNameParent/MadeUpLongTagNameChild")
        self.assertEqual(loaded_schema.tags["MadeUpLongTagNameParent"].name, "MadeUpLongTagNameParent")
        self.assertEqual(loaded_schema, loaded_out_of_order)

    def test_loading_circular(self):
        # Verify a circular reference properly reports an error
        dataframes = create_empty_dataframes()
        struct_df = self._create_structure_df()
        tag_df = pd.DataFrame([], columns=df_constants.tag_columns, dtype=str)

        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagNameParent", "MadeUpLongTagNameChild")
        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagNameChild", "MadeUpLongTagNameParent")

        dataframes[df_constants.STRUCT_KEY] = struct_df
        dataframes[df_constants.TAG_KEY] = tag_df

        with self.assertRaises(HedFileError) as error:
            _ = from_dataframes(dataframes)
        self.assertEqual(error.exception.args[0], HedExceptions.SCHEMA_TAG_TSV_BAD_PARENT)

        dataframes = create_empty_dataframes()
        struct_df = self._create_structure_df()
        tag_df = pd.DataFrame([], columns=df_constants.tag_columns, dtype=str)

        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagName1", "MadeUpLongTagName2")
        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagName2", "MadeUpLongTagName3")
        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagName3", "MadeUpLongTagName1")

        dataframes[df_constants.STRUCT_KEY] = struct_df
        dataframes[df_constants.TAG_KEY] = tag_df

        with self.assertRaises(HedFileError) as error:
            _ = from_dataframes(dataframes)
        self.assertEqual(error.exception.args[0], HedExceptions.SCHEMA_TAG_TSV_BAD_PARENT)

    def test_empty_tag_dataframe_has_headers(self):
        """Test that when a schema has no tags, the tag DataFrame still has proper column headers."""
        from hed.schema.schema_io.schema2df import Schema2DF
        from tests.schema.util_create_schemas import _get_test_schema

        # Create a minimal schema with no tags (only required sections)
        schema = _get_test_schema([])

        # Test the schema converter
        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        tag_df = output_dfs[df_constants.TAG_KEY]

        # The DataFrame should be empty but have proper column headers
        self.assertTrue(tag_df.empty, "Tag DataFrame should be empty")
        self.assertGreater(len(tag_df.columns), 0, "Tag DataFrame should have column headers")
        self.assertEqual(
            list(tag_df.columns),
            df_constants.tag_columns,
            f"Expected columns {df_constants.tag_columns}, got {list(tag_df.columns)}",
        )

    def test_all_empty_dataframes_have_headers(self):
        """Test that all empty DataFrames have proper column headers."""
        from hed.schema.schema_io.schema2df import Schema2DF
        from tests.schema.util_create_schemas import _get_test_schema

        # Create a minimal schema with no tags
        schema = _get_test_schema([])

        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        # Check all DataFrames have proper headers even when empty
        for key, df in output_dfs.items():
            if key in df_constants.attribute_key_names:
                expected_columns = df_constants.attribute_key_names[key]
                if df.empty:
                    self.assertGreater(len(df.columns), 0, f"{key} DataFrame should have column headers when empty")
                    self.assertEqual(list(df.columns), expected_columns, f"{key} DataFrame has incorrect columns")

    def test_no_equivalent_to_column_in_tags(self):
        """Test that equivalent_to column is never generated in tag DataFrames."""
        from hed.schema.schema_io.schema2df import Schema2DF
        from tests.schema.util_create_schemas import load_schema1

        # Load a schema with tags
        schema = load_schema1()

        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        tag_df = output_dfs[df_constants.TAG_KEY]

        # Verify no equivalent_to column exists
        self.assertNotIn("omn:EquivalentTo", tag_df.columns, "Tag DataFrame should not have equivalent_to column")

    def test_no_equivalent_to_column_in_units(self):
        """Test that equivalent_to column is never generated in unit-related DataFrames."""
        from hed.schema.schema_io.schema2df import Schema2DF

        # Use the standard schema which has units
        schema = self.schema

        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        # Check units, unit classes, and unit modifiers
        for key in [df_constants.UNIT_KEY, df_constants.UNIT_CLASS_KEY, df_constants.UNIT_MODIFIER_KEY]:
            if key in output_dfs and not output_dfs[key].empty:
                df = output_dfs[key]
                self.assertNotIn("omn:EquivalentTo", df.columns, f"{key} DataFrame should not have equivalent_to column")

    def test_no_equivalent_to_column_in_value_classes(self):
        """Test that equivalent_to column is never generated in value class DataFrames."""
        from hed.schema.schema_io.schema2df import Schema2DF

        schema = self.schema

        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        if df_constants.VALUE_CLASS_KEY in output_dfs:
            vc_df = output_dfs[df_constants.VALUE_CLASS_KEY]
            if not vc_df.empty:
                self.assertNotIn(
                    "omn:EquivalentTo", vc_df.columns, "Value class DataFrame should not have equivalent_to column"
                )

    def test_tag_columns_correct_with_data(self):
        """Test that tag DataFrames with data have exactly the expected columns."""
        from hed.schema.schema_io.schema2df import Schema2DF
        from tests.schema.util_create_schemas import load_schema1

        schema = load_schema1()

        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        tag_df = output_dfs[df_constants.TAG_KEY]

        # Should have data
        self.assertFalse(tag_df.empty, "Tag DataFrame should have data")

        # Should have exactly the expected columns (no more, no less)
        self.assertEqual(
            set(tag_df.columns), set(df_constants.tag_columns), "Tag DataFrame should have exactly the expected columns"
        )

    def test_save_and_load_empty_schema(self):
        """Test that an empty schema can be saved and loaded with proper headers."""
        from tests.schema.util_create_schemas import _get_test_schema
        import tempfile

        schema = _get_test_schema([])

        # Save to a temporary location
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "empty_schema.tsv")
            schema.save_as_dataframes(output_path)

            # Check that the tag TSV file exists and has headers
            tag_file = output_path.replace(".tsv", "_Tag.tsv")
            self.assertTrue(os.path.exists(tag_file), "Tag TSV file should exist")

            # Read the file and verify it has headers
            with open(tag_file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                self.assertTrue(len(first_line) > 0, "Tag TSV should have header line")
                # Should have tab-separated column names
                headers = first_line.split("\t")
                self.assertGreater(len(headers), 0, "Should have column headers")

            # Verify we can reload the schema
            reloaded_schema = load_schema(output_path)
            self.assertIsNotNone(reloaded_schema, "Should be able to reload empty schema")

    def test_schema2df_constructor_no_params(self):
        """Test that Schema2DF constructor works without parameters."""
        from hed.schema.schema_io.schema2df import Schema2DF

        # Should work without any parameters
        converter = Schema2DF()
        self.assertIsNotNone(converter, "Schema2DF should construct without parameters")

        # Should be able to process a schema
        from tests.schema.util_create_schemas import load_schema1

        schema = load_schema1()
        output_dfs = converter.process_schema(schema)
        self.assertIsNotNone(output_dfs, "Should be able to process schema")
        self.assertIn(df_constants.TAG_KEY, output_dfs, "Should produce tag DataFrame")

    def test_unit_columns_with_has_unit_class(self):
        """Test that unit DataFrames have hasUnitClass column populated correctly."""
        from hed.schema.schema_io.schema2df import Schema2DF

        schema = self.schema

        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        if df_constants.UNIT_KEY in output_dfs and not output_dfs[df_constants.UNIT_KEY].empty:
            unit_df = output_dfs[df_constants.UNIT_KEY]

            # Should have hasUnitClass column
            self.assertIn(df_constants.has_unit_class, unit_df.columns, "Unit DataFrame should have hasUnitClass column")

            # Values should be unit class names (strings), not IDs
            has_unit_class_values = unit_df[df_constants.has_unit_class].dropna()
            if len(has_unit_class_values) > 0:
                # Check that values don't look like IDs (e.g., "hed:HED_0012345")
                for value in has_unit_class_values:
                    self.assertFalse(value.startswith("hed:HED_"), f"hasUnitClass should contain names, not IDs: {value}")

    def test_tsv_output_uses_lf_line_endings(self):
        """Test that TSV output always uses LF (\\n) line endings, not CRLF (\\r\\n)."""
        from tests.schema.util_create_schemas import load_schema1
        import tempfile

        schema = load_schema1()

        # Save to a temporary location
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_schema.tsv")
            schema.save_as_dataframes(output_path)

            # Check that the tag TSV file uses LF endings
            tag_file = output_path.replace(".tsv", "_Tag.tsv")
            self.assertTrue(os.path.exists(tag_file), "Tag TSV file should exist")

            # Read file in binary mode to check actual line endings
            with open(tag_file, "rb") as f:
                content = f.read()

            # Check that file uses LF (\n) not CRLF (\r\n)
            self.assertNotIn(b"\r\n", content, "File should not contain CRLF line endings")
            self.assertIn(b"\n", content, "File should contain LF line endings")

    def test_tsv_reading_handles_both_line_endings(self):
        """Test that TSV files can be read correctly with either LF or CRLF line endings."""
        from tests.schema.util_create_schemas import load_schema1
        from hed.schema import load_schema
        import tempfile

        schema = load_schema1()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Save the schema with LF endings (our standard)
            lf_path = os.path.join(tmpdir, "lf_schema.tsv")
            schema.save_as_dataframes(lf_path)

            # Create a version with CRLF endings
            crlf_path = os.path.join(tmpdir, "crlf_schema.tsv")
            tag_lf = lf_path.replace(".tsv", "_Tag.tsv")
            tag_crlf = crlf_path.replace(".tsv", "_Tag.tsv")

            # Read the LF file and convert to CRLF
            with open(tag_lf, "rb") as f:
                lf_content = f.read()

            # Normalize to LF first, then convert to CRLF to avoid double carriage returns
            crlf_content = lf_content.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")

            # Write CRLF version
            os.makedirs(os.path.dirname(crlf_path), exist_ok=True)
            with open(tag_crlf, "wb") as f:
                f.write(crlf_content)

            # Copy other files
            for suffix in [
                "Structure",
                "UnitClass",
                "Unit",
                "UnitModifier",
                "ValueClass",
                "AnnotationProperty",
                "DataProperty",
                "ObjectProperty",
                "AttributeProperty",
            ]:
                src = lf_path.replace(".tsv", f"_{suffix}.tsv")
                dst = crlf_path.replace(".tsv", f"_{suffix}.tsv")
                if os.path.exists(src):
                    with open(src, "rb") as f:
                        content = f.read()
                    # Normalize to LF first, then convert to CRLF to avoid double carriage returns
                    with open(dst, "wb") as f:
                        f.write(content.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))

            # Both should load successfully
            lf_schema = load_schema(lf_path)
            crlf_schema = load_schema(crlf_path)

            # And they should be equivalent
            self.assertEqual(lf_schema, crlf_schema, "Schemas with different line endings should be equivalent")

    def test_xml_output_uses_lf_line_endings(self):
        """Test that XML schema files always use LF line endings, not CRLF."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = os.path.join(tmpdir, "test_schema.xml")

            # Save schema as XML
            self.schema.save_as_xml(xml_path)

            # Read file in binary mode to check actual line endings
            with open(xml_path, "rb") as f:
                content = f.read()

            # Should not contain CRLF (b'\r\n')
            self.assertNotIn(b"\r\n", content, "XML file should not contain CRLF line endings")
            # Should contain LF (b'\n')
            self.assertIn(b"\n", content, "XML file should contain LF line endings")

    def test_mediawiki_output_uses_lf_line_endings(self):
        """Test that MediaWiki schema files always use LF line endings, not CRLF."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            wiki_path = os.path.join(tmpdir, "test_schema.mediawiki")

            # Save schema as MediaWiki
            self.schema.save_as_mediawiki(wiki_path)

            # Read file in binary mode to check actual line endings
            with open(wiki_path, "rb") as f:
                content = f.read()

            # Should not contain CRLF (b'\r\n')
            self.assertNotIn(b"\r\n", content, "MediaWiki file should not contain CRLF line endings")
            # Should contain LF (b'\n')
            self.assertIn(b"\n", content, "MediaWiki file should contain LF line endings")

    def test_json_output_uses_lf_line_endings(self):
        """Test that JSON schema files always use LF line endings, not CRLF."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "test_schema.json")

            # Save schema as JSON
            self.schema.save_as_json(json_path)

            # Read file in binary mode to check actual line endings
            with open(json_path, "rb") as f:
                content = f.read()

            # Should not contain CRLF (b'\r\n')
            self.assertNotIn(b"\r\n", content, "JSON file should not contain CRLF line endings")
            # Should contain LF (b'\n')
            self.assertIn(b"\n", content, "JSON file should contain LF line endings")

    def test_xml_library_schema_uses_lf(self):
        """Test that library schemas saved as XML use LF line endings."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Load a library schema
            lib_schema = load_schema_version("testlib_3.0.0")

            # Test both merged and unmerged saves
            for save_merged in [True, False]:
                xml_path = os.path.join(tmpdir, f"testlib_merged_{save_merged}.xml")
                lib_schema.save_as_xml(xml_path, save_merged=save_merged)

                with open(xml_path, "rb") as f:
                    content = f.read()

                self.assertNotIn(
                    b"\r\n",
                    content,
                    f"XML library schema (save_merged={save_merged}) should not contain CRLF",
                )
                self.assertIn(b"\n", content, "XML file should contain LF line endings")

    def test_mediawiki_library_schema_uses_lf(self):
        """Test that library schemas saved as MediaWiki use LF line endings."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Load a library schema
            lib_schema = load_schema_version("testlib_3.0.0")

            # Test both merged and unmerged saves
            for save_merged in [True, False]:
                wiki_path = os.path.join(tmpdir, f"testlib_merged_{save_merged}.mediawiki")
                lib_schema.save_as_mediawiki(wiki_path, save_merged=save_merged)

                with open(wiki_path, "rb") as f:
                    content = f.read()

                self.assertNotIn(
                    b"\r\n",
                    content,
                    f"MediaWiki library schema (save_merged={save_merged}) should not contain CRLF",
                )
                self.assertIn(b"\n", content, "MediaWiki file should contain LF line endings")

    def test_json_library_schema_uses_lf(self):
        """Test that library schemas saved as JSON use LF line endings."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Load a library schema
            lib_schema = load_schema_version("testlib_3.0.0")

            # Test both merged and unmerged saves
            for save_merged in [True, False]:
                json_path = os.path.join(tmpdir, f"testlib_merged_{save_merged}.json")
                lib_schema.save_as_json(json_path, save_merged=save_merged)

                with open(json_path, "rb") as f:
                    content = f.read()

                self.assertNotIn(b"\r\n", content, f"JSON library schema (save_merged={save_merged}) should not contain CRLF")
                self.assertIn(b"\n", content, "JSON file should contain LF line endings")

    def test_tsv_library_schema_uses_lf(self):
        """Test that library schemas saved as TSV use LF line endings."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Load a library schema
            lib_schema = load_schema_version("testlib_3.0.0")

            # Test both merged and unmerged saves
            for save_merged in [True, False]:
                tsv_path = os.path.join(tmpdir, f"testlib_merged_{save_merged}.tsv")
                lib_schema.save_as_dataframes(tsv_path, save_merged=save_merged)

                # Check all TSV files
                tag_path = tsv_path.replace(".tsv", "_Tag.tsv")
                if os.path.exists(tag_path):
                    with open(tag_path, "rb") as f:
                        content = f.read()

                    self.assertNotIn(
                        b"\r\n",
                        content,
                        f"TSV library schema Tag file (save_merged={save_merged}) should not contain CRLF",
                    )
                    self.assertIn(b"\n", content, "TSV file should contain LF line endings")

    def test_all_formats_roundtrip_with_lf(self):
        """Test that all formats can be saved and reloaded with LF line endings preserved."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            schema = load_schema_version("8.3.0")

            # Test XML
            xml_path = os.path.join(tmpdir, "test.xml")
            schema.save_as_xml(xml_path)
            reloaded_xml = load_schema(xml_path)
            self.assertEqual(schema, reloaded_xml, "XML schema should round-trip correctly")

            # Verify LF in saved file
            with open(xml_path, "rb") as f:
                self.assertNotIn(b"\r\n", f.read(), "Saved XML should use LF")

            # Test MediaWiki
            wiki_path = os.path.join(tmpdir, "test.mediawiki")
            schema.save_as_mediawiki(wiki_path)
            reloaded_wiki = load_schema(wiki_path)
            self.assertEqual(schema, reloaded_wiki, "MediaWiki schema should round-trip correctly")

            # Verify LF in saved file
            with open(wiki_path, "rb") as f:
                self.assertNotIn(b"\r\n", f.read(), "Saved MediaWiki should use LF")

            # Test JSON
            json_path = os.path.join(tmpdir, "test.json")
            schema.save_as_json(json_path)
            reloaded_json = load_schema(json_path)
            self.assertEqual(schema, reloaded_json, "JSON schema should round-trip correctly")

            # Verify LF in saved file
            with open(json_path, "rb") as f:
                self.assertNotIn(b"\r\n", f.read(), "Saved JSON should use LF")

            # Test TSV
            tsv_path = os.path.join(tmpdir, "test.tsv")
            schema.save_as_dataframes(tsv_path)
            reloaded_tsv = load_schema(tsv_path)
            self.assertEqual(schema, reloaded_tsv, "TSV schema should round-trip correctly")

            # Verify LF in all TSV files
            for suffix in ["Tag", "Structure", "Unit", "UnitClass", "UnitModifier", "ValueClass"]:
                file_path = tsv_path.replace(".tsv", f"_{suffix}.tsv")
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        self.assertNotIn(b"\r\n", f.read(), f"Saved TSV {suffix} should use LF")

    def test_no_carriage_return_anywhere_in_output(self):
        """Test that there are absolutely no carriage return characters in any schema output."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            schema = load_schema_version("8.4.0")

            # Test all formats
            formats = [
                ("xml", lambda p: schema.save_as_xml(p)),
                ("mediawiki", lambda p: schema.save_as_mediawiki(p)),
                ("json", lambda p: schema.save_as_json(p)),
            ]

            for ext, save_func in formats:
                file_path = os.path.join(tmpdir, f"test.{ext}")
                save_func(file_path)

                with open(file_path, "rb") as f:
                    content = f.read()

                # Count carriage returns - should be zero
                cr_count = content.count(b"\r")
                self.assertEqual(cr_count, 0, f"Format {ext} should have ZERO carriage return characters, found {cr_count}")

            # Test TSV format
            tsv_path = os.path.join(tmpdir, "test.tsv")
            schema.save_as_dataframes(tsv_path)

            # Check all generated TSV files
            for file in os.listdir(tmpdir):
                if file.startswith("test") and file.endswith(".tsv"):
                    file_path = os.path.join(tmpdir, file)
                    with open(file_path, "rb") as f:
                        content = f.read()

                    cr_count = content.count(b"\r")
                    self.assertEqual(
                        cr_count, 0, f"TSV file {file} should have ZERO carriage return characters, found {cr_count}"
                    )


if __name__ == "__main__":
    unittest.main()
