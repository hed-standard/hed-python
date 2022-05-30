import os
import io
import json
from hed.models.sidecar import Sidecar
from hed.tools.bids.bids_file import BidsFile


class BidsSidecarFile(BidsFile):
    """ A BIDS sidecar file. """

    def __init__(self, file_path):
        super().__init__(file_path)

    def is_sidecar_for(self, obj):
        """ Return true if this is a sidecar for obj.

         Args:
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

    def set_contents(self, content_info=None):
        """ Set the contents of the sidecar.

        Args:
            content_info (list or None): If None, create a Sidecar from the objects file-path.
                Otherwise a list of .json files to be merged starting from the root level downward.

         """
        if not content_info:
            file_contents = self.file_path
        elif isinstance(content_info, str):
            file_contents = content_info
        elif isinstance(content_info, list):
            file_contents = io.StringIO(json.dumps(self.get_merged(content_info)))
        self.contents = Sidecar(file=file_contents, name=os.path.realpath(os.path.basename(self.file_path)))

    @staticmethod
    def get_merged(file_list):
        """ Return merged contents of JSON files as dict.

        Args:
            file_list (list or None):  A list of JSON files representing sidecars in the order they are to be merged.

        Returns:
            dict:  A merged JSON dictionary.

        Notes:
            - Merging takes place from front to back with overwriting of top-level keys.

        """
        merged_sidecar = {}
        if not file_list:
            return merged_sidecar
        for file in file_list:
            if isinstance(file, BidsSidecarFile):
                file = file.file_path
            with open(file, 'r') as fp:
                next_sidecar = json.load(fp)
            for key, item in next_sidecar.items():
                merged_sidecar[key] = item
        return merged_sidecar