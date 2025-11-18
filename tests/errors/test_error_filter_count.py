import unittest
from hed.errors.error_reporter import ErrorHandler


class TestFilterIssuesByCount(unittest.TestCase):

    def test_empty_issues_list(self):
        issues = []
        result, result_counts = ErrorHandler.filter_issues_by_count(issues, 2)
        self.assertEqual(result, [])

    def test_all_below_limit(self):
        issues = [{"code": "A"}, {"code": "B"}, {"code": "A"}]
        counts = {"A": 2, "B": 1}
        result, result_counts = ErrorHandler.filter_issues_by_count(issues, 2)
        self.assertEqual(result, issues)
        self.assertEqual(counts, result_counts)

    def test_some_above_limit(self):
        issues = [{"code": "A"}, {"code": "A"}, {"code": "A"}, {"code": "B"}, {"code": "B"}, {"code": "C"}]
        counts = {"A": 3, "B": 2, "C": 1}
        expected = [{"code": "A"}, {"code": "A"}, {"code": "B"}, {"code": "B"}, {"code": "C"}]
        result, result_counts = ErrorHandler.filter_issues_by_count(issues, 2)
        self.assertEqual(result, expected)
        self.assertEqual(counts, result_counts)

    def test_zero_limit(self):
        issues = [{"code": "A"}, {"code": "B"}, {"code": "A"}]
        counts = {"A": 2, "B": 1}
        result, result_counts = ErrorHandler.filter_issues_by_count(issues, 0)
        self.assertEqual(result, [])
        self.assertEqual(counts, result_counts)

    def test_single_issue_limit(self):
        issues = [{"code": "X"}, {"code": "X"}, {"code": "Y"}, {"code": "Y"}, {"code": "Z"}]
        counts = {"X": 2, "Y": 2, "Z": 1}
        expected = [{"code": "X"}, {"code": "Y"}, {"code": "Z"}]
        result, result_counts = ErrorHandler.filter_issues_by_count(issues, 1)
        self.assertEqual(result, expected)
        self.assertEqual(counts, result_counts)

    def test_non_consecutive_codes(self):
        issues = [{"code": "A"}, {"code": "B"}, {"code": "A"}, {"code": "B"}, {"code": "A"}, {"code": "B"}]
        counts = {"A": 3, "B": 3}
        expected = [{"code": "A"}, {"code": "B"}, {"code": "A"}, {"code": "B"}]
        result, result_counts = ErrorHandler.filter_issues_by_count(issues, 2)
        self.assertEqual(result, expected)
        self.assertEqual(counts, result_counts)

    def test_by_file_false_default_behavior(self):
        issues = [
            {"code": "A", "ec_filename": "file1"},
            {"code": "A", "ec_filename": "file1"},
            {"code": "A", "ec_filename": "file2"},
        ]
        counts = {"A": 3}
        result, result_counts = ErrorHandler.filter_issues_by_count(issues, 2)
        expected = [{"code": "A", "ec_filename": "file1"}, {"code": "A", "ec_filename": "file1"}]
        self.assertEqual(result, expected)
        self.assertEqual(counts, result_counts)

    def test_by_file_true_grouping(self):
        issues = [
            {"code": "A", "ec_filename": "file1"},
            {"code": "A", "ec_filename": "file1"},
            {"code": "A", "ec_filename": "file2"},
            {"code": "A", "ec_filename": "file2"},
            {"code": "A", "ec_filename": "file2"},
        ]
        counts = {"A": 5}
        result, result_counts = ErrorHandler.filter_issues_by_count(issues, 2, by_file=True)
        expected = [
            {"code": "A", "ec_filename": "file1"},
            {"code": "A", "ec_filename": "file1"},
            {"code": "A", "ec_filename": "file2"},
            {"code": "A", "ec_filename": "file2"},
        ]
        self.assertEqual(result, expected)
        self.assertEqual(counts, result_counts)

    def test_mixed_codes_and_files(self):
        issues = [
            {"code": "X", "ec_filename": "file1"},
            {"code": "X", "ec_filename": "file1"},
            {"code": "X", "ec_filename": "file2"},
            {"code": "Y", "ec_filename": "file1"},
            {"code": "Y", "ec_filename": "file2"},
            {"code": "Y", "ec_filename": "file2"},
        ]
        counts = {"X": 3, "Y": 3}
        result, result_counts = ErrorHandler.filter_issues_by_count(issues, 1, by_file=True)
        expected = [
            {"code": "X", "ec_filename": "file1"},
            {"code": "X", "ec_filename": "file2"},
            {"code": "Y", "ec_filename": "file1"},
            {"code": "Y", "ec_filename": "file2"},
        ]
        self.assertEqual(result, expected)
        self.assertEqual(counts, result_counts)

    def test_missing_ec_filename_with_by_file(self):
        issues = [
            {"code": "A"},  # No 'ec_filename'
            {"code": "A"},  # No 'ec_filename'
            {"code": "A", "ec_filename": "file1"},
            {"code": "A", "ec_filename": "file1"},
        ]
        counts = {"A": 4}
        result, result_counts = ErrorHandler.filter_issues_by_count(issues, 1, by_file=True)
        expected = [
            {"code": "A"},  # First from default ('' file group)
            {"code": "A", "ec_filename": "file1"},  # First from file1 group
        ]
        self.assertEqual(result, expected)
        self.assertEqual(counts, result_counts)


class TestAggregateCodeCounts(unittest.TestCase):

    def test_empty_input(self):
        input_data = {}
        expected_output = {}
        self.assertEqual(ErrorHandler.aggregate_code_counts(input_data), expected_output)

    def test_single_file_single_code(self):
        input_data = {"file1.txt": {"A": 5}}
        expected_output = {"A": 5}
        self.assertEqual(ErrorHandler.aggregate_code_counts(input_data), expected_output)

    def test_single_file_multiple_codes(self):
        input_data = {"file1.txt": {"A": 1, "B": 2, "C": 3}}
        expected_output = {"A": 1, "B": 2, "C": 3}
        self.assertEqual(ErrorHandler.aggregate_code_counts(input_data), expected_output)

    def test_multiple_files_overlapping_codes(self):
        input_data = {"file1.txt": {"A": 2, "B": 1}, "file2.txt": {"A": 3, "C": 4}, "file3.txt": {"B": 2, "C": 1}}
        expected_output = {"A": 5, "B": 3, "C": 5}
        self.assertEqual(ErrorHandler.aggregate_code_counts(input_data), expected_output)

    def test_multiple_files_non_overlapping_codes(self):
        input_data = {"file1.txt": {"A": 2}, "file2.txt": {"B": 3}, "file3.txt": {"C": 4}}
        expected_output = {"A": 2, "B": 3, "C": 4}
        self.assertEqual(ErrorHandler.aggregate_code_counts(input_data), expected_output)

    def test_zero_counts(self):
        input_data = {"file1.txt": {"A": 0}, "file2.txt": {"A": 2}}
        expected_output = {"A": 2}
        self.assertEqual(ErrorHandler.aggregate_code_counts(input_data), expected_output)


if __name__ == "__main__":
    unittest.main()
