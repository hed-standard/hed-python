from copy import deepcopy
import json
import unittest


class Test(unittest.TestCase):
    """ """

    @classmethod
    def setUpClass(cls):
        cls.sample_data = [
            [33.4228, 2.0084, "80"],
            [36.9395, 0.5, "40"],
            [37.4395, 0.25, "30"],
            [37.6895, 0.4083, "12"],
            [38.0936, 0.0, "2"],
            [38.0979, 0.5, "40"],
            [38.5979, 0.25, "30"],
            [38.8479, 0.3, "11"],
            [39.1435, 0.0, "1"],
            [39.1479, 0.5, "40"],
            [115.6238, 0.25, "30"],
            [115.8738, 0.3083, "12"],
            [116.1782, 0.0, "1"],
            [116.18220000000001, 0.0167, "70"],
            [134.1619, 0.0, "3"],
            [134.16570000000002, 2.0084, "80"],
            [151.7409, 0.5, "40"],
            [152.241, 0.25, "30"],
            [152.491, 0.2, "211"],
            [152.691, 1.05, "221"],
            [347.9184, 0.5, "40"],
            [348.4184, 0.25, "30"],
            [348.6684, 0.4667, "11"],
            [349.1281, 0.0, "1"],
            [349.1351, 0.0167, "70"],
            [366.5138, 0.0, "3"],
            [366.5186, 2.0084, "Stress_post"],
        ]

        cls.sample_columns = ["onset", "duration", "code"]
        cls.existing_sample_columns = ["onset", "duration", "number"]

        cls.numbered_data = [
            [33.4228, 2.0084, "80", "n/a"],
            [36.9395, 0.5, "40", "n/a"],
            [37.4395, 0.25, "30", 1],
            [37.6895, 0.4083, "12", 1],
            [38.0936, 0.0, "2", 1],
            [38.0979, 0.5, "40", "n/a"],
            [38.5979, 0.25, "30", 2],
            [38.8479, 0.3, "11", 2],
            [39.1435, 0.0, "1", 2],
            [39.1479, 0.5, "40", "n/a"],
            [115.6238, 0.25, "30", 3],
            [115.8738, 0.3083, "12", 3],
            [116.1782, 0.0, "1", 3],
            [116.18220000000001, 0.0167, "70", "n/a"],
            [134.1619, 0.0, "3", "n/a"],
            [134.16570000000002, 2.0084, "80", "n/a"],
            [151.7409, 0.5, "40", "n/a"],
            [152.241, 0.25, "30", 4],
            [152.491, 0.2, "211", 4],
            [152.691, 1.05, "221", 4],
            [347.9184, 0.5, "40", "n/a"],
            [348.4184, 0.25, "30", 5],
            [348.6684, 0.4667, "11", 5],
            [349.1281, 0.0, "1", 5],
            [349.1351, 0.0167, "70", "n/a"],
            [366.5138, 0.0, "3", "n/a"],
            [366.5186, 2.0084, "Stress_post", "n/a"],
        ]

        cls.numbered_columns = ["onset", "duration", "code", "number"]

        cls.overwritten_data = [
            [33.4228, 2.0084, "n/a"],
            [36.9395, 0.5, "n/a"],
            [37.4395, 0.25, 1],
            [37.6895, 0.4083, 1],
            [38.0936, 0.0, 1],
            [38.0979, 0.5, "n/a"],
            [38.5979, 0.25, 2],
            [38.8479, 0.3, 2],
            [39.1435, 0.0, 2],
            [39.1479, 0.5, "n/a"],
            [115.6238, 0.25, 3],
            [115.8738, 0.3083, 3],
            [116.1782, 0.0, 3],
            [116.18220000000001, 0.0167, "n/a"],
            [134.1619, 0.0, "n/a"],
            [134.16570000000002, 2.0084, "n/a"],
            [151.7409, 0.5, "n/a"],
            [152.241, 0.25, 4],
            [152.491, 0.2, 4],
            [152.691, 1.05, 4],
            [347.9184, 0.5, "n/a"],
            [348.4184, 0.25, 5],
            [348.6684, 0.4667, 5],
            [349.1281, 0.0, 5],
            [349.1351, 0.0167, "n/a"],
            [366.5138, 0.0, "n/a"],
            [366.5186, 2.0084, "n/a"],
        ]

        base_parameters = {
            "number_column_name": "number",
            "source_column": "code",
            "start": {"values": ["40"], "inclusion": "exclude"},
            "stop": {"values": ["40", "70"], "inclusion": "exclude"},
        }

        overwrite_false_parameters = deepcopy(base_parameters)
        overwrite_false_parameters["overwrite"] = False
        overwrite_false_parameters["source_column"] = "number"

        overwrite_true_parms = deepcopy(base_parameters)
        overwrite_true_parms["overwrite"] = True
        overwrite_true_parms["source_column"] = "number"

        missing_startstop_parms = deepcopy(base_parameters)
        missing_startstop_parms["start"] = {"values": ["40"]}

        wrong_startstop_parms = deepcopy(base_parameters)
        wrong_startstop_parms["stop"]["column"] = "number"

        wrong_startstop_type_parms = deepcopy(base_parameters)
        wrong_startstop_type_parms["start"]["values"] = "40"

        wrong_inclusion_parms = deepcopy(base_parameters)
        wrong_inclusion_parms["stop"]["inclusion"] = "exclusive"

        missing_startstop_value_parms = deepcopy(base_parameters)
        missing_startstop_value_parms["start"]["values"] = ["40", "20"]

        cls.json_parms = json.dumps(base_parameters)
        cls.json_overwrite_false_parms = json.dumps(overwrite_false_parameters)
        cls.json_overwrite_true_parms = json.dumps(overwrite_true_parms)
        cls.json_missing_startstop_parms = json.dumps(missing_startstop_parms)
        cls.json_wrong_startstop_parms = json.dumps(wrong_startstop_parms)
        cls.json_wrong_startstop_type_parms = json.dumps(wrong_startstop_type_parms)
        cls.json_wrong_inclusion_parms = json.dumps(wrong_inclusion_parms)
        cls.json_missing_startstop_value_parms = json.dumps(missing_startstop_value_parms)

        cls.dispatcher = None
        cls.file_name = None

    @classmethod
    def tearDownClass(cls):
        pass

    # test working
    def test_number_groups_new_column(self):
        pass
