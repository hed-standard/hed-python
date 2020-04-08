import unittest
from hedvalidation import warning_reporter


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.warning_types = ['cap', 'required', 'unitClass']

    def test_report_warning_type(self):
        for warning_type in self.warning_types:
            warning_report = warning_reporter.report_warning_type(warning_type)
            self.assertIsInstance(warning_report, str)

if __name__ == '__main__':
    unittest.main()