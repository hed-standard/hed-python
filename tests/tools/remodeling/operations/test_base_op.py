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

if __name__ == '__main__':
    unittest.main()
