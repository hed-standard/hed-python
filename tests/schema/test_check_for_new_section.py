import unittest


class TestCheckForNewSection(unittest.TestCase):
    pass
    # def test_empty_line_returns_none(self):
    #     result = SchemaLoaderWiki._check_for_new_section('', 0)
    #     self.assertEqual(result, (None, 0))
    #
    # def test_content_after_endhed_raises(self):
    #     with self.assertRaises(HedFileError) as cm:
    #         SchemaLoaderWiki._check_for_new_section('*SectionA content', HedWikiSection.EndHed, filename='schema.wiki')
    #     self.assertEqual(cm.exception.code, HedExceptions.WIKI_LINE_INVALID)
    #
    # def test_non_section_line_returns_none(self):
    #     result = SchemaLoaderWiki._check_for_new_section('Not a section tag', 1)
    #     self.assertEqual(result, (None, 1))
    #
    # def test_valid_section_in_order(self):
    #     result = SchemaLoaderWiki._check_for_new_section("!# start schema", 0)
    #     self.assertEqual(result, ("!# start schema", 4))
    #
    # def test_second_section_in_order(self):
    #     result = SchemaLoaderWiki._check_for_new_section('*SectionB This is SectionB', 1)
    #     self.assertEqual(result, ('SectionB', 2))
    #
    # def test_section_out_of_order_raises(self):
    #     with self.assertRaises(HedFileError) as cm:
    #         SchemaLoaderWiki._check_for_new_section('*SectionA Again', 2)
    #     self.assertEqual(cm.exception.code, HedExceptions.SCHEMA_SECTION_MISSING)
    #
    # def test_invalid_end_tag_raises(self):
    #     with self.assertRaises(HedFileError) as cm:
    #         SchemaLoaderWiki._check_for_new_section('*END unexpected trailing content', 2)
    #     self.assertEqual(cm.exception.code, HedExceptions.WIKI_SEPARATOR_INVALID)
    #
    # def test_section_with_extra_spaces(self):
    #     result = SchemaLoaderWiki._check_for_new_section("   '''SectionC'''  Label   ", 2)
    #     self.assertEqual(result, ('SectionC', 3))
    #
    # def test_line_with_unrecognized_tag_returns_none(self):
    #     result = SchemaLoaderWiki._check_for_new_section('*UnknownTag Foo', 1)
    #     self.assertEqual(result, (None, 1))


if __name__ == "__main__":
    unittest.main()
