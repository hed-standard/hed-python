import pandas as pd
import unittest
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.util.schema_util import flatten_schema


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_flatten_schema(self):
        hed_schema = load_schema_version("8.1.0")
        df = flatten_schema(hed_schema, skip_non_tag=True)
        # df.to_csv("h:/Version_3_column.tsv", sep='\t', index=None)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df.columns), 3)
        self.assertEqual(len(df.index), 1037)


if __name__ == "__main__":
    unittest.main()
