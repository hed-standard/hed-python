""" Utilities for creating a word cloud. """

import numpy as np
from PIL import Image
from hed.errors.exceptions import HedFileError
from hed.tools.visualization import word_cloud_util
from wordcloud import WordCloud

MIN_WORD_CLOUD_SIZE = 100

def create_wordcloud(word_dict, mask_path=None, background_color=None, width=400, height=300, **kwargs):
    """ Takes a word dict and returns a generated word cloud object.

    Parameters:
        word_dict (dict): words and their frequencies
        mask_path (str or None): The path of the mask file
        background_color (str or None): If None, transparent background.
        width (int): width in pixels.
        height (int): height in pixels.
        kwargs (kwargs): Any other parameters WordCloud accepts, overrides default values where relevant.

    Returns:
        WordCloud: The generated cloud. (Use .to_file to save it out as an image.)

    :raises ValueError:
        An empty dictionary was passed
    """
    mask_image = None
    if mask_path:
        mask_image = load_and_resize_mask(mask_path, width, height)
        width = round(mask_image.shape[1])
        height = round(mask_image.shape[0])
    if height is None and width is None:
        width = 400
        height = 300
    elif height is None:
        height = round(width/1.5)
    elif width is None:
        width = round(height * 1.5)
    width = max(width, MIN_WORD_CLOUD_SIZE)
    height = max(height, MIN_WORD_CLOUD_SIZE)
    kwargs.setdefault('contour_width', 3)
    kwargs.setdefault('contour_color', 'black')
    kwargs.setdefault('prefer_horizontal', 0.75)
    kwargs.setdefault('color_func', word_cloud_util.default_color_func)
    kwargs.setdefault('relative_scaling', 1)
    kwargs.setdefault('max_font_size', max(round(height / 20), 12))
    kwargs.setdefault('min_font_size', 8)
    if 'font_path' not in kwargs:
        kwargs['font_path'] = None
    elif kwargs['font_path'] and not kwargs['font_path'].lower().endswith((".ttf", ".otf", ".ttc")):
        raise HedFileError("InvalidFontPath", f"Font {kwargs['font_path']} not valid on this system", "")

    wc = WordCloud(background_color=background_color, mask=mask_image,
                   width=width, height=height, mode="RGBA", **kwargs)

    wc.generate_from_frequencies(word_dict)

    return wc


def word_cloud_to_svg(wc):
    """ Return a WordCould as an SVG string.

    Parameters:
        wc (WordCloud): the word cloud object.

    Returns:
       str: The svg for the word cloud.

    """
    svg_string = wc.to_svg()
    svg_string = svg_string.replace("fill:", "fill:rgb")
    svg_string = svg_string.replace("</svg>", word_cloud_util.generate_contour_svg(wc, wc.width, wc.height) + "</svg>")
    return svg_string


def load_and_resize_mask(mask_path, width=None, height=None):
    """ Load a mask image and resize it according to given dimensions.

        The image is resized maintaining aspect ratio if only width or height is provided.

        Returns None if no mask_path.

    Parameters:
        mask_path (str): The path to the mask image file.
        width (int, optional): The desired width of the resized image. If only width is provided,
            the image is scaled to maintain its original aspect ratio. Defaults to None.
        height (int, optional): The desired height of the resized image. If only height is provided,
            the image is scaled to maintain its original aspect ratio. Defaults to None.

    Returns:
        numpy.ndarray: The loaded and processed mask image as a numpy array with binary values (0 or 255).
    """
    if mask_path:
        mask_image = Image.open(mask_path).convert("RGBA")

        if width or height:
            original_size = np.array((mask_image.width, mask_image.height))
            output_size = np.array((width, height))
            # Handle one missing param
            if not height:
                scale = original_size[0] / width
                output_size = original_size / scale
            elif not width:
                scale = original_size[1] / height
                output_size = original_size / scale

            mask_image = mask_image.resize(tuple(output_size.astype(int)), Image.LANCZOS)

        mask_image_array = np.array(mask_image)
        # Treat transparency (alpha < 128) or white (R>127, G>127, B>127) as white, else black
        mask_image_array = np.where((mask_image_array[:, :, 3] < 128) |
                                    ((mask_image_array[:, :, 0] > 127) &
                                     (mask_image_array[:, :, 1] > 127) &
                                     (mask_image_array[:, :, 2] > 127)), 255, 0)

        return mask_image_array.astype(np.uint8)
