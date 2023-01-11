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
        super().__init__(self.PARAMS, parameters)

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
        cls.json_parameters = json.dumps(base_parameters)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        parameters = json.loads(self.json_parameters)
        op1 = BaseOp(self.params, parameters)
        self.assertIsInstance(op1, BaseOp, "constructor should create a BaseOp")
        self.assertIn("is_string", op1.required_params,
                      "constructor required_params should contain an expected value")

    def test_constructor_no_operation(self):
        with self.assertRaises(ValueError) as context:
            BaseOp({}, {})
        self.assertEqual(context.exception.args[0], 'OpMustHaveOperation')

    def test_constructor_no_parameters(self):
        op1 = BaseOp({"operation": "no_parameter_operation"}, {})
        self.assertIsInstance(op1, BaseOp, "constructor allows a operation with no parameters")

    def test_check_parameters_bad_element(self):
        parameters = json.loads(self.json_parameters)
        parameters["is_multiple"] = {"a": 1, "b": 2}
        with self.assertRaises(TypeError) as context:
            BaseOp(self.params, parameters)
        self.assertEqual(context.exception.args[0], 'BadType')

    def test_parse_operations_missing_required(self):
        parameters = json.loads(self.json_parameters)
        parameters.pop("is_string")
        with self.assertRaises(KeyError) as context:
            BaseOp(TestOp.PARAMS, parameters)
        self.assertEqual(context.exception.args[0], 'MissingRequiredParameters')

    def test_check_parameters_test(self):
        parameters1 = {"op_name": "test", "skip_columns": ["onset", "duration"], "keep_all": True, "junk": "bad_parm"}
        with self.assertRaises(KeyError) as context1:
            BaseOp(TestOp.PARAMS, parameters1)
        self.assertEqual(context1.exception.args[0], 'BadParameter')
        parameters2 = {"op_name": "test", "skip_columns": ["onset", "duration"], "keep_all": "true"}
        with self.assertRaises(TypeError) as context2:
            TestOp(parameters2)
        self.assertEqual(context2.exception.args[0], 'BadType')


if __name__ == '__main__':
    unittest.main()
