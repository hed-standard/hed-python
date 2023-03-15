import os
import unittest

from hed import schema as hedschema
from hed.models import Sidecar, TabularInput, HedString, HedTag, HedGroup
from hed.tools import assemble_hed
from hed.tools.analysis.temporal_event import TemporalEvent


# noinspection PyBroadException
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../../data/schema_tests/HED8.1.0.xml'))
        cls.hed_schema = hedschema.load_schema(schema_path)

    def test_constructor_no_group(self):
        test1 = HedString("(Onset, Def/Blech)", hed_schema=self.hed_schema)
        groups = test1.find_top_level_tags(["onset"], include_groups=1)
        te = TemporalEvent(groups[0], 3, 4.5)
        self.assertEqual(te.start_index, 3)
        self.assertEqual(te.start_time, 4.5)
        self.assertFalse(te.internal_group)
        
    def test_constructor_group(self):
        test1 = HedString("(Onset, (Label/Apple, Blue), Def/Blech)", hed_schema=self.hed_schema)
        groups = test1.find_top_level_tags(["onset"], include_groups=1)
        te = TemporalEvent(groups[0], 3, 4.5)
        self.assertEqual(te.start_index, 3)
        self.assertEqual(te.start_time, 4.5)
        self.assertTrue(te.internal_group)
        self.assertIsInstance(te.internal_group, HedGroup)


if __name__ == '__main__':
    unittest.main()
