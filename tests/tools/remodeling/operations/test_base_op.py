import json
import unittest
from hed.tools.remodeling.operations.base_op import BaseOp


class TestOp(BaseOp):
    PARAMS = {
        "operation": "test_op",
        "required_parameters": {
            "op_name": str,
            "skip_columns": list,
            "keep_all": bool,
        },
        "optional_parameters": {
            "keep_columns": list
        }
    }

    def __init__(self, parameters):
        super().__init__(self.PARAMS["operation"], self.PARAMS["required_parameters"],
                         self.PARAMS["optional_parameters"])
        self.check_parameters(parameters)

    def do_op(self, dispatcher, df, name, sidecar=None):
        return df


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.params = {
            "operation": "test_op",
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
        op1 = BaseOp(self.params["operation"], self.params["required_parameters"], self.params["optional_parameters"])
        self.assertIsInstance(op1, BaseOp,
                              "constructor should create a BaseOp")
        self.assertIn("is_string", op1.required_params,
                      "constructor required_params should contain an expected value")

    def test_constructor_no_operation(self):
        with self.assertRaises(ValueError) as context:
            BaseOp([], self.params["required_parameters"], self.params["optional_parameters"])
        self.assertEqual(context.exception.args[0], 'OpMustHaveOperation')

    def test_constructor_no_parameters(self):
        op1 = BaseOp("no_parameter_operation", [], [])
        self.assertIsInstance(op1, BaseOp, "constructor allows a operation with no parameters")

    def test_check_parameters(self):
        parms = json.loads(self.json_parms)
        op1 = BaseOp(self.params["operation"], self.params["required_parameters"], self.params["optional_parameters"])
        op1.check_parameters(parms)
        self.assertIsInstance(op1, BaseOp, "constructor should create a BaseOp and list parameter not raise error")

    def test_check_parameters_bad_element(self):
        parms = json.loads(self.json_parms)
        parms["is_multiple"] = {"a": 1, "b": 2}
        op1 = BaseOp(self.params["operation"], self.params["required_parameters"], self.params["optional_parameters"])
        self.assertIsInstance(op1, BaseOp, "constructor should create a BaseOp and list parameter not raise error")
        with self.assertRaises(TypeError) as context:
            op1.check_parameters(parms)
        self.assertEqual(context.exception.args[0], 'BadType')

    def test_parse_operations_missing_required(self):
        op1 = BaseOp(self.params["operation"], self.params["required_parameters"], self.params["optional_parameters"])
        parms = json.loads(self.json_parms)
        parms.pop("is_string")
        with self.assertRaises(KeyError) as context:
            op1.check_parameters(parms)
        self.assertEqual(context.exception.args[0], 'MissingRequiredParameters')

    def test_check_parameters_test(self):
        params1 = {"op_name": "test_op", "skip_columns": ["onset", "duration"], "keep_all": True, "junk": "bad_parm"}
        with self.assertRaises(KeyError) as context1:
            TestOp(params1)
        self.assertEqual(context1.exception.args[0], 'BadParameter')
        params2 = {"op_name": "test_op", "skip_columns": ["onset", "duration"], "keep_all": "true"}
        with self.assertRaises(TypeError) as context2:
            TestOp(params2)
        self.assertEqual(context2.exception.args[0], 'BadType')


if __name__ == '__main__':
    unittest.main()
