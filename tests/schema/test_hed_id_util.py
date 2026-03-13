import unittest
import pandas as pd

from hed import HedFileError
from hed.schema.schema_io import hed_id_util, df_util, df_constants as constants
from hed.schema.schema_io.hed_id_util import (
    _verify_hedid_matches,
    assign_hed_ids_section,
    get_all_ids,
    update_dataframes_from_schema,
)
from hed.schema.schema_io.df_util import get_library_name_and_id
from hed import load_schema_version

hed_schema_global = load_schema_version("8.4.0")


class TestLibraryFunctions(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_library_name_and_id_default(self):
        # Test default case where no library name is provided
        name, first_id = get_library_name_and_id(hed_schema_global)
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
        id_set = hed_id_util._get_hedid_range("score", constants.DATA_KEY)
        self.assertTrue(40401 in id_set)
        self.assertEqual(len(id_set), 200)  # Check the range size

    def test_get_hedid_range_boundary(self):
        # Test boundary condition where end range is -1
        id_set = hed_id_util._get_hedid_range("score", constants.TAG_KEY)
        self.assertTrue(42001 in id_set)
        self.assertEqual(len(id_set), 18000 - 1)  # From 42001 to 60000

    def test_get_hedid_range_error(self):
        with self.assertRaises(NotImplementedError):
            hed_id_util._get_hedid_range("lang", constants.STRUCT_KEY)


class TestVerifyHedIdMatches(unittest.TestCase):
    def setUp(self):
        self.schema_82 = load_schema_version("8.2.0")

    def test_no_hedid(self):
        df = pd.DataFrame([{"rdfs:label": "Event", "hedId": ""}, {"rdfs:label": "Age-#", "hedId": ""}])
        errors = _verify_hedid_matches(self.schema_82.tags, df, hed_id_util._get_hedid_range("", constants.TAG_KEY))
        self.assertEqual(len(errors), 0)

    def test_id_matches(self):
        df = pd.DataFrame(
            [{"rdfs:label": "Event", "hedId": "HED_0012001"}, {"rdfs:label": "Age-#", "hedId": "HED_0012475"}]
        )
        errors = _verify_hedid_matches(hed_schema_global.tags, df, hed_id_util._get_hedid_range("", constants.TAG_KEY))
        self.assertEqual(len(errors), 0)

    def test_label_mismatch_id(self):
        df = pd.DataFrame(
            [{"rdfs:label": "Event", "hedId": "HED_0012005"}, {"rdfs:label": "Age-#", "hedId": "HED_0012007"}]
        )

        errors = _verify_hedid_matches(hed_schema_global.tags, df, hed_id_util._get_hedid_range("", constants.TAG_KEY))
        self.assertEqual(len(errors), 2)

    def test_label_no_entry(self):
        df = pd.DataFrame([{"rdfs:label": "NotARealEvent", "hedId": "does_not_matter"}])

        errors = _verify_hedid_matches(hed_schema_global.tags, df, hed_id_util._get_hedid_range("", constants.TAG_KEY))
        self.assertEqual(len(errors), 1)

    def test_out_of_range(self):
        df = pd.DataFrame([{"rdfs:label": "Event", "hedId": "HED_0000000"}])

        errors = _verify_hedid_matches(self.schema_82.tags, df, hed_id_util._get_hedid_range("", constants.TAG_KEY))
        self.assertEqual(len(errors), 1)

    def test_not_int(self):
        df = pd.DataFrame([{"rdfs:label": "Event", "hedId": "HED_AAAAAAA"}])

        errors = _verify_hedid_matches(self.schema_82.tags, df, hed_id_util._get_hedid_range("", constants.TAG_KEY))
        self.assertEqual(len(errors), 1)

    def test_verify_unknown_library_skips_range_check(self):
        """An unregistered library returns empty range — IDs should not be reported as out-of-range."""
        empty_range = set()
        df = pd.DataFrame([{"rdfs:label": "Event", "hedId": "HED_0012001"}])
        # testlib has no library_data entry, so _get_hedid_range returns {}
        errors = _verify_hedid_matches(self.schema_82.tags, df, empty_range)
        self.assertEqual(len(errors), 0, "Unknown-library empty range should not trigger range errors")

    def test_empty_unused_ids_no_crash(self):
        """_verify_hedid_matches must not crash when unused_tag_ids is empty (covers min/max guard)."""
        empty_range = set()
        df = pd.DataFrame(
            [{"rdfs:label": "Event", "hedId": "HED_0099999"}, {"rdfs:label": "Age-#", "hedId": "HED_0000001"}]
        )
        # Should complete without raising ValueError from min()/max()
        errors = _verify_hedid_matches(self.schema_82.tags, df, empty_range)
        self.assertEqual(len(errors), 0)

    def test_get_all_ids_exists(self):
        # Test when hedId column exists and has proper prefixed IDs
        df = pd.DataFrame({"hedId": ["HED_0000001", "HED_0000002", "HED_0000003"]})
        result = get_all_ids(df)
        self.assertEqual(result, {1, 2, 3})

    def test_get_all_ids_not_exists(self):
        # Test when hedId column does not exist
        df = pd.DataFrame({"otherId": [1, 2, 3]})
        result = get_all_ids(df)
        self.assertIsNone(result)

    def test_get_all_ids_mixed_invalid(self):
        # Test when hedId column exists but contains invalid and non-numeric entries
        df = pd.DataFrame({"hedId": ["HED_0000001", "HED_ABC", "HED_0000003", "HED_"]})
        result = get_all_ids(df)
        self.assertEqual(result, {1, 3})  # Should ignore non-numeric and malformed IDs

    def test_get_all_ids_with_nan(self):
        # Test when hedId column contains NaN values (pandas null)
        df = pd.DataFrame({"hedId": ["HED_0000001", pd.NA, "HED_0000003", None]})
        result = get_all_ids(df)
        self.assertEqual(result, {1, 3})  # Should handle NaN/None gracefully

    def test_get_all_ids_with_numeric_types(self):
        # Test when hedId column contains numeric types (edge case)
        # pd.to_numeric will convert these numeric values as-is
        df = pd.DataFrame({"hedId": ["HED_0000001", 123, "HED_0000003", 456]})
        result = get_all_ids(df)
        # Should extract from valid string entries with HED_ prefix AND numeric values
        self.assertEqual(result, {1, 3, 123, 456})

    def test_get_all_ids_empty_strings(self):
        # Test when hedId column contains empty strings
        df = pd.DataFrame({"hedId": ["HED_0000001", "", "HED_0000003", ""]})
        result = get_all_ids(df)
        self.assertEqual(result, {1, 3})

    def test_get_all_ids_with_none(self):
        # Test when hedId column contains None values
        df = pd.DataFrame({"hedId": ["HED_0000001", None, "HED_0000003", None]})
        result = get_all_ids(df)
        self.assertEqual(result, {1, 3})

    def test_assign_hed_ids_section(self):
        df = pd.DataFrame(
            {
                "hedId": ["HED_0000001", "HED_0000003", None, None],
                "label": ["Label1", "Label2", "Label3", "Label4"],  # Adding arbitrary labels
            }
        )
        expected_result = df.copy()
        expected_result.loc[2, "hedId"] = "HED_0000002"
        expected_result.loc[3, "hedId"] = "HED_0000004"
        unused_tag_ids = {2, 4, 5}  # Simulate unused hedIds
        assign_hed_ids_section(df, unused_tag_ids)

        self.assertTrue(df.equals(expected_result))

    def test_assign_actually_mutates_df(self):
        """assign_hed_ids_section must write IDs back into the original DataFrame."""
        df = pd.DataFrame({"hedId": ["", "", ""], "label": ["A", "B", "C"]})
        assign_hed_ids_section(df, {1, 2, 3})
        # All rows should now have a non-empty hedId
        self.assertTrue(all(df["hedId"].str.startswith("HED_")), "IDs were not written into the DataFrame")

    def test_assign_preserves_existing_ids(self):
        """assign_hed_ids_section must not overwrite rows that already have an ID."""
        df = pd.DataFrame({"hedId": ["HED_0000005", "", "HED_0000010"], "label": ["A", "B", "C"]})
        assign_hed_ids_section(df, {1, 2, 3, 4, 5, 10})
        self.assertEqual(df.loc[0, "hedId"], "HED_0000005")
        self.assertEqual(df.loc[2, "hedId"], "HED_0000010")
        self.assertTrue(df.loc[1, "hedId"].startswith("HED_"))


class TestUpdateDataframes(unittest.TestCase):
    def test_update_dataframes_from_schema(self):
        # Use matching schema + dataframes so the ID verification passes
        schema = load_schema_version("8.4.0")
        schema_dataframes = schema.get_as_dataframes()
        # Add a test column and ensure it stays around
        fixed_value = "test_column_value"
        for _key, df in schema_dataframes.items():
            df["test_column"] = fixed_value

        updated_dataframes = update_dataframes_from_schema(schema_dataframes, schema)

        for key, df in updated_dataframes.items():
            if key not in constants.DF_EXTRAS:
                self.assertTrue((df["test_column"] == fixed_value).all())

    def test_conflict_detected(self):
        """Bug #1 regression: verify HedFileError IS raised when a hedId in the dataframe mismatches the schema."""
        schema = load_schema_version("8.4.0")
        schema_dataframes = schema.get_as_dataframes()

        # Corrupt a hedId in the Tag dataframe so it mismatches the schema
        tag_df = schema_dataframes[constants.TAG_KEY]
        # Change the first non-empty hedId to an out-of-range value
        non_empty_mask = tag_df["hedId"].str.startswith("HED_", na=False)
        first_idx = tag_df.index[non_empty_mask][0]
        schema_dataframes[constants.TAG_KEY].loc[first_idx, "hedId"] = "HED_0000000"

        with self.assertRaises(HedFileError) as ctx:
            update_dataframes_from_schema(schema_dataframes, schema)
        self.assertGreater(len(ctx.exception.issues), 0)


if __name__ == "__main__":
    unittest.main()
