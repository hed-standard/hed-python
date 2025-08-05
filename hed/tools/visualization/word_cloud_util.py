""" Support utilities for word cloud generation. """
import random
from random import Random

import numpy as np
from PIL import Image, ImageFilter
import matplotlib as mp1
import wordcloud as wcloud


def generate_contour_svg(wc, width, height):
    """ Generate an SVG contour mask based on a word cloud object and dimensions.

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
    return _numpy_to_svg(contour, radius=wc.contour_width, color=wc.contour_color)


def _get_contour_mask(wc, width, height):
    """ Slightly tweaked copy of internal WorldCloud function to allow transparency for mask.

    Parameters:
        wc (WordCloud): Representation of the word cloud.
        width (int): Width of the generated mask.
        height (int): Height of generated mask.

    Returns:
        Image:  Image of mask.


    """
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


def _draw_contour(wc, img: Image):
    """Slightly tweaked copy of internal WorldCloud function to allow transparency.

    Parameters:
        wc (WordCloud): Wordcloud object.
        img (Image):  Image to work with.

    Returns:
        Image: Modified image.

    """
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
wcloud.WordCloud._draw_contour = _draw_contour


def _numpy_to_svg(contour, radius=1, color="black"):
    """ Convert a numpy array to SVG.

    Parameters:
        contour (np.Array): Image to be converted.
        radius (float): The radius of the contour to draw.
        color(string): the color to draw it as, e.g. "red".

    Returns:
        str: The SVG representation.
    """
    svg_elements = []
    points = np.array(contour.nonzero()).T
    for y, x in points:
        svg_elements.append(f'<circle cx="{x}" cy="{y}" r="{radius}" stroke="{color}" fill="{color}" />')

    return '\n'.join(svg_elements)


def random_color_darker(random_state=None):
    """Random color generation function.

    Parameters:
        random_state (Random or None): Previous state of random generation for next color generation.

    Returns:
        str:  Represents a hue, saturation, and lightness.

    """
    if random_state is None:
        random_state = Random()
    return f"hsl({random_state.randint(0, 255)}, {random_state.randint(50, 100)}%, {random_state.randint(0, 50)}%)"


class ColormapColorFunc:
    """ Represents a colormap. """
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
        self.colormap = mp1.colormaps[colormap]
        self.color_range = color_range
        self.color_step_range = color_step_range
        self.current_fraction = random.uniform(0, 1)  # Start at a random point

    def color_func(self, word, font_size, position, orientation, random_state=None, **kwargs):
        """ Update the current color fraction and wrap around if necessary. """
        color_step = random.uniform(*self.color_step_range)
        self.current_fraction = (self.current_fraction + color_step) % 1.0

        # Scale the fraction to the desired range
        scaled_fraction = self.color_range[0] + (self.current_fraction * (self.color_range[1] - self.color_range[0]))

        # Get the color from the colormap
        color = self.colormap(scaled_fraction)

        return tuple(int(c * 255) for c in color[:3])  # Convert to RGB format


default_color_func = ColormapColorFunc().color_func
