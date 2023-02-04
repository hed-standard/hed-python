""" Container for a BIDS sidecar file. """

import os
from hed.models.sidecar import Sidecar
from hed.tools.bids.bids_file import BidsFile


class BidsSidecarFile(BidsFile):
    """ A BIDS sidecar file. """

    def __init__(self, file_path):
        """ Constructs a bids sidecar from a file.

        Parameters:
            file_path (str): The real path of the sidecar.

        """
        super().__init__(file_path)

    def is_sidecar_for(self, obj):
        """ Return true if this is a sidecar for obj.

         Parameters:
             obj (BidsFile):  A BidsFile object to check.

         Returns:
             bool:   True if this is a BIDS parent of obj and False otherwise.

         Notes:
             - A sidecar is a sidecar for itself.

         """

        if obj.file_path == self.file_path:
            return True
        elif obj.suffix != self.suffix:
            return False
        elif os.path.dirname(self.file_path) != os.path.commonpath([obj.file_path, self.file_path]):
            return False

        for key, item in self.entity_dict.items():
            if key not in obj.entity_dict or obj.entity_dict[key] != item:
                return False
        return True

    def set_contents(self, content_info=None, overwrite=False):
        """ Set the contents of the sidecar.

        Parameters:
            content_info (list, str, or None): If None, create a Sidecar from the object's file-path.
            overwrite (bool): If True, overwrite contents if already set.

        Notes:
            - The handling of content_info is as follows:
                - None: This object's file_path is used.
                - str:  The string is interpreted as a path of the JSON.
                - list: The list is of paths.

         """
        if not overwrite and self.contents:
            return
        if not content_info:
            content_info = self.file_path
        self._contents = Sidecar(files=content_info, name=os.path.basename(self.file_path))
        self.has_hed = self.is_hed(self.contents.loaded_dict)

    @staticmethod
    def is_hed(json_dict):
        """ Return True if the json has HED.

        Parameters:
            json_dict (dict): A dictionary representing a JSON file or merged file.

        Returns:
            bool:  True if the dictionary has HED or HED_assembled as a first or second-level key.

        """

        if not json_dict or not isinstance(json_dict, dict):
            return False
        json_keys = json_dict.keys()
        if 'HED' in json_keys or 'HED_assembled' in json_keys:
            return True
        for key, value in json_dict.items():
            if not isinstance(value, dict):
                continue
            val_keys = value.keys()
            if 'HED' in val_keys or 'HED_assembled' in val_keys:
                return True

        return False
