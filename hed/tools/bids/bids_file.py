""" Models a BIDS file. """

import os
from hed.tools.bids import bids_util


class BidsFile:
    """ A BIDS file with entity dictionary.

    Attributes:
        file_path (str):             Real path of the file.
        suffix (str):                Suffix part of the filename.
        ext (str):                   Extension (including the .).
        entity_dict (dict):          Dictionary of entity-names (keys) and entity-values (values).

    Notes:
        - This class may hold the merged sidecar giving metadata for this file as well as contents.

    """

    def __init__(self, file_path):
        """ Constructor for a file path.

        Parameters:
            file_path(str): Full path of the file.

        """
        self.file_path = os.path.realpath(file_path)
        name_dict = bids_util.parse_bids_filename(self.file_path)
        self.basename = name_dict.get("basename")
        self.suffix = name_dict.get("suffix")
        self.ext = name_dict.get("ext")
        self.entity_dict = name_dict.get("entities")
        self.bad = name_dict.get("bad")
        self._contents = None
        self.has_hed = False

    @property
    def contents(self):
        """ Return the current contents of this object. """
        return self._contents

    def clear_contents(self):
        """ Set the contents attribute of this object to None. """
        self._contents = None

    def get_entity(self, entity_name):
        """ Return the entity value for the specified entity.

        Parameters:
            entity_name (str): Name of the BIDS entity, for example task, run, or sub.

        Returns:
            Union[str, None]: Entity value if any, otherwise None.
        """
        return self.entity_dict.get(entity_name, None)

    def get_key(self, entities=None):
        """ Return a key for this BIDS file given a list of entities.

        Parameters:
            entities (tuple):  A tuple of strings representing entities.

        Returns:
            str:  A key based on this object.

        Notes:
            If entities is None, then the file path is used as the key.

        """

        if not entities:
            return self.file_path
        key_list = []
        for entity in entities:
            if entity in self.entity_dict:
                key_list.append(f"{entity}-{self.entity_dict[entity]}")
        key = '_'.join(key_list)
        return key

    def set_contents(self, content_info=None, overwrite=False):
        """ Set the contents of this object.

        Parameters:
            content_info (Any):      JSON dictionary The contents appropriate for this object.
            overwrite (bool):  If False and the contents are not empty, do nothing.

        Notes:
            - Do not set if the contents are already set and no_overwrite is True.

        """
        if self._contents and not overwrite:
            return
        self._contents = content_info
        self.has_hed = False

    def __str__(self):
        """ Return a string representation of this object. """
        my_str = self.file_path + ":\n\tname_suffix=" + self.suffix + " ext=" + self.ext + \
            " entity_dict=" + str(self.entity_dict)
        return my_str
