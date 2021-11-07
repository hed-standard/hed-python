import unittest
from tests.test_web_base import TestWebBase


class Test(TestWebBase):

    def test_create_column_selections(self):
        from hedweb.columns import create_column_selections
        form_dict = {'column_1_use': 'on', 'column_1_name': 'event_type', 'column_1_category': 'on',
                     'column_2_name': 'event_num',
                     'column_3_use': 'on', 'column_3_name': 'event_test',
                     'column_4_use': 'on', 'column_4_category': 'on',
                     'column_5_use': 'on', 'column_5_name': 'event_type_blech', 'column_5_category': 'on'}
        column_selections = create_column_selections(form_dict)
        self.assertTrue(column_selections['event_type'], 'event_type should be a category column')
        self.assertNotIn('event_num', column_selections, 'event_num not used so should not be in column_selections')
        self.assertFalse(column_selections['event_test'], 'event_test is not a category column')
        self.assertTrue(column_selections['event_type_blech'], 'event_type_blech should be a category column')
        self.assertEqual(len(column_selections.keys()), 3, 'column must have both a _use and a _name')


if __name__ == '__main__':
    unittest.main()
