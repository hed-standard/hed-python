import unittest;

from hedvalidation import error_reporter


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.error_types = ['bracket', 'row', 'isNumeric', 'required', 'requireChild', 'tilde', 'unique', 'unitClass', 'valid'];

    def test_report_error_type(self):
        for error_type in self.error_types:
            error_report = error_reporter.report_error_type(error_type);
            self.assertIsInstance(error_report, basestring);

if __name__ == '__main__':
    unittest.main();