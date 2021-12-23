import unittest
from io import StringIO
from unittest import mock
from hed.tools.hed_logger import HedLogger


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp = ""

    def test_hed_logger_constructor(self):
        status = HedLogger()
        self.assertIsInstance(status, HedLogger, "HED logger creates")
        keys = status.get_log_keys()
        self.assertFalse(keys, "The logger should have no keys when constructed")

    def test_add_get(self):
        status = HedLogger()
        status.add("baloney", "Test message 1")
        status.add("baloney", "Test message 2")
        keys = status.get_log_keys()
        self.assertEqual(len(keys), 1, "It should have one key if only messages for same key")
        baloney_log = status.get_log("baloney")
        self.assertEqual(len(baloney_log), 2, "It should have the right number of ")

    def test_get_keys(self):
        status = HedLogger()
        status.add("baloney", "Test message")
        keys = status.get_log_keys()
        self.assertEqual(len(keys), 1, "It should have one key after one message")
        self.assertEqual(keys[0], "baloney", "It should have the correct key after insertion")

    def test_print_log(self):
        status = HedLogger()
        status.add("baloney", "Test message 1", also_print=True)
        status.add("baloney", "Test message 2", also_print=True)
        with mock.patch('sys.stdout', new=StringIO()) as fake_out:
            status.add("baloney", "Test message 3", also_print=True)
            status.add("baloney", "Test message 4", also_print=True)


if __name__ == '__main__':
    unittest.main()
