import unittest
import pandas as pd

from hed import HedFileError
from hed.schema import hed_schema_df_constants as constants
from hed.schema.schema_io import ontology_util, df_util
from hed.schema.schema_io.ontology_util import _verify_hedid_matches, assign_hed_ids_section, \
    get_all_ids, convert_df_to_omn, update_dataframes_from_schema
from hed.schema.schema_io.df_util import get_library_name_and_id
from hed import load_schema_version


class TestLibraryFunctions(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_library_name_and_id_default(self):
        # Test default case where no library name is provided
        schema = load_schema_version("8.3.0")
        name, first_id = get_library_name_and_id(schema)
        self.assertEqual(name, "Standard")
        self.assertEqual(first_id, 10000)

    def test_get_library_name_and_id_non_default(self):
        # Test non-default case
        schema = load_schema_version("score_1.1.0")
        name, first_id = get_library_name_and_id(schema)
        self.assertEqual(name, "Score")
        self.assertEqual(first_id, 40000)

    def test_get_library_name_and_id_unknown(self):
        # Test for an unknown library
        schema = load_schema_version("testlib_2.0.0")
        name, first_id = get_library_name_and_id(schema)
        self.assertEqual(name, "Testlib")
        self.assertEqual(first_id, df_util.UNKNOWN_LIBRARY_VALUE)

    def test_get_hedid_range_normal_case(self):
        id_set = ontology_util._get_hedid_range("score", constants.DATA_KEY)
        self.assertTrue(40401 in id_set)
        self.assertEqual(len(id_set), 200)  # Check the range size

    def test_get_hedid_range_boundary(self):
        # Test boundary condition where end range is -1
        id_set = ontology_util._get_hedid_range("score", constants.TAG_KEY)
        self.assertTrue(42001 in id_set)
        self.assertEqual(len(id_set), 18000 - 1)  # From 42001 to 60000

    def test_get_hedid_range_error(self):
        with self.assertRaises(NotImplementedError):
            ontology_util._get_hedid_range("lang", constants.STRUCT_KEY)


class TestVerifyHedIdMatches(unittest.TestCase):
    def setUp(self):
        self.schema_82 = load_schema_version("8.2.0")
        self.schema_id = load_schema_version("8.3.0")

    def test_no_hedid(self):
        df = pd.DataFrame([{'rdfs:label': 'Event', 'hedId': ''}, {'rdfs:label': 'Age-#', 'hedId': ''}])
        errors = _verify_hedid_matches(self.schema_82.tags, df, ontology_util._get_hedid_range("", constants.TAG_KEY))
        self.assertEqual(len(errors), 0)

    def test_id_matches(self):
        df = pd.DataFrame(
            [{'rdfs:label': 'Event', 'hedId': 'HED_0012001'}, {'rdfs:label': 'Age-#', 'hedId': 'HED_0012475'}])
        errors = _verify_hedid_matches(self.schema_id.tags, df, ontology_util._get_hedid_range("", constants.TAG_KEY))
        self.assertEqual(len(errors), 0)

    def test_label_mismatch_id(self):
        df = pd.DataFrame(
            [{'rdfs:label': 'Event', 'hedId': 'HED_0012005'}, {'rdfs:label': 'Age-#', 'hedId': 'HED_0012007'}])

        errors = _verify_hedid_matches(self.schema_id.tags, df, ontology_util._get_hedid_range("", constants.TAG_KEY))
        self.assertEqual(len(errors), 2)

    def test_label_no_entry(self):
        df = pd.DataFrame([{'rdfs:label': 'NotARealEvent', 'hedId': 'does_not_matter'}])

        errors = _verify_hedid_matches(self.schema_id.tags, df, ontology_util._get_hedid_range("", constants.TAG_KEY))
        self.assertEqual(len(errors), 1)

    def test_out_of_range(self):
        df = pd.DataFrame([{'rdfs:label': 'Event', 'hedId': 'HED_0000000'}])

        errors = _verify_hedid_matches(self.schema_82.tags, df,
                                       ontology_util._get_hedid_range("", constants.TAG_KEY))
        self.assertEqual(len(errors), 1)

    def test_not_int(self):
        df = pd.DataFrame([{'rdfs:label': 'Event', 'hedId': 'HED_AAAAAAA'}])

        errors = _verify_hedid_matches(self.schema_82.tags, df,
                                       ontology_util._get_hedid_range("", constants.TAG_KEY))
        self.assertEqual(len(errors), 1)

    def test_get_all_ids_exists(self):
        # Test when hedId column exists and has proper prefixed IDs
        df = pd.DataFrame({
            'hedId': ['HED_0000001', 'HED_0000002', 'HED_0000003']
        })
        result = get_all_ids(df)
        self.assertEqual(result, {1, 2, 3})

    def test_get_all_ids_not_exists(self):
        # Test when hedId column does not exist
        df = pd.DataFrame({
            'otherId': [1, 2, 3]
        })
        result = get_all_ids(df)
        self.assertIsNone(result)

    def test_get_all_ids_mixed_invalid(self):
        # Test when hedId column exists but contains invalid and non-numeric entries
        df = pd.DataFrame({
            'hedId': ['HED_0000001', 'HED_ABC', 'HED_0000003', 'HED_']
        })
        result = get_all_ids(df)
        self.assertEqual(result, {1, 3})  # Should ignore non-numeric and malformed IDs

    def test_assign_hed_ids_section(self):
        df = pd.DataFrame({
            'hedId': ['HED_0000001', 'HED_0000003', None, None],
            'label': ['Label1', 'Label2', 'Label3', 'Label4']  # Adding arbitrary labels
        })
        expected_result = df.copy()
        expected_result.loc[2, 'hedId'] = "HED_0000002"
        expected_result.loc[3, 'hedId'] = "HED_0000004"
        unused_tag_ids = {2, 4, 5}  # Simulate unused hedIds
        assign_hed_ids_section(df, unused_tag_ids)

        self.assertTrue(df.equals(expected_result))


class TestUpdateDataframes(unittest.TestCase):
    def test_update_dataframes_from_schema(self):
        # valid direction first
        schema_dataframes = load_schema_version("8.3.0").get_as_dataframes()
        schema_83 = load_schema_version("8.3.0")
        # Add a test column and ensure it stays around
        fixed_value = "test_column_value"
        for key, df in schema_dataframes.items():
            df['test_column'] = fixed_value

        updated_dataframes = update_dataframes_from_schema(schema_dataframes, schema_83)

        for key, df in updated_dataframes.items():
            self.assertTrue((df['test_column'] == fixed_value).all())
        # this is expected to bomb horribly, since schema lacks many of the spreadsheet entries.
        schema = load_schema_version("8.3.0")
        schema_dataframes_new = load_schema_version("8.3.0").get_as_dataframes()
        try:
            updated_dataframes = update_dataframes_from_schema(schema_dataframes_new, schema)
        except HedFileError as e:
            self.assertEqual(len(e.issues), 115)
        breakHere = 3


class TestConvertOmn(unittest.TestCase):
    def test_convert_df_to_omn(self):
        dataframes = load_schema_version("8.3.0").get_as_dataframes()
        omn_version, _ = convert_df_to_omn(dataframes)

        # make these more robust, for now just verify it's somewhere in the result
        for df_name, df in dataframes.items():
            if df_name == constants.STRUCT_KEY:
                continue  # Not implemented yet
            for label in df['rdfs:label']:
                # Verify that the label is somewhere in the OMN text
                error = f"Label '{label}' from dataframe '{df_name}' was not found in the OMN output."
                label_key = f'rdfs:label "{label}"'
                self.assertIn(label_key, omn_version, error)

            for hed_id in df[constants.hed_id]:
                if df_name == constants.STRUCT_KEY:
                    continue  # Not implemented yet
                base_id = f": hed:{hed_id}"
                error = f"HedId '{base_id}' from dataframe '{df_name}' was not found in the OMN output."
                self.assertIn(base_id, omn_version, error)
