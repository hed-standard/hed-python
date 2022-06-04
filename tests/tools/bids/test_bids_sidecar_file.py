import os
import unittest
from hed.errors import HedFileError
from hed.models.sidecar import Sidecar
from hed.tools.bids.bids_tabular_file import BidsTabularFile
from hed.tools.bids.bids_file import BidsFile
from hed.tools.bids.bids_sidecar_file import BidsSidecarFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.description_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                            '../../data/bids/eeg_ds003654s_hed/dataset_description.json')
        cls.event_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                      '../../data/bids/eeg_ds003654s_hed/sub-002/'
                                      'eeg/sub-002_task-FacePerception_run-1_events.tsv')

        cls.sidecar_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json')
        path_upper = '../../data/bids/eeg_ds003654s_hed_inheritance/task-FacePerception_events.json'
        path_lower2 = '../../data/bids/eeg_ds003654s_hed_inheritance/sub-002/sub-002_task-FacePerception_events.json'
        path_lower3 = '../../data/bids/eeg_ds003654s_hed_inheritance/sub-003/sub-003_task-FacePerception_events.json'
        cls.sidecar_path_upper = os.path.join(os.path.dirname(os.path.realpath(__file__)), path_upper)
        cls.sidecar_path_lower2 = os.path.join(os.path.dirname(os.path.realpath(__file__)), path_lower2)
        cls.sidecar_path_lower3 = os.path.join(os.path.dirname(os.path.realpath(__file__)), path_lower3)

    def test_constructor(self):
        sidecar1 = BidsSidecarFile(self.sidecar_path)
        self.assertEqual(sidecar1.suffix, 'events', "BidsSidecarFile should have correct name_suffix")
        self.assertEqual(sidecar1.ext, '.json', "BidsSidecarFile should have correct ext")
        self.assertEqual(len(sidecar1.entity_dict), 1, "BidsSidecarFile should have right number of entity_dict")
        self.assertFalse(sidecar1.contents)
        self.assertFalse(sidecar1.has_hed)

    def test_bad_constructor(self):
        try:
            json1 = BidsSidecarFile(self.description_path)
        except HedFileError:
            pass
        except Exception:
            self.fail("BidsSidecarFile threw the wrong exception when filename invalid")
        else:
            self.fail("BidsSidecarFile should have thrown a HedFileError when duplicate key")

    def test_bids_sidecar_file_str(self):
        sidecar1 = BidsSidecarFile(self.sidecar_path)
        self.assertTrue(str(sidecar1), "BidsSidecarFile should have a string representation")
        sidecar2 = BidsSidecarFile(self.sidecar_path)
        self.assertTrue(str(sidecar2), "BidsSidecarFile should have a string representation")

    def test_bids_sidecar_file_set_contents(self):
        sidecar1 = BidsSidecarFile(self.sidecar_path)
        self.assertFalse(sidecar1.contents, "BidsSidecarFile should have no contents until set")
        sidecar1.set_contents()
        self.assertIsInstance(sidecar1.contents, Sidecar, "BidsSidecarFile should have dict contents after setting")
        sidecar1.clear_contents()
        self.assertFalse(sidecar1.contents, "BidsSidecarFile should have no contents after clearing")


    def test_get_merged(self):
        side_upper = BidsSidecarFile.get_merged([self.sidecar_path_upper])
        side_lower2 = BidsSidecarFile.get_merged([self.sidecar_path_lower2])
        side_lower3 = BidsSidecarFile.get_merged([self.sidecar_path_lower3])
        side_merged2 = BidsSidecarFile.get_merged([self.sidecar_path_upper, self.sidecar_path_lower2])
        self.assertIsInstance(side_upper, dict, "get_merged produces a dict when one path")
        self.assertIsInstance(side_lower2, dict, "get_merged produces a dict when one path")
        self.assertIsInstance(side_merged2, dict, "get_merged produces a dict when one path")
        self.assertIn('event_type', side_upper, "get_merged upper has key event_type")
        self.assertNotIn('event_type', side_lower2, "get_merged lower does not have event_type")
        self.assertIn('event_type', side_merged2, "get_merged merged has key event_type from upper")
        self.assertIn('rep_lag', side_merged2, "get_merged merged has key rep_lag from lower")
        self.assertEqual(side_merged2['rep_lag']['HED'], side_lower2['rep_lag']['HED'],
                         "get_merged overrode key from lower")

        side_merged3 = BidsSidecarFile.get_merged([self.sidecar_path_upper, self.sidecar_path_lower3])
        self.assertIn('face_type', side_upper, "get_merged upper has key face_type")
        self.assertIn('face_type', side_lower3, "get_merged lower3 has key face_type")
        self.assertIn('face_type', side_merged3, "get_merged merged3 has key face_type")
        self.assertEqual(side_merged3['rep_lag']['HED'], side_lower3['rep_lag']['HED'],
                         "get_merged side_merged3 got rep_lag key from lower")
        self.assertNotEqual(side_merged3['face_type']['HED']['famous_face'],
                            side_upper['face_type']['HED']['famous_face'],
                            "get_merged overrode face_type key with lower has changed")
        self.assertEqual(side_merged3['face_type']['HED']['famous_face'],
                         side_lower3['face_type']['HED']['famous_face'],
                         "get_merged overrode face_type key with lower3 has changed")

    def test_get_merged_empty(self):
        side_dict1 = BidsSidecarFile.get_merged([])
        self.assertFalse(side_dict1, "get_merged is empty if empty list")
        self.assertIsInstance(side_dict1, dict, "get_merged produces dict when empty list")
        side_dict2 = BidsSidecarFile.get_merged(None)
        self.assertFalse(side_dict2, "get_merged is empty if None")
        self.assertIsInstance(side_dict2, dict, "get_merged produces dict when None")

    def test_is_hed(self):
        dict1 = {'a' : 'b', 'c': {'d': 'e'}}
        self.assertFalse(BidsSidecarFile.is_hed(dict1), 'is_hed returns False if no HED or HED_assembled')
        dict2 = {'HED' : 'b', 'c': {'d':'e'}}
        self.assertTrue(BidsSidecarFile.is_hed(dict2), 'is_hed returns True if HED at top level.')
        dict3 = {'HED_assembled': 'b', 'c': {'d':'e'}}
        self.assertTrue(BidsSidecarFile.is_hed(dict3), 'is_hed returns True if HED_assembled at top level.')
        dict4 = {'a' : 'b', 'c': {'d':'HED'}}
        self.assertFalse(BidsSidecarFile.is_hed(dict4),
                         'is_hed returns False if HED at second level is not a key')
        dict5 = {'a' : 'b', 'c': {'d':'HED_assembled'}}
        self.assertFalse(BidsSidecarFile.is_hed(dict5),
                         'is_hed returns False if HED_assembled at second level is not a key')
        dict6 = {'a' : 'b', 'c': {'HED': 'a', 'Levels': {'e':'f'}}}
        self.assertTrue(BidsSidecarFile.is_hed(dict6), 'is_hed returns True if HED key at second level')
        dict7 = {'a' : 'b', 'c': {'HED_assembled': 'a', 'Levels': {'e':'f'}}}
        self.assertTrue(BidsSidecarFile.is_hed(dict7), 'is_hed returns True if HED_assembled key at second level')
        dict8 = {'a': 'b', 'c': {'HED': {'a': 'b'}, 'Levels': {'e': 'f'}}}
        self.assertTrue(BidsSidecarFile.is_hed(dict8), 'is_hed returns True if HED key at second level')
        dict9 = {'a': 'b', 'c': {'HED_assembled': {'a': 'b'}, 'Levels': {'e': 'f'}}}
        self.assertTrue(BidsSidecarFile.is_hed(dict9), 'is_hed returns True if HED_assembled key at second level')
        dict10 = {'a': 'b', 'c': {'d': {'f': {'HED': 'g'}}}}
        self.assertFalse(BidsSidecarFile.is_hed(dict10), 'is_hed returns False if HED key at third level')
        dict11 = {'a': 'b', 'c': {'d': {'f': {'HED_assembled': 'g'}}}}
        self.assertFalse(BidsSidecarFile.is_hed(dict11), 'is_hed returns False if HED_assembled key at third level')


    def test_is_sidecar_for(self):
        sidecar1 = BidsSidecarFile(self.sidecar_path)
        events1 = BidsTabularFile(self.event_path)
        self.assertTrue(sidecar1.is_sidecar_for(events1))

        the_path = '/d/base/sub-01/ses-test/func/sub-01_ses-test_task-overt_run-2_bold.nfti'
        bids = BidsFile(the_path)
        other = BidsSidecarFile('/d/base/task-overt_run-2_bold.json')
        self.assertTrue(other.is_sidecar_for(bids), "is_a_parent returns true if parent at top level")
        other1 = BidsSidecarFile('/d/base1/task-overt_run-2_bold.json')
        self.assertFalse(other1.is_sidecar_for(bids), "is_a_parent returns false if directories don't match")
        other2 = BidsSidecarFile('/d/base/task-overt_run-3_bold.json')
        self.assertFalse(other2.is_sidecar_for(bids), "is_a_parent returns false if entity_dict don't match")
        other3 = BidsSidecarFile('/d/base/sub-01/sub-01_task-overt_bold.json')
        self.assertTrue(other3.is_sidecar_for(bids), "is_a_parent returns true if entity_dict  match")
        other4 = BidsSidecarFile('/d/base/sub-01/sub-01_task-overt_events.json')
        self.assertFalse(other4.is_sidecar_for(bids), "is_a_parent returns false if suffixes don't match")
        other5 = BidsSidecarFile('/d/base/sub-01/ses-test/func/temp/sub-01_ses-test_task-overt_run-2_bold.json')
        self.assertFalse(other5.is_sidecar_for(bids), "is_a_parent returns false for child even if entity_dict match")

    def test_set_contents(self):
        sidecar1 = BidsSidecarFile(self.sidecar_path)
        self.assertFalse(sidecar1.contents, "set_contents before has no contents")
        self.assertFalse(sidecar1.has_hed, "set_contents before has_hed false")
        sidecar1.set_contents()
        self.assertIsInstance(sidecar1.contents, Sidecar, "set_contents creates a sidecar on setcontents")
        self.assertTrue(sidecar1.has_hed, "set_contents before has_hed false")
        a = sidecar1.contents
        sidecar1.set_contents({'HED': 'xyz'})
        self.assertIs(a, sidecar1.contents, 'By default, existing contents are not overwritten.')


if __name__ == '__main__':
    unittest.main()
