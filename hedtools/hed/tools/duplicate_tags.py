from hed.util.file_util import write_text_iter_to_file
from hed.util.hed_dictionary import HedDictionary


def check_for_duplicate_tags(local_xml_file):
    """Checks if a source XML file has duplicate tags.

        If there are no duplicates, returns None.
        If there are any duplicates, points to a file containing the formatted result.
    Parameters
    ----------
        local_xml_file: string
    Returns
    -------
    dictionary
            Contains source file location, dest, etc
    """
    hed_dict = HedDictionary(local_xml_file)
    dupe_tag_file = None
    if hed_dict.has_duplicate_tags():
        dupe_tag_file = write_text_iter_to_file(hed_dict.dupe_tag_iter(True))
    # for line in hed_dict.dupe_tag_iter(True):
    #     print(line)
    return dupe_tag_file
