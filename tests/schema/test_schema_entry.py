import unittest
from hed.schema.hed_schema_entry import HedTagEntry
class MockEntry:
    def __init__(self, attributes, parent=None):
        self.attributes = attributes
        self.takes_value_child_entry = False
        self._parent_tag = parent

    _check_inherited_attribute = HedTagEntry._check_inherited_attribute
    _check_inherited_attribute_internal = HedTagEntry._check_inherited_attribute_internal


class TestMockEntry(unittest.TestCase):

    def setUp(self):
        # Test setup
        self.root_entry = MockEntry({'color': 'blue', 'size': 'large', 'is_round': False})
        self.child_entry1 = MockEntry({'color': 'green', 'shape': 'circle', 'is_round': True}, parent=self.root_entry)
        self.child_entry2 = MockEntry({'size': 'medium', 'material': 'wood', 'number': 5}, parent=self.child_entry1)

    def test_check_inherited_attribute(self):
        # Test attribute present in the current entry but not in parents
        self.assertEqual(self.child_entry2._check_inherited_attribute('material', return_value=True, return_union=False), 'wood')

        # Test attribute present in the parent but not in the current entry
        self.assertEqual(self.child_entry2._check_inherited_attribute('color', return_value=True, return_union=False), 'green')

        # Test attribute present in the parent but not in the current entry, treat_as_string=True
        self.assertEqual(self.child_entry2._check_inherited_attribute('color', return_value=True, return_union=True), 'green,blue')

        # Test attribute present in the current entry and in parents, treat_as_string=True
        self.assertEqual(self.child_entry2._check_inherited_attribute('size', return_value=True, return_union=True), 'medium,large')

        # Test attribute not present anywhere
        self.assertIsNone(self.child_entry2._check_inherited_attribute('weight', return_value=True, return_union=False))

        # Test attribute present in the current entry but not in parents, no return value
        self.assertTrue(self.child_entry2._check_inherited_attribute('material', return_value=False, return_union=False))

        # Test attribute not present anywhere, no return value
        self.assertFalse(self.child_entry2._check_inherited_attribute('weight', return_value=False, return_union=False))

    def test_check_inherited_attribute_bool(self):
        # Test boolean attribute present in the current entry but not in parents
        self.assertTrue(self.child_entry2._check_inherited_attribute('is_round', return_value=True, return_union=False))

        # Test boolean attribute present in the parent and in the current entry, treat_as_string=True
        with self.assertRaises(TypeError):
            self.child_entry2._check_inherited_attribute('is_round', return_value=True, return_union=True)

    def test_check_inherited_attribute_numeric(self):
        # Test numeric attribute present only in the current entry
        self.assertEqual(self.child_entry2._check_inherited_attribute('number', return_value=True, return_union=False), 5)

        # Test numeric attribute with treat_as_string=True should raise TypeError
        with self.assertRaises(TypeError):
            self.child_entry2._check_inherited_attribute('number', return_value=True, return_union=True)
