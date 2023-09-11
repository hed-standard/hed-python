import random
from random import Random

import numpy as np
from PIL import Image, ImageFilter
from matplotlib import cm
from wordcloud import WordCloud


def generate_contour_svg(wc, width, height):
    """Generates an SVG contour mask based on a word cloud object and dimensions.

    Parameters:
        wc (WordCloud): The word cloud object.
        width (int): SVG image width in pixels.
        height (int): SVG image height in pixels.

    Returns:
        str: SVG point list for the contour mask, or empty string if not generated.
    """
    contour = _get_contour_mask(wc, width, height)
    if contour is None:
        return ""
    return _numpy_to_svg(contour)


def _get_contour_mask(wc, width, height):
    """Slightly tweaked copy of internal WorldCloud function to allow transparency"""
    if wc.mask is None or wc.contour_width == 0 or wc.contour_color is None:
        return None

    mask = wc._get_bolean_mask(wc.mask) * 255
    contour = Image.fromarray(mask.astype(np.uint8))
    contour = contour.resize((width, height))
    contour = contour.filter(ImageFilter.FIND_EDGES)
    contour = np.array(contour)

    # make sure borders are not drawn before changing width
    contour[[0, -1], :] = 0
    contour[:, [0, -1]] = 0

    return contour


def _draw_contour(wc, img):
    """Slightly tweaked copy of internal WorldCloud function to allow transparency"""
    contour = _get_contour_mask(wc, img.width, img.height)
    if contour is None:
        return img

    # use gaussian to change width, divide by 10 to give more resolution
    radius = wc.contour_width / 10
    contour = Image.fromarray(contour)
    contour = contour.filter(ImageFilter.GaussianBlur(radius=radius))
    contour = np.array(contour) > 0
    if img.mode == 'RGBA':
        contour = np.dstack((contour, contour, contour, contour))
    else:
        contour = np.dstack((contour, contour, contour))

    # color the contour
    ret = np.array(img) * np.invert(contour)
    color = np.array(Image.new(img.mode, img.size, wc.contour_color))
    ret += color * contour

    return Image.fromarray(ret)


# Replace WordCloud function with one that can handle transparency
WordCloud._draw_contour = _draw_contour


def _numpy_to_svg(contour):
    svg_elements = []
    points = np.array(contour.nonzero()).T
    for y, x in points:
        svg_elements.append(f'<circle cx="{x}" cy="{y}" r="1" stroke="black" fill="black" />')

    return '\n'.join(svg_elements)


def random_color_darker(word=None, font_size=None, position=None, orientation=None, font_path=None, random_state=None):
    """Random color generation func"""
    if random_state is None:
        random_state = Random()
    return f"hsl({random_state.randint(0, 255)}, {random_state.randint(50, 100)}%, {random_state.randint(0, 50)}%)"


class ColormapColorFunc:
    def __init__(self, colormap='nipy_spectral', color_range=(0.0, 0.5), color_step_range=(0.15, 0.25)):
        """Initialize a word cloud color generator.

        Parameters:
            colormap (str, optional): The name of the matplotlib colormap to use for generating colors.
                                      Defaults to 'nipy_spectral'.
            color_range (tuple of float, optional): A tuple containing the minimum and maximum values to use
                                                    from the colormap. Defaults to (0.0, 0.5).
            color_step_range (tuple of float, optional): A tuple containing the minimum and maximum values to step
                                                         through the colormap. Defaults to (0.15, 0.25).
                                                         This is the speed at which it goes through the range chosen.
                                                         .25 means it will go through 1/4 of the range each pick.
        """
        self.colormap = cm.get_cmap(colormap)
        self.color_range = color_range
        self.color_step_range = color_step_range
        self.current_fraction = random.uniform(0, 1)  # Start at a random point

    def color_func(self, word, font_size, position, orientation, random_state=None, **kwargs):
        # Update the current color fraction and wrap around if necessary
        color_step = random.uniform(*self.color_step_range)
        self.current_fraction = (self.current_fraction + color_step) % 1.0

        # Scale the fraction to the desired range
        scaled_fraction = self.color_range[0] + (self.current_fraction * (self.color_range[1] - self.color_range[0]))

        # Get the color from the colormap
        color = self.colormap(scaled_fraction)

        return tuple(int(c * 255) for c in color[:3])  # Convert to RGB format


default_color_func = ColormapColorFunc().color_func
