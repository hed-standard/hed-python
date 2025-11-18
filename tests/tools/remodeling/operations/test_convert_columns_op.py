import unittest


class Test(unittest.TestCase):
    """

    TODO: Test when no factor names and values are given.

    """

    @classmethod
    def setUpClass(cls):
        cls.sample_data = [
            [0.0776, 0.5083, "go", "n/a", 0.565, "correct", "right", "female"],
            [5.5774, 0.5083, "unsuccesful_stop", 0.2, 0.49, "correct", "right", "female"],
            [9.5856, 0.5084, "go", "n/a", 0.45, "correct", "right", "female"],
            [13.5939, 0.5083, "succesful_stop", 0.2, "n/a", "n/a", "n/a", "female"],
            [17.1021, 0.5083, "unsuccesful_stop", 0.25, 0.633, "correct", "left", "male"],
            [21.6103, 0.5083, "go", "n/a", 0.443, "correct", "left", "male"],
        ]
        cls.factored = [
            [0.0776, 0.5083, "go", "n/a", 0.565, "correct", "right", "female", 0, 0],
            [5.5774, 0.5083, "unsuccesful_stop", 0.2, 0.49, "correct", "right", "female", 0, 1],
            [9.5856, 0.5084, "go", "n/a", 0.45, "correct", "right", "female", 0, 0],
            [13.5939, 0.5083, "succesful_stop", 0.2, "n/a", "n/a", "n/a", "female", 1, 0],
            [17.1021, 0.5083, "unsuccesful_stop", 0.25, 0.633, "correct", "left", "male", 0, 1],
            [21.6103, 0.5083, "go", "n/a", 0.443, "correct", "left", "male", 0, 0],
        ]
        cls.sample_columns = [
            "onset",
            "duration",
            "trial_type",
            "stop_signal_delay",
            "response_time",
            "response_accuracy",
            "response_hand",
            "sex",
        ]
        cls.default_factor_columns = ["trial_type.succesful_stop", "trial_type.unsuccesful_stop"]

    def setUp(self):
        self.base_parameters = {"column_names": ["onset", "duration", "response_time"], "convert_to": "int"}

    @classmethod
    def tearDownClass(cls):
        pass


if __name__ == "__main__":
    unittest.main()
