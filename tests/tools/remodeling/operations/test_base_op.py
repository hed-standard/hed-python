import json
import unittest
from hed.tools.remodeling.operations.base_op import BaseOp


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.params = {
            "command": "test_op",
            "required_parameters": {
                "is_string": str,
                "is_multiple": [str, int, float, list],
                "is_bool": bool,
                "is_list": list
            },
            "optional_parameters": {}
        }
        base_parameters = {
            "is_string": "Condition-variable",
            "is_multiple": ["a", "b", "c"],
            "is_bool": False,
            "is_list": [3, 4, 5]
        }
        cls.json_parms = json.dumps(base_parameters)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        op1 = BaseOp(self.params["command"], self.params["required_parameters"], self.params["optional_parameters"])
        self.assertIsInstance(op1, BaseOp,
                              "constructor should create a BaseOp")
        self.assertIn("is_string", op1.required_params,
                      "constructor required_params should contain an expected value")

    def test_constructor_no_command(self):
        with self.assertRaises(ValueError):
            BaseOp([], self.params["required_parameters"], self.params["optional_parameters"])

    def test_constructor_no_parameters(self):
        op1 = BaseOp("no_parameter_command", [], [])
        self.assertIsInstance(op1, BaseOp, "constructor allows a command with no parameters")

    def test_check_parameters(self):
        parms = json.loads(self.json_parms)
        op1 = BaseOp(self.params["command"], self.params["required_parameters"], self.params["optional_parameters"])
        op1.check_parameters(parms)
        self.assertIsInstance(op1, BaseOp, "constructor should create a BaseOp and list parameter not raise error")

    def test_check_parameters_bad_element(self):
        parms = json.loads(self.json_parms)
        parms["is_multiple"] = {"a":1, "b": 2}
        op1 = BaseOp(self.params["command"], self.params["required_parameters"], self.params["optional_parameters"])
        self.assertIsInstance(op1, BaseOp, "constructor should create a BaseOp and list parameter not raise error")
        with self.assertRaises(TypeError):
            op1.check_parameters(parms)

    def test_parse_commands_missing_required(self):
        op1 = BaseOp(self.params["command"], self.params["required_parameters"], self.params["optional_parameters"])
        parms = json.loads(self.json_parms)
        parms.pop("is_string")
        with self.assertRaises(KeyError):
            op1.check_parameters(parms)


if __name__ == '__main__':
    unittest.main()
