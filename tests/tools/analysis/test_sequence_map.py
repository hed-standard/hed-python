import unittest
import os
from hed.tools.analysis.sequence_map import SequenceMap


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # curation_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/other_tests')
        base_path = ""
        cls.events_path = os.path.realpath(
            base_path + "/sub-01/ses-01/eeg/sub-01_ses-01_task-DriveRandomSound_run-1_events.tsv"
        )

    def test_constructor(self):
        codes1 = [
            "1111",
            "1112",
            "1121",
            "1122",
            "1131",
            "1132",
            "1141",
            "1142",
            "1311",
            "1312",
            "1321",
            "1322",
            "4210",
            "4220",
            "4230",
            "4311",
            "4312",
        ]

        smap1 = SequenceMap(codes=codes1)
        self.assertIsInstance(smap1, SequenceMap)
        # df = get_new_dataframe(self.events_path)
        # data = df['value']
        # smap1.update(data)
        # #print(f"{smap1.__str__}")
        # print("to here")

    def test_update(self):
        # codes1 = ['1111', '1121', '1131', '1141', '1311', '1321',
        #          '4210', '4220', '4230', '4311']
        codes1 = ["1111", "1121", "1131", "1141", "1311", "4311"]
        # codes1 = ['1111', '1121', '1131', '1141', '1311']
        smap1 = SequenceMap(codes=codes1)
        self.assertIsInstance(smap1, SequenceMap)
        # df = get_new_dataframe(self.events_path)
        # data = df['value']
        # smap1.update(data)
        # print(f"{smap1.dot_str()}")
        # group_spec = {"stimulus": {"color": "#FFAAAA", "nodes": ["1111", "1121", "1131", "1141", "1311"]}}
        # print(f"{smap1.dot_str(group_spec=group_spec)}")

    def test_str(self):
        pass


if __name__ == "__main__":
    unittest.main()
