import unittest;
from hedvalidation.hed_string_delimiter import HedStringDelimiter;


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mixed_hed_string = 'tag1,(tag2,tag5,(tag1),tag6),tag2,(tag3,tag5,tag6),tag3';
        cls.group_hed_string = '(tag1, tag2)';
        cls.empty_hed_string = '';
        cls.newline_hed_string = '\n';
        cls.removal_elements = ['(tag2,tag5,(tag1),tag6)', '(tag3,tag5,tag6)'];
        cls.unformatted_tag = '/Event/label/This label ends with a slash/';
        cls.formatted_tag = 'event/label/this label ends with a slash'

    def test_split_hed_string_into_list(self):
        split_hed_string = HedStringDelimiter.split_hed_string_into_list(self.mixed_hed_string);
        self.assertTrue(split_hed_string);
        self.assertIsInstance(split_hed_string, list);

    def test_format_hed_tags_in_set(self):
        hed_string_delimiter = HedStringDelimiter(self.mixed_hed_string);
        tag_set = hed_string_delimiter.get_tags();
        formatted_tag_set = HedStringDelimiter.format_hed_tags_in_set(tag_set);
        self.assertIsInstance(formatted_tag_set, set);
        self.assertEqual(len(tag_set), len(formatted_tag_set));

    def test_format_hed_tags_in_list(self):
        hed_string_delimiter = HedStringDelimiter(self.mixed_hed_string);
        top_level_tags = hed_string_delimiter.get_top_level_tags();
        formatted_top_level_tags = HedStringDelimiter.format_hed_tags_in_list(top_level_tags);
        self.assertIsInstance(formatted_top_level_tags, list);
        self.assertEqual(len(top_level_tags), len(formatted_top_level_tags));
        tag_groups = hed_string_delimiter.get_tag_groups();
        formatted_tag_groups = HedStringDelimiter.format_hed_tags_in_list(tag_groups);
        self.assertIsInstance(formatted_tag_groups, list);
        self.assertEqual(len(tag_groups), len(formatted_tag_groups));

    def test_format_hed_tag(self):
        formatted_tag = HedStringDelimiter.format_hed_tag(self.unformatted_tag);
        self.assertIsInstance(formatted_tag, str);
        self.assertEqual(formatted_tag, self.formatted_tag);

    def test_get_tags(self):
        hed_string_delimiter = HedStringDelimiter(self.mixed_hed_string);
        tag_set = hed_string_delimiter.get_tags();
        self.assertTrue(tag_set);
        self.assertIsInstance(tag_set, list);

    def test_get_formatted_tags(self):
        hed_string_delimiter = HedStringDelimiter(self.mixed_hed_string);
        formatted_tags = hed_string_delimiter.get_formatted_tags();
        self.assertTrue(formatted_tags);
        self.assertIsInstance(formatted_tags, list);

    def test_get_hed_string(self):
        hed_string_delimiter = HedStringDelimiter(self.mixed_hed_string);
        hed_string = hed_string_delimiter.get_hed_string();
        self.assertTrue(hed_string);
        self.assertIsInstance(hed_string, str);
        self.assertEqual(hed_string, self.mixed_hed_string);

    def test_get_split_hed_string_list(self):
        hed_string_delimiter = HedStringDelimiter(self.mixed_hed_string);
        split_hed_string = hed_string_delimiter.get_split_hed_string_list();
        self.assertTrue(split_hed_string);
        self.assertIsInstance(split_hed_string, list);

    def test_get_top_level_tags(self):
        hed_string_delimiter = HedStringDelimiter(self.mixed_hed_string);
        tag_set = hed_string_delimiter.get_tags();
        top_level_tags = hed_string_delimiter.get_top_level_tags();
        self.assertTrue(top_level_tags);
        self.assertIsInstance(top_level_tags, list);
        self.assertNotEqual(len(tag_set), len(top_level_tags));

    def test_get_formatted_top_level_tags(self):
        hed_string_delimiter = HedStringDelimiter(self.mixed_hed_string);
        tag_set = hed_string_delimiter.get_tags();
        formatted_top_level_tags = hed_string_delimiter.get_formatted_top_level_tags();
        self.assertTrue(formatted_top_level_tags);
        self.assertIsInstance(formatted_top_level_tags, list);
        self.assertNotEqual(len(tag_set), len(formatted_top_level_tags));

    def test__find_top_level_tags(self):
        hed_string_delimiter = HedStringDelimiter(self.mixed_hed_string);
        tag_set = hed_string_delimiter.get_tags();
        top_level_tags_1 = hed_string_delimiter.get_top_level_tags();
        self.assertTrue(top_level_tags_1);
        self.assertIsInstance(top_level_tags_1, list);
        self.assertNotEqual(len(tag_set), len(top_level_tags_1));
        hed_string_delimiter._find_top_level_tags();
        top_level_tags_2 = hed_string_delimiter.get_top_level_tags();
        self.assertTrue(top_level_tags_2);
        self.assertIsInstance(top_level_tags_2, list);
        self.assertNotEqual(len(tag_set), len(top_level_tags_2));
        self.assertEqual(top_level_tags_1, top_level_tags_2);

    def test_get_tag_groups(self):
        hed_string_delimiter = HedStringDelimiter(self.mixed_hed_string);
        tag_set = hed_string_delimiter.get_tags();
        group_tags = hed_string_delimiter.get_tag_groups();
        self.assertTrue(group_tags);
        self.assertIsInstance(group_tags, list);
        self.assertNotEqual(len(tag_set), len(group_tags));

    def test_get_formatted_tag_groups(self):
        hed_string_delimiter = HedStringDelimiter(self.mixed_hed_string);
        tag_set = hed_string_delimiter.get_tags();
        formatted_group_tags = hed_string_delimiter.get_formatted_tag_groups();
        self.assertTrue(formatted_group_tags);
        self.assertIsInstance(formatted_group_tags, list);
        self.assertNotEqual(len(tag_set), len(formatted_group_tags));

    def test_find_group_tags(self):
        hed_string_delimiter = HedStringDelimiter(self.mixed_hed_string);
        tag_set = hed_string_delimiter.get_tags();
        group_tags_1 = hed_string_delimiter.get_tag_groups();
        self.assertTrue(group_tags_1);
        self.assertIsInstance(group_tags_1, list);
        self.assertNotEqual(len(tag_set), len(group_tags_1));
        hed_string_delimiter._find_group_tags(hed_string_delimiter.get_split_hed_string_list());
        group_tags_2 = hed_string_delimiter.get_tag_groups();
        self.assertTrue(group_tags_2);
        self.assertIsInstance(group_tags_2, list);
        self.assertNotEqual(len(tag_set), len(group_tags_2));
        self.assertEqual(group_tags_1, group_tags_2);

    def test_hed_string_is_a_group(self):
        is_group = HedStringDelimiter.hed_string_is_a_group(self.mixed_hed_string);
        self.assertFalse(is_group);
        self.assertIsInstance(is_group, bool);
        is_group = HedStringDelimiter.hed_string_is_a_group(self.group_hed_string);
        self.assertTrue(is_group);
        self.assertIsInstance(is_group, bool);

    def test_string_is_space_or_empty(self):
        is_space_or_empty = HedStringDelimiter.string_is_space_or_empty(self.mixed_hed_string);
        self.assertFalse(is_space_or_empty);
        is_space_or_empty = HedStringDelimiter.string_is_space_or_empty(self.empty_hed_string);
        self.assertTrue(is_space_or_empty);
        is_space_or_empty = HedStringDelimiter.string_is_space_or_empty(self.newline_hed_string);
        self.assertTrue(is_space_or_empty);


if __name__ == '__main__':
    unittest.main();
