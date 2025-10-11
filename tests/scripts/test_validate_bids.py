import os
import io
import unittest
from unittest.mock import patch
from hed.scripts.validate_bids import main


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_root = os.path.realpath(os.path.join(os.path.dirname(__file__), "../data/bids_tests/eeg_ds003645s_hed_demo"))

    def test_main_bids(self):
        arg_list = [self.data_root, "-x", "derivatives", "stimuli"]
        # Suppress all output including logging
        with (
            patch("sys.stdout", new=io.StringIO()),
            patch("sys.stderr", new=io.StringIO()),
            patch("logging.getLogger") as mock_logger,
        ):
            # Configure mock logger to do nothing
            mock_logger.return_value.info.return_value = None
            mock_logger.return_value.debug.return_value = None
            mock_logger.return_value.warning.return_value = None
            mock_logger.return_value.error.return_value = None
            x = main(arg_list)
            self.assertFalse(x)

    def test_main_warnings(self):
        arg_list = [self.data_root, "-x", "derivatives", "stimuli", "-w", "-p", "-s"]
        # Suppress all output including logging
        with (
            patch("sys.stdout", new=io.StringIO()),
            patch("sys.stderr", new=io.StringIO()),
            patch("logging.getLogger") as mock_logger,
        ):
            # Configure mock logger to do nothing
            mock_logger.return_value.info.return_value = None
            mock_logger.return_value.debug.return_value = None
            mock_logger.return_value.warning.return_value = None
            mock_logger.return_value.error.return_value = None
            x = main(arg_list)
            self.assertTrue(x)


if __name__ == "__main__":
    unittest.main()
