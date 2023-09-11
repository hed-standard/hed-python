import numpy as np
from PIL import Image
from hed.tools.visualization.word_cloud_util import default_color_func, WordCloud, generate_contour_svg


def create_wordcloud(word_dict, mask_path=None, background_color=None, width=400, height=None, **kwargs):
    """Takes a word dict and returns a generated word cloud object

    Parameters:
        word_dict(dict): words and their frequencies
        mask_path(str or None): The path of the mask file
        background_color(str or None): If None, transparent background.
        width(int): width in pixels
        height(int): height in pixels
        kwargs(kwargs): Any other parameters WordCloud accepts, overrides default values where relevant.
    Returns:
        word_cloud(WordCloud): The generated cloud.
                               Use .to_file to save it out as an image.

    :raises ValueError:
        An empty dictionary was passed
    """
    mask_image = None
    if mask_path:
        mask_image = load_and_resize_mask(mask_path, width, height)
        width = mask_image.shape[1]
        height = mask_image.shape[0]
    if height is None:
        if width is None:
            width = 400
        height = width // 2
    if width is None:
        width = height * 2

    kwargs.setdefault('contour_width', 3)
    kwargs.setdefault('contour_color', 'black')
    kwargs.setdefault('prefer_horizontal', 0.75)
    kwargs.setdefault('color_func', default_color_func)
    kwargs.setdefault('relative_scaling', 1)
    kwargs.setdefault('max_font_size', height / 15)
    kwargs.setdefault('min_font_size', 5)

    wc = WordCloud(background_color=background_color, mask=mask_image,
                   width=width, height=height, mode="RGBA", **kwargs)

    wc.generate_from_frequencies(word_dict)

    return wc


def word_cloud_to_svg(wc):
    """Takes word cloud and returns it as an SVG string.

    Parameters:
        wc(WordCloud): the word cloud object
    Returns:
        svg_string(str): The svg for the word cloud
    """
    svg_string = wc.to_svg()
    svg_string = svg_string.replace("fill:", "fill:rgb")
    svg_string = svg_string.replace("</svg>", generate_contour_svg(wc, wc.width, wc.height) + "</svg>")
    return svg_string


def summary_to_dict(summary, transform=np.log10, adjustment=5):
    """Converts a HedTagSummary json dict into the word cloud input format

    Parameters:
        summary(dict): The summary from a summarize hed tags op
        transform(func): The function to transform the number of found tags
                         Default log10
        adjustment(int): Value added after transform.
    Returns:
        word_dict(dict): a dict of the words and their occurrence count

    :raises KeyError:
        A malformed dictionary was passed

    """
    if transform is None:
        transform = lambda x: x
    overall_summary = summary.get("Overall summary", {})
    specifics = overall_summary.get("Specifics", {})
    tag_dict = specifics.get("Main tags", {})
    word_dict = {}
    for tag_sub_list in tag_dict.values():
        for tag_sub_dict in tag_sub_list:
            word_dict[tag_sub_dict['tag']] = transform(tag_sub_dict['events']) + adjustment

    return word_dict


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
        mask_image = Image.open(mask_path)

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

            mask_image = mask_image.resize(output_size.astype(int), Image.LANCZOS)

            # Convert to greyscale then to binary black and white (0 or 255)
            mask_image = mask_image.convert('L')
            mask_image_array = np.array(mask_image)
            mask_image_array = np.where(mask_image_array > 127, 255, 0)
        else:
            mask_image_array = np.array(mask_image)

        return mask_image_array.astype(np.uint8)
