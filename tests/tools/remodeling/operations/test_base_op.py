import json
import unittest
from hed.tools.remodeling.operations.base_op import BaseOp


class TestOp(BaseOp):
    NAME = "test"
    PARAMS = {
        "type": "object",
        "properties": {"column_name": {"type": "string"}},
        "required": ["column_name"],
        "additionalProperties": False,
    }

    def do_op(self, dispatcher, df, name, sidecar=None):
        return df

    @staticmethod
    def validate_input_data(parameters):
        return []


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        base_parameters = {"column_name": "a_descriptive_name"}
        cls.json_parameters = json.dumps(base_parameters)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        parameters = json.loads(self.json_parameters)
        test_instantiate = TestOp(parameters)
        self.assertDictEqual(test_instantiate.parameters, parameters)

    def test_constructor_no_name(self):
        class TestOpNoName(BaseOp):
            PARAMS = {
                "type": "object",
                "properties": {"column_name": {"type": "string"}},
                "required": ["column_name"],
                "additionalProperties": False,
            }

            def do_op(self, dispatcher, df, name, sidecar=None):
                return df

        with self.assertRaises(TypeError):
            TestOpNoName({})


if __name__ == "__main__":
    unittest.main()
