import os
import unittest

from hed.tools import BidsDataset
from hed.errors import get_printable_issue_string


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "hed-examples/datasets"))
        cls.fail_count = []

        # Check if the required directory exists
        if not os.path.exists(cls.base_dir):
            cls.skip_tests = True
            # Only print warning if not in CI environment to avoid interference
            if not os.environ.get("GITHUB_ACTIONS"):
                print(f"WARNING: Test directory not found: {cls.base_dir}")
                print("To run BIDS validation tests, copy hed-examples repository content to spec_tests/hed-examples/")
        else:
            cls.skip_tests = False

    @classmethod
    def tearDownClass(cls):
        pass

    def test_validation(self):
        if hasattr(self, "skip_tests") and self.skip_tests:
            self.skipTest("hed-examples directory not found. Copy submodule content to run this test.")

        base_dir = self.base_dir
        for directory in os.listdir(base_dir):
            dataset_path = os.path.join(base_dir, directory)
            if not os.path.isdir(dataset_path):
                continue

            bids_data = BidsDataset(dataset_path)
            issues = bids_data.validate(check_for_warnings=False)
            if issues:
                self.fail_count.append((directory, issues))
        print(f"{len(self.fail_count)} tests got an unexpected result")
        print(
            "\n".join(
                get_printable_issue_string(issue, f"Errors in directory: {title}", skip_filename=False)
                for title, issue in self.fail_count
            )
        )
        self.assertEqual(0, len(self.fail_count))


if __name__ == "__main__":
    unittest.main()
