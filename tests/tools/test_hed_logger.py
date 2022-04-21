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

    def test_get_log_string(self):
        status = HedLogger()
        status.add("baloney", "Test message 1", level="ERROR")
        status.add("baloney", "Test message 2")
        stuff1 = status.get_log_string()
        self.assertGreater(len(stuff1), 0, "get_log should contain messages.")
        self.assertEqual(stuff1.count('\n'), 3, "get_log should output right number of lines.")
        status.add("banana", "")
        stuff2 = status.get_log_string(level="ERROR")
        self.assertEqual(stuff2.count('\n'), 3, "get_log should output right number of lines when level is given.")

    def test_print_log(self):
        status = HedLogger()
        with mock.patch('sys.stdout', new=StringIO()) as fake_out1:
            self.assertIsInstance(fake_out1, StringIO, "Mock creates a StringIO")
            status.add("baloney", "Test message 1", level="ERROR", also_print=True)
            status.add("baloney", "Test message 2", also_print=True)
            stuff1 = fake_out1.getvalue()
            self.assertGreater(len(stuff1), 0, "HedLogger should print messages if also_print is True")
            self.assertEqual(stuff1.count('\n'), 2,
                             "HedLogger should output right number of lines if also_print is True")

        with mock.patch('sys.stdout', new=StringIO()) as fake_out2:
            self.assertIsInstance(fake_out2, StringIO, "Mock creates a StringIO")
            status.print_log()
            stuff2 = fake_out2.getvalue()
            self.assertGreater(len(stuff2), 0, "HedLogger should print messages if also_print is True")
            self.assertEqual(stuff2.count('\n'), 3,
                             "HedLogger should output right number of lines if also_print is True")

        with mock.patch('sys.stdout', new=StringIO()) as fake_out3:
            self.assertIsInstance(fake_out3, StringIO, "Mock creates a StringIO")
            status.print_log(level="ERROR")
            stuff3 = fake_out3.getvalue()
            self.assertGreater(len(stuff3), 0, "HedLogger should print messages if also_print is True")
            self.assertEqual(stuff3.count('\n'), 2,
                             "HedLogger should output right number of lines if also_print is True")


if __name__ == '__main__':
    unittest.main()
