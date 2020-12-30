from hed.util.file_util import write_text_iter_to_file
from hed.schematools import constants
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
    for line in hed_dict.dupe_tag_iter(True):
        print(line)
    hed_info_dictionary = {constants.HED_XML_TREE_KEY: None,
                           constants.HED_XML_VERSION_KEY: None,
                           constants.HED_CHANGE_LOG_KEY: None,
                           constants.HED_WIKI_PAGE_KEY: None,
                           constants.HED_INPUT_LOCATION_KEY: local_xml_file,
                           constants.HED_OUTPUT_LOCATION_KEY: dupe_tag_file}
    return hed_info_dictionary
