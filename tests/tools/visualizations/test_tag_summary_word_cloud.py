import unittest
from wordcloud import WordCloud
from hed.tools.visualizations import tag_summary_word_cloud

class TestWordCloudFunctions(unittest.TestCase):

    def test_convert_summary_to_word_dict(self):
        # Assume we have a valid summary_json
        summary_json = {
            'Dataset': {
                'Overall summary': {
                    'Main tags': {
                        'tag_category_1': [
                            {'tag': 'tag1', 'events': 5},
                            {'tag': 'tag2', 'events': 3}
                        ],
                        'tag_category_2': [
                            {'tag': 'tag3', 'events': 7}
                        ]
                    }
                }
            }
        }
        expected_output = {'tag1': 5, 'tag2': 3, 'tag3': 7}

        word_dict = tag_summary_word_cloud.convert_summary_to_word_dict(summary_json)
        self.assertEqual(word_dict, expected_output)

    def test_create_wordcloud(self):
        word_dict = {'tag1': 5, 'tag2': 3, 'tag3': 7}
        width = 400
        height = 200
        wc = tag_summary_word_cloud.create_wordcloud(word_dict, width, height)

        self.assertIsInstance(wc, WordCloud)
        self.assertEqual(wc.width, width)
        self.assertEqual(wc.height, height)

    def test_create_wordcloud_with_empty_dict(self):
        # Test creation of word cloud with an empty dictionary
        word_dict = {}
        with self.assertRaises(ValueError):
            tag_summary_word_cloud.create_wordcloud(word_dict)

    def test_create_wordcloud_with_single_word(self):
        # Test creation of word cloud with a single word
        word_dict = {'single_word': 1}
        wc = tag_summary_word_cloud.create_wordcloud(word_dict)
        self.assertIsInstance(wc, WordCloud)
        # Check that the single word is in the word cloud
        self.assertIn('single_word', wc.words_)