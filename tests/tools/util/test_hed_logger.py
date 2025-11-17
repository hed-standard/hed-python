import unittest
from hed.tools.util.hed_logger import HedLogger


class Test(unittest.TestCase):

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
        status.add("bacon", "Test message 3", level="ERROR")
        status.add("olives", "Test message 4", level="ERROR")
        stuff1 = status.get_log_string()
        self.assertGreater(len(stuff1), 0, "get_log should contain messages.")
        self.assertEqual(stuff1.count("\n"), 7, "get_log should output right number of lines.")
        status.add("banana", "Test message 5")
        stuff2 = status.get_log_string()
        self.assertEqual(stuff2.count("\n"), 9, "get_log should output right number of lines.")
        stuff3 = status.get_log_string(level="ERROR")
        self.assertEqual(stuff3.count("\n"), 7, "get_log should output right number of lines when level is given.")

    def test_get_log(self):
        status = HedLogger(name="help")
        status.add("baloney", "Test message 1", level="ERROR")
        status.add("baloney", "Test message 2", level="ERROR")
        status.add("bacon", "Test message 3", level="ERROR")
        status.add("olives", "Test message 4", level="ERROR")
        baloney = status.get_log("baloney")
        self.assertIsInstance(baloney, list)
        self.assertEqual(len(baloney), 2)
        oranges = status.get_log("oranges")
        self.assertIsInstance(baloney, list)
        self.assertEqual(len(oranges), 0)


if __name__ == "__main__":
    unittest.main()
