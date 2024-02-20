import unittest
import wordcloud
from hed.tools.visualization import tag_word_cloud
from hed.tools.visualization.tag_word_cloud import load_and_resize_mask

import numpy as np
from PIL import Image, ImageDraw
import os


class TestWordCloudFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mask_path = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                      '../../data/visualization/word_mask.png'))

    def test_create_wordcloud(self):
        word_dict = {'tag1': 5, 'tag2': 3, 'tag3': 7}
        width = 400
        height = 200
        wc = tag_word_cloud.create_wordcloud(word_dict, width=width, height=height)

        self.assertIsInstance(wc, wordcloud.WordCloud)
        self.assertEqual(wc.width, width)
        self.assertEqual(wc.height, height)

    def test_create_wordcloud_default_params(self):
        word_dict = {'tag1': 5, 'tag2': 3, 'tag3': 7}
        wc = tag_word_cloud.create_wordcloud(word_dict)

        self.assertIsInstance(wc, wordcloud.WordCloud)
        self.assertEqual(wc.width, 400)
        self.assertEqual(wc.height, 300)

    def test_mask_scaling(self):
        word_dict = {'tag1': 5, 'tag2': 3, 'tag3': 7}
        wc = tag_word_cloud.create_wordcloud(word_dict, self.mask_path, width=300, height=300)

        self.assertIsInstance(wc, wordcloud.WordCloud)
        self.assertEqual(wc.width, 300)
        self.assertEqual(wc.height, 300)

    def test_mask_scaling2(self):
        word_dict = {'tag1': 5, 'tag2': 3, 'tag3': 7}
        wc = tag_word_cloud.create_wordcloud(word_dict, self.mask_path, width=300, height=None)

        self.assertIsInstance(wc, wordcloud.WordCloud)
        self.assertEqual(wc.width, 300)
        self.assertLess(wc.height, 300)

    def test_create_wordcloud_with_empty_dict(self):
        # Test creation of word cloud with an empty dictionary
        word_dict = {}
        with self.assertRaises(ValueError):
            tag_word_cloud.create_wordcloud(word_dict)

    def test_create_wordcloud_with_single_word(self):
        # Test creation of word cloud with a single word
        word_dict = {'single_word': 1}
        wc = tag_word_cloud.create_wordcloud(word_dict)
        self.assertIsInstance(wc, wordcloud.WordCloud)
        # Check that the single word is in the word cloud
        self.assertIn('single_word', wc.words_)

    def test_valid_word_cloud(self):
        word_dict = {'tag1': 5, 'tag2': 3, 'tag3': 7}
        wc = tag_word_cloud.create_wordcloud(word_dict, mask_path=self.mask_path, width=400, height=None)
        svg_output = tag_word_cloud.word_cloud_to_svg(wc)
        self.assertTrue(svg_output.startswith('<svg'))
        self.assertIn("<circle cx=", svg_output)
        self.assertTrue(svg_output.endswith('</svg>'))
        self.assertIn('fill:rgb', svg_output)


class TestLoadAndResizeMask(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a simple black and white image
        cls.original_size = (300, 200)
        cls.img = Image.new('L', cls.original_size, 255)  # Start with a white image

        # Draw a black circle in the middle of the image
        d = ImageDraw.Draw(cls.img)
        circle_radius = min(cls.original_size) // 4
        circle_center = (cls.original_size[0] // 2, cls.original_size[1] // 2)
        d.ellipse((circle_center[0] - circle_radius,
                   circle_center[1] - circle_radius,
                   circle_center[0] + circle_radius,
                   circle_center[1] + circle_radius),
                  fill=0)
        cls.img_path = 'temp_img.png'
        cls.img.save(cls.img_path)

        # Start with a black fully transparent image
        cls.img_trans = Image.new('RGBA', cls.original_size, (0, 0, 0, 0))

        # Draw a black opaque circle in the middle
        d = ImageDraw.Draw(cls.img_trans)
        circle_radius = min(cls.original_size) // 4
        circle_center = (cls.original_size[0] // 2, cls.original_size[1] // 2)
        d.ellipse((circle_center[0] - circle_radius,
                   circle_center[1] - circle_radius,
                   circle_center[0] + circle_radius,
                   circle_center[1] + circle_radius),
                  fill=(0, 0, 0, 255))
        cls.img_path_trans = 'temp_img_trans.png'
        cls.img_trans.save(cls.img_path_trans)


    @classmethod
    def tearDownClass(cls):
        # Clean up the temp image
        os.remove(cls.img_path)
        os.remove(cls.img_path_trans)

    def test_no_resizing(self):
        mask = load_and_resize_mask(self.img_path)
        mask_img = Image.fromarray(mask)
        self.assertEqual((mask_img.width, mask_img.height), self.original_size)

    def test_width_resizing(self):
        width = 150
        mask = load_and_resize_mask(self.img_path, width=width)
        mask_img = Image.fromarray(mask)
        expected_width, expected_height = width, int(self.original_size[1] * width / self.original_size[0])
        self.assertEqual((mask_img.width, mask_img.height), (expected_width, expected_height))

    def test_height_resizing(self):
        height = 100
        mask = load_and_resize_mask(self.img_path, height=height)
        mask_img = Image.fromarray(mask)
        expected_shape = (int(self.original_size[0] * height / self.original_size[1]), height)
        self.assertEqual((mask_img.width, mask_img.height), expected_shape)

    def test_both_dimensions_resizing(self):
        width, height = 100, 75
        mask = load_and_resize_mask(self.img_path, width=width, height=height)
        self.assertEqual(mask.shape, (height, width))

    def test_mask_color(self):
        mask = load_and_resize_mask(self.img_path)
        # The mask should have 0 and 1, and no other values
        unique_values = np.unique(mask)
        self.assertCountEqual(unique_values, [0, 255])

    def test_transparent_mask(self):
        mask = load_and_resize_mask(self.img_path_trans)
        # The mask should have 0 and 1, and no other values
        unique_values = np.unique(mask)
        self.assertCountEqual(unique_values, [0, 255])

        mask = load_and_resize_mask(self.img_path_trans, width=500)
        # The mask should have 0 and 1, and no other values
        unique_values = np.unique(mask)
        self.assertCountEqual(unique_values, [0, 255])
        # Verify sizes
        self.assertEqual(mask.shape, (333, 500))

        mask_img = Image.fromarray(mask)
        expected_width, expected_height = 500, int(self.original_size[1] * 500 / self.original_size[0])
        self.assertEqual((mask_img.width, mask_img.height), (expected_width, expected_height))