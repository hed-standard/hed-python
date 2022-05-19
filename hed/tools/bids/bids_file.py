import os
from hed.util.io_util import parse_bids_filename


class BidsFile:
    """ Represents the entity dictionary and file names for a BIDs file.

    Args:
        file_path (str):   Full path of the file.

    Attributes:
        file_path (str):     Real path of the file.
        suffix (str):        Suffix part of the filename.
        ext (str):           Extension (including the .).
        entity_dict (dict):  Dictionary of entity-names (keys) and entity-values (values).

    """

    def __init__(self, file_path):
        self.file_path = os.path.realpath(file_path)
        suffix, ext, entity_dict = parse_bids_filename(self.file_path)
        self.suffix = suffix
        self.ext = ext
        self.entity_dict = entity_dict
        self.sidecar = None    # list of sidecars starting at the root (including itself if sidecar)
        self.contents = None

    @property
    def get_contents(self):
        return self.contents

    def clear_contents(self):
        self.contents = None

    def set_contents(self, content_info=None, no_overwrite=True):
        if self.contents and no_overwrite:
            return
        self.contents = content_info

    def __str__(self):
        my_str = self.file_path + ":\n\tname_suffix=" + self.suffix + " ext=" + self.ext + \
               " entity_dict=" + str(self.entity_dict)
        if self.sidecar:
            my_str = my_str + "\n\tmerged sidecar=" + str(self.sidecar.file_path)
        return my_str
