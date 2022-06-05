import os
from hed.util.io_util import parse_bids_filename


class BidsFile:
    """ A BIDS file with entity dictionary.

    Attributes:
        file_path (str):             Real path of the file.
        suffix (str):                Suffix part of the filename.
        ext (str):                   Extension (including the .).
        entity_dict (dict):          Dictionary of entity-names (keys) and entity-values (values).
        sidecar (BidsSidecarFile):   Merged sidecar for this file.
        contents:                    Contents of this file

    Notes:
        - This class may hold the merged sidecar giving metadata for this file as well as contents.

    """

    def __init__(self, file_path):
        """ Constructor for a file path.

        Args:
            file_path(str): Full path of the file.

        """
        self.file_path = os.path.realpath(file_path)
        suffix, ext, entity_dict = parse_bids_filename(self.file_path)
        self.suffix = suffix
        self.ext = ext
        self.entity_dict = entity_dict
        self.sidecar = None    # list of sidecars starting at the root (including itself if sidecar)
        self.contents = None
        self.has_hed = False

    @property
    def get_contents(self):
        """ Return the current contents of this object. """
        return self.contents

    def clear_contents(self):
        """ Set the contents attribute of this object to None. """
        self.contents = None

    def get_key(self, entities):
        """ Return a key for this BIDS file given a list of entities.

        Args:
            entities (tuple):  A tuple of strings representing entities.

        Returns:
            str:  A key based on this object.

        """
        key_list = []
        for entity in entities:
            if entity in self.entity_dict:
                key_list.append(f"{entity}-{self.entity_dict[entity]}")
        key = '_'.join(key_list)
        return key

    def set_contents(self, content_info=None, overwrite=False):
        """ Set the contents of this object.

        Args:
            content_info:      The contents appropriate for this object.
            overwrite (bool):  If False and the contents are not empty, do nothing.

        Notes:
            - Do not set if the contents are already set and no_overwrite is True.

        """
        if self.contents and not overwrite:
            return
        self.contents = content_info
        self.has_hed = False

    def __str__(self):
        """ Return a string representation of this object. """
        my_str = self.file_path + ":\n\tname_suffix=" + self.suffix + " ext=" + self.ext + \
            " entity_dict=" + str(self.entity_dict)
        if self.sidecar:
            my_str = my_str + "\n\tmerged sidecar=" + str(self.sidecar.file_path)
        return my_str
