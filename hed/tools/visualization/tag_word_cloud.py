from wordcloud import WordCloud


def create_wordcloud(word_dict, width=400, height=200):
    """Takes a word dict and returns a generated word cloud object

    Parameters:
        word_dict(dict): words and their frequencies
        width(int): width in pixels
        height(int): height in pixels
    Returns:
        word_cloud(WordCloud): The generated cloud.
                               Use .to_file to save it out as an image.

    :raises ValueError:
        An empty dictionary was passed
    """
    wc = WordCloud(background_color='white', width=width, height=height)

    wc.generate_from_frequencies(word_dict)

    return wc


def summary_to_dict(summary):
    """Converts a HedTagSummary json dict into the word cloud input format

    Parameters:
        summary(dict): The summary from a summarize hed tags op

    Returns:
        word_dict(dict): a dict of the words and their occurrence count
        
    :raises KeyError:
        A malformed dictionary was passed
        
    """
    overall_summary = summary.get("Overall summary", {})
    specifics = overall_summary.get("Specifics", {})
    tag_dict = specifics.get("Main tags", {})
    word_dict = {}
    for tag_sub_list in tag_dict.values():
        for tag_sub_dict in tag_sub_list:
            word_dict[tag_sub_dict['tag']] = tag_sub_dict['events']

    return word_dict
