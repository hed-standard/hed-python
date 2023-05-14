import json
import unittest
from hed.tools.analysis.tabular_column_name_summary import TabularColumnNameSummary


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.columns1 = ['a', 'b', 'c']
        cls.columns2 = ['onset', 'duration']
        cls.columns3 = ['a', 'b', 'c', 'd', 'e']
        cls.columns4 = ['a', 'b', 'd']

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        column_summary1 = TabularColumnNameSummary(name='Dataset')
        self.assertIsInstance(column_summary1, TabularColumnNameSummary)
        self.assertEqual(column_summary1.name, 'Dataset')
        self.assertFalse(column_summary1.file_dict)
        self.assertFalse(column_summary1.unique_headers)
        column_summary2 = TabularColumnNameSummary()
        self.assertIsInstance(column_summary2, TabularColumnNameSummary)

    def test_update(self):
        column_summary = TabularColumnNameSummary()
        column_summary.update('run-01', self.columns1)
        column_summary.update('run-02', self.columns1)
        self.assertEqual(len(column_summary.unique_headers), 1)
        self.assertEqual(len(column_summary.file_dict), 2)
        column_summary.update('run-03', self.columns2)
        column_summary.update('run-04', self.columns3)
        self.assertEqual(len(column_summary.unique_headers), 3)
        self.assertEqual(len(column_summary.file_dict), 4)

        with self.assertRaises(ValueError) as context:
            column_summary.update('run-02', self.columns3)
        self.assertEqual(context.exception.args[0], "FileHasChangedColumnNames")

    def test_update_headers(self):
        column_summary = TabularColumnNameSummary()
        pos1 = column_summary.update_headers(self.columns1)
        self.assertEqual(pos1, 0)
        pos2 = column_summary.update_headers(self.columns1)
        self.assertEqual(pos2, 0)
        pos3 = column_summary.update_headers(self.columns2)
        self.assertEqual(pos3, 1)

    def test_get_summary(self):
        column_summary = TabularColumnNameSummary('Dataset')
        column_summary.update('run-01', self.columns1)
        column_summary.update('run-02', self.columns1)
        summary1 = column_summary.get_summary()
        column_summary.update('run-03', self.columns2)
        column_summary.update('run-04', self.columns3)
        summary2 = column_summary.get_summary()
        self.assertIsInstance(summary2, dict)
        summary3 = column_summary.get_summary(as_json=True)
        self.assertIsInstance(summary3, str)
        self.assertIsInstance(json.loads(summary3), dict)


if __name__ == '__main__':
    unittest.main()
